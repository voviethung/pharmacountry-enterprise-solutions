import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyOrderDetail, DealerApiError, formatVnd } from "@/lib/api";

// Force dynamic rendering — session-gated, per-order dynamic route, calls the real backend.
export const dynamic = "force-dynamic";

export default async function OrderDetailPage({
  params,
}: {
  params: Promise<{ locale: string; name: string }>;
}) {
  const { locale, name } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("orderDetail");

  const session = await requireSession();

  // get_my_order_detail() re-checks the order's own `customer` against the session-resolved
  // dealer server-side; a nonexistent order OR one belonging to a different dealer both surface
  // as the SAME DoesNotExistError here, rendered as an ordinary Next.js 404 — never a
  // distinguishable "found but not yours" response.
  let order;
  try {
    order = await getMyOrderDetail(session.frappeSid, name);
  } catch (err) {
    if (err instanceof DealerApiError) notFound();
    throw err;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{order.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("metaLine", {
            date: order.transaction_date,
            deliveryDate: order.delivery_date,
            status: order.status,
          })}
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("thItem")}</Th>
              <Th>{t("thQty")}</Th>
              <Th>{t("thRate")}</Th>
              <Th>{t("thAmount")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {order.items.map((row, i) => (
              <tr key={i}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{row.item_name}</p>
                  <p className="text-xs text-slate-400">{row.item_code}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{row.qty}</td>
                <td className="px-4 py-3 text-slate-600">{formatVnd(row.rate)}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatVnd(row.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                {t("grandTotal")}
              </td>
              <td className="px-4 py-3 text-sm font-bold text-slate-900">{formatVnd(order.grand_total)}</td>
            </tr>
          </tfoot>
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
