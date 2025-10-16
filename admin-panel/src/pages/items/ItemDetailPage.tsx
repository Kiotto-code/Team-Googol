import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/http';
import type { ItemRecord } from '@/types/inventory';
import { dayjs } from '@/lib/dayjs';
import { useUIStore } from '@/store/ui';

export function ItemDetailPage() {
  const { itemId } = useParams();
  const timezone = useUIStore((state) => state.timezone);

  const { data } = useQuery<ItemRecord>({
    queryKey: ['items', itemId],
    enabled: Boolean(itemId),
    queryFn: async () => {
      const response = await api.get<ItemRecord>(`/inventory/items/${itemId}`);
      return response.data;
    }
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
    <Card>
      <CardHeader>
        <CardTitle>{data.name}</CardTitle>
        <CardDescription>SKU: {data.sku}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        <div>
          <span className="text-sm text-muted-foreground">Quantity</span>
          <p className="text-lg font-semibold">{data.quantity}</p>
        </div>
        <div>
          <span className="text-sm text-muted-foreground">Location</span>
          <p className="text-lg font-semibold">{data.location}</p>
        </div>
        <div>
          <span className="text-sm text-muted-foreground">Updated</span>
          <p className="text-lg font-semibold">{dayjs(data.updatedAt).tz(timezone).format('YYYY-MM-DD HH:mm:ss')}</p>
        </div>
      </CardContent>
    </Card>
  );
}
