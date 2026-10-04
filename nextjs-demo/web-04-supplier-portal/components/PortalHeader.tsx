import { useTranslations, useLocale } from "next-intl";
import { Link } from "@/i18n/navigation";
import LogoutButton from "./LogoutButton";
import LocaleSwitcher from "./LocaleSwitcher";

const NAV = [
  { href: "/dashboard", key: "dashboard" },
  { href: "/rfqs", key: "rfqs" },
  { href: "/quotations", key: "quotations" },
  { href: "/purchase-orders", key: "purchaseOrders" },
  { href: "/deliveries", key: "deliveries" },
  { href: "/qualification", key: "qualification" },
  { href: "/documents", key: "documents" },
] as const;

export default function PortalHeader({ supplierName }: { supplierName: string }) {
  const t = useTranslations("portalHeader");
  const locale = useLocale();
  return (
    <div>
      <div className="border-b border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-1.5">
          <a
            href={`https://pharmacountry.vn/${locale}`}
            className="inline-block text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
          >
            {t("backToHub")}
          </a>
        </div>
      </div>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
            {t("label")}
          </p>
          <p className="text-sm font-medium text-slate-900">{supplierName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-teal-700">
              {t(`nav.${item.key}`)}
            </Link>
          ))}
          <LocaleSwitcher />
          <LogoutButton />
        </nav>
        </div>
      </header>
    </div>
  );
}
