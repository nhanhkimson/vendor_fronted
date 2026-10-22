export type GuestLine = {
  variant_id: string;
  qty: number;
  title: string;
  price_cents: number;
  image_url?: string | null;
};

const KEY = "bazaar.guestCart";

export function readGuestCart(): GuestLine[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || "[]") as GuestLine[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeGuestCart(lines: GuestLine[]) {
  localStorage.setItem(KEY, JSON.stringify(lines));
  window.dispatchEvent(new Event("bazaar-cart"));
}

export function addGuestLine(line: GuestLine) {
  const lines = readGuestCart();
  const existing = lines.find((item) => item.variant_id === line.variant_id);
  if (existing) existing.qty = Math.min(10, existing.qty + line.qty);
  else lines.push(line);
  writeGuestCart(lines);
}

export function clearGuestCart() {
  localStorage.removeItem(KEY);
  window.dispatchEvent(new Event("bazaar-cart"));
}
