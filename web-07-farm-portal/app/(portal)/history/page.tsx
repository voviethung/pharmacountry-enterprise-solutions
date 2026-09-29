import { requireSession } from "@/lib/auth";
import { getMyServiceHistory } from "@/lib/api";

export default async function HistoryPage() {
  const session = await requireSession();
  const events = await getMyServiceHistory(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Service History</h1>
        <p className="mt-1 text-sm text-slate-500">
          A unified timeline of {session.customerName}&apos;s own real orders and technical visits —
          nothing else, never another farm&apos;s.
        </p>
      </div>

      <ol className="space-y-3 border-l-2 border-slate-200 pl-4">
        {events.map((e, i) => (
          <li key={i} className="relative">
            <span
              className={`absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full ${
                e.type === "Order" ? "bg-emerald-600" : "bg-indigo-500"
              }`}
            />
            <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span
                  className={`text-xs font-semibold uppercase tracking-wide ${
                    e.type === "Order" ? "text-emerald-700" : "text-indigo-600"
                  }`}
                >
                  {e.type}
                </span>
                <span className="text-xs text-slate-400">{e.date}</span>
              </div>
              <p className="mt-1 text-sm text-slate-700">{e.summary}</p>
            </div>
          </li>
        ))}
        {events.length === 0 && (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-400 shadow-sm">
            No service history yet.
          </p>
        )}
      </ol>
    </div>
  );
}
