import { ReactNode, Suspense } from "react"
import { I18nextProvider } from "react-i18next"
import i18n from "../i18n"
import { ThemeProvider } from "../components/layout/theme-provider"
import { ErrorBoundary } from "../components/common/error-boundary"

export const AppProviders = ({ children }: { children: ReactNode }) => (
  <ErrorBoundary>
    <I18nextProvider i18n={i18n}>
      <ThemeProvider>
        <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
          {children}
        </Suspense>
      </ThemeProvider>
    </I18nextProvider>
  </ErrorBoundary>
)
