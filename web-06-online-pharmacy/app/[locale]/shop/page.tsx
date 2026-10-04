import { getTranslations, setRequestLocale } from "next-intl/server";
import { getPharmacyCatalog, formatVnd } from "@/lib/api";
import AddToCartButton from "@/components/AddToCartButton";

// Force dynamic rendering — this page calls the real Frappe backend (live per-store stock,
// pricing) on every request. Without this, Next.js prerenders it once at Docker build time
// (when the backend isn't reachable from inside the build container) and serves that stale
// snapshot to every visitor forever.
export const dynamic = "force-dynamic";

export default async function ShopPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("shop");

  let items: Awaited<ReturnType<typeof getPharmacyCatalog>> = [];
  let loadError = false;
  try {
    items = await getPharmacyCatalog();
  } catch {
    loadError = true;
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-1 text-sm text-slate-600">{t("subtitle")}</p>

      {loadError && (
        <p className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{t("loadError")}</p>
      )}

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        {/* item_code/category/item_name/description/price/uom/store/available_qty are real
            catalog data from the connected Frappe backend — never translated. */}
        {items.map((item) => (
          <div key={item.item_code} className="rounded-lg border border-slate-200 p-5">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-sky-700">{item.category}</p>
              {!item.requires_prescription && (
                <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
                  {t("otcBadge")}
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
                ? t("inStock", { qty: Math.floor(item.available_qty), store: item.store })
                : t("outOfStock", { store: item.store })}
            </p>
            <div className="mt-4">
              <AddToCartButton item={item} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-slate-500">{t("footerNote")}</p>
    </div>
  );
}
