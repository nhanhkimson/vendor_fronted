"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { OrderDetail, OrdersList } from "@/components/account/order";
import { GrowthDashboard } from "@/components/admin/growth";
import { ListingQueue } from "@/components/admin/listings";
import { ShopQueue } from "@/components/admin/shops";
import { Area, DoThis } from "@/components/area";
import { Field, FlowSteps } from "@/components/flow";
import { useSession } from "@/components/providers";
import { Records } from "@/components/records";
import { SellerProducts } from "@/components/seller/products";
import { SellerPromotions } from "@/components/seller/promotions";
import { StackSkeleton } from "@/components/skeletons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import { money, rate, titleCase, when } from "@/lib/format";
import { shopLabel } from "@/lib/labels";
import { isOwner, staffLabel } from "@/lib/roles";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

type MetricDef = {
  key: string;
  label: string;
  hint: string;
  href: string;
  group: "attention" | "money" | "activity";
  money?: boolean;
  warnWhenPositive?: boolean;
};

const METRICS: Record<"account" | "seller" | "admin", MetricDef[]> = {
  account: [
    { key: "open_orders", label: "Open orders", hint: "Still in progress", href: "/account/orders", group: "attention", warnWhenPositive: true },
    { key: "orders", label: "All orders", hint: "Placed on Bazaar", href: "/account/orders", group: "activity" },
  ],
  seller: [
    { key: "open_orders", label: "Needs shipping", hint: "Orders waiting on your shop", href: "/seller/orders", group: "attention", warnWhenPositive: true },
    { key: "pending_listings", label: "Listings to finish", hint: "Draft or waiting for staff", href: "/seller/products", group: "attention", warnWhenPositive: true },
    { key: "eligible_payouts", label: "Payouts ready", hint: "You can request these now", href: "/seller/payouts", group: "attention", warnWhenPositive: true },
    { key: "available_cents", label: "Available to withdraw", hint: "Balance ready after holdback", href: "/seller/payouts", group: "money", money: true },
    { key: "orders", label: "All shop orders", hint: "Every order for this shop", href: "/seller/orders", group: "activity" },
  ],
  admin: [
    { key: "vendors_to_review", label: "Shops to verify", hint: "Check documents, then go live", href: "/admin/vendors", group: "attention", warnWhenPositive: true },
    { key: "listings_to_review", label: "Products to publish", hint: "Approve before buyers see them", href: "/admin/listings", group: "attention", warnWhenPositive: true },
    { key: "open_disputes", label: "Open disputes", hint: "Across the marketplace", href: "/admin/disputes", group: "attention", warnWhenPositive: true },
    { key: "gmv_cents", label: "GMV", hint: "What buyers spent", href: "/admin/reports", group: "money", money: true },
    { key: "commission_cents", label: "Commission", hint: "Charged when a customer pays", href: "/admin/reports", group: "money", money: true },
    { key: "shops", label: "Shops", hint: "Registered shops", href: "/admin/vendors", group: "activity" },
    { key: "customers", label: "Customers", hint: "Buyer accounts", href: "/admin/customers", group: "activity" },
    { key: "products", label: "Live listings", hint: "Published on the website", href: "/admin/products", group: "activity" },
  ],
};

const GROUP_TITLE = {
  attention: "Needs attention",
  money: "Money",
  activity: "Pulse",
} as const;

function Overview({ area }: { area: "account" | "seller" | "admin" }) {
  const { me } = useSession();
  const path = area === "account" ? "/api/account/summary" : area === "seller" ? "/api/seller/summary" : "/api/admin/summary";
  const summary = useQuery({ queryKey: ["summary", area], queryFn: () => unwrap(browserApi.GET(path)) });
  const data = summary.data as Record<string, number | string> | undefined;

  const numberFor = (key: string) => {
    const value = data?.[key];
    return typeof value === "number" ? value : 0;
  };

  const hints = {
    account:
      numberFor("open_orders") > 0
        ? "You have parcels in progress. Open an order to see payment, shipping, and tracking."
        : "Pick listings, pay once at checkout, then track each shop’s parcel here.",
    seller:
      numberFor("open_orders") > 0
        ? "Ship open orders first. Then add products or run a discount from your menu."
        : "Start here. Add a product with photo, price, and description. Staff publish it. Then run discounts from Discounts.",
    admin:
      numberFor("vendors_to_review") > 0
        ? "Verify shop documents first. A shop is not real to buyers until you approve it."
        : numberFor("listings_to_review") > 0
          ? "Approve products shops want to publish."
          : isOwner(me)
            ? "Marketplace is clear. Check growth and permissions."
            : "Review shops and listings when they arrive.",
  };

  const actions =
    area === "seller"
      ? [
          ...(numberFor("open_orders") > 0
            ? [{ href: "/seller/orders", label: `Ship open orders (${numberFor("open_orders")})`, primary: true }]
            : [{ href: "/seller/products", label: "Add a product", primary: true }]),
          ...(numberFor("pending_listings") > 0
            ? [{ href: "/seller/products", label: `Finish listings (${numberFor("pending_listings")})`, primary: false }]
            : [{ href: "/seller/promotions", label: "Create a discount", primary: false }]),
          ...(numberFor("eligible_payouts") > 0
            ? [{ href: "/seller/payouts", label: `Request payout (${numberFor("eligible_payouts")})`, primary: false }]
            : [{ href: "/seller/payouts", label: "View payouts", primary: false }]),
        ]
      : area === "account"
        ? [
            { href: "/", label: "Continue shopping", primary: true },
            { href: "/account/orders", label: "Track orders", primary: false },
          ]
        : [
            ...(numberFor("vendors_to_review") > 0
              ? [{ href: "/admin/vendors", label: `Verify shops (${numberFor("vendors_to_review")})`, primary: true }]
              : []),
            ...(numberFor("listings_to_review") > 0
              ? [{ href: "/admin/listings", label: `Publish products (${numberFor("listings_to_review")})`, primary: numberFor("vendors_to_review") === 0 }]
              : []),
            { href: "/admin/reports", label: "Open growth", primary: numberFor("vendors_to_review") === 0 && numberFor("listings_to_review") === 0 },
            ...(isOwner(me) ? [{ href: "/admin/roles", label: "Permissions", primary: false }] : []),
          ];

  const metrics = METRICS[area].filter((metric) => !data || metric.key in data);
  const groups = (["attention", "money", "activity"] as const).filter((group) => metrics.some((metric) => metric.group === group));
  const subtitle =
    area === "account"
      ? "Customer · your purchases only"
      : area === "seller"
        ? "Vendor · own shop only"
        : [staffLabel(me), me?.roles.map((role) => role.name).join(", ")].filter(Boolean).join(" · ");

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="serif text-5xl leading-none">
          {area === "seller"
            ? (me?.vendor ? shopLabel(me.vendor.id, me.vendor.name) : "Seller Central")
            : area === "admin"
              ? staffLabel(me)
              : "Your orders"}
        </h1>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>

      {area === "seller" ? (
        <div className="panel space-y-5 p-6">
          <div>
            <p className="text-[11px] uppercase tracking-[0.16em] text-secondary">How your shop works</p>
            <h2 className="mt-1 serif text-3xl leading-none">Overview first, then products</h2>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Read this once. Then open Products to upload a photo, write a description, and set a price. After staff publish it, manage discounts from Discounts — not from the catalogue list.
            </p>
          </div>
          <ol className="grid gap-3 sm:grid-cols-3">
            {[
              { n: "1", title: "Add product", body: "Photo, description, price. Send for review." },
              { n: "2", title: "Staff publish", body: "Buyers only see approved listings." },
              { n: "3", title: "Sell and discount", body: "Ship orders. Run shop codes anytime." },
            ].map((step) => (
              <li key={step.n} className="rounded-2xl bg-muted/60 p-4">
                <p className="text-xs uppercase tracking-wide text-secondary">Step {step.n}</p>
                <p className="mt-1 font-medium">{step.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
      {area === "account" ? (
        <FlowSteps
          steps={[{ label: "Cart" }, { label: "Pay" }, { label: "Ship" }, { label: "Track" }]}
          current={numberFor("open_orders") > 0 ? 3 : 0}
        />
      ) : null}

      <DoThis text={hints[area]} actions={actions} />

      {summary.isLoading ? (
        <div className="grid gap-3 sm:grid-cols-3">
          {METRICS[area].map((metric) => (
            <Skeleton key={metric.key} className="h-28" />
          ))}
        </div>
      ) : (
        groups.map((group) => (
          <section key={group} className="space-y-3">
            <h2 className="text-xs uppercase tracking-[0.16em] text-secondary">{GROUP_TITLE[group]}</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {metrics
                .filter((metric) => metric.group === group)
                .map((metric) => {
                  const value = numberFor(metric.key);
                  const warn = Boolean(metric.warnWhenPositive && value > 0);
                  return (
                    <Link
                      key={metric.key}
                      href={metric.href}
                      className={`panel dash-metric ${warn ? "border-secondary/55" : ""}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-medium text-foreground">{metric.label}</p>
                        {warn ? (
                          <span className="rounded-md bg-secondary/15 px-2.5 py-1 text-xs font-medium text-secondary">Needs you</span>
                        ) : null}
                      </div>
                      <p className={`mt-3 text-foreground ${metric.money ? "price price-lg" : "text-3xl tracking-tight"}`}>
                        {metric.money ? money(value) : value}
                      </p>
                      <p className="mt-2 text-sm text-muted-foreground">{metric.hint}</p>
                    </Link>
                  );
                })}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

export function AccountWorkspace({ slug }: { slug?: string[] }) {
  const section = slug?.[0] ?? "home";
  const id = slug?.[1];
  const { me } = useSession();
  let body: React.ReactNode = <Overview area="account" />;
  if (section === "orders" && id) body = <OrderDetail id={id} />;
  else if (section === "orders") body = <OrdersList />;
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
        <p className="text-muted-foreground">{me?.email}</p>
        <p>{me?.city}</p>
        {me?.banned ? <p className="text-destructive">Restricted: {me.ban_reason}</p> : null}
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
      {messages.isLoading ? <StackSkeleton /> : null}
      {messages.data?.map((conversation) => (
        <article key={conversation.id} className="panel space-y-2 p-4">
          <h2>{conversation.subject}</h2>
          {conversation.messages.map((message) => (
            <p key={message.id} className="text-sm">
              <b>{message.sender_name}</b> · {message.body}
            </p>
          ))}
          <button
            className="text-sm text-secondary"
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
      <input className="w-full rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={body} onChange={(event) => setBody(event.target.value)} />
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
      {notes.isLoading ? <StackSkeleton /> : null}
      {notes.data?.items.map((note) => (
        <article key={note.id} className="panel p-4">
          <p className="font-medium">{note.title}</p>
          <p className="text-sm text-muted-foreground">{note.body}</p>
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
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="serif text-4xl">Shop orders</h1>
          <p className="mt-1 text-sm text-muted-foreground">Accept, pack, ship, then mark delivered. One clear action at a time.</p>
        </div>
        <Field id="tracking" label="Tracking number for Ship">
          <Input id="tracking" value={tracking} onChange={(event) => setTracking(event.target.value)} className="min-w-[220px]" />
        </Field>
      </div>
      {orders.isLoading ? <StackSkeleton rows={4} /> : null}
      {!orders.isLoading && !orders.data?.length ? (
        <div className="panel p-10 text-center text-sm text-muted-foreground">No shop orders yet.</div>
      ) : null}
      <div className="space-y-3">
        {orders.data?.map((sub) => (
          <article key={sub.id} className="panel space-y-4 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{sub.id}</p>
                <h2 className="serif text-2xl leading-none">{titleCase(sub.status)}</h2>
                <p className="text-sm text-muted-foreground">
                  Commission {money(sub.commission_cents)} · net {money(sub.vendor_net_cents)}
                  {sub.tracking_number ? ` · ${sub.tracking_number}` : ""}
                </p>
              </div>
              <p className="price price-lg">{money(sub.charged_cents)}</p>
            </div>
            <div className="dash-actions border-t border-border pt-4">
              {sub.allowed_actions.includes("accept") ? (
                <Button onClick={() => void move(sub.id, "accept")}>Accept</Button>
              ) : null}
              {sub.allowed_actions.includes("pack") ? (
                <Button onClick={() => void move(sub.id, "pack")}>Pack</Button>
              ) : null}
              {sub.allowed_actions.includes("ship") ? (
                <Button
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
                </Button>
              ) : null}
              {sub.allowed_actions.includes("deliver") ? (
                <Button variant="outline" onClick={() => void move(sub.id, "deliver")}>
                  Deliver
                </Button>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function SellerWorkspace({ slug }: { slug?: string[] }) {
  const section = slug?.[0] ?? "home";
  const queryClient = useQueryClient();
  let body: React.ReactNode = <Overview area="seller" />;
  if (section === "products") body = <SellerProducts />;
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
  else if (section === "promotions") body = <SellerPromotions />;
  else if (section === "payouts") body = <SellerPayouts />;
  else if (section === "reports") body = <GrowthDashboard seller />;
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
      {earnings.isLoading ? <StackSkeleton /> : null}
      {data ? (
        <>
          <p>
            Balance {money(data.balance_cents)} · available {money(data.available_cents)}
            {data.open_dispute ? " · frozen by an open dispute" : ""}
          </p>
          <button className="rounded-full bg-primary px-3 py-2 text-sm text-primary-foreground" onClick={() => void run(() => unwrap(browserApi.POST("/api/seller/payouts")), "Payout requested")}>
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
      ) : null}
    </div>
  );
}

function SellerReviews() {
  const reviews = useQuery({ queryKey: ["seller-reviews"], queryFn: () => unwrap(browserApi.GET("/api/seller/reviews")) });
  return (
    <div className="space-y-3">
      <h1 className="serif text-4xl">Reviews</h1>
      {reviews.isLoading ? <StackSkeleton /> : null}
      {reviews.data?.map((review) => (
        <article key={review.id} className="panel p-4">
          <p>
            {review.product_title} · {review.rating} stars · {titleCase(review.status)}
          </p>
          <p>{review.body}</p>
          {review.vendor_response ? <p className="text-sm text-muted-foreground">Reply: {review.vendor_response}</p> : null}
          {review.allowed_actions.includes("respond") ? (
            <button
              className="mt-2 text-sm text-secondary"
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
  const queryClient = useQueryClient();
  const shop = useQuery({ queryKey: ["shop"], queryFn: () => unwrap(browserApi.GET("/api/seller/shop")) });
  const [headline, setHeadline] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const data = shop.data;

  async function refreshShop() {
    await queryClient.invalidateQueries({ queryKey: ["shop"] });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="serif text-4xl">{shop.isLoading ? "Storefront" : data?.name || "Storefront"}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {data ? `${titleCase(data.status)} · ${data.city}` : "Manage how buyers see this shop."}
        </p>
      </div>
      {shop.isLoading ? <StackSkeleton rows={2} /> : null}
      <div className="panel max-w-xl space-y-4 p-6">
        <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Shop photo</p>
        {data?.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={data.image_url} alt="" className="h-44 w-full rounded-2xl object-cover" />
        ) : (
          <div className="flex h-44 items-center justify-center rounded-2xl bg-muted text-sm text-muted-foreground">No photo yet</div>
        )}
        <Field id="shop-photo" label="Replace photo" hint="JPEG, PNG or WebP. Up to 5 MB.">
          <Input
            id="shop-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => setPhoto(event.target.files?.[0] || null)}
          />
        </Field>
        <Button
          type="button"
          disabled={!photo}
          onClick={() => {
            if (!photo) return;
            const body = new FormData();
            body.set("file", photo);
            void run(async () => {
              const response = await fetch("/api/seller/shop/image", {
                method: "POST",
                body,
                credentials: "include",
                headers: { "X-Bazaar-Client": "web" },
              });
              const payload = await response.json().catch(() => null);
              if (!response.ok) {
                throw new ApiError(response.status, payload?.detail || "Upload failed");
              }
              setPhoto(null);
              await refreshShop();
            }, "Shop photo updated");
          }}
        >
          Upload photo
        </Button>
      </div>
      <form
        className="panel max-w-xl space-y-4 p-6"
        onSubmit={(event) => {
          event.preventDefault();
          void run(
            () => unwrap(browserApi.PATCH("/api/seller/shop", { body: { headline } })).then(() => refreshShop()),
            "Storefront updated",
          );
        }}
      >
        <Field id="headline" label="Headline" hint="This line appears on your public shop page.">
          <Input id="headline" placeholder={data?.headline || "New headline"} value={headline} onChange={(event) => setHeadline(event.target.value)} />
        </Field>
        <Button type="submit" size="lg">
          Save headline
        </Button>
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
        <input className="rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={code} onChange={(event) => setCode(event.target.value)} />
        <button className="rounded-full bg-secondary px-3 text-secondary-foreground">Create 10%</button>
      </form>
      {coupons.isLoading ? <StackSkeleton /> : null}
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
  if (section === "vendors") body = <ShopQueue />;
  else if (section === "listings") body = <ListingQueue />;
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
          { key: "listing_status", label: "Listing", render: (row) => titleCase(row.listing_status) },
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
            <span className="flex justify-end gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/disputes/{dispute_id}/resolve", {
                          params: { path: { dispute_id: row.id } },
                          body: { outcome: "reject", note: "Tracking shows the parcel is moving." },
                        }),
                      ).then(() => queryClient.invalidateQueries({ queryKey: ["disputes"] })),
                    "Kept with the shop",
                  )
                }
              >
                Keep
              </Button>
              <Button
                size="sm"
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/disputes/{dispute_id}/resolve", {
                          params: { path: { dispute_id: row.id } },
                          body: { outcome: "refund", note: "Refunded after review." },
                        }),
                      ).then(() => queryClient.invalidateQueries({ queryKey: ["disputes"] })),
                    "Refunded the buyer",
                  )
                }
              >
                Refund
              </Button>
            </span>
          ) : null
        }
      />
    );
  else if (section === "roles") body = <Roles />;
  else if (section === "audit") body = <AuditLog />;
  else if (section === "commissions") body = <Commissions />;
  else if (section === "payouts") body = <AdminPayouts />;
  else if (section === "reports") body = <GrowthDashboard seller={false} />;
  return <Area area="admin">{body}</Area>;
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
  const queryClient = useQueryClient();
  const matrix = useQuery({ queryKey: ["matrix"], queryFn: () => unwrap(browserApi.GET("/api/permissions")) });
  const [roleId, setRoleId] = useState("support");
  const [key, setKey] = useState("commission:manage_rule");
  const roles = matrix.data?.roles || [];

  return (
    <div className="space-y-6">
      <div className="max-w-2xl space-y-2">
        <h1 className="serif text-4xl">Permissions</h1>
        <p className="text-sm text-muted-foreground">
          Owner inherits Staff. Support cannot change rates or roles. Revoking a key takes effect on the next request.
        </p>
      </div>

      <form
        className="panel grid gap-4 p-5 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
        onSubmit={(event) => {
          event.preventDefault();
          void run(
            () =>
              unwrap(browserApi.DELETE("/api/roles/{role_id}/permissions/{key}", { params: { path: { role_id: roleId, key } } })).then(() =>
                queryClient.invalidateQueries({ queryKey: ["matrix"] }),
              ),
            "Permission revoked",
          );
        }}
      >
        <Field id="role-id" label="Role id" hint="Example: support, admin, vendor">
          <Input id="role-id" value={roleId} onChange={(event) => setRoleId(event.target.value)} list="role-ids" />
          <datalist id="role-ids">
            {roles.map((role) => (
              <option key={role.id} value={role.id} />
            ))}
          </datalist>
        </Field>
        <Field id="perm-key" label="Permission key" hint="Example: commission:manage_rule">
          <Input id="perm-key" value={key} onChange={(event) => setKey(event.target.value)} />
        </Field>
        <Button type="submit" variant="destructive" size="lg" className="w-full sm:w-auto">
          Revoke key
        </Button>
      </form>

      {matrix.isLoading ? <StackSkeleton rows={4} /> : null}

      <div className="grid gap-3 lg:grid-cols-2">
        {roles.map((role) => {
          const selected = role.id === roleId;
          return (
            <article
              key={role.id}
              className={`panel space-y-4 p-5 transition ${selected ? "border-primary ring-1 ring-primary/30" : ""}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 space-y-1">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{role.id}</p>
                  <h2 className="serif text-3xl leading-none">{role.name}</h2>
                  <p className="text-sm text-muted-foreground">
                    {role.parent_name ? `Inherits ${role.parent_name} · ` : ""}
                    {role.effective.length} keys
                  </p>
                </div>
                <Button
                  type="button"
                  variant={selected ? "default" : "outline"}
                  onClick={() => setRoleId(role.id)}
                >
                  {selected ? "Selected" : "Manage"}
                </Button>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{role.description}</p>
              <div className="flex flex-wrap gap-2 border-t border-border pt-4">
                {role.effective.slice(0, 8).map((perm) => (
                  <button
                    key={perm.key}
                    type="button"
                    className="rounded-md bg-muted px-2.5 py-1.5 text-left text-xs text-foreground transition hover:bg-primary hover:text-primary-foreground"
                    onClick={() => {
                      setRoleId(role.id);
                      setKey(perm.key);
                    }}
                    title="Load into revoke form"
                  >
                    {perm.key}
                  </button>
                ))}
                {role.effective.length > 8 ? (
                  <span className="rounded-md px-2.5 py-1.5 text-xs text-muted-foreground">+{role.effective.length - 8} more</span>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
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
        <input className="rounded-xl border border-border bg-background px-3 py-2 text-foreground" placeholder="Actor id" value={actor} onChange={(event) => setActor(event.target.value)} />
        <input className="rounded-xl border border-border bg-background px-3 py-2 text-foreground" placeholder="Module" value={module} onChange={(event) => setModule(event.target.value)} />
      </div>
      <a className="text-sm text-secondary" href="/api/audit-logs/export?format=csv">
        Export CSV
      </a>
      {log.isLoading ? <StackSkeleton rows={5} /> : null}
      {log.data?.items.map((row) => (
        <article key={row.id} className="panel p-3 text-sm">
          <p>
            {when(row.at)} · {row.actor_name} ({row.actor_roles.join(", ")}) · {row.module}.{row.action} · {row.outcome}
          </p>
          <p className="text-muted-foreground">
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
      <p>Trial balance {trial.isLoading ? "is loading…" : trial.data?.balanced ? "is balanced" : "needs attention"}.</p>
      {rules.isLoading ? <StackSkeleton /> : null}
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
        <input className="rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={ruleId} onChange={(event) => setRuleId(event.target.value)} />
        <input className="w-28 rounded-xl border border-border bg-background px-3 py-2 text-foreground" type="number" value={bps} onChange={(event) => setBps(Number(event.target.value))} />
        <button className="rounded-full bg-primary px-3 text-primary-foreground">Revise</button>
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
      <input className="rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={reference} onChange={(event) => setReference(event.target.value)} />
      {payouts.isLoading ? <StackSkeleton rows={4} /> : null}
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
