import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark' | 'system';
export type TimezoneOption = 'Asia/Kuala_Lumpur' | 'UTC';
export type LanguageOption = 'en' | 'zh';

interface UIState {
  theme: ThemeMode;
  timezone: TimezoneOption;
  language: LanguageOption;
  setTheme: (theme: ThemeMode) => void;
  setTimezone: (timezone: TimezoneOption) => void;
  setLanguage: (language: LanguageOption) => void;
}

const resolveUIStorage = () => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return import.meta.env.VITE_AUTH_STORAGE === 'session' ? window.sessionStorage : window.localStorage;
};

const defaultTimezone: TimezoneOption = import.meta.env.VITE_DEFAULT_TZ === 'UTC' ? 'UTC' : 'Asia/Kuala_Lumpur';
const uiStorage = resolveUIStorage();

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'system',
      timezone: defaultTimezone,
      language: 'en',
      setTheme: (theme) => set({ theme }),
      setTimezone: (timezone) => set({ timezone }),
      setLanguage: (language) => set({ language })
    }),
    {
      name: 'admin-panel-ui',
      storage: uiStorage ? createJSONStorage(() => uiStorage) : undefined
    }
  )
);
