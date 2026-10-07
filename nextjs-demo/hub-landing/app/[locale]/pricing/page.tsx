import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { getPricingPlans, type PricingPlan } from "@/lib/api";
import PricingTable, { type PricingGroup } from "@/components/PricingTable";

const LEGACY_SAMPLE_EDITION = "PHARMA_MFG_STARTER";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("pricingTitle"),
    description: t("pricingDescription"),
  };
}

export const dynamic = "force-dynamic";

const INDUSTRY_ORDER = [
  "PHARMA",
  "SUPPLEMENT_COSMETICS",
  "MEDICAL_DEVICE",
  "ANIMAL_FEED",
  "LIVESTOCK",
  "AQUACULTURE",
  "PROCESSING",
  "VETERINARY",
];

export default async function PricingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("pricing");

  let plans: PricingPlan[] = [];
  let loadError = false;
  try {
    plans = (await getPricingPlans()).filter(
      (plan) => plan.edition_code !== LEGACY_SAMPLE_EDITION
    );
  } catch {
    loadError = true;
  }

  const byIndustry = new Map<string, PricingPlan[]>();
  for (const plan of plans) {
    const list = byIndustry.get(plan.industry) ?? [];
    list.push(plan);
    byIndustry.set(plan.industry, list);
  }

  const industries = [...byIndustry.keys()].sort((a, b) => {
    const ai = INDUSTRY_ORDER.indexOf(a);
    const bi = INDUSTRY_ORDER.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  const groups: PricingGroup[] = industries.map((industry) => ({
    industry,
    label: t(`industries.${industry}`),
    plans: byIndustry.get(industry)!,
  }));

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 max-w-2xl text-slate-600">{t("intro")}</p>

      {loadError && (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {t("loadError")}
        </p>
      )}

      {!loadError && <PricingTable groups={groups} />}
    </div>
  );
}
