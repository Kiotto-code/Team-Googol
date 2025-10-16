export type Box = {
  id: string
  status: "available" | "processing" | "complete"
  location: string
  updated_at: string
}

export type Case = {
  id: string
  priority: "low" | "medium" | "high"
  assignee: string
  created_at: string
}

export type InventoryItem = {
  id: string
  name: string
  quantity: number
  location: string
}

export type AuditLog = {
  id: string
  actor: string
  action: string
  resource: string
  timestamp: string
}

export type MetricPoint = {
  label: string
  value: number
}

export type HealthCheck = {
  service: string
  status: "healthy" | "degraded" | "down"
  message?: string
}
