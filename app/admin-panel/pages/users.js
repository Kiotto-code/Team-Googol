import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createTable } from '../components/app-table.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

export const usersPage = {
  route: '/users',
  label: 'Users',
  icon: '👥',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    let users = [];
    let isLoading = true;
    let query = '';
    const { modal } = context;

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Users';
    header.appendChild(title);

    const searchForm = document.createElement('form');
    searchForm.setAttribute('role', 'search');
    searchForm.style.display = 'flex';
    searchForm.style.gap = '12px';

    const searchLabel = document.createElement('label');
    searchLabel.textContent = 'Search';
    const searchInput = document.createElement('input');
    searchInput.type = 'search';
    searchInput.placeholder = 'Name, email, RFID, student ID…';
    searchLabel.appendChild(searchInput);
    searchForm.appendChild(searchLabel);

    const searchButton = document.createElement('button');
    searchButton.type = 'submit';
    searchButton.textContent = 'Search';
    searchForm.appendChild(searchButton);

    searchForm.addEventListener('submit', (event) => {
      event.preventDefault();
      query = searchInput.value;
      fetchUsers();
    });

    header.appendChild(searchForm);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const totalCard = createCard({
      title: 'Visible Users',
      value: '—',
      meta: 'Including staff and admins',
    });
    totalCard.classList.add('grid-col-span-3');
    grid.appendChild(totalCard);

    const disabledCard = createCard({
      title: 'Disabled Accounts',
      value: '—',
      meta: 'Accounts blocked from login',
    });
    disabledCard.classList.add('grid-col-span-3');
    grid.appendChild(disabledCard);

    const roleCard = createCard({
      title: 'Role Distribution',
      value: '—',
      meta: 'User · Staff · Admin',
    });
    roleCard.classList.add('grid-col-span-6');
    grid.appendChild(roleCard);

    const tableSection = document.createElement('section');
    tableSection.className = 'grid-col-span-12 card';
    grid.appendChild(tableSection);

    function updateSummary() {
      totalCard.querySelector('.card__value').textContent = String(users.length);
      totalCard.querySelector('.card__meta').textContent = query
        ? `Filtered by "${query}"`
        : 'Latest administrative roster';

      const disabled = users.filter((user) => user.is_disabled).length;
      disabledCard.querySelector('.card__value').textContent = String(disabled);
      disabledCard.querySelector('.card__meta').textContent = `${disabled} of ${users.length} disabled`;

      const roles = users.reduce((acc, user) => {
        const role = user.role || 'user';
        acc[role] = (acc[role] || 0) + 1;
        return acc;
      }, {});
      roleCard.querySelector('.card__value').textContent = `${Object.keys(roles).length} roles`;
      roleCard.querySelector('.card__meta').textContent = Object.keys(roles).length
        ? Object.entries(roles)
            .map(([role, count]) => `${role}: ${count}`)
            .join(' · ')
        : 'No roles to display';
    }

    function renderTable() {
      tableSection.innerHTML = '';
      const heading = document.createElement('h2');
      heading.textContent = 'Directory';
      tableSection.appendChild(heading);

      const table = createTable({
        columns: [
          { label: 'ID', accessor: (row) => `#${row.user_id}` },
          { label: 'Name', accessor: (row) => row.name || '—' },
          { label: 'Email', accessor: (row) => row.email || '—' },
          { label: 'Role', accessor: (row) => row.role },
          {
            label: 'Status',
            accessor: (row) => (row.is_disabled ? 'Disabled' : 'Active'),
          },
        ],
        rows: users,
        isLoading,
        emptyState: 'No users matched your query.',
        onRowClick: (row) => showUserDetails(row),
      });
      tableSection.appendChild(table);
    }

    async function updateUser(userId, payload, successMessage) {
      try {
        const index = users.findIndex((user) => user.user_id === userId);
        if (index !== -1) {
          users[index] = { ...users[index], ...payload };
          renderTable();
          updateSummary();
        }
        const updated = await apiClient.request(`admin/users/${userId}`, {
          method: 'PUT',
          body: payload,
        });
        users = users.map((user) => (user.user_id === userId ? { ...user, ...updated } : user));
        renderTable();
        updateSummary();
        showToast({ title: successMessage, type: 'success' });
      } catch (error) {
        console.error('User update failed', error);
        showToast({ title: 'User update failed', message: error.message, type: 'error' });
        fetchUsers();
      }
    }

    function showUserDetails(user) {
      const body = document.createElement('div');
      body.style.display = 'flex';
      body.style.flexDirection = 'column';
      body.style.gap = '16px';
      body.appendChild(
        createCodeBlock(user, {
          label: `User ${user.user_id} profile`,
        })
      );

      const roleLabel = document.createElement('label');
      roleLabel.textContent = 'Role';
      const roleSelect = document.createElement('select');
      ['user', 'staff', 'admin'].forEach((role) => {
        const opt = document.createElement('option');
        opt.value = role;
        opt.textContent = role.charAt(0).toUpperCase() + role.slice(1);
        if (role === user.role) {
          opt.selected = true;
        }
        roleSelect.appendChild(opt);
      });
      roleLabel.appendChild(roleSelect);
      body.appendChild(roleLabel);

      const statusButton = document.createElement('button');
      statusButton.textContent = user.is_disabled ? 'Enable Login' : 'Disable Login';
      statusButton.addEventListener('click', () =>
        updateUser(
          user.user_id,
          { is_disabled: !user.is_disabled },
          user.is_disabled ? 'User enabled' : 'User disabled'
        )
      );

      const saveRole = document.createElement('button');
      saveRole.textContent = 'Update Role';
      saveRole.addEventListener('click', () =>
        updateUser(user.user_id, { role: roleSelect.value }, 'Role updated')
      );

      modal.show({
        title: `User #${user.user_id}`,
        body,
        actions: [statusButton, saveRole],
      });
    }

    async function fetchUsers() {
      isLoading = true;
      renderTable();
      try {
        const response = await apiClient.request('admin/users', {
          query: {
            page: 1,
            limit: 25,
            q: query || undefined,
          },
        });
        users = response.data || [];
        isLoading = false;
        renderTable();
        updateSummary();
      } catch (error) {
        console.error('Failed to load users', error);
        showToast({ title: 'Unable to load users', message: error.message, type: 'error' });
      }
    }

    await fetchUsers();
  },
};
