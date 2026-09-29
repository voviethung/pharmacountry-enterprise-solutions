export default function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-slate-500 space-y-1">
        <p>
          Demo Pharmacy Chain Co. — this is a demo storefront (ENTERPRISE_PLATFORM WEB-06, Phase 7).
          All products, prices, stock levels, and orders are real ERP records in a demo instance
          (Golden Demo #23, Store A), not a real commercial pharmacy.
        </p>
        <p>
          Every product on this site is over-the-counter (OTC) — this demo does not implement
          prescription upload or pharmacist verification (see this app&apos;s README for why).
        </p>
        <p>
          Payment: Cash on Delivery only — this demo does not integrate any real payment gateway. No
          card details are ever collected by this site.
        </p>
      </div>
    </footer>
  );
}
