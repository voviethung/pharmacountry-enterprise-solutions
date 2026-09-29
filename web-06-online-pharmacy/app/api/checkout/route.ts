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
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  let body: { items?: CheckoutLine[]; contact?: CheckoutContact };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Malformed request body." }, { status: 400 });
  }

  const items = Array.isArray(body.items)
    ? body.items.map((row) => ({ item_code: String(row.item_code), qty: Number(row.qty) }))
    : [];
  const contact = body.contact;

  if (!items.length || !contact) {
    return NextResponse.json({ error: "Cart items and contact information are required." }, { status: 400 });
  }

  try {
    const order = await placePharmacyOrder(items, contact);
    return NextResponse.json(order);
  } catch (err) {
    if (err instanceof PharmacyApiError) {
      return NextResponse.json({ error: err.message }, { status: err.status || 500 });
    }
    return NextResponse.json({ error: "Checkout failed. Please try again." }, { status: 500 });
  }
}
