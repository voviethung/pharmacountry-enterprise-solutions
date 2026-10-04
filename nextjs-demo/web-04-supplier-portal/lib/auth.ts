import { cookies } from "next/headers";
import { getLocale } from "next-intl/server";
import { redirect } from "@/i18n/navigation";
import { getSession, SESSION_COOKIE_NAME, type SupplierSession } from "./session";

export async function getCurrentSession(): Promise<SupplierSession | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  return getSession(token);
}

export async function requireSession(): Promise<SupplierSession> {
  const session = await getCurrentSession();
  if (session) return session;

  // next-intl's locale-aware redirect() needs the current request's locale explicitly (it has
  // no React hook context to infer it from here) — getLocale() reads it from the same
  // requestLocale context next-intl/plugin populates per-request, so this still lands on
  // /vi/login or /en/login correctly rather than an unprefixed /login.
  const locale = await getLocale();
  redirect({ href: "/login", locale });
  // Unreachable: redirect() always throws Next.js's internal NEXT_REDIRECT signal before
  // returning — this satisfies TypeScript's return-type checking for this function.
  throw new Error("unreachable");
}

export { SESSION_COOKIE_NAME };
