// WEB-04 — submit a real Supplier Quotation against a real RFQ. The session cookie resolves which
// supplier this is server-side (lib/auth.ts); the request body only ever carries the RFQ name and
// this supplier's own quote terms, never a supplier id — there is nothing here for a client to
// spoof (mirrors WEB-03's app/api/orders/route.ts exactly).
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { submitQuotation, SupplierApiError } from "@/lib/api";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error: "Not logged in." }, { status: 401 });
  }

  let body: {
    rfq: string;
    rate: number;
    currency: string;
    conversion_rate: number;
    incoterm?: string;
    valid_till_days?: number;
    lead_time_days?: number;
    terms?: string;
  };
  try {
    body = await request.json();
    if (!body.rfq || !body.rate || !body.currency || !body.conversion_rate) throw new Error("missing fields");
  } catch {
    return NextResponse.json({ error: "RFQ, rate, currency and conversion rate are required." }, { status: 400 });
  }

  try {
    const result = await submitQuotation(session.frappeSid, session.csrfToken, body);
    return NextResponse.json({ ok: true, quotation: result });
  } catch (err) {
    const message = err instanceof SupplierApiError ? err.message : "Could not submit the quotation.";
    // A real ERPNext validation failure surfaces here with its own real message — never swallowed
    // or replaced with a generic success.
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
