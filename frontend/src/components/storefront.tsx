"use client";

import Link from "next/link";

import { AddToCart } from "@/components/buy";
import { useSession } from "@/components/providers";
import { DealPrice, ProductGrid } from "@/components/site";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { categoryLabel, cityLabel, isDemoListing, productBlurb, productLabel, saleFor, shopBlurb, shopLabel } from "@/lib/labels";
import type { components } from "@/lib/api-types";

type Home = components["schemas"]["HomeOut"];
type Shop = components["schemas"]["ShopCard"];
type Review = components["schemas"]["ReviewCard"];
type Product = components["schemas"]["ProductCard"];
type ProductDetail = components["schemas"]["ProductDetail"];
type ShopPage = components["schemas"]["ShopPage"];
type Category = components["schemas"]["CategoryOut"];

function Section({
  title,
  action,
  hint,
  children,
  heading = "h2",
}: {
  title: string;
  action?: React.ReactNode;
  hint?: string;
  children: React.ReactNode;
  heading?: "h1" | "h2";
}) {
  const Heading = heading;
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Heading className="serif text-4xl leading-none">{title}</Heading>
          {hint ? <p className="mt-2 text-sm text-muted-foreground">{hint}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function HomeView({
  home,
  listings,
  listingTotal,
}: {
  home: Home;
  listings: Product[];
  listingTotal: number;
}) {
  const { me } = useSession();
  const catalogue = (listings.length ? listings : [...home.featured, ...home.new_arrivals])
    .filter((item) => !isDemoListing(item.title))
    .slice(0, 8);
  const shops = home.shops.slice(0, 4);
  const guest = !me;

  return (
    <div className="wrap space-y-12 py-8">
      <section className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div className="space-y-4">
          <p className="text-xs uppercase tracking-[0.18em] text-secondary">Cambodia marketplace</p>
          <h1 className="serif text-5xl leading-[0.95] sm:text-6xl">Independent shops. One checkout.</h1>
          <p className="max-w-xl text-muted-foreground">
            Buy from real makers, pay once, and track each shop’s parcel. Sellers list a photo, price, and description. Staff verify the shop before it goes live.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button asChild className="rounded-full">
              <Link href="/search">Browse listings</Link>
            </Button>
            <Button asChild variant="outline" className="rounded-full">
              <Link href={guest ? "/login" : me.kind === "customer" ? "/account" : me.kind === "vendor" ? "/seller" : "/admin"}>
                {guest ? "Sign in" : me.kind === "customer" ? "Your orders" : me.kind === "vendor" ? "Seller desk" : "Staff desk"}
              </Link>
            </Button>
          </div>
        </div>
        <ol className="grid gap-3 sm:grid-cols-3">
          {[
            ["1", "Buy", "Add to cart, pay, then track."],
            ["2", "Sell", "Photo, description, price. Then discounts."],
            ["3", "Staff", "Verify the shop. Publish the listing."],
          ].map(([n, title, body]) => (
            <li key={title} className="panel space-y-2 p-4">
              <p className="text-xs uppercase tracking-wide text-secondary">{n} · {title}</p>
              <p className="text-sm leading-snug">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <Section
        title="For you today"
        hint="A short set. Open Browse when you want the full catalogue."
        action={
          <Link href="/search" className="text-sm text-muted-foreground hover:underline">
            See all{listingTotal ? ` · ${listingTotal}` : ""}
          </Link>
        }
      >
        <ProductGrid products={catalogue} />
      </Section>

      {shops.length ? (
        <Section title="Shops" hint="Each shop ships its own parcel." action={<Link href="/shops" className="text-sm text-muted-foreground hover:underline">All shops</Link>}>
          <ShopGrid shops={shops} />
        </Section>
      ) : null}

      {me?.kind === "vendor" || me?.kind === "platform" ? null : (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-card px-5 py-4 ring-1 ring-border">
          <p className="text-sm">Selling? Open a shop, add a photo and a price, then wait for staff to publish.</p>
          <Button asChild size="sm" className="rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90">
            <Link href="/sell">Open a shop</Link>
          </Button>
        </div>
      )}
    </div>
  );
}

function ShopGrid({ shops }: { shops: Shop[] }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
      {shops.map((shop) => (
        <Link key={shop.id} href={`/shops/${shop.slug}`} className="group panel overflow-hidden transition hover:-translate-y-0.5 hover:border-primary/40">
          <div className="relative h-44 overflow-hidden bg-muted">
            {shop.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={shop.image_url} alt="" className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]" />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">{cityLabel(shop.city)}</div>
            )}
            <span className="absolute left-3 top-3 rounded-full bg-background/90 px-2.5 py-1 text-xs">{cityLabel(shop.city)}</span>
          </div>
          <div className="space-y-2 p-4">
            <h3 className="serif text-2xl leading-tight">{shopLabel(shop.id, shop.name)}</h3>
            <p className="line-clamp-2 text-sm text-muted-foreground">{shopBlurb(shop.id, shop.headline)}</p>
            <p className="text-xs text-muted-foreground">
              {shop.product_count} listings
              {shop.rating ? ` · ${shop.rating.toFixed(1)}` : ""}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}

export function ShopsView({ shops }: { shops: Shop[] }) {
  return (
    <div className="wrap space-y-8 py-8">
      <div className="max-w-2xl space-y-2">
        <h1 className="serif text-5xl">Shops</h1>
        <p className="text-muted-foreground">A short list of live makers. Open one shop, then buy. Each shop ships its own parcel.</p>
      </div>
      <ShopGrid shops={shops} />
    </div>
  );
}

export function ShopView({ page }: { page: ShopPage }) {
  const shop = page.shop;
  return (
    <div className="wrap space-y-8 py-8">
      <div className="panel overflow-hidden md:grid md:grid-cols-[0.9fr_1.1fr]">
        <div className="h-56 bg-muted md:h-auto">
          {shop.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={shop.image_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full min-h-56 items-center justify-center text-muted-foreground">{cityLabel(shop.city)}</div>
          )}
        </div>
        <div className="space-y-3 p-6 md:p-8">
          <p className="text-xs uppercase tracking-wide text-secondary">{cityLabel(shop.city)}</p>
          <h1 className="serif text-5xl leading-none">{shopLabel(shop.id, shop.name)}</h1>
          <p className="max-w-md text-muted-foreground">{shopBlurb(shop.id, shop.headline)}</p>
          <p className="text-sm text-muted-foreground">
            {shop.product_count} listings
            {shop.rating ? ` · ${shop.rating.toFixed(1)}` : ""}
            {" · Ships its own parcels"}
          </p>
        </div>
      </div>
      <ProductGrid products={page.products} />
      {page.reviews.length ? (
        <Section title="Reviews">
          <div className="space-y-3">
            {page.reviews.map((review) => (
              <article key={review.id} className="panel p-4">
                <p className="text-sm text-muted-foreground">
                  {review.product_title} · {review.rating ?? "—"} stars
                </p>
                <p className="mt-1">{review.body}</p>
              </article>
            ))}
          </div>
        </Section>
      ) : null}
    </div>
  );
}

export function ReviewsView({ items }: { items: Review[] }) {
  const { t } = useI18n();
  return (
    <div className="wrap space-y-4 py-8">
      <h1 className="serif text-5xl">{t.reviews.title}</h1>
      <p className="text-muted-foreground">{t.reviews.intro}</p>
      {items.map((review) => (
        <article key={review.id} className="panel p-4">
          <p className="text-sm text-muted-foreground">
            {review.product_title} · {review.vendor_name} · {review.rating ?? "—"} {t.reviews.stars}
            {review.verified_purchase ? ` · ${t.reviews.verified}` : ""}
          </p>
          <p className="mt-1">{review.body}</p>
        </article>
      ))}
    </div>
  );
}

const SORTS = ["popular", "newest", "price_asc", "price_desc"] as const;

export function SearchView({
  q,
  category,
  sort,
  total,
  products,
  categories,
}: {
  q?: string;
  category?: string;
  sort?: string;
  total: number;
  products: Product[];
  categories: Category[];
}) {
  const roots = categories.filter((item) => !item.parent_id);
  const currentSort = sort || "popular";
  const sortLabel: Record<(typeof SORTS)[number], string> = {
    popular: "Popular",
    newest: "Newest",
    price_asc: "Price: low to high",
    price_desc: "Price: high to low",
  };

  function href(next: { category?: string; sort?: string }) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    const nextCategory = next.category === undefined ? category : next.category;
    const nextSort = next.sort === undefined ? currentSort : next.sort;
    if (nextCategory) params.set("category", nextCategory);
    if (nextSort && nextSort !== "popular") params.set("sort", nextSort);
    const query = params.toString();
    return query ? `/search?${query}` : "/search";
  }

  return (
    <div className="wrap space-y-6 py-8">
      <div className="space-y-2">
        <h1 className="serif text-5xl">{q ? `Results for “${q}”` : "All listings"}</h1>
        <p className="text-sm text-muted-foreground">
          {total} listings
        </p>
      </div>
      {roots.length ? (
        <div className="chips">
          <Link
            href={href({ category: "" })}
            className={`shrink-0 rounded-full px-4 py-2 text-sm ring-1 ${!category ? "bg-primary text-primary-foreground ring-primary" : "bg-card ring-border"}`}
          >
            All
          </Link>
          {roots.map((item) => (
            <Link
              key={item.id}
              href={href({ category: item.slug })}
              className={`shrink-0 rounded-full px-4 py-2 text-sm ring-1 ${category === item.slug ? "bg-primary text-primary-foreground ring-primary" : "bg-card ring-border"}`}
            >
              {categoryLabel(item.slug, item.name)}
              <span className="ml-2 opacity-70">{item.product_count}</span>
            </Link>
          ))}
        </div>
      ) : null}
      <div className="chips">
        {SORTS.map((item) => (
          <Link
            key={item}
            href={href({ sort: item })}
            className={`shrink-0 rounded-full px-4 py-2 text-sm ring-1 ${currentSort === item ? "bg-card ring-primary" : "bg-card ring-border"}`}
          >
            {sortLabel[item]}
          </Link>
        ))}
      </div>
      {products.length ? <ProductGrid products={products} /> : <p className="text-muted-foreground">No listings match that search.</p>}
    </div>
  );
}

export function ProductView({ product }: { product: ProductDetail }) {
  const sale = saleFor(product.id, product.vendor_id, product.price_cents);
  return (
    <div className="wrap space-y-12 py-8">
      <nav className="flex flex-wrap gap-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:underline">
          Home
        </Link>
        {product.category_path.map((item) => (
          <span key={item.id}>
            /{" "}
            <Link href={`/search?category=${encodeURIComponent(item.slug)}`} className="hover:underline">
              {categoryLabel(item.slug, item.name)}
            </Link>
          </span>
        ))}
      </nav>
      <div className="grid gap-8 md:grid-cols-2">
        <div className="panel overflow-hidden">
          <div className="product-media flex items-center justify-center bg-muted text-muted-foreground">
            {product.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image_url} alt="" className="h-full w-full object-cover" />
            ) : (
              product.vendor_name
            )}
          </div>
        </div>
        <div className="space-y-4">
          <Link href={`/shops/${product.vendor_slug}`} className="text-sm text-secondary hover:underline">
            {shopLabel(product.vendor_id, product.vendor_name)}
          </Link>
          <h1 className="serif text-5xl leading-none">{productLabel(product.id, product.title)}</h1>
          {sale ? (
            <p className="text-xs font-medium uppercase tracking-wide text-secondary">{sale.percent}% off</p>
          ) : null}
          <DealPrice cents={product.price_cents} deal={sale} size="lg" />
          <p className="text-sm text-muted-foreground">
            {product.units_sold ? `${product.units_sold} sold` : null}
            {` · ${product.available} in stock`}
          </p>
          <p className="text-sm text-muted-foreground">Ships from {cityLabel(product.shop.city)}</p>
          {product.description ? (
            <p className="max-w-prose text-sm leading-relaxed">{productBlurb(product.id, product.description)}</p>
          ) : null}
          <AddToCart product={product} />
        </div>
      </div>
      {product.reviews.length ? (
        <Section title="Reviews">
          <div className="space-y-3">
            {product.reviews.map((review) => (
              <article key={review.id} className="panel p-4">
                <p className="text-sm">
                  {review.rating ? `${review.rating} stars` : review.sentiment} · {review.buyer_name}
                </p>
                <p className="mt-1">{review.body}</p>
                {review.vendor_response ? <p className="mt-2 text-sm text-muted-foreground">Shop: {review.vendor_response}</p> : null}
              </article>
            ))}
          </div>
        </Section>
      ) : null}
      {product.related.length ? (
        <Section title="More from the catalogue">
          <ProductGrid products={product.related} />
        </Section>
      ) : null}
    </div>
  );
}

export function AboutView() {
  const { t } = useI18n();
  return (
    <div className="wrap max-w-2xl space-y-4 py-10">
      <h1 className="serif text-5xl">{t.about.title}</h1>
      <p>{t.about.p1}</p>
      <p>{t.about.p2}</p>
      <p className="text-muted-foreground">{t.about.note}</p>
    </div>
  );
}

export function GuideView() {
  const { t } = useI18n();
  return (
    <div className="wrap max-w-3xl space-y-8 py-10">
      <div className="space-y-2">
        <h1 className="serif text-5xl">{t.guide.title}</h1>
        <p className="text-muted-foreground">{t.guide.intro}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {t.guide.surfaces.map(([title, body]) => (
          <div key={title} className="panel space-y-2 p-4">
            <p className="text-xs uppercase tracking-wide text-secondary">{title}</p>
            <p className="text-sm leading-relaxed text-foreground">{body}</p>
          </div>
        ))}
      </div>
      <ol className="space-y-4">
        {t.guide.steps.map(([title, body], index) => (
          <li key={title} className="panel p-4">
            <p className="text-xs uppercase tracking-wide text-secondary">
              {t.guide.step} {index + 1}
            </p>
            <h2 className="text-xl">{title}</h2>
            <p className="text-muted-foreground">{body}</p>
          </li>
        ))}
      </ol>
      <p>
        {t.guide.footerBefore} <Link href="/login">{t.guide.loginPage}</Link>
        {t.guide.footerAfter} <b>demo</b>. {t.guide.apiRef} <a href="/api/docs">/api/docs</a>.
      </p>
    </div>
  );
}
