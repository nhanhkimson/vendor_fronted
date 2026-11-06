import { HomeView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function HomePage() {
  const [home, catalogue] = await Promise.all([
    unwrap(serverApi.GET("/api/store/home")),
    unwrap(serverApi.GET("/api/store/products", { params: { query: { page_size: 8, sort: "popular" } } })),
  ]);
  return <HomeView home={home} listings={catalogue.items} listingTotal={catalogue.total} />;
}
