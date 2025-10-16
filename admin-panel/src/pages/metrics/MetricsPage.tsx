import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/http';
import { useTranslation } from 'react-i18next';

function parseMetrics(raw: string) {
  return raw
    .split('\n')
    .filter((line) => line && !line.startsWith('#'))
    .slice(0, 50);
}

export function MetricsPage() {
  const { t } = useTranslation();
  const { data, isLoading, refetch, isFetching } = useQuery<string>({
    queryKey: ['metrics'],
    queryFn: async () => {
      const response = await api.get<string>('/metrics', { responseType: 'text' });
      return response.data;
    },
    staleTime: 1000 * 30
  });

  const metrics = data ? parseMetrics(data) : [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('metrics.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('metrics.description')}</p>
        </div>
        <button
          className="inline-flex items-center rounded-md border border-input bg-background px-3 py-2 text-sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          {isFetching ? 'Refreshing...' : t('actions.refresh')}
        </button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Prometheus</CardTitle>
          <CardDescription>Top metrics preview</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : (
            <pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-xs">
              {metrics.length ? metrics.join('\n') : 'No metrics received'}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
