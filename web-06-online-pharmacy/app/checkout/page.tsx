"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useCart } from "@/components/CartProvider";
import { formatVnd, type OrderConfirmation } from "@/lib/api";

const CONFIRMATION_STORAGE_KEY = "web06-last-order";

export default function CheckoutPage() {
  const { items, totalPrice, clearCart } = useCart();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Your cart is empty</h1>
        <Link href="/shop" className="mt-4 inline-block text-sky-700 underline">
          Go to Shop
        </Link>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: items.map((i) => ({ item_code: i.item_code, qty: i.qty })),
          contact: {
            full_name: fullName,
            phone,
            email: email || undefined,
            address_line1: addressLine1,
            city,
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Checkout failed. Please try again.");
        setSubmitting(false);
        return;
      }
      const order = data as OrderConfirmation;
      try {
        window.sessionStorage.setItem(CONFIRMATION_STORAGE_KEY, JSON.stringify(order));
      } catch {
        // sessionStorage unavailable — confirmation page will just show a generic message.
      }
      clearCart();
      router.push("/confirmation");
    } catch {
      setError("Could not reach the server. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Checkout</h1>
      <p className="mt-1 text-sm text-slate-600">
        No account needed — just tell us where to deliver your order.
      </p>

      <div className="mt-6 rounded-lg bg-slate-50 p-4 text-sm">
        <p className="font-semibold text-slate-800">Order summary</p>
        <ul className="mt-2 space-y-1">
          {items.map((i) => (
            <li key={i.item_code} className="flex justify-between">
              <span>
                {i.item_name} × {i.qty}
              </span>
              <span>{formatVnd(i.price * i.qty)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>Estimated total</span>
          <span>{formatVnd(totalPrice)}</span>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          This is an estimate. The real, final price — and the specific real, non-expired batch your
          order is filled from — is computed by our system at the moment you submit this order. It is
          never taken from this page, and an already-expired batch can never be used to fill an order.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Full name</label>
          <input
            required
            maxLength={120}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Phone number</label>
          <input
            required
            type="tel"
            maxLength={20}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="e.g. 0912345678"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
          <p className="mt-1 text-xs text-slate-500">
            Keep this handy — you&apos;ll need it (with your order reference) to track your order later.
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Email (optional)</label>
          <input
            type="email"
            maxLength={200}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Delivery address</label>
          <input
            required
            maxLength={200}
            value={addressLine1}
            onChange={(e) => setAddressLine1(e.target.value)}
            placeholder="Street address"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">City / Province</label>
          <input
            required
            maxLength={100}
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>

        <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900">
          Payment method: <strong>Cash on Delivery</strong> — the only option this demo supports. No
          card details or real payment information is ever collected by this site.
        </div>

        {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-sky-600 px-6 py-3 font-semibold text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? "Placing order…" : "Place Order"}
        </button>
      </form>
    </div>
  );
}
