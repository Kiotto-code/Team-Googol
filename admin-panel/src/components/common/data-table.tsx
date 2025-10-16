import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type RowSelectionState,
  type SortingState,
  type TableOptions,
  type Updater,
} from "@tanstack/react-table"
import { useMemo, useState, type ReactNode } from "react"
import { Button } from "../ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { cn } from "../../lib/utils"

export interface DataTableProps<TData, TValue> {
  data: TData[]
  columns: ColumnDef<TData, TValue>[]
  bulkActions?: ReactNode
  className?: string
  rowSelection?: RowSelectionState
  onRowSelectionChange?: (value: RowSelectionState) => void
  getRowId?: TableOptions<TData>["getRowId"]
}

export function DataTable<TData, TValue>({
  data,
  columns,
  bulkActions,
  className,
  rowSelection: externalRowSelection,
  onRowSelectionChange,
  getRowId,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [internalRowSelection, setInternalRowSelection] = useState<RowSelectionState>({})

  const rowSelection = externalRowSelection ?? internalRowSelection

  const handleRowSelectionChange = (updater: Updater<RowSelectionState>) => {
    const nextValue = typeof updater === "function" ? updater(rowSelection) : updater
    setInternalRowSelection(nextValue)
    onRowSelectionChange?.(nextValue)
  }

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, rowSelection },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onRowSelectionChange: handleRowSelectionChange,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getRowId,
    enableRowSelection: true,
  })

  const selectedCount = Object.values(rowSelection ?? {}).filter(Boolean).length
  const hasBulkActions = !!bulkActions && selectedCount > 0

  const headerGroups = useMemo(() => table.getHeaderGroups(), [table, sorting, columnFilters, rowSelection, data])
  const rowModel = useMemo(() => table.getRowModel(), [table, sorting, columnFilters, rowSelection, data])

  return (
    <div className={cn("space-y-4", className)}>
      {hasBulkActions ? (
        <div className="flex items-center justify-between rounded-md border bg-muted/40 p-3">{bulkActions}</div>
      ) : null}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {headerGroups.map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rowModel.rows.length ? (
              rowModel.rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() ? "selected" : undefined}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  No data available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
          Previous
        </Button>
        <Button size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
          Next
        </Button>
      </div>
    </div>
  )
}
