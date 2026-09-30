import type { Metadata } from "next";
import Link from "next/link";
import { getBrandProducts } from "@/lib/api";

export const metadata: Metadata = {
  title: "Our Products",
};

// P2 post-launch reviewer fix: this app originally showcased exactly 1 SKU end-to-end. Two
// more real products (VITD3-1000-SG, ZINC-50-TAB) were taken through the same real
// production -> QC -> LIMS COA pipeline as the original flagship (VITC-1000-EFF) so this
// lineup page can show a genuine small real range (3 SKUs) rather than one product dressed up
// to look like a catalog.
//
// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function ProductsPage() {
  const products = await getBrandProducts();

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
        Our Range
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">Our Products</h1>
      <p className="mt-4 max-w-2xl text-lg text-stone-600 leading-relaxed">
        Every product below is formulated, manufactured, and lab-tested end-to-end by Demo
        Supplement Co. — the same real formula and real quality-testing data shown on WEB-01&apos;s
        distributor catalog, told here from the brand&apos;s own point of view.
      </p>

      <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6">
        {products.map((product) => (
          <Link
            key={product.item_code}
            href={`/product/${product.item_code}`}
            className="group rounded-xl border border-stone-200 bg-white p-6 hover:border-emerald-700 hover:shadow-sm transition-all"
          >
            <div className="aspect-square rounded-lg bg-gradient-to-br from-orange-100 to-emerald-100 flex items-center justify-center">
              <span className="text-4xl font-bold text-orange-300">
                {product.item_name.charAt(0)}
              </span>
            </div>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-orange-600">
              {product.category}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-stone-900 group-hover:text-emerald-800 transition-colors">
              {product.item_name}
            </h2>
            <p className="mt-2 text-sm text-stone-600 leading-relaxed">{product.tagline}</p>
            <p className="mt-4 text-sm font-semibold text-emerald-800">
              See formula &amp; lab results &rarr;
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
