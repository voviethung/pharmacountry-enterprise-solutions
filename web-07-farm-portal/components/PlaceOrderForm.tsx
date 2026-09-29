"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CatalogItem } from "@/lib/api";

export default function PlaceOrderForm({ item }: { item: CatalogItem | undefined }) {
  const router = useRouter();
  const [qty, setQty] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qty: Number(qty) }),
      });
      const data = await res.json();
      if (!res.ok) {
        // Real ERPNext validation errors (e.g. the native credit-limit block) surface here
        // verbatim — never hidden behind a generic "something went wrong."
        setError(data.error || "Could not place the order.");
        setLoading(false);
        return;
      }
      setSuccess(`Order ${data.order.name} placed — total ${data.order.grand_total.toLocaleString("vi-VN")} VND.`);
      setQty("1");
      router.refresh();
    } catch {
      setError("Could not reach the portal. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (!item) {
    return <p className="text-sm text-slate-500">No orderable product is available right now.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
        <p className="font-medium text-slate-900">{item.item_name}</p>
        <p className="mt-1 text-xs text-slate-500">
          Indicated for: {item.target_species || "—"} · Withdrawal period:{" "}
          {item.withdrawal_period_days != null ? `${item.withdrawal_period_days} days` : "—"}
        </p>
        <p className="mt-1 text-sm text-slate-700">
          {item.price.toLocaleString("vi-VN")} {item.currency} / {item.stock_uom}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor="qty" className="text-sm text-slate-600">
          Quantity ({item.stock_uom})
        </label>
        <input
          id="qty"
          type="number"
          min="1"
          step="1"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </div>

      {error && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      {success && <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p>}

      <button
        type="submit"
        disabled={loading}
        className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-60"
      >
        {loading ? "Placing order…" : "Place order"}
      </button>
    </form>
  );
}
