import { requireSession } from "@/lib/auth";
import { getMyQualificationStatus } from "@/lib/api";

export default async function QualificationPage() {
  const session = await requireSession();
  const q = await getMyQualificationStatus(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Qualification Status</h1>
        <p className="mt-1 text-sm text-slate-500">
          {session.supplierName}&apos;s own quality status only — never another supplier&apos;s.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Quality status" value={q.quality_status} />
        <StatCard label="Critical supplier" value={q.is_critical_supplier ? "Yes" : "No"} />
        <StatCard
          label="QC pass rate"
          value={q.qc_pass_rate === null ? "—" : `${Math.round(q.qc_pass_rate * 100)}%`}
          sub={`${q.quality_inspections_accepted} of ${q.quality_inspections_total} inspections accepted`}
        />
      </div>

      <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">
        Quality status and critical-supplier flag are set through this platform&apos;s internal
        AI-assisted procurement review workflow (a human always reviews and approves any change —
        this portal only displays your own current, already-decided status; it cannot change it).
      </p>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
