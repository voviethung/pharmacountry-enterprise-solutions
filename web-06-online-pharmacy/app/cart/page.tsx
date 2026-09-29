"use client";

import Link from "next/link";
import { useCart } from "@/components/CartProvider";
import { formatVnd } from "@/lib/api";

export default function CartPage() {
  const { items, updateQty, removeItem, totalPrice } = useCart();

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Your cart is empty</h1>
        <p className="mt-2 text-slate-600">Add a product from the shop to get started.</p>
        <Link
          href="/shop"
          className="mt-6 inline-block rounded-md bg-sky-600 px-6 py-3 font-semibold text-white hover:bg-sky-700"
        >
          Go to Shop
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Your Cart</h1>

      <div className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200">
        {items.map((item) => (
          <div key={item.item_code} className="flex items-center gap-4 p-4">
            <div className="flex-1">
              <p className="font-medium text-slate-900">{item.item_name}</p>
              <p className="text-sm text-slate-500">
                {formatVnd(item.price)} / {item.uom}
              </p>
            </div>
            <input
              type="number"
              min={1}
              max={20}
              value={item.qty}
              onChange={(e) => updateQty(item.item_code, Number(e.target.value) || 1)}
              className="w-16 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              aria-label={`Quantity for ${item.item_name}`}
            />
            <p className="w-28 text-right font-semibold text-slate-900">{formatVnd(item.price * item.qty)}</p>
            <button
              type="button"
              onClick={() => removeItem(item.item_code)}
              className="text-sm text-red-600 hover:underline"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between rounded-lg bg-slate-50 p-4">
        <p className="text-sm text-slate-600">
          Estimated total (indicative — confirmed by our system at checkout)
        </p>
        <p className="text-xl font-bold text-slate-900">{formatVnd(totalPrice)}</p>
      </div>

      <div className="mt-6 flex justify-between">
        <Link href="/shop" className="text-sm font-medium text-sky-700 hover:underline">
          ← Continue shopping
        </Link>
        <Link
          href="/checkout"
          className="rounded-md bg-sky-600 px-6 py-3 font-semibold text-white hover:bg-sky-700"
        >
          Proceed to Checkout
        </Link>
      </div>
    </div>
  );
}
