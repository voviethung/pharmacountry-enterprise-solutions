import { requireSession } from "@/lib/auth";
import { getCatalogWithMyPricing, getStockAvailability, formatVnd } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export default async function CatalogPage() {
  const session = await requireSession();
  const [items, stock] = await Promise.all([
    getCatalogWithMyPricing(session.frappeSid),
    getStockAvailability(session.frappeSid),
  ]);
  const stockByItem = new Map(stock.map((s) => [s.item_code, s.available_qty]));

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-900">Catalog & Stock</h1>
      <p className="mt-1 text-sm text-slate-500">
        Prices below are YOUR dealer price list ({items[0]?.price_list ?? "—"}) — not the public
        retail price.
      </p>

      <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>Item</Th>
              <Th>UOM</Th>
              <Th>Your price</Th>
              <Th>Available stock</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.item_code}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{item.item_name}</p>
                  <p className="text-xs text-slate-400">{item.item_code}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{item.uom}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{formatVnd(item.my_price)}</td>
                <td className="px-4 py-3 text-slate-600">
                  {stockByItem.get(item.item_code) ?? 0} {item.uom}
                </td>
              </tr>
            ))}
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
