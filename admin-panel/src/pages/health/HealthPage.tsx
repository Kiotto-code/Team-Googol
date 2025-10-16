import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/http';
import { useTranslation } from 'react-i18next';

interface HealthCheck {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  message?: string;
  latencyMs?: number;
}

const fallbackHealth: HealthCheck[] = [
  { name: 'Database', status: 'healthy', latencyMs: 32 },
  { name: 'Redis', status: 'healthy', latencyMs: 12 },
  { name: 'Worker queue', status: 'degraded', latencyMs: 120, message: 'Retry backlog increasing' }
];

const statusColor: Record<HealthCheck['status'], string> = {
  healthy: 'text-emerald-600',
  degraded: 'text-amber-500',
  down: 'text-red-600'
};

export function HealthPage() {
  const { t } = useTranslation();
  const { data = fallbackHealth, isLoading, refetch, isFetching } = useQuery<HealthCheck[]>({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await api.get<HealthCheck[]>('/health');
      return response.data;
    },
    staleTime: 1000 * 30
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('health.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('health.description')}</p>
        </div>
        <button
          className="inline-flex items-center rounded-md border border-input bg-background px-3 py-2 text-sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          {isFetching ? 'Refreshing...' : t('actions.refresh')}
        </button>
      </div>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((check) => (
            <Card key={check.name}>
              <CardHeader>
                <CardTitle>{check.name}</CardTitle>
                <CardDescription className={statusColor[check.status]}>{check.status.toUpperCase()}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {check.latencyMs ? <p className="text-sm">Latency: {check.latencyMs} ms</p> : null}
                {check.message ? <p className="text-sm text-muted-foreground">{check.message}</p> : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
