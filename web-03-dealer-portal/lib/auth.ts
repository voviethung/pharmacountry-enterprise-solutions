// WEB-03 — per-request session resolution for Server Components / Route Handlers. Every
// protected page calls `requireSession()` before fetching any dealer data; nothing downstream of
// it ever sees a client-supplied "which dealer" value — only the resolved session's own
// `customer`, ultimately backed by the real Frappe session cookie this app holds server-side.
import { cookies } from "next/headers";
import { getLocale } from "next-intl/server";
import { redirect } from "@/i18n/navigation";
import { getSession, SESSION_COOKIE_NAME, type DealerSession } from "./session";

export async function getCurrentSession(): Promise<DealerSession | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  return getSession(token);
}

/** Redirects to /login if there is no valid session — use at the top of every protected page. */
export async function requireSession(): Promise<DealerSession> {
  const session = await getCurrentSession();
  if (!session) {
    // next-intl's react-server `redirect()` (unlike its client-side counterpart) requires the
    // target locale explicitly rather than inferring it — resolved here from the current
    // request's own locale context, so this still lands on /vi/login or /en/login correctly.
    const locale = await getLocale();
    return redirect({ href: "/login", locale });
  }
  return session;
}

export { SESSION_COOKIE_NAME };
