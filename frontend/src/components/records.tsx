"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api";

export function Records<T extends object>({
  title,
  hint,
  queryKey,
  load,
  columns,
  render,
}: {
  title: string;
  hint?: string;
  queryKey: unknown[];
  load: () => Promise<T[]>;
  columns: { key: string; label: string; render?: (row: T) => React.ReactNode }[];
  render?: (row: T) => React.ReactNode;
}) {
  const query = useQuery({ queryKey, queryFn: load });
  return (
    <section className="space-y-4">
      <div>
        <h1 className="serif text-4xl">{title}</h1>
        {hint ? <p className="mt-1 text-sm text-[#6b6258]">{hint}</p> : null}
      </div>
      {query.isLoading ? <p>Loading…</p> : null}
      {query.error ? <p className="text-[#9f2d3a]">{query.error instanceof ApiError ? query.error.message : "Could not load this list."}</p> : null}
      {query.data ? (
        <div className="panel overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[#e2d8c8] text-[#6b6258]">
              <tr>
                {columns.map((column) => (
                  <th key={column.key} className="px-3 py-3 font-medium">
                    {column.label}
                  </th>
                ))}
                {render ? <th className="px-3 py-3" /> : null}
              </tr>
            </thead>
            <tbody>
              {query.data.map((row, index) => (
                <tr key={index} className="border-b border-[#e2d8c8] last:border-0">
                  {columns.map((column) => (
                    <td key={column.key} className="px-3 py-3 align-top">
                      {column.render ? column.render(row) : String((row as Record<string, unknown>)[column.key] ?? "—")}
                    </td>
                  ))}
                  {render ? <td className="px-3 py-3">{render(row)}</td> : null}
                </tr>
              ))}
            </tbody>
          </table>
          {query.data.length === 0 ? <p className="p-4 text-sm text-[#6b6258]">Nothing here yet.</p> : null}
        </div>
      ) : null}
    </section>
  );
}
