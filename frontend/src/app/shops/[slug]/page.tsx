import { ShopView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function ShopPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await unwrap(serverApi.GET("/api/store/shops/{slug}", { params: { path: { slug } } }));
  return <ShopView page={page} />;
}
