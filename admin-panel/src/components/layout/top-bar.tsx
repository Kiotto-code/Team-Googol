import { useTranslation } from "react-i18next"
import { useMemo } from "react"
import { DateTime } from "luxon"
import { Button } from "../ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Switch } from "../ui/switch"
import { authStore } from "../../stores/auth-store"
import { preferencesStore } from "../../stores/preferences-store"
import { useNavigate } from "react-router-dom"

const supportedValues = (Intl as typeof Intl & { supportedValuesOf?: (key: string) => string[] }).supportedValuesOf
const timezones = supportedValues ? supportedValues("timeZone") : ["UTC"]

export const TopBar = () => {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = authStore((state) => ({ user: state.user, logout: state.logout }))
  const { theme, timezone, setTheme, setTimezone } = preferencesStore()

  const localizedTime = useMemo(() => {
    return DateTime.now().setZone(timezone).toFormat("DDD t")
  }, [timezone])

  return (
    <header className="flex items-center justify-between border-b bg-background px-6 py-4">
      <div>
        <p className="text-sm text-muted-foreground">{t("app.welcome", { name: user?.name ?? "" })}</p>
        <p className="text-xs text-muted-foreground">{localizedTime}</p>
      </div>
      <div className="flex items-center gap-3">
        <Select value={i18n.language} onValueChange={(value) => i18n.changeLanguage(value)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder={t("app.language")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="en">English</SelectItem>
            <SelectItem value="es">Español</SelectItem>
          </SelectContent>
        </Select>
        <Select value={timezone} onValueChange={setTimezone}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder={t("app.timezone")} />
          </SelectTrigger>
          <SelectContent className="max-h-64 overflow-auto">
            {timezones.map((zone: string) => (
              <SelectItem key={zone} value={zone}>
                {zone}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex items-center gap-2 text-sm">
          <span>{t("app.theme")}</span>
          <Switch
            checked={theme === "dark"}
            onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
            aria-label="Toggle dark mode"
          />
        </div>
        <Button
          variant="outline"
          onClick={() => {
            logout()
            navigate("/login")
          }}
        >
          {t("app.logout")}
        </Button>
      </div>
    </header>
  )
}
