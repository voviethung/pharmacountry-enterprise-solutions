// WEB-03 login Route Handler — the ONLY place this app ever sends a username/password to Frappe.
//
// Flow: (1) real Frappe login via lib/frappeAuth.ts's native /api/method/login call, obtaining a
// real `sid`; (2) IMMEDIATELY use that `sid` to call `get_my_profile()` — this both confirms the
// login actually resolved to a real, provisioned dealer account (a valid Frappe login that is NOT
// linked to a Customer via User Permission is rejected here, not silently let through) and fetches
// the real Frappe CSRF token needed for this app's own later state-changing calls; (3) create our
// own opaque session (lib/session.ts) and hand the BROWSER only that opaque token, as an `httpOnly`
// cookie — the real `sid` never leaves this server process. See lib/session.ts and this app's
// README for the full authentication design and its disclosed limitations.
import { NextResponse } from "next/server";
import { loginToFrappe, FrappeLoginError } from "@/lib/frappeAuth";
import { getMyProfile, DealerApiError } from "@/lib/api";
import { createSession, SESSION_COOKIE_NAME } from "@/lib/session";

// Force dynamic rendering — calls the real Frappe backend and sets a session cookie; must never
// be cached/prerendered.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let username: string;
  let password: string;
  try {
    const body = await request.json();
    username = String(body.username || "");
    password = String(body.password || "");
  } catch {
    // Machine-readable code, not English prose — this Route Handler runs outside next-intl's
    // locale context, so the consuming client component (LoginForm.tsx) translates this code
    // via its own `errors.<code>` message key instead.
    return NextResponse.json({ error_code: "invalid_request_body" }, { status: 400 });
  }

  if (!username || !password) {
    return NextResponse.json({ error_code: "missing_credentials" }, { status: 400 });
  }

  try {
    const { sid } = await loginToFrappe(username, password);
    // Confirms this is a real, provisioned dealer login — not just any valid Frappe account.
    // dealer_portal_api.get_my_profile() throws PermissionError for a login with no Customer
    // User Permission (e.g. Administrator), which surfaces here as a DealerApiError.
    const profile = await getMyProfile(sid);

    const session = createSession({
      frappeSid: sid,
      csrfToken: profile.csrf_token,
      user: profile.user,
      customer: profile.customer,
      customerName: profile.customer_name,
      priceList: profile.price_list,
    });

    const response = NextResponse.json({
      ok: true,
      customerName: profile.customer_name,
    });
    response.cookies.set(SESSION_COOKIE_NAME, session.token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 2 * 60 * 60, // 2 hours, matches lib/session.ts's own TTL
    });
    return response;
  } catch (err) {
    if (err instanceof FrappeLoginError) {
      // FrappeLoginError's own message ("Invalid username or password." / "Could not reach the
      // backend.") is itself a hardcoded English string from lib/frappeAuth.ts — never passed
      // through raw. Both cases surface the same client-facing code; see this app's i18n
      // migration notes for why the two aren't distinguished here.
      return NextResponse.json({ error_code: "invalid_credentials" }, { status: 401 });
    }
    if (err instanceof DealerApiError) {
      return NextResponse.json({ error_code: "not_provisioned" }, { status: 403 });
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 500 });
  }
}
