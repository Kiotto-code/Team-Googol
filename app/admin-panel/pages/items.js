import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

const ITEM_STATUSES = [
  '',
  'uploaded',
  'processing',
  'available',
  'matched',
  'claimed',
  'returned',
  'expired',
  'archived',
];

export const itemsPage = {
  route: '/items',
  label: 'Items',
  icon: '🎒',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    let items = [];
    let isLoading = true;
    let selectedStatus = '';
    const { modal } = context;

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Items';
    header.appendChild(title);

    const filterForm = document.createElement('form');
    filterForm.setAttribute('aria-label', 'Filter items');
    filterForm.style.flexDirection = 'row';
    filterForm.style.gap = '12px';

    const statusField = document.createElement('label');
    statusField.textContent = 'Status';
    const select = document.createElement('select');
    ITEM_STATUSES.forEach((status) => {
      const opt = document.createElement('option');
      opt.value = status;
      opt.textContent = status ? status.charAt(0).toUpperCase() + status.slice(1) : 'All statuses';
      select.appendChild(opt);
    });
    statusField.appendChild(select);
    filterForm.appendChild(statusField);

    const refreshButton = document.createElement('button');
    refreshButton.type = 'submit';
    refreshButton.textContent = 'Apply';
    filterForm.appendChild(refreshButton);

    filterForm.addEventListener('submit', (event) => {
      event.preventDefault();
      selectedStatus = select.value;
      fetchItems();
    });

    header.appendChild(filterForm);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const summaryCard = createCard({
      title: 'Visible Items',
      value: '—',
      meta: 'Total count for the current filter',
    });
    summaryCard.classList.add('grid-col-span-3');
    grid.appendChild(summaryCard);

    const statusCard = createCard({
      title: 'Status Mix',
      value: '—',
      meta: 'Breakdown of statuses',
    });
    statusCard.classList.add('grid-col-span-3');
    grid.appendChild(statusCard);

    const embeddingCard = createCard({
      title: 'Embedding Coverage',
      value: '—',
      meta: 'Items with both embeddings available',
    });
    embeddingCard.classList.add('grid-col-span-6');
    grid.appendChild(embeddingCard);

    const tableSection = document.createElement('section');
    tableSection.className = 'grid-col-span-12 card';
    grid.appendChild(tableSection);

    function updateSummary() {
      summaryCard.querySelector('.card__value').textContent = String(items.length);
      summaryCard.querySelector('.card__meta').textContent = selectedStatus
        ? `Filtered by ${selectedStatus}`
        : 'Showing latest inventory';

      const statusCounts = items.reduce((acc, item) => {
        const key = item.status || 'unknown';
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {});
      statusCard.querySelector('.card__value').textContent = `${Object.keys(statusCounts).length} statuses`;
      statusCard.querySelector('.card__meta').textContent = Object.keys(statusCounts).length
        ? Object.entries(statusCounts)
            .map(([status, count]) => `${status}: ${count}`)
            .join(' · ')
        : 'No items available';

      if (!items.length) {
        embeddingCard.querySelector('.card__value').textContent = '0%';
        embeddingCard.querySelector('.card__meta').textContent = 'No items in this view';
      } else {
        const enriched = items.filter((item) => item.image_embedding && item.description_embedding).length;
        const coverage = Math.round((enriched / items.length) * 100);
        embeddingCard.querySelector('.card__value').textContent = `${coverage}%`;
        embeddingCard.querySelector('.card__meta').textContent = `${enriched}/${items.length} enriched entries`;
      }
    }

    function renderTable() {
      tableSection.innerHTML = '';
      const heading = document.createElement('h2');
      heading.textContent = 'Catalogued Items';
      tableSection.appendChild(heading);
      const table = createTable({
        columns: [
          { label: 'ID', accessor: (row) => `#${row.item_id}` },
          { label: 'Description', accessor: (row) => row.description || row.gemini_description || '—' },
          { label: 'Status', accessor: (row) => row.status || '—' },
          { label: 'Finder', accessor: (row) => (row.finder_user_id ? `User ${row.finder_user_id}` : '—') },
          {
            label: 'Updated',
            accessor: (row) => new Date(row.updated_at || row.created_at).toLocaleString(),
          },
        ],
        rows: items,
        isLoading,
        emptyState: 'No items match the current filters.',
        onRowClick: (row) => showItemDetails(row),
      });
      tableSection.appendChild(table);
    }

    async function updateItem(itemId, payload, message) {
      try {
        const index = items.findIndex((item) => item.item_id === itemId);
        if (index !== -1) {
          items[index] = { ...items[index], ...payload };
          renderTable();
          updateSummary();
        }
        const updated = await apiClient.request(`admin/items/${itemId}`, {
          method: 'PUT',
          body: payload,
        });
        items = items.map((item) => (item.item_id === itemId ? { ...item, ...updated } : item));
        renderTable();
        updateSummary();
        if (message) {
          showToast({ title: message, type: 'success' });
        }
      } catch (error) {
        console.error('Item update failed', error);
        showToast({ title: 'Item update failed', message: error.message, type: 'error' });
        fetchItems();
      }
    }

    function showItemDetails(item) {
      const body = document.createElement('div');
      body.style.display = 'flex';
      body.style.flexDirection = 'column';
      body.style.gap = '16px';

      body.appendChild(
        createCodeBlock(item, {
          label: `Item ${item.item_id} payload`,
        })
      );

      const statusLabel = document.createElement('label');
      statusLabel.textContent = 'Status';
      const statusSelect = document.createElement('select');
      ITEM_STATUSES.filter(Boolean).forEach((status) => {
        const opt = document.createElement('option');
        opt.value = status;
        opt.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        if (status === item.status) {
          opt.selected = true;
        }
        statusSelect.appendChild(opt);
      });
      statusLabel.appendChild(statusSelect);
      body.appendChild(statusLabel);

      const descriptionLabel = document.createElement('label');
      descriptionLabel.textContent = 'Description';
      const textarea = document.createElement('textarea');
      textarea.rows = 4;
      textarea.value = item.description || '';
      descriptionLabel.appendChild(textarea);
      body.appendChild(descriptionLabel);

      const actions = [];

      const saveButton = document.createElement('button');
      saveButton.textContent = 'Save Changes';
      saveButton.addEventListener('click', () =>
        updateItem(
          item.item_id,
          {
            status: statusSelect.value,
            description: textarea.value,
          },
          'Item updated'
        )
      );
      actions.push(saveButton);

      modal.show({
        title: `Item #${item.item_id}`,
        body,
        actions,
      });
    }

    async function fetchItems() {
      isLoading = true;
      renderTable();
      try {
        const response = await apiClient.request('admin/items', {
          query: {
            page: 1,
            limit: 25,
            status: selectedStatus || undefined,
          },
        });
        items = response.data || [];
        isLoading = false;
        renderTable();
        updateSummary();
      } catch (error) {
        console.error('Failed to load items', error);
        showToast({ title: 'Unable to load items', message: error.message, type: 'error' });
      }
    }

    await fetchItems();
  },
};
