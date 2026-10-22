import { AddToCart } from "@/components/buy";
import { money } from "@/lib/format";
import { serverApi, unwrap } from "@/lib/api";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await unwrap(serverApi.GET("/api/store/products/{product_id}", { params: { path: { product_id: id } } }));
  return (
    <div className="wrap grid gap-8 py-8 md:grid-cols-2">
      <div className="panel flex min-h-80 items-center justify-center bg-[#ebe3d4] text-[#6b6258]">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image_url} alt="" className="h-full w-full object-cover" />
        ) : (
          product.vendor_name
        )}
      </div>
      <div className="space-y-4">
        <p className="text-sm text-[#b8572a]">{product.vendor_name}</p>
        <h1 className="serif text-5xl">{product.title}</h1>
        <p className="text-2xl">{money(product.price_cents)}</p>
        <p className="text-[#6b6258]">{product.description}</p>
        <AddToCart product={product} />
        <div className="space-y-3 pt-4">
          {product.reviews.map((review) => (
            <article key={review.id} className="panel p-4">
              <p className="text-sm">{review.rating ? `${review.rating} stars` : review.sentiment} · {review.buyer_name}</p>
              <p>{review.body}</p>
              {review.vendor_response ? <p className="mt-2 text-sm text-[#6b6258]">Shop: {review.vendor_response}</p> : null}
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
