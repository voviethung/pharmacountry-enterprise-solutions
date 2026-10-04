import { getTranslations, setRequestLocale } from "next-intl/server";
import { getStorefrontCatalog, formatVnd } from "@/lib/api";
import AddToCartButton from "@/components/AddToCartButton";

// Force dynamic rendering — this page calls the real Frappe backend (live catalog + stock) on
// every request. Without this, Next.js prerenders it once at Docker build time (when the
// backend isn't reachable from inside the build container) and serves that stale/fallback
// snapshot forever.
export const dynamic = "force-dynamic";

export default async function ShopPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("shop");

  let items: Awaited<ReturnType<typeof getStorefrontCatalog>> = [];
  let loadError = false;
  try {
    items = await getStorefrontCatalog();
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
        {items.map((item) => (
          <div key={item.item_code} className="rounded-lg border border-slate-200 p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">{item.category}</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">{item.item_name}</h2>
            <p className="mt-2 text-sm text-slate-600">{item.description}</p>
            <p className="mt-3 text-lg font-bold text-slate-900">
              {formatVnd(item.price)} <span className="text-sm font-normal text-slate-500">/ {item.uom}</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {item.available_qty > 0
                ? t("inStock", { count: Math.floor(item.available_qty) })
                : t("outOfStock")}
            </p>
            <div className="mt-4">
              <AddToCartButton item={item} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-slate-500">{t("priceNote")}</p>
    </div>
  );
}
