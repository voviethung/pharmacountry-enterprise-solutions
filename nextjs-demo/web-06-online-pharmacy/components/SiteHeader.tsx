"use client";

import { useTranslations, useLocale } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useCart } from "./CartProvider";
import LocaleSwitcher from "./LocaleSwitcher";

export default function SiteHeader() {
  const t = useTranslations("nav");
  const locale = useLocale();
  const { totalQty } = useCart();

  return (
    <div>
      <div className="border-b border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-5xl px-4 py-1.5">
          <a
            href={`https://pharmacountry.vn/${locale}`}
            className="inline-block text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
          >
            {t("backToHub")}
          </a>
        </div>
      </div>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-lg font-semibold text-slate-900">
          {t("brandName")} <span className="text-sm font-normal text-slate-500">{t("brandSub")}</span>
        </Link>
        <nav className="flex items-center gap-5 text-sm font-medium text-slate-700">
          <Link href="/shop" className="hover:text-sky-700">
            {t("shop")}
          </Link>
          <Link href="/track" className="hover:text-sky-700">
            {t("trackOrder")}
          </Link>
          <Link href="/cart" className="flex items-center gap-1 hover:text-sky-700">
            {t("cart")}
            <span className="inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-sky-600 px-1.5 py-0.5 text-xs font-semibold text-white">
              {totalQty}
            </span>
          </Link>
          <LocaleSwitcher />
        </nav>
        </div>
      </header>
    </div>
  );
}
