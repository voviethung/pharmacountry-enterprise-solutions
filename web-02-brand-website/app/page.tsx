import Link from "next/link";
import { getBrandProduct, getBrandProfile } from "@/lib/api";

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [profile, product] = await Promise.all([
    getBrandProfile(),
    getBrandProduct(),
  ]);

  return (
    <div>
      <section className="border-b border-stone-200 bg-gradient-to-b from-orange-50 to-[#fffaf0]">
        <div className="mx-auto max-w-5xl px-6 py-24">
          <p className="text-sm font-medium uppercase tracking-wide text-emerald-800">
            {profile.country} &middot; {product.category}
          </p>
          <h1 className="mt-3 text-4xl sm:text-5xl font-bold tracking-tight text-stone-900 max-w-2xl">
            {profile.tagline}
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-stone-600 leading-relaxed">
            {profile.mission}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/product"
              className="rounded-full bg-orange-600 px-6 py-3 text-sm font-semibold text-white hover:bg-orange-700 transition-colors"
            >
              Meet Our Product
            </Link>
            <Link
              href="/our-story"
              className="rounded-full border border-stone-300 px-6 py-3 text-sm font-semibold text-stone-700 hover:border-emerald-800 hover:text-emerald-800 transition-colors"
            >
              Our Story
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div className="aspect-square rounded-2xl bg-gradient-to-br from-orange-100 to-emerald-100 flex items-center justify-center">
            <span className="text-7xl font-bold text-orange-300">
              {product.item_name.charAt(0)}
            </span>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
              Our Flagship
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-900">
              {product.item_name}
            </h2>
            <p className="mt-3 text-stone-600 leading-relaxed">{product.tagline}</p>
            <ul className="mt-6 space-y-2">
              {product.benefits.slice(0, 3).map((b) => (
                <li key={b} className="flex items-start gap-2 text-sm text-stone-700">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-700" />
                  {b}
                </li>
              ))}
            </ul>
            <Link
              href="/product"
              className="mt-6 inline-block text-sm font-semibold text-emerald-800 hover:text-emerald-900"
            >
              See the full formula &amp; lab results &rarr;
            </Link>
          </div>
        </div>
      </section>

      {product.quality && (
        <section className="border-t border-stone-200 bg-emerald-50">
          <div className="mx-auto max-w-5xl px-6 py-16 text-center">
            <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
              Quality You Can Verify
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-900">
              Every batch is lab-tested before it ships
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-stone-600">
              Our most recent batch was independently verified in-house on{" "}
              {product.quality.verified_on}, tested at{" "}
              {product.quality.latest_tested_values["Vitamin C Content"]}
              {" "}
              {product.quality.specification[0]?.unit} of Vitamin C per tablet —
              well within our published guarantee of{" "}
              {product.quality.specification[0]?.min_value}&ndash;
              {product.quality.specification[0]?.max_value}{" "}
              {product.quality.specification[0]?.unit}.
            </p>
          </div>
        </section>
      )}

      <section className="border-t border-stone-200 bg-stone-100">
        <div className="mx-auto max-w-5xl px-6 py-14 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <h2 className="text-xl font-semibold text-stone-900">
              Find {product.item_name} near you
            </h2>
            <p className="mt-1 text-sm text-stone-600">
              Sold through a nationwide network of pharmacies and health retailers.
            </p>
          </div>
          <Link
            href="/where-to-buy"
            className="rounded-full bg-orange-600 px-6 py-3 text-sm font-semibold text-white hover:bg-orange-700 transition-colors whitespace-nowrap"
          >
            Where to Buy
          </Link>
        </div>
      </section>
    </div>
  );
}
