"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { formatVnd, type OrderConfirmation } from "@/lib/api";

const CONFIRMATION_STORAGE_KEY = "web06-last-order";

export default function ConfirmationPage() {
  const t = useTranslations("confirmation");
  const [order, setOrder] = useState<OrderConfirmation | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    // One-time client-only read of sessionStorage (only exists in the browser, so this can't run
    // during SSR/static generation) — the canonical, narrow exception to the "don't setState in an
    // effect" guideline for reading browser-only storage right after mount.
    try {
      const raw = window.sessionStorage.getItem(CONFIRMATION_STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (raw) setOrder(JSON.parse(raw));
    } catch {
      // sessionStorage unavailable — fall through to the "no order" state below.
    }
    setLoaded(true);
  }, []);

  if (!loaded) return null;

  if (!order) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900">{t("noOrderTitle")}</h1>
        <p className="mt-2 text-slate-600">{t("noOrderBody")}</p>
        <div className="mt-6 flex justify-center gap-4">
          <Link href="/shop" className="text-sky-700 underline">
            {t("goToShop")}
          </Link>
          <Link href="/track" className="text-sky-700 underline">
            {t("trackOrder")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <div className="rounded-lg border border-sky-200 bg-sky-50 p-6 text-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-sky-700">{t("orderPlacedBadge")}</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">{t("thankYou")}</h1>
        <p className="mt-2 text-slate-700">
          {t("orderRefIntro")}
          <br />
          <span className="mt-1 inline-block rounded bg-white px-3 py-1 font-mono text-lg font-bold text-sky-800">
            {order.order_token}
          </span>
        </p>
        <p className="mt-3 text-sm text-slate-600">{t("saveRefNote")}</p>
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 p-5">
        <p className="font-semibold text-slate-800">{t("orderDetailsHeading")}</p>
        <ul className="mt-2 space-y-2 text-sm">
          {/* i.item_name/batch_no/batch_expiry_date are real order data from the connected Frappe
              backend — never translated; only the surrounding labels are. */}
          {order.items.map((i) => (
            <li key={i.item_code} className="flex items-start justify-between gap-4">
              <span>
                {i.item_name} × {i.qty}
                <span className="mt-0.5 block text-xs text-slate-500">
                  {t("batchLabel", { batch: i.batch_no })}
                  {i.batch_expiry_date ? t("batchExpirySuffix", { date: i.batch_expiry_date }) : ""}
                </span>
              </span>
              <span className="shrink-0">{formatVnd(i.amount)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>{t("totalLabel", { method: order.payment_method })}</span>
          <span>{formatVnd(order.grand_total)}</span>
        </div>
        <p className="mt-2 whitespace-pre-line text-sm text-slate-500">
          {t("deliveringTo", { address: order.address_display?.replace(/<br\s*\/?>/g, "\n") ?? "" })}
        </p>
        <p className="mt-2 text-xs text-slate-500">{t("batchNote")}</p>
      </div>

      <div className="mt-6 text-center">
        <Link href="/shop" className="text-sky-700 underline">
          {t("continueShopping")}
        </Link>
      </div>
    </div>
  );
}
