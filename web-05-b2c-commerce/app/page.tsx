import Link from "next/link";
import { getStorefrontCatalog, formatVnd } from "@/lib/api";

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  let items: Awaited<ReturnType<typeof getStorefrontCatalog>> = [];
  try {
    items = await getStorefrontCatalog();
  } catch {
    items = [];
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 space-y-12">
      <section className="text-center space-y-4">
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
          WEB-05 — B2C Commerce Demo
        </p>
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
          Buy Vitamin C and Facial Cleanser direct from Demo Consumer Distribution Co.
        </h1>
        <p className="mx-auto max-w-2xl text-slate-600">
          Browse real products, add them to your cart, and check out as a guest — no account
          needed. Every price you see is real, live data from our ERP system; the price you&apos;re
          actually charged is confirmed by our system at checkout.
        </p>
        <div>
          <Link
            href="/shop"
            className="inline-block rounded-md bg-emerald-600 px-6 py-3 font-semibold text-white hover:bg-emerald-700"
          >
            Shop Now
          </Link>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-slate-900">Featured Products</h2>
        {items.length === 0 ? (
          <p className="text-slate-500">Catalog is temporarily unavailable — please try again shortly.</p>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2">
            {items.map((item) => (
              <Link
                key={item.item_code}
                href="/shop"
                className="block rounded-lg border border-slate-200 p-5 hover:border-emerald-400 hover:shadow-sm"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
                  {item.category}
                </p>
                <h3 className="mt-1 text-lg font-semibold text-slate-900">{item.item_name}</h3>
                <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                <p className="mt-3 text-lg font-bold text-slate-900">
                  {formatVnd(item.price)}{" "}
                  <span className="text-sm font-normal text-slate-500">/ {item.uom}</span>
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg bg-slate-50 p-6 text-sm text-slate-600">
        <p className="font-semibold text-slate-800">How ordering works on this demo</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>No account or login required — add items to your cart and check out as a guest.</li>
          <li>Payment is Cash on Delivery only — no real payment gateway is used anywhere on this site.</li>
          <li>
            After checkout you&apos;ll get an order reference — use it with your phone number on the
            <Link href="/track" className="mx-1 text-emerald-700 underline">
              Track Order
            </Link>
            page to check your order&apos;s status.
          </li>
        </ul>
      </section>
    </div>
  );
}
