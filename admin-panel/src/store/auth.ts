import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { api, setAuthProvider } from '@/lib/http';
import type { AuthUser } from '@/types/auth';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error?: string;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<AuthUser | null>;
  setTokens: (tokens: { accessToken: string; refreshToken: string }) => void;
}

const resolveAuthStorage = () => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return import.meta.env.VITE_AUTH_STORAGE === 'session' ? window.sessionStorage : window.localStorage;
};

const authStorage = resolveAuthStorage();

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      async login(credentials) {
        set({ isLoading: true, error: undefined });
        try {
          const { data } = await api.post('/auth/login', credentials);
          const { access_token: accessToken, refresh_token: refreshToken } = data;
          set({ accessToken, refreshToken });
          await get().fetchCurrentUser();
        } catch (err) {
          set({ error: 'AUTH_LOGIN_FAILED' });
          throw err;
        } finally {
          set({ isLoading: false });
        }
      },
      logout() {
        set({ user: null, accessToken: null, refreshToken: null });
      },
      async fetchCurrentUser() {
        try {
          const { data } = await api.get<AuthUser>('/auth/me');
          set({ user: data });
          return data;
        } catch {
          set({ user: null });
          return null;
        }
      },
      setTokens({ accessToken, refreshToken }) {
        set({ accessToken, refreshToken });
      }
    }),
    {
      name: 'admin-panel-auth',
      storage: authStorage ? createJSONStorage(() => authStorage) : undefined,
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user
      })
    }
  )
);

setAuthProvider({
  getAccessToken: () => useAuthStore.getState().accessToken,
  getRefreshToken: () => useAuthStore.getState().refreshToken,
  setTokens: (tokens) => useAuthStore.getState().setTokens(tokens),
  onAuthFailure: () => useAuthStore.getState().logout()
});
