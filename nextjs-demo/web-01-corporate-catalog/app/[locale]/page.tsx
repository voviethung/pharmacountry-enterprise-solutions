import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getCatalogItems, getCompanyProfile, formatPrice } from "@/lib/api";

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");
  const tCatalogItem = await getTranslations("catalogItem");

  const [profile, items] = await Promise.all([
    getCompanyProfile(),
    getCatalogItems(),
  ]);
  const featured = items.slice(0, 3);

  return (
    <div>
      <section className="border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <p className="text-sm font-medium uppercase tracking-wide text-amber-600">
            {profile.country} &middot; {t("distributorLabel")}
          </p>
          <h1 className="mt-3 text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 max-w-2xl">
            {profile.company_name}
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-600 leading-relaxed">
            {profile.about}
          </p>
          <div className="mt-8 flex gap-4">
            <Link
              href="/catalog"
              className="rounded-md bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700 transition-colors"
            >
              {t("ctaViewCatalog")}
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="flex items-end justify-between mb-8">
          <h2 className="text-2xl font-semibold text-slate-900">
            {t("featuredHeading")}
          </h2>
          <Link
            href="/catalog"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            {t("viewAll")}
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {featured.map((item) => (
            <Link
              key={item.item_code}
              href={`/catalog/${encodeURIComponent(item.item_code)}`}
              className="group rounded-lg border border-slate-200 p-6 hover:border-slate-400 hover:shadow-sm transition-all"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
                {item.category}
              </p>
              <h3 className="mt-2 font-semibold text-slate-900 group-hover:text-slate-700">
                {item.item_name}
              </h3>
              <p className="mt-2 text-sm text-slate-600 line-clamp-2">
                {item.description}
              </p>
              <p className="mt-4 font-medium text-slate-900">
                {item.price === null || item.currency === null
                  ? tCatalogItem("priceOnRequest")
                  : formatPrice(item.price, item.currency)}
              </p>
            </Link>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <p className="text-3xl font-bold text-slate-900">{items.length}</p>
            <p className="mt-1 text-sm text-slate-600">{t("stats.productsInCatalog")}</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-slate-900">{profile.currency}</p>
            <p className="mt-1 text-sm text-slate-600">{t("stats.pricingCurrency")}</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-slate-900">{profile.country}</p>
            <p className="mt-1 text-sm text-slate-600">{t("stats.headquarteredIn")}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
