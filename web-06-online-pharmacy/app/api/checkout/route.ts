import { NextRequest, NextResponse } from "next/server";
import { placePharmacyOrder, PharmacyApiError, type CheckoutContact, type CheckoutLine } from "@/lib/api";

// Server-side proxy for the ONE write this whole app performs. The browser never talks to Frappe
// directly (same "backend URL/response never visible in client-side network calls" discipline
// every prior WEB-0X app follows) — it POSTs here, and THIS Route Handler forwards to the real
// guest-writable `place_pharmacy_order` endpoint using the Host-header workaround in lib/api.ts. No
// price/rate/batch is ever read from the request body here either; only item_code/qty and contact
// fields are forwarded, exactly mirroring the real backend's own accepted shape.
//
// Force dynamic — this is a live guest-checkout write against the real Frappe backend and must
// never be evaluated/cached at build time.
//
// Responses carry a stable, machine-readable `error_code` (never English prose) so the bilingual
// checkout page can render a properly localized (vi/en) message via next-intl. `detail` carries
// the raw backend message (which may itself be in English, since it comes straight from Frappe)
// purely for developer debugging/logging — the UI must never display it directly.
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  let body: { items?: CheckoutLine[]; contact?: CheckoutContact };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error_code: "malformed_body" }, { status: 400 });
  }

  const items = Array.isArray(body.items)
    ? body.items.map((row) => ({ item_code: String(row.item_code), qty: Number(row.qty) }))
    : [];
  const contact = body.contact;

  if (!items.length || !contact) {
    return NextResponse.json({ error_code: "missing_fields" }, { status: 400 });
  }

  try {
    const order = await placePharmacyOrder(items, contact);
    return NextResponse.json(order);
  } catch (err) {
    if (err instanceof PharmacyApiError) {
      const status = err.status || 500;
      return NextResponse.json(
        { error_code: status >= 400 && status < 500 ? "order_rejected" : "server_error", detail: err.message },
        { status }
      );
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 500 });
  }
}
