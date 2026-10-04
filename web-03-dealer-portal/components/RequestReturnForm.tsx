"use client";

import { useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import type { DeliverySummary } from "@/lib/api";

const KNOWN_ERROR_CODES = new Set(["not_logged_in", "validation_failed", "server_error"]);

export default function RequestReturnForm({ deliveries }: { deliveries: DeliverySummary[] }) {
  const router = useRouter();
  const t = useTranslations("returns");
  const tErrors = useTranslations("errors");
  const [deliveryNote, setDeliveryNote] = useState(deliveries[0]?.name ?? "");
  const [qty, setQty] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (deliveries.length === 0) {
    return <p className="text-sm text-slate-400">{t("noDeliveries")}</p>;
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
        // Real backend validation errors come through as `data.error` verbatim (dynamic
        // content); this app's own hardcoded fallback strings come through as `data.error_code`
        // instead, translated client-side — see app/api/returns/route.ts.
        if (typeof data.error === "string" && data.error) {
          setError(data.error);
        } else {
          const code = typeof data.error_code === "string" ? data.error_code : null;
          setError(tErrors(code && KNOWN_ERROR_CODES.has(code) ? code : "unknown"));
        }
        setLoading(false);
        return;
      }
      setSuccess(t("successMessage", { name: data.return.name }));
      router.refresh();
    } catch {
      setError(tErrors("network"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={deliveryNote}
          onChange={(e) => setDeliveryNote(e.target.value)}
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
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
          aria-label={t("quantityAriaLabel")}
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
        {loading ? t("filingReturn") : t("fileReturnButton")}
      </button>
    </form>
  );
}
