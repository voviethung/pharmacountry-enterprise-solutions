"use client";

import { usePathname, useRouter } from "@/i18n/navigation";
import { useParams } from "next/navigation";
import type { Locale } from "@/i18n/routing";

// Manual VI/EN toggle in the header, independent of whatever middleware.ts's CF-IPCountry/
// Accept-Language detection picked automatically — a visitor can always override it. Swaps the
// locale segment of the CURRENT path (via next-intl's own locale-aware navigation helpers), so
// switching language on e.g. /en/products lands on /vi/products, not back at the home page.
export default function LocaleSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams();
  const activeLocale = params.locale as Locale;

  function setLocale(locale: Locale) {
    router.replace(pathname, { locale });
  }

  return (
    <div className="flex items-center gap-1 rounded-full border border-stone-300 p-0.5 text-xs font-semibold">
      <button
        type="button"
        onClick={() => setLocale("vi")}
        aria-current={activeLocale === "vi"}
        className={`rounded-full px-2.5 py-1 transition-colors ${
          activeLocale === "vi"
            ? "bg-emerald-800 text-white"
            : "text-stone-500 hover:text-stone-900"
        }`}
      >
        VI
      </button>
      <button
        type="button"
        onClick={() => setLocale("en")}
        aria-current={activeLocale === "en"}
        className={`rounded-full px-2.5 py-1 transition-colors ${
          activeLocale === "en"
            ? "bg-emerald-800 text-white"
            : "text-stone-500 hover:text-stone-900"
        }`}
      >
        EN
      </button>
    </div>
  );
}
