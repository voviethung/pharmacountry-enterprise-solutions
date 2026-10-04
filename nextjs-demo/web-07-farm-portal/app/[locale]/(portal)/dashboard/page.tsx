import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { requireSession } from "@/lib/auth";
import { getMyOrders, getMyTechnicalVisits, getMyRecommendations, formatVnd } from "@/lib/api";

// Force dynamic rendering — login-gated page that calls the real Frappe backend with a
// per-session farm scope on every request. Without this, Next.js could prerender it once at
// Docker build time (no session, no backend reachable) and serve that stale/broken snapshot to
// every visitor forever. A login-gated page can never be static.
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
  const [orders, visits, recommendations] = await Promise.all([
    getMyOrders(session.frappeSid),
    getMyTechnicalVisits(session.frappeSid),
    getMyRecommendations(session.frappeSid),
  ]);

  const openOrders = orders.filter((o) => o.status !== "Closed" && o.status !== "Cancelled").length;
  const upcomingFollowUps = visits.filter((v) => v.follow_up_date).length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-slate-900">
          {t("welcome", { name: session.customerName })}
        </h1>
        <p className="mt-1 text-sm text-slate-500">{t("loggedInAs", { user: session.user })}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label={t("stats.ordersPlaced")}
          value={String(orders.length)}
          sub={t("stats.ordersOpen", { count: openOrders })}
        />
        <StatCard
          label={t("stats.technicalVisits")}
          value={String(visits.length)}
          sub={t("stats.followUps", { count: upcomingFollowUps })}
        />
        <StatCard
          label={t("stats.recommendations")}
          value={String(recommendations.length)}
          sub={t("stats.recommendationsSub")}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <QuickLink
          href="/orders"
          title={t("quickLinks.placeOrder.title")}
          desc={t("quickLinks.placeOrder.desc")}
        />
        <QuickLink
          href="/visits"
          title={t("quickLinks.visits.title")}
          desc={t("quickLinks.visits.desc")}
        />
        <QuickLink
          href="/recommendations"
          title={t("quickLinks.recommendations.title")}
          desc={t("quickLinks.recommendations.desc")}
        />
        <QuickLink
          href="/history"
          title={t("quickLinks.history.title")}
          desc={t("quickLinks.history.desc")}
        />
      </div>

      {orders.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-slate-900">{t("mostRecentOrder")}</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="font-medium text-slate-900">{orders[0].name}</p>
            <p className="mt-1 text-sm text-slate-500">
              {orders[0].transaction_date} · {orders[0].status} · {formatVnd(orders[0].grand_total)}
            </p>
          </div>
        </div>
      )}
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
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-emerald-300 hover:shadow"
    >
      <p className="font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{desc}</p>
    </Link>
  );
}
