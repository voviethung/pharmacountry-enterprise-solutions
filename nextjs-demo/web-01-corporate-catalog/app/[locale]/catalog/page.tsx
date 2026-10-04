import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getCatalogItems, formatPrice } from "@/lib/api";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return { title: t("catalogTitle") };
}

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function CatalogPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("catalog");
  const tCatalogItem = await getTranslations("catalogItem");

  const items = await getCatalogItems();

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 max-w-2xl text-slate-600">{t("lead")}</p>

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item) => (
          <Link
            key={item.item_code}
            href={`/catalog/${encodeURIComponent(item.item_code)}`}
            className="group rounded-lg border border-slate-200 p-6 hover:border-slate-400 hover:shadow-sm transition-all flex flex-col"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
              {item.category}
            </p>
            <h2 className="mt-2 font-semibold text-slate-900 group-hover:text-slate-700">
              {item.item_name}
            </h2>
            <p className="mt-2 text-sm text-slate-600 flex-1">{item.description}</p>
            <div className="mt-4 flex items-center justify-between">
              <span className="font-medium text-slate-900">
                {item.price === null || item.currency === null
                  ? tCatalogItem("priceOnRequest")
                  : formatPrice(item.price, item.currency)}
              </span>
              <span className="text-xs text-slate-400">{item.item_code}</span>
            </div>
          </Link>
        ))}
      </div>

      {items.length === 0 && <p className="mt-10 text-slate-500">{t("empty")}</p>}
    </div>
  );
}
