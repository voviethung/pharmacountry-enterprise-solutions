// WEB-04 — submit a real Supplier Quotation against a real RFQ. The session cookie resolves which
// supplier this is server-side (lib/auth.ts); the request body only ever carries the RFQ name and
// this supplier's own quote terms, never a supplier id — there is nothing here for a client to
// spoof (mirrors WEB-03's app/api/orders/route.ts exactly).
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { submitQuotation, SupplierApiError } from "@/lib/api";

// Force dynamic — reads the session cookie and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error_code: "not_logged_in" }, { status: 401 });
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
    return NextResponse.json({ error_code: "invalid_request" }, { status: 400 });
  }

  try {
    const result = await submitQuotation(session.frappeSid, session.csrfToken, body);
    return NextResponse.json({ ok: true, quotation: result });
  } catch (err) {
    if (err instanceof SupplierApiError) {
      // A real ERPNext validation failure surfaces here with its own real message — never
      // swallowed or replaced with a generic success, and never translated (it's live backend
      // content, not this app's own static UI chrome).
      return NextResponse.json({ error: err.message }, { status: 422 });
    }
    return NextResponse.json({ error_code: "generic" }, { status: 422 });
  }
}
