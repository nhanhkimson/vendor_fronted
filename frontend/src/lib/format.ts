export function money(cents: number | null | undefined): string {
  const value = (cents ?? 0) / 100;
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function rate(bps: number | null | undefined): string {
  return `${((bps ?? 0) / 100).toFixed(2)}%`;
}

export function when(value: string | null | undefined): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function titleCase(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ");
}
