import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getPricingPlans, type BillingCycle, type PricingPlan } from "@/lib/api";
import SignupForm from "@/components/SignupForm";

const LEGACY_SAMPLE_EDITION = "PHARMA_MFG_STARTER";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("signupTitle"),
    description: t("signupDescription"),
  };
}

export const dynamic = "force-dynamic";

export default async function SignupPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ edition?: string; cycle?: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { edition, cycle } = await searchParams;
  const t = await getTranslations("signup");

  const editionCode = typeof edition === "string" ? edition.trim() : "";
  const billingCycle: BillingCycle = cycle === "Yearly" ? "Yearly" : "Monthly";
  const signupIntro =
    locale === "vi"
      ? "Nhập thông tin doanh nghiệp để tiếp tục thanh toán qua PayPal. Sau khi PayPal xác nhận đăng ký, hệ thống sẽ ghi nhận subscription và hoàn tất tenant theo quy trình provisioning; tên miền có thể cần bước cấu hình hạ tầng trước khi truy cập."
      : "Enter your company details to continue to PayPal. After PayPal confirms the subscription, the platform records the subscription and completes the tenant through the provisioning workflow; hostname infrastructure may still require a configuration step before access.";

  let plan: PricingPlan | null = null;
  let loadError = false;
  try {
    const plans = await getPricingPlans();
    plan =
      editionCode === LEGACY_SAMPLE_EDITION
        ? null
        : plans.find((p) => p.edition_code === editionCode) ?? null;
  } catch {
    loadError = true;
  }

  if (loadError) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {t("loadError")}
        </p>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-bold text-slate-900">{t("planNotFoundTitle")}</h1>
        <p className="mt-3 max-w-xl text-slate-600">{t("planNotFoundBody")}</p>
        <Link
          href="/pricing"
          className="mt-6 inline-block text-sm font-medium text-[#158A57] hover:text-[#0A4A2D] hover:underline"
        >
          {t("backToPricing")}
        </Link>
      </div>
    );
  }

  const price = billingCycle === "Monthly" ? plan.monthly_price : plan.yearly_price;

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 max-w-2xl text-slate-600">{signupIntro}</p>

      <div className="mt-10 grid grid-cols-1 gap-10 md:grid-cols-[1fr_320px]">
        <SignupForm editionCode={plan.edition_code} billingCycle={billingCycle} locale={locale} />

        <aside className="h-fit rounded-lg border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t("selectedPlanHeading")}
          </h2>
          <p className="mt-2 font-semibold text-slate-900">{plan.edition_name}</p>
          <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
          <p className="mt-4 text-2xl font-bold text-slate-900">
            ${price.toFixed(0)}
            <span className="text-sm font-medium text-slate-500">
              {billingCycle === "Monthly" ? t("perMonthShort") : t("perYearShort")}
            </span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {billingCycle === "Monthly" ? t("billedMonthly") : t("billedYearly")}
          </p>
        </aside>
      </div>
    </div>
  );
}
