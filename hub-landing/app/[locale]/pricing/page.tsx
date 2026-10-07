import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { getPricingPlans, type PricingPlan } from "@/lib/api";
import PricingTable, { type PricingGroup } from "@/components/PricingTable";

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

// Force dynamic rendering — this page calls the real Frappe backend (get_pricing_plans()) on
// every request, same discipline as every other backend-reading page in this app (see
// app/[locale]/page.tsx's own comment on why).
export const dynamic = "force-dynamic";

// Presentation-only display order for the real industry groups `get_pricing_plans()` returns
// (computed server-side from the real Edition.edition_code, see that function's own
// docstring) — any industry code not listed here (there shouldn't be one today) still renders,
// just sorted alphabetically after the ones below, rather than being dropped.
const INDUSTRY_ORDER = [
  "PHARMA",
  "PHARMA_MFG",
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
    plans = await getPricingPlans();
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
