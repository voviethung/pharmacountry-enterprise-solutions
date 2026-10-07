"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import type { BillingCycle } from "@/lib/api";

type Status = "idle" | "submitting" | "error";

// Browser-side form backing the Hub's new /signup page. Submits to this SAME app's own
// /api/checkout route handler (never directly to Frappe — see that route's own top-of-file
// comment for why), which calls the already-built, already-PayPal-Sandbox-tested
// `paypal_billing.create_subscription_checkout()`. On success, redirects the browser straight
// to the real PayPal approval_url it returns — this component never itself provisions a
// tenant; that happens later, out of band, via paypal_billing.py's own webhook once the
// customer actually approves and pays.
export default function SignupForm({
  editionCode,
  billingCycle,
  locale,
}: {
  editionCode: string;
  billingCycle: BillingCycle;
  locale: string;
}) {
  const t = useTranslations("signup");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const companyName = String(formData.get("companyName") || "").trim();
    const customerEmail = String(formData.get("customerEmail") || "").trim();
    const tenantSite = String(formData.get("tenantSite") || "")
      .trim()
      .toLowerCase();

    if (
      !companyName ||
      !customerEmail ||
      !customerEmail.includes("@") ||
      !tenantSite ||
      !/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/.test(tenantSite)
    ) {
      setStatus("error");
      setErrorMessage(t("errorValidation"));
      return;
    }

    setStatus("submitting");
    setErrorMessage(null);

    // Absolute URLs (required by PayPal) pointing back at THIS SAME app — never a new domain —
    // with the current locale preserved, same locale-prefix convention as every other route in
    // this app (see i18n/routing.ts).
    const origin = window.location.origin;
    const returnUrl = `${origin}/${locale}/checkout/success`;
    const cancelUrl = `${origin}/${locale}/checkout/cancel`;

    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          editionCode,
          billingCycle,
          tenantSite,
          companyName,
          customerEmail,
          returnUrl,
          cancelUrl,
        }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok || !data?.approval_url) {
        throw new Error(data?.error || t("errorGeneric"));
      }
      window.location.href = data.approval_url;
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : t("errorGeneric"));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="companyName" className="block text-sm font-medium text-slate-900">
          {t("labelCompanyName")}
        </label>
        <input
          id="companyName"
          name="companyName"
          type="text"
          required
          maxLength={120}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>
      <div>
        <label htmlFor="customerEmail" className="block text-sm font-medium text-slate-900">
          {t("labelEmail")}
        </label>
        <input
          id="customerEmail"
          name="customerEmail"
          type="email"
          required
          maxLength={180}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>
      <div>
        <label htmlFor="tenantSite" className="block text-sm font-medium text-slate-900">
          {t("labelTenantSite")}
        </label>
        <div className="mt-1.5 flex items-center overflow-hidden rounded-md border border-slate-300 focus-within:border-[#158A57] focus-within:ring-1 focus-within:ring-[#158A57]">
          <input
            id="tenantSite"
            name="tenantSite"
            type="text"
            required
            maxLength={63}
            pattern="[a-z0-9]([a-z0-9-]*[a-z0-9])?"
            placeholder="acme"
            className="block w-full px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none"
          />
          <span className="shrink-0 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-500">
            .pharmacountry.vn
          </span>
        </div>
        <p className="mt-1.5 text-xs text-slate-500">{t("tenantSiteHint")}</p>
      </div>

      {status === "error" && errorMessage && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <button
        type="submit"
        disabled={status === "submitting"}
        className="inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0A4A2D] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "submitting" ? t("submitting") : t("submit")}
      </button>
    </form>
  );
}
