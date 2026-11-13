/**
 * Proxy access decision for stakeholder-portal#123.
 *
 * Pure function (no Next.js imports) so the role-aware allow/deny behavior
 * is unit-testable without booting NextAuth; `src/proxy.ts` maps the
 * decision to a response.
 *
 * - `/admin/*` and `/dashboard` require an authorized admin session: the
 *   session role must be exactly `"admin"` (see
 *   `src/lib/github-admin-allowlist.ts`). A session alone is insufficient.
 * - Anonymous users are redirected to sign-in; signed-in non-admin users
 *   are forbidden (a redirect would loop: they are already signed in).
 * - Everything else (including `/api/auth/*` and `/api/admin/*`, which have
 *   their own auth) is allowed through unchanged.
 */
export type ProxyAccessDecision = "allow" | "signin" | "forbidden";

export interface ProxySessionLike {
  user?: { role?: unknown } | null;
}

export function decideProxyAccess(
  pathname: string,
  session: ProxySessionLike | null | undefined
): ProxyAccessDecision {
  if (pathname.startsWith("/api/auth")) return "allow";

  const requiresAdmin =
    pathname.startsWith("/admin") || pathname.startsWith("/dashboard");
  if (!requiresAdmin) return "allow";
  if (!session || !session.user) return "signin";
  return session.user.role === "admin" ? "allow" : "forbidden";
}
