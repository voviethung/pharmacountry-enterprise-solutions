import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import LogoutButton from "./LogoutButton";
import LocaleSwitcher from "./LocaleSwitcher";

export default async function PortalHeader({ customerName }: { customerName: string }) {
  const t = await getTranslations("portalHeader");

  const NAV = [
    { href: "/dashboard", label: t("navDashboard") },
    { href: "/catalog", label: t("navCatalog") },
    { href: "/orders", label: t("navOrders") },
    { href: "/invoices", label: t("navInvoices") },
    { href: "/debt", label: t("navDebt") },
    { href: "/returns", label: t("navReturns") },
  ];

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
            {t("brandLabel")}
          </p>
          <p className="text-sm font-medium text-slate-900">{customerName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-indigo-600">
              {item.label}
            </Link>
          ))}
          <LocaleSwitcher />
          <LogoutButton />
        </nav>
      </div>
    </header>
  );
}
