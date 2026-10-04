import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getBrandProduct } from "@/lib/api";

// P2 post-launch reviewer fix: generalized version of the original single-product `/product`
// page (still kept as-is, unparameterized, for the flagship/homepage links) so the 2 new real
// SKUs (VITD3-1000-SG, ZINC-50-TAB) can each get their own real formula/lab-result detail page.

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; item_code: string }>;
}): Promise<Metadata> {
  const { item_code } = await params;
  const product = await getBrandProduct(item_code);
  return { title: product.item_name };
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ locale: string; item_code: string }>;
}) {
  const { locale, item_code } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("product");
  const tNav = await getTranslations("nav");
  const product = await getBrandProduct(item_code);

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link
        href="/products"
        className="text-sm font-medium text-emerald-800 hover:text-emerald-900"
      >
        &larr; {tNav("products")}
      </Link>
      <p className="mt-6 text-xs font-medium uppercase tracking-wide text-orange-600">
        {product.category}
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">
        {product.item_name}
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-stone-600 leading-relaxed">
        {product.story}
      </p>

      {/* Benefits */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold text-stone-900">{t("whyPeopleTakeIt")}</h2>
        <ul className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {product.benefits.map((b) => (
            <li
              key={b}
              className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-700"
            >
              {b}
            </li>
          ))}
        </ul>
      </section>

      {/* Allergen transparency */}
      {product.contains_allergen && (
        <section className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <strong className="font-semibold">{t("allergen.label")}</strong>{" "}
          {t("allergen.generic")}
        </section>
      )}

      {/* Real formula / ingredients */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold text-stone-900">
          {t("publishedFormula.heading")}
        </h2>
        <p className="mt-2 text-sm text-stone-600">{t("publishedFormula.desc")}</p>
        <div className="mt-6 space-y-3">
          {product.ingredients.map((ing) => (
            <div key={ing.item_code} className="rounded-lg border border-stone-200 bg-white p-4">
              <div className="flex items-center justify-between gap-4">
                <span className="font-medium text-stone-900">{ing.name}</span>
                <span className="text-sm font-semibold text-emerald-800">
                  {ing.percent_of_formula}%
                </span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-stone-100">
                <div
                  className="h-2 rounded-full bg-emerald-700"
                  style={{ width: `${ing.percent_of_formula}%` }}
                />
              </div>
              {ing.note && (
                <p className="mt-2 text-sm text-stone-500">{ing.note}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Quality / lab verification */}
      {product.quality && (
        <section className="mt-12 rounded-xl border border-emerald-200 bg-emerald-50 p-6">
          <h2 className="text-xl font-semibold text-stone-900">{t("labVerified.heading")}</h2>
          <p className="mt-2 text-sm text-stone-600">{t("labVerified.desc")}</p>
          <dl className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
            {product.quality.specification.map((spec) => (
              <div key={spec.parameter_name}>
                <dt className="text-xs uppercase tracking-wide text-stone-500">
                  {spec.parameter_name}
                </dt>
                <dd className="mt-1 text-lg font-semibold text-stone-900">
                  {spec.min_value}&ndash;{spec.max_value} {spec.unit}
                </dd>
                <p className="mt-1 text-xs text-stone-500">{t("specRangeLabel")}</p>
              </div>
            ))}
            {Object.entries(product.quality.latest_tested_values).map(([param, value]) => (
              <div key={param}>
                <dt className="text-xs uppercase tracking-wide text-stone-500">
                  {t("latestResultLabel")}
                </dt>
                <dd className="mt-1 text-lg font-semibold text-emerald-800">
                  {value}{" "}
                  {product.quality!.specification.find((s) => s.parameter_name === param)
                    ?.unit}
                </dd>
                <p className="mt-1 text-xs text-stone-500">
                  {product.quality!.verified_on
                    ? t("verifiedOn", { date: product.quality!.verified_on })
                    : t("verifiedLabel")}
                </p>
              </div>
            ))}
          </dl>
        </section>
      )}

      <section className="mt-12 border-t border-stone-200 pt-6 text-sm text-stone-500">
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-stone-400">{t("productCodeLabel")}</dt>
            <dd className="mt-1 font-medium text-stone-900">{product.item_code}</dd>
          </div>
          <div>
            <dt className="text-stone-400">{t("shelfLifeLabel")}</dt>
            <dd className="mt-1 font-medium text-stone-900">
              {t("daysSuffix", { count: product.shelf_life_days })}
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
