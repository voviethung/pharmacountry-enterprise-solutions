import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { PharmaCountryMark, PharmaCountryWordmark } from "./PharmaCountryLogo";
import LocaleSwitcher from "./LocaleSwitcher";

export default function SiteHeader() {
  const t = useTranslations("nav");
  const tBrand = useTranslations("brand");

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-3.5 flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2.5 group shrink-0">
          {/* Real PharmaCountry brand mark/wordmark, ported from the sibling project's own
              brand-assets (see components/PharmaCountryLogo.tsx) — not a reinvented logo. */}
          <PharmaCountryMark size={34} className="sm:hidden" />
          <PharmaCountryWordmark width={150} height={40} className="hidden sm:block" />
          <span className="hidden lg:inline text-[11px] font-semibold uppercase tracking-wide text-[#158A57] border-l border-slate-200 pl-2.5 ml-0.5">
            {tBrand("subBrand")}
          </span>
        </Link>
        <nav className="flex items-center gap-3 sm:gap-6 text-sm font-medium text-slate-600">
          <Link href="/" className="hover:text-slate-900 transition-colors">
            {t("home")}
          </Link>
          <Link href="/solutions" className="hover:text-slate-900 transition-colors">
            <span className="sm:hidden">{t("solutions")}</span>
            <span className="hidden sm:inline">{t("solutionsFull")}</span>
          </Link>
          <Link href="/about" className="hover:text-slate-900 transition-colors">
            {t("about")}
          </Link>
          <Link href="/contact" className="hover:text-slate-900 transition-colors">
            {t("contact")}
          </Link>
          <LocaleSwitcher />
        </nav>
      </div>
    </header>
  );
}
