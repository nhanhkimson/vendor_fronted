import { ProductView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await unwrap(serverApi.GET("/api/store/products/{product_id}", { params: { path: { product_id: id } } }));
  return <ProductView product={product} />;
}
