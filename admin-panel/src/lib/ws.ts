import { useEffect, useRef } from "react"
import { resolveWsUrl } from "./utils"
import { type Box } from "../types"

export interface BoxesWsMessage {
  type: "box-status"
  payload: Pick<Box, "id" | "status" | "location"> & Partial<Box>
}

export const SOCKET_RECONNECT_DELAY = 2000

export const useBoxesSocket = (onMessage: (message: BoxesWsMessage) => void) => {
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    let isActive = true

    const connect = () => {
      if (!isActive) return
      const ws = new WebSocket(resolveWsUrl("/api/v1/admin/ws/boxes"))
      socketRef.current = ws

      const handleMessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as BoxesWsMessage
          handlerRef.current?.(data)
        } catch (error) {
          console.error("Failed to parse box websocket payload", error)
        }
      }

      const scheduleReconnect = () => {
        if (!isActive || reconnectTimeoutRef.current) return
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = undefined
          connect()
        }, SOCKET_RECONNECT_DELAY)
      }

      const handleDisconnect = () => {
        ws.removeEventListener("message", handleMessage)
        ws.removeEventListener("close", handleDisconnect)
        ws.removeEventListener("error", handleDisconnect)
        if (socketRef.current === ws) {
          socketRef.current = null
        }
        scheduleReconnect()
      }

      ws.addEventListener("message", handleMessage)
      ws.addEventListener("close", handleDisconnect)
      ws.addEventListener("error", handleDisconnect)
    }

    connect()

    return () => {
      isActive = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = undefined
      }
      if (socketRef.current) {
        const ws = socketRef.current
        socketRef.current = null
        ws.close()
      }
    }
  }, [])
}
