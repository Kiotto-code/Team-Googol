import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from './DataTable';

type Row = {
  id: number;
  name: string;
  status: string;
};

const columns: ColumnDef<Row>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => row.original.name
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => row.original.status
  }
];

describe('DataTable', () => {
  it('filters rows via the global search input', async () => {
    const user = userEvent.setup();
    const data: Row[] = [
      { id: 1, name: 'Alpha', status: 'open' },
      { id: 2, name: 'Beta', status: 'closed' },
      { id: 3, name: 'Gamma', status: 'open' }
    ];

    render(<DataTable columns={columns} data={data} />);

    await user.type(screen.getByPlaceholderText('tables.search'), 'Alpha');

    const table = screen.getByRole('table');
    const bodyRows = within(table).getAllByRole('row');

    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.queryByText('Beta')).not.toBeInTheDocument();
    expect(bodyRows.length).toBeGreaterThan(1);
  });

  it('navigates between pages with the pagination controls', async () => {
    const user = userEvent.setup();
    const data: Row[] = Array.from({ length: 15 }, (_, index) => ({
      id: index + 1,
      name: `Item ${index + 1}`,
      status: index % 2 === 0 ? 'open' : 'closed'
    }));

    render(<DataTable columns={columns} data={data} />);

    expect(screen.getByText('Item 1')).toBeInTheDocument();

    const nextButtons = screen.getAllByRole('button', { name: /Next/i });
    await user.click(nextButtons[nextButtons.length - 1]);

    expect(screen.getByText('Item 11')).toBeInTheDocument();
    expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
  });
});
