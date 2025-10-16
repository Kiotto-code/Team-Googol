import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/tables/DataTable';
import { api } from '@/lib/http';
import type { UserRecord } from '@/types/inventory';
import { useNavigate } from 'react-router-dom';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

const fallbackUsers: UserRecord[] = Array.from({ length: 10 }).map((_, index) => ({
  id: `USR-${index + 1}`,
  name: ['Maya', 'Ethan', 'Sofia', 'Liam'][index % 4],
  email: `user${index + 1}@example.com`,
  roles: index % 2 === 0 ? ['admin'] : ['viewer'],
  lastLoginAt: dayjs().subtract(index, 'day').toISOString(),
  status: index % 3 === 0 ? 'suspended' : 'active'
}));

export function UsersPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const timezone = useUIStore((state) => state.timezone);

  const { data = fallbackUsers, isLoading, refetch } = useQuery<UserRecord[]>({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get<UserRecord[]>('/admin/users');
      return response.data;
    },
    staleTime: 1000 * 60
  });

  const columns = useMemo<ColumnDef<UserRecord>[]>(
    () => [
      { accessorKey: 'name', header: 'Name' },
      { accessorKey: 'email', header: 'Email' },
      {
        accessorKey: 'roles',
        header: 'Roles',
        cell: ({ row }) => row.original.roles.join(', ')
      },
      {
        accessorKey: 'status',
        header: 'Status'
      },
      {
        accessorKey: 'lastLoginAt',
        header: 'Last login',
        cell: ({ row }) => dayjs(row.original.lastLoginAt).tz(timezone).format('YYYY-MM-DD HH:mm')
      },
      {
        id: 'actions',
        header: t('actions.view'),
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => navigate(`/users/${row.original.id}`)}>
            {t('actions.view')}
          </Button>
        )
      }
    ],
    [navigate, t, timezone]
  );

  return <DataTable columns={columns} data={data} isLoading={isLoading} onRefresh={() => refetch()} csvFilename="users.csv" />;
}
