"use client";

import Link from "next/link";

import { ProductGrid } from "@/components/site";
import { useI18n } from "@/lib/i18n";
import type { components } from "@/lib/api-types";

type Home = components["schemas"]["HomeOut"];
type Shop = components["schemas"]["ShopCard"];
type Review = components["schemas"]["ReviewCard"];
type Product = components["schemas"]["ProductCard"];

export function HomeView({ home }: { home: Home }) {
  const { t } = useI18n();
  return (
    <div className="wrap space-y-12 py-8">
      <section className="grid items-center gap-8 md:grid-cols-2">
        <div>
          <p className="copper">{t.home.eyebrow}</p>
          <h1 className="serif mt-2 text-6xl leading-none">{t.home.title}</h1>
          <p className="mt-4 max-w-md text-[#6b6258]">{t.home.body}</p>
          <div className="mt-6 flex gap-3 text-sm">
            <span className="rounded-full bg-white px-3 py-2">
              {home.stats.shops} {t.home.shops}
            </span>
            <span className="rounded-full bg-white px-3 py-2">
              {home.stats.products} {t.home.pieces}
            </span>
            <span className="rounded-full bg-white px-3 py-2">
              {home.stats.customers} {t.home.customers}
            </span>
          </div>
        </div>
        <div className="panel p-5">
          <p className="text-xs uppercase tracking-wide text-[#b8572a]">{t.home.liveNow}</p>
          <ul className="mt-3 space-y-2">
            {home.promotions.map((promo) => (
              <li key={promo.code}>
                <b>{promo.code}</b> <span className="text-[#6b6258]">{promo.note}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
      <section>
        <div className="mb-4 flex items-end justify-between">
          <h2 className="serif text-4xl">{t.home.featured}</h2>
          <Link href="/search">{t.home.browseAll}</Link>
        </div>
        <ProductGrid products={home.featured} />
      </section>
      <section>
        <h2 className="serif mb-4 text-4xl">{t.home.shopsHeading}</h2>
        <div className="grid gap-3 md:grid-cols-3">
          {home.shops.map((shop) => (
            <Link key={shop.id} href={`/shops/${shop.slug}`} className="panel p-4">
              <h3 className="text-lg">{shop.name}</h3>
              <p className="text-sm text-[#6b6258]">{shop.headline}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

export function ShopsView({ shops }: { shops: Shop[] }) {
  const { t } = useI18n();
  return (
    <div className="wrap space-y-6 py-8">
      <h1 className="serif text-5xl">{t.shops.title}</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {shops.map((shop) => (
          <Link key={shop.id} href={`/shops/${shop.slug}`} className="panel p-5">
            <p className="text-xs uppercase tracking-wide text-[#b8572a]">{shop.city}</p>
            <h2 className="serif text-3xl">{shop.name}</h2>
            <p className="text-[#6b6258]">{shop.headline}</p>
            <p className="mt-2 text-sm">
              {shop.product_count} {t.shops.pieces} · {shop.tier_name}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function ReviewsView({ items }: { items: Review[] }) {
  const { t } = useI18n();
  return (
    <div className="wrap space-y-4 py-8">
      <h1 className="serif text-5xl">{t.reviews.title}</h1>
      <p className="text-[#6b6258]">{t.reviews.intro}</p>
      {items.map((review) => (
        <article key={review.id} className="panel p-4">
          <p className="text-sm text-[#6b6258]">
            {review.product_title} · {review.vendor_name} · {review.rating ?? "—"} {t.reviews.stars}
            {review.verified_purchase ? ` · ${t.reviews.verified}` : ""}
          </p>
          <p className="mt-1">{review.body}</p>
        </article>
      ))}
    </div>
  );
}

export function SearchView({ q, total, products }: { q?: string; total: number; products: Product[] }) {
  const { t } = useI18n();
  return (
    <div className="wrap space-y-6 py-8">
      <h1 className="serif text-5xl">{q ? `${t.search.resultsFor} “${q}”` : t.search.catalogue}</h1>
      <p className="text-sm text-[#6b6258]">
        {total} {t.search.pieces}
      </p>
      <ProductGrid products={products} />
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
      <p className="text-[#6b6258]">{t.about.note}</p>
    </div>
  );
}

export function GuideView() {
  const { t } = useI18n();
  return (
    <div className="wrap max-w-2xl space-y-6 py-10">
      <h1 className="serif text-5xl">{t.guide.title}</h1>
      <ol className="space-y-4">
        {t.guide.steps.map(([title, body], index) => (
          <li key={title} className="panel p-4">
            <p className="text-xs uppercase tracking-wide text-[#b8572a]">
              {t.guide.step} {index + 1}
            </p>
            <h2 className="text-xl">{title}</h2>
            <p className="text-[#6b6258]">{body}</p>
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
