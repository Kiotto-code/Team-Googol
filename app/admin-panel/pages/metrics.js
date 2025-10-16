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

    // Overview KPI cards row
    const usersCard = createCard({ title: 'Users', body: 'Loading…' });
    usersCard.classList.add('grid-col-span-3');
    const itemsCard = createCard({ title: 'Items', body: 'Loading…' });
    itemsCard.classList.add('grid-col-span-3');
    const casesCard = createCard({ title: 'Cases', body: 'Loading…' });
    casesCard.classList.add('grid-col-span-3');
    const boxesCard = createCard({ title: 'Boxes', body: 'Loading…' });
    boxesCard.classList.add('grid-col-span-3');
    grid.appendChild(usersCard);
    grid.appendChild(itemsCard);
    grid.appendChild(casesCard);
    grid.appendChild(boxesCard);

    const promCard = createCard({
      title: 'Prometheus Export',
      body: 'Loading…',
      meta: 'Scrape endpoint: /api/v1/admin/metrics',
    });
    promCard.classList.add('grid-col-span-12');
    // Add a copy action
    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.textContent = 'Copy payload';
    promCard.querySelector('.card__header')?.appendChild(copyBtn);
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
        copyBtn.onclick = async () => {
          try {
            await navigator.clipboard.writeText(text);
            showToast({ title: 'Copied metrics payload', type: 'success' });
          } catch (e) {
            showToast({ title: 'Copy failed', message: 'Clipboard not available', type: 'warning' });
          }
        };
      } catch (error) {
        console.error('Failed to load metrics', error);
        promCard.querySelector('.card__body').textContent = 'Unable to fetch metrics.';
        showToast({ title: 'Metrics unavailable', message: error.message, type: 'error' });
      } finally {
        refreshButton.disabled = false;
      }
    }

    async function fetchOverview() {
      try {
        const data = await apiClient.request('admin/reports/overview');
        const { users, items, cases, boxes, generated_at } = data || {};

        // Users
        const usersBody = document.createElement('div');
        const usersValue = document.createElement('div');
        usersValue.className = 'card__value';
        usersValue.textContent = String(users?.total ?? '0');
        const usersMeta = document.createElement('p');
        usersMeta.className = 'card__meta';
        usersMeta.textContent = `active ${users?.active ?? 0} · disabled ${users?.disabled ?? 0} · deleted ${users?.deleted ?? 0}`;
        usersBody.appendChild(usersValue);
        usersBody.appendChild(usersMeta);
        usersCard.querySelector('.card__body').replaceChildren(usersBody);

        // Items
        const itemsBody = document.createElement('div');
        const itemsValue = document.createElement('div');
        itemsValue.className = 'card__value';
        itemsValue.textContent = String(items?.total ?? '0');
        const itemsMeta = document.createElement('p');
        itemsMeta.className = 'card__meta';
        const byStatus = items?.by_status ? Object.entries(items.by_status).map(([k, v]) => `${k}: ${v}`).join(' · ') : '—';
        itemsMeta.textContent = `deleted ${items?.deleted ?? 0} · ${byStatus}`;
        itemsBody.appendChild(itemsValue);
        itemsBody.appendChild(itemsMeta);
        itemsCard.querySelector('.card__body').replaceChildren(itemsBody);

        // Cases
        const casesBody = document.createElement('div');
        const casesValue = document.createElement('div');
        casesValue.className = 'card__value';
        casesValue.textContent = String(cases?.total ?? '0');
        const casesMeta = document.createElement('p');
        casesMeta.className = 'card__meta';
        const avgHrs = cases?.average_resolution_hours != null ? `${cases.average_resolution_hours.toFixed(1)}h avg` : 'no data';
        casesMeta.textContent = `open ${cases?.open ?? 0} · closed ${cases?.closed ?? 0} · 30d closed ${cases?.closed_last_30_days ?? 0} · ${avgHrs}`;
        casesBody.appendChild(casesValue);
        casesBody.appendChild(casesMeta);
        casesCard.querySelector('.card__body').replaceChildren(casesBody);

        // Boxes
        const boxesBody = document.createElement('div');
        const boxesValue = document.createElement('div');
        boxesValue.className = 'card__value';
        boxesValue.textContent = String(boxes?.total ?? '0');
        const boxesMeta = document.createElement('p');
        boxesMeta.className = 'card__meta';
  const avgLoad = boxes?.average_load != null ? `${boxes.average_load.toFixed(0)}% avg load` : 'avg load —';
        boxesMeta.textContent = `available ${boxes?.available ?? 0} · unavailable ${boxes?.unavailable ?? 0} · unknown ${boxes?.unknown ?? 0} · active cases ${boxes?.with_active_cases ?? 0} · doors open ${boxes?.doors_open ?? 0} · ${avgLoad}`;
        boxesBody.appendChild(boxesValue);
        boxesBody.appendChild(boxesMeta);
        boxesCard.querySelector('.card__body').replaceChildren(boxesBody);

  // Timestamp available in payload if needed: generated_at
      } catch (error) {
        console.error('Failed to load overview', error);
        showToast({ title: 'Overview unavailable', message: error.message, type: 'error' });
      }
    }

    refreshButton.addEventListener('click', fetchMetrics);
    refreshButton.addEventListener('click', fetchOverview);
    await Promise.all([fetchOverview(), fetchMetrics()]);
  },
};
