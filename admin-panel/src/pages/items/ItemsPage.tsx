import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/tables/DataTable';
import { api } from '@/lib/http';
import type { ItemRecord } from '@/types/inventory';
import { useNavigate } from 'react-router-dom';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

const fallbackItems: ItemRecord[] = Array.from({ length: 20 }).map((_, index) => ({
  id: `ITEM-${3000 + index}`,
  name: `Component ${index + 1}`,
  sku: `SKU-${9000 + index}`,
  quantity: Math.round(Math.random() * 1000),
  location: ['Rack A', 'Rack B', 'Rack C'][index % 3],
  updatedAt: dayjs().subtract(index, 'hour').toISOString()
}));

export function ItemsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const timezone = useUIStore((state) => state.timezone);

  const { data = fallbackItems, isLoading, refetch } = useQuery<ItemRecord[]>({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await api.get<ItemRecord[]>('/inventory/items');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const columns = useMemo<ColumnDef<ItemRecord>[]>(
    () => [
      { accessorKey: 'id', header: 'ID' },
      { accessorKey: 'name', header: 'Name' },
      { accessorKey: 'sku', header: 'SKU' },
      { accessorKey: 'quantity', header: 'Qty' },
      { accessorKey: 'location', header: 'Location' },
      {
        accessorKey: 'updatedAt',
        header: 'Updated',
        cell: ({ row }) => dayjs(row.original.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm')
      },
      {
        id: 'actions',
        header: t('actions.view'),
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => navigate(`/items/${row.original.id}`)}>
            {t('actions.view')}
          </Button>
        )
      }
    ],
    [navigate, t, timezone]
  );

  return <DataTable columns={columns} data={data} isLoading={isLoading} onRefresh={() => refetch()} csvFilename="items.csv" />;
}
