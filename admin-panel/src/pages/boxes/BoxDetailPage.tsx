import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { api } from '@/lib/http';
import type { Box } from '@/types/inventory';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';
import { useState } from 'react';
import { toast } from 'sonner';

export function BoxDetailPage() {
  const { boxId } = useParams();
  const timezone = useUIStore((state) => state.timezone);
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState<'suspend' | 'delete' | null>(null);

  const { data } = useQuery<Box>({
    queryKey: ['boxes', boxId],
    enabled: Boolean(boxId),
    queryFn: async () => {
      const response = await api.get<Box>(`/inventory/boxes/${boxId}`);
      return response.data;
    }
  });

  const mutation = useMutation({
    mutationFn: async (action: 'suspend' | 'delete') => {
      if (!boxId) return;
      await api.post(`/inventory/boxes/${boxId}/${action}`);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['boxes'] });
      toast.success('Action completed');
      setOpenDialog(null);
    },
    onError: () => {
      toast.error('Failed to perform action');
    }
  });

  if (!data) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Loading...</CardTitle>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{data.id}</CardTitle>
          <CardDescription>Status: {data.status}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <div>
            <span className="text-sm font-medium text-muted-foreground">Owner</span>
            <p className="text-lg font-semibold">{data.owner}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-muted-foreground">Location</span>
            <p className="text-lg font-semibold">{data.location}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-muted-foreground">Updated at</span>
            <p className="text-lg font-semibold">
              {dayjs(data.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Dialog open={openDialog === 'suspend'} onOpenChange={(open) => setOpenDialog(open ? 'suspend' : null)}>
          <DialogTrigger asChild>
            <Button variant="outline">Suspend box</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm suspension</DialogTitle>
              <DialogDescription>This action will pause box processing until manual review.</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setOpenDialog(null)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => mutation.mutate('suspend')}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? 'Processing...' : 'Confirm'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={openDialog === 'delete'} onOpenChange={(open) => setOpenDialog(open ? 'delete' : null)}>
          <DialogTrigger asChild>
            <Button variant="destructive">Delete box</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm deletion</DialogTitle>
              <DialogDescription>This will permanently remove this box record.</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setOpenDialog(null)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => mutation.mutate('delete')}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? 'Processing...' : 'Confirm'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
