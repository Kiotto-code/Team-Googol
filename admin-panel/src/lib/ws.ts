import { useEffect, useRef } from "react"
import { resolveWsUrl } from "./utils"
import { type Box } from "../types"

export interface BoxesWsMessage {
  type: "box-status"
  payload: Pick<Box, "id" | "status" | "location"> & Partial<Box>
}

export const useBoxesSocket = (onMessage: (message: BoxesWsMessage) => void) => {
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage

  useEffect(() => {
    const ws = new WebSocket(resolveWsUrl("/api/v1/admin/ws/boxes"))
    ws.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data) as BoxesWsMessage
        handlerRef.current?.(data)
      } catch (error) {
        console.error("Failed to parse box websocket payload", error)
      }
    })

    return () => {
      ws.close()
    }
  }, [])
}
