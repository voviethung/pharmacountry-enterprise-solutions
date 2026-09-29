"use client";

import { useState } from "react";
import { formatVnd, type OrderStatus } from "@/lib/api";

export default function TrackOrderPage() {
  const [orderToken, setOrderToken] = useState("");
  const [phone, setPhone] = useState("");
  const [result, setResult] = useState<OrderStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const params = new URLSearchParams({ order_token: orderToken.trim(), phone: phone.trim() });
      const res = await fetch(`/api/track-order?${params.toString()}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Order not found. Check your order reference and phone number.");
        return;
      }
      setResult(data as OrderStatus);
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Track Your Order</h1>
      <p className="mt-1 text-sm text-slate-600">
        Enter the order reference you received at checkout AND the phone number you checked out
        with. Both are required — we never look up an order by reference alone, to protect your
        privacy.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Order reference</label>
          <input
            required
            value={orderToken}
            onChange={(e) => setOrderToken(e.target.value)}
            placeholder="e.g. WEB06-XXXXXXXXXX"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Phone number used at checkout</label>
          <input
            required
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-sky-600 px-6 py-3 font-semibold text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? "Looking up…" : "Track Order"}
        </button>
      </form>

      {error && <p className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</p>}

      {result && (
        <div className="mt-6 rounded-lg border border-slate-200 p-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-sky-700">{result.status}</p>
          <p className="mt-1 text-sm text-slate-600">
            Ordered by {result.contact_display} on {result.transaction_date} — {result.store}
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            {result.items.map((i) => (
              <li key={i.item_code} className="flex items-start justify-between gap-4">
                <span>
                  {i.item_name} × {i.qty}
                  <span className="mt-0.5 block text-xs text-slate-500">
                    Batch {i.batch_no}
                    {i.batch_expiry_date ? ` — exp. ${i.batch_expiry_date}` : ""}
                  </span>
                </span>
                <span className="shrink-0">{formatVnd(i.amount)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-semibold">
            <span>Total ({result.payment_method})</span>
            <span>{formatVnd(result.grand_total)}</span>
          </div>
          <p className="mt-2 whitespace-pre-line text-xs text-slate-500">
            Delivery address: {result.address_display?.replace(/<br\s*\/?>/g, "\n")}
          </p>
        </div>
      )}
    </div>
  );
}
