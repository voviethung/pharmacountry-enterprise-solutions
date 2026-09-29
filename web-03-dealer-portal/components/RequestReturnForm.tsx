"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { DeliverySummary } from "@/lib/api";

export default function RequestReturnForm({ deliveries }: { deliveries: DeliverySummary[] }) {
  const router = useRouter();
  const [deliveryNote, setDeliveryNote] = useState(deliveries[0]?.name ?? "");
  const [qty, setQty] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (deliveries.length === 0) {
    return <p className="text-sm text-slate-400">No deliveries available to return yet.</p>;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const res = await fetch("/api/returns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ delivery_note: deliveryNote, qty: Number(qty) }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not file the return.");
        setLoading(false);
        return;
      }
      setSuccess(`Return ${data.return.name} filed.`);
      router.refresh();
    } catch {
      setError("Could not reach the portal. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex items-center gap-2">
        <select
          value={deliveryNote}
          onChange={(e) => setDeliveryNote(e.target.value)}
          className="flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        >
          {deliveries.map((d) => (
            <option key={d.name} value={d.name}>
              {d.name} — {d.posting_date}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="1"
          step="1"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          aria-label="Quantity to return"
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
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-60"
      >
        {loading ? "Filing return…" : "File return"}
      </button>
    </form>
  );
}
