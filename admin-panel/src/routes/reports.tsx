import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { api } from "../lib/api-client"

interface ReportSummary {
  id: string
  title: string
  description: string
  updated_at: string
}

export const ReportsRoute = () => {
  const [reports, setReports] = useState<ReportSummary[]>([])

  useEffect(() => {
    api.get<ReportSummary[]>("/reports").then((response) => setReports(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reports</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {reports.map((report) => (
          <Card key={report.id}>
            <CardHeader>
              <CardTitle>{report.title}</CardTitle>
              <CardDescription>{report.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Updated {new Date(report.updated_at).toLocaleString()}
              </span>
              <Button size="sm" variant="outline" onClick={() => void api.get(`/reports/${report.id}/download`)}>
                Download
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
