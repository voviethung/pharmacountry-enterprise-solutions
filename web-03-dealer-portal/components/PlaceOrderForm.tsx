"use client";

import { useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import type { CatalogItem } from "@/lib/api";

interface Line {
  item_code: string;
  qty: string;
}

const KNOWN_ERROR_CODES = new Set(["not_logged_in", "validation_failed", "server_error"]);

export default function PlaceOrderForm({ items }: { items: CatalogItem[] }) {
  const router = useRouter();
  const t = useTranslations("orders");
  const tErrors = useTranslations("errors");
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
        // Real ERPNext validation errors (e.g. the native credit-limit block) come through as
        // `data.error` verbatim — real, dynamic backend content, never hidden behind a generic
        // "something went wrong." This app's OWN hardcoded fallback strings come through as
        // `data.error_code` instead, translated client-side.
        if (typeof data.error === "string" && data.error) {
          setError(data.error);
        } else {
          const code = typeof data.error_code === "string" ? data.error_code : null;
          setError(tErrors(code && KNOWN_ERROR_CODES.has(code) ? code : "unknown"));
        }
        setLoading(false);
        return;
      }
      setSuccess(
        t("successMessage", {
          name: data.order.name,
          total: data.order.grand_total.toLocaleString("vi-VN"),
        })
      );
      setLines([{ item_code: items[0]?.item_code ?? "", qty: "1" }]);
      router.refresh();
    } catch {
      setError(tErrors("network"));
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
              {t("removeLine")}
            </button>
          )}
        </div>
      ))}
      <button type="button" onClick={addLine} className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
        {t("addLine")}
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
        {loading ? t("placingOrder") : t("placeOrderButton")}
      </button>
    </form>
  );
}
