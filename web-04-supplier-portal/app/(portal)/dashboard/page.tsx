import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyRfqs, getMyQuotations, getMyPurchaseOrders, getMyQualificationStatus } from "@/lib/api";

// Force dynamic rendering — this is a login-gated page that fetches this supplier's own live
// data from Frappe on every request. Without this, Next.js could prerender it once at Docker
// build time (before the backend is even reachable, and with no real session) and serve that
// stale/broken snapshot to every visitor forever.
export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const session = await requireSession();
  const [rfqs, quotations, purchaseOrders, qualification] = await Promise.all([
    getMyRfqs(session.frappeSid),
    getMyQuotations(session.frappeSid),
    getMyPurchaseOrders(session.frappeSid),
    getMyQualificationStatus(session.frappeSid),
  ]);

  const pendingRfqs = rfqs.filter((r) => r.quote_status === "Pending").length;
  const openPurchaseOrders = purchaseOrders.filter((p) => p.status !== "Closed" && p.status !== "Cancelled").length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Welcome back, {session.supplierName}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Logged in as {session.user}. Supplier-scoped data only — never another supplier&apos;s.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard label="RFQ invitations" value={String(rfqs.length)} sub={`${pendingRfqs} awaiting your response`} />
        <StatCard label="Quotations submitted" value={String(quotations.length)} />
        <StatCard label="Purchase orders" value={String(purchaseOrders.length)} sub={`${openPurchaseOrders} open`} />
        <StatCard
          label="Qualification status"
          value={qualification.quality_status}
          sub={qualification.is_critical_supplier ? "Critical supplier" : undefined}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <QuickLink href="/rfqs" title="My RFQs" desc="RFQs you've been invited to respond to." />
        <QuickLink href="/quotations" title="My Quotations" desc="Every quotation you've submitted, RFQ-linked or not." />
        <QuickLink href="/purchase-orders" title="My Purchase Orders" desc="Purchase Orders issued to you." />
        <QuickLink href="/deliveries" title="My Deliveries" desc="Your shipment/delivery and QC status." />
      </div>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function QuickLink({ href, title, desc }: { href: string; title: string; desc: string }) {
  return (
    <Link
      href={href}
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-teal-300 hover:shadow"
    >
      <p className="font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{desc}</p>
    </Link>
  );
}
