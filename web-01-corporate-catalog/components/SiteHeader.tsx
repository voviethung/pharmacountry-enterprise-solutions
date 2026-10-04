import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import LocaleSwitcher from "./LocaleSwitcher";

export default function SiteHeader({ companyName }: { companyName: string }) {
  const t = useTranslations("nav");

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-900 text-white font-semibold">
            {companyName.charAt(0)}
          </span>
          <span className="font-semibold text-slate-900 group-hover:text-slate-700 transition-colors">
            {companyName}
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium text-slate-600">
          <Link href="/" className="hover:text-slate-900 transition-colors">
            {t("home")}
          </Link>
          <Link href="/catalog" className="hover:text-slate-900 transition-colors">
            {t("catalog")}
          </Link>
          <LocaleSwitcher />
        </nav>
      </div>
    </header>
  );
}
