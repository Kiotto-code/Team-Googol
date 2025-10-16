import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useBoxEvents } from './useBoxEvents';

const authState = {
  accessToken: 'abc123'
};

vi.mock('@/store/auth', () => ({
  useAuthStore: <T,>(selector: (state: typeof authState) => T) => selector(authState)
}));

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState = MockWebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent | Event) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public send = vi.fn();
  public close = vi.fn();

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }
}

declare global {
  interface Window {
    WebSocket: typeof MockWebSocket;
  }
}

let reconnectCallback: (() => void) | null = null;

describe('useBoxEvents', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    window.WebSocket = MockWebSocket as unknown as typeof WebSocket;
    globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
    const originalSetTimeout = window.setTimeout;
    vi.spyOn(window, 'setTimeout').mockImplementation(((callback: TimerHandler, delay?: number, ...args: unknown[]) => {
      if (typeof callback === 'function' && delay === 5000) {
        reconnectCallback = () => {
          (callback as (...cbArgs: unknown[]) => void)(...args);
        };
        return 0 as unknown as number;
      }
      return originalSetTimeout(callback, delay as number, ...(args as unknown[]));
    }) as unknown as typeof window.setTimeout);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    reconnectCallback = null;
  });

  it('attempts to reconnect after the socket closes', async () => {
    const { result, unmount } = renderHook(() => useBoxEvents());

    expect(result.current.status).toBe('connecting');
    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => {
      const socket = MockWebSocket.instances[0];
      socket.readyState = MockWebSocket.OPEN;
      socket.onopen?.(new Event('open'));
    });

    await waitFor(() => expect(result.current.status).toBe('open'));

    act(() => {
      const socket = MockWebSocket.instances[0];
      socket.readyState = MockWebSocket.CLOSED;
      socket.onclose?.(new Event('close'));
    });

    await waitFor(() => expect(result.current.status).toBe('closed'));

    act(() => {
      reconnectCallback?.();
    });

    await waitFor(() => expect(MockWebSocket.instances.length).toBe(2));
    await waitFor(() => expect(result.current.status).toBe('connecting'));

    unmount();
  });
});
