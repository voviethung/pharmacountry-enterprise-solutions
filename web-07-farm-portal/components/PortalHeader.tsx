import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import LogoutButton from "./LogoutButton";
import LocaleSwitcher from "./LocaleSwitcher";

const NAV = [
  { href: "/dashboard", key: "dashboard" },
  { href: "/orders", key: "orders" },
  { href: "/visits", key: "visits" },
  { href: "/recommendations", key: "recommendations" },
  { href: "/history", key: "history" },
] as const;

export default function PortalHeader({ customerName }: { customerName: string }) {
  const t = useTranslations("portalHeader");

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            {t("tag")}
          </p>
          <p className="text-sm font-medium text-slate-900">{customerName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-emerald-700">
              {t(`nav.${item.key}`)}
            </Link>
          ))}
          <LocaleSwitcher />
          <LogoutButton />
        </nav>
      </div>
    </header>
  );
}
