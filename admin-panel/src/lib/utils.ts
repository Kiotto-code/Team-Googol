import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const env = import.meta.env

const resolvedApiBase = env.VITE_API_BASE_URL?.trim()
export const apiBase = resolvedApiBase && resolvedApiBase.length > 0 ? resolvedApiBase : "/api/v1/admin"

const resolvedWsBase = env.VITE_WS_URL?.trim()
export const wsBase = ((): string => {
  if (resolvedWsBase && resolvedWsBase.length > 0) {
    return resolvedWsBase
  }
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss" : "ws"
  const host = typeof window !== "undefined" ? window.location.host : ""
  return `${protocol}://${host}`
})()

export const resolveWsUrl = (path: string) => `${wsBase}${path}`
