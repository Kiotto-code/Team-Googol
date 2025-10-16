import { useEffect, useMemo, useState } from "react"
import { ColumnDef, RowSelectionState } from "@tanstack/react-table"
import { Checkbox } from "../components/ui/checkbox"
import { DataTable } from "../components/common/data-table"
import { Box } from "../types"
import { api } from "../lib/api-client"
import { useBoxesSocket, BoxesWsMessage } from "../lib/ws"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"

export const BoxesRoute = () => {
  const [boxes, setBoxes] = useState<Box[]>([])
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({})

  useEffect(() => {
    api.get<Box[]>("/boxes").then((response) => setBoxes(response.data))
  }, [])

  useBoxesSocket((message: BoxesWsMessage) => {
    if (message.type === "box-status") {
      setBoxes((prev) => {
        const existing = prev.find((box) => box.id === message.payload.id)
        const updatedAt = new Date().toISOString()
        if (existing) {
          return prev.map((box) => (box.id === message.payload.id ? { ...box, ...message.payload, updated_at: updatedAt } : box))
        }
        return [...prev, { ...message.payload, updated_at: updatedAt, status: message.payload.status }]
      })
    }
  })

  const columns = useMemo<ColumnDef<Box>[]>(
    () => [
      {
        id: "select",
        header: ({ table }) => (
          <Checkbox
            checked={table.getIsAllPageRowsSelected()}
            onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
            aria-label="Select all"
          />
        ),
        cell: ({ row }) => (
          <Checkbox checked={row.getIsSelected()} onCheckedChange={(value) => row.toggleSelected(!!value)} aria-label="Select row" />
        ),
        enableSorting: false,
        enableHiding: false,
      },
      { accessorKey: "id", header: "Box", cell: ({ row }) => <span className="font-mono text-xs">{row.original.id}</span> },
      { accessorKey: "status", header: "Status", cell: ({ row }) => <Badge variant="secondary">{row.original.status}</Badge> },
      { accessorKey: "location", header: "Location" },
      { accessorKey: "updated_at", header: "Updated", cell: ({ row }) => new Date(row.original.updated_at).toLocaleString() },
    ],
    [],
  )

  const selectedIds = useMemo(() => Object.keys(rowSelection).filter((id) => rowSelection[id]), [rowSelection])

  const handleBulkAction = () => {
    if (!selectedIds.length) return
    void api.post("/boxes/bulk-retry", { ids: selectedIds })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Boxes</h1>
      <DataTable
        data={boxes}
        columns={columns}
        bulkActions={
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{selectedIds.length} selected</span>
            <Button onClick={handleBulkAction}>Retry selected</Button>
          </div>
        }
        getRowId={(row) => row.id}
        rowSelection={rowSelection}
        onRowSelectionChange={setRowSelection}
      />
    </div>
  )
}
