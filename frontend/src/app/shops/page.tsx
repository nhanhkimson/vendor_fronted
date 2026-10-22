import Link from "next/link";

import { serverApi, unwrap } from "@/lib/api";

export default async function ShopsPage() {
  const shops = await unwrap(serverApi.GET("/api/store/shops"));
  return (
    <div className="wrap space-y-6 py-8">
      <h1 className="serif text-5xl">Shops</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {shops.map((shop) => (
          <Link key={shop.id} href={`/shops/${shop.slug}`} className="panel p-5">
            <p className="text-xs uppercase tracking-wide text-[#b8572a]">{shop.city}</p>
            <h2 className="serif text-3xl">{shop.name}</h2>
            <p className="text-[#6b6258]">{shop.headline}</p>
            <p className="mt-2 text-sm">{shop.product_count} pieces · {shop.tier_name}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
