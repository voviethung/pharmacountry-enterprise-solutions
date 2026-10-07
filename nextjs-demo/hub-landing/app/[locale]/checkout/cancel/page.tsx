import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { XCircle } from "lucide-react";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("checkoutCancelTitle"),
    description: t("checkoutCancelDescription"),
  };
}

// Plain confirmation page — PayPal redirects the browser here if the customer cancels approval.
// The Tenant Subscription record paypal_billing.create_subscription_checkout() created stays
// "Pending" (never activated) — nothing further happens automatically.
export default async function CheckoutCancelPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("checkout.cancel");

  return (
    <div className="mx-auto max-w-2xl px-6 py-20 text-center">
      <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100">
        <XCircle className="h-7 w-7 text-amber-700" strokeWidth={1.75} />
      </span>
      <h1 className="mt-6 text-2xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 text-slate-600">{t("body")}</p>
      <Link
        href="/pricing"
        className="mt-8 inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0A4A2D]"
      >
        {t("backToPricing")}
      </Link>
    </div>
  );
}
