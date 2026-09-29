import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyRfqs } from "@/lib/api";

export default async function RfqsPage() {
  const session = await requireSession();
  const rfqs = await getMyRfqs(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">My RFQs</h1>
        <p className="mt-1 text-sm text-slate-500">
          Only Request for Quotations inviting {session.supplierName} — never another
          supplier&apos;s. Every RFQ on this platform names exactly one supplier, by design (see
          this app&apos;s README).
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>RFQ</Th>
              <Th>Date</Th>
              <Th>Schedule date</Th>
              <Th>Your response status</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rfqs.map((rfq) => (
              <tr key={rfq.name}>
                <td className="px-4 py-3">
                  <Link href={`/rfqs/${rfq.name}`} className="font-medium text-teal-700 hover:underline">
                    {rfq.name}
                  </Link>
                  <p className="text-xs text-slate-400">{rfq.title}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{rfq.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{rfq.schedule_date}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={rfq.quote_status} />
                </td>
              </tr>
            ))}
            {rfqs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  No RFQ invitations yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isPending = status === "Pending";
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        isPending ? "bg-amber-50 text-amber-700" : "bg-green-50 text-green-700"
      }`}
    >
      {status}
    </span>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
