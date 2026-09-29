// WEB-03 — per-request session resolution for Server Components / Route Handlers. Every
// protected page calls `requireSession()` before fetching any dealer data; nothing downstream of
// it ever sees a client-supplied "which dealer" value — only the resolved session's own
// `customer`, ultimately backed by the real Frappe session cookie this app holds server-side.
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getSession, SESSION_COOKIE_NAME, type DealerSession } from "./session";

export async function getCurrentSession(): Promise<DealerSession | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  return getSession(token);
}

/** Redirects to /login if there is no valid session — use at the top of every protected page. */
export async function requireSession(): Promise<DealerSession> {
  const session = await getCurrentSession();
  if (!session) redirect("/login");
  return session;
}

export { SESSION_COOKIE_NAME };
