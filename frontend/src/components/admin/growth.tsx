"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { StackSkeleton } from "@/components/skeletons";
import { Button } from "@/components/ui/button";
import { browserApi, unwrap } from "@/lib/api";
import { money } from "@/lib/format";
import { productLabel, shopLabel } from "@/lib/labels";

export function GrowthDashboard({ seller }: { seller: boolean }) {
  const path = seller ? "/api/seller/reports/overview" : "/api/reports/overview";
  const report = useQuery({ queryKey: ["report", path], queryFn: () => unwrap(browserApi.GET(path)) });
  const data = report.data;
  const totals = data?.totals;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="serif text-4xl">{seller ? "Shop reports" : "Growth"}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {seller
              ? "Sales for this shop after customers pay. Commission is taken at checkout."
              : "Platform take is the commission charged when a customer pays. GMV is what buyers spent."}
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <a href={seller ? "/api/seller/reports/sales/export" : "/api/reports/sales/export"}>Download CSV</a>
        </Button>
      </div>

      {report.isLoading ? <StackSkeleton rows={4} /> : null}

      {totals ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="GMV" value={money(totals.gmv_cents)} hint="Customer spend" />
          <Stat label="Commission" value={money(totals.commission_cents)} hint="Charged at payment" />
          <Stat label="Orders" value={String(totals.orders)} hint={`${totals.sub_orders} shop parcels`} />
          <Stat label="Average order" value={money(totals.aov_cents)} hint="GMV ÷ orders" />
        </div>
      ) : null}

      {data?.revenue?.length ? (
        <section className="panel p-4">
          <h2 className="mb-3 text-sm font-medium">Revenue over time</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.revenue}>
                <CartesianGrid stroke="var(--border)" />
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip
                  formatter={(value, name) => [money(Number(value)), name === "commission_cents" ? "Commission" : "GMV"]}
                />
                <Line type="monotone" dataKey="gmv_cents" stroke="var(--secondary)" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="commission_cents" stroke="var(--primary)" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      ) : null}

      {!seller && data?.sales_by_vendor?.length ? (
        <section className="space-y-3">
          <h2 className="serif text-2xl">By shop</h2>
          <div className="panel h-72 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.sales_by_vendor.slice(0, 8).map((row) => ({ ...row, name: shopLabel(row.vendor_id, row.vendor_name) }))}>
                <CartesianGrid stroke="var(--border)" />
                <XAxis dataKey="name" hide />
                <YAxis hide />
                <Tooltip formatter={(value) => money(Number(value))} />
                <Bar dataKey="gmv_cents" fill="var(--secondary)" radius={6} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul className="space-y-2">
            {data.sales_by_vendor.map((row) => (
              <li key={row.vendor_id} className="flex items-center justify-between gap-3 text-sm">
                <span>{shopLabel(row.vendor_id, row.vendor_name)}</span>
                <span>
                  {money(row.gmv_cents)} · take {money(row.commission_cents)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {data?.top_products?.length ? (
        <section className="space-y-3">
          <h2 className="serif text-2xl">Top products</h2>
          <ul className="space-y-2">
            {data.top_products.map((row) => (
              <li key={row.product_id} className="panel flex items-center justify-between gap-3 p-3 text-sm">
                <span>
                  {productLabel(row.product_id, row.title)}
                  <span className="block text-muted-foreground">{shopLabel(row.vendor_id, row.vendor_name)} · {row.units} sold</span>
                </span>
                <span className="font-medium">{money(row.revenue_cents)}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="panel p-4">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl tracking-tight">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{hint}</p>
    </div>
  );
}
