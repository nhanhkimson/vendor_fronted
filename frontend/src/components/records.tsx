"use client";

import { useQuery } from "@tanstack/react-query";

import { TableSkeleton } from "@/components/skeletons";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError } from "@/lib/api";

export function Records<T extends object>({
  title,
  hint,
  queryKey,
  load,
  columns,
  render,
  actions,
}: {
  title: string;
  hint?: string;
  queryKey: unknown[];
  load: () => Promise<T[]>;
  columns: { key: string; label: string; render?: (row: T) => React.ReactNode }[];
  render?: (row: T) => React.ReactNode;
  actions?: React.ReactNode;
}) {
  const query = useQuery({ queryKey, queryFn: load });
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="serif text-4xl">{title}</h1>
          {hint ? <p className="mt-1 text-sm text-muted-foreground">{hint}</p> : null}
        </div>
        {actions}
      </div>
      {query.isLoading ? <TableSkeleton columns={columns.length + (render ? 1 : 0)} /> : null}
      {query.error ? (
        <p className="text-sm text-destructive">{query.error instanceof ApiError ? query.error.message : "Could not load this list."}</p>
      ) : null}
      {query.data ? (
        <Card className="py-0">
          <CardContent className="px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((column) => (
                    <TableHead key={column.key}>{column.label}</TableHead>
                  ))}
                  {render ? <TableHead className="w-[1%] whitespace-nowrap">Actions</TableHead> : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {query.data.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.length + (render ? 1 : 0)} className="h-24 text-center text-muted-foreground">
                      Nothing here yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  query.data.map((row, index) => (
                    <TableRow key={index}>
                      {columns.map((column) => (
                        <TableCell key={column.key}>
                          {column.render ? column.render(row) : String((row as Record<string, unknown>)[column.key] ?? "—")}
                        </TableCell>
                      ))}
                      {render ? <TableCell className="text-right">{render(row)}</TableCell> : null}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
