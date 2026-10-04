import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyDebt, formatVnd } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export default async function DebtPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("debt");

  const session = await requireSession();
  const debt = await getMyDebt(session.frappeSid);

  const utilization =
    debt.credit_limit && debt.credit_limit > 0
      ? Math.min(100, Math.round((debt.outstanding_balance / debt.credit_limit) * 100))
      : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subtitle", { customerName: session.customerName })}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card label={t("cardOutstanding")} value={formatVnd(debt.outstanding_balance)} />
        <Card
          label={t("cardCreditLimit")}
          value={debt.credit_limit !== null ? formatVnd(debt.credit_limit) : t("cardNoLimit")}
        />
        <Card
          label={t("cardAvailableCredit")}
          value={debt.available_credit !== null ? formatVnd(debt.available_credit) : "—"}
        />
      </div>

      {utilization !== null && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="mb-2 text-sm font-medium text-slate-700">
            {t("utilizationLabel", { percent: utilization })}
          </p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full ${utilization > 90 ? "bg-red-500" : utilization > 70 ? "bg-amber-500" : "bg-emerald-500"}`}
              style={{ width: `${utilization}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
