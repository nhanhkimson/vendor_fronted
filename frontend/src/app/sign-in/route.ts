import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

function safePath(value: string, fallback: string) {
  if (value.startsWith("/") && !value.startsWith("//") && !value.includes("\\")) return value;
  return fallback;
}

function browserOrigin(request: Request) {
  const forwarded = request.headers.get("x-forwarded-host");
  const host = forwarded || request.headers.get("host") || "";
  if (host && !host.startsWith("0.0.0.0")) {
    const proto = request.headers.get("x-forwarded-proto") || "http";
    return `${proto}://${host}`;
  }
  const origin = request.headers.get("origin");
  if (origin) return origin;
  return new URL(request.url).origin;
}

export async function POST(request: Request) {
  const form = await request.formData();
  const email = String(form.get("email") || "").trim().toLowerCase();
  const password = String(form.get("password") || "");
  const next = String(form.get("next") || "");
  const failed = new URL("/login", browserOrigin(request));
  failed.searchParams.set("error", "1");
  if (next) failed.searchParams.set("next", safePath(next, ""));

  const upstream = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json", "X-Bazaar-Client": "web" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });
  if (!upstream.ok) return NextResponse.redirect(failed, 303);

  const me = (await upstream.json()) as { home?: string };
  const destination = new URL(safePath(next, me.home || "/account"), browserOrigin(request));
  const response = NextResponse.redirect(destination, 303);
  const cookies = upstream.headers.getSetCookie?.() ?? [];
  for (const cookie of cookies) response.headers.append("set-cookie", cookie);
  return response;
}
