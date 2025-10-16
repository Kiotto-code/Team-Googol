import { apiClient } from './api.js';
import { Router } from './router.js';
import { createModalManager } from './components/app-modal.js';
import { showToast } from './components/app-toast.js';
import {
  dashboardPage,
  boxesPage,
  casesPage,
  itemsPage,
  usersPage,
  auditLogsPage,
  reportsPage,
  metricsPage,
  profilePage,
} from './pages/index.js';

const PAGES = [
  dashboardPage,
  boxesPage,
  casesPage,
  itemsPage,
  usersPage,
  auditLogsPage,
  reportsPage,
  metricsPage,
  profilePage,
];

const routeMap = PAGES.reduce((acc, page) => {
  acc[page.route] = page;
  return acc;
}, {});

const app = document.getElementById('app');
const modal = createModalManager();
let router;
let cleanup;
let statusTimer;
let currentUser;
let navLinks = [];
let sidebar;
let sidebarOverlay;
let topbarUser;
let healthChip;
let readyChip;
let contentArea;

function createStatusChip(label) {
  const chip = document.createElement('span');
  chip.className = 'status-chip';
  chip.textContent = `${label}: pending`;
  return chip;
}

function updateStatusChip(chip, status) {
  chip.classList.remove('is-healthy', 'is-degraded', 'is-down');
  chip.textContent = status.label;
  if (status.state === 'healthy') {
    chip.classList.add('is-healthy');
  } else if (status.state === 'degraded') {
    chip.classList.add('is-degraded');
  } else if (status.state === 'down') {
    chip.classList.add('is-down');
  }
}

function closeSidebar() {
  if (!sidebar) return;
  sidebar.classList.remove('is-open');
  sidebarOverlay?.classList.remove('is-open');
}

function toggleSidebar() {
  if (!sidebar) return;
  sidebar.classList.toggle('is-open');
  sidebarOverlay?.classList.toggle('is-open');
}

async function refreshSystemStatus() {
  if (!healthChip || !readyChip) return;
  try {
    const [healthResponse, readyResponse] = await Promise.all([
      fetch(`${apiClient.API_BASE}/healthz`).then((res) => res.json()),
      fetch(`${apiClient.API_BASE}/readyz`).then((res) => res.json()),
    ]);
    updateStatusChip(healthChip, {
      label: `Health · ${healthResponse.status}`,
      state: healthResponse.status === 'ok' ? 'healthy' : 'degraded',
    });
    updateStatusChip(readyChip, {
      label: `Ready · ${readyResponse.status}`,
      state:
        readyResponse.status === 'ready'
          ? 'healthy'
          : readyResponse.status === 'degraded'
          ? 'degraded'
          : 'down',
    });
  } catch (error) {
    updateStatusChip(healthChip, { label: 'Health · error', state: 'down' });
    updateStatusChip(readyChip, { label: 'Ready · error', state: 'down' });
  }
}

async function loadCurrentUser() {
  try {
    currentUser = await apiClient.request('admin/auth/me');
    if (topbarUser) {
      topbarUser.textContent = `${currentUser.user.name || currentUser.user.email} · ${currentUser.roles.join(
        ', '
      )}`;
    }
  } catch (error) {
    console.error('Failed to resolve current user', error);
    showToast({ title: 'Session expired', message: 'Please sign in again.', type: 'warning' });
    await apiClient.logout();
  }
}

function highlightNav(route) {
  navLinks.forEach((link) => {
    if (link.dataset.route === route.route) {
      link.classList.add('is-active');
      link.setAttribute('aria-current', 'page');
    } else {
      link.classList.remove('is-active');
      link.removeAttribute('aria-current');
    }
  });
}

async function handleRouteChange(route, params) {
  if (!contentArea) return;
  if (cleanup) {
    cleanup();
    cleanup = null;
  }
  contentArea.innerHTML = '';
  contentArea.setAttribute('data-route', route.route);
  highlightNav(route);
  document.title = `${route.label} · Admin Control Center`;
  const result = await route.render({ root: contentArea, params, context: { modal, currentUser } });
  if (typeof result === 'function') {
    cleanup = result;
  }
  closeSidebar();
}

function createNotFoundRoute() {
  return {
    route: '*',
    label: 'Not Found',
    async render({ root }) {
      const message = document.createElement('div');
      message.className = 'card';
      const title = document.createElement('h2');
      title.textContent = 'Page not found';
      const body = document.createElement('p');
      body.textContent = 'The requested page does not exist. Choose an option from the navigation.';
      message.appendChild(title);
      message.appendChild(body);
      root.appendChild(message);
    },
  };
}

async function mountRouter() {
  if (router) return;
  router = new Router({
    routes: { ...routeMap, '*': createNotFoundRoute() },
    onRouteChange: handleRouteChange,
    fallback: ({ error }) => {
      showToast({
        title: 'Navigation error',
        message: error?.message || 'Unable to load page',
        type: 'error',
      });
    },
  });
  router.start();
}

function buildLayout() {
  app.innerHTML = '';

  sidebarOverlay = document.createElement('div');
  sidebarOverlay.className = 'sidebar__overlay';
  sidebarOverlay.addEventListener('click', closeSidebar);
  app.appendChild(sidebarOverlay);

  sidebar = document.createElement('aside');
  sidebar.className = 'sidebar';
  sidebar.setAttribute('aria-label', 'Primary');

  const brand = document.createElement('div');
  brand.className = 'sidebar__brand';
  const logo = document.createElement('img');
  logo.src = './assets/logo.svg';
  logo.alt = 'Admin logo';
  logo.width = 32;
  logo.height = 32;
  brand.appendChild(logo);
  const brandTitle = document.createElement('span');
  brandTitle.textContent = 'Control Center';
  brand.appendChild(brandTitle);
  sidebar.appendChild(brand);

  const nav = document.createElement('nav');
  nav.className = 'sidebar__nav';
  nav.setAttribute('aria-label', 'Main navigation');

  navLinks = PAGES.map((page) => {
    const link = document.createElement('a');
    link.href = `#${page.route}`;
    link.dataset.route = page.route;
    link.innerHTML = `${page.icon ?? ''} <span>${page.label}</span>`;
    nav.appendChild(link);
    return link;
  });
  sidebar.appendChild(nav);

  const footer = document.createElement('div');
  footer.className = 'sidebar__footer';
  footer.textContent = 'Team Googol · Enterprise Edition';
  sidebar.appendChild(footer);

  app.appendChild(sidebar);

  const main = document.createElement('div');
  main.className = 'main';

  const topbar = document.createElement('header');
  topbar.className = 'topbar';

  const leftGroup = document.createElement('div');
  leftGroup.className = 'topbar__group';
  const toggleButton = document.createElement('button');
  toggleButton.type = 'button';
  toggleButton.textContent = 'Menu';
  toggleButton.addEventListener('click', toggleSidebar);
  leftGroup.appendChild(toggleButton);
  topbar.appendChild(leftGroup);

  const statusGroup = document.createElement('div');
  statusGroup.className = 'topbar__status';
  healthChip = createStatusChip('Health');
  readyChip = createStatusChip('Ready');
  statusGroup.appendChild(healthChip);
  statusGroup.appendChild(readyChip);
  topbar.appendChild(statusGroup);

  const rightGroup = document.createElement('div');
  rightGroup.className = 'topbar__group';
  topbarUser = document.createElement('span');
  topbarUser.className = 'helper-text';
  rightGroup.appendChild(topbarUser);
  const profileLink = document.createElement('a');
  profileLink.href = '#/profile';
  profileLink.textContent = 'Profile';
  profileLink.className = 'badge';
  rightGroup.appendChild(profileLink);
  const logoutButton = document.createElement('button');
  logoutButton.type = 'button';
  logoutButton.textContent = 'Logout';
  logoutButton.addEventListener('click', async () => {
    await apiClient.logout();
    showToast({ title: 'Signed out', type: 'success' });
  });
  rightGroup.appendChild(logoutButton);
  topbar.appendChild(rightGroup);

  main.appendChild(topbar);

  contentArea = document.createElement('div');
  contentArea.className = 'content';
  contentArea.setAttribute('role', 'main');
  contentArea.setAttribute('tabindex', '-1');
  main.appendChild(contentArea);

  app.appendChild(main);
}

function renderLogin() {
  if (router) {
    router = null;
  }
  if (cleanup) {
    cleanup();
    cleanup = null;
  }
  window.clearInterval(statusTimer);
  app.innerHTML = '';
  sidebar = null;
  sidebarOverlay = null;
  contentArea = null;
  navLinks = [];
  healthChip = null;
  readyChip = null;
  const card = document.createElement('div');
  card.className = 'login-card';

  const heading = document.createElement('h1');
  heading.className = 'login-card__title';
  heading.textContent = 'Admin Sign In';
  card.appendChild(heading);

  const form = document.createElement('form');
  form.noValidate = true;

  const identifierLabel = document.createElement('label');
  identifierLabel.textContent = 'Email or student ID';
  const identifierInput = document.createElement('input');
  identifierInput.type = 'text';
  identifierInput.name = 'identifier';
  identifierInput.required = true;
  identifierInput.autocomplete = 'username';
  identifierLabel.appendChild(identifierInput);
  form.appendChild(identifierLabel);

  const passwordLabel = document.createElement('label');
  passwordLabel.textContent = 'Password';
  const passwordInput = document.createElement('input');
  passwordInput.type = 'password';
  passwordInput.name = 'password';
  passwordInput.required = true;
  passwordInput.autocomplete = 'current-password';
  passwordLabel.appendChild(passwordInput);
  form.appendChild(passwordLabel);

  const submit = document.createElement('button');
  submit.type = 'submit';
  submit.textContent = 'Sign in';
  form.appendChild(submit);

  const helper = document.createElement('p');
  helper.className = 'helper-text';
  helper.textContent = 'Access is restricted to authorized staff.';
  card.appendChild(form);
  card.appendChild(helper);

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      await apiClient.login({ identifier: identifierInput.value, password: passwordInput.value });
      showToast({ title: 'Welcome back', type: 'success' });
      renderApp();
    } catch (error) {
      console.error('Login failed', error);
      showToast({
        title: 'Login failed',
        message: error.message || 'Invalid credentials',
        type: 'error',
      });
    } finally {
      submit.disabled = false;
    }
  });

  app.appendChild(card);
  identifierInput.focus();
}

async function renderApp() {
  if (!apiClient.isAuthenticated) {
    renderLogin();
    return;
  }

  if (!contentArea) {
    buildLayout();
  }

  await loadCurrentUser();
  await refreshSystemStatus();
  window.clearInterval(statusTimer);
  statusTimer = window.setInterval(refreshSystemStatus, 30000);

  await mountRouter();
}

apiClient.onAuthChange(({ isAuthenticated }) => {
  if (!isAuthenticated) {
    renderLogin();
  }
});

renderApp();
