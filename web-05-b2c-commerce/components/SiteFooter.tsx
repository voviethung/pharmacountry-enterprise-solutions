export default function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-slate-500 space-y-1">
        <p>
          Demo Consumer Distribution Co. — this is a demo storefront (ENTERPRISE_PLATFORM WEB-05,
          Phase 7). All products, prices, and orders are real ERP records in a demo instance, not a
          real commercial store.
        </p>
        <p>
          Payment: Cash on Delivery only — this demo does not integrate any real payment gateway.
          No card details are ever collected by this site.
        </p>
      </div>
    </footer>
  );
}
