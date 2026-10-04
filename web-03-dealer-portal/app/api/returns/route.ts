// WEB-03 — file a real return against one of THIS dealer's own Delivery Notes. The backend
// (dealer_portal_api.request_return) re-checks the delivery note's own customer against the
// session-resolved dealer before doing anything — this route never trusts the client-supplied
// delivery_note id on its own.
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { requestReturn, DealerApiError } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    // Machine-readable code, not English prose — see app/api/auth/login/route.ts's own comment
    // on why (this Route Handler runs outside next-intl's locale context).
    return NextResponse.json({ error_code: "not_logged_in" }, { status: 401 });
  }

  let deliveryNote: string;
  let qty: number | undefined;
  try {
    const body = await request.json();
    deliveryNote = String(body.delivery_note || "");
    qty = body.qty ? Number(body.qty) : undefined;
    if (!deliveryNote) throw new Error("missing");
  } catch {
    return NextResponse.json({ error_code: "validation_failed" }, { status: 400 });
  }

  try {
    const result = await requestReturn(session.frappeSid, session.csrfToken, deliveryNote, qty);
    return NextResponse.json({ ok: true, return: result });
  } catch (err) {
    if (err instanceof DealerApiError) {
      // Real, dynamic backend validation message (e.g. the delivery-note-ownership re-check) —
      // passed through unchanged, same rationale as app/api/orders/route.ts.
      return NextResponse.json({ error: err.message }, { status: 422 });
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 422 });
  }
}
