"use client";

import { useParams } from "next/navigation";

import { AdminWorkspace } from "@/components/workspaces";

export default function AdminPage() {
  const params = useParams<{ slug?: string[] }>();
  return <AdminWorkspace slug={params.slug} />;
}
