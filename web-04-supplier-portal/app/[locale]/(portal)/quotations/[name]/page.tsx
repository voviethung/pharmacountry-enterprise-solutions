import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyQuotationDetail, SupplierApiError, formatMoney } from "@/lib/api";

// Force dynamic rendering — login-gated dynamic-segment page, fetches this supplier's own live
// quotation detail on every request. See app/[locale]/(portal)/dashboard/page.tsx for the full
// reasoning.
export const dynamic = "force-dynamic";

export default async function QuotationDetailPage({
  params,
}: {
  params: Promise<{ locale: string; name: string }>;
}) {
  const { locale, name } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("quotations.detail");

  const session = await requireSession();

  let quotation;
  try {
    quotation = await getMyQuotationDetail(session.frappeSid, name);
  } catch (err) {
    if (err instanceof SupplierApiError) notFound();
    throw err;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{quotation.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("meta", {
            date: quotation.transaction_date,
            validTill: quotation.valid_till,
            status: quotation.status,
          })}
          {quotation.incoterm ? t("incoterm", { incoterm: quotation.incoterm }) : ""}
        </p>
        {quotation.terms && (
          <p className="mt-2 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            {quotation.terms}
          </p>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("table.item")}</Th>
              <Th>{t("table.qty")}</Th>
              <Th>{t("table.rate")}</Th>
              <Th>{t("table.amount")}</Th>
              <Th>{t("table.leadTime")}</Th>
              <Th>{t("table.rfq")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {quotation.items.map((row, i) => (
              <tr key={i}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{row.item_name}</p>
                  <p className="text-xs text-slate-400">{row.item_code}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{row.qty}</td>
                <td className="px-4 py-3 text-slate-600">{formatMoney(row.rate, quotation.currency)}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(row.amount, quotation.currency)}</td>
                <td className="px-4 py-3 text-slate-600">
                  {row.lead_time_days ?? "—"} {t("days")}
                </td>
                <td className="px-4 py-3 text-slate-600">{row.request_for_quotation || "—"}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                {t("grandTotal")}
              </td>
              <td colSpan={3} className="px-4 py-3 text-sm font-bold text-slate-900">
                {formatMoney(quotation.grand_total, quotation.currency)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
