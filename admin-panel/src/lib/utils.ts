import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const apiBase = "/api/v1/admin"

export const wsBase = ((): string => {
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss" : "ws"
  const host = typeof window !== "undefined" ? window.location.host : ""
  return `${protocol}://${host}`
})()

export const resolveWsUrl = (path: string) => `${wsBase}${path}`
