"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { browserApi, unwrap } from "@/lib/api";
import { readGuestCart } from "@/lib/guest-cart";
import { money } from "@/lib/format";
import { LanguageSwitcher, useI18n } from "@/lib/i18n";
import type { components } from "@/lib/api-types";

type Card = components["schemas"]["ProductCard"];

export function SiteHeader() {
  const { me, loading, refresh } = useSession();
  const { t } = useI18n();
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
    ["/", t.nav.shop],
    ["/shops", t.nav.shops],
    ["/reviews", t.nav.reviews],
    ["/sell", t.nav.sell],
    ["/guide", t.nav.guide],
  ] as const;

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/90 backdrop-blur">
      <div className="wrap flex min-h-[72px] items-center gap-4">
        <Link href="/" className="serif text-3xl leading-none tracking-tight">
          Bazaar
        </Link>
        <nav className="flex flex-1 flex-wrap gap-1">
          {links.map(([href, label]) => (
            <Button key={href} asChild variant={path === href ? "secondary" : "ghost"} size="sm">
              <Link href={href}>{label}</Link>
            </Button>
          ))}
        </nav>
        <LanguageSwitcher />
        <ThemeToggle />
        <form
          className="hidden sm:block"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            router.push(`/search?q=${encodeURIComponent(String(data.get("q") || ""))}`);
          }}
        >
          <Input name="q" placeholder={t.nav.search} className="w-44 rounded-full" />
        </form>
        <Button asChild variant="outline" size="sm" className="rounded-full">
          <Link href="/cart">
            {t.nav.cart}
            {count ? (
              <Badge variant="secondary" className="ml-1">
                {count}
              </Badge>
            ) : null}
          </Link>
        </Button>
        {loading ? (
          <Skeleton className="h-9 w-24 rounded-full" />
        ) : me ? (
          <>
            <Button asChild size="sm" className="rounded-full">
              <Link href={me.home}>{me.name}</Link>
            </Button>
            <Button variant="ghost" size="sm" onClick={() => void signOut()}>
              {t.nav.signOut}
            </Button>
          </>
        ) : (
          <Button asChild size="sm" className="rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90">
            <Link href="/login">{t.nav.signIn}</Link>
          </Button>
        )}
      </div>
    </header>
  );
}

export function SiteFooter() {
  const { t } = useI18n();
  return (
    <footer className="mt-16 border-t border-border py-8 text-sm text-muted-foreground">
      <div className="wrap flex flex-wrap justify-between gap-3">
        <p className="serif text-2xl text-foreground">Bazaar</p>
        <p>{t.footer.tagline}</p>
        <div className="flex gap-3">
          <Link href="/sell" className="underline-offset-2 hover:underline">
            {t.nav.sell}
          </Link>
          <Link href="/about">{t.nav.about}</Link>
        </div>
      </div>
    </footer>
  );
}

export function ProductGrid({ products }: { products: Card[] }) {
  return (
    <div className="grid-cards">
      {products.map((product) => (
        <Link key={product.id} href={`/products/${product.id}`} className="panel overflow-hidden">
          <div className="flex h-40 items-center justify-center bg-muted text-muted-foreground">
            {product.image_url ? (
              // Seeded photos are served by the API when the files exist.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image_url} alt="" className="h-full w-full object-cover" />
            ) : (
              product.vendor_name
            )}
          </div>
          <div className="space-y-1 p-4">
            <p className="text-xs uppercase tracking-wide text-primary">{product.vendor_name}</p>
            <h3 className="font-medium">{product.title}</h3>
            <p className="text-sm text-muted-foreground">
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
