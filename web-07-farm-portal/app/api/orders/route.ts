// WEB-07 — place a real order. The session cookie resolves which farm this is server-side
// (lib/auth.ts); the request body only ever carries `qty` — item and rate are server-side
// constants in farm_portal_api.py (there is exactly one real sellable product), so there is
// nothing here for a client to spoof.
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { placeOrder, FarmApiError } from "@/lib/api";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error: "Not logged in." }, { status: 401 });
  }

  let qty: number;
  try {
    const body = await request.json();
    qty = Number(body.qty);
    if (!qty || qty <= 0) throw new Error("invalid qty");
  } catch {
    return NextResponse.json({ error: "A valid quantity is required." }, { status: 400 });
  }

  try {
    const result = await placeOrder(session.frappeSid, session.csrfToken, qty);
    return NextResponse.json({ ok: true, order: result });
  } catch (err) {
    const message = err instanceof FarmApiError ? err.message : "Could not place the order.";
    // A real ERPNext validation failure (e.g. the native credit-limit block) surfaces here with
    // its own real message — never swallowed or replaced with a generic success.
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
