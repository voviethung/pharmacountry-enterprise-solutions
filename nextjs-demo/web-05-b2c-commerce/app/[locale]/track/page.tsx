"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { formatVnd, type OrderStatus } from "@/lib/api";

// Error codes the /api/track-order Route Handler can return (see
// app/api/track-order/route.ts) — anything else falls back to the generic message below.
const KNOWN_ERROR_CODES = new Set(["missing_tracking_fields", "backend_rejected", "lookup_failed"]);

export default function TrackOrderPage() {
  const t = useTranslations("track");
  const tErrors = useTranslations("errors");
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
        const code = typeof data?.error_code === "string" ? data.error_code : undefined;
        setError(tErrors(code && KNOWN_ERROR_CODES.has(code) ? code : "generic"));
        return;
      }
      setResult(data as OrderStatus);
    } catch {
      setError(tErrors("network"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-1 text-sm text-slate-600">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelOrderRef")}</label>
          <input
            required
            value={orderToken}
            onChange={(e) => setOrderToken(e.target.value)}
            placeholder={t("orderRefPlaceholder")}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelPhone")}</label>
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
          className="w-full rounded-md bg-emerald-600 px-6 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? t("loading") : t("submit")}
        </button>
      </form>

      {error && <p className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</p>}

      {result && (
        <div className="mt-6 rounded-lg border border-slate-200 p-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">{result.status}</p>
          <p className="mt-1 text-sm text-slate-600">
            {t("orderedByLine", { name: result.contact_display, date: result.transaction_date })}
          </p>
          <ul className="mt-3 space-y-1 text-sm">
            {result.items.map((i) => (
              <li key={i.item_code} className="flex justify-between">
                <span>
                  {i.item_name} × {i.qty}
                </span>
                <span>{formatVnd(i.amount)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-semibold">
            <span>{t("totalLabel", { method: result.payment_method })}</span>
            <span>{formatVnd(result.grand_total)}</span>
          </div>
          <p className="mt-2 text-xs text-slate-500 whitespace-pre-line">
            {t("deliveryAddressLabel")} {result.address_display?.replace(/<br\s*\/?>/g, "\n")}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {t("deliveryEstimate", { date: result.delivery_date })}
          </p>
        </div>
      )}
    </div>
  );
}
