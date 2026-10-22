"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { useSession } from "@/components/providers";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { money } from "@/lib/format";
import { addGuestLine, clearGuestCart, readGuestCart } from "@/lib/guest-cart";

type Product = components["schemas"]["ProductDetail"];

export function AddToCart({ product }: { product: Product }) {
  const { me } = useSession();
  const [variantId, setVariantId] = useState(product.variants[0]?.id ?? "");
  const variant = product.variants.find((item) => item.id === variantId) ?? product.variants[0];

  async function add() {
    if (!variant) return;
    if (me?.kind === "customer") {
      try {
        await unwrap(browserApi.POST("/api/cart/items", { body: { variant_id: variant.id, qty: 1 } }));
        window.dispatchEvent(new Event("bazaar-cart"));
        toast.success("Added to your cart");
      } catch (error) {
        toast.error(error instanceof ApiError ? error.message : "Could not add that item");
      }
      return;
    }
    if (me) {
      toast.error("Sign in as a customer to shop");
      return;
    }
    addGuestLine({
      variant_id: variant.id,
      qty: 1,
      title: `${product.title} · ${variant.color}`,
      price_cents: product.price_cents,
      image_url: product.image_url,
    });
    toast.success("Saved in your guest cart");
  }

  return (
    <div className="space-y-3">
      {product.variants.length > 1 ? (
        <select className="rounded-full border border-[#e2d8c8] bg-white px-3 py-2" value={variantId} onChange={(event) => setVariantId(event.target.value)}>
          {product.variants.map((item) => (
            <option key={item.id} value={item.id}>
              {item.size} / {item.color} · {item.available} left
            </option>
          ))}
        </select>
      ) : (
        <p className="text-sm text-[#6b6258]">{variant ? `${variant.available} available` : "Sold out"}</p>
      )}
      <button className="rounded-full bg-[#b8572a] px-4 py-2 text-white" onClick={() => void add()} disabled={!variant || variant.available < 1}>
        Add to cart
      </button>
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

  if (loading) return <p className="wrap py-8">Loading…</p>;

  if (me?.kind !== "customer") {
    const lines = guest;
    return (
      <div className="wrap space-y-4 py-8">
        <h1 className="serif text-5xl">Cart</h1>
        {lines.length === 0 ? <p>Your cart is empty.</p> : null}
        {lines.map((line) => (
          <div key={line.variant_id} className="panel flex items-center justify-between p-4">
            <div>
              <p>{line.title}</p>
              <p className="text-sm text-[#6b6258]">{money(line.price_cents)} · qty {line.qty}</p>
            </div>
            <button
              onClick={() => {
                const next = readGuestCart().filter((item) => item.variant_id !== line.variant_id);
                setGuest(next);
                localStorage.setItem("bazaar.guestCart", JSON.stringify(next));
              }}
            >
              Remove
            </button>
          </div>
        ))}
        <Link href="/login?next=/cart" className="inline-block rounded-full bg-[#24362c] px-4 py-2 text-[#f6efe3]">
          Sign in to check out
        </Link>
      </div>
    );
  }

  return (
    <div className="wrap space-y-4 py-8">
      <h1 className="serif text-5xl">Cart</h1>
      <button className="text-sm text-[#6b6258]" onClick={() => void refresh()}>
        {cartQuery.isLoading ? "Loading prices…" : "Refresh prices"}
      </button>
      {cart?.groups.map((group) => (
        <section key={group.vendor_id} className="panel p-4">
          <h2>{group.vendor_name}</h2>
          {group.lines.map((line) => (
            <div key={line.id} className="mt-3 flex justify-between gap-3">
              <div>
                <p>{line.title}</p>
                <p className="text-sm text-[#6b6258]">
                  {line.color} · {money(line.unit_price_cents)} · {line.qty}
                  {line.problem ? ` · ${line.problem}` : ""}
                </p>
              </div>
              <button
                onClick={() =>
                  void unwrap(browserApi.DELETE("/api/cart/items/{line_id}", { params: { path: { line_id: line.id } } })).then(() => refresh())
                }
              >
                Remove
              </button>
            </div>
          ))}
        </section>
      ))}
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void unwrap(browserApi.POST("/api/cart/coupon", { body: { code } }))
            .then(() => refresh())
            .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : "Coupon was not applied"));
        }}
      >
        <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="WELCOME10" className="rounded-full border border-[#e2d8c8] bg-white px-3 py-2" />
        <button className="rounded-full border border-[#e2d8c8] px-3">Apply</button>
      </form>
      {cart ? (
        <p>
          Total {money(cart.total_cents)}
          {cart.coupon_message ? ` · ${cart.coupon_message}` : ""}
        </p>
      ) : (
        <p>Open the cart to load live prices.</p>
      )}
      <Link href="/checkout" className="inline-block rounded-full bg-[#b8572a] px-4 py-2 text-white">
        Checkout
      </Link>
    </div>
  );
}

export function CheckoutScreen() {
  const { me, loading } = useSession();
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

  if (loading) return <p className="wrap py-8">Loading…</p>;
  if (!me) return <p className="wrap py-8"><Link href="/login?next=/checkout">Sign in</Link> to check out.</p>;
  if (me.kind !== "customer") return <p className="wrap py-8">Checkout is for customer accounts.</p>;

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
      toast.success(`Order ${order.id} is placed`);
      router.push(`/account/orders/${order.id}`);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Checkout failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="wrap max-w-xl space-y-4 py-8" onSubmit={(event) => void pay(event)}>
      <h1 className="serif text-5xl">Checkout</h1>
      <p className="text-sm text-[#6b6258]">{cart ? `Total ${money(cart.total_cents)}` : cartQuery.isLoading ? "Loading the cart…" : "Your cart is empty."}</p>
      <label className="block">
        Name
        <input className="mt-1 w-full rounded-xl border border-[#e2d8c8] bg-white px-3 py-2" value={name} onChange={(event) => setShipName(event.target.value)} required />
      </label>
      <label className="block">
        Address
        <input className="mt-1 w-full rounded-xl border border-[#e2d8c8] bg-white px-3 py-2" value={shipAddress} onChange={(event) => setShipAddress(event.target.value)} required />
      </label>
      <label className="block">
        Card
        <input className="mt-1 w-full rounded-xl border border-[#e2d8c8] bg-white px-3 py-2" value={card} onChange={(event) => setCard(event.target.value)} required />
      </label>
      <p className="text-sm text-[#6b6258]">4242 4242 4242 4242 is approved. 4000 0000 0000 0002 is declined and releases the stock.</p>
      <button disabled={busy} className="rounded-full bg-[#24362c] px-4 py-2 text-[#f6efe3]">
        {busy ? "Paying…" : "Pay and place the order"}
      </button>
    </form>
  );
}
