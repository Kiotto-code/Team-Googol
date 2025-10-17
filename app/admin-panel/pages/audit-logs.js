import { apiClient } from '../api.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { createCard } from '../components/app-card.js';
import { showToast } from '../components/app-toast.js';

export const auditLogsPage = {
  route: '/audit-logs',
  label: 'Audit Logs',
  icon: '🕵️',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    let entries = [];
    let isLoading = true;
    let page = 1;
    let totalPages = 1;
    const { modal } = context;

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Audit Logs';
    header.appendChild(title);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const summaryCard = createCard({
      title: 'Entries Loaded',
      value: '—',
      meta: 'Across pages',
    });
    summaryCard.classList.add('grid-col-span-4');
    grid.appendChild(summaryCard);

    const tableSection = document.createElement('section');
    tableSection.className = 'grid-col-span-12 card';
    grid.appendChild(tableSection);

    const loadMore = document.createElement('button');
    loadMore.type = 'button';
    loadMore.textContent = 'Load more';
    loadMore.addEventListener('click', () => {
      if (page < totalPages) {
        page += 1;
        fetchAuditLogs(true);
      }
    });

    function updateSummary() {
      summaryCard.querySelector('.card__value').textContent = String(entries.length);
      summaryCard.querySelector('.card__meta').textContent = `Page ${page} of ${totalPages}`;
    }

    function renderTable() {
      tableSection.innerHTML = '';
      const heading = document.createElement('h2');
      heading.textContent = 'Recent Activity';
      tableSection.appendChild(heading);

      const table = createTable({
        columns: [
          { label: 'ID', accessor: (row) => `#${row.audit_id}` },
          { label: 'Actor', accessor: (row) => (row.actor_user_id ? `#${row.actor_user_id}` : 'System') },
          { label: 'Entity', accessor: (row) => row.entity_type || '—' },
          { label: 'Action', accessor: (row) => row.action },
          {
            label: 'When',
            accessor: (row) => new Date(row.created_at).toLocaleString(),
          },
        ],
        rows: entries,
        isLoading,
        emptyState: 'No audit events yet.',
        onRowClick: (row) =>
          modal.show({
            title: `Audit #${row.audit_id}`,
            body: createCodeBlock(row, { label: 'Audit payload' }),
          }),
      });
      tableSection.appendChild(table);
      if (page < totalPages) {
        tableSection.appendChild(loadMore);
      }
    }

    async function fetchAuditLogs(append = false) {
      isLoading = true;
      renderTable();
      try {
        const response = await apiClient.request('admin/audit-logs', {
          query: {
            page,
            limit: 25,
          },
        });
        totalPages = response.meta?.total_pages || 1;
        entries = append ? [...entries, ...(response.data || [])] : response.data || [];
        isLoading = false;
        renderTable();
        updateSummary();
      } catch (error) {
        console.error('Failed to load audit logs', error);
        showToast({ title: 'Unable to load audit logs', message: error.message, type: 'error' });
      }
    }

    await fetchAuditLogs();
  },
};
