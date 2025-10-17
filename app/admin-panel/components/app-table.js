function createSkeletonCell() {
  const span = document.createElement('span');
  span.className = 'skeleton-line';
  return span;
}

function createSkeletonRow(columnCount = 4) {
  const row = document.createElement('div');
  row.className = 'table__skeleton-row';
  for (let i = 0; i < columnCount; i += 1) {
    row.appendChild(createSkeletonCell());
  }
  return row;
}

export function createTable({
  columns,
  rows,
  emptyState,
  isLoading,
  onRowClick,
}) {
  const container = document.createElement('div');
  container.setAttribute('role', 'region');
  container.setAttribute('aria-live', 'polite');

  const table = document.createElement('table');
  table.className = 'table';
  table.createTHead();
  const headRow = table.tHead.insertRow();
  columns.forEach((column) => {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = column.label;
    if (column.width) {
      th.style.width = column.width;
    }
    headRow.appendChild(th);
  });

  const tbody = table.createTBody();

  if (isLoading) {
    const skeletonRow = tbody.insertRow();
    const cell = skeletonRow.insertCell();
    cell.colSpan = columns.length;
    cell.appendChild(createSkeletonRow(columns.length));
  } else if (!rows || rows.length === 0) {
    const emptyRow = tbody.insertRow();
    const cell = emptyRow.insertCell();
    cell.colSpan = columns.length;
    const empty = document.createElement('div');
    empty.className = 'table__empty';
    empty.innerHTML = emptyState || 'No records found.';
    cell.appendChild(empty);
  } else {
    rows.forEach((row) => {
      const tr = tbody.insertRow();
      if (onRowClick) {
        tr.style.cursor = 'pointer';
        tr.addEventListener('click', () => onRowClick(row));
        tr.setAttribute('tabindex', '0');
        tr.addEventListener('keypress', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onRowClick(row);
          }
        });
      }
      columns.forEach((column) => {
        const cell = tr.insertCell();
        const value = typeof column.accessor === 'function'
          ? column.accessor(row)
          : row[column.accessor];
        if (value instanceof Node) {
          cell.appendChild(value);
        } else if (value !== undefined && value !== null) {
          cell.textContent = value;
        } else {
          cell.innerHTML = '&mdash;';
        }
      });
    });
  }

  container.appendChild(table);
  return container;
}
