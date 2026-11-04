import { ApiError } from "@/lib/api";

export type ListingProduct = {
  id: string;
  title: string;
  description?: string;
  price_cents: number;
  available: number;
  listing_status: string;
  listing_reason?: string | null;
  vendor_name?: string;
  category_id?: string | null;
};

export type ProductCreateInput = {
  title: string;
  description?: string;
  price_cents: number;
  category_id?: string | null;
  variants?: { sku: string; size?: string; color?: string; stock: number }[];
};

export type ProductUpdateInput = {
  title?: string;
  description?: string;
  price_cents?: number;
  category_id?: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-Bazaar-Client", "web");
  if (init?.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...init, headers, credentials: "include" });
  const ctype = response.headers.get("content-type") || response.headers.get("Content-Type") || "";
  const payload = ctype.includes("json") || response.status !== 204 ? await response.json().catch(() => null) : null;
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : response.statusText || "Request failed";
    throw new ApiError(response.status, detail, payload?.code);
  }
  return payload as T;
}

export function listSellerProducts() {
  return request<ListingProduct[]>("/api/seller/products");
}

export function createProduct(body: ProductCreateInput) {
  return request<ListingProduct>("/api/seller/products", { method: "POST", body: JSON.stringify(body) });
}

export function updateProduct(productId: string, body: ProductUpdateInput) {
  return request<ListingProduct>(`/api/seller/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function submitListing(productId: string) {
  return request<ListingProduct>(`/api/seller/products/${productId}/submit`, { method: "POST" });
}

export function listPendingListings() {
  return request<ListingProduct[]>("/api/listings/pending");
}

export function approveListing(productId: string) {
  return request<ListingProduct>(`/api/listings/${productId}/approve`, { method: "POST" });
}

export function rejectListing(productId: string, reason: string) {
  return request<ListingProduct>(`/api/listings/${productId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
