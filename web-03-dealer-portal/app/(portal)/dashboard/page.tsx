import Link from "next/link";
import { requireSession } from "@/lib/auth";
import { getMyDebt, getMyOrders, getMyInvoices, formatVnd } from "@/lib/api";

export default async function DashboardPage() {
  const session = await requireSession();
  const [debt, orders, invoices] = await Promise.all([
    getMyDebt(session.frappeSid),
    getMyOrders(session.frappeSid),
    getMyInvoices(session.frappeSid),
  ]);

  const openOrders = orders.filter((o) => o.status !== "Closed" && o.status !== "Cancelled").length;
  const outstandingInvoices = invoices.filter((i) => i.outstanding_amount > 0).length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Welcome back, {session.customerName}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Logged in as {session.user}. Territory-scoped, dealer-scoped data only — never another
          dealer&apos;s.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Outstanding balance" value={formatVnd(debt.outstanding_balance)} />
        <StatCard
          label="Available credit"
          value={debt.available_credit !== null ? formatVnd(debt.available_credit) : "—"}
          sub={debt.credit_limit !== null ? `of ${formatVnd(debt.credit_limit)} limit` : undefined}
        />
        <StatCard label="Open orders" value={String(openOrders)} sub={`${orders.length} total`} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <QuickLink href="/catalog" title="Browse catalog" desc="Your own negotiated pricing and live stock." />
        <QuickLink href="/orders" title="Place a new order" desc="Order against your own catalog and price list." />
        <QuickLink
          href="/invoices"
          title="My invoices"
          desc={`${outstandingInvoices} invoice(s) with an outstanding balance.`}
        />
        <QuickLink href="/returns" title="Returns" desc="File a return against one of your own deliveries." />
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
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-indigo-300 hover:shadow"
    >
      <p className="font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{desc}</p>
    </Link>
  );
}
