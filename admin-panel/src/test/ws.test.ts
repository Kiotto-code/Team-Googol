import { act, renderHook } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { SOCKET_RECONNECT_DELAY, useBoxesSocket } from "../lib/ws"

class MockWebSocket {
  static instances: MockWebSocket[] = []

  public url: string
  public readyState = 1
  private listeners: Map<string, Set<(event: any) => void>> = new Map()

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  addEventListener(type: string, listener: (event: any) => void) {
    const existing = this.listeners.get(type) ?? new Set()
    existing.add(listener)
    this.listeners.set(type, existing)
  }

  removeEventListener(type: string, listener: (event: any) => void) {
    const existing = this.listeners.get(type)
    existing?.delete(listener)
  }

  close() {
    this.readyState = 3
  }

  dispatch(type: string, event: any = {}) {
    this.listeners.get(type)?.forEach((listener) => listener(event))
  }
}

describe("useBoxesSocket", () => {
  const originalWebSocket = globalThis.WebSocket

  beforeEach(() => {
    MockWebSocket.instances = []
    ;(globalThis as { WebSocket: typeof WebSocket }).WebSocket = MockWebSocket as unknown as typeof WebSocket
  })

  afterEach(() => {
    ;(globalThis as { WebSocket: typeof WebSocket }).WebSocket = originalWebSocket
    MockWebSocket.instances = []
    vi.useRealTimers()
  })

  it("reconnects after the socket closes", async () => {
    vi.useFakeTimers()
    const handler = vi.fn()

    const { unmount } = renderHook(() => useBoxesSocket(handler))

    expect(MockWebSocket.instances).toHaveLength(1)

    act(() => {
      MockWebSocket.instances[0].dispatch("close")
    })

    await act(async () => {
      vi.advanceTimersByTime(SOCKET_RECONNECT_DELAY)
      await Promise.resolve()
    })

    expect(MockWebSocket.instances).toHaveLength(2)

    unmount()
  })
})
