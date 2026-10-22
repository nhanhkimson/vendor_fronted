import { ProductGrid } from "@/components/site";
import { serverApi, unwrap } from "@/lib/api";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string; category?: string; tag?: string }> }) {
  const query = await searchParams;
  const page = await unwrap(
    serverApi.GET("/api/store/products", {
      params: { query: { q: query.q, category: query.category, tag: query.tag, page_size: 24 } },
    }),
  );
  return (
    <div className="wrap space-y-6 py-8">
      <h1 className="serif text-5xl">{query.q ? `Results for “${query.q}”` : "The catalogue"}</h1>
      <p className="text-sm text-[#6b6258]">{page.total} pieces</p>
      <ProductGrid products={page.items} />
    </div>
  );
}
