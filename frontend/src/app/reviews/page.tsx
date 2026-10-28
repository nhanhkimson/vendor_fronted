import { ReviewsView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function ReviewsPage() {
  const page = await unwrap(serverApi.GET("/api/store/reviews", { params: { query: { page_size: 30 } } }));
  return <ReviewsView items={page.items} />;
}
