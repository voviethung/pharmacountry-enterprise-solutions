import { NextRequest, NextResponse } from "next/server";
import { getOrderStatus, B2cApiError } from "@/lib/api";

// Force dynamic — this looks up live order data from the real Frappe backend per-request
// (keyed on query params) and must never be cached or treated as static output.
export const dynamic = "force-dynamic";

// Server-side proxy for the order-status lookup. Forwards ONLY order_token + phone — both are
// required by the real backend (see b2c_commerce_api.py's own docstring for why neither alone is
// enough), and this route does nothing to weaken that: it's a thin passthrough, not a second place
// that could accidentally allow a token-only or phone-only lookup.
// Error responses carry a stable, machine-readable `error_code` rather than English prose — this
// Route Handler runs outside next-intl's locale context, so it cannot itself produce a localized
// message. The consuming client component (app/[locale]/track/page.tsx) maps each code to a
// translated string via useTranslations("errors"), with a generic fallback for any code it
// doesn't recognize.
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const orderToken = searchParams.get("order_token") || "";
  const phone = searchParams.get("phone") || "";

  if (!orderToken || !phone) {
    return NextResponse.json({ error_code: "missing_tracking_fields" }, { status: 400 });
  }

  try {
    const status = await getOrderStatus(orderToken, phone);
    return NextResponse.json(status);
  } catch (err) {
    if (err instanceof B2cApiError) {
      // Same reasoning as api/checkout/route.ts: the real backend's own message is arbitrary
      // English prose we can't safely show untranslated — log it, return a stable code.
      console.error("[api/track-order] backend rejected lookup:", err.message);
      return NextResponse.json({ error_code: "backend_rejected" }, { status: err.status || 500 });
    }
    return NextResponse.json({ error_code: "lookup_failed" }, { status: 500 });
  }
}
