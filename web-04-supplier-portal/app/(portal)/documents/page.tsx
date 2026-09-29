import { requireSession } from "@/lib/auth";
import { getMyDocuments } from "@/lib/api";

export default async function DocumentsPage() {
  const session = await requireSession();
  const docs = await getMyDocuments(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Documents</h1>
        <p className="mt-1 text-sm text-slate-500">
          Real document references tied to {session.supplierName}&apos;s own relationship — RFQ
          invitations, quotations, purchase orders, delivery receipts and quality inspection
          certificates. Not a document-management system (see this platform&apos;s DMS demo for
          that) — every row here links to a real transactional record this supplier already owns.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Type</Th>
              <Th>Reference</Th>
              <Th>Date</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {docs.map((d, i) => (
              <tr key={i}>
                <td className="px-4 py-3 text-slate-600">{d.type}</td>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{d.title}</p>
                  <p className="text-xs text-slate-400">
                    {d.reference_doctype} · {d.reference_name}
                  </p>
                </td>
                <td className="px-4 py-3 text-slate-600">{d.date || "—"}</td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-slate-400">
                  No documents yet.
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
