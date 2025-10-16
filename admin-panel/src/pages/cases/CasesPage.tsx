import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/tables/DataTable';
import { api } from '@/lib/http';
import type { CaseRecord } from '@/types/inventory';
import { useNavigate } from 'react-router-dom';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

const fallbackCases: CaseRecord[] = Array.from({ length: 12 }).map((_, index) => ({
  id: `CASE-${2000 + index}`,
  boxId: `BOX-${1000 + index}`,
  priority: ['low', 'medium', 'high'][index % 3] as CaseRecord['priority'],
  status: ['open', 'investigating', 'resolved'][index % 3] as CaseRecord['status'],
  assignee: ['Ivy', 'Noah', 'Leo'][index % 3],
  updatedAt: dayjs().subtract(index, 'day').toISOString()
}));

export function CasesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const timezone = useUIStore((state) => state.timezone);

  const { data = fallbackCases, isLoading, refetch } = useQuery<CaseRecord[]>({
    queryKey: ['cases'],
    queryFn: async () => {
      const response = await api.get<CaseRecord[]>('/investigations/cases');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const columns = useMemo<ColumnDef<CaseRecord>[]>(
    () => [
      { accessorKey: 'id', header: 'ID' },
      { accessorKey: 'boxId', header: 'Box' },
      { accessorKey: 'priority', header: 'Priority' },
      { accessorKey: 'status', header: 'Status' },
      { accessorKey: 'assignee', header: 'Assignee' },
      {
        accessorKey: 'updatedAt',
        header: 'Updated',
        cell: ({ row }) => dayjs(row.original.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm')
      },
      {
        id: 'actions',
        header: t('actions.view'),
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => navigate(`/cases/${row.original.id}`)}>
            {t('actions.view')}
          </Button>
        )
      }
    ],
    [navigate, t, timezone]
  );

  return <DataTable columns={columns} data={data} isLoading={isLoading} onRefresh={() => refetch()} csvFilename="cases.csv" />;
}
