import { serverApi, unwrap } from "@/lib/api";

export default async function ReviewsPage() {
  const page = await unwrap(serverApi.GET("/api/store/reviews", { params: { query: { page_size: 30 } } }));
  return (
    <div className="wrap space-y-4 py-8">
      <h1 className="serif text-5xl">Reviews</h1>
      <p className="text-[#6b6258]">Published reviews only. A verified purchase is one placed on Bazaar and delivered.</p>
      {page.items.map((review) => (
        <article key={review.id} className="panel p-4">
          <p className="text-sm text-[#6b6258]">
            {review.product_title} · {review.vendor_name} · {review.rating ?? "—"} stars
            {review.verified_purchase ? " · verified purchase" : ""}
          </p>
          <p className="mt-1">{review.body}</p>
        </article>
      ))}
    </div>
  );
}
