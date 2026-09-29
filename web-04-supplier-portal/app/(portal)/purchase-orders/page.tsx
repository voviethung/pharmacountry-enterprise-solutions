import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyPurchaseOrders, formatMoney } from "@/lib/api";

export default async function PurchaseOrdersPage() {
  const session = await requireSession();
  const orders = await getMyPurchaseOrders(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Purchase Orders</h1>
        <p className="mt-1 text-sm text-slate-500">
          Only Purchase Orders issued to {session.supplierName} — never another supplier&apos;s.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Purchase Order</Th>
              <Th>Date</Th>
              <Th>Schedule date</Th>
              <Th>Status</Th>
              <Th>Total</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((po) => (
              <tr key={po.name}>
                <td className="px-4 py-3">
                  <Link href={`/purchase-orders/${po.name}`} className="font-medium text-teal-700 hover:underline">
                    {po.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{po.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{po.schedule_date}</td>
                <td className="px-4 py-3 text-slate-600">{po.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(po.grand_total, po.currency)}</td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No purchase orders yet.
                </td>
              </tr>
            )}
          </tbody>
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
