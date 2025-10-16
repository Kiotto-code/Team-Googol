import { useEffect, useState } from "react"
import { TrendChart } from "../components/widgets/trend-chart"
import { MetricPoint } from "../types"
import { api } from "../lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"

interface MetricsResponse {
  throughput: MetricPoint[]
  sla: MetricPoint[]
}

export const MetricsRoute = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)

  useEffect(() => {
    api.get<MetricsResponse>("/metrics").then((response) => setMetrics(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Metrics</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <TrendChart title="Throughput" data={metrics?.throughput ?? []} />
        <TrendChart title="SLA" data={metrics?.sla ?? []} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Recent KPIs</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <Kpi label="Order Accuracy" value="99.1%" trend="+0.3%" />
          <Kpi label="Fulfillment" value="1.3 days" trend="-0.2 days" />
          <Kpi label="Churn" value="2.1%" trend="-0.1%" />
        </CardContent>
      </Card>
    </div>
  )
}

const Kpi = ({ label, value, trend }: { label: string; value: string; trend: string }) => (
  <div className="rounded-lg border bg-card p-4">
    <p className="text-sm text-muted-foreground">{label}</p>
    <p className="text-xl font-semibold">{value}</p>
    <p className="text-xs text-emerald-500">{trend}</p>
  </div>
)
