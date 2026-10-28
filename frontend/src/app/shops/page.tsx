import { ShopsView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function ShopsPage() {
  const shops = await unwrap(serverApi.GET("/api/store/shops"));
  return <ShopsView shops={shops} />;
}
