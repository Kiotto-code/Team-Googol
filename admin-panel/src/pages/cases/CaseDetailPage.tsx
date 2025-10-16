import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { CaseRecord } from '@/types/inventory';
import { api } from '@/lib/http';
import { useState } from 'react';
import { toast } from 'sonner';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

export function CaseDetailPage() {
  const { caseId } = useParams();
  const timezone = useUIStore((state) => state.timezone);
  const queryClient = useQueryClient();
  const [dialog, setDialog] = useState<'resolve' | null>(null);

  const { data } = useQuery<CaseRecord>({
    queryKey: ['cases', caseId],
    enabled: Boolean(caseId),
    queryFn: async () => {
      const response = await api.get<CaseRecord>(`/investigations/cases/${caseId}`);
      return response.data;
    }
  });

  const mutation = useMutation({
    mutationFn: async () => {
      if (!caseId) return;
      await api.post(`/investigations/cases/${caseId}/resolve`);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cases'] });
      toast.success('Case resolved');
      setDialog(null);
    },
    onError: () => toast.error('Failed to resolve case')
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
          <CardTitle>{data.id}</CardTitle>
          <CardDescription>Box: {data.boxId}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <div>
            <span className="text-sm text-muted-foreground">Priority</span>
            <p className="text-lg font-semibold">{data.priority}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Status</span>
            <p className="text-lg font-semibold">{data.status}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Assignee</span>
            <p className="text-lg font-semibold">{data.assignee}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Updated</span>
            <p className="text-lg font-semibold">{dayjs(data.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')}</p>
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialog === 'resolve'} onOpenChange={(open) => setDialog(open ? 'resolve' : null)}>
        <DialogTrigger asChild>
          <Button variant="outline">Resolve case</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve this case?</DialogTitle>
            <DialogDescription>This will mark the investigation as completed.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialog(null)}>
              Cancel
            </Button>
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
