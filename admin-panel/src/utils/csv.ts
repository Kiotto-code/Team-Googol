export function exportToCsv<T extends Record<string, unknown>>(filename: string, rows: T[], columns?: string[]) {
  if (!rows.length) {
    return;
  }

  const headers = columns ?? Object.keys(rows[0]);
  const csv = [headers.join(',')]
    .concat(
      rows.map((row) =>
        headers
          .map((field) => {
            const value = row[field];
            if (value === null || value === undefined) {
              return '';
            }
            const escaped = String(value).replace(/"/g, '""');
            if (escaped.search(/[",\n]/g) >= 0) {
              return `"${escaped}"`;
            }
            return escaped;
          })
          .join(',')
      )
    )
    .join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.click();
  URL.revokeObjectURL(url);
}
