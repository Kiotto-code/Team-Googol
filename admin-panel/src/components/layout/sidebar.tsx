import { NavLink } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { cn } from "../../lib/utils"

const links = [
  { to: "/dashboard", i18nKey: "navigation.dashboard" },
  { to: "/boxes", i18nKey: "navigation.boxes" },
  { to: "/cases", i18nKey: "navigation.cases" },
  { to: "/items", i18nKey: "navigation.items" },
  { to: "/users", i18nKey: "navigation.users" },
  { to: "/audit-logs", i18nKey: "navigation.auditLogs" },
  { to: "/reports", i18nKey: "navigation.reports" },
  { to: "/metrics", i18nKey: "navigation.metrics" },
  { to: "/health", i18nKey: "navigation.health" },
  { to: "/settings", i18nKey: "navigation.settings" },
]

export const Sidebar = () => {
  const { t } = useTranslation()
  return (
    <aside className="hidden w-64 flex-col border-r bg-muted/40 p-4 lg:flex">
      <div className="text-lg font-semibold">{t("app.title")}</div>
      <nav className="mt-6 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            {t(link.i18nKey)}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
