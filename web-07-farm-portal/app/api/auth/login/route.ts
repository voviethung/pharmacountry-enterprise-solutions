// WEB-07 login Route Handler — the ONLY place this app ever sends a username/password to Frappe.
//
// Flow: (1) real Frappe login via lib/frappeAuth.ts's native /api/method/login call, obtaining a
// real `sid`; (2) IMMEDIATELY use that `sid` to call `get_my_profile()` — this both confirms the
// login actually resolved to a real, provisioned farm account (a valid Frappe login that is NOT
// linked to a Customer via User Permission is rejected here, not silently let through) and fetches
// the real Frappe CSRF token needed for this app's own later state-changing calls; (3) create our
// own opaque session (lib/session.ts) and hand the BROWSER only that opaque token, as an `httpOnly`
// cookie — the real `sid` never leaves this server process. See lib/session.ts and this app's
// README for the full authentication design (reused verbatim from WEB-03/04) and its disclosed
// limitations.
import { NextResponse } from "next/server";
import { loginToFrappe, FrappeLoginError } from "@/lib/frappeAuth";
import { getMyProfile, FarmApiError } from "@/lib/api";
import { createSession, SESSION_COOKIE_NAME } from "@/lib/session";

// Force dynamic — this Route Handler calls the real Frappe backend and sets a session cookie on
// every request. POST handlers are never statically optimized by Next.js anyway, but this is
// made explicit for consistency with every other backend-dependent route in this app.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let username: string;
  let password: string;
  try {
    const body = await request.json();
    username = String(body.username || "");
    password = String(body.password || "");
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  if (!username || !password) {
    return NextResponse.json({ error: "Username and password are required." }, { status: 400 });
  }

  try {
    const { sid } = await loginToFrappe(username, password);
    // Confirms this is a real, provisioned farm login — not just any valid Frappe account.
    // farm_portal_api.get_my_profile() throws PermissionError for a login with no Customer User
    // Permission (e.g. Administrator), which surfaces here as a FarmApiError.
    const profile = await getMyProfile(sid);

    const session = createSession({
      frappeSid: sid,
      csrfToken: profile.csrf_token,
      user: profile.user,
      customer: profile.customer,
      customerName: profile.customer_name,
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
      return NextResponse.json({ error: err.message }, { status: 401 });
    }
    if (err instanceof FarmApiError) {
      return NextResponse.json(
        { error: "This account is not a provisioned farm login." },
        { status: 403 }
      );
    }
    return NextResponse.json({ error: "Login failed. Please try again." }, { status: 500 });
  }
}
