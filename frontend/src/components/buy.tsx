"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Field, FlowSteps } from "@/components/flow";
import { useSession } from "@/components/providers";
import { DealPrice } from "@/components/site";
import { CartSkeleton, CheckoutSkeleton, StackSkeleton } from "@/components/skeletons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { resendOtp, startRegister, verifyEmail } from "@/lib/auth-api";
import { money } from "@/lib/format";
import { addGuestLine, clearGuestCart, readGuestCart, setGuestQty, writeGuestCart } from "@/lib/guest-cart";
import { productLabel, saleFor, shopLabel } from "@/lib/labels";
import { useI18n } from "@/lib/i18n";

type Product = components["schemas"]["ProductDetail"];
type Cart = components["schemas"]["CartOut"];

const BUY_STEPS = [{ label: "Cart" }, { label: "Account" }, { label: "Pay" }, { label: "Track" }];

function Qty({ value, onMinus, onPlus }: { value: number; onMinus: () => void; onPlus: () => void }) {
  return (
    <div className="inline-flex items-center rounded-full ring-1 ring-border">
      <button type="button" className="px-3 py-1 text-sm" onClick={onMinus} aria-label="Decrease quantity">
        −
      </button>
      <span className="w-6 text-center text-sm">{value}</span>
      <button type="button" className="px-3 py-1 text-sm" onClick={onPlus} aria-label="Increase quantity">
        +
      </button>
    </div>
  );
}

async function mergeGuestCart() {
  const guest = readGuestCart();
  if (!guest.length) return;
  await unwrap(
    browserApi.POST("/api/cart/merge", {
      body: { items: guest.map((line) => ({ variant_id: line.variant_id, qty: line.qty })) },
    }),
  );
  clearGuestCart();
}

function Thumb({ src }: { src?: string | null }) {
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt="" className="h-20 w-20 shrink-0 rounded-xl object-cover" />;
  }
  return <div className="h-20 w-20 shrink-0 rounded-xl bg-muted" />;
}

export function AddToCart({ product }: { product: Product }) {
  const { me } = useSession();
  const { t } = useI18n();
  const router = useRouter();
  const [variantId, setVariantId] = useState(product.variants[0]?.id ?? "");
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const variant = product.variants.find((item) => item.id === variantId) ?? product.variants[0];
  const max = Math.min(10, variant?.available ?? 0);

  async function add(next?: "cart" | "checkout") {
    if (!variant) return;
    const count = Math.min(Math.max(1, qty), max || 1);
    if (me?.kind === "customer") {
      try {
        await unwrap(browserApi.POST("/api/cart/items", { body: { variant_id: variant.id, qty: count } }));
        window.dispatchEvent(new Event("bazaar-cart"));
        toast.success("Added to cart");
        setAdded(true);
        if (next === "checkout") router.push("/checkout");
        else if (next === "cart") router.push("/cart");
      } catch (error) {
        toast.error(error instanceof ApiError ? error.message : t.product.addFailed);
      }
      return;
    }
    if (me) {
      toast.error("Sign in as a customer to buy.");
      return;
    }
    addGuestLine({
      variant_id: variant.id,
      qty: count,
      title: productLabel(product.id, product.title),
      price_cents: product.price_cents,
      image_url: product.image_url,
      product_id: product.id,
      vendor_id: product.vendor_id,
    });
    toast.success("Saved. Create an account at checkout to pay.");
    setAdded(true);
    if (next) router.push(next === "checkout" ? "/checkout" : "/cart");
  }

  return (
    <div className="space-y-3">
      {product.variants.length > 1 ? (
        <Select value={variantId} onValueChange={setVariantId}>
          <SelectTrigger className="w-full max-w-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {product.variants.map((item) => (
              <SelectItem key={item.id} value={item.id}>
                {item.size} · {item.available} left
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <p className="text-sm text-muted-foreground">{variant ? `${variant.available} in stock` : "Sold out"}</p>
      )}
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Qty</span>
        <Qty value={qty} onMinus={() => setQty((n) => Math.max(1, n - 1))} onPlus={() => setQty((n) => Math.min(max || 1, n + 1))} />
      </div>
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => void add("cart")} disabled={!variant || variant.available < 1}>
          Add to cart
        </Button>
        <Button variant="outline" onClick={() => void add("checkout")} disabled={!variant || variant.available < 1}>
          Buy now
        </Button>
        {added ? (
          <Button asChild variant="ghost">
            <Link href="/cart">View cart</Link>
          </Button>
        ) : null}
      </div>
    </div>
  );
}

export function CartScreen() {
  const { me, loading } = useSession();
  const queryClient = useQueryClient();
  const cartQuery = useQuery({
    queryKey: ["cart"],
    enabled: me?.kind === "customer",
    queryFn: () => unwrap(browserApi.GET("/api/cart")),
  });
  const cart = cartQuery.data ?? null;
  const [guest, setGuest] = useState(readGuestCart());
  const [code, setCode] = useState("");

  function refresh() {
    return queryClient.invalidateQueries({ queryKey: ["cart"] });
  }

  if (loading) return <CartSkeleton />;

  if (me?.kind !== "customer") {
    const lines = guest;
    const subtotal = lines.reduce((sum, line) => sum + line.price_cents * line.qty, 0);
    const bestSale = lines.map((line) => saleFor(line.product_id, line.vendor_id, line.price_cents)).find(Boolean);
    return (
      <div className="wrap max-w-5xl space-y-8 py-8">
        <FlowSteps steps={BUY_STEPS} current={0} />
        <div className="space-y-2">
          <h1 className="serif text-5xl">Cart</h1>
          <p className="text-sm text-muted-foreground">Create an account at checkout, then pay with a demo card.</p>
        </div>
        {lines.length === 0 ? (
          <EmptyCart />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
            <div className="space-y-4">
              {bestSale ? <DealBanner percent={bestSale.percent} /> : null}
              {lines.map((line) => {
                const sale = saleFor(line.product_id, line.vendor_id, line.price_cents);
                const unit = sale?.now ?? line.price_cents;
                return (
                  <article key={line.variant_id} className="panel overflow-hidden">
                    {sale ? (
                      <div className="flex items-center justify-between bg-secondary/10 px-4 py-2 text-xs font-medium text-secondary">
                        <span>{sale.percent}% off on this item</span>
                        <span>
                          Was {money(sale.was)} · now {money(sale.now)}
                        </span>
                      </div>
                    ) : null}
                    <div className="flex gap-4 p-4">
                      <Thumb src={line.image_url} />
                      <div className="min-w-0 flex-1 space-y-2">
                        <p className="font-medium leading-snug">{line.title}</p>
                        <DealPrice cents={line.price_cents} deal={sale} size="sm" />
                        <Qty
                          value={line.qty}
                          onMinus={() => {
                            setGuestQty(line.variant_id, line.qty - 1);
                            setGuest(readGuestCart());
                          }}
                          onPlus={() => {
                            setGuestQty(line.variant_id, line.qty + 1);
                            setGuest(readGuestCart());
                          }}
                        />
                      </div>
                      <div className="flex flex-col items-end justify-between">
                        <p className="font-medium">{money(unit * line.qty)}</p>
                        <button
                          type="button"
                          className="text-xs text-muted-foreground hover:underline"
                          onClick={() => {
                            writeGuestCart(readGuestCart().filter((item) => item.variant_id !== line.variant_id));
                            setGuest(readGuestCart());
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
            <aside className="panel h-fit space-y-4 p-5">
              <h2 className="font-medium">Next</h2>
              <p className="flex justify-between text-sm">
                <span>Items</span>
                <span>{money(subtotal)}</span>
              </p>
              <Button asChild className="w-full">
                <Link href="/checkout">Account and pay</Link>
              </Button>
              <Button asChild variant="ghost" className="w-full">
                <Link href="/search">Keep shopping</Link>
              </Button>
            </aside>
          </div>
        )}
      </div>
    );
  }

  const empty = !cartQuery.isLoading && (!cart || !cart.groups.length);

  return (
    <div className="wrap max-w-5xl space-y-8 py-8">
      <FlowSteps steps={BUY_STEPS} current={0} />
      <div className="space-y-2">
        <h1 className="serif text-5xl">Cart</h1>
        <p className="text-sm text-muted-foreground">Check prices, apply a shop code, then pay.</p>
      </div>
      {cartQuery.isLoading && !cart ? <StackSkeleton rows={2} /> : null}
      {empty ? (
        <EmptyCart />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="space-y-4">
            {cart?.discount_cents ? <DealBanner percent={Math.round((cart.discount_cents / Math.max(1, cart.items_subtotal_cents)) * 100)} code={cart.coupon_code} /> : null}
            {cart?.groups.map((group) => {
              const groupOff = (group.vendor_discount_cents || 0) + (group.platform_discount_cents || 0);
              return (
                <section key={group.vendor_id} className="panel overflow-hidden">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/40 px-4 py-3">
                    <div>
                      <p className="text-sm font-medium">{shopLabel(group.vendor_id, group.vendor_name)}</p>
                      <p className="text-xs text-muted-foreground">Ships its own parcel</p>
                    </div>
                    {groupOff ? (
                      <span className="rounded-full bg-secondary/15 px-2.5 py-1 text-xs font-medium text-secondary">
                        −{money(groupOff)} shop discount
                      </span>
                    ) : null}
                  </div>
                  <div className="divide-y divide-border px-4">
                    {group.lines.map((line) => {
                      const off = (line.vendor_discount_cents || 0) + (line.platform_discount_cents || 0);
                      const unitNow = off ? Math.max(0, line.unit_price_cents - Math.round(off / line.qty)) : line.unit_price_cents;
                      const sale = off
                        ? { percent: Math.round((off / (line.unit_price_cents * line.qty)) * 100), was: line.unit_price_cents, now: unitNow }
                        : saleFor(line.product_id, group.vendor_id, line.unit_price_cents);
                      const lineNow = off ? line.line_total_cents - off : line.line_total_cents;
                      return (
                        <div key={line.id} className="flex gap-4 py-4">
                          <Thumb src={line.image_url} />
                          <div className="min-w-0 flex-1 space-y-2">
                            <div className="flex flex-wrap items-start gap-2">
                              <p className="font-medium leading-snug">{productLabel(line.product_id, line.title)}</p>
                              {sale ? (
                                <span className="rounded-full bg-secondary/15 px-2 py-0.5 text-[11px] font-medium text-secondary">
                                  {sale.percent}% off
                                </span>
                              ) : null}
                            </div>
                            <DealPrice cents={unitNow} deal={sale} size="sm" />
                            <Qty
                              value={line.qty}
                              onMinus={() =>
                                void unwrap(
                                  browserApi.PATCH("/api/cart/items/{line_id}", {
                                    params: { path: { line_id: line.id } },
                                    body: { qty: line.qty - 1 },
                                  }),
                                ).then(() => refresh())
                              }
                              onPlus={() =>
                                void unwrap(
                                  browserApi.PATCH("/api/cart/items/{line_id}", {
                                    params: { path: { line_id: line.id } },
                                    body: { qty: line.qty + 1 },
                                  }),
                                ).then(() => refresh())
                              }
                            />
                          </div>
                          <div className="flex flex-col items-end justify-between">
                            <div className="text-right">
                              <p className="font-medium">{money(lineNow)}</p>
                              {off ? <p className="text-xs text-muted-foreground line-through">{money(line.line_total_cents)}</p> : null}
                            </div>
                            <button
                              type="button"
                              className="text-xs text-muted-foreground hover:underline"
                              onClick={() =>
                                void unwrap(browserApi.DELETE("/api/cart/items/{line_id}", { params: { path: { line_id: line.id } } })).then(() => refresh())
                              }
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
          <CartSummary cart={cart} code={code} setCode={setCode} onApplied={() => void refresh()} />
        </div>
      )}
    </div>
  );
}

function EmptyCart() {
  return (
    <div className="panel space-y-3 p-8 text-center">
      <p className="serif text-3xl">Your cart is empty</p>
      <p className="text-sm text-muted-foreground">Browse listings, then come back to pay.</p>
      <Button asChild>
        <Link href="/search">Browse listings</Link>
      </Button>
    </div>
  );
}

function DealBanner({ percent, code }: { percent: number; code?: string | null }) {
  if (!percent) return null;
  return (
    <div className="rounded-2xl bg-secondary px-4 py-3 text-sm text-secondary-foreground">
      {code ? (
        <>
          Code <b>{code}</b> saves about {percent}% on this order.
        </>
      ) : (
        <>Sale prices are on. You save about {percent}% on marked items.</>
      )}
    </div>
  );
}

function CartSummary({
  cart,
  code,
  setCode,
  onApplied,
}: {
  cart: Cart | null;
  code: string;
  setCode: (value: string) => void;
  onApplied: () => void;
}) {
  return (
    <aside className="panel h-fit space-y-5 p-5">
      <div>
        <h2 className="font-medium">Order total</h2>
        <p className="text-xs text-muted-foreground">Shop discount codes apply here.</p>
      </div>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void unwrap(browserApi.POST("/api/cart/coupon", { body: { code } }))
            .then(() => {
              toast.success("Discount applied");
              onApplied();
            })
            .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : "That coupon did not apply"));
        }}
      >
        <Input value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} placeholder="Discount code" aria-label="Coupon" />
        <Button type="submit" variant="outline">
          Apply
        </Button>
      </form>
      {cart ? (
        <div className="space-y-2 text-sm">
          <p className="flex justify-between">
            <span>Items</span>
            <span>{money(cart.items_subtotal_cents)}</span>
          </p>
          <p className="flex justify-between">
            <span>Shipping</span>
            <span>{money(cart.shipping_cents)}</span>
          </p>
          {cart.discount_cents ? (
            <p className="flex justify-between text-secondary">
              <span>Discount{cart.coupon_code ? ` · ${cart.coupon_code}` : ""}</span>
              <span>−{money(cart.discount_cents)}</span>
            </p>
          ) : null}
          <p className="flex justify-between border-t border-border pt-3 text-lg text-foreground">
            <span>Total</span>
            <span>{money(cart.total_cents)}</span>
          </p>
          {cart.coupon_message ? <p className="text-xs text-muted-foreground">{cart.coupon_message}</p> : null}
        </div>
      ) : null}
      <Button asChild className="w-full" disabled={Boolean(cart && !cart.can_checkout)}>
        <Link href="/checkout">Review and pay</Link>
      </Button>
      <Button asChild variant="ghost" className="w-full">
        <Link href="/search">Keep shopping</Link>
      </Button>
    </aside>
  );
}

export function CheckoutScreen() {
  const { me, loading, refresh } = useSession();
  const { t } = useI18n();
  const router = useRouter();
  const cartQuery = useQuery({
    queryKey: ["cart"],
    enabled: me?.kind === "customer",
    queryFn: () => unwrap(browserApi.GET("/api/cart")),
  });
  const cart = cartQuery.data ?? null;
  const guest = me ? [] : readGuestCart();
  const [name, setName] = useState(me?.name || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("demo1234");
  const [otp, setOtp] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [accountStep, setAccountStep] = useState<"details" | "otp">("details");
  const [shipAddress, setShipAddress] = useState("St. 240, Daun Penh, Phnom Penh");
  const [card, setCard] = useState("4242 4242 4242 4242");
  const [busy, setBusy] = useState(false);

  if (loading) return <CheckoutSkeleton />;
  if (me && me.kind !== "customer") {
    return (
      <div className="wrap max-w-lg space-y-4 py-10">
        <h1 className="serif text-4xl">Customers only</h1>
        <p className="text-muted-foreground">Sign out, then enter as a customer to pay.</p>
        <Button asChild>
          <Link href="/login?next=/checkout">Customer sign in</Link>
        </Button>
      </div>
    );
  }

  const empty = me?.kind === "customer" ? !cartQuery.isLoading && (!cart || !cart.groups.length) : guest.length === 0;
  const guestTotal = guest.reduce((sum, line) => sum + line.price_cents * line.qty, 0);

  async function payAsCustomer(shipName: string) {
    const intent = await unwrap(browserApi.POST("/api/checkout", { body: { ship_name: shipName, ship_address: shipAddress } }));
    const order = await unwrap(
      browserApi.POST("/api/payments/{intent_id}/confirm", {
        params: { path: { intent_id: intent.id } },
        body: { card_number: card },
      }),
    );
    clearGuestCart();
    window.dispatchEvent(new Event("bazaar-cart"));
    toast.success("Payment successful", {
      description: `Order ${order.id} paid. E-receipt emailed to you.`,
      duration: 7000,
    });
    router.push(`/account/orders/${order.id}`);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      if (!me) {
        if (accountStep === "details") {
          const started = await startRegister({ name, email, password, city: "Phnom Penh" });
          setDevCode(started.dev_code || null);
          setAccountStep("otp");
          toast.success("Verification code sent to your email");
          return;
        }
        await verifyEmail({ email, code: otp.trim() });
        await refresh();
        await mergeGuestCart();
      }
      await payAsCustomer(name || me?.name || "Customer");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t.checkout.failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wrap max-w-5xl space-y-8 py-8">
      <FlowSteps steps={BUY_STEPS} current={me ? 2 : accountStep === "otp" ? 1 : 1} />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="serif text-5xl">{me ? "Pay" : accountStep === "otp" ? "Verify email" : "Account and pay"}</h1>
        <Button asChild variant="ghost" size="sm">
          <Link href="/cart">Back to cart</Link>
        </Button>
      </div>
      {me?.kind === "customer" && cartQuery.isLoading && !cart ? <StackSkeleton rows={1} /> : null}
      {empty ? (
        <div className="panel space-y-3 p-6">
          <p>Nothing to pay yet.</p>
          <Button asChild>
            <Link href="/search">Browse listings</Link>
          </Button>
        </div>
      ) : (
        <form className="grid gap-6 lg:grid-cols-[1fr_0.9fr]" onSubmit={(event) => void submit(event)}>
          <div className="space-y-4">
            {!me ? (
              <div className="panel space-y-4 p-6">
                <div>
                  <p className="text-xs uppercase tracking-wide text-secondary">
                    {accountStep === "details" ? "1 · Create account" : "1 · Verify email"}
                  </p>
                  <h2 className="mt-1 text-lg">{accountStep === "details" ? "Your credentials" : "Enter the code"}</h2>
                  <p className="text-sm text-muted-foreground">
                    {accountStep === "details" ? (
                      <>
                        We email a code before payment. Already a customer?{" "}
                        <Link href="/login?next=/checkout" className="underline">
                          Sign in
                        </Link>
                        .
                      </>
                    ) : (
                      <>Sent to {email}. Then you can pay with the demo card.</>
                    )}
                  </p>
                </div>
                {accountStep === "details" ? (
                  <>
                    <Field id="name" label="Full name">
                      <Input id="name" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} autoComplete="name" />
                    </Field>
                    <Field id="email" label="Email">
                      <Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
                    </Field>
                    <Field id="password" label="Password" hint="At least 8 characters.">
                      <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete="new-password" />
                    </Field>
                    <Button type="submit" disabled={busy} className="w-full">
                      {busy ? "Sending…" : "Send verification code"}
                    </Button>
                  </>
                ) : (
                  <>
                    {devCode ? (
                      <div className="rounded-2xl bg-secondary/10 px-4 py-3 text-sm text-secondary">
                        Demo inbox: code <span className="font-semibold tracking-widest">{devCode}</span>
                      </div>
                    ) : null}
                    <Field id="otp" label="6-digit code">
                      <Input
                        id="otp"
                        required
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        value={otp}
                        onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                        className="tracking-[0.35em]"
                        placeholder="000000"
                      />
                    </Field>
                    <button
                      type="button"
                      className="text-sm text-muted-foreground underline-offset-4 hover:underline"
                      onClick={() =>
                        void resendOtp(email)
                          .then((started) => {
                            setDevCode(started.dev_code || null);
                            toast.success("New code sent");
                          })
                          .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : "Could not resend"))
                      }
                    >
                      Resend code
                    </button>
                  </>
                )}
              </div>
            ) : null}
            {(me || accountStep === "otp") && (
              <div className="panel space-y-4 p-6">
                <div>
                  <p className="text-xs uppercase tracking-wide text-secondary">{me ? "Ship and pay" : "2 · Simulated payment"}</p>
                  <h2 className="mt-1 text-lg">Pay for the order</h2>
                  <p className="text-sm text-muted-foreground">Demo card only. 4242… is approved. You get an e-receipt by email after pay.</p>
                </div>
                <Field id="ship-name" label="Name on the parcel">
                  <Input id="ship-name" value={name} onChange={(event) => setName(event.target.value)} required />
                </Field>
                <Field id="ship-address" label="Delivery address">
                  <Input id="ship-address" value={shipAddress} onChange={(event) => setShipAddress(event.target.value)} required />
                </Field>
                <Field id="card" label="Card number">
                  <Input id="card" value={card} onChange={(event) => setCard(event.target.value)} required inputMode="numeric" />
                </Field>
                <Button type="submit" disabled={busy || (!me && otp.length < 6)} className="w-full">
                  {busy ? "Working…" : me ? "Pay now" : "Verify and pay"}
                </Button>
              </div>
            )}
          </div>
          <aside className="panel h-fit space-y-4 p-6">
            <h2 className="font-medium">You are buying</h2>
            {me?.kind === "customer"
              ? cart?.groups.map((group) => (
                  <div key={group.vendor_id} className="space-y-2 border-b border-border pb-3 last:border-0">
                    <p className="text-sm font-medium">{shopLabel(group.vendor_id, group.vendor_name)}</p>
                    {group.lines.map((line) => (
                      <div key={line.id} className="flex items-center gap-2 text-sm">
                        <Thumb src={line.image_url} />
                        <p className="min-w-0 flex-1 text-muted-foreground">
                          {productLabel(line.product_id, line.title)} · {line.qty}
                        </p>
                        <span>{money(line.line_total_cents)}</span>
                      </div>
                    ))}
                  </div>
                ))
              : guest.map((line) => (
                  <div key={line.variant_id} className="flex items-center gap-2 text-sm">
                    <Thumb src={line.image_url} />
                    <p className="min-w-0 flex-1 text-muted-foreground">
                      {line.title} · {line.qty}
                    </p>
                    <span>{money(line.price_cents * line.qty)}</span>
                  </div>
                ))}
            {me?.kind === "customer" && cart ? (
              <div className="space-y-1 text-sm">
                {cart.discount_cents ? (
                  <p className="flex justify-between text-secondary">
                    <span>Discount</span>
                    <span>−{money(cart.discount_cents)}</span>
                  </p>
                ) : null}
                <p className="flex justify-between text-lg">
                  <span>Total</span>
                  <span>{money(cart.total_cents)}</span>
                </p>
              </div>
            ) : (
              <p className="flex justify-between text-lg">
                <span>Total</span>
                <span>{money(guestTotal)}</span>
              </p>
            )}
          </aside>
        </form>
      )}
    </div>
  );
}
