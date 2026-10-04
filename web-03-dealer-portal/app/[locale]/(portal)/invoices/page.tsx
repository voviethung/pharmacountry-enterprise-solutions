import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyInvoices, formatVnd } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export default async function InvoicesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("invoices");

  const session = await requireSession();
  const invoices = await getMyInvoices(session.frappeSid);

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
      <p className="mt-1 text-sm text-slate-500">
        {t("subtitle", { customerName: session.customerName })}
      </p>

      <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("thInvoice")}</Th>
              <Th>{t("thDate")}</Th>
              <Th>{t("thDue")}</Th>
              <Th>{t("thTotal")}</Th>
              <Th>{t("thOutstanding")}</Th>
              <Th>{t("thStatus")}</Th>
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
                  {t("emptyInvoices")}
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
