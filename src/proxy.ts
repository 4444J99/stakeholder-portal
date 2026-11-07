/**
 * Next.js request proxy.
 * - /admin/* and /dashboard require an authorized admin NextAuth session
 *   (GitHub SSO). A session alone is not enough: the session role must be
 *   "admin" (see AUTH_GITHUB_ADMIN_ALLOWLIST in
 *   src/lib/github-admin-allowlist.ts). Anonymous users are redirected to
 *   sign-in; signed-in non-admin users get 403 (a redirect would loop:
 *   they are already signed in).
 * - /api/cron/* is intentionally left out of matchers — it uses CRON_SECRET (M2M).
 * - /api/admin/* is intentionally left out — it accepts both session + ADMIN_API_TOKEN.
 */
import { auth } from "@/auth";
import { decideProxyAccess } from "@/lib/proxy-auth";
import { NextResponse } from "next/server";

export default auth(function proxy(req) {
  const { pathname } = req.nextUrl;

  switch (decideProxyAccess(pathname, req.auth)) {
    case "allow":
      return NextResponse.next();
    case "forbidden":
      return new NextResponse("Forbidden", { status: 403 });
    case "signin": {
      const loginUrl = new URL("/api/auth/signin", req.url);
      loginUrl.searchParams.set("callbackUrl", req.url);
      return NextResponse.redirect(loginUrl);
    }
  }
});

export const config = {
  matcher: [
    "/admin/:path*",
    "/dashboard/:path*",
    // Exclude static assets, Next internals, cron, and API token routes from the proxy
    "/((?!_next/static|_next/image|favicon.ico|api/cron|api/auth).*)",
  ],
};
