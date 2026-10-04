// WEB-07 — per-request session resolution for Server Components / Route Handlers. Every
// protected page calls `requireSession()` before fetching any farm data; nothing downstream of it
// ever sees a client-supplied "which farm" value — only the resolved session's own `customer`,
// ultimately backed by the real Frappe session cookie this app holds server-side.
import { cookies } from "next/headers";
import { getLocale } from "next-intl/server";
import { redirect } from "@/i18n/navigation";
import { getSession, SESSION_COOKIE_NAME, type FarmSession } from "./session";

export async function getCurrentSession(): Promise<FarmSession | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  return getSession(token);
}

/** Redirects to /login if there is no valid session — use at the top of every protected page. */
export async function requireSession(): Promise<FarmSession> {
  const session = await getCurrentSession();
  if (session) return session;
  // next-intl's react-server `redirect` (from @/i18n/navigation) requires an explicit `locale`
  // — unlike its client-side counterpart, a Server Component has no browser URL to infer it
  // from. `getLocale()` reads the current request's locale (set by middleware.ts) so this still
  // lands on /vi/login or /en/login correctly, with no caller changes needed.
  const locale = await getLocale();
  redirect({ href: "/login", locale });
  // Unreachable — `redirect()` always throws Next.js's internal redirect signal. This
  // satisfies TypeScript's control-flow analysis for this function's declared return type.
  throw new Error("unreachable");
}

export { SESSION_COOKIE_NAME };
