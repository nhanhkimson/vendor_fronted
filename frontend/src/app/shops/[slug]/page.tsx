import { ProductGrid } from "@/components/site";
import { serverApi, unwrap } from "@/lib/api";

export default async function ShopPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await unwrap(serverApi.GET("/api/store/shops/{slug}", { params: { path: { slug } } }));
  return (
    <div className="wrap space-y-6 py-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-[#b8572a]">{page.shop.city}</p>
        <h1 className="serif text-5xl">{page.shop.name}</h1>
        <p className="max-w-xl text-[#6b6258]">{page.shop.about}</p>
      </div>
      <ProductGrid products={page.products} />
    </div>
  );
}
