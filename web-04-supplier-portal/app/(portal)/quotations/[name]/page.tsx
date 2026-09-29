import { notFound } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { getMyQuotationDetail, SupplierApiError, formatMoney } from "@/lib/api";

export default async function QuotationDetailPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const session = await requireSession();
  const { name } = await params;

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
          {quotation.transaction_date} · Valid till {quotation.valid_till} · Status {quotation.status}
          {quotation.incoterm ? ` · Incoterm ${quotation.incoterm}` : ""}
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
              <Th>Item</Th>
              <Th>Qty</Th>
              <Th>Rate</Th>
              <Th>Amount</Th>
              <Th>Lead time</Th>
              <Th>RFQ</Th>
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
                <td className="px-4 py-3 text-slate-600">{row.lead_time_days ?? "—"} days</td>
                <td className="px-4 py-3 text-slate-600">{row.request_for_quotation || "—"}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                Grand total
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
