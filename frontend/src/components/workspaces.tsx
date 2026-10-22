"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useState } from "react";
import { toast } from "sonner";

import { Area, DoThis } from "@/components/area";
import { useSession } from "@/components/providers";
import { Records } from "@/components/records";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import { money, rate, titleCase, when } from "@/lib/format";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

function Overview({ area }: { area: "account" | "seller" | "admin" }) {
  const { me } = useSession();
  const path = area === "account" ? "/api/account/summary" : area === "seller" ? "/api/seller/summary" : "/api/admin/summary";
  const summary = useQuery({ queryKey: ["summary", area], queryFn: () => unwrap(browserApi.GET(path)) });
  const hints = {
    account: "Shop two shops in one cart, pay with 4242 4242 4242 4242, then track each shipment.",
    seller: "Ship the open order, reply to a review, and request the eligible payout.",
    admin: "Revise a commission rate, co-sign a payout, and read the activity log.",
  };
  const keys = {
    account: ["orders", "open_orders", "wishlist", "unread", "open_disputes"],
    seller: ["orders", "open_orders", "low_stock", "waiting_messages", "available_cents", "eligible_payouts", "open_disputes", "unread"],
    admin: ["open_orders", "open_disputes", "vendors_to_review", "payouts_to_sign", "flagged_reviews", "unread"],
  };
  return (
    <div className="space-y-4">
      <h1 className="serif text-5xl">{area === "seller" ? me?.vendor?.name || "Seller Central" : area === "admin" ? "Admin Console" : "Your account"}</h1>
      <DoThis text={hints[area]} />
      <p className="text-sm text-[#6b6258]">{area === "account" ? "Customer" : area === "seller" ? "Vendor · own shop only" : me?.roles.map((role) => role.name).join(", ")}</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {summary.data
          ? keys[area]
              .filter((key) => key in summary.data)
              .map((key) => {
                const value = summary.data[key as keyof typeof summary.data];
                return (
                <div key={key} className="panel p-4">
                  <p className="text-xs uppercase tracking-wide text-[#6b6258]">{titleCase(key)}</p>
                  <p className="text-2xl">{typeof value === "number" && key.endsWith("cents") ? money(value) : String(value)}</p>
                </div>
                );
              })
          : null}
      </div>
    </div>
  );
}

function OrderDetail({ id }: { id: string }) {
  const queryClient = useQueryClient();
  const order = useQuery({
    queryKey: ["order", id],
    queryFn: () => unwrap(browserApi.GET("/api/account/orders/{order_id}", { params: { path: { order_id: id } } })),
  });
  if (!order.data) return <p>{order.isLoading ? "Loading…" : "Order not found."}</p>;
  const data = order.data;
  return (
    <div className="space-y-4">
      <h1 className="serif text-4xl">{data.id}</h1>
      <p>
        {titleCase(data.status)} · {money(data.total_cents)} · {when(data.placed_at)}
      </p>
      {data.sub_orders.map((sub) => (
        <section key={sub.id} className="panel space-y-2 p-4">
          <h2>
            {sub.vendor_name} · {titleCase(sub.status)}
          </h2>
          <p className="text-sm text-[#6b6258]">
            {sub.tracking_number ? `${sub.carrier || "Carrier"} ${sub.tracking_number}` : "No tracking yet"} · {money(sub.charged_cents)}
          </p>
          <ol className="space-y-1 text-sm">
            {sub.events.map((event, index) => (
              <li key={index}>
                {when(event.at)} · {titleCase(event.to_status)} {event.note ? `· ${event.note}` : ""}
              </li>
            ))}
          </ol>
          <div className="flex flex-wrap gap-2">
            {sub.allowed_actions.includes("confirm_delivery") ? (
              <button
                className="rounded-full bg-[#24362c] px-3 py-1 text-sm text-[#f6efe3]"
                onClick={() =>
                  void run(
                    () =>
                      unwrap(browserApi.POST("/api/account/sub-orders/{sub_id}/confirm-delivery", { params: { path: { sub_id: sub.id } } })).then(() =>
                        queryClient.invalidateQueries({ queryKey: ["order", id] }),
                      ),
                    "Delivery confirmed",
                  )
                }
              >
                Confirm delivery
              </button>
            ) : null}
            {sub.allowed_actions.includes("dispute") ? (
              <button
                className="rounded-full border border-[#e2d8c8] px-3 py-1 text-sm"
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/account/sub-orders/{sub_id}/dispute", {
                          params: { path: { sub_id: sub.id } },
                          body: { reason: "shipping_delay", note: "The parcel has not moved." },
                        }),
                      ),
                    "Dispute opened",
                  )
                }
              >
                Open a dispute
              </button>
            ) : null}
          </div>
        </section>
      ))}
    </div>
  );
}

export function AccountWorkspace({ slug }: { slug?: string[] }) {
  const section = slug?.[0] ?? "home";
  const id = slug?.[1];
  const { me } = useSession();
  let body: React.ReactNode = <Overview area="account" />;
  if (section === "orders" && id) body = <OrderDetail id={id} />;
  else if (section === "orders")
    body = (
      <Records
        title="Orders"
        queryKey={["my-orders"]}
        load={() => unwrap(browserApi.GET("/api/account/orders"))}
        columns={[
          { key: "id", label: "Order", render: (row) => <Link href={`/account/orders/${row.id}`}>{row.id}</Link> },
          { key: "status", label: "Status", render: (row) => titleCase(row.status) },
          { key: "total", label: "Total", render: (row) => money(row.total_cents) },
          { key: "placed", label: "Placed", render: (row) => when(row.placed_at) },
        ]}
      />
    );
  else if (section === "wishlist")
    body = (
      <Records
        title="Wishlist"
        queryKey={["wishlist"]}
        load={() => unwrap(browserApi.GET("/api/account/wishlist"))}
        columns={[
          { key: "product", label: "Piece", render: (row) => <Link href={`/products/${row.product_id}`}>{row.product.title}</Link> },
          { key: "price", label: "Price", render: (row) => money(row.product.price_cents) },
        ]}
      />
    );
  else if (section === "messages") body = <Messages mine />;
  else if (section === "notifications") body = <Notifications />;
  else if (section === "settings")
    body = (
      <div className="space-y-2">
        <h1 className="serif text-4xl">Settings</h1>
        <p>{me?.name}</p>
        <p className="text-[#6b6258]">{me?.email}</p>
        <p>{me?.city}</p>
        {me?.banned ? <p className="text-[#9f2d3a]">Restricted: {me.ban_reason}</p> : null}
      </div>
    );
  return <Area area="account">{body}</Area>;
}

function Messages({ mine }: { mine: boolean }) {
  const path = mine ? "/api/account/messages" : "/api/seller/messages";
  const messages = useQuery({ queryKey: ["messages", path], queryFn: () => unwrap(browserApi.GET(path)) });
  const [body, setBody] = useState("Thanks, I will take a look.");
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Messages</h1>
      {messages.data?.map((conversation) => (
        <article key={conversation.id} className="panel space-y-2 p-4">
          <h2>{conversation.subject}</h2>
          {conversation.messages.map((message) => (
            <p key={message.id} className="text-sm">
              <b>{message.sender_name}</b> · {message.body}
            </p>
          ))}
          <button
            className="text-sm text-[#b8572a]"
            onClick={() =>
              void run(async () => {
                if (mine) {
                  await unwrap(
                    browserApi.POST("/api/account/messages/{conversation_id}/reply", {
                      params: { path: { conversation_id: conversation.id } },
                      body: { body },
                    }),
                  );
                } else {
                  await unwrap(
                    browserApi.POST("/api/seller/messages/{conversation_id}/reply", {
                      params: { path: { conversation_id: conversation.id } },
                      body: { body },
                    }),
                  );
                }
              }, "Reply sent")
            }
          >
            Send “{body}”
          </button>
        </article>
      ))}
      <input className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={body} onChange={(event) => setBody(event.target.value)} />
    </div>
  );
}

function Notifications() {
  const queryClient = useQueryClient();
  const notes = useQuery({ queryKey: ["notes"], queryFn: () => unwrap(browserApi.GET("/api/notifications")) });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Notifications</h1>
      <button
        className="text-sm"
        onClick={() => void run(() => unwrap(browserApi.POST("/api/notifications/read-all")).then(() => queryClient.invalidateQueries({ queryKey: ["notes"] })), "Marked read")}
      >
        Mark all read
      </button>
      {notes.data?.items.map((note) => (
        <article key={note.id} className="panel p-4">
          <p className="font-medium">{note.title}</p>
          <p className="text-sm text-[#6b6258]">{note.body}</p>
          {note.link ? <Link href={note.link}>{note.link}</Link> : null}
        </article>
      ))}
    </div>
  );
}

function SellerOrders() {
  const queryClient = useQueryClient();
  const [tracking, setTracking] = useState("US-DEMO-1");
  const orders = useQuery({ queryKey: ["seller-orders"], queryFn: () => unwrap(browserApi.GET("/api/seller/orders")) });
  async function move(id: string, action: "accept" | "pack" | "deliver") {
    const path =
      action === "accept"
        ? "/api/seller/orders/{sub_id}/accept"
        : action === "pack"
          ? "/api/seller/orders/{sub_id}/pack"
          : "/api/seller/orders/{sub_id}/deliver";
    await run(() => unwrap(browserApi.POST(path, { params: { path: { sub_id: id } } })).then(() => queryClient.invalidateQueries({ queryKey: ["seller-orders"] })), "Updated");
  }
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Shop orders</h1>
      <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={tracking} onChange={(event) => setTracking(event.target.value)} />
      {orders.data?.map((sub) => (
        <article key={sub.id} className="panel space-y-2 p-4">
          <h2>
            {sub.id} · {titleCase(sub.status)} · {money(sub.charged_cents)}
          </h2>
          <p className="text-sm text-[#6b6258]">
            Commission {money(sub.commission_cents)} · net {money(sub.vendor_net_cents)}
            {sub.tracking_number ? ` · ${sub.tracking_number}` : ""}
          </p>
          <div className="flex flex-wrap gap-2">
            {sub.allowed_actions.includes("accept") ? <button onClick={() => void move(sub.id, "accept")}>Accept</button> : null}
            {sub.allowed_actions.includes("pack") ? <button onClick={() => void move(sub.id, "pack")}>Pack</button> : null}
            {sub.allowed_actions.includes("ship") ? (
              <button
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/seller/orders/{sub_id}/ship", {
                          params: { path: { sub_id: sub.id } },
                          body: { tracking_number: tracking, carrier: "USPS" },
                        }),
                      ).then(() => queryClient.invalidateQueries({ queryKey: ["seller-orders"] })),
                    "Shipped",
                  )
                }
              >
                Ship
              </button>
            ) : null}
            {sub.allowed_actions.includes("deliver") ? <button onClick={() => void move(sub.id, "deliver")}>Deliver</button> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function Reports({ seller }: { seller: boolean }) {
  const path = seller ? "/api/seller/reports/overview" : "/api/reports/overview";
  const report = useQuery({ queryKey: ["report", path], queryFn: () => unwrap(browserApi.GET(path)) });
  const data = report.data;
  return (
    <div className="space-y-4">
      <h1 className="serif text-4xl">{seller ? "My shop" : "Platform"} reports</h1>
      {data ? (
        <>
          <p>
            GMV {money(data.totals.gmv_cents)} · commission {money(data.totals.commission_cents)} · {data.totals.orders} orders
          </p>
          <div className="panel h-64 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.revenue}>
                <CartesianGrid stroke="#e2d8c8" />
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip formatter={(value) => money(Number(value))} />
                <Line type="monotone" dataKey="gmv_cents" stroke="#b8572a" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <ul className="text-sm">
            {data.sales_by_vendor.map((row) => (
              <li key={row.vendor_id}>
                {row.vendor_name}: {money(row.gmv_cents)}
              </li>
            ))}
          </ul>
          <a className="text-[#b8572a]" href={seller ? "/api/seller/reports/sales/export" : "/api/reports/sales/export"}>
            Download CSV
          </a>
        </>
      ) : (
        <p>Loading…</p>
      )}
    </div>
  );
}

export function SellerWorkspace({ slug }: { slug?: string[] }) {
  const section = slug?.[0] ?? "home";
  const queryClient = useQueryClient();
  let body: React.ReactNode = <Overview area="seller" />;
  if (section === "products")
    body = (
      <Records
        title="Products"
        hint="Only this shop's listings."
        queryKey={["seller-products"]}
        load={() => unwrap(browserApi.GET("/api/seller/products"))}
        columns={[
          { key: "title", label: "Title" },
          { key: "price", label: "Price", render: (row) => money(row.price_cents) },
          { key: "stock", label: "Available", render: (row) => String(row.available) },
        ]}
      />
    );
  else if (section === "inventory")
    body = (
      <Records
        title="Inventory"
        queryKey={["inventory"]}
        load={() => unwrap(browserApi.GET("/api/seller/inventory"))}
        columns={[
          { key: "title", label: "Piece" },
          { key: "sku", label: "SKU" },
          { key: "on_hand", label: "On hand", render: (row) => String(row.on_hand) },
          { key: "low", label: "Low", render: (row) => (row.low ? "Yes" : "") },
        ]}
        render={(row) => (
          <button
            onClick={() =>
              void run(
                () =>
                  unwrap(
                    browserApi.POST("/api/seller/inventory/{variant_id}/adjust", {
                      params: { path: { variant_id: row.variant_id } },
                      body: { delta: 1, reason: "Restocked one unit from Seller Central" },
                    }),
                  ).then(() => queryClient.invalidateQueries({ queryKey: ["inventory"] })),
                "Stock updated",
              )
            }
          >
            +1
          </button>
        )}
      />
    );
  else if (section === "orders") body = <SellerOrders />;
  else if (section === "promotions") body = <Coupons seller />;
  else if (section === "payouts") body = <SellerPayouts />;
  else if (section === "reports") body = <Reports seller />;
  else if (section === "storefront") body = <ShopSettings />;
  else if (section === "messages") body = <Messages mine={false} />;
  else if (section === "reviews") body = <SellerReviews />;
  return <Area area="seller">{body}</Area>;
}

function SellerPayouts() {
  const earnings = useQuery({ queryKey: ["earnings"], queryFn: () => unwrap(browserApi.GET("/api/seller/earnings")) });
  const data = earnings.data;
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Payouts</h1>
      {data ? (
        <>
          <p>
            Balance {money(data.balance_cents)} · available {money(data.available_cents)}
            {data.open_dispute ? " · frozen by an open dispute" : ""}
          </p>
          <button className="rounded-full bg-[#24362c] px-3 py-2 text-sm text-[#f6efe3]" onClick={() => void run(() => unwrap(browserApi.POST("/api/seller/payouts")), "Payout requested")}>
            Request matured earnings
          </button>
          {data.payouts.map((payout) => (
            <div key={payout.id} className="panel flex items-center justify-between p-3">
              <span>
                {payout.id} · {titleCase(payout.status)} · {money(payout.amount_cents)}
              </span>
              {payout.allowed_actions.includes("request") ? (
                <button onClick={() => void run(() => unwrap(browserApi.POST("/api/seller/payouts/{payout_id}/request", { params: { path: { payout_id: payout.id } } })), "Requested")}>
                  Request
                </button>
              ) : null}
            </div>
          ))}
        </>
      ) : (
        <p>Loading…</p>
      )}
    </div>
  );
}

function SellerReviews() {
  const reviews = useQuery({ queryKey: ["seller-reviews"], queryFn: () => unwrap(browserApi.GET("/api/seller/reviews")) });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Reviews</h1>
      {reviews.data?.map((review) => (
        <article key={review.id} className="panel p-4">
          <p>
            {review.product_title} · {review.rating} stars · {titleCase(review.status)}
          </p>
          <p>{review.body}</p>
          {review.vendor_response ? <p className="text-sm text-[#6b6258]">Reply: {review.vendor_response}</p> : null}
          {review.allowed_actions.includes("respond") ? (
            <button
              className="mt-2 text-sm text-[#b8572a]"
              onClick={() =>
                void run(
                  () =>
                    unwrap(
                      browserApi.POST("/api/seller/reviews/{review_id}/reply", {
                        params: { path: { review_id: review.id } },
                        body: { response: "Thank you. The stars stay as you left them." },
                      }),
                    ),
                  "Reply saved",
                )
              }
            >
              Reply
            </button>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function ShopSettings() {
  const shop = useQuery({ queryKey: ["shop"], queryFn: () => unwrap(browserApi.GET("/api/seller/shop")) });
  const [headline, setHeadline] = useState("");
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">{shop.data?.name || "Storefront"}</h1>
      <p className="text-[#6b6258]">{shop.data?.headline}</p>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void run(() => unwrap(browserApi.PATCH("/api/seller/shop", { body: { headline } })), "Storefront updated");
        }}
      >
        <input className="flex-1 rounded-xl border border-[#e2d8c8] px-3 py-2" placeholder="New headline" value={headline} onChange={(event) => setHeadline(event.target.value)} />
        <button className="rounded-full bg-[#24362c] px-3 text-[#f6efe3]">Save</button>
      </form>
    </div>
  );
}

function Coupons({ seller }: { seller: boolean }) {
  const path = seller ? "/api/seller/coupons" : "/api/coupons";
  const coupons = useQuery({ queryKey: ["coupons", path], queryFn: () => unwrap(browserApi.GET(path)) });
  const [code, setCode] = useState(seller ? "SHOP10" : "SPRING15");
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Coupons</h1>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const now = new Date();
          const end = new Date(now.getTime() + 60 * 24 * 3600 * 1000);
          void run(
            () =>
              unwrap(
                browserApi.POST(path, {
                  body: {
                    code,
                    funded_by: seller ? "vendor" : "platform",
                    discount_type: "percent",
                    percent_off: 10,
                    min_subtotal_cents: 2000,
                    starts_at: now.toISOString(),
                    ends_at: end.toISOString(),
                    per_customer_limit: 1,
                    is_flash: false,
                    note: seller ? "Funded by this shop" : "Platform funded",
                  },
                }),
              ),
            "Coupon created",
          );
        }}
      >
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={code} onChange={(event) => setCode(event.target.value)} />
        <button className="rounded-full bg-[#b8572a] px-3 text-white">Create 10%</button>
      </form>
      {coupons.data?.map((coupon) => (
        <p key={coupon.code}>
          {coupon.code} · {coupon.summary} · used {coupon.used_count}
        </p>
      ))}
    </div>
  );
}

export function AdminWorkspace({ slug }: { slug?: string[] }) {
  const section = slug?.[0] ?? "home";
  const queryClient = useQueryClient();
  let body: React.ReactNode = <Overview area="admin" />;
  if (section === "vendors") body = <Vendors />;
  else if (section === "products")
    body = (
      <Records
        title="Products"
        queryKey={["all-products"]}
        load={() => unwrap(browserApi.GET("/api/products"))}
        columns={[
          { key: "title", label: "Title" },
          { key: "shop", label: "Shop", render: (row) => row.vendor_name },
          { key: "price", label: "Price", render: (row) => money(row.price_cents) },
        ]}
      />
    );
  else if (section === "categories")
    body = (
      <Records
        title="Categories"
        queryKey={["categories"]}
        load={() => unwrap(browserApi.GET("/api/categories"))}
        columns={[
          { key: "name", label: "Name" },
          { key: "kh", label: "Khmer", render: (row) => row.name_kh || "—" },
          { key: "count", label: "Products", render: (row) => String(row.product_count) },
        ]}
      />
    );
  else if (section === "orders")
    body = (
      <Records
        title="Orders"
        queryKey={["staff-orders"]}
        load={() => unwrap(browserApi.GET("/api/orders"))}
        columns={[
          { key: "id", label: "Order" },
          { key: "status", label: "Status", render: (row) => titleCase(row.status) },
          { key: "total", label: "Total", render: (row) => money(row.total_cents) },
          { key: "shops", label: "Shops", render: (row) => String(row.sub_orders.length) },
        ]}
      />
    );
  else if (section === "customers") body = <Customers />;
  else if (section === "reviews") body = <ModerateReviews />;
  else if (section === "coupons") body = <Coupons seller={false} />;
  else if (section === "disputes")
    body = (
      <Records
        title="Disputes"
        queryKey={["disputes"]}
        load={() => unwrap(browserApi.GET("/api/disputes"))}
        columns={[
          { key: "id", label: "Dispute" },
          { key: "shop", label: "Shop", render: (row) => row.vendor_name },
          { key: "status", label: "Status", render: (row) => titleCase(row.status) },
          { key: "reason", label: "Reason" },
        ]}
        render={(row) =>
          row.status === "open" ? (
            <button
              onClick={() =>
                void run(
                  () =>
                    unwrap(
                      browserApi.POST("/api/disputes/{dispute_id}/resolve", {
                        params: { path: { dispute_id: row.id } },
                        body: { outcome: "reject", note: "Tracking shows the parcel is moving." },
                      }),
                    ).then(() => queryClient.invalidateQueries({ queryKey: ["disputes"] })),
                  "Dispute resolved",
                )
              }
            >
              Reject
            </button>
          ) : null
        }
      />
    );
  else if (section === "roles") body = <Roles />;
  else if (section === "audit") body = <AuditLog />;
  else if (section === "commissions") body = <Commissions />;
  else if (section === "payouts") body = <AdminPayouts />;
  else if (section === "reports") body = <Reports seller={false} />;
  return <Area area="admin">{body}</Area>;
}

function Vendors() {
  const queryClient = useQueryClient();
  const vendors = useQuery({ queryKey: ["vendors"], queryFn: () => unwrap(browserApi.GET("/api/vendors")) });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Vendors</h1>
      {vendors.data?.map((vendor) => (
        <article key={vendor.id} className="panel space-y-2 p-4">
          <h2>
            {vendor.name} · {titleCase(vendor.status)} · {vendor.tier_name}
          </h2>
          <p className="text-sm text-[#6b6258]">{vendor.headline}</p>
          {vendor.documents?.map((doc) => (
            <div key={doc.id} className="flex items-center gap-2 text-sm">
              <span>
                {doc.name}: {doc.status}
              </span>
              {doc.status !== "verified" ? (
                <button
                  onClick={() =>
                    void run(
                      () =>
                        unwrap(
                          browserApi.POST("/api/vendors/{vendor_id}/documents/{doc_id}/review", {
                            params: { path: { vendor_id: vendor.id, doc_id: doc.id } },
                            body: { decision: "verified" },
                          }),
                        ).then(() => queryClient.invalidateQueries({ queryKey: ["vendors"] })),
                      "Document approved",
                    )
                  }
                >
                  Approve
                </button>
              ) : null}
            </div>
          ))}
          {vendor.status === "under_review" ? (
            <button
              className="rounded-full bg-[#24362c] px-3 py-1 text-sm text-[#f6efe3]"
              onClick={() =>
                void run(
                  () => unwrap(browserApi.POST("/api/vendors/{vendor_id}/verify", { params: { path: { vendor_id: vendor.id } } })).then(() => queryClient.invalidateQueries({ queryKey: ["vendors"] })),
                  "Shop verified",
                )
              }
            >
              Verify shop
            </button>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function Customers() {
  const queryClient = useQueryClient();
  return (
    <Records
      title="Customers"
      hint="Sellers cannot open this list."
      queryKey={["customers"]}
      load={() => unwrap(browserApi.GET("/api/customers"))}
      columns={[
        { key: "name", label: "Name" },
        { key: "email", label: "Email" },
        { key: "city", label: "City" },
        { key: "spent", label: "Spent", render: (row) => money(row.spent_cents) },
        { key: "banned", label: "Banned", render: (row) => (row.banned ? row.ban_reason || "Yes" : "") },
      ]}
      render={(row) => (
        <button
          onClick={() =>
            void run(
              () =>
                unwrap(
                  browserApi.POST(row.banned ? "/api/customers/{user_id}/unban" : "/api/customers/{user_id}/ban", {
                    params: { path: { user_id: row.id } },
                    body: { reason: row.banned ? "Restriction lifted" : "Abuse of the marketplace" },
                  }),
                ).then(() => queryClient.invalidateQueries({ queryKey: ["customers"] })),
              row.banned ? "Unbanned" : "Banned",
            )
          }
        >
          {row.banned ? "Unban" : "Ban"}
        </button>
      )}
    />
  );
}

function ModerateReviews() {
  const queryClient = useQueryClient();
  return (
    <Records
      title="Reviews"
      queryKey={["staff-reviews"]}
      load={() => unwrap(browserApi.GET("/api/reviews"))}
      columns={[
        { key: "product", label: "Piece", render: (row) => row.product_title },
        { key: "rating", label: "Stars", render: (row) => String(row.rating ?? "—") },
        { key: "status", label: "Status", render: (row) => titleCase(row.status) },
      ]}
      render={(row) => (
        <span className="flex gap-2">
          {row.allowed_actions.includes("flag") ? (
            <button
              onClick={() =>
                void run(
                  () =>
                    unwrap(browserApi.POST("/api/reviews/{review_id}/flag", { params: { path: { review_id: row.id } }, body: { reason: "Needs a second look" } })).then(() =>
                      queryClient.invalidateQueries({ queryKey: ["staff-reviews"] }),
                    ),
                  "Flagged",
                )
              }
            >
              Flag
            </button>
          ) : null}
          {row.allowed_actions.includes("remove") ? (
            <button
              onClick={() =>
                void run(
                  () =>
                    unwrap(browserApi.POST("/api/reviews/{review_id}/remove", { params: { path: { review_id: row.id } }, body: { reason: "Removed from the store" } })).then(() =>
                      queryClient.invalidateQueries({ queryKey: ["staff-reviews"] }),
                    ),
                  "Removed",
                )
              }
            >
              Remove
            </button>
          ) : null}
        </span>
      )}
    />
  );
}

function Roles() {
  const matrix = useQuery({ queryKey: ["matrix"], queryFn: () => unwrap(browserApi.GET("/api/permissions")) });
  const [roleId, setRoleId] = useState("vendor");
  const [key, setKey] = useState("product:delete");
  return (
    <div className="space-y-4">
      <h1 className="serif text-4xl">Roles</h1>
      <p className="text-sm text-[#6b6258]">Super Admin inherits Admin. Revoking a permission takes effect on the next request.</p>
      <form
        className="flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void run(() => unwrap(browserApi.DELETE("/api/roles/{role_id}/permissions/{key}", { params: { path: { role_id: roleId, key } } })), "Permission revoked");
        }}
      >
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={roleId} onChange={(event) => setRoleId(event.target.value)} />
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={key} onChange={(event) => setKey(event.target.value)} />
        <button className="rounded-full border border-[#e2d8c8] px-3">Revoke</button>
      </form>
      {matrix.data?.roles.map((role) => (
        <p key={role.id}>
          <b>{role.name}</b> · {role.effective.length} permissions{role.parent_name ? ` · inherits ${role.parent_name}` : ""}
        </p>
      ))}
    </div>
  );
}

function AuditLog() {
  const [actor, setActor] = useState("");
  const [module, setModule] = useState("");
  const log = useQuery({
    queryKey: ["audit", actor, module],
    queryFn: () => unwrap(browserApi.GET("/api/audit-logs", { params: { query: { actor: actor || undefined, module: module || undefined, page_size: 30 } } })),
  });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Activity log</h1>
      <div className="flex gap-2">
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" placeholder="Actor id" value={actor} onChange={(event) => setActor(event.target.value)} />
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" placeholder="Module" value={module} onChange={(event) => setModule(event.target.value)} />
      </div>
      <a className="text-sm text-[#b8572a]" href="/api/audit-logs/export?format=csv">
        Export CSV
      </a>
      {log.data?.items.map((row) => (
        <article key={row.id} className="panel p-3 text-sm">
          <p>
            {when(row.at)} · {row.actor_name} ({row.actor_roles.join(", ")}) · {row.module}.{row.action} · {row.outcome}
          </p>
          <p className="text-[#6b6258]">
            {row.resource_type} {row.resource_id}
          </p>
          {row.before || row.after ? (
            <pre className="mt-2 overflow-x-auto text-xs">{JSON.stringify({ before: row.before, after: row.after }, null, 2)}</pre>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function Commissions() {
  const rules = useQuery({ queryKey: ["rules"], queryFn: () => unwrap(browserApi.GET("/api/commission-rules", { params: { query: { include_ended: true } } })) });
  const trial = useQuery({ queryKey: ["trial"], queryFn: () => unwrap(browserApi.GET("/api/ledger/trial-balance")) });
  const [ruleId, setRuleId] = useState("CR-GROW");
  const [bps, setBps] = useState(1100);
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Commission</h1>
      <p>Trial balance {trial.data?.balanced ? "is balanced" : "is loading"}.</p>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void run(
            () => unwrap(browserApi.POST("/api/commission-rules/{rule_id}/revise", { params: { path: { rule_id: ruleId } }, body: { rate_bps: bps, min_fee_cents: 30 } })),
            "New version opened. Past orders keep the old rate.",
          );
        }}
      >
        <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={ruleId} onChange={(event) => setRuleId(event.target.value)} />
        <input className="w-28 rounded-xl border border-[#e2d8c8] px-3 py-2" type="number" value={bps} onChange={(event) => setBps(Number(event.target.value))} />
        <button className="rounded-full bg-[#24362c] px-3 text-[#f6efe3]">Revise</button>
      </form>
      {rules.data?.map((rule) => (
        <p key={rule.id} className="text-sm">
          {rule.name} v{rule.version} · {rate(rule.rate_bps)} · {rule.open ? "open" : `ended ${when(rule.effective_to)}`}
        </p>
      ))}
    </div>
  );
}

function AdminPayouts() {
  const queryClient = useQueryClient();
  const [reference, setReference] = useState("TRF-1008");
  const payouts = useQuery({ queryKey: ["payouts"], queryFn: () => unwrap(browserApi.GET("/api/payouts")) });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Payouts</h1>
      <input className="rounded-xl border border-[#e2d8c8] px-3 py-2" value={reference} onChange={(event) => setReference(event.target.value)} />
      {payouts.data?.map((payout) => (
        <article key={payout.id} className="panel flex flex-wrap items-center justify-between gap-2 p-3">
          <span>
            {payout.id} · {payout.vendor_name} · {titleCase(payout.status)} · {money(payout.amount_cents)}
          </span>
          <span className="flex gap-2">
            {payout.allowed_actions.includes("approve") ? (
              <button
                onClick={() =>
                  void run(
                    () =>
                      unwrap(browserApi.POST("/api/payouts/{payout_id}/approve", { params: { path: { payout_id: payout.id } }, body: { note: "Signed in the console" } })).then(() =>
                        queryClient.invalidateQueries({ queryKey: ["payouts"] }),
                      ),
                    "Signed",
                  )
                }
              >
                Sign
              </button>
            ) : null}
            {payout.allowed_actions.includes("pay") ? (
              <button
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/payouts/{payout_id}/pay", {
                          params: { path: { payout_id: payout.id } },
                          body: { reference },
                        }),
                      ).then(() => queryClient.invalidateQueries({ queryKey: ["payouts"] })),
                    "Paid",
                  )
                }
              >
                Pay
              </button>
            ) : null}
          </span>
        </article>
      ))}
    </div>
  );
}
