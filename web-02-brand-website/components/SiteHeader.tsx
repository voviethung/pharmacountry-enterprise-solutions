import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import LocaleSwitcher from "./LocaleSwitcher";

export default function SiteHeader({ companyName }: { companyName: string }) {
  const t = useTranslations("nav");

  return (
    <header className="border-b border-stone-200 bg-[#fffaf0]/90 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2 group shrink-0">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-800 text-white font-semibold">
            {companyName.charAt(0)}
          </span>
          <span className="font-semibold text-stone-900 group-hover:text-emerald-800 transition-colors">
            {companyName}
          </span>
        </Link>
        <nav className="flex items-center gap-3 sm:gap-6 text-sm font-medium text-stone-600">
          <Link href="/" className="hover:text-emerald-800 transition-colors">
            {t("home")}
          </Link>
          <Link href="/products" className="hover:text-emerald-800 transition-colors">
            {t("products")}
          </Link>
          <Link href="/our-story" className="hover:text-emerald-800 transition-colors">
            {t("ourStory")}
          </Link>
          <Link
            href="/where-to-buy"
            className="rounded-full bg-orange-600 px-4 py-2 text-white hover:bg-orange-700 transition-colors"
          >
            {t("whereToBuy")}
          </Link>
          <LocaleSwitcher />
        </nav>
      </div>
    </header>
  );
}
