import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getItemDetail, formatPrice } from "@/lib/api";

type Params = Promise<{ itemCode: string }>;

async function loadItem(itemCode: string) {
  try {
    return await getItemDetail(itemCode);
  } catch {
    // getItemDetail() throws whenever the backend's guest API returns non-200 — which is
    // exactly what public_api.get_item_detail() does for any item_code outside its real,
    // data-driven safe set (see that function's docstring). Render Next.js's own 404 rather
    // than leaking the backend error detail to the visitor.
    return null;
  }
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { itemCode } = await params;
  const item = await loadItem(itemCode);
  return { title: item ? item.item_name : "Product not found" };
}

export default async function ProductDetailPage({ params }: { params: Params }) {
  const { itemCode } = await params;
  const item = await loadItem(itemCode);
  if (!item) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link href="/catalog" className="text-sm font-medium text-slate-500 hover:text-slate-900">
        &larr; Back to catalog
      </Link>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-10 items-start">
        <div className="aspect-square rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
          <span className="text-6xl font-bold text-slate-300">
            {item.item_name.charAt(0)}
          </span>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
            {item.category}
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">{item.item_name}</h1>
          <p className="mt-4 text-lg font-semibold text-slate-900">
            {formatPrice(item.price, item.currency)}
          </p>
          <p className="mt-6 text-slate-600 leading-relaxed">{item.description}</p>

          <dl className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-200 pt-6 text-sm">
            <div>
              <dt className="text-slate-400">Product Code</dt>
              <dd className="mt-1 font-medium text-slate-900">{item.item_code}</dd>
            </div>
            <div>
              <dt className="text-slate-400">Unit</dt>
              <dd className="mt-1 font-medium text-slate-900">{item.uom}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
