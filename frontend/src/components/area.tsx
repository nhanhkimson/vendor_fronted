"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  ClipboardCheck,
  LayoutDashboard,
  Menu,
  Package,
  Settings,
  Shield,
  Store,
  Tag,
  Truck,
  Wallet,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { useSession } from "@/components/providers";
import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { browserApi, unwrap } from "@/lib/api";
import { shopLabel } from "@/lib/labels";
import { staffLabel } from "@/lib/roles";

type AreaId = "account" | "seller" | "admin";
type MenuItem = { href: string; label: string; group?: string; permission?: string; icon: LucideIcon };

const MENUS: Record<AreaId, MenuItem[]> = {
  account: [
    { href: "/account", label: "Overview", icon: LayoutDashboard },
    { href: "/account/orders", label: "Orders", icon: Package },
    { href: "/account/settings", label: "Settings", icon: Settings },
  ],
  seller: [
    { href: "/seller", label: "Overview", icon: LayoutDashboard },
    { href: "/seller/products", label: "Products", icon: Package },
    { href: "/seller/orders", label: "Orders", icon: Truck },
    { href: "/seller/promotions", label: "Discounts", icon: Tag },
    { href: "/seller/storefront", label: "Shop page", icon: Store },
    { href: "/seller/payouts", label: "Payouts", icon: Wallet },
  ],
  admin: [
    { href: "/admin", label: "Overview", icon: LayoutDashboard },
    { href: "/admin/vendors", label: "Shops", permission: "vendor:read", icon: Store },
    { href: "/admin/listings", label: "Publish", permission: "product:moderate", icon: ClipboardCheck },
    { href: "/admin/disputes", label: "Disputes", permission: "dispute:read", icon: AlertTriangle },
    { href: "/admin/reports", label: "Growth", permission: "report:read", icon: BarChart3 },
    { href: "/admin/roles", label: "Permissions", permission: "role:update", icon: Shield },
  ],
};

const AREA_META: Record<AreaId, { label: string; home: string; shop: string }> = {
  account: { label: "Your orders", home: "/account", shop: "Back to shop" },
  seller: { label: "Seller Dashboard", home: "/seller", shop: "View marketplace" },
  admin: { label: "Staff Console", home: "/admin", shop: "View marketplace" },
};

function badgeFor(area: AreaId, label: string, counts?: Record<string, number | string>) {
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
    if (label === "Shops") return value("vendors_to_review");
    if (label === "Publish") return value("listings_to_review");
    if (label === "Disputes") return value("open_disputes");
    if (label === "Payouts") return value("payouts_to_sign");
    if (label === "Reviews") return value("flagged_reviews");
  }
  return 0;
}

function NavList({
  area,
  items,
  counts,
  onNavigate,
}: {
  area: AreaId;
  items: MenuItem[];
  counts?: Record<string, number | string>;
  onNavigate?: () => void;
}) {
  const path = usePathname();
  const overviewHref = AREA_META[area].home;
  let lastGroup = "";
  return (
    <nav className="flex flex-col gap-0.5 px-2 pb-4">
      {items.map((item) => {
        const showGroup = Boolean(item.group && item.group !== lastGroup);
        if (item.group) lastGroup = item.group;
        const badge = badgeFor(area, item.label, counts);
        const isActive = item.href === overviewHref ? path === item.href : path === item.href || path.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <div key={item.href}>
            {showGroup ? <p className="mb-1 mt-4 px-3 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">{item.group}</p> : null}
            <Button asChild variant={isActive ? "secondary" : "ghost"} className="h-9 w-full justify-between px-3 font-normal">
              <Link href={item.href} onClick={onNavigate}>
                <span className="flex items-center gap-2.5">
                  <Icon className="size-4 opacity-70" />
                  {item.label}
                </span>
                {badge ? <Badge>{badge}</Badge> : null}
              </Link>
            </Button>
          </div>
        );
      })}
    </nav>
  );
}

function areaTitle(area: AreaId, me: ReturnType<typeof useSession>["me"]) {
  if (area === "admin") return staffLabel(me);
  return AREA_META[area].label;
}

function SidebarBrand({ area }: { area: AreaId }) {
  const { me } = useSession();
  return (
    <div className="space-y-3 border-b border-border px-5 py-5">
      <Link href="/" className="serif text-2xl leading-none">
        Bazaar
      </Link>
      <div>
        <p className="text-[11px] uppercase tracking-[0.16em] text-secondary">{areaTitle(area, me)}</p>
        <p className="mt-1 truncate text-sm font-medium">{me?.name}</p>
        {area === "seller" && me?.vendor ? (
          <p className="truncate text-xs text-muted-foreground">{shopLabel(me.vendor.id, me.vendor.name)}</p>
        ) : null}
        {area === "admin" ? <p className="truncate text-xs text-muted-foreground">{me?.roles.map((role) => role.name).join(" · ")}</p> : null}
      </div>
    </div>
  );
}

export function Area({ area, children }: { area: AreaId; children: React.ReactNode }) {
  const { me, refresh } = useSession();
  const router = useRouter();
  const summaryPath = area === "account" ? "/api/account/summary" : area === "seller" ? "/api/seller/summary" : "/api/admin/summary";
  const summary = useQuery({
    queryKey: ["summary", area],
    queryFn: () => unwrap(browserApi.GET(summaryPath)),
  });
  const counts = summary.data as Record<string, number | string> | undefined;
  const permissions = new Set(me?.permissions || []);
  const items = MENUS[area].filter((item) => !item.permission || permissions.has(item.permission));

  async function signOut() {
    await unwrap(browserApi.POST("/api/auth/logout"));
    await refresh();
    router.push("/");
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        <SidebarBrand area={area} />
        <ScrollArea className="flex-1">
          <NavList area={area} items={items} counts={counts} />
        </ScrollArea>
        <div className="border-t border-border p-3">
          <Button asChild variant="outline" size="sm" className="w-full justify-start">
            <Link href="/">{AREA_META[area].shop}</Link>
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur md:px-6">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon-sm" className="md:hidden" aria-label="Open menu">
                <Menu />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetHeader className="sr-only">
                <SheetTitle>{AREA_META[area].label}</SheetTitle>
              </SheetHeader>
              <SidebarBrand area={area} />
              <NavList area={area} items={items} counts={counts} />
            </SheetContent>
          </Sheet>
          <p className="serif text-lg md:hidden">Bazaar</p>
          <p className="hidden text-sm text-muted-foreground md:block">{areaTitle(area, me)}</p>
          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
            <Avatar size="sm">
              {me?.avatar_url ? <AvatarImage src={me.avatar_url} alt="" /> : null}
              <AvatarFallback>{me?.name?.slice(0, 1) || "?"}</AvatarFallback>
            </Avatar>
            <Button variant="ghost" size="sm" onClick={() => void signOut()}>
              Sign out
            </Button>
          </div>
        </header>
        <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8">{children}</div>
      </div>
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
    <div className="panel space-y-5 p-6">
      <div className="max-w-2xl">
        <p className="text-[11px] uppercase tracking-[0.16em] text-secondary">Do this now</p>
        <p className="mt-2 text-xl leading-snug">{text}</p>
      </div>
      {actions.length ? (
        <div className="dash-actions">
          {actions.map((action) => (
            <Button key={action.href + action.label} asChild size="lg" variant={action.primary ? "default" : "outline"}>
              <Link href={action.href}>{action.label}</Link>
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
