import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyReturns, getMyDeliveriesEligibleForReturn, formatVnd } from "@/lib/api";
import RequestReturnForm from "@/components/RequestReturnForm";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export default async function ReturnsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("returns");

  const session = await requireSession();
  const [returns, deliveries] = await Promise.all([
    getMyReturns(session.frappeSid),
    getMyDeliveriesEligibleForReturn(session.frappeSid),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">{t("subtitle")}</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">{t("fileNewReturnHeading")}</h2>
        <RequestReturnForm deliveries={deliveries} />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("thReturn")}</Th>
              <Th>{t("thAgainstDelivery")}</Th>
              <Th>{t("thDate")}</Th>
              <Th>{t("thAmount")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {returns.map((r) => (
              <tr key={r.name}>
                <td className="px-4 py-3 font-medium text-slate-900">{r.name}</td>
                <td className="px-4 py-3 text-slate-600">{r.return_against}</td>
                <td className="px-4 py-3 text-slate-600">{r.posting_date}</td>
                <td className="px-4 py-3 text-slate-600">{formatVnd(r.grand_total)}</td>
              </tr>
            ))}
            {returns.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  {t("emptyReturns")}
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
