"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers";
import { browserApi, unwrap } from "@/lib/api";
import { readGuestCart } from "@/lib/guest-cart";
import { money } from "@/lib/format";
import type { components } from "@/lib/api-types";

type Card = components["schemas"]["ProductCard"];

export function SiteHeader() {
  const { me, refresh } = useSession();
  const path = usePathname();
  const router = useRouter();
  const [count, setCount] = useState(0);

  useEffect(() => {
    let stop = false;
    async function load() {
      if (me?.kind === "customer") {
        const cart = await unwrap(browserApi.GET("/api/cart")).catch(() => null);
        if (!stop) setCount(cart?.item_count ?? 0);
      } else if (!me) {
        if (!stop) setCount(readGuestCart().reduce((sum, line) => sum + line.qty, 0));
      } else if (!stop) setCount(0);
    }
    void load();
    window.addEventListener("bazaar-cart", load);
    return () => {
      stop = true;
      window.removeEventListener("bazaar-cart", load);
    };
  }, [me]);

  async function signOut() {
    await unwrap(browserApi.POST("/api/auth/logout"));
    await refresh();
    router.push("/");
  }

  const links = [
    ["/", "Shop"],
    ["/shops", "Shops"],
    ["/reviews", "Reviews"],
    ["/sell", "Sell"],
    ["/guide", "Guide"],
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-[#e2d8c8] bg-[#f4eee4]/90 backdrop-blur">
      <div className="wrap flex min-h-[72px] items-center gap-4">
        <Link href="/" className="serif text-3xl leading-none tracking-tight">
          Bazaar
        </Link>
        <nav className="flex flex-1 flex-wrap gap-1">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className={`rounded-full px-3 py-2 text-sm ${path === href ? "bg-white" : "text-[#6b6258]"}`}
            >
              {label}
            </Link>
          ))}
        </nav>
        <form
          className="hidden sm:block"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            router.push(`/search?q=${encodeURIComponent(String(data.get("q") || ""))}`);
          }}
        >
          <input name="q" placeholder="Search makers" className="rounded-full border border-[#e2d8c8] bg-white px-4 py-2 text-sm" />
        </form>
        <Link href="/cart" className="rounded-full border border-[#e2d8c8] bg-white px-3 py-2 text-sm">
          Cart{count ? ` ${count}` : ""}
        </Link>
        {me ? (
          <>
            <Link href={me.home} className="rounded-full bg-[#24362c] px-3 py-2 text-sm text-[#f6efe3]">
              {me.name}
            </Link>
            <button onClick={() => void signOut()} className="text-sm text-[#6b6258]">
              Sign out
            </button>
          </>
        ) : (
          <Link href="/login" className="rounded-full bg-[#b8572a] px-3 py-2 text-sm text-white">
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-[#e2d8c8] py-8 text-sm text-[#6b6258]">
      <div className="wrap flex flex-wrap justify-between gap-3">
        <p className="serif text-2xl text-[#171411]">Bazaar</p>
        <p>Independent shops. One checkout. Commission frozen at the moment you pay.</p>
        <Link href="/about">About</Link>
      </div>
    </footer>
  );
}

export function ProductGrid({ products }: { products: Card[] }) {
  return (
    <div className="grid-cards">
      {products.map((product) => (
        <Link key={product.id} href={`/products/${product.id}`} className="panel overflow-hidden">
          <div className="flex h-40 items-center justify-center bg-[#ebe3d4] text-[#6b6258]">
            {product.image_url ? (
              // Seeded photos are served by the API when the files exist.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image_url} alt="" className="h-full w-full object-cover" />
            ) : (
              product.vendor_name
            )}
          </div>
          <div className="space-y-1 p-4">
            <p className="text-xs uppercase tracking-wide text-[#b8572a]">{product.vendor_name}</p>
            <h3 className="font-medium">{product.title}</h3>
            <p className="text-sm text-[#6b6258]">
              {money(product.price_cents)}
              {product.rating ? ` · ${product.rating.toFixed(1)}` : ""}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}

export function moneyLabel(cents: number | null | undefined) {
  return money(cents);
}
