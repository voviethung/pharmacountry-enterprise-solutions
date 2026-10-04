import { NextResponse } from "next/server";
import { loginToFrappe, FrappeLoginError } from "@/lib/frappeAuth";
import { getMyProfile, SupplierApiError } from "@/lib/api";
import { createSession, SESSION_COOKIE_NAME } from "@/lib/session";

// Force dynamic — calls the real Frappe backend and mints a session on every request; a
// POST-only Route Handler is never statically cached by Next.js anyway, but this is explicit
// defense-in-depth (same convention as every page in this app).
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let username: string;
  let password: string;
  try {
    const body = await request.json();
    username = String(body.username || "");
    password = String(body.password || "");
  } catch {
    return NextResponse.json({ error_code: "invalid_request" }, { status: 400 });
  }

  if (!username || !password) {
    return NextResponse.json({ error_code: "invalid_request" }, { status: 400 });
  }

  try {
    const { sid } = await loginToFrappe(username, password);
    // Confirms this is a real, provisioned supplier login — get_my_profile() throws
    // PermissionError for a login with no Supplier User Permission (e.g. Administrator).
    const profile = await getMyProfile(sid);

    const session = createSession({
      frappeSid: sid,
      csrfToken: profile.csrf_token,
      user: profile.user,
      supplier: profile.supplier,
      supplierName: profile.supplier_name,
    });

    const response = NextResponse.json({ ok: true, supplierName: profile.supplier_name });
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
      // Two distinct FrappeLoginError cases (see lib/frappeAuth.ts): bad credentials vs. a
      // network failure reaching the backend. Mapped to distinct machine-readable codes here —
      // same HTTP status as before, only the body's error representation changes (English prose
      // -> a stable code the client translates via messages/*.json).
      const code = err.message.includes("reach") ? "server_error" : "invalid_credentials";
      return NextResponse.json({ error_code: code }, { status: 401 });
    }
    if (err instanceof SupplierApiError) {
      return NextResponse.json({ error_code: "not_provisioned" }, { status: 403 });
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 500 });
  }
}
