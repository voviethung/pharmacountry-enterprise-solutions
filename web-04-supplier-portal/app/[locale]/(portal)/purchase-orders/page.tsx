import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyPurchaseOrders, formatMoney } from "@/lib/api";

// Force dynamic rendering — login-gated page, fetches this supplier's own live purchase orders
// on every request. See app/[locale]/(portal)/dashboard/page.tsx for the full reasoning.
export const dynamic = "force-dynamic";

export default async function PurchaseOrdersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("purchaseOrders");

  const session = await requireSession();
  const orders = await getMyPurchaseOrders(session.frappeSid);

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
              <Th>{t("table.purchaseOrder")}</Th>
              <Th>{t("table.date")}</Th>
              <Th>{t("table.scheduleDate")}</Th>
              <Th>{t("table.status")}</Th>
              <Th>{t("table.total")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((po) => (
              <tr key={po.name}>
                <td className="px-4 py-3">
                  <Link href={`/purchase-orders/${po.name}`} className="font-medium text-teal-700 hover:underline">
                    {po.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{po.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{po.schedule_date}</td>
                <td className="px-4 py-3 text-slate-600">{po.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatMoney(po.grand_total, po.currency)}</td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
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

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
