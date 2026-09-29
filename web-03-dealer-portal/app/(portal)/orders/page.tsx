import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyOrders, getCatalogWithMyPricing, formatVnd } from "@/lib/api";
import PlaceOrderForm from "@/components/PlaceOrderForm";

export default async function OrdersPage() {
  const session = await requireSession();
  const [orders, catalog] = await Promise.all([
    getMyOrders(session.frappeSid),
    getCatalogWithMyPricing(session.frappeSid),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Orders</h1>
        <p className="mt-1 text-sm text-slate-500">
          Only Sales Orders belonging to {session.customerName} — never another dealer&apos;s.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Place a new order</h2>
        <PlaceOrderForm items={catalog} />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Order</Th>
              <Th>Date</Th>
              <Th>Status</Th>
              <Th>Total</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((order) => (
              <tr key={order.name}>
                <td className="px-4 py-3">
                  <Link href={`/orders/${order.name}`} className="font-medium text-indigo-600 hover:underline">
                    {order.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{order.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{order.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatVnd(order.grand_total)}</td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  No orders yet.
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
