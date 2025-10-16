import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/http';
import { useTranslation } from 'react-i18next';

interface ReportSummary {
  id: string;
  name: string;
  description: string;
  format: 'csv' | 'pdf';
}

const fallbackReports: ReportSummary[] = [
  { id: 'inventory', name: 'Inventory snapshot', description: 'Current inventory by location', format: 'csv' },
  { id: 'exceptions', name: 'Exceptions', description: 'Outstanding cases and alerts', format: 'csv' },
  { id: 'users', name: 'User access', description: 'Admin users with roles', format: 'pdf' }
];

export function ReportsPage() {
  const { t } = useTranslation();
  const { data = fallbackReports, isFetching, refetch } = useQuery<ReportSummary[]>({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get<ReportSummary[]>('/reports');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const handleDownload = async (report: ReportSummary) => {
    const response = await api.get(`/reports/${report.id}`, { responseType: 'blob' });
    const blob = new Blob([response.data], { type: report.format === 'csv' ? 'text/csv' : 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.id}.${report.format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('reports.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('reports.description')}</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? 'Refreshing...' : t('actions.refresh')}
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data.map((report) => (
          <Card key={report.id} className="flex flex-col justify-between">
            <div>
              <CardHeader>
                <CardTitle>{report.name}</CardTitle>
                <CardDescription>{report.description}</CardDescription>
              </CardHeader>
            </div>
            <CardContent>
              <Button onClick={() => handleDownload(report)}>{t('reports.download')}</Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
