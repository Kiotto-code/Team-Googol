import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

export const metricsPage = {
  route: '/metrics',
  label: 'Metrics',
  icon: '📈',
  async render({ root }) {
    root.innerHTML = '';
    root.className = 'page';

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Metrics';
    header.appendChild(title);

    const refreshButton = document.createElement('button');
    refreshButton.type = 'button';
    refreshButton.textContent = 'Refresh';
    header.appendChild(refreshButton);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const promCard = createCard({
      title: 'Prometheus Export',
      body: 'Loading…',
      meta: 'Scrape endpoint: /api/v1/admin/metrics',
    });
    promCard.classList.add('grid-col-span-12');
    grid.appendChild(promCard);

    async function fetchMetrics() {
      try {
        refreshButton.disabled = true;
        const response = await fetch(`${apiClient.API_BASE}/admin/metrics`, {
          headers: apiClient.buildHeaders(new Headers({ Accept: 'text/plain' })),
        });
        if (!response.ok) {
          throw new Error('Metrics endpoint returned an error');
        }
        const text = await response.text();
        promCard.querySelector('.card__body').replaceChildren(
          createCodeBlock(text, { language: 'prometheus', label: 'Prometheus payload' })
        );
        promCard.querySelector('.card__meta').textContent = `Last fetched ${new Date().toLocaleTimeString()}`;
      } catch (error) {
        console.error('Failed to load metrics', error);
        promCard.querySelector('.card__body').textContent = 'Unable to fetch metrics.';
        showToast({ title: 'Metrics unavailable', message: error.message, type: 'error' });
      } finally {
        refreshButton.disabled = false;
      }
    }

    refreshButton.addEventListener('click', fetchMetrics);
    await fetchMetrics();
  },
};
