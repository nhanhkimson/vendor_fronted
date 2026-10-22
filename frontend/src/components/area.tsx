"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { useSession } from "@/components/providers";
import { browserApi, unwrap } from "@/lib/api";

const MENUS = {
  account: [
    ["/account", "Overview"],
    ["/account/orders", "Orders"],
    ["/account/wishlist", "Wishlist"],
    ["/account/messages", "Messages"],
    ["/account/notifications", "Notifications"],
    ["/account/settings", "Settings"],
  ],
  seller: [
    ["/seller", "Overview"],
    ["/seller/products", "Products"],
    ["/seller/inventory", "Inventory"],
    ["/seller/orders", "Orders"],
    ["/seller/promotions", "Promotions"],
    ["/seller/payouts", "Payouts"],
    ["/seller/reports", "Reports"],
    ["/seller/storefront", "Storefront"],
    ["/seller/messages", "Messages"],
    ["/seller/reviews", "Reviews"],
  ],
  admin: [
    ["/admin", "Overview"],
    ["/admin/vendors", "Vendors"],
    ["/admin/products", "Products"],
    ["/admin/categories", "Categories"],
    ["/admin/orders", "Orders"],
    ["/admin/customers", "Customers"],
    ["/admin/reviews", "Reviews"],
    ["/admin/coupons", "Coupons"],
    ["/admin/disputes", "Disputes"],
    ["/admin/roles", "Roles"],
    ["/admin/audit", "Activity log"],
    ["/admin/commissions", "Commission"],
    ["/admin/payouts", "Payouts"],
    ["/admin/reports", "Reports"],
  ],
} as const;

const COPY = {
  account: "Your orders, saved pieces, and messages with the shops.",
  seller: "This shop only. Another seller's orders and payouts stay invisible.",
  admin: "Platform operations. Sellers cannot open these screens.",
};

export function Area({ area, children }: { area: keyof typeof MENUS; children: React.ReactNode }) {
  const path = usePathname();
  const { me } = useSession();
  const summaryPath = area === "account" ? "/api/account/summary" : area === "seller" ? "/api/seller/summary" : "/api/admin/summary";
  const summary = useQuery({
    queryKey: ["summary", area],
    queryFn: () => unwrap(browserApi.GET(summaryPath)),
  });
  const counts = summary.data as Record<string, number | string> | undefined;
  return (
    <div className="wrap grid gap-8 py-8 md:grid-cols-[220px_1fr]">
      <aside className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-[#b8572a]">{area}</p>
          <h2 className="serif text-3xl">{me?.name}</h2>
          <p className="text-sm text-[#6b6258]">{me?.blurb || COPY[area]}</p>
        </div>
        <nav className="flex flex-col gap-1">
          {MENUS[area].map(([href, label]) => (
            <Link key={href} href={href} className={`rounded-full px-3 py-2 text-sm ${path === href ? "bg-white" : "text-[#6b6258]"}`}>
              {label}
              {label === "Orders" && counts?.open_orders ? ` (${counts.open_orders})` : ""}
              {label === "Notifications" && counts?.unread ? ` (${counts.unread})` : ""}
            </Link>
          ))}
        </nav>
      </aside>
      <div>{children}</div>
    </div>
  );
}

export function DoThis({ text }: { text: string }) {
  return (
    <div className="panel p-5">
      <p className="text-xs uppercase tracking-wide text-[#b8572a]">Do this now</p>
      <p className="mt-2 text-lg">{text}</p>
    </div>
  );
}
