import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { PharmaCountryWordmark } from "./PharmaCountryLogo";

export default function SiteFooter() {
  const t = useTranslations("footer");
  const tNav = useTranslations("nav");
  const year = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-10 flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <PharmaCountryWordmark width={140} height={36} />
            <span className="text-sm text-slate-500">{t("tagline")}</span>
          </div>
          <nav className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm font-medium text-slate-600">
            <Link href="/" className="hover:text-slate-900 transition-colors">
              {tNav("home")}
            </Link>
            <Link href="/solutions" className="hover:text-slate-900 transition-colors">
              {tNav("solutionsFull")}
            </Link>
            <Link href="/about" className="hover:text-slate-900 transition-colors">
              {tNav("about")}
            </Link>
            <Link href="/contact" className="hover:text-slate-900 transition-colors">
              {tNav("contact")}
            </Link>
          </nav>
        </div>
        <div className="border-t border-slate-200 pt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm text-slate-500">
          <p>{t("rights", { year })}</p>
          <p>{t("builtOn")}</p>
        </div>
      </div>
    </footer>
  );
}
