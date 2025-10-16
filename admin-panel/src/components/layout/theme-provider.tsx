import { ReactNode, useEffect } from "react"
import { preferencesStore, computeActiveTheme } from "../../stores/preferences-store"

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const { theme } = preferencesStore()
  useEffect(() => {
    const root = window.document.documentElement
    const activeTheme = computeActiveTheme(theme)
    root.classList.remove("light", "dark")
    root.classList.add(activeTheme)
  }, [theme])

  return <>{children}</>
}
