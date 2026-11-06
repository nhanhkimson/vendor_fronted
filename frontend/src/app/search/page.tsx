import { SearchView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string; tag?: string; sort?: string }>;
}) {
  const query = await searchParams;
  const [page, categories] = await Promise.all([
    unwrap(
      serverApi.GET("/api/store/products", {
        params: {
          query: {
            q: query.q,
            category: query.category,
            tag: query.tag,
            sort: query.sort || "popular",
            page_size: 48,
          },
        },
      }),
    ),
    unwrap(serverApi.GET("/api/store/categories")),
  ]);
  return (
    <SearchView
      q={query.q}
      category={query.category}
      sort={query.sort}
      total={page.total}
      products={page.items}
      categories={categories}
    />
  );
}
