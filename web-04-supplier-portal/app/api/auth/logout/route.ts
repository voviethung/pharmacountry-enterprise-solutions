import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { logoutFromFrappe } from "@/lib/frappeAuth";
import { getSession, destroySession, SESSION_COOKIE_NAME } from "@/lib/session";

export async function POST() {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  const session = getSession(token);
  if (session) {
    await logoutFromFrappe(session.frappeSid); // best-effort
    destroySession(token);
  }
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}
