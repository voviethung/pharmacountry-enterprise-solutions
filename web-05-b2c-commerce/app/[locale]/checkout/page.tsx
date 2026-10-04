"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter, Link } from "@/i18n/navigation";
import { useCart } from "@/components/CartProvider";
import { formatVnd, type OrderConfirmation } from "@/lib/api";

const CONFIRMATION_STORAGE_KEY = "web05-last-order";

// Error codes the /api/checkout Route Handler can return (see app/api/checkout/route.ts) —
// anything else falls back to the generic message below.
const KNOWN_ERROR_CODES = new Set([
  "malformed_body",
  "missing_fields",
  "backend_rejected",
  "checkout_failed",
]);

export default function CheckoutPage() {
  const t = useTranslations("checkout");
  const tErrors = useTranslations("errors");
  const { items, totalPrice, clearCart } = useCart();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900">{t("emptyTitle")}</h1>
        <Link href="/shop" className="mt-4 inline-block text-emerald-700 underline">
          {t("goToShop")}
        </Link>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: items.map((i) => ({ item_code: i.item_code, qty: i.qty })),
          contact: {
            full_name: fullName,
            phone,
            email: email || undefined,
            address_line1: addressLine1,
            city,
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        const code = typeof data?.error_code === "string" ? data.error_code : undefined;
        setError(tErrors(code && KNOWN_ERROR_CODES.has(code) ? code : "generic"));
        setSubmitting(false);
        return;
      }
      const order = data as OrderConfirmation;
      try {
        window.sessionStorage.setItem(CONFIRMATION_STORAGE_KEY, JSON.stringify(order));
      } catch {
        // sessionStorage unavailable — confirmation page will just show a generic message.
      }
      clearCart();
      router.push("/confirmation");
    } catch {
      setError(tErrors("network"));
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-1 text-sm text-slate-600">{t("subtitle")}</p>

      <div className="mt-6 rounded-lg bg-slate-50 p-4 text-sm">
        <p className="font-semibold text-slate-800">{t("orderSummary")}</p>
        <ul className="mt-2 space-y-1">
          {items.map((i) => (
            <li key={i.item_code} className="flex justify-between">
              <span>
                {i.item_name} × {i.qty}
              </span>
              <span>{formatVnd(i.price * i.qty)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>{t("estimatedTotal")}</span>
          <span>{formatVnd(totalPrice)}</span>
        </div>
        <p className="mt-2 text-xs text-slate-500">{t("estimateNote")}</p>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelFullName")}</label>
          <input
            required
            maxLength={120}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelPhone")}</label>
          <input
            required
            type="tel"
            maxLength={20}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="e.g. 0912345678"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
          <p className="mt-1 text-xs text-slate-500">{t("phoneHint")}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelEmail")}</label>
          <input
            type="email"
            maxLength={200}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelAddress")}</label>
          <input
            required
            maxLength={200}
            value={addressLine1}
            onChange={(e) => setAddressLine1(e.target.value)}
            placeholder={t("addressPlaceholder")}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("labelCity")}</label>
          <input
            required
            maxLength={100}
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>

        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
          {t.rich("paymentNote", { strong: (chunks) => <strong>{chunks}</strong> })}
        </div>

        {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-emerald-600 px-6 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? t("submitting") : t("placeOrder")}
        </button>
      </form>
    </div>
  );
}
