import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyOrders, getMyCatalog, formatVnd } from "@/lib/api";
import PlaceOrderForm from "@/components/PlaceOrderForm";

// Force dynamic rendering — login-gated page that calls the real Frappe backend with a
// per-session farm scope on every request. See dashboard/page.tsx for the full rationale.
export const dynamic = "force-dynamic";

export default async function OrdersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("orders");

  const session = await requireSession();
  const [orders, catalog] = await Promise.all([
    getMyOrders(session.frappeSid),
    getMyCatalog(session.frappeSid),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("title")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subtitle", { name: session.customerName })}
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">{t("placeNewOrder")}</h2>
        <PlaceOrderForm item={catalog[0]} />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("table.order")}</Th>
              <Th>{t("table.date")}</Th>
              <Th>{t("table.status")}</Th>
              <Th>{t("table.total")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((order) => (
              <tr key={order.name}>
                <td className="px-4 py-3">
                  <Link href={`/orders/${order.name}`} className="font-medium text-emerald-700 hover:underline">
                    {order.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{order.transaction_date}</td>
                <td className="px-4 py-3 text-slate-600">{order.status}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatVnd(order.grand_total)}</td>
              </tr>
            ))}
            {orders.length === 0 && (
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

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
