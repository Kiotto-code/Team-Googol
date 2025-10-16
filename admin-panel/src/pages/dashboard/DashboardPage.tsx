import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/http';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, BarChart, Bar } from 'recharts';
import { useBoxEvents } from '@/hooks/useBoxEvents';
import { useUIStore } from '@/store/ui';
import { dayjs } from '@/lib/dayjs';

interface DashboardResponse {
  throughput: number;
  occupancy: number;
  slaCompliance: number;
  alerts: number;
  trend: { timestamp: string; boxesProcessed: number; exceptions: number }[];
}

const fallbackData: DashboardResponse = {
  throughput: 1280,
  occupancy: 82,
  slaCompliance: 96,
  alerts: 4,
  trend: Array.from({ length: 7 }).map((_, index) => ({
    timestamp: dayjs().subtract(6 - index, 'day').toISOString(),
    boxesProcessed: Math.round(1000 + Math.random() * 200),
    exceptions: Math.round(Math.random() * 20)
  }))
};

export function DashboardPage() {
  const { t } = useTranslation();
  const timezone = useUIStore((state) => state.timezone);
  const { events, status } = useBoxEvents();

  const { data = fallbackData } = useQuery<DashboardResponse>({
    queryKey: ['dashboard-overview'],
    queryFn: async () => {
      const response = await api.get<DashboardResponse>('/analytics/dashboard');
      return response.data;
    },
    staleTime: 1000 * 60,
    retry: 1
  });

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardDescription>{t('dashboard.throughput')}</CardDescription>
            <CardTitle className="text-3xl font-bold">{data.throughput.toLocaleString()}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t('dashboard.occupancy')}</CardDescription>
            <CardTitle className="text-3xl font-bold">{data.occupancy}%</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t('dashboard.sla')}</CardDescription>
            <CardTitle className="text-3xl font-bold">{data.slaCompliance}%</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Active alerts</CardDescription>
            <CardTitle className="text-3xl font-bold">{data.alerts}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('dashboard.chart')}</CardTitle>
          <CardDescription>{t('dashboard.kpis')}</CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(value) => dayjs(value).tz(timezone).format('MM-DD')} />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => dayjs(value).tz(timezone).format('YYYY-MM-DD HH:mm')}
                formatter={(value: number) => value.toLocaleString()}
              />
              <Line type="monotone" dataKey="boxesProcessed" stroke="#2563eb" strokeWidth={2} dot={false} name="Boxes" />
              <Line type="monotone" dataKey="exceptions" stroke="#f97316" strokeWidth={2} dot={false} name="Exceptions" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.liveFeed')}</CardTitle>
            <CardDescription>WebSocket status: {status}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No live events yet.</p>
            ) : (
              <ul className="space-y-2">
                {events.map((event) => (
                  <li key={event.id} className="rounded-md border p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{event.boxId}</span>
                      <span className="text-muted-foreground">
                        {dayjs(event.occurredAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{event.status}</p>
                    {event.description ? <p className="text-xs text-muted-foreground">{event.description}</p> : null}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.kpis')}</CardTitle>
            <CardDescription>{t('dashboard.throughput')}</CardDescription>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => dayjs(value).tz(timezone).format('MM-DD')} />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => dayjs(value).tz(timezone).format('YYYY-MM-DD HH:mm')}
                  formatter={(value: number) => value.toLocaleString()}
                />
                <Bar dataKey="boxesProcessed" fill="#10b981" name="Boxes" />
                <Bar dataKey="exceptions" fill="#f97316" name="Exceptions" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
