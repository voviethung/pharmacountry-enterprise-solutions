import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyDebt, getMyOrders, getMyInvoices, formatVnd } from "@/lib/api";

// Force dynamic rendering — session-gated and calls the real Frappe backend on every request.
export const dynamic = "force-dynamic";

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("dashboard");

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
        <h1 className="text-xl font-bold text-slate-900">
          {t("welcome", { name: session.customerName })}
        </h1>
        <p className="mt-1 text-sm text-slate-500">{t("loggedInAs", { user: session.user })}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label={t("statOutstandingBalance")} value={formatVnd(debt.outstanding_balance)} />
        <StatCard
          label={t("statAvailableCredit")}
          value={debt.available_credit !== null ? formatVnd(debt.available_credit) : "—"}
          sub={
            debt.credit_limit !== null
              ? t("statAvailableCreditSub", { limit: formatVnd(debt.credit_limit) })
              : undefined
          }
        />
        <StatCard
          label={t("statOpenOrders")}
          value={String(openOrders)}
          sub={t("statOpenOrdersSub", { count: orders.length })}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <QuickLink href="/catalog" title={t("quickLinkCatalogTitle")} desc={t("quickLinkCatalogDesc")} />
        <QuickLink href="/orders" title={t("quickLinkOrdersTitle")} desc={t("quickLinkOrdersDesc")} />
        <QuickLink
          href="/invoices"
          title={t("quickLinkInvoicesTitle")}
          desc={t("quickLinkInvoicesDesc", { count: outstandingInvoices })}
        />
        <QuickLink href="/returns" title={t("quickLinkReturnsTitle")} desc={t("quickLinkReturnsDesc")} />
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
