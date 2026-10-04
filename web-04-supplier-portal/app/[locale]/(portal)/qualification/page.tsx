import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyQualificationStatus } from "@/lib/api";

// Force dynamic rendering — login-gated page, fetches this supplier's own live qualification
// status on every request. See app/[locale]/(portal)/dashboard/page.tsx for the full reasoning.
export const dynamic = "force-dynamic";

export default async function QualificationPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("qualification");

  const session = await requireSession();
  const q = await getMyQualificationStatus(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subhead", { supplierName: session.supplierName })}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label={t("stats.qualityStatus")} value={q.quality_status} />
        <StatCard
          label={t("stats.criticalSupplier")}
          value={q.is_critical_supplier ? t("stats.yes") : t("stats.no")}
        />
        <StatCard
          label={t("stats.qcPassRate")}
          value={q.qc_pass_rate === null ? "—" : `${Math.round(q.qc_pass_rate * 100)}%`}
          sub={t("stats.inspectionsAccepted", {
            accepted: q.quality_inspections_accepted,
            total: q.quality_inspections_total,
          })}
        />
      </div>

      <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">{t("note")}</p>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
