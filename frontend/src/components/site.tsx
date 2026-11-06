"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers";
import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { browserApi, unwrap } from "@/lib/api";
import { money } from "@/lib/format";
import { readGuestCart } from "@/lib/guest-cart";
import { isDemoListing, productLabel, saleFor, shopLabel, type SaleDeal } from "@/lib/labels";
import type { components } from "@/lib/api-types";

type Card = components["schemas"]["ProductCard"];

export function SearchBar({ size = "sm", className = "" }: { size?: "sm" | "lg"; className?: string }) {
  const router = useRouter();
  return (
    <form
      className={className}
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        const q = String(data.get("q") || "").trim();
        router.push(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
      }}
    >
      <Input
        name="q"
        placeholder="Search products and shops"
        className={size === "lg" ? "h-12 w-full rounded-full bg-card px-5 text-base" : "h-10 w-full rounded-full bg-card"}
        aria-label="Search products and shops"
      />
    </form>
  );
}

function workspaceMeta(kind?: string) {
  if (kind === "vendor") return { href: "/seller", label: "Seller" };
  if (kind === "platform") return { href: "/admin", label: "Admin" };
  return { href: "/account", label: "Account" };
}

export function SiteHeader() {
  const { me, loading, refresh } = useSession();
  const path = usePathname();
  const router = useRouter();
  const [count, setCount] = useState(0);
  const workspace = workspaceMeta(me?.kind);

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
    ["/search", "Browse"],
    ["/shops", "Shops"],
    ["/sell", "Sell"],
  ] as const;

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/90 backdrop-blur">
      <div className="wrap flex flex-col gap-2 py-2.5">
        <div className="flex items-center gap-3">
          <Link href="/" className="serif shrink-0 text-3xl leading-none tracking-tight">
            Bazaar
          </Link>
          <SearchBar className="hidden min-w-0 flex-1 md:block" />
          <nav className="hidden items-center gap-0.5 md:flex">
            {links.map(([href, label]) =>
              label === "Sell" ? (
                <Button
                  key={href}
                  asChild
                  size="sm"
                  className="shrink-0 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90"
                >
                  <Link href={href}>{label}</Link>
                </Button>
              ) : (
                <Button key={href} asChild variant={path === href ? "secondary" : "ghost"} size="sm" className="shrink-0">
                  <Link href={href}>{label}</Link>
                </Button>
              ),
            )}
          </nav>
          <div className="ml-auto flex shrink-0 items-center gap-1">
            <ThemeToggle />
            <Button asChild size="sm" className="rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90 md:hidden">
              <Link href="/sell">Sell</Link>
            </Button>
            {me?.kind !== "platform" && me?.kind !== "vendor" ? (
              <Button asChild variant="outline" size="sm" className="rounded-full">
                <Link href="/cart">
                  Cart
                  {count ? (
                    <Badge variant="secondary" className="ml-1">
                      {count}
                    </Badge>
                  ) : null}
                </Link>
              </Button>
            ) : null}
            {loading ? (
              <Skeleton className="h-9 w-24 rounded-full" />
            ) : me ? (
              <>
                {me.kind !== "customer" ? (
                  <Button asChild size="sm" className="rounded-full">
                    <Link href={workspace.href}>{workspace.label}</Link>
                  </Button>
                ) : null}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="rounded-full pl-1 pr-2">
                      <Avatar size="sm">
                        {me.avatar_url ? <AvatarImage src={me.avatar_url} alt="" /> : null}
                        <AvatarFallback>{me.name.slice(0, 1)}</AvatarFallback>
                      </Avatar>
                      <span className="hidden max-w-28 truncate sm:inline">{me.name}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <p className="truncate">{me.name}</p>
                      <p className="truncate text-xs font-normal text-muted-foreground">{me.email}</p>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {me.kind === "customer" ? (
                      <>
                        <DropdownMenuItem onClick={() => router.push("/account")}>Orders and account</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => router.push("/account/wishlist")}>Wishlist</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => router.push("/cart")}>Cart</DropdownMenuItem>
                      </>
                    ) : (
                      <DropdownMenuItem onClick={() => router.push(workspace.href)}>Open {workspace.label}</DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => void signOut()}>Sign out</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <Button asChild size="sm" className="rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90">
                <Link href="/login">Sign in</Link>
              </Button>
            )}
          </div>
        </div>
        <SearchBar className="md:hidden" />
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-border py-8 text-sm text-muted-foreground">
      <div className="wrap flex flex-wrap items-center justify-between gap-4">
        <p className="serif text-xl text-foreground">Bazaar</p>
        <nav className="flex flex-wrap gap-x-5 gap-y-2">
          <Link href="/search" className="hover:underline">
            Browse
          </Link>
          <Link href="/shops" className="hover:underline">
            Shops
          </Link>
          <Link href="/sell" className="hover:underline">
            Open a shop
          </Link>
          <Link href="/login" className="hover:underline">
            Sign in
          </Link>
        </nav>
      </div>
    </footer>
  );
}

export function ProductGrid({ products }: { products: Card[] }) {
  const items = products.filter((product) => !isDemoListing(product.title));
  if (!items.length) return null;
  return (
    <div className="grid-cards">
      {items.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

export function DealPrice({
  cents,
  productId,
  vendorId,
  deal,
  size = "md",
}: {
  cents: number;
  productId?: string | null;
  vendorId?: string | null;
  deal?: SaleDeal | null;
  size?: "sm" | "md" | "lg";
}) {
  const sale = deal ?? saleFor(productId, vendorId, cents);
  const now = size === "lg" ? "text-2xl font-medium" : size === "sm" ? "text-sm font-medium" : "text-base font-medium";
  if (!sale) return <span className={now}>{money(cents)}</span>;
  return (
    <span className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
      <span className={`${now} text-secondary`}>{money(sale.now)}</span>
      <span className="text-sm text-muted-foreground line-through">{money(sale.was)}</span>
    </span>
  );
}

export function ProductCard({ product }: { product: Card }) {
  const soldOut = product.available < 1;
  const shop = shopLabel(product.vendor_id, product.vendor_name);
  const title = productLabel(product.id, product.title);
  const sale = saleFor(product.id, product.vendor_id, product.price_cents);
  return (
    <Link href={`/products/${product.id}`} className="group block h-full">
      <article className="panel h-full overflow-hidden transition hover:-translate-y-0.5 hover:border-primary/40">
        <div className="product-media relative flex items-center justify-center bg-muted text-muted-foreground">
          {product.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image_url} alt="" className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" />
          ) : (
            <span className="px-3 text-center text-sm">{shop}</span>
          )}
          {sale ? (
            <span className="absolute left-3 top-3 rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground">
              {sale.percent}% off
            </span>
          ) : null}
          {soldOut ? (
            <span className="absolute inset-x-3 bottom-3 rounded-full bg-background/90 px-2 py-1 text-center text-xs">Sold out</span>
          ) : null}
        </div>
        <div className="space-y-1.5 p-4">
          <p className="text-xs text-muted-foreground">{shop}</p>
          <h3 className="line-clamp-2 min-h-11 font-medium leading-snug">{title}</h3>
          <DealPrice cents={product.price_cents} deal={sale} />
        </div>
      </article>
    </Link>
  );
}

export function moneyLabel(cents: number | null | undefined) {
  return money(cents);
}
