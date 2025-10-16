import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { KpiCard } from "../components/widgets/kpi-card"
import { TrendChart } from "../components/widgets/trend-chart"
import { AuditFeedback } from "../components/widgets/audit-feedback"
import { MetricPoint } from "../types"
import { api } from "../lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"

interface DashboardMetrics {
  activeBoxes: number
  openCases: number
  newUsers: number
  throughput: MetricPoint[]
  auditScore: number
}

export const DashboardRoute = () => {
  const { t } = useTranslation()
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)

  useEffect(() => {
    api.get<DashboardMetrics>("/dashboard").then((response) => setMetrics(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("navigation.dashboard")}</h1>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Active Boxes" value={metrics?.activeBoxes?.toString() ?? "-"} delta="2.3% vs last week" />
        <KpiCard title="Open Cases" value={metrics?.openCases?.toString() ?? "-"} delta="Stable" />
        <KpiCard title="New Users" value={metrics?.newUsers?.toString() ?? "-"} delta="+12" />
        <KpiCard title="Audit Score" value={`${metrics?.auditScore ?? 0}%`} delta="Quarter to date" />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendChart title="Operational Throughput" data={metrics?.throughput ?? []} />
        </div>
        <AuditFeedback />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Telemetry</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <TelemetryStat label="Requests/min" value="1,240" trend="+5.6%" />
          <TelemetryStat label="Latency p95" value="220ms" trend="-12%" />
          <TelemetryStat label="Error rate" value="0.3%" trend="-0.1%" />
        </CardContent>
      </Card>
    </div>
  )
}

const TelemetryStat = ({ label, value, trend }: { label: string; value: string; trend: string }) => (
  <div className="rounded-lg border bg-card p-4">
    <p className="text-sm text-muted-foreground">{label}</p>
    <p className="text-xl font-semibold">{value}</p>
    <p className="text-xs text-emerald-500">{trend}</p>
  </div>
)
