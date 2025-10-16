import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { api } from '@/lib/http';
import type { UserRecord } from '@/types/inventory';
import { useState } from 'react';
import { toast } from 'sonner';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

export function UserDetailPage() {
  const { userId } = useParams();
  const timezone = useUIStore((state) => state.timezone);
  const [dialog, setDialog] = useState<'suspend' | 'activate' | null>(null);
  const queryClient = useQueryClient();

  const { data } = useQuery<UserRecord>({
    queryKey: ['users', userId],
    enabled: Boolean(userId),
    queryFn: async () => {
      const response = await api.get<UserRecord>(`/admin/users/${userId}`);
      return response.data;
    }
  });

  const mutation = useMutation({
    mutationFn: async (action: 'suspend' | 'activate') => {
      if (!userId) return;
      await api.post(`/admin/users/${userId}/${action}`);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success('User updated');
      setDialog(null);
    },
    onError: () => toast.error('Failed to update user')
  });

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading...</CardTitle>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{data.name}</CardTitle>
          <CardDescription>{data.email}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <div>
            <span className="text-sm text-muted-foreground">Roles</span>
            <p className="text-lg font-semibold">{data.roles.join(', ')}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Status</span>
            <p className="text-lg font-semibold">{data.status}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Last login</span>
            <p className="text-lg font-semibold">{dayjs(data.lastLoginAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')}</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Dialog open={dialog === 'suspend'} onOpenChange={(open) => setDialog(open ? 'suspend' : null)}>
          <DialogTrigger asChild>
            <Button variant="destructive">Suspend user</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Suspend this user?</DialogTitle>
              <DialogDescription>User access will be revoked immediately.</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setDialog(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => mutation.mutate('suspend')} disabled={mutation.isPending}>
                {mutation.isPending ? 'Processing...' : 'Confirm'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={dialog === 'activate'} onOpenChange={(open) => setDialog(open ? 'activate' : null)}>
          <DialogTrigger asChild>
            <Button variant="outline">Re-activate user</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Re-activate user?</DialogTitle>
              <DialogDescription>Restore access to the admin panel.</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setDialog(null)}>
                Cancel
              </Button>
              <Button onClick={() => mutation.mutate('activate')} disabled={mutation.isPending}>
                {mutation.isPending ? 'Processing...' : 'Confirm'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
