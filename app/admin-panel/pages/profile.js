import { apiClient } from '../api.js';
import { createCard } from '../components/app-card.js';
import { createCodeBlock } from '../components/code-block.js';
import { showToast } from '../components/app-toast.js';

export const profilePage = {
  route: '/profile',
  label: 'Profile',
  icon: '🙋',
  async render({ root, context }) {
    root.innerHTML = '';
    root.className = 'page';

    const header = document.createElement('div');
    header.className = 'page__header';
    const title = document.createElement('h1');
    title.className = 'page__title';
    title.textContent = 'Your Session';
    header.appendChild(title);

    const logoutButton = document.createElement('button');
    logoutButton.type = 'button';
    logoutButton.textContent = 'Sign out';
    logoutButton.addEventListener('click', async () => {
      await apiClient.logout();
      showToast({ title: 'Signed out', type: 'success' });
    });
    header.appendChild(logoutButton);
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'page__grid';
    root.appendChild(grid);

    const identityCard = createCard({
      title: 'Identity',
      body: 'Loading…',
      meta: 'Roles and permissions',
    });
    identityCard.classList.add('grid-col-span-6');
    grid.appendChild(identityCard);

    const tokensCard = createCard({
      title: 'Session Tokens',
      body: 'Loading…',
      meta: 'Stored in sessionStorage',
    });
    tokensCard.classList.add('grid-col-span-6');
    grid.appendChild(tokensCard);

    try {
      const response = await apiClient.request('admin/auth/me');
      identityCard.querySelector('.card__body').replaceChildren(
        createCodeBlock(response, { label: 'Authenticated user' })
      );
      identityCard.querySelector('.card__meta').textContent = response.roles.join(' · ');
    } catch (error) {
      identityCard.querySelector('.card__body').textContent = 'Failed to load profile.';
      showToast({ title: 'Profile unavailable', message: error.message, type: 'error' });
    }

    const tokenDetails = {
      accessTokenPreview: `${apiClient.accessToken?.slice(0, 12) || '—'}…`,
      refreshTokenPresent: Boolean(apiClient.refreshToken),
    };
    tokensCard.querySelector('.card__body').replaceChildren(
      createCodeBlock(tokenDetails, { label: 'Session tokens' })
    );
  },
};
