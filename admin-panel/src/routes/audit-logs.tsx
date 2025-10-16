import { useEffect, useState } from "react"
import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../components/common/data-table"
import { AuditLog } from "../types"
import { api } from "../lib/api-client"

const columns: ColumnDef<AuditLog>[] = [
  { accessorKey: "timestamp", header: "Timestamp", cell: ({ row }) => new Date(row.original.timestamp).toLocaleString() },
  { accessorKey: "actor", header: "Actor" },
  { accessorKey: "action", header: "Action" },
  { accessorKey: "resource", header: "Resource" },
]

export const AuditLogsRoute = () => {
  const [logs, setLogs] = useState<AuditLog[]>([])

  useEffect(() => {
    api.get<AuditLog[]>("/audit/logs").then((response) => setLogs(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Audit Logs</h1>
      <DataTable data={logs} columns={columns} />
    </div>
  )
}
