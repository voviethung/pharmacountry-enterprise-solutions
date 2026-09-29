import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getSession, destroySession, SESSION_COOKIE_NAME } from "@/lib/session";
import { logoutFromFrappe } from "@/lib/frappeAuth";

export async function POST() {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  const session = getSession(token);
  if (session) {
    // Best-effort — this app's own session is destroyed below regardless of whether Frappe's own
    // logout call succeeds.
    await logoutFromFrappe(session.frappeSid);
    destroySession(token);
  }
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}
