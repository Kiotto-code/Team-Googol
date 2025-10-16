import { useEffect, useState } from "react"
import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../components/common/data-table"
import { Case } from "../types"
import { api } from "../lib/api-client"
import { Badge } from "../components/ui/badge"

const columns: ColumnDef<Case>[] = [
  { accessorKey: "id", header: "Case" },
  {
    accessorKey: "priority",
    header: "Priority",
    cell: ({ row }) => <Badge variant={row.original.priority === "high" ? "destructive" : "secondary"}>{row.original.priority}</Badge>,
  },
  { accessorKey: "assignee", header: "Assignee" },
  { accessorKey: "created_at", header: "Created", cell: ({ row }) => new Date(row.original.created_at).toLocaleString() },
]

export const CasesRoute = () => {
  const [cases, setCases] = useState<Case[]>([])

  useEffect(() => {
    api.get<Case[]>("/cases").then((response) => setCases(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Cases</h1>
      <DataTable data={cases} columns={columns} />
    </div>
  )
}
