"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { CheckCircle2 } from "lucide-react";
import type { BillingCycle, PricingPlan } from "@/lib/api";

// One real Edition group (one of the 8 real industries, or the 1 extra Starter-only
// PHARMA_MFG edition) — pre-grouped/pre-labeled server-side by app/[locale]/pricing/page.tsx
// so this client component only ever renders real data, never re-derives it.
export interface PricingGroup {
  industry: string;
  label: string;
  plans: PricingPlan[];
}

// Display order for the 3 real tiers that exist on `Edition.edition_code` — see
// public_api.py's `get_pricing_plans()`/`_split_edition_code()` for where "Starter"/
// "Professional"/"Enterprise" actually comes from (computed from the real edition_code, never
// stored as its own field).
const TIER_ORDER = ["Starter", "Professional", "Enterprise"] as const;

export default function PricingTable({ groups }: { groups: PricingGroup[] }) {
  const t = useTranslations("pricing");
  const [cycle, setCycle] = useState<BillingCycle>("Monthly");

  return (
    <div>
      <div className="mt-8 inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 p-1">
        <button
          type="button"
          onClick={() => setCycle("Monthly")}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
            cycle === "Monthly" ? "bg-[#158A57] text-white" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          {t("toggle.monthly")}
        </button>
        <button
          type="button"
          onClick={() => setCycle("Yearly")}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
            cycle === "Yearly" ? "bg-[#158A57] text-white" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          {t("toggle.yearly")}
        </button>
      </div>
      {cycle === "Yearly" && (
        <p className="mt-3 text-sm text-[#158A57]">{t("yearlySavingsNote")}</p>
      )}

      <div className="mt-12 space-y-14">
        {groups.map((group) => (
          <section key={group.industry}>
            <h2 className="text-xl font-semibold text-slate-900">{group.label}</h2>
            <div className="mt-5 grid grid-cols-1 gap-6 sm:grid-cols-3">
              {TIER_ORDER.filter((tier) => group.plans.some((p) => p.tier === tier)).map(
                (tier) => {
                  const plan = group.plans.find((p) => p.tier === tier);
                  if (!plan) return null;
                  const price = cycle === "Monthly" ? plan.monthly_price : plan.yearly_price;
                  return (
                    <div
                      key={plan.edition_code}
                      className="flex flex-col rounded-lg border border-slate-200 bg-white p-6 hover:border-[#3DBB89] hover:shadow-sm transition-all"
                    >
                      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-[#158A57]/10 px-2.5 py-1 text-xs font-semibold text-[#0A4A2D]">
                        {t(`tierLabel.${tier}`)}
                      </span>
                      <p className="mt-4 text-3xl font-bold text-slate-900">
                        ${price.toFixed(0)}
                        <span className="text-sm font-medium text-slate-500">
                          {cycle === "Monthly" ? t("perMonth") : t("perYear")}
                        </span>
                      </p>
                      <p className="mt-3 flex-1 text-sm text-slate-600">{plan.description}</p>
                      <Link
                        href={`/signup?edition=${plan.edition_code}&cycle=${cycle}`}
                        className="mt-6 inline-flex items-center justify-center gap-2 rounded-md bg-[#158A57] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#0A4A2D]"
                      >
                        <CheckCircle2 className="h-4 w-4" strokeWidth={2} />
                        {t("subscribe")}
                      </Link>
                    </div>
                  );
                }
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
