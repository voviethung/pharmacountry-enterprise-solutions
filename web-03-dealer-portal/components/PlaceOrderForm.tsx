"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CatalogItem } from "@/lib/api";

interface Line {
  item_code: string;
  qty: string;
}

export default function PlaceOrderForm({ items }: { items: CatalogItem[] }) {
  const router = useRouter();
  const [lines, setLines] = useState<Line[]>([{ item_code: items[0]?.item_code ?? "", qty: "1" }]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateLine(index: number, patch: Partial<Line>) {
    setLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  }

  function addLine() {
    setLines((prev) => [...prev, { item_code: items[0]?.item_code ?? "", qty: "1" }]);
  }

  function removeLine(index: number) {
    setLines((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: lines.map((l) => ({ item_code: l.item_code, qty: Number(l.qty) })),
        }),
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
      setLines([{ item_code: items[0]?.item_code ?? "", qty: "1" }]);
      router.refresh();
    } catch {
      setError("Could not reach the portal. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {lines.map((line, index) => (
        <div key={index} className="flex items-center gap-2">
          <select
            value={line.item_code}
            onChange={(e) => updateLine(index, { item_code: e.target.value })}
            className="flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          >
            {items.map((item) => (
              <option key={item.item_code} value={item.item_code}>
                {item.item_name}
              </option>
            ))}
          </select>
          <input
            type="number"
            min="1"
            step="1"
            value={line.qty}
            onChange={(e) => updateLine(index, { qty: e.target.value })}
            className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          />
          {lines.length > 1 && (
            <button
              type="button"
              onClick={() => removeLine(index)}
              className="text-sm text-slate-400 hover:text-red-600"
            >
              Remove
            </button>
          )}
        </div>
      ))}
      <button type="button" onClick={addLine} className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
        + Add another item
      </button>

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
        {loading ? "Placing order…" : "Place order"}
      </button>
    </form>
  );
}
