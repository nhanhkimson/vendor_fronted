import { jwtVerify } from "jose";
import { NextResponse, type NextRequest } from "next/server";

const SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "dev-only-secret-change-me-before-any-real-deployment",
);

function homeFor(roles: string[]) {
  if (roles.some((role) => role === "super_admin" || role === "admin" || role === "support")) return "/admin";
  if (roles.includes("vendor")) return "/seller";
  return "/account";
}

export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const token = request.cookies.get("bazaar_session")?.value;
  let roles: string[] = [];
  if (token) {
    try {
      const { payload } = await jwtVerify(token, SECRET);
      roles = Array.isArray(payload.roles) ? payload.roles.filter((role): role is string => typeof role === "string") : [];
    } catch {
      roles = [];
    }
  }
  const signedIn = roles.length > 0;
  const destination = homeFor(roles);
  const needsAccount = path.startsWith("/account");
  const needsSeller = path.startsWith("/seller");
  const needsAdmin = path.startsWith("/admin");
  if ((needsAccount || needsSeller || needsAdmin) && !signedIn) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", path);
    return NextResponse.redirect(login);
  }
  const staff = roles.some((role) => role === "super_admin" || role === "admin" || role === "support");
  const vendor = roles.includes("vendor");
  const customer = roles.includes("customer");
  const notifications = path.startsWith("/account/notifications");
  if (needsAdmin && !staff) return NextResponse.redirect(new URL(destination, request.url));
  if (needsSeller && !vendor) return NextResponse.redirect(new URL(destination, request.url));
  if (needsAccount && !customer && !notifications) return NextResponse.redirect(new URL(destination, request.url));
  return NextResponse.next();
}

export const config = {
  matcher: ["/account", "/account/:path*", "/seller", "/seller/:path*", "/admin", "/admin/:path*"],
};
