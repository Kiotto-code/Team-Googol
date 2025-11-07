const DEFAULT_REFRESH_INTERVAL = 14 * 60 * 1000; // 14 minutes
const storage = window.sessionStorage;

const listeners = new Set();

function dispatchAuthChange(state) {
  listeners.forEach((listener) => {
    try {
      listener(state);
    } catch (error) {
      console.error('Auth listener error', error);
    }
  });
}

class ApiClient {
  constructor() {
    this.API_BASE = window.API_BASE || '/api/v1';
    this.accessTokenKey = 'admin_access_token';
    this.refreshTokenKey = 'admin_refresh_token';
    this.refreshTimer = null;
    this.isRefreshing = false;
  }

  onAuthChange(callback) {
    listeners.add(callback);
    return () => listeners.delete(callback);
  }

  get accessToken() {
    return storage.getItem(this.accessTokenKey);
  }

  get refreshToken() {
    return storage.getItem(this.refreshTokenKey);
  }

  get isAuthenticated() {
    return Boolean(this.accessToken);
  }

  setTokens({ accessToken, refreshToken, expiresIn }) {
    if (accessToken) {
      storage.setItem(this.accessTokenKey, accessToken);
    }
    if (refreshToken) {
      storage.setItem(this.refreshTokenKey, refreshToken);
    }
    this.scheduleRefresh(expiresIn);
    dispatchAuthChange({ isAuthenticated: true });
  }

  clearTokens() {
    storage.removeItem(this.accessTokenKey);
    storage.removeItem(this.refreshTokenKey);
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    dispatchAuthChange({ isAuthenticated: false });
  }

  scheduleRefresh(expiresIn) {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    const interval = typeof expiresIn === 'number' && expiresIn > 0
      ? Math.max(expiresIn * 1000 - 30 * 1000, 60 * 1000)
      : DEFAULT_REFRESH_INTERVAL;
    this.refreshTimer = window.setTimeout(() => {
      this.refreshAccessToken().catch((error) => {
        console.warn('Automatic token refresh failed', error);
        this.clearTokens();
      });
    }, interval);
  }

  async login({ identifier, password }) {
    const response = await fetch(`${this.API_BASE}/admin/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier, password }),
    });

    if (!response.ok) {
      const errorPayload = await this.safeReadJson(response);
      const error = new Error(errorPayload?.detail || 'Unable to sign in');
      error.status = response.status;
      error.payload = errorPayload;
      throw error;
    }

    const data = await response.json();
    this.setTokens({
      accessToken: data.access_token || data.accessToken,
      refreshToken: data.refresh_token || data.refreshToken,
      expiresIn: data.expires_in || data.expiresIn,
    });
    return data;
  }

  async refreshAccessToken() {
    if (this.isRefreshing) return null;
    if (!this.refreshToken) throw new Error('Missing refresh token');
    this.isRefreshing = true;
    try {
      const response = await fetch(`${this.API_BASE}/admin/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Unable to refresh session');
      }
      const data = await response.json();
      this.setTokens({
        accessToken: data.access_token || data.accessToken,
        refreshToken: data.refresh_token || data.refreshToken || this.refreshToken,
        expiresIn: data.expires_in || data.expiresIn,
      });
      return data;
    } finally {
      this.isRefreshing = false;
    }
  }

  async logout() {
    try {
      await fetch(`${this.API_BASE}/admin/auth/logout`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
    } catch (error) {
      console.warn('Logout request failed', error);
    } finally {
      this.clearTokens();
    }
  }

  buildHeaders(extra = {}) {
    const headers = new Headers();
    if (extra instanceof Headers) {
      extra.forEach((value, key) => headers.set(key, value));
    } else {
      Object.entries(extra || {}).forEach(([key, value]) => {
        headers.set(key, value);
      });
    }
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    if (this.accessToken) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }
    return headers;
  }

  async request(path, { method = 'GET', headers, body, query } = {}) {
    const url = new URL(path.startsWith('http') ? path : `${this.API_BASE}/${path.replace(/^\//, '')}`, window.location.origin);
    if (query && typeof query === 'object') {
      Object.entries(query).forEach(([key, value]) => {
        if (value === undefined || value === null) return;
        url.searchParams.append(key, value);
      });
    }

    const finalHeaders = this.buildHeaders(headers);
    const contentType = finalHeaders.get('Content-Type');

    // Auto-add Idempotency-Key for admin box POST action endpoints if missing
    function generateIdempotencyKey() {
      try {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
          return window.crypto.randomUUID();
        }
      } catch (_) {}
      return `idemp-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    }
    const m = (method || 'GET').toUpperCase();
    const isBoxesAction = m === 'POST' && /\/api\/v1\/admin\/boxes\/[^/]+:.+/.test(url.pathname);
    if (isBoxesAction && !finalHeaders.has('Idempotency-Key')) {
      finalHeaders.set('Idempotency-Key', generateIdempotencyKey());
    }

    const response = await fetch(url.toString(), {
      method,
      headers: finalHeaders,
      body: body && contentType === 'application/json'
        ? JSON.stringify(body)
        : body instanceof FormData || body instanceof Blob
        ? body
        : body && typeof body === 'object' && contentType === 'application/json'
        ? JSON.stringify(body)
        : body,
    });

    if (response.status === 401 && this.refreshToken) {
      try {
        await this.refreshAccessToken();
        return this.request(path, { method, headers, body, query });
      } catch (error) {
        this.clearTokens();
        throw error;
      }
    }

    if (!response.ok) {
      const errorPayload = await this.safeReadJson(response);
      const error = new Error(errorPayload?.detail || 'Request failed');
      error.status = response.status;
      error.payload = errorPayload;
      throw error;
    }

    return this.safeReadJson(response);
  }

  async safeReadJson(response) {
    try {
      return await response.json();
    } catch (error) {
      return null;
    }
  }
}

export const apiClient = new ApiClient();
