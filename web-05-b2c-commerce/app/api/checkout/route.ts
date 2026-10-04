import { NextRequest, NextResponse } from "next/server";
import { placeWebOrder, B2cApiError, type CheckoutContact, type CheckoutLine } from "@/lib/api";

// Force dynamic — this is a guest-writable order-creation endpoint hitting the real Frappe
// backend on every call; it must never be cached or treated as static output.
export const dynamic = "force-dynamic";

// Server-side proxy for the ONE write this whole app performs. The browser never talks to Frappe
// directly (same "backend URL/response never visible in client-side network calls" discipline
// every prior WEB-0X app follows) — it POSTs here, and THIS Route Handler forwards to the real
// guest-writable `place_web_order` endpoint using the Host-header workaround in lib/api.ts. No
// price/rate is ever read from the request body here either; only item_code/qty and contact fields
// are forwarded, exactly mirroring the real backend's own accepted shape.
// Error responses carry a stable, machine-readable `error_code` rather than English prose — this
// Route Handler runs outside next-intl's locale context (it's a plain Next.js API route, not a
// page under app/[locale]), so it cannot itself produce a localized message for a Vietnamese or
// English visitor. The consuming client component (app/[locale]/checkout/page.tsx) maps each
// code to a translated string via useTranslations("errors"), with a generic fallback for any
// code it doesn't recognize.
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
    const order = await placeWebOrder(items, contact);
    return NextResponse.json(order);
  } catch (err) {
    if (err instanceof B2cApiError) {
      // The real backend's own message (Frappe validation prose, e.g. stock/contact issues) is
      // arbitrary English text we can't safely show untranslated on a bilingual storefront.
      // Log it server-side for diagnostics and return a stable generic code to the client.
      console.error("[api/checkout] backend rejected order:", err.message);
      return NextResponse.json({ error_code: "backend_rejected" }, { status: err.status || 500 });
    }
    return NextResponse.json({ error_code: "checkout_failed" }, { status: 500 });
  }
}
