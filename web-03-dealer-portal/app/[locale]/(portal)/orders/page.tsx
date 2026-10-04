import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyOrders, getCatalogWithMyPricing, formatVnd } from "@/lib/api";
import PlaceOrderForm from "@/components/PlaceOrderForm";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
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
    getCatalogWithMyPricing(session.frappeSid),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subtitle", { customerName: session.customerName })}
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">{t("placeNewOrderHeading")}</h2>
        <PlaceOrderForm items={catalog} />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("thOrder")}</Th>
              <Th>{t("thDate")}</Th>
              <Th>{t("thStatus")}</Th>
              <Th>{t("thTotal")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((order) => (
              <tr key={order.name}>
                <td className="px-4 py-3">
                  <Link href={`/orders/${order.name}`} className="font-medium text-indigo-600 hover:underline">
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
                  {t("emptyOrders")}
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
