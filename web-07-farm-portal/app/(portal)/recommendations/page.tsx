import { requireSession } from "@/lib/auth";
import { getMyRecommendations } from "@/lib/api";

export default async function RecommendationsPage() {
  const session = await requireSession();
  const recommendations = await getMyRecommendations(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Treatment / Feed Recommendations</h1>
        <p className="mt-1 text-sm text-slate-500">
          Real products your field rep recommended during a technical visit to {session.customerName}
          . A recommendation is a technical visit that named a specific product — not a separate
          fabricated record.
        </p>
      </div>

      <div className="space-y-4">
        {recommendations.map((r) => (
          <div key={r.name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold text-slate-900">{r.item?.item_name || r.recommended_item}</p>
              <p className="text-xs text-slate-500">Visit on {r.visit_date}</p>
            </div>
            {r.item && (
              <p className="mt-1 text-xs text-slate-500">
                Indicated for: {r.item.target_species || "—"} · {r.item.indication || "—"} · Withdrawal
                period: {r.item.withdrawal_period_days != null ? `${r.item.withdrawal_period_days} days` : "—"}
              </p>
            )}
            {r.notes && <p className="mt-2 text-sm text-slate-600">{r.notes}</p>}
          </div>
        ))}
        {recommendations.length === 0 && (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-400 shadow-sm">
            No recommendations recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}
