"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

// Stable machine-readable codes app/api/quotations/route.ts may return. Any code not in this
// set (or no code at all — see the real ERPNext-message passthrough below) falls back to the
// generic translated message.
const KNOWN_ERROR_CODES = new Set(["invalid_request", "not_logged_in", "generic"]);

export default function SubmitQuotationForm({ rfq }: { rfq: string }) {
  const router = useRouter();
  const t = useTranslations("quotationForm");
  const tErrors = useTranslations("errors");
  const [rate, setRate] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [conversionRate, setConversionRate] = useState("25000");
  const [incoterm, setIncoterm] = useState("CIF");
  const [leadTimeDays, setLeadTimeDays] = useState("21");
  const [validTillDays, setValidTillDays] = useState("30");
  const [terms, setTerms] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const res = await fetch("/api/quotations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rfq,
          rate: Number(rate),
          currency,
          conversion_rate: Number(conversionRate),
          incoterm,
          lead_time_days: Number(leadTimeDays),
          valid_till_days: Number(validTillDays),
          terms,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (typeof data.error === "string") {
          // Real ERPNext validation error, surfaced verbatim — this is live backend content,
          // never hidden behind a generic "something went wrong" and never translated (it isn't
          // this app's own UI chrome).
          setError(data.error);
        } else {
          const code = typeof data.error_code === "string" && KNOWN_ERROR_CODES.has(data.error_code)
            ? data.error_code
            : "generic";
          setError(tErrors(code));
        }
        setLoading(false);
        return;
      }
      setSuccess(t("success", { name: data.quotation.name }));
      router.refresh();
    } catch {
      setError(tErrors("network"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <Field label={t("rate")}>
        <input
          type="number"
          step="0.0001"
          required
          value={rate}
          onChange={(e) => setRate(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <Field label={t("currency")}>
        <input
          value={currency}
          onChange={(e) => setCurrency(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <Field label={t("conversionRate")}>
        <input
          type="number"
          step="0.01"
          value={conversionRate}
          onChange={(e) => setConversionRate(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <Field label={t("incoterm")}>
        <input
          value={incoterm}
          onChange={(e) => setIncoterm(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <Field label={t("leadTimeDays")}>
        <input
          type="number"
          value={leadTimeDays}
          onChange={(e) => setLeadTimeDays(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <Field label={t("validDays")}>
        <input
          type="number"
          value={validTillDays}
          onChange={(e) => setValidTillDays(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </Field>
      <div className="sm:col-span-3">
        <Field label={t("terms")}>
          <textarea
            value={terms}
            onChange={(e) => setTerms(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          />
        </Field>
      </div>

      {error && (
        <p className="sm:col-span-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      {success && (
        <p className="sm:col-span-3 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p>
      )}

      <div className="sm:col-span-3">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-600 disabled:opacity-60"
        >
          {loading ? t("submitting") : t("submit")}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-slate-600">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
