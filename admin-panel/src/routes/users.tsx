import { useEffect, useState } from "react"
import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../components/common/data-table"
import { api } from "../lib/api-client"
import { Badge } from "../components/ui/badge"

interface AdminListUser {
  id: string
  email: string
  name: string
  roles: string[]
  lastSeen: string
}

const columns: ColumnDef<AdminListUser>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "email", header: "Email" },
  {
    accessorKey: "roles",
    header: "Roles",
    cell: ({ row }) => (
      <div className="flex flex-wrap gap-1">
        {row.original.roles.map((role) => (
          <Badge key={role} variant="outline">
            {role}
          </Badge>
        ))}
      </div>
    ),
  },
  { accessorKey: "lastSeen", header: "Last seen", cell: ({ row }) => new Date(row.original.lastSeen).toLocaleString() },
]

export const UsersRoute = () => {
  const [users, setUsers] = useState<AdminListUser[]>([])

  useEffect(() => {
    api.get<AdminListUser[]>("/users").then((response) => setUsers(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Users</h1>
      <DataTable data={users} columns={columns} />
    </div>
  )
}
