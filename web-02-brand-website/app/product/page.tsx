import type { Metadata } from "next";
import { getBrandProduct } from "@/lib/api";

export const metadata: Metadata = {
  title: "Our Product",
};

export default async function ProductPage() {
  const product = await getBrandProduct();

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
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
        <h2 className="text-xl font-semibold text-stone-900">Why people take it</h2>
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
          <strong className="font-semibold">Allergen notice:</strong> this formula contains
          soy lecithin (see the full ingredient breakdown below) — flagged here clearly, not
          buried in fine print.
        </section>
      )}

      {/* Real formula / ingredients */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold text-stone-900">Our published formula</h2>
        <p className="mt-2 text-sm text-stone-600">
          Every ingredient below, and its real proportion of the formula by weight, is drawn
          live from our own manufacturing system&apos;s current, active production formula —
          not a marketing approximation.
        </p>
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
          <h2 className="text-xl font-semibold text-stone-900">Lab-verified quality</h2>
          <p className="mt-2 text-sm text-stone-600">
            We publish our internal potency specification and the real, verified result from
            our most recently released batch&apos;s Certificate of Analysis.
          </p>
          <dl className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
            {product.quality.specification.map((spec) => (
              <div key={spec.parameter_name}>
                <dt className="text-xs uppercase tracking-wide text-stone-500">
                  {spec.parameter_name}
                </dt>
                <dd className="mt-1 text-lg font-semibold text-stone-900">
                  {spec.min_value}&ndash;{spec.max_value} {spec.unit}
                </dd>
                <p className="mt-1 text-xs text-stone-500">Published specification range</p>
              </div>
            ))}
            {Object.entries(product.quality.latest_tested_values).map(([param, value]) => (
              <div key={param}>
                <dt className="text-xs uppercase tracking-wide text-stone-500">
                  Latest verified result
                </dt>
                <dd className="mt-1 text-lg font-semibold text-emerald-800">
                  {value}{" "}
                  {product.quality!.specification.find((s) => s.parameter_name === param)
                    ?.unit}
                </dd>
                <p className="mt-1 text-xs text-stone-500">
                  {product.quality!.verified_on
                    ? `Verified ${product.quality!.verified_on}`
                    : "Verified"}
                </p>
              </div>
            ))}
          </dl>
        </section>
      )}

      <section className="mt-12 border-t border-stone-200 pt-6 text-sm text-stone-500">
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-stone-400">Product Code</dt>
            <dd className="mt-1 font-medium text-stone-900">{product.item_code}</dd>
          </div>
          <div>
            <dt className="text-stone-400">Shelf Life</dt>
            <dd className="mt-1 font-medium text-stone-900">
              {product.shelf_life_days} days
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
