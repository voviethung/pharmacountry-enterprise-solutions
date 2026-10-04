import { NextRequest, NextResponse } from "next/server";
import { getPharmacyOrderStatus, PharmacyApiError } from "@/lib/api";

// Server-side proxy for the order-status lookup. Forwards ONLY order_token + phone — both are
// required by the real backend (see online_pharmacy_api.py's own docstring for why neither alone is
// enough), and this route does nothing to weaken that: it's a thin passthrough, not a second place
// that could accidentally allow a token-only or phone-only lookup.
//
// Force dynamic — this reads live order data from the real Frappe backend per request and must
// never be evaluated/cached at build time.
//
// Responses carry a stable, machine-readable `error_code` (never English prose) so the bilingual
// Track Order page can render a properly localized (vi/en) message via next-intl. `detail` carries
// the raw backend message purely for developer debugging/logging — the UI must never display it.
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const orderToken = searchParams.get("order_token") || "";
  const phone = searchParams.get("phone") || "";

  if (!orderToken || !phone) {
    return NextResponse.json({ error_code: "missing_fields" }, { status: 400 });
  }

  try {
    const status = await getPharmacyOrderStatus(orderToken, phone);
    return NextResponse.json(status);
  } catch (err) {
    if (err instanceof PharmacyApiError) {
      const status = err.status || 500;
      return NextResponse.json(
        { error_code: status === 404 ? "order_not_found" : "server_error", detail: err.message },
        { status }
      );
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 500 });
  }
}
