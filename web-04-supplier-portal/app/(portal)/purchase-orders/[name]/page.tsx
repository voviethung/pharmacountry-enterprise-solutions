import { notFound } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { getMyPurchaseOrderDetail, SupplierApiError, formatMoney } from "@/lib/api";

export default async function PurchaseOrderDetailPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const session = await requireSession();
  const { name } = await params;

  let po;
  try {
    po = await getMyPurchaseOrderDetail(session.frappeSid, name);
  } catch (err) {
    if (err instanceof SupplierApiError) notFound();
    throw err;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{po.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {po.transaction_date} · Schedule {po.schedule_date} · Status {po.status}
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Item</Th>
              <Th>Qty ordered</Th>
              <Th>Qty received</Th>
              <Th>Rate</Th>
              <Th>Amount</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {po.items.map((row, i) => (
              <tr key={i}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{row.item_name}</p>
                  <p className="text-xs text-slate-400">{row.item_code}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{row.qty}</td>
                <td className="px-4 py-3 text-slate-600">{row.received_qty}</td>
                <td className="px-4 py-3 text-slate-600">{formatMoney(row.rate, po.currency)}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(row.amount, po.currency)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={4} className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                Grand total
              </td>
              <td className="px-4 py-3 text-sm font-bold text-slate-900">{formatMoney(po.grand_total, po.currency)}</td>
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
