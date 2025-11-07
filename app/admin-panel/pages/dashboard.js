import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';
import { createPieChart, createBarChart } from '../components/app-charts.js';

function createHeader(title, subtitle) {
  const header = document.createElement('div');
  header.className = 'page__header';

  const h1 = document.createElement('h1');
  h1.className = 'page__title';
  h1.textContent = title;

  header.appendChild(h1);

  if (subtitle) {
    const helper = document.createElement('p');
    helper.className = 'helper-text';
    helper.textContent = subtitle;
    header.appendChild(helper);
  }

  return header;
}


export const dashboardPage = {
  route: '/dashboard',
  label: 'Dashboard',
  icon: '📊',
  async render({ root }) {
    root.innerHTML = '';
    root.className = 'page';

    root.appendChild(
      createHeader('Command Center', 'At-a-glance test health across inventory and operations.')
    );

    const metricsGrid = document.createElement('div');
    metricsGrid.className = 'page__grid';
    root.appendChild(metricsGrid);

    try {
      const [overview, boxes, cases, auditLogs] = await Promise.all([
        apiClient.request('admin/reports/overview'),
        apiClient.request('admin/boxes', { query: { limit: 5 } }),
        apiClient.request('admin/cases', { query: { limit: 5 } }),
        apiClient.request('admin/audit-logs', { query: { limit: 5, page: 1 } }),
      ]);

      metricsGrid.innerHTML = '';
      // Create summary cards
      const summaryCards = [
        createCard({
          title: 'Active Users',
          value: overview?.users?.active ?? '—',
          meta: `${overview?.users?.disabled ?? 0} disabled · ${overview?.users?.deleted ?? 0} deleted`,
          icon: '👥',
        }),
        createCard({
          title: 'Catalogued Items',
          value: overview?.items?.total ?? '—',
          meta: `${overview?.items?.deleted ?? 0} removed · ${Object.keys(overview?.items?.by_status || {}).length} statuses`,
          icon: '🎒',
        }),
        createCard({
          title: 'Open Cases',
          value: overview?.cases?.open ?? '—',
          meta: `${overview?.cases?.closed ?? 0} closed · ${overview?.cases?.overdue ?? 0} overdue`,
          icon: '📁',
        }),
        createCard({
          title: 'Operational Boxes',
          value: overview?.boxes?.online ?? '—',
          meta: `${overview?.boxes?.offline ?? 0} offline · ${overview?.boxes?.maintenance ?? 0} maintenance`,
          icon: '🗄️',
        }),
      ];
      
      summaryCards.forEach(card => {
        card.classList.add('grid-col-span-3');
        metricsGrid.appendChild(card);
      });

      // Create charts section
      // Create stats card with two pie charts
      const statsContainer = document.createElement('div');
      statsContainer.style.display = 'flex';
      statsContainer.style.gap = '20px';
      statsContainer.style.justifyContent = 'space-between';

      // Create pie chart for item status distribution
      const itemStatusData = {
        labels: Object.keys(overview?.items?.by_status || {}),
        values: Object.values(overview?.items?.by_status || {})
      };
      const itemChart = createPieChart(itemStatusData, {
        title: 'Items by Status',
        height: '250px',
        width: '50%'
      });
      itemChart.style.flex = '1';
      statsContainer.appendChild(itemChart);

      // Create pie chart for box status distribution
      const boxStatusData = {
        labels: ['Available', 'Unavailable', 'Unknown'],
        values: [
          overview?.boxes?.available || 0,
          overview?.boxes?.unavailable || 0,
          overview?.boxes?.unknown || 0
        ]
      };
      const boxChart = createPieChart(boxStatusData, {
        title: 'Box Status Distribution',
        height: '250px',
        width: '50%'
      });
      boxChart.style.flex = '1';
      statsContainer.appendChild(boxChart);

      const statsCard = createCard({
        title: 'System Status Distribution',
        body: statsContainer
      });
      statsCard.classList.add('grid-col-span-6');
      metricsGrid.appendChild(statsCard);

      // Create bar chart for cases overview
      const caseData = {
        labels: ['Open', 'Closed', 'Closed (30 Days)'],
        values: [
          overview?.cases?.open || 0,
          overview?.cases?.closed || 0,
          overview?.cases?.closed_last_30_days || 0
        ]
      };
      const caseMetricsCard = createCard({
        title: 'Case Metrics',
        body: createBarChart(caseData, {
          title: 'Case Distribution',
          label: 'Number of Cases',
          height: '250px',
          showLegend: true
        })
      });
      caseMetricsCard.classList.add('grid-col-span-6');
      metricsGrid.appendChild(caseMetricsCard);

      // Create activity section
      const activitySection = document.createElement('section');
      activitySection.className = 'grid-col-span-12 card';
      
      const recentActivity = createTable({
        columns: [
          { label: 'Timestamp', accessor: (row) => new Date(row.created_at).toLocaleString() },
          { label: 'Actor', accessor: (row) => row.actor_user_id ?? 'System' },
          { label: 'Entity', accessor: (row) => row.entity_type ?? '—' },
          { label: 'Action', accessor: (row) => row.action },
        ],
        rows: auditLogs?.data ?? [],
        emptyState: 'No recent audit trail entries.',
      });
      const activityHeader = document.createElement('h2');
      activityHeader.textContent = 'Recent Administrative Activity';
      activitySection.appendChild(activityHeader);
      activitySection.appendChild(recentActivity);
      root.appendChild(activitySection);

      const casesTable = createTable({
        columns: [
          { label: 'Case', accessor: (row) => `#${row.found_id}` },
          { label: 'Status', accessor: (row) => row.status },
          {
            label: 'Updated',
            accessor: (row) => (row.updated_at ? new Date(row.updated_at).toLocaleString() : '—'),
          },
        ],
        rows: cases?.items ?? [],
        emptyState: 'No open cases to review.',
      });
      const casesCard = createCard({
        title: 'Latest Cases',
        body: casesTable,
      });
      casesCard.classList.add('grid-col-span-6');
      metricsGrid.appendChild(casesCard);

      const boxesTable = createTable({
        columns: [
          { label: 'Box', accessor: (row) => `#${row.box_id}` },
          { label: 'Location', accessor: 'location' },
          { label: 'Door', accessor: (row) => (row.door_status ? 'Open' : 'Closed') },
          { label: 'Status', accessor: (row) => (row.status ? 'Online' : 'Offline') },
        ],
        rows: boxes?.items ?? [],
        emptyState: 'No boxes registered.',
      });
      const boxesCard = createCard({
        title: 'Smart Box Status',
        body: boxesTable,
      });
      boxesCard.classList.add('grid-col-span-12');
      metricsGrid.appendChild(boxesCard);
    } catch (error) {
      console.error('Dashboard failed to load', error);
      showToast({
        title: 'Dashboard Unavailable',
        message: error.message || 'Failed to fetch metrics.',
        type: 'error',
      });
    }
  },
};
