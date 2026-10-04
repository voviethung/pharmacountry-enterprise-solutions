import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyRecommendations } from "@/lib/api";

// Force dynamic rendering — login-gated page that calls the real Frappe backend with a
// per-session farm scope on every request. See dashboard/page.tsx for the full rationale.
export const dynamic = "force-dynamic";

export default async function RecommendationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("recommendations");
  const tCommon = await getTranslations("common");

  const session = await requireSession();
  const recommendations = await getMyRecommendations(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("title")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subtitle", { name: session.customerName })}
        </p>
      </div>

      <div className="space-y-4">
        {recommendations.map((r) => (
          <div key={r.name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold text-slate-900">{r.item?.item_name || r.recommended_item}</p>
              <p className="text-xs text-slate-500">{t("visitOn", { date: r.visit_date })}</p>
            </div>
            {r.item && (
              <p className="mt-1 text-xs text-slate-500">
                {t("indicatedFor", {
                  species: r.item.target_species || tCommon("dash"),
                  indication: r.item.indication || tCommon("dash"),
                  period:
                    r.item.withdrawal_period_days != null
                      ? `${r.item.withdrawal_period_days} ${tCommon("daysUnit")}`
                      : tCommon("dash"),
                })}
              </p>
            )}
            {r.notes && <p className="mt-2 text-sm text-slate-600">{r.notes}</p>}
          </div>
        ))}
        {recommendations.length === 0 && (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-400 shadow-sm">
            {t("empty")}
          </p>
        )}
      </div>
    </div>
  );
}
