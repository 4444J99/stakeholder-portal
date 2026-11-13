/**
 * GitHub SSO admin allowlist (stakeholder-portal#123).
 *
 * GitHub SSO authorization is fail-closed: only identities listed in
 * `AUTH_GITHUB_ADMIN_ALLOWLIST` receive the admin role. Every other
 * authenticated GitHub user signs in as a non-admin ("public") user and
 * cannot reach `/admin/*` or `/dashboard` (see `src/lib/proxy-auth.ts`).
 *
 * Policy format (comma-separated, one env var):
 * - a GitHub login, e.g. `some-login` — matched case-insensitively after
 *   trimming; or
 * - a numeric GitHub user ID, e.g. `id:12345678` — matched against the
 *   immutable `profile.id` from the OAuth profile.
 *
 * Missing, empty, or malformed configuration grants admin to nobody. A
 * single malformed entry invalidates the whole policy rather than being
 * silently skipped, so a typo can never silently widen access. The
 * allowlist is never logged.
 */
import type { Role } from "./security";

export interface GitHubIdentity {
  login?: unknown;
  id?: unknown;
}

export interface GitHubAdminAllowlist {
  /** Normalized (lowercase) GitHub logins granted admin. */
  logins: ReadonlySet<string>;
  /** GitHub numeric user IDs (as strings, no leading zeros) granted admin. */
  ids: ReadonlySet<string>;
  /** False when the raw policy was malformed; the policy then grants admin to nobody. */
  valid: boolean;
  /** True when a non-empty policy was supplied. */
  configured: boolean;
}

const EMPTY_ALLOWLIST: GitHubAdminAllowlist = {
  logins: new Set<string>(),
  ids: new Set<string>(),
  valid: true,
  configured: false,
};

// GitHub login: 1-39 chars, alphanumerics and single hyphens, never a
// leading/trailing hyphen and never two hyphens in a row.
const LOGIN_PATTERN = /^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,38}$/;
const ID_PATTERN = /^id:[0-9]+$/;

function normalizeId(raw: string): string {
  return String(Number.parseInt(raw, 10));
}

export function parseGitHubAdminAllowlist(
  raw: string | undefined | null
): GitHubAdminAllowlist {
  if (raw === undefined || raw === null) return EMPTY_ALLOWLIST;
  const entries = raw
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
  if (entries.length === 0) return EMPTY_ALLOWLIST;

  const logins = new Set<string>();
  const ids = new Set<string>();
  for (const entry of entries) {
    const normalized = entry.toLowerCase();
    if (ID_PATTERN.test(normalized)) {
      ids.add(normalizeId(normalized.slice("id:".length)));
      continue;
    }
    if (LOGIN_PATTERN.test(normalized)) {
      logins.add(normalized);
      continue;
    }
    // Malformed entry: fail closed — the whole policy grants admin to nobody.
    return {
      logins: new Set<string>(),
      ids: new Set<string>(),
      valid: false,
      configured: true,
    };
  }
  return { logins, ids, valid: true, configured: true };
}

function normalizeLogin(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.trim().toLowerCase();
  return normalized.length > 0 ? normalized : null;
}

function normalizeIdentityId(value: unknown): string | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(Math.trunc(value));
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (/^[0-9]+$/.test(trimmed)) return normalizeId(trimmed);
  }
  return null;
}

export function isGitHubAdmin(
  identity: GitHubIdentity | null | undefined,
  allowlist: GitHubAdminAllowlist = parseGitHubAdminAllowlist(
    process.env.AUTH_GITHUB_ADMIN_ALLOWLIST
  )
): boolean {
  if (!allowlist.valid) return false;
  if (!identity) return false;
  const login = normalizeLogin(identity.login);
  if (login !== null && allowlist.logins.has(login)) return true;
  const id = normalizeIdentityId(identity.id);
  if (id !== null && allowlist.ids.has(id)) return true;
  return false;
}

/** SSO role for a GitHub identity: "admin" when allowlisted, "public" otherwise. */
export function resolveGitHubRole(
  identity: GitHubIdentity | null | undefined,
  allowlist: GitHubAdminAllowlist = parseGitHubAdminAllowlist(
    process.env.AUTH_GITHUB_ADMIN_ALLOWLIST
  )
): Role {
  return isGitHubAdmin(identity, allowlist) ? "admin" : "public";
}
