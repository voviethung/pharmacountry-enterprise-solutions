import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyRfqDetail, SupplierApiError } from "@/lib/api";
import SubmitQuotationForm from "@/components/SubmitQuotationForm";

// Force dynamic rendering — login-gated dynamic-segment page, fetches this supplier's own live
// RFQ detail on every request. See app/[locale]/(portal)/dashboard/page.tsx for the full
// reasoning.
export const dynamic = "force-dynamic";

export default async function RfqDetailPage({
  params,
}: {
  params: Promise<{ locale: string; name: string }>;
}) {
  const { locale, name } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("rfqs.detail");

  const session = await requireSession();

  // get_my_rfq_detail() re-checks the RFQ's own invited-supplier list against the session-resolved
  // supplier server-side; a nonexistent RFQ, one inviting a different supplier, OR one that (by
  // mistake) invites more than one supplier, all surface as the SAME DoesNotExistError here,
  // rendered as an ordinary Next.js 404 — never a distinguishable "found but not yours" response.
  let rfq;
  try {
    rfq = await getMyRfqDetail(session.frappeSid, name);
  } catch (err) {
    if (err instanceof SupplierApiError) notFound();
    throw err;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{rfq.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("meta", {
            title: rfq.title,
            date: rfq.transaction_date,
            scheduleDate: rfq.schedule_date,
            status: rfq.quote_status,
          })}
        </p>
        {rfq.message_for_supplier && (
          <p className="mt-2 rounded-md bg-slate-50 p-3 text-sm text-slate-700">{rfq.message_for_supplier}</p>
        )}
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("table.item")}</Th>
              <Th>{t("table.qty")}</Th>
              <Th>{t("table.uom")}</Th>
              <Th>{t("table.requestedDelivery")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rfq.items.map((row, i) => (
              <tr key={i}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{row.item_name}</p>
                  <p className="text-xs text-slate-400">{row.item_code}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{row.qty}</td>
                <td className="px-4 py-3 text-slate-600">{row.uom}</td>
                <td className="px-4 py-3 text-slate-600">{row.schedule_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rfq.quote_status === "Pending" ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">{t("submitHeading")}</h2>
          <SubmitQuotationForm rfq={rfq.name} />
        </div>
      ) : (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{t("alreadyResponded")}</p>
      )}
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
