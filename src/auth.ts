import NextAuth, { type DefaultSession } from "next-auth"
import GitHub from "next-auth/providers/github"
import {
  parseGitHubAdminAllowlist,
  resolveGitHubRole,
} from "@/lib/github-admin-allowlist"

declare module "next-auth" {
  interface Session {
    user: {
      role: string;
    } & DefaultSession["user"]
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
    })
  ],
  callbacks: {
    jwt({ token, user, profile }) {
      if (user) {
        // Fail-closed SSO: only GitHub identities on
        // AUTH_GITHUB_ADMIN_ALLOWLIST receive the admin role; every other
        // authenticated user signs in as a non-admin ("public") user.
        // Existing sessions keep the role issued at sign-in until they
        // re-authenticate.
        token.role = resolveGitHubRole(
          profile,
          parseGitHubAdminAllowlist(process.env.AUTH_GITHUB_ADMIN_ALLOWLIST)
        );
      }
      return token
    },
    session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as string;
      }
      return session;
    }
  }
})
