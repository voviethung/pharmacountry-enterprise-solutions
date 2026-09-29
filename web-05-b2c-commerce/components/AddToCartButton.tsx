"use client";

import { useState } from "react";
import { useCart } from "./CartProvider";
import type { StorefrontItem } from "@/lib/api";

export default function AddToCartButton({ item }: { item: StorefrontItem }) {
  const { addItem } = useCart();
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const outOfStock = item.available_qty <= 0;

  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        min={1}
        max={20}
        value={qty}
        disabled={outOfStock}
        onChange={(e) => setQty(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
        className="w-16 rounded-md border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-100"
        aria-label={`Quantity for ${item.item_name}`}
      />
      <button
        type="button"
        disabled={outOfStock}
        onClick={() => {
          addItem(
            {
              item_code: item.item_code,
              item_name: item.item_name,
              price: item.price,
              currency: item.currency,
              uom: item.uom,
            },
            qty
          );
          setAdded(true);
          setTimeout(() => setAdded(false), 1500);
        }}
        className="flex-1 rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {outOfStock ? "Out of stock" : added ? "Added ✓" : "Add to Cart"}
      </button>
    </div>
  );
}
