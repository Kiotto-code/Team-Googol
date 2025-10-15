const TOKEN_STORAGE_KEY = 'adminAccessToken';
const REFRESH_STORAGE_KEY = 'adminRefreshToken';
const POLL_INTERVAL_MS = 20000;
const REFRESH_INTERVAL_MS = 14 * 60 * 1000;

const loginPanel = document.getElementById('login-panel');
const dashboardContent = document.getElementById('dashboard-content');
const loginForm = document.getElementById('admin-login-form');
const loginStatus = document.getElementById('login-status');
const logoutButton = document.getElementById('logout-button');
const userDisplayName = document.getElementById('user-display-name');

const usersTotalEl = document.getElementById('data-users-total');
const itemsTotalEl = document.getElementById('data-items-total');
const casesOpenEl = document.getElementById('data-cases-open');
const boxesTotalEl = document.getElementById('data-boxes-total');
const overviewUpdatedEl = document.getElementById('overview-updated-at');
const boxesUpdatedEl = document.getElementById('boxes-updated-at');
const casesUpdatedEl = document.getElementById('cases-updated-at');
const boxesTableBody = document.getElementById('boxes-table-body');
const openCasesTableBody = document.getElementById('open-cases-table-body');
const recentActivityList = document.getElementById('recent-activity-list');
const auditLogList = document.getElementById('audit-log-list');
const readyzStatusEl = document.getElementById('readyz-status');
const readyzCheckedAtEl = document.getElementById('readyz-checked-at');
const systemHealthStatusEl = document.getElementById('system-health-status');

let pollingTimer = null;
let refreshTimer = null;
let isAuthenticating = false;

function getStoredTokens() {
  return {
    accessToken: localStorage.getItem(TOKEN_STORAGE_KEY),
    refreshToken: localStorage.getItem(REFRESH_STORAGE_KEY),
  };
}

function storeTokens(tokens) {
  if (tokens?.access_token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
  }
  if (tokens?.refresh_token) {
    localStorage.setItem(REFRESH_STORAGE_KEY, tokens.refresh_token);
  }
}

function clearTokens() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(REFRESH_STORAGE_KEY);
}

function setLoginStatus(message, variant = '') {
  if (!loginStatus) return;
  loginStatus.textContent = message ?? '';
  loginStatus.classList.remove('is-error', 'is-success');
  if (variant) {
    loginStatus.classList.add(variant);
  }
}

function toggleAuthUI(isAuthenticated) {
  if (isAuthenticated) {
    document.body.classList.add('is-authenticated');
    dashboardContent?.classList.remove('is-hidden');
    if (loginPanel) loginPanel.hidden = true;
  } else {
    document.body.classList.remove('is-authenticated');
    dashboardContent?.classList.add('is-hidden');
    if (loginPanel) loginPanel.hidden = false;
  }
}

async function authorizedFetch(input, init = {}, retry = true) {
  const tokens = getStoredTokens();
  const headers = new Headers(init.headers || {});
  if (tokens.accessToken) {
    headers.set('Authorization', `Bearer ${tokens.accessToken}`);
  }
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401 && retry && tokens.refreshToken) {
    const refreshed = await refreshSession();
    if (refreshed) {
      return authorizedFetch(input, init, false);
    }
  }
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    const errorText = await safeReadError(response);
    throw new Error(errorText || `${response.status} ${response.statusText}`);
  }
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

async function safeReadError(response) {
  try {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data = await response.json();
      return data.detail || JSON.stringify(data);
    }
    return await response.text();
  } catch (error) {
    console.error('Failed to parse error response', error);
    return '';
  }
}

async function login(credentials) {
  isAuthenticating = true;
  setLoginStatus('Verifying credentials…');
  try {
    const response = await fetch('/api/v1/admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (!response.ok) {
      const errorText = await safeReadError(response);
      throw new Error(errorText || 'Authentication failed');
    }
    const data = await response.json();
    storeTokens(data);
    setLoginStatus('Authenticated successfully.', 'is-success');
    await initializeSession();
  } catch (error) {
    console.error('Login error', error);
    setLoginStatus(error.message || 'Unable to authenticate.', 'is-error');
    toggleAuthUI(false);
  } finally {
    isAuthenticating = false;
  }
}

async function refreshSession() {
  const { refreshToken } = getStoredTokens();
  if (!refreshToken) {
    return false;
  }
  try {
    const response = await fetch('/api/v1/admin/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${refreshToken}`,
      },
    });
    if (!response.ok) {
      throw new Error(await safeReadError(response));
    }
    const data = await response.json();
    storeTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token ?? refreshToken,
    });
    scheduleTokenRefresh();
    return true;
  } catch (error) {
    console.error('Failed to refresh session', error);
    handleUnauthorized();
    return false;
  }
}

function scheduleTokenRefresh() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
  }
  refreshTimer = setTimeout(() => {
    refreshSession().catch((error) => {
      console.error('Automatic refresh failed', error);
    });
  }, REFRESH_INTERVAL_MS);
}

async function initializeSession() {
  try {
    toggleAuthUI(true);
    await fetchProfile();
    await pollEndpoints();
    startPolling();
    scheduleTokenRefresh();
  } catch (error) {
    console.error('Failed to initialize session', error);
    handleUnauthorized(error.message);
  }
}

async function fetchProfile() {
  const profile = await authorizedFetch('/api/v1/admin/auth/me');
  if (profile?.full_name) {
    userDisplayName.textContent = profile.full_name;
  } else if (profile?.username) {
    userDisplayName.textContent = profile.username;
  } else {
    userDisplayName.textContent = 'Administrator';
  }
}

function startPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
  }
  pollingTimer = setInterval(() => {
    pollEndpoints().catch((error) => {
      console.error('Polling error', error);
    });
  }, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

async function pollEndpoints() {
  await Promise.all([
    fetchOverviewReport(),
    fetchBoxesUtilization(),
    fetchReadyzStatus(),
  ]);
}

async function fetchOverviewReport() {
  try {
    const overview = await authorizedFetch('/api/v1/admin/reports/overview');
    updateOverview(overview);
  } catch (error) {
    console.error('Overview fetch failed', error);
  }
}

async function fetchBoxesUtilization() {
  try {
    const data = await authorizedFetch('/api/v1/admin/reports/boxes-utilization');
    updateBoxesTable(Array.isArray(data) ? data : data?.results || []);
  } catch (error) {
    console.error('Boxes utilization fetch failed', error);
  }
}

async function fetchReadyzStatus() {
  try {
    const status = await authorizedFetch('/api/v1/readyz');
    updateHealthStatus(status);
  } catch (error) {
    console.error('Readyz fetch failed', error);
    updateHealthStatus({ ok: false, detail: error.message });
  }
}

function updateOverview(overview) {
  if (!overview || typeof overview !== 'object') {
    return;
  }
  setMetric(usersTotalEl, overview.users_total ?? overview.users ?? '—');
  setMetric(itemsTotalEl, overview.items_total ?? overview.items ?? '—');
  setMetric(casesOpenEl, overview.cases_open ?? overview.open_cases_total ?? '—');
  setMetric(boxesTotalEl, overview.boxes_total ?? overview.boxes ?? '—');

  if (overview.timestamp || overview.updated_at) {
    setTimestamp(overviewUpdatedEl, overview.timestamp || overview.updated_at);
  } else {
    setTimestamp(overviewUpdatedEl, new Date().toISOString());
  }

  updateActivityList(recentActivityList, overview.recent_activity);
  updateActivityList(auditLogList, overview.audit_log);
  updateCasesTable(overview.open_cases);
}

function setMetric(element, value) {
  if (!element) return;
  if (value === null || value === undefined || value === '') {
    element.textContent = '—';
    return;
  }
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    element.textContent = numberValue.toLocaleString();
  } else {
    element.textContent = String(value);
  }
}

function setTimestamp(element, value) {
  if (!element) return;
  try {
    const date = value ? new Date(value) : new Date();
    if (Number.isNaN(date.getTime())) {
      element.textContent = '—';
      element.dateTime = '';
      return;
    }
    element.textContent = date.toLocaleString();
    element.dateTime = date.toISOString();
  } catch (error) {
    element.textContent = '—';
    element.dateTime = '';
  }
}

function updateActivityList(container, entries) {
  if (!container) return;
  container.innerHTML = '';
  if (!Array.isArray(entries) || entries.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'empty-state';
    empty.textContent = 'No records available.';
    container.appendChild(empty);
    return;
  }
  entries.forEach((entry) => {
    const item = document.createElement('li');
    if (typeof entry === 'string') {
      item.textContent = entry;
    } else if (entry && typeof entry === 'object') {
      item.textContent = formatActivityEntry(entry);
    } else {
      item.textContent = String(entry);
    }
    container.appendChild(item);
  });
}

function formatActivityEntry(entry) {
  const time = entry.timestamp || entry.time || entry.created_at;
  const actor = entry.actor || entry.user || entry.owner;
  const action = entry.action || entry.event || entry.summary;
  const context = entry.context || entry.details || entry.description;
  const parts = [];
  if (time) {
    parts.push(`[${new Date(time).toLocaleString()}]`);
  }
  if (actor) {
    parts.push(actor);
  }
  if (action) {
    parts.push(action);
  }
  if (context) {
    parts.push(`– ${context}`);
  }
  return parts.length ? parts.join(' ') : JSON.stringify(entry);
}

function updateBoxesTable(rows) {
  if (!boxesTableBody) return;
  boxesTableBody.innerHTML = '';
  if (!Array.isArray(rows) || rows.length === 0) {
    const emptyRow = document.createElement('tr');
    emptyRow.className = 'empty-state-row';
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.textContent = 'Utilization data has not been retrieved.';
    emptyRow.appendChild(cell);
    boxesTableBody.appendChild(emptyRow);
    return;
  }

  rows.forEach((row) => {
    const tr = document.createElement('tr');
    const utilizationPercentage = toPercent(row.utilization ?? row.fill_rate ?? row.percentage);
    tr.innerHTML = `
      <td>${escapeHtml(row.box_name || row.box || row.id || '—')}</td>
      <td>${escapeHtml(row.location || row.site || '—')}</td>
      <td>${formatNumeric(row.capacity || row.max_items)}</td>
      <td>${utilizationPercentage}</td>
      <td>${renderStatusPill(row.status || row.state)}</td>
    `;
    boxesTableBody.appendChild(tr);
  });
  setTimestamp(boxesUpdatedEl, new Date().toISOString());
}

function updateCasesTable(cases) {
  if (!openCasesTableBody) return;
  openCasesTableBody.innerHTML = '';
  if (!Array.isArray(cases) || cases.length === 0) {
    const emptyRow = document.createElement('tr');
    emptyRow.className = 'empty-state-row';
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.textContent = 'No open cases are currently assigned.';
    emptyRow.appendChild(cell);
    openCasesTableBody.appendChild(emptyRow);
    return;
  }

  cases.forEach((item) => {
    const tr = document.createElement('tr');
    const openedAt = item.opened_at || item.created_at || item.timestamp;
    tr.innerHTML = `
      <td>${escapeHtml(item.id || item.case_id || '—')}</td>
      <td>${escapeHtml(item.owner || item.assignee || item.user || '—')}</td>
      <td>${renderStatusPill(item.priority || item.status)}</td>
      <td>${formatDate(openedAt)}</td>
      <td>${escapeHtml(item.summary || item.description || '—')}</td>
    `;
    openCasesTableBody.appendChild(tr);
  });
  setTimestamp(casesUpdatedEl, new Date().toISOString());
}

function renderStatusPill(value) {
  if (!value) {
    return '<span class="status-pill">Unknown</span>';
  }
  const normalized = String(value).toLowerCase();
  let toneClass = '';
  if (['ok', 'healthy', 'available', 'open', 'low'].includes(normalized)) {
    toneClass = 'status-pill ok';
  } else if (['warning', 'partial', 'medium'].includes(normalized)) {
    toneClass = 'status-pill warning';
  } else if (['critical', 'down', 'closed', 'high'].includes(normalized)) {
    toneClass = 'status-pill danger';
  } else {
    toneClass = 'status-pill';
  }
  const label = normalized
    .split(/[_\s-]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
  return `<span class="${toneClass}">${label || value}</span>`;
}

function toPercent(value) {
  if (value === null || value === undefined) {
    return '—';
  }
  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    if (numeric <= 1) {
      return `${Math.round(numeric * 100)}%`;
    }
    return `${Math.round(numeric)}%`;
  }
  return escapeHtml(String(value));
}

function formatNumeric(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString() : escapeHtml(String(value));
}

function formatDate(value) {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return escapeHtml(String(value));
  }
  return date.toLocaleDateString();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function updateHealthStatus(status) {
  let isHealthy = false;
  let isWarning = false;
  let isCritical = false;
  let description = 'Service check pending.';

  if (typeof status === 'string') {
    description = status;
    isHealthy = status.toLowerCase().includes('ok') || status.toLowerCase().includes('ready');
    isCritical = status.toLowerCase().includes('fail');
  } else if (status && typeof status === 'object') {
    if (status.detail) {
      description = status.detail;
    } else if (status.message) {
      description = status.message;
    } else if (status.status) {
      description = status.status;
    }
    const healthFlag = status.ok ?? status.ready ?? status.status === 'ok';
    isHealthy = Boolean(healthFlag);
    if (status.warning) {
      isWarning = true;
    }
    if (status.critical || status.error) {
      isCritical = true;
    }
  }

  readyzStatusEl.textContent = description;
  setTimestamp(readyzCheckedAtEl, new Date().toISOString());
  systemHealthStatusEl.classList.remove('is-healthy', 'is-warning', 'is-critical', 'is-unknown');

  if (isCritical) {
    systemHealthStatusEl.classList.add('is-critical');
    systemHealthStatusEl.textContent = 'Critical';
  } else if (isWarning) {
    systemHealthStatusEl.classList.add('is-warning');
    systemHealthStatusEl.textContent = 'Warning';
  } else if (isHealthy) {
    systemHealthStatusEl.classList.add('is-healthy');
    systemHealthStatusEl.textContent = 'Healthy';
  } else {
    systemHealthStatusEl.classList.add('is-unknown');
    systemHealthStatusEl.textContent = 'Unknown';
  }
}

function handleUnauthorized(message) {
  stopPolling();
  clearTokens();
  toggleAuthUI(false);
  if (message) {
    setLoginStatus(message, 'is-error');
  }
}

async function logout() {
  const { accessToken } = getStoredTokens();
  try {
    if (accessToken) {
      await fetch('/api/v1/admin/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    }
  } catch (error) {
    console.error('Logout request failed', error);
  } finally {
    stopPolling();
    clearTokens();
    toggleAuthUI(false);
    setLoginStatus('You have been signed out.');
  }
}

function setupEventHandlers() {
  if (loginForm) {
    loginForm.addEventListener('submit', (event) => {
      event.preventDefault();
      if (isAuthenticating) {
        return;
      }
      const formData = new FormData(loginForm);
      const username = formData.get('username');
      const password = formData.get('password');
      if (!username || !password) {
        setLoginStatus('Please provide both username and password.', 'is-error');
        return;
      }
      login({ username, password });
    });
  }

  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      logout();
    });
  }
}

async function bootstrap() {
  setupEventHandlers();
  const { accessToken } = getStoredTokens();
  if (!accessToken) {
    toggleAuthUI(false);
    return;
  }
  try {
    await initializeSession();
  } catch (error) {
    console.error('Failed to restore session', error);
    handleUnauthorized('Session expired. Please sign in again.');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  bootstrap().catch((error) => {
    console.error('Bootstrap error', error);
  });
});
