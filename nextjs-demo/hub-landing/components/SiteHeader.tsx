import { useLocale, useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { PharmaCountryMark, PharmaCountryWordmark } from "./PharmaCountryLogo";
import LocaleSwitcher from "./LocaleSwitcher";

export default function SiteHeader() {
  const locale = useLocale();
  const t = useTranslations("nav");
  const tBrand = useTranslations("brand");
  const labels =
    locale === "vi"
      ? { products: "Sản phẩm", industries: "Ngành", platform: "Nền tảng" }
      : { products: "Products", industries: "Industries", platform: "Platform" };

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-3.5 flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2.5 group shrink-0">
          <PharmaCountryMark size={34} className="sm:hidden" />
          <PharmaCountryWordmark width={150} height={40} className="hidden sm:block" />
          <span className="hidden lg:inline text-[11px] font-semibold uppercase tracking-wide text-[#158A57] border-l border-slate-200 pl-2.5 ml-0.5">
            {tBrand("subBrand")}
          </span>
        </Link>
        <nav className="flex items-center gap-3 sm:gap-5 text-sm font-medium text-slate-600">
          <Link href="/products" className="hover:text-slate-900 transition-colors">
            {labels.products}
          </Link>
          <Link href="/solutions" className="hidden md:inline hover:text-slate-900 transition-colors">
            {labels.industries}
          </Link>
          <Link href="/platform" className="hidden lg:inline hover:text-slate-900 transition-colors">
            {labels.platform}
          </Link>
          <Link href="/pricing" className="hover:text-slate-900 transition-colors">
            {t("pricing")}
          </Link>
          <Link href="/contact" className="hidden sm:inline hover:text-slate-900 transition-colors">
            {t("contact")}
          </Link>
          <LocaleSwitcher />
        </nav>
      </div>
    </header>
  );
}
