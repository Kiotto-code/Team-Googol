import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/tables/DataTable';
import { api } from '@/lib/http';
import type { AuditLog } from '@/types/inventory';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

const fallbackAudit: AuditLog[] = Array.from({ length: 25 }).map((_, index) => ({
  id: `AUD-${index + 1}`,
  actor: ['Maya', 'Ethan', 'Sofia', 'Liam'][index % 4],
  action: ['login', 'update_box', 'resolve_case', 'download_report'][index % 4],
  entity: ['BOX-1001', 'CASE-2001', 'USER-1'][index % 3],
  createdAt: dayjs().subtract(index, 'hour').toISOString(),
  details: 'Sample audit record'
}));

export function AuditLogsPage() {
  const timezone = useUIStore((state) => state.timezone);

  const { data = fallbackAudit, isLoading, refetch } = useQuery<AuditLog[]>({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const response = await api.get<AuditLog[]>('/admin/audit');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const columns = useMemo<ColumnDef<AuditLog>[]>(
    () => [
      { accessorKey: 'actor', header: 'Actor' },
      { accessorKey: 'action', header: 'Action' },
      { accessorKey: 'entity', header: 'Entity' },
      {
        accessorKey: 'createdAt',
        header: 'Timestamp',
        cell: ({ row }) => dayjs(row.original.createdAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')
      },
      { accessorKey: 'details', header: 'Details' }
    ],
    [timezone]
  );

  return <DataTable columns={columns} data={data} isLoading={isLoading} onRefresh={() => refetch()} csvFilename="audit.csv" />;
}
