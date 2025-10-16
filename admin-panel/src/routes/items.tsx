import { useEffect, useState } from "react"
import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../components/common/data-table"
import { InventoryItem } from "../types"
import { api } from "../lib/api-client"

const columns: ColumnDef<InventoryItem>[] = [
  { accessorKey: "id", header: "Item" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "quantity", header: "Qty" },
  { accessorKey: "location", header: "Location" },
]

export const ItemsRoute = () => {
  const [items, setItems] = useState<InventoryItem[]>([])

  useEffect(() => {
    api.get<InventoryItem[]>("/items").then((response) => setItems(response.data))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Items</h1>
      <DataTable data={items} columns={columns} />
    </div>
  )
}
