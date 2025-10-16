import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'open', label: 'Open' },
  { value: 'claimed', label: 'Claimed' },
  { value: 'retrieved', label: 'Retrieved' },
  { value: 'expired', label: 'Expired' },
  { value: 'forfeited', label: 'Forfeited' },
];

export const casesPage = {
  route: '/cases',
  label: 'Cases',
  icon: '📁',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    let cases = [];
    let isLoading = true;
    let selectedStatus = '';
    const { modal } = context;

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Cases';
    header.appendChild(title);

    const filterForm = document.createElement('form');
    filterForm.setAttribute('aria-label', 'Filter cases');
    filterForm.style.flexDirection = 'row';
    filterForm.style.gap = '12px';
    filterForm.style.alignItems = 'flex-end';

    const statusField = document.createElement('label');
    statusField.textContent = 'Status';
    const select = document.createElement('select');
    STATUS_OPTIONS.forEach((option) => {
      const opt = document.createElement('option');
      opt.value = option.value;
      opt.textContent = option.label;
      select.appendChild(opt);
    });
    statusField.appendChild(select);
    filterForm.appendChild(statusField);

    const applyButton = document.createElement('button');
    applyButton.type = 'submit';
    applyButton.textContent = 'Apply';
    filterForm.appendChild(applyButton);

    filterForm.addEventListener('submit', (event) => {
      event.preventDefault();
      selectedStatus = select.value;
      fetchCases();
    });

    header.appendChild(filterForm);
    root.appendChild(header);

    const statsGrid = document.createElement('div');
    statsGrid.className = 'page__grid';
    root.appendChild(statsGrid);

    const summaryCard = createCard({
      title: 'Overview',
      value: '—',
      meta: 'Cases grouped by status',
    });
    summaryCard.classList.add('grid-col-span-4');
    statsGrid.appendChild(summaryCard);

    const terminalCard = createCard({
      title: 'Terminal Cases',
      value: '—',
      meta: 'Retrieved · Expired · Forfeited',
    });
    terminalCard.classList.add('grid-col-span-4');
    statsGrid.appendChild(terminalCard);

    const agingCard = createCard({
      title: 'Oldest Open Case',
      value: '—',
      meta: 'Age in days',
    });
    agingCard.classList.add('grid-col-span-4');
    statsGrid.appendChild(agingCard);

    const tableSection = document.createElement('section');
    tableSection.className = 'grid-col-span-12 card';
    statsGrid.appendChild(tableSection);

    function updateSummary() {
      if (!cases.length) {
        summaryCard.querySelector('.card__value').textContent = '0';
        summaryCard.querySelector('.card__meta').textContent = 'No matching cases';
        terminalCard.querySelector('.card__value').textContent = '0';
        terminalCard.querySelector('.card__meta').textContent = 'No terminal cases';
        agingCard.querySelector('.card__value').textContent = '—';
        agingCard.querySelector('.card__meta').textContent = 'No open cases pending';
        return;
      }
      summaryCard.querySelector('.card__value').textContent = String(cases.length);
      summaryCard.querySelector('.card__meta').textContent = `Filtered by ${selectedStatus || 'any status'}`;

      const terminalStatuses = ['retrieved', 'expired', 'forfeited'];
      const terminalCases = cases.filter((entry) => terminalStatuses.includes(entry.status));
      terminalCard.querySelector('.card__value').textContent = String(terminalCases.length);
      const terminalCounts = terminalCases
        .map((entry) => entry.status)
        .reduce((acc, status) => ({ ...acc, [status]: (acc[status] || 0) + 1 }), {});
      terminalCard.querySelector('.card__meta').textContent = Object.keys(terminalCounts).length
        ? Object.entries(terminalCounts)
            .map(([status, count]) => `${status}: ${count}`)
            .join(' · ')
        : 'No terminal cases yet';

      const openCases = cases.filter((entry) => entry.status === 'open' || entry.status === 'claimed');
      if (openCases.length) {
        const sorted = [...openCases].sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        const oldest = sorted[0];
        const days = Math.max(
          0,
          Math.round((Date.now() - new Date(oldest.created_at).getTime()) / (1000 * 60 * 60 * 24))
        );
        agingCard.querySelector('.card__value').textContent = `${days}d`;
        agingCard.querySelector('.card__meta').textContent = `Case #${oldest.found_id} opened ${new Date(
          oldest.created_at
        ).toLocaleString()}`;
      } else {
        agingCard.querySelector('.card__value').textContent = '—';
        agingCard.querySelector('.card__meta').textContent = 'No open or claimed cases';
      }
    }

    function renderTable() {
      tableSection.innerHTML = '';
      const heading = document.createElement('h2');
      heading.textContent = 'Case Queue';
      tableSection.appendChild(heading);
      const table = createTable({
        columns: [
          { label: 'Case', accessor: (row) => `#${row.found_id}` },
          { label: 'Status', accessor: (row) => row.status },
          { label: 'Box', accessor: (row) => (row.box_id ? `#${row.box_id}` : '—') },
          {
            label: 'Opened',
            accessor: (row) => new Date(row.created_at).toLocaleString(),
          },
          {
            label: 'Remarks',
            accessor: (row) => row.remarks ?? '—',
          },
        ],
        rows: cases,
        isLoading,
        emptyState: 'No cases match the current filters.',
        onRowClick: (row) => showCaseDetails(row),
      });
      tableSection.appendChild(table);
    }

    async function mutateCase(caseId, actionLabel, endpoint, payload) {
      try {
        const optimisticIndex = cases.findIndex((entry) => entry.found_id === caseId);
        if (optimisticIndex !== -1) {
          cases[optimisticIndex] = { ...cases[optimisticIndex], ...payload };
          renderTable();
          updateSummary();
        }
        const updated = await apiClient.request(`admin/cases/${caseId}${endpoint}`, {
          method: 'POST',
          body: payload,
        });
        cases = cases.map((entry) => (entry.found_id === caseId ? { ...entry, ...updated } : entry));
        renderTable();
        updateSummary();
        showToast({ title: actionLabel, type: 'success' });
      } catch (error) {
        console.error('Case action failed', error);
        showToast({ title: 'Case action failed', message: error.message, type: 'error' });
        fetchCases();
      }
    }

    function showCaseDetails(caseEntry) {
      const body = document.createElement('div');
      body.style.display = 'flex';
      body.style.flexDirection = 'column';
      body.style.gap = '16px';
      body.appendChild(
        createCodeBlock(caseEntry, {
          label: `Case ${caseEntry.found_id} details`,
        })
      );

      const remarksLabel = document.createElement('label');
      remarksLabel.textContent = 'Internal Remarks';
      const textarea = document.createElement('textarea');
      textarea.rows = 4;
      textarea.value = caseEntry.remarks || '';
      remarksLabel.appendChild(textarea);
      body.appendChild(remarksLabel);

      const actions = [];

      const saveRemarks = document.createElement('button');
      saveRemarks.textContent = 'Save Remarks';
      saveRemarks.addEventListener('click', async () => {
        try {
          await apiClient.request(`admin/cases/${caseEntry.found_id}`, {
            method: 'PUT',
            body: { remarks: textarea.value },
          });
          caseEntry.remarks = textarea.value;
          cases = cases.map((entry) =>
            entry.found_id === caseEntry.found_id ? { ...entry, remarks: textarea.value } : entry
          );
          renderTable();
          showToast({ title: 'Remarks updated', type: 'success' });
        } catch (error) {
          showToast({ title: 'Failed to update remarks', message: error.message, type: 'error' });
        }
      });
      actions.push(saveRemarks);

      const claimButton = document.createElement('button');
      claimButton.textContent = 'Mark as Claimed';
      claimButton.addEventListener('click', () =>
        mutateCase(caseEntry.found_id, 'Case claimed', ':claim', {
          remarks: textarea.value || caseEntry.remarks,
          reciver_id: caseEntry.reciver_id,
        })
      );
      actions.push(claimButton);

      const retrieveButton = document.createElement('button');
      retrieveButton.textContent = 'Mark as Retrieved';
      retrieveButton.addEventListener('click', () =>
        mutateCase(caseEntry.found_id, 'Case retrieved', ':retrieve', {
          remarks: textarea.value || caseEntry.remarks,
          reciver_id: caseEntry.reciver_id,
        })
      );
      actions.push(retrieveButton);

      const expireButton = document.createElement('button');
      expireButton.textContent = 'Expire Case';
      expireButton.addEventListener('click', () =>
        mutateCase(caseEntry.found_id, 'Case expired', ':expire', {
          remarks: textarea.value || caseEntry.remarks,
        })
      );
      actions.push(expireButton);

      const forfeitButton = document.createElement('button');
      forfeitButton.textContent = 'Forfeit Case';
      forfeitButton.addEventListener('click', () =>
        mutateCase(caseEntry.found_id, 'Case forfeited', ':forfeit', {
          remarks: textarea.value || caseEntry.remarks,
        })
      );
      actions.push(forfeitButton);

      modal.show({
        title: `Case #${caseEntry.found_id}`,
        body,
        actions,
      });
    }

    async function fetchCases() {
      isLoading = true;
      renderTable();
      try {
        const response = await apiClient.request('admin/cases', {
          query: {
            limit: 50,
            offset: 0,
            status: selectedStatus || undefined,
          },
        });
        cases = response.items || [];
        isLoading = false;
        renderTable();
        updateSummary();
      } catch (error) {
        console.error('Failed to load cases', error);
        showToast({ title: 'Unable to load cases', message: error.message, type: 'error' });
      }
    }

    await fetchCases();
  },
};
