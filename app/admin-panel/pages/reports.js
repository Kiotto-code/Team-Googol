import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

export const reportsPage = {
  route: '/reports',
  label: 'Reports',
  icon: '📊',
  async render({ root }) {
    root.innerHTML = '';
    root.className = 'page';

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Reports';
    header.appendChild(title);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const overviewCard = createCard({
      title: 'Overview Report',
      meta: 'Key metrics snapshot',
      body: 'Loading…',
    });
    overviewCard.classList.add('grid-col-span-6');
    grid.appendChild(overviewCard);

    const utilizationCard = createCard({
      title: 'Box Utilization',
      meta: 'Per-box capacity metrics',
      body: 'Loading…',
    });
    utilizationCard.classList.add('grid-col-span-6');
    grid.appendChild(utilizationCard);

    let overview = null;
    let utilization = null;

    const downloadButton = document.createElement('button');
    downloadButton.type = 'button';
    downloadButton.textContent = 'Download JSON bundle';
    downloadButton.addEventListener('click', async () => {
      try {
        const data = {
          overview,
          boxes: utilization,
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `admin-reports-${Date.now()}.json`;
        anchor.click();
        URL.revokeObjectURL(url);
      } catch (error) {
        showToast({ title: 'Export failed', message: error.message, type: 'error' });
      }
    });
    root.appendChild(downloadButton);

    try {
      [overview, utilization] = await Promise.all([
        apiClient.request('admin/reports/overview'),
        apiClient.request('admin/reports/boxes-utilization'),
      ]);

      overviewCard.querySelector('.card__body').replaceChildren(
        createCodeBlock(overview, { label: 'Overview report' })
      );
      overviewCard.querySelector('.card__meta').textContent = `Generated at ${new Date(
        overview.generated_at
      ).toLocaleString()}`;

      utilizationCard.querySelector('.card__body').replaceChildren(
        createCodeBlock(utilization, { label: 'Box utilization report' })
      );
      utilizationCard.querySelector('.card__meta').textContent = `${utilization.totals.active_boxes} active boxes · ${utilization.totals.total_cases} cases tracked`;
    } catch (error) {
      console.error('Failed to load reports', error);
      overviewCard.querySelector('.card__body').textContent = 'Failed to load overview report.';
      utilizationCard.querySelector('.card__body').textContent = 'Failed to load utilization report.';
      showToast({ title: 'Reports unavailable', message: error.message, type: 'error' });
    }
  },
};
