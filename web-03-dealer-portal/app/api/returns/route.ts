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
    return NextResponse.json({ error: "Not logged in." }, { status: 401 });
  }

  let deliveryNote: string;
  let qty: number | undefined;
  try {
    const body = await request.json();
    deliveryNote = String(body.delivery_note || "");
    qty = body.qty ? Number(body.qty) : undefined;
    if (!deliveryNote) throw new Error("missing");
  } catch {
    return NextResponse.json({ error: "A delivery note is required." }, { status: 400 });
  }

  try {
    const result = await requestReturn(session.frappeSid, session.csrfToken, deliveryNote, qty);
    return NextResponse.json({ ok: true, return: result });
  } catch (err) {
    const message = err instanceof DealerApiError ? err.message : "Could not file the return.";
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
