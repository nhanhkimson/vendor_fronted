"use client";

import { useParams } from "next/navigation";

import { SellerWorkspace } from "@/components/workspaces";

export default function SellerPage() {
  const params = useParams<{ slug?: string[] }>();
  return <SellerWorkspace slug={params.slug} />;
}
