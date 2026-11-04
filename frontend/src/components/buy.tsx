"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { useSession } from "@/components/providers";
import { CartSkeleton, CheckoutSkeleton, StackSkeleton } from "@/components/skeletons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { money } from "@/lib/format";
import { addGuestLine, clearGuestCart, readGuestCart } from "@/lib/guest-cart";
import { useI18n } from "@/lib/i18n";

type Product = components["schemas"]["ProductDetail"];

export function AddToCart({ product }: { product: Product }) {
  const { me } = useSession();
  const { t } = useI18n();
  const [variantId, setVariantId] = useState(product.variants[0]?.id ?? "");
  const variant = product.variants.find((item) => item.id === variantId) ?? product.variants[0];

  async function add() {
    if (!variant) return;
    if (me?.kind === "customer") {
      try {
        await unwrap(browserApi.POST("/api/cart/items", { body: { variant_id: variant.id, qty: 1 } }));
        window.dispatchEvent(new Event("bazaar-cart"));
        toast.success(t.product.added);
      } catch (error) {
        toast.error(error instanceof ApiError ? error.message : t.product.addFailed);
      }
      return;
    }
    if (me) {
      toast.error(t.product.customerOnly);
      return;
    }
    addGuestLine({
      variant_id: variant.id,
      qty: 1,
      title: `${product.title} · ${variant.color}`,
      price_cents: product.price_cents,
      image_url: product.image_url,
    });
    toast.success(t.product.guestSaved);
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
                {item.size} / {item.color} · {item.available} {t.product.left}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <p className="text-sm text-muted-foreground">{variant ? `${variant.available} ${t.product.available}` : t.product.soldOut}</p>
      )}
      <Button onClick={() => void add()} disabled={!variant || variant.available < 1}>
        {t.product.addToCart}
      </Button>
    </div>
  );
}

export function CartScreen() {
  const { me, loading } = useSession();
  const { t } = useI18n();
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
    return (
      <div className="wrap space-y-4 py-8">
        <h1 className="serif text-5xl">{t.cart.title}</h1>
        {lines.length === 0 ? <p>{t.cart.empty}</p> : null}
        {lines.map((line) => (
          <div key={line.variant_id} className="panel flex items-center justify-between p-4">
            <div>
              <p>{line.title}</p>
              <p className="text-sm text-muted-foreground">
                {money(line.price_cents)} · {t.cart.qty} {line.qty}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const next = readGuestCart().filter((item) => item.variant_id !== line.variant_id);
                setGuest(next);
                localStorage.setItem("bazaar.guestCart", JSON.stringify(next));
              }}
            >
              {t.cart.remove}
            </Button>
          </div>
        ))}
        <Button asChild>
          <Link href="/login?next=/cart">{t.cart.signInToCheckout}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="wrap space-y-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="serif text-5xl">{t.cart.title}</h1>
        <Button variant="ghost" size="sm" onClick={() => void refresh()}>
          {t.cart.refresh}
        </Button>
      </div>
      {cartQuery.isLoading && !cart ? <StackSkeleton rows={2} /> : null}
      {cart?.groups.map((group) => (
        <section key={group.vendor_id} className="panel p-4">
          <h2>{group.vendor_name}</h2>
          {group.lines.map((line) => (
            <div key={line.id} className="mt-3 flex justify-between gap-3">
              <div>
                <p>{line.title}</p>
                <p className="text-sm text-muted-foreground">
                  {line.color} · {money(line.unit_price_cents)} · {line.qty}
                  {line.problem ? ` · ${line.problem}` : ""}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  void unwrap(browserApi.DELETE("/api/cart/items/{line_id}", { params: { path: { line_id: line.id } } })).then(() => refresh())
                }
              >
                {t.cart.remove}
              </Button>
            </div>
          ))}
        </section>
      ))}
      <form
        className="flex max-w-md gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void unwrap(browserApi.POST("/api/cart/coupon", { body: { code } }))
            .then(() => refresh())
            .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : t.cart.couponFailed));
        }}
      >
        <Input value={code} onChange={(event) => setCode(event.target.value)} placeholder="WELCOME10" aria-label={t.cart.coupon} />
        <Button type="submit" variant="outline">
          {t.cart.apply}
        </Button>
      </form>
      {cart ? (
        <p>
          {t.cart.total} {money(cart.total_cents)}
          {cart.coupon_message ? ` · ${cart.coupon_message}` : ""}
        </p>
      ) : cartQuery.isLoading ? null : (
        <p>{t.cart.empty}</p>
      )}
      <Button asChild>
        <Link href="/checkout">{t.cart.checkout}</Link>
      </Button>
    </div>
  );
}

export function CheckoutScreen() {
  const { me, loading } = useSession();
  const { t } = useI18n();
  const router = useRouter();
  const cartQuery = useQuery({
    queryKey: ["cart"],
    enabled: me?.kind === "customer",
    queryFn: () => unwrap(browserApi.GET("/api/cart")),
  });
  const cart = cartQuery.data ?? null;
  const [shipName, setShipName] = useState<string | null>(null);
  const name = shipName ?? me?.name ?? "";
  const [shipAddress, setShipAddress] = useState("St. 240, Daun Penh, Phnom Penh");
  const [card, setCard] = useState("4242 4242 4242 4242");
  const [busy, setBusy] = useState(false);

  if (loading) return <CheckoutSkeleton />;
  if (!me)
    return (
      <p className="wrap py-8">
        <Button asChild variant="link" className="px-0">
          <Link href="/login?next=/checkout">{t.nav.signIn}</Link>
        </Button>{" "}
        {t.checkout.signInFirst}
      </p>
    );
  if (me.kind !== "customer") return <p className="wrap py-8">{t.checkout.customersOnly}</p>;

  async function pay(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const intent = await unwrap(browserApi.POST("/api/checkout", { body: { ship_name: name, ship_address: shipAddress } }));
      const order = await unwrap(
        browserApi.POST("/api/payments/{intent_id}/confirm", {
          params: { path: { intent_id: intent.id } },
          body: { card_number: card },
        }),
      );
      clearGuestCart();
      toast.success(`Order ${order.id} ${t.checkout.placed}`);
      router.push(`/account/orders/${order.id}`);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t.checkout.failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="wrap max-w-xl space-y-4 py-8" onSubmit={(event) => void pay(event)}>
      <h1 className="serif text-5xl">{t.checkout.title}</h1>
      {cartQuery.isLoading && !cart ? <StackSkeleton rows={1} /> : null}
      <p className="text-sm text-muted-foreground">{cart ? `${t.cart.total} ${money(cart.total_cents)}` : cartQuery.isLoading ? null : t.checkout.empty}</p>
      <div className="space-y-2">
        <Label htmlFor="ship-name">{t.checkout.name}</Label>
        <Input id="ship-name" value={name} onChange={(event) => setShipName(event.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="ship-address">{t.checkout.address}</Label>
        <Input id="ship-address" value={shipAddress} onChange={(event) => setShipAddress(event.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="card">{t.checkout.card}</Label>
        <Input id="card" value={card} onChange={(event) => setCard(event.target.value)} required />
      </div>
      <p className="text-sm text-muted-foreground">{t.checkout.cardHint}</p>
      <Button type="submit" disabled={busy}>
        {busy ? t.checkout.paying : t.checkout.pay}
      </Button>
    </form>
  );
}
