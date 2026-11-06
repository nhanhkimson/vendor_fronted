"use client";

import { usePathname } from "next/navigation";

import { SiteFooter, SiteHeader } from "@/components/site";

function isWorkspace(path: string) {
  return path.startsWith("/admin") || path.startsWith("/seller") || path.startsWith("/account");
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "/";
  if (isWorkspace(path)) {
    return <main className="min-h-full">{children}</main>;
  }
  return (
    <>
      <SiteHeader />
      <main>{children}</main>
      <SiteFooter />
    </>
  );
}
