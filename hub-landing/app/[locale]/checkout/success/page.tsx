import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { CheckCircle2 } from "lucide-react";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("checkoutSuccessTitle"),
    description: t("checkoutSuccessDescription"),
  };
}

// Plain confirmation page — PayPal redirects the browser here after a real approval. The actual
// tenant activation happens later, out of band, once paypal_billing.py's webhook_api() receives
// PayPal's own BILLING.SUBSCRIPTION.ACTIVATED event — this page never itself provisions
// anything, it only confirms the checkout step completed.
export default async function CheckoutSuccessPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("checkout.success");

  return (
    <div className="mx-auto max-w-2xl px-6 py-20 text-center">
      <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#158A57]/10">
        <CheckCircle2 className="h-7 w-7 text-[#0A4A2D]" strokeWidth={1.75} />
      </span>
      <h1 className="mt-6 text-2xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 text-slate-600">{t("body")}</p>
      <Link
        href="/"
        className="mt-8 inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0A4A2D]"
      >
        {t("backHome")}
      </Link>
    </div>
  );
}
