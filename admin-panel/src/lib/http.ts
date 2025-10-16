import axios, { type AxiosRequestConfig, type AxiosRequestHeaders } from 'axios';

interface AuthProvider {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  setTokens: (tokens: { accessToken: string; refreshToken: string }) => void;
  onAuthFailure: () => void;
}

type RetriableRequestConfig = AxiosRequestConfig & { _retry?: boolean };

let authProvider: AuthProvider | null = null;
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

export const setAuthProvider = (provider: AuthProvider) => {
  authProvider = provider;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1/admin';

export const api = axios.create({
  baseURL: apiBaseUrl
});

api.interceptors.request.use((config) => {
  const token = authProvider?.getAccessToken();
  if (token) {
    const headers = (config.headers ?? {}) as AxiosRequestHeaders;
    headers.Authorization = `Bearer ${token}`;
    config.headers = headers;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!authProvider) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as RetriableRequestConfig;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = (async () => {
            try {
              const refreshToken = authProvider?.getRefreshToken();
              if (!refreshToken) {
                return null;
              }
              const { data } = await axios.post('/api/v1/admin/auth/refresh', {
                refresh_token: refreshToken
              });
              const { access_token: accessToken, refresh_token: newRefreshToken } = data;
              authProvider?.setTokens({ accessToken, refreshToken: newRefreshToken });
              return accessToken as string;
            } finally {
              isRefreshing = false;
            }
          })();
        }

        const newToken = await refreshPromise;
        if (newToken) {
          const headers = (originalRequest.headers ?? {}) as AxiosRequestHeaders;
          headers.Authorization = `Bearer ${newToken}`;
          originalRequest.headers = headers;
          return api(originalRequest);
        }
        authProvider.onAuthFailure();
      } catch (refreshError) {
        authProvider.onAuthFailure();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
