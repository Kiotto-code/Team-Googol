import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import { ColumnDef } from "@tanstack/react-table"

import { DataTable } from "../components/common/data-table"

type Person = {
  id: string
  name: string
  role: string
}

describe("DataTable", () => {
  const rows: Person[] = Array.from({ length: 12 }, (_, index) => ({
    id: `${index + 1}`,
    name: `User ${index + 1}`,
    role: index % 2 === 0 ? "Admin" : "Viewer",
  }))

  const columns: ColumnDef<Person>[] = [
    {
      accessorKey: "name",
      header: ({ column }) => (
        <label className="flex flex-col gap-1 text-left">
          <span>Name</span>
          <input
            aria-label="Filter by name"
            value={(column.getFilterValue() as string) ?? ""}
            onChange={(event) => column.setFilterValue(event.target.value)}
          />
        </label>
      ),
      cell: ({ getValue }) => <span>{getValue<string>()}</span>,
    },
    { accessorKey: "role", header: "Role", cell: ({ getValue }) => <span>{getValue<string>()}</span> },
  ]

  it("supports pagination controls and column filtering", async () => {
    const user = userEvent.setup()
    render(<DataTable data={rows} columns={columns} pageSize={5} />)

    expect(screen.getByText("User 1")).toBeInTheDocument()
    expect(screen.queryByText("User 11")).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Next/i }))

    expect(await screen.findByText("User 6")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Next/i }))

    expect(await screen.findByText("User 11")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Previous/i }))
    expect(await screen.findByText("User 6")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Previous/i }))
    expect(await screen.findByText("User 1")).toBeInTheDocument()

    await user.type(screen.getByLabelText(/Filter by name/i), "User 3")

    expect(await screen.findByText("User 3")).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText("User 1")).not.toBeInTheDocument())
  })
})
