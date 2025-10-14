// generic data table — accepts column defs + data array
export default function Table({ columns = [], data = [], onRowClick }) {
  return (
    <div className="overflow-hidden border border-neutral-200 rounded-2xl shadow-sm bg-white">
      <table className="min-w-full divide-y divide-neutral-200">
        <thead className="bg-bronze-100/40">
          <tr>
            {columns.map((col) => (
              <th
                key={col.accessor}
                className="px-4 py-3 text-left text-sm font-semibold text-bronze-700 uppercase tracking-wide"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>

        <tbody className="divide-y divide-neutral-100">
          {data.length ? (
            data.map((row, i) => (
              <tr
                key={i}
                onClick={() => onRowClick?.(row)}
                className="hover:bg-bronze-50/70 cursor-pointer transition-colors"
              >
                {columns.map((col) => (
                  <td key={col.accessor} className="px-4 py-3 text-sm text-neutral-700">
                    {(() => {
                      const v = row[col.accessor];
                      return v || (col.accessor === "summary" ? "No description available." : "");
                    })()}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="text-center py-8 text-neutral-400 text-sm">
                No records found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
