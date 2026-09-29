// WEB-03 — place a real order. The session cookie resolves which dealer this is server-side
// (lib/auth.ts); the request body only ever carries item_code/qty, never a customer/dealer id —
// there is nothing here for a client to spoof.
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { placeOrder, DealerApiError } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error: "Not logged in." }, { status: 401 });
  }

  let items: { item_code: string; qty: number }[];
  try {
    const body = await request.json();
    items = body.items;
    if (!Array.isArray(items) || items.length === 0) throw new Error("empty");
  } catch {
    return NextResponse.json({ error: "At least one order line is required." }, { status: 400 });
  }

  try {
    const result = await placeOrder(session.frappeSid, session.csrfToken, items);
    return NextResponse.json({ ok: true, order: result });
  } catch (err) {
    const message = err instanceof DealerApiError ? err.message : "Could not place the order.";
    // A real ERPNext validation failure (e.g. the native credit-limit block) surfaces here with
    // its own real message — never swallowed or replaced with a generic success.
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
