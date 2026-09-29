import { requireSession } from "@/lib/auth";
import { getMyInvoices, formatVnd } from "@/lib/api";

export default async function InvoicesPage() {
  const session = await requireSession();
  const invoices = await getMyInvoices(session.frappeSid);

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-900">My Invoices</h1>
      <p className="mt-1 text-sm text-slate-500">
        Only Sales Invoices belonging to {session.customerName} — never another dealer&apos;s.
      </p>

      <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Invoice</Th>
              <Th>Date</Th>
              <Th>Due</Th>
              <Th>Total</Th>
              <Th>Outstanding</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {invoices.map((inv) => (
              <tr key={inv.name}>
                <td className="px-4 py-3 font-medium text-slate-900">{inv.name}</td>
                <td className="px-4 py-3 text-slate-600">{inv.posting_date}</td>
                <td className="px-4 py-3 text-slate-600">{inv.due_date}</td>
                <td className="px-4 py-3 text-slate-600">{formatVnd(inv.grand_total)}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatVnd(inv.outstanding_amount)}</td>
                <td className="px-4 py-3 text-slate-600">{inv.status}</td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                  No invoices yet.
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
