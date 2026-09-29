import { requireSession } from "@/lib/auth";
import { getMyTechnicalVisits } from "@/lib/api";

// Force dynamic rendering — login-gated page that calls the real Frappe backend with a
// per-session farm scope on every request. See dashboard/page.tsx for the full rationale.
export const dynamic = "force-dynamic";

export default async function VisitsPage() {
  const session = await requireSession();
  const visits = await getMyTechnicalVisits(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Technical Visits</h1>
        <p className="mt-1 text-sm text-slate-500">
          Every real field-rep visit made to {session.customerName} — never another farm&apos;s.
        </p>
      </div>

      <div className="space-y-4">
        {visits.map((v) => (
          <div key={v.name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium text-slate-900">Visit on {v.visit_date}</p>
              {v.sales_person && <p className="text-xs text-slate-500">by {v.sales_person}</p>}
            </div>
            {v.products_discussed && (
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium">Products discussed: </span>
                {v.products_discussed}
              </p>
            )}
            {v.notes && (
              <p className="mt-2 text-sm text-slate-600">
                <span className="font-medium">Notes: </span>
                {v.notes}
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              {v.recommended_item && (
                <span className="rounded-full bg-emerald-50 px-2 py-1 font-medium text-emerald-700">
                  Recommended: {v.recommended_item}
                </span>
              )}
              {v.follow_up_date && (
                <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600">
                  Follow-up due {v.follow_up_date}
                </span>
              )}
            </div>
          </div>
        ))}
        {visits.length === 0 && (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-400 shadow-sm">
            No technical visits recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}
