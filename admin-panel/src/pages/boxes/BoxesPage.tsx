import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/tables/DataTable';
import { api } from '@/lib/http';
import type { Box } from '@/types/inventory';
import { useNavigate } from 'react-router-dom';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

const fallbackBoxes: Box[] = Array.from({ length: 15 }).map((_, index) => ({
  id: `BOX-${1000 + index}`,
  status: ['pending', 'in_transit', 'delivered', 'exception'][index % 4] as Box['status'],
  location: ['KUL', 'SIN', 'BKK'][index % 3],
  updatedAt: dayjs().subtract(index, 'hour').toISOString(),
  owner: ['Alice', 'Bob', 'Charlie'][index % 3]
}));

export function BoxesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const timezone = useUIStore((state) => state.timezone);

  const { data = fallbackBoxes, isLoading, refetch } = useQuery<Box[]>({
    queryKey: ['boxes'],
    queryFn: async () => {
      const response = await api.get<Box[]>('/inventory/boxes');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const columns = useMemo<ColumnDef<Box>[]>(
    () => [
      {
        accessorKey: 'id',
        header: 'ID'
      },
      {
        accessorKey: 'status',
        header: 'Status'
      },
      {
        accessorKey: 'location',
        header: 'Location'
      },
      {
        accessorKey: 'owner',
        header: 'Owner'
      },
      {
        accessorKey: 'updatedAt',
        header: 'Updated',
        cell: ({ row }) => dayjs(row.original.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm')
      },
      {
        id: 'actions',
        header: t('actions.view'),
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => navigate(`/boxes/${row.original.id}`)}>
            {t('actions.view')}
          </Button>
        )
      }
    ],
    [navigate, t, timezone]
  );

  return <DataTable columns={columns} data={data} isLoading={isLoading} onRefresh={() => refetch()} csvFilename="boxes.csv" />;
}
