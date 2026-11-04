"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { useSession } from "@/components/providers";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { browserApi, unwrap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type MenuItem = { href: string; label: string; group?: string; permission?: string };

const MENUS: Record<"account" | "seller" | "admin", MenuItem[]> = {
  account: [
    { href: "/account", label: "Overview" },
    { href: "/account/orders", label: "Orders" },
    { href: "/account/wishlist", label: "Wishlist" },
    { href: "/account/messages", label: "Messages" },
    { href: "/account/notifications", label: "Notifications" },
    { href: "/account/settings", label: "Settings" },
  ],
  seller: [
    { href: "/seller", label: "Overview" },
    { href: "/seller/products", label: "Products", group: "Catalogue" },
    { href: "/seller/inventory", label: "Inventory", group: "Catalogue" },
    { href: "/seller/orders", label: "Orders", group: "Orders" },
    { href: "/seller/promotions", label: "Promotions", group: "Growth" },
    { href: "/seller/payouts", label: "Payouts", group: "Money" },
    { href: "/seller/reports", label: "Reports", group: "Money" },
    { href: "/seller/storefront", label: "Storefront", group: "Shop" },
    { href: "/seller/messages", label: "Messages", group: "Shop" },
    { href: "/seller/reviews", label: "Reviews", group: "Shop" },
  ],
  admin: [
    { href: "/admin", label: "Overview" },
    { href: "/admin/vendors", label: "Vendors", group: "Queues", permission: "vendor:read" },
    { href: "/admin/listings", label: "Listings", group: "Queues", permission: "product:moderate" },
    { href: "/admin/disputes", label: "Disputes", group: "Queues", permission: "dispute:read" },
    { href: "/admin/payouts", label: "Payouts", group: "Queues", permission: "payout:read" },
    { href: "/admin/products", label: "Products", group: "Catalogue", permission: "product:read" },
    { href: "/admin/categories", label: "Categories", group: "Catalogue", permission: "category:read" },
    { href: "/admin/orders", label: "Orders", group: "Ops", permission: "order:read" },
    { href: "/admin/customers", label: "Customers", group: "Ops", permission: "customer:read" },
    { href: "/admin/reviews", label: "Reviews", group: "Ops", permission: "review:read" },
    { href: "/admin/coupons", label: "Coupons", group: "Ops", permission: "coupon:read" },
    { href: "/admin/commissions", label: "Commission", group: "Money", permission: "commission:read" },
    { href: "/admin/reports", label: "Reports", group: "Money", permission: "report:read" },
    { href: "/admin/roles", label: "Roles", group: "Governance", permission: "role:read" },
    { href: "/admin/audit", label: "Activity log", group: "Governance", permission: "audit:read" },
  ],
};

const AREA_LABEL = {
  account: "Account",
  seller: "Seller Dashboard",
  admin: "Admin Console",
} as const;

const COPY = {
  account: "Your orders, saved pieces, and messages with the shops.",
  seller: "This shop only. Another seller's orders and payouts stay invisible.",
  admin: "Platform operations. Sellers cannot open these screens.",
};

function badgeFor(area: keyof typeof MENUS, label: string, counts?: Record<string, number | string>) {
  if (!counts) return 0;
  const value = (key: string) => {
    const raw = counts[key];
    return typeof raw === "number" && raw > 0 ? raw : 0;
  };
  if (area === "seller") {
    if (label === "Orders") return value("open_orders");
    if (label === "Products") return value("pending_listings");
    if (label === "Inventory") return value("low_stock");
    if (label === "Payouts") return value("eligible_payouts");
    if (label === "Messages") return value("waiting_messages");
    if (label === "Reviews") return value("unread");
  }
  if (area === "account") {
    if (label === "Orders") return value("open_orders");
    if (label === "Notifications") return value("unread");
  }
  if (area === "admin") {
    if (label === "Orders") return value("open_orders");
    if (label === "Vendors") return value("vendors_to_review");
    if (label === "Listings") return value("listings_to_review");
    if (label === "Disputes") return value("open_disputes");
    if (label === "Payouts") return value("payouts_to_sign");
    if (label === "Reviews") return value("flagged_reviews");
  }
  return 0;
}

export function Area({ area, children }: { area: keyof typeof MENUS; children: React.ReactNode }) {
  const path = usePathname();
  const { me } = useSession();
  const { t } = useI18n();
  const summaryPath = area === "account" ? "/api/account/summary" : area === "seller" ? "/api/seller/summary" : "/api/admin/summary";
  const summary = useQuery({
    queryKey: ["summary", area],
    queryFn: () => unwrap(browserApi.GET(summaryPath)),
  });
  const counts = summary.data as Record<string, number | string> | undefined;
  const permissions = new Set(me?.permissions || []);
  const items = MENUS[area].filter((item) => !item.permission || permissions.has(item.permission));
  const overviewHref = area === "account" ? "/account" : area === "seller" ? "/seller" : "/admin";
  const where =
    area === "account" ? t.orientation.account : area === "seller" ? t.orientation.seller : t.orientation.admin;

  let lastGroup = "";

  return (
    <div className="wrap grid gap-8 py-8 md:grid-cols-[240px_1fr]">
      <aside className="space-y-4">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-secondary">{AREA_LABEL[area]}</p>
          <h2 className="serif text-3xl leading-tight">{me?.name}</h2>
          <p className="text-sm text-muted-foreground">{where}</p>
          {area === "seller" && me?.vendor ? (
            <>
              <p className="text-sm text-muted-foreground">{me.blurb || COPY.seller}</p>
              <p className="text-xs leading-relaxed text-muted-foreground">Shop: {me.vendor.name}</p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">{me?.blurb || COPY[area]}</p>
          )}
          <Button asChild variant="outline" size="sm">
            <Link href="/guide">{t.orientation.learnMore}</Link>
          </Button>
        </div>
        <Separator />
        <nav className="flex flex-col gap-1">
          {items.map((item) => {
            const showGroup = Boolean(item.group && item.group !== lastGroup);
            if (item.group) lastGroup = item.group;
            const badge = badgeFor(area, item.label, counts);
            const isActive = item.href === overviewHref ? path === item.href : path === item.href || path.startsWith(`${item.href}/`);
            return (
              <div key={item.href}>
                {showGroup ? <p className="mb-1 mt-3 px-3 text-[11px] uppercase tracking-wide text-muted-foreground">{item.group}</p> : null}
                <Button asChild variant={isActive ? "secondary" : "ghost"} className="h-auto w-full justify-between px-3 py-2 font-normal">
                  <Link href={item.href}>
                    <span>{item.label}</span>
                    {badge ? <Badge>{badge}</Badge> : null}
                  </Link>
                </Button>
              </div>
            );
          })}
        </nav>
      </aside>
      <div>{children}</div>
    </div>
  );
}

export function DoThis({
  text,
  actions = [],
}: {
  text: string;
  actions?: { href: string; label: string; primary?: boolean }[];
}) {
  return (
    <div className="panel space-y-4 p-5">
      <div>
        <p className="text-xs uppercase tracking-wide text-secondary">Do this now</p>
        <p className="mt-2 text-lg leading-snug">{text}</p>
      </div>
      {actions.length ? (
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <Button key={action.href + action.label} asChild variant={action.primary ? "default" : "outline"}>
              <Link href={action.href}>{action.label}</Link>
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
