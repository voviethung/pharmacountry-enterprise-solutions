// WEB-07 — place a real order. The session cookie resolves which farm this is server-side
// (lib/auth.ts); the request body only ever carries `qty` — item and rate are server-side
// constants in farm_portal_api.py (there is exactly one real sellable product), so there is
// nothing here for a client to spoof.
import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth";
import { placeOrder, FarmApiError } from "@/lib/api";

// Force dynamic — reads the session cookie and calls the real Frappe backend on every request.
// See app/api/auth/login/route.ts for the full rationale.
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error_code: "not_logged_in" }, { status: 401 });
  }

  let qty: number;
  try {
    const body = await request.json();
    qty = Number(body.qty);
    if (!qty || qty <= 0) throw new Error("invalid qty");
  } catch {
    return NextResponse.json({ error_code: "invalid_quantity" }, { status: 400 });
  }

  try {
    const result = await placeOrder(session.frappeSid, session.csrfToken, qty);
    return NextResponse.json({ ok: true, order: result });
  } catch (err) {
    // A real ERPNext validation failure (e.g. the native credit-limit block) is genuine backend
    // DATA (like an order amount), not this app's own authored UI copy — it is passed through
    // verbatim in `detail` (never swallowed or replaced) alongside a stable, translatable
    // `error_code` the client uses for the surrounding label text.
    if (err instanceof FarmApiError) {
      return NextResponse.json(
        { error_code: "order_failed", detail: err.message },
        { status: 422 }
      );
    }
    return NextResponse.json({ error_code: "server_error" }, { status: 422 });
  }
}
