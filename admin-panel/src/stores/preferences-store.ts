import { create } from "zustand"
import { persist } from "zustand/middleware"
import { DateTime } from "luxon"

type Theme = "light" | "dark" | "system"

type PreferencesState = {
  theme: Theme
  timezone: string
  setTheme: (theme: Theme) => void
  setTimezone: (timezone: string) => void
}

const resolveSystemTheme = (): Theme =>
  typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"

const defaultTimezone = DateTime.local().zoneName

export const preferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: "system",
      timezone: defaultTimezone,
      setTheme: (theme) => set({ theme }),
      setTimezone: (timezone) => set({ timezone }),
    }),
    { name: "admin-preferences" },
  ),
)

export const computeActiveTheme = (theme: Theme) => {
  if (theme === "system") {
    return resolveSystemTheme()
  }
  return theme
}
