"use client";

import { usePathname, useRouter } from "@/i18n/navigation";
import { useParams } from "next/navigation";
import type { Locale } from "@/i18n/routing";

// Manual VI/EN toggle in the header, independent of whatever middleware.ts's CF-IPCountry/
// Accept-Language detection picked automatically — a visitor can always override it. Swaps the
// locale segment of the CURRENT path (via next-intl's own locale-aware navigation helpers), so
// switching language on e.g. /en/catalog lands on /vi/catalog, not back at the home page.
//
// Colors follow this app's own existing palette (slate-900 is already this app's primary accent
// — see the SiteHeader logo badge and the homepage's primary CTA button — rather than
// hub-landing's PharmaCountry green, which has no equivalent here).
export default function LocaleSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams();
  const activeLocale = params.locale as Locale;

  function setLocale(locale: Locale) {
    router.replace(pathname, { locale });
  }

  return (
    <div className="flex items-center gap-1 rounded-full border border-slate-200 p-0.5 text-xs font-semibold">
      <button
        type="button"
        onClick={() => setLocale("vi")}
        aria-current={activeLocale === "vi"}
        className={`rounded-full px-2.5 py-1 transition-colors ${
          activeLocale === "vi"
            ? "bg-slate-900 text-white"
            : "text-slate-500 hover:text-slate-900"
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
            ? "bg-slate-900 text-white"
            : "text-slate-500 hover:text-slate-900"
        }`}
      >
        EN
      </button>
    </div>
  );
}
