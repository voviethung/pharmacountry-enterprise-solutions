import Link from "next/link";
import type { Metadata } from "next";
import { getCatalogItems, formatPrice } from "@/lib/api";

export const metadata: Metadata = {
  title: "Product Catalog",
};

export default async function CatalogPage() {
  const items = await getCatalogItems();

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Product Catalog</h1>
      <p className="mt-3 max-w-2xl text-slate-600">
        Live product data served from our ERP system&apos;s public catalog API.
      </p>

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
                {formatPrice(item.price, item.currency)}
              </span>
              <span className="text-xs text-slate-400">{item.item_code}</span>
            </div>
          </Link>
        ))}
      </div>

      {items.length === 0 && (
        <p className="mt-10 text-slate-500">No products are currently published.</p>
      )}
    </div>
  );
}
