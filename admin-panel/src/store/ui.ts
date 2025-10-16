import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'system',
      timezone: 'Asia/Kuala_Lumpur',
      language: 'en',
      setTheme: (theme) => set({ theme }),
      setTimezone: (timezone) => set({ timezone }),
      setLanguage: (language) => set({ language })
    }),
    {
      name: 'admin-panel-ui'
    }
  )
);
