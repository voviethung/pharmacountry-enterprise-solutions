import { NextRequest, NextResponse } from "next/server";
import { getOrderStatus, B2cApiError } from "@/lib/api";

// Force dynamic — this looks up live order data from the real Frappe backend per-request
// (keyed on query params) and must never be cached or treated as static output.
export const dynamic = "force-dynamic";

// Server-side proxy for the order-status lookup. Forwards ONLY order_token + phone — both are
// required by the real backend (see b2c_commerce_api.py's own docstring for why neither alone is
// enough), and this route does nothing to weaken that: it's a thin passthrough, not a second place
// that could accidentally allow a token-only or phone-only lookup.
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const orderToken = searchParams.get("order_token") || "";
  const phone = searchParams.get("phone") || "";

  if (!orderToken || !phone) {
    return NextResponse.json({ error: "Both an order reference and a phone number are required." }, { status: 400 });
  }

  try {
    const status = await getOrderStatus(orderToken, phone);
    return NextResponse.json(status);
  } catch (err) {
    if (err instanceof B2cApiError) {
      return NextResponse.json({ error: err.message }, { status: err.status || 500 });
    }
    return NextResponse.json({ error: "Could not look up this order." }, { status: 500 });
  }
}
