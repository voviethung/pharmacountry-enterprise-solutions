import { requireSession } from "@/lib/auth";
import { getMyDeliveries, formatMoney } from "@/lib/api";

export default async function DeliveriesPage() {
  const session = await requireSession();
  const deliveries = await getMyDeliveries(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Deliveries</h1>
        <p className="mt-1 text-sm text-slate-500">
          Only Purchase Receipts (delivery/shipment records) for {session.supplierName} — never
          another supplier&apos;s — with each shipment&apos;s own real Quality Inspection result.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Receipt</Th>
              <Th>Date</Th>
              <Th>Status</Th>
              <Th>Total</Th>
              <Th>Quality Inspection</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {deliveries.map((d) => (
              <tr key={d.name}>
                <td className="px-4 py-3 font-medium text-slate-900">{d.name}</td>
                <td className="px-4 py-3 text-slate-600">{d.posting_date}</td>
                <td className="px-4 py-3 text-slate-600">{d.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(d.grand_total)}</td>
                <td className="px-4 py-3">
                  {d.quality_inspections.length === 0 ? (
                    <span className="text-slate-400">—</span>
                  ) : (
                    d.quality_inspections.map((qi) => (
                      <span
                        key={qi.name}
                        className={`mr-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          qi.status === "Accepted" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                        }`}
                      >
                        {qi.item_code}: {qi.status}
                      </span>
                    ))
                  )}
                </td>
              </tr>
            ))}
            {deliveries.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No deliveries yet.
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
