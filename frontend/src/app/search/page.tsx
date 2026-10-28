import { SearchView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string; category?: string; tag?: string }> }) {
  const query = await searchParams;
  const page = await unwrap(
    serverApi.GET("/api/store/products", {
      params: { query: { q: query.q, category: query.category, tag: query.tag, page_size: 24 } },
    }),
  );
  return <SearchView q={query.q} total={page.total} products={page.items} />;
}
