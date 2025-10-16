import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '@/store/auth';

export interface BoxEvent {
  id: string;
  boxId: string;
  status: string;
  occurredAt: string;
  description?: string;
}

type ConnectionStatus = 'connecting' | 'open' | 'closed' | 'error';

export function useBoxEvents() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const [events, setEvents] = useState<BoxEvent[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const reconnectRef = useRef<number | null>(null);
  const heartbeatRef = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${protocol}://${window.location.host}/api/v1/admin/ws/boxes?token=${accessToken}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      setStatus('connecting');

      ws.onopen = () => {
        setStatus('open');
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'boxes' }));
        heartbeatRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'pong') {
            return;
          }
          if (payload.type === 'box_event') {
            setEvents((prev) => [payload.data as BoxEvent, ...prev].slice(0, 20));
          }
        } catch (error) {
          console.error('Failed to parse websocket message', error);
        }
      };

      ws.onerror = () => {
        setStatus('error');
      };

      ws.onclose = () => {
        setStatus('closed');
        if (heartbeatRef.current) {
          window.clearInterval(heartbeatRef.current);
          heartbeatRef.current = null;
        }
        reconnectRef.current = window.setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (reconnectRef.current) {
        window.clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
      wsRef.current?.close();
    };
  }, [accessToken]);

  return { events, status };
}
