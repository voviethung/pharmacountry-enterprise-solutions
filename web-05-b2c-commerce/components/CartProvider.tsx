"use client";

// Client-side shopping cart — a plain React Context persisted to this browser's own
// localStorage. Deliberately NOT a server-side cart/session: there is nothing here Frappe needs to
// know about until the guest actually checks out (see b2c_commerce_api.py's own module docstring —
// `place_web_order` is genuinely stateless-per-request). The price/name shown here are a snapshot
// taken from the real catalog at "Add to Cart" time purely for DISPLAY — the real, authoritative
// price is always recomputed server-side at checkout from the current Item Price, never trusted
// from this cart (see CheckoutForm's own note to the same effect). This is a deliberate, disclosed
// simplification appropriate for a demo (no cross-device cart, cleared if browser storage is
// cleared) — documented in this app's own README.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export interface CartItem {
  item_code: string;
  item_name: string;
  price: number;
  currency: string;
  uom: string;
  qty: number;
}

interface CartContextValue {
  items: CartItem[];
  addItem: (item: Omit<CartItem, "qty">, qty: number) => void;
  updateQty: (itemCode: string, qty: number) => void;
  removeItem: (itemCode: string) => void;
  clearCart: () => void;
  totalQty: number;
  totalPrice: number;
}

const CartContext = createContext<CartContextValue | null>(null);

const STORAGE_KEY = "web05-cart-v1";
const MAX_QTY_PER_LINE = 20; // mirrors the backend's own _MAX_QTY_PER_LINE — a UI-side sanity bound
// only; the real enforcement (including the real live stock check) happens server-side at checkout.

function loadFromStorage(): CartItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveToStorage(items: CartItem[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Private browsing / blocked storage — the cart simply won't persist across reloads. Not
    // fatal for a demo; checkout itself doesn't depend on storage succeeding.
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // One-time client-only hydration from localStorage (server-rendered HTML always starts with an
    // empty cart, since localStorage doesn't exist during SSR/static generation). This intentionally
    // triggers exactly one extra render right after mount — the canonical, narrow exception to the
    // "don't setState in an effect" guideline for reading browser-only storage on first mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItems(loadFromStorage());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveToStorage(items);
  }, [items, hydrated]);

  const addItem: CartContextValue["addItem"] = (item, qty) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.item_code === item.item_code);
      if (existing) {
        const newQty = Math.min(existing.qty + qty, MAX_QTY_PER_LINE);
        return prev.map((i) => (i.item_code === item.item_code ? { ...i, qty: newQty } : i));
      }
      return [...prev, { ...item, qty: Math.min(qty, MAX_QTY_PER_LINE) }];
    });
  };

  const updateQty: CartContextValue["updateQty"] = (itemCode, qty) => {
    setItems((prev) =>
      prev
        .map((i) => (i.item_code === itemCode ? { ...i, qty: Math.max(0, Math.min(qty, MAX_QTY_PER_LINE)) } : i))
        .filter((i) => i.qty > 0)
    );
  };

  const removeItem: CartContextValue["removeItem"] = (itemCode) => {
    setItems((prev) => prev.filter((i) => i.item_code !== itemCode));
  };

  const clearCart = () => setItems([]);

  const totalQty = useMemo(() => items.reduce((sum, i) => sum + i.qty, 0), [items]);
  const totalPrice = useMemo(() => items.reduce((sum, i) => sum + i.qty * i.price, 0), [items]);

  return (
    <CartContext.Provider value={{ items, addItem, updateQty, removeItem, clearCart, totalQty, totalPrice }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within a CartProvider");
  return ctx;
}
