import { getPharmacyCatalog, formatVnd } from "@/lib/api";
import AddToCartButton from "@/components/AddToCartButton";

// Force dynamic rendering — this page calls the real Frappe backend (live per-store stock,
// pricing) on every request. Without this, Next.js prerenders it once at Docker build time
// (when the backend isn't reachable from inside the build container) and serves that stale
// snapshot to every visitor forever.
export const dynamic = "force-dynamic";

export default async function ShopPage() {
  let items: Awaited<ReturnType<typeof getPharmacyCatalog>> = [];
  let loadError = false;
  try {
    items = await getPharmacyCatalog();
  } catch {
    loadError = true;
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Shop — Store A</h1>
      <p className="mt-1 text-sm text-slate-600">
        Live demo products, prices, and per-store stock, generated and managed directly by our
        connected pharmacy ERP system.
      </p>

      {loadError && (
        <p className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">
          Could not load the catalog right now — please try again shortly.
        </p>
      )}

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.item_code} className="rounded-lg border border-slate-200 p-5">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-sky-700">{item.category}</p>
              {!item.requires_prescription && (
                <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
                  OTC — no prescription needed
                </span>
              )}
            </div>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">{item.item_name}</h2>
            <p className="mt-2 text-sm text-slate-600">{item.description}</p>
            <p className="mt-3 text-lg font-bold text-slate-900">
              {formatVnd(item.price)} <span className="text-sm font-normal text-slate-500">/ {item.uom}</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {item.available_qty > 0
                ? `${Math.floor(item.available_qty)} in stock at ${item.store} (non-expired only)`
                : `Out of stock at ${item.store}`}
            </p>
            <div className="mt-4">
              <AddToCartButton item={item} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-slate-500">
        Prices and stock shown here are the current catalog snapshot at the time this page was
        loaded. The price you&apos;re actually charged, and the specific batch your order is filled
        from, are always confirmed by our system at checkout — an expired batch can never be sold,
        no matter what this page shows.
      </p>
    </div>
  );
}
