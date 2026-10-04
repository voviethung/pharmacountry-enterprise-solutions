// WEB-03 — place a real order. The session cookie resolves which dealer this is server-side
// (lib/auth.ts); the request body only ever carries item_code/qty, never a customer/dealer id —
// there is nothing here for a client to spoof.
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { placeOrder, DealerApiError } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    // Machine-readable code, not English prose — see app/api/auth/login/route.ts's own comment
    // on why (this Route Handler runs outside next-intl's locale context).
    return NextResponse.json({ error_code: "not_logged_in" }, { status: 401 });
  }

  let items: { item_code: string; qty: number }[];
  try {
    const body = await request.json();
    items = body.items;
    if (!Array.isArray(items) || items.length === 0) throw new Error("empty");
  } catch {
    return NextResponse.json({ error_code: "validation_failed" }, { status: 400 });
  }

  try {
    const result = await placeOrder(session.frappeSid, session.csrfToken, items);
    return NextResponse.json({ ok: true, order: result });
  } catch (err) {
    if (err instanceof DealerApiError) {
      // A real ERPNext validation failure (e.g. the native credit-limit block) surfaces here
      // with its own real, dynamic message straight from the live backend — this is real data
      // from Frappe, not a hardcoded UI string, so it is passed through unchanged rather than
      // mapped to a translated error code (never swallowed or replaced with a generic message).
      return NextResponse.json({ error: err.message }, { status: 422 });
    }
    // Only this generic fallback (e.g. a network failure reaching the backend) is this app's own
    // hardcoded string, so only this one becomes a translatable error_code.
    return NextResponse.json({ error_code: "server_error" }, { status: 422 });
  }
}
