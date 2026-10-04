import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyRfqs } from "@/lib/api";

// Force dynamic rendering — login-gated page, fetches this supplier's own live RFQs on every
// request. See app/[locale]/(portal)/dashboard/page.tsx for the full reasoning.
export const dynamic = "force-dynamic";

export default async function RfqsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("rfqs");

  const session = await requireSession();
  const rfqs = await getMyRfqs(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subhead", { supplierName: session.supplierName })}
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("table.rfq")}</Th>
              <Th>{t("table.date")}</Th>
              <Th>{t("table.scheduleDate")}</Th>
              <Th>{t("table.yourStatus")}</Th>
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
                  {t("empty")}
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
