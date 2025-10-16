import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"

export const KpiCard = ({ title, value, delta }: { title: string; value: string; delta?: string }) => (
  <Card>
    <CardHeader>
      <CardDescription>{title}</CardDescription>
      <CardTitle className="text-3xl font-bold">{value}</CardTitle>
    </CardHeader>
    {delta && (
      <CardContent>
        <span className="text-sm text-muted-foreground">{delta}</span>
      </CardContent>
    )}
  </Card>
)
