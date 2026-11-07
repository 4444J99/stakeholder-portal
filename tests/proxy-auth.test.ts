import { describe, expect, it } from "vitest";
import { decideProxyAccess } from "@/lib/proxy-auth";

const admin = { user: { role: "admin" } };
const nonAdmin = { user: { role: "public" } };

describe("decideProxyAccess", () => {
  it("redirects anonymous users to sign-in for protected routes", () => {
    expect(decideProxyAccess("/admin", null)).toBe("signin");
    expect(decideProxyAccess("/admin/intel", null)).toBe("signin");
    expect(decideProxyAccess("/admin/login", null)).toBe("signin");
    expect(decideProxyAccess("/dashboard", undefined)).toBe("signin");
    expect(decideProxyAccess("/dashboard", { user: null })).toBe("signin");
  });

  it("allows admin sessions to protected routes", () => {
    expect(decideProxyAccess("/admin", admin)).toBe("allow");
    expect(decideProxyAccess("/admin/intel", admin)).toBe("allow");
    expect(decideProxyAccess("/dashboard", admin)).toBe("allow");
  });

  it("forbids signed-in non-admin sessions on protected routes", () => {
    expect(decideProxyAccess("/admin", nonAdmin)).toBe("forbidden");
    expect(decideProxyAccess("/admin/intel", nonAdmin)).toBe("forbidden");
    expect(decideProxyAccess("/admin/login", nonAdmin)).toBe("forbidden");
    expect(decideProxyAccess("/dashboard", nonAdmin)).toBe("forbidden");
    expect(decideProxyAccess("/dashboard", { user: { role: "stakeholder" } })).toBe(
      "forbidden"
    );
    // Role comparison is exact: a differently-cased role is not admin.
    expect(decideProxyAccess("/admin", { user: { role: "Admin" } })).toBe(
      "forbidden"
    );
  });

  it("allows the auth callback flow and public routes through unchanged", () => {
    expect(decideProxyAccess("/api/auth/callback/github", null)).toBe("allow");
    expect(decideProxyAccess("/api/auth/signin", null)).toBe("allow");
    expect(decideProxyAccess("/", null)).toBe("allow");
    expect(decideProxyAccess("/", nonAdmin)).toBe("allow");
    expect(decideProxyAccess("/repos/some-repo", null)).toBe("allow");
  });

  it("leaves API admin routes to their own auth (session + token)", () => {
    expect(decideProxyAccess("/api/admin/intel", null)).toBe("allow");
    expect(decideProxyAccess("/api/admin/session", null)).toBe("allow");
  });
});
