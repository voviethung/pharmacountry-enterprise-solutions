"use client";

import Link from "next/link";
import { useCart } from "./CartProvider";

export default function SiteHeader() {
  const { totalQty } = useCart();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-lg font-semibold text-slate-900">
          Demo Consumer Distribution Co.{" "}
          <span className="text-sm font-normal text-slate-500">— Online Store</span>
        </Link>
        <nav className="flex items-center gap-5 text-sm font-medium text-slate-700">
          <Link href="/shop" className="hover:text-emerald-700">
            Shop
          </Link>
          <Link href="/track" className="hover:text-emerald-700">
            Track Order
          </Link>
          <Link href="/cart" className="flex items-center gap-1 hover:text-emerald-700">
            Cart
            <span className="inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-emerald-600 px-1.5 py-0.5 text-xs font-semibold text-white">
              {totalQty}
            </span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
