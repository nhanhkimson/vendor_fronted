"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Field, FlowSteps } from "@/components/flow";
import { StackSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { money, titleCase, when } from "@/lib/format";
import { productLabel, shopLabel } from "@/lib/labels";

type SubOrder = components["schemas"]["SubOrderOut"];

const PIPELINE = [
  { id: "pending_acceptance", label: "Paid" },
  { id: "accepted", label: "Accepted" },
  { id: "packing", label: "Packing" },
  { id: "shipped", label: "Shipped" },
  { id: "delivered", label: "Delivered" },
];

function pipelineIndex(status: string) {
  if (status === "completed") return PIPELINE.length - 1;
  const index = PIPELINE.findIndex((step) => step.id === status);
  return index;
}

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

export function OrderDetail({ id }: { id: string }) {
  const queryClient = useQueryClient();
  const order = useQuery({
    queryKey: ["order", id],
    queryFn: () => unwrap(browserApi.GET("/api/account/orders/{order_id}", { params: { path: { order_id: id } } })),
  });
  if (!order.data) return order.isLoading ? <StackSkeleton rows={4} /> : <p>Order not found.</p>;
  const data = order.data;
  const open = !["completed", "cancelled", "refunded"].includes(data.status);

  return (
    <div className="space-y-6">
      <FlowSteps
        steps={[{ label: "Cart" }, { label: "Pay" }, { label: "Ship" }, { label: "Track" }]}
        current={open ? 3 : 3}
      />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary">Order</p>
          <h1 className="serif text-4xl">{data.id}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Placed {when(data.placed_at)} · {titleCase(data.status)}
          </p>
        </div>
        <p className="text-2xl font-medium">{money(data.total_cents)}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="panel p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Payment</p>
          <p className="mt-1 font-medium">Card {data.card_last4 ? `•••• ${data.card_last4}` : "paid"}</p>
          <p className="text-sm text-muted-foreground">
            {money(data.items_subtotal_cents)} items
            {data.shipping_cents ? ` · ${money(data.shipping_cents)} shipping` : ""}
            {data.discount_cents ? ` · −${money(data.discount_cents)}` : ""}
          </p>
        </div>
        <div className="panel p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Ship to</p>
          <p className="mt-1 font-medium">{data.ship_name}</p>
          <p className="text-sm text-muted-foreground">{data.ship_address}</p>
        </div>
        <div className="panel p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Parcels</p>
          <p className="mt-1 font-medium">
            {data.sub_orders.length} shop{data.sub_orders.length === 1 ? "" : "s"}
          </p>
          <p className="text-sm text-muted-foreground">Each shop ships on its own.</p>
        </div>
      </div>

      {data.sub_orders.map((sub) => (
        <Parcel
          key={sub.id}
          orderId={id}
          sub={sub}
          onChange={() => queryClient.invalidateQueries({ queryKey: ["order", id] })}
        />
      ))}
    </div>
  );
}

function Parcel({
  orderId,
  sub,
  onChange,
}: {
  orderId: string;
  sub: SubOrder;
  onChange: () => void;
}) {
  const index = pipelineIndex(sub.status);
  const current = index < 0 ? 0 : index;
  const stopped = ["cancelled", "refunded"].includes(sub.status);

  return (
    <section className="panel space-y-4 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href={`/shops/${sub.vendor_slug}`} className="text-sm text-secondary hover:underline">
            {shopLabel(sub.vendor_slug, sub.vendor_name)}
          </Link>
          <h2 className="text-xl font-medium">{titleCase(sub.status)}</h2>
        </div>
        <p className="font-medium">{money(sub.charged_cents)}</p>
      </div>

      {stopped ? (
        <p className="text-sm text-destructive">{titleCase(sub.status)}</p>
      ) : (
        <ol className="flex flex-wrap items-center gap-y-2 text-sm">
          {PIPELINE.map((step, stepIndex) => (
            <li key={step.id} className="flex items-center">
              {stepIndex > 0 ? <span className="mx-2 h-px w-5 bg-border sm:w-8" aria-hidden /> : null}
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs ${
                  stepIndex === current
                    ? "bg-primary text-primary-foreground"
                    : stepIndex < current
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {stepIndex + 1}
              </span>
              <span className={`ml-2 ${stepIndex === current ? "font-medium" : "text-muted-foreground"}`}>{step.label}</span>
            </li>
          ))}
        </ol>
      )}

      <div className="rounded-xl bg-muted/60 px-4 py-3 text-sm">
        {sub.tracking_number ? (
          <p>
            Tracking <b>{sub.carrier || "Carrier"}</b> · {sub.tracking_number}
          </p>
        ) : (
          <p className="text-muted-foreground">No tracking yet. The shop adds a number when it ships.</p>
        )}
        {sub.next_step ? <p className="mt-1 text-muted-foreground">{sub.next_step}</p> : null}
      </div>

      <ul className="space-y-2">
        {sub.lines.map((line) => (
          <li key={line.id} className="flex items-start justify-between gap-3 text-sm">
            <div>
              <Link href={`/products/${line.product_id}`} className="hover:underline">
                {productLabel(line.product_id, line.title)}
              </Link>
              <p className="text-muted-foreground">
                {line.color} · qty {line.qty}
              </p>
            </div>
            <span>{money(line.line_total_cents)}</span>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap gap-2">
        {sub.allowed_actions.includes("confirm_delivery") ? (
          <Button
            size="sm"
            onClick={() =>
              void run(
                () =>
                  unwrap(browserApi.POST("/api/account/sub-orders/{sub_id}/confirm-delivery", { params: { path: { sub_id: sub.id } } })).then(onChange),
                "Delivery confirmed",
              )
            }
          >
            Confirm delivery
          </Button>
        ) : null}
        {sub.allowed_actions.includes("dispute") ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              void run(
                () =>
                  unwrap(
                    browserApi.POST("/api/account/sub-orders/{sub_id}/dispute", {
                      params: { path: { sub_id: sub.id } },
                      body: { reason: "shipping_delay", note: "The parcel has not moved." },
                    }),
                  ).then(onChange),
                "Dispute opened",
              )
            }
          >
            Open a dispute
          </Button>
        ) : null}
      </div>
      {sub.lines.some((line) => line.can_review) ? <ReviewForm orderId={orderId} subId={sub.id} lines={sub.lines} onChange={onChange} /> : null}
    </section>
  );
}

function ReviewForm({
  orderId,
  subId,
  lines,
  onChange,
}: {
  orderId: string;
  subId: string;
  lines: { id: number; product_id: string; title: string; can_review: boolean }[];
  onChange: () => void;
}) {
  const reviewable = lines.filter((line) => line.can_review);
  const [productId, setProductId] = useState(reviewable[0]?.product_id || "");
  const [body, setBody] = useState("");
  if (!reviewable.length) return null;
  return (
    <form
      className="space-y-3 border-t border-border pt-4"
      onSubmit={(event) => {
        event.preventDefault();
        void run(
          () =>
            unwrap(
              browserApi.POST("/api/account/reviews", {
                body: { sub_order_id: subId, product_id: productId, rating: 5, body: body.trim() },
              }),
            ).then(() => {
              setBody("");
              onChange();
            }),
          "Review saved",
        );
      }}
    >
      <p className="text-sm font-medium">Leave a review</p>
      <select
        className="h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
        value={productId}
        onChange={(event) => setProductId(event.target.value)}
      >
        {reviewable.map((line) => (
          <option key={line.product_id} value={line.product_id}>
            {productLabel(line.product_id, line.title)}
          </option>
        ))}
      </select>
      <Field id={`review-${orderId}-${subId}`} label="What did you think?" hint="At least 10 characters.">
        <Textarea id={`review-${orderId}-${subId}`} value={body} onChange={(event) => setBody(event.target.value)} rows={3} required minLength={10} />
      </Field>
      <Button type="submit" size="sm">
        Post 5-star review
      </Button>
    </form>
  );
}

export function OrdersList() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="serif text-4xl">Orders</h1>
        <p className="mt-1 text-sm text-muted-foreground">Pay once. Then track each shop’s parcel here.</p>
      </div>
      <OrderRows />
    </div>
  );
}

function OrderRows() {
  const orders = useQuery({
    queryKey: ["my-orders"],
    queryFn: () => unwrap(browserApi.GET("/api/account/orders")),
  });
  if (orders.isLoading) return <StackSkeleton rows={3} />;
  if (!orders.data?.length) {
    return (
      <div className="panel space-y-3 p-6">
        <p>No orders yet.</p>
        <Button asChild>
          <Link href="/search">Browse listings</Link>
        </Button>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {orders.data.map((row) => (
        <Link key={row.id} href={`/account/orders/${row.id}`} className="panel flex flex-wrap items-center justify-between gap-3 p-4 transition hover:border-primary/40">
          <div>
            <p className="font-medium">{row.id}</p>
            <p className="text-sm text-muted-foreground">
              {when(row.placed_at)} · {row.sub_orders.length} parcel{row.sub_orders.length === 1 ? "" : "s"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={row.status === "completed" ? "secondary" : "outline"}>{titleCase(row.status)}</Badge>
            <span className="font-medium">{money(row.total_cents)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
