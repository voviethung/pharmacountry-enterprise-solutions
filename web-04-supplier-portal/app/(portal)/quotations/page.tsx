import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyQuotations, formatMoney } from "@/lib/api";

export default async function QuotationsPage() {
  const session = await requireSession();
  const quotations = await getMyQuotations(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Quotations</h1>
        <p className="mt-1 text-sm text-slate-500">
          Only Supplier Quotations belonging to {session.supplierName} — never another
          supplier&apos;s. Includes quotations submitted with or without an inviting RFQ.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Quotation</Th>
              <Th>Date</Th>
              <Th>Valid till</Th>
              <Th>Status</Th>
              <Th>Total</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {quotations.map((q) => (
              <tr key={q.name}>
                <td className="px-4 py-3">
                  <Link href={`/quotations/${q.name}`} className="font-medium text-teal-700 hover:underline">
                    {q.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{q.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{q.valid_till}</td>
                <td className="px-4 py-3 text-slate-600">{q.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(q.grand_total, q.currency)}</td>
              </tr>
            ))}
            {quotations.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No quotations yet.
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
