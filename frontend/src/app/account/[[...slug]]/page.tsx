"use client";

import { useParams } from "next/navigation";

import { AccountWorkspace } from "@/components/workspaces";

export default function AccountPage() {
  const params = useParams<{ slug?: string[] }>();
  return <AccountWorkspace slug={params.slug} />;
}
