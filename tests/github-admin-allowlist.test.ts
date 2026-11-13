import { describe, expect, it } from "vitest";
import {
  isGitHubAdmin,
  parseGitHubAdminAllowlist,
  resolveGitHubRole,
} from "@/lib/github-admin-allowlist";

describe("parseGitHubAdminAllowlist", () => {
  it("treats missing or empty policy as unconfigured and valid (nobody admin)", () => {
    for (const raw of [undefined, null, "", "   ", ",,,"]) {
      const allowlist = parseGitHubAdminAllowlist(raw);
      expect(allowlist.configured).toBe(false);
      expect(allowlist.valid).toBe(true);
      expect(allowlist.logins.size).toBe(0);
      expect(allowlist.ids.size).toBe(0);
      expect(isGitHubAdmin({ login: "anyone" }, allowlist)).toBe(false);
    }
  });

  it("normalizes logins (case and whitespace) and dedupes", () => {
    const allowlist = parseGitHubAdminAllowlist(" Alice ,BOB,alice,");
    expect(allowlist.configured).toBe(true);
    expect(allowlist.valid).toBe(true);
    expect([...allowlist.logins].sort()).toEqual(["alice", "bob"]);
  });

  it("accepts numeric user IDs as id:<digits>", () => {
    const allowlist = parseGitHubAdminAllowlist("id:12345678, ID:42");
    expect(allowlist.valid).toBe(true);
    expect([...allowlist.ids].sort()).toEqual(["12345678", "42"]);
  });

  it("invalidates the whole policy on any malformed entry (fail closed)", () => {
    for (const raw of [
      "alice, not a login!",
      "alice, id:abc",
      "alice, id:",
      "alice, -bad-",
      "alice, a--b",
      "alice, id:12x",
      `alice, ${"a".repeat(40)}`,
    ]) {
      const allowlist = parseGitHubAdminAllowlist(raw);
      expect(allowlist.valid).toBe(false);
      expect(allowlist.logins.size).toBe(0);
      expect(allowlist.ids.size).toBe(0);
      expect(isGitHubAdmin({ login: "alice" }, allowlist)).toBe(false);
    }
  });
});

describe("isGitHubAdmin", () => {
  it("matches a listed login case-insensitively", () => {
    const allowlist = parseGitHubAdminAllowlist("Alice");
    expect(isGitHubAdmin({ login: "alice" }, allowlist)).toBe(true);
    expect(isGitHubAdmin({ login: "  ALICE " }, allowlist)).toBe(true);
    expect(isGitHubAdmin({ login: "alice2" }, allowlist)).toBe(false);
  });

  it("matches a listed numeric user ID as number or string", () => {
    const allowlist = parseGitHubAdminAllowlist("id:12345678");
    expect(isGitHubAdmin({ id: 12345678 }, allowlist)).toBe(true);
    expect(isGitHubAdmin({ id: "12345678" }, allowlist)).toBe(true);
    expect(isGitHubAdmin({ id: 87654321 }, allowlist)).toBe(false);
  });

  it("does not confuse a bare numeric login with a numeric ID", () => {
    // Bare entries are logins; only id:<digits> entries match profile.id.
    const allowlist = parseGitHubAdminAllowlist("12345678");
    expect(isGitHubAdmin({ login: "12345678" }, allowlist)).toBe(true);
    expect(isGitHubAdmin({ id: 12345678 }, allowlist)).toBe(false);
  });

  it("rejects missing identity and unlisted identities", () => {
    const allowlist = parseGitHubAdminAllowlist("alice, id:1");
    expect(isGitHubAdmin(null, allowlist)).toBe(false);
    expect(isGitHubAdmin(undefined, allowlist)).toBe(false);
    expect(isGitHubAdmin({}, allowlist)).toBe(false);
    expect(isGitHubAdmin({ login: "mallory", id: 999 }, allowlist)).toBe(false);
  });

  it("never grants admin from a forged client-side role field", () => {
    const allowlist = parseGitHubAdminAllowlist("alice");
    // Only login/id are consulted; a caller-supplied role is ignored.
    const forged: Record<string, unknown> = { login: "mallory", role: "admin" };
    expect(isGitHubAdmin(forged, allowlist)).toBe(false);
  });
});

describe("resolveGitHubRole", () => {
  it("returns admin for allowlisted identities and public otherwise", () => {
    const allowlist = parseGitHubAdminAllowlist("alice, id:7");
    expect(resolveGitHubRole({ login: "alice" }, allowlist)).toBe("admin");
    expect(resolveGitHubRole({ id: 7 }, allowlist)).toBe("admin");
    expect(resolveGitHubRole({ login: "mallory" }, allowlist)).toBe("public");
    expect(resolveGitHubRole(null, allowlist)).toBe("public");
  });

  it("returns public for everyone when the policy is missing or malformed", () => {
    expect(resolveGitHubRole({ login: "alice" })).toBe("public");
    const malformed = parseGitHubAdminAllowlist("alice, ???");
    expect(resolveGitHubRole({ login: "alice" }, malformed)).toBe("public");
  });
});
