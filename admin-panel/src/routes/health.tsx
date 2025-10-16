import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { HealthCheck } from "../types"
import { api } from "../lib/api-client"

export const HealthRoute = () => {
  const [checks, setChecks] = useState<HealthCheck[]>([])

  useEffect(() => {
    api.get<HealthCheck[]>("/health").then((response) => setChecks(response.data))
  }, [])

  const badgeVariant = (status: HealthCheck["status"]) => {
    switch (status) {
      case "healthy":
        return "secondary" as const
      case "degraded":
        return "outline" as const
      case "down":
      default:
        return "destructive" as const
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Health</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {checks.map((check) => (
          <Card key={check.service}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{check.service}</CardTitle>
              <Badge variant={badgeVariant(check.status)}>{check.status}</Badge>
            </CardHeader>
            {check.message && <CardContent className="text-sm text-muted-foreground">{check.message}</CardContent>}
          </Card>
        ))}
      </div>
    </div>
  )
}
