import type { Metadata } from "next";
import { getBrandProduct, getBrandProfile } from "@/lib/api";

export const metadata: Metadata = {
  title: "Where to Buy",
};

// This page is intentionally narrative-only — see this app's README for why. It does not
// call out to, or claim integration with, any real distributor/retailer system. The platform
// already has a real distributor demo (WEB-01, nextjs-demo/web-01-corporate-catalog, backed
// by Golden Demo #25's "Demo Consumer Distribution Co.") that actually resells this exact
// product (VITC-1000-EFF) at a real price — this page references that relationship in plain
// prose, without wiring up a live cross-app integration that this demo stage doesn't need.
export default async function WhereToBuyPage() {
  const [profile, product] = await Promise.all([getBrandProfile(), getBrandProduct()]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
        {profile.company_name}
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">
        Where to Buy {product.item_name}
      </h1>
      <p className="mt-4 text-lg text-stone-600 leading-relaxed">
        {product.item_name} is sold through a nationwide network of pharmacies and health
        retailers across {profile.country} — we manufacture it, and a network of distribution
        partners gets it onto real shelves near you.
      </p>

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="rounded-lg border border-stone-200 bg-white p-6">
          <h2 className="font-semibold text-stone-900">Pharmacy Chains</h2>
          <p className="mt-2 text-sm text-stone-600">
            Available at major pharmacy chains nationwide. Ask your local pharmacist if{" "}
            {product.item_name} is in stock, or if they can order it in.
          </p>
        </div>
        <div className="rounded-lg border border-stone-200 bg-white p-6">
          <h2 className="font-semibold text-stone-900">Health &amp; Wellness Retailers</h2>
          <p className="mt-2 text-sm text-stone-600">
            Carried by independent health-food and wellness retailers as part of our everyday
            immune-support range.
          </p>
        </div>
      </div>

      <section className="mt-12 rounded-xl border border-stone-200 bg-stone-50 p-6 text-sm text-stone-600">
        <p>
          <strong className="text-stone-900">Note on this demo:</strong> this page is
          illustrative brand copy — it does not link to a real store locator or e-commerce
          checkout. This platform separately includes a real distributor-facing site (
          <strong>WEB-01, &ldquo;Corporate + Product Catalog&rdquo;</strong>) that genuinely
          resells this same product with a real, live selling price drawn from ERP data; this
          brand site deliberately does not duplicate that price-list experience, and the two
          are not integrated with each other for this demo stage.
        </p>
      </section>
    </div>
  );
}
