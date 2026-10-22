import Link from "next/link";

import { ProductGrid } from "@/components/site";
import { serverApi, unwrap } from "@/lib/api";

export default async function HomePage() {
  const home = await unwrap(serverApi.GET("/api/store/home"));
  return (
    <div className="wrap space-y-12 py-8">
      <section className="grid items-center gap-8 md:grid-cols-2">
        <div>
          <p className="kh copper">ផ្សារទំនិញពីសិប្បករ</p>
          <h1 className="serif mt-2 text-6xl leading-none">Many shops. One checkout.</h1>
          <p className="mt-4 max-w-md text-[#6b6258]">
            Buy from independent makers in a single payment. Each shop ships its own parcel, and the commission was
            frozen when you paid.
          </p>
          <div className="mt-6 flex gap-3 text-sm">
            <span className="rounded-full bg-white px-3 py-2">{home.stats.shops} shops</span>
            <span className="rounded-full bg-white px-3 py-2">{home.stats.products} pieces</span>
            <span className="rounded-full bg-white px-3 py-2">{home.stats.customers} customers</span>
          </div>
        </div>
        <div className="panel p-5">
          <p className="text-xs uppercase tracking-wide text-[#b8572a]">Live now</p>
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
          <h2 className="serif text-4xl">Featured</h2>
          <Link href="/search">Browse all</Link>
        </div>
        <ProductGrid products={home.featured} />
      </section>
      <section>
        <h2 className="serif mb-4 text-4xl">Shops</h2>
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
