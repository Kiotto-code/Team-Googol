import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

function createHeader(root, onRefresh) {
  const header = document.createElement('div');
  header.className = 'page__header';

  const title = document.createElement('h1');
  title.className = 'page__title';
  title.textContent = 'Smart Boxes';

  const actionGroup = document.createElement('div');
  actionGroup.className = 'topbar__group';

  const refreshButton = document.createElement('button');
  refreshButton.type = 'button';
  refreshButton.textContent = 'Refresh';
  refreshButton.addEventListener('click', onRefresh);

  actionGroup.appendChild(refreshButton);
  header.appendChild(title);
  header.appendChild(actionGroup);
  root.appendChild(header);

  return { refreshButton };
}

function createWebSocketConnection(onMessage, onStatus) {
  if (!apiClient.accessToken) {
    return { close() {} };
  }
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${protocol}://${window.location.host}/api/v1/admin/ws/boxes?token=${encodeURIComponent(
    apiClient.accessToken
  )}`;

  let socket;
  let retryTimer;
  let closed = false;

  function connect(delay = 0) {
    if (closed) return;
    window.clearTimeout(retryTimer);
    retryTimer = window.setTimeout(() => {
      socket = new WebSocket(url);
      socket.addEventListener('open', () => onStatus('connected'));
      socket.addEventListener('close', () => {
        onStatus('disconnected');
        if (!closed) {
          connect(1500);
        }
      });
      socket.addEventListener('error', () => socket.close());
      socket.addEventListener('message', (event) => {
        try {
          const payload = JSON.parse(event.data);
          onMessage(payload);
        } catch (error) {
          console.warn('Telemetry message parse failure', error);
        }
      });
    }, delay);
  }

  connect();

  return {
    close() {
      closed = true;
      window.clearTimeout(retryTimer);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    },
  };
}

export const boxesPage = {
  route: '/boxes',
  label: 'Boxes',
  icon: '🗄️',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    let boxes = [];
    let isLoading = true;
    const { modal } = context;

    const socketStatus = document.createElement('span');
    socketStatus.className = 'helper-text';
    socketStatus.textContent = 'Realtime: connecting…';

    const { refreshButton } = createHeader(root, () => fetchBoxes());
    root.appendChild(socketStatus);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const summaryCard = createCard({
      title: 'Fleet Summary',
      value: '—',
      meta: 'Total boxes · Online vs offline',
    });
    summaryCard.classList.add('grid-col-span-4');
    grid.appendChild(summaryCard);

    const loadCard = createCard({
      title: 'Average Load',
      value: '—',
      meta: 'Across connected boxes',
    });
    loadCard.classList.add('grid-col-span-4');
    grid.appendChild(loadCard);

    const doorCard = createCard({
      title: 'Doors Open',
      value: '—',
      meta: 'Live snapshot from telemetry',
    });
    doorCard.classList.add('grid-col-span-4');
    grid.appendChild(doorCard);

    const tableContainer = document.createElement('section');
    tableContainer.className = 'grid-col-span-12 card';
    grid.appendChild(tableContainer);

    function updateSummary() {
      if (!boxes.length) {
        summaryCard.querySelector('.card__value').textContent = '0';
        summaryCard.querySelector('.card__meta').textContent = 'No boxes registered';
        loadCard.querySelector('.card__value').textContent = '—';
        loadCard.querySelector('.card__meta').textContent = 'Waiting for telemetry';
        doorCard.querySelector('.card__value').textContent = '0';
        doorCard.querySelector('.card__meta').textContent = 'All doors closed';
        return;
      }
      const online = boxes.filter((box) => box.status).length;
      const offline = boxes.length - online;
      summaryCard.querySelector('.card__value').textContent = String(boxes.length);
      summaryCard.querySelector(
        '.card__meta'
      ).textContent = `${online} online · ${offline} offline`;

      const loads = boxes.map((box) => Number(box.load || 0));
      const averageLoad = loads.reduce((sum, value) => sum + value, 0) / loads.length;
      loadCard.querySelector('.card__value').textContent = `${Math.round(averageLoad)}%`;
      loadCard.querySelector('.card__meta').textContent = 'Smarter placements yield shorter pickup times';

      const openDoors = boxes.filter((box) => box.door_status).length;
      doorCard.querySelector('.card__value').textContent = String(openDoors);
      doorCard.querySelector(
        '.card__meta'
      ).textContent = `${openDoors} open · ${boxes.length - openDoors} closed`;
    }

    function renderTable() {
      tableContainer.innerHTML = '';
      const title = document.createElement('h2');
      title.textContent = 'Registered Boxes';
      tableContainer.appendChild(title);

      const table = createTable({
        columns: [
          { label: 'ID', accessor: (row) => `#${row.box_id}` },
          { label: 'Location', accessor: 'location' },
          { label: 'Status', accessor: (row) => (row.status ? 'Online' : 'Offline') },
          { label: 'Door', accessor: (row) => (row.door_status ? 'Open' : 'Closed') },
          {
            label: 'Load',
            accessor: (row) => (row.load != null ? `${row.load}%` : '—'),
          },
          {
            label: 'Last Accessed',
            accessor: (row) => (row.last_accessed ? new Date(row.last_accessed).toLocaleString() : '—'),
          },
        ],
        rows: boxes,
        emptyState: 'No boxes found. Use the API to register a box.',
        isLoading,
        onRowClick: (row) => showBoxDetails(row),
      });
      tableContainer.appendChild(table);
    }

    async function mutateBox(boxId, action, request) {
      try {
        refreshButton.disabled = true;
        const optimisticIndex = boxes.findIndex((box) => box.box_id === boxId);
        if (optimisticIndex !== -1) {
          boxes[optimisticIndex] = { ...boxes[optimisticIndex], ...action.optimistic };
          renderTable();
          updateSummary();
        }
        const response = await request();
        if (response) {
          boxes = boxes.map((box) => (box.box_id === boxId ? { ...box, ...response } : box));
          renderTable();
          updateSummary();
        }
        showToast({ title: action.message, type: 'success' });
      } catch (error) {
        console.error('Box mutation failed', error);
        showToast({
          title: 'Box action failed',
          message: error.message,
          type: 'error',
        });
        fetchBoxes();
      } finally {
        refreshButton.disabled = false;
      }
    }

    function showBoxDetails(box) {
      const body = document.createElement('div');
      body.style.display = 'flex';
      body.style.flexDirection = 'column';
      body.style.gap = '16px';

      const metaTable = document.createElement('div');
      metaTable.appendChild(
        createCodeBlock(
          {
            id: box.box_id,
            location: box.location,
            status: box.status,
            door_status: box.door_status,
            load: box.load,
            last_accessed: box.last_accessed,
          },
          { label: 'Box snapshot' }
        )
      );
      body.appendChild(metaTable);

      const actions = [];

      const toggleDoor = document.createElement('button');
      toggleDoor.textContent = box.door_status ? 'Close Door' : 'Open Door';
      toggleDoor.addEventListener('click', () => {
        mutateBox(box.box_id, {
          optimistic: { door_status: !box.door_status },
          message: 'Door command sent',
        }, async () =>
          apiClient.request(`admin/boxes/${box.box_id}:${box.door_status ? 'close-door' : 'open-door'}`, {
            method: 'POST',
          })
        );
      });
      actions.push(toggleDoor);

      const pingButton = document.createElement('button');
      pingButton.textContent = 'Ping Box';
      pingButton.addEventListener('click', () => {
        mutateBox(
          box.box_id,
          {
            optimistic: {},
            message: 'Ping dispatched',
          },
          async () => apiClient.request(`admin/boxes/${box.box_id}:ping`, { method: 'POST' })
        );
      });
      actions.push(pingButton);

      const statusButton = document.createElement('button');
      statusButton.textContent = box.status ? 'Mark Offline' : 'Mark Online';
      statusButton.addEventListener('click', () => {
        mutateBox(
          box.box_id,
          {
            optimistic: { status: !box.status },
            message: 'Status update queued',
          },
          async () =>
            apiClient.request(`admin/boxes/${box.box_id}`, {
              method: 'PUT',
              body: { status: !box.status },
            })
        );
      });
      actions.push(statusButton);

      modal.show({
        title: `Box #${box.box_id}`,
        body,
        actions,
      });
    }

    async function fetchBoxes() {
      isLoading = true;
      renderTable();
      try {
        const response = await apiClient.request('admin/boxes', { query: { limit: 100, offset: 0 } });
        boxes = response.items || [];
        isLoading = false;
        renderTable();
        updateSummary();
      } catch (error) {
        console.error('Failed to load boxes', error);
        showToast({
          title: 'Unable to load boxes',
          message: error.message,
          type: 'error',
        });
      }
    }

    const connection = createWebSocketConnection(
      (message) => {
        if (message?.type === 'telemetry' && message?.box_id) {
          boxes = boxes.map((box) =>
            box.box_id === message.box_id
              ? {
                  ...box,
                  door_status: message.telemetry?.door_status ?? box.door_status,
                  status: message.telemetry?.status ?? box.status,
                  load: message.telemetry?.payload?.load ?? box.load,
                  last_accessed: message.telemetry?.recorded_at ?? box.last_accessed,
                }
              : box
          );
          renderTable();
          updateSummary();
        }
      },
      (status) => {
        socketStatus.textContent = `Realtime: ${status}`;
      }
    );

    await fetchBoxes();

    return () => {
      connection.close();
    };
  },
};
