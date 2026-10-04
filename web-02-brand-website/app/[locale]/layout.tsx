import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { getBrandProfile } from "@/lib/api";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import HtmlLangSync from "@/components/HtmlLangSync";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("homeTitle"),
    description: t("homeDescription"),
  };
}

// This layout also calls the real Frappe backend directly (see loadHeaderProfile below) on
// every request. Force dynamic rendering here too so it (and any future page that doesn't set
// this itself) never gets baked into a static snapshot taken at Docker build time, when the
// backend may not even be reachable.
export const dynamic = "force-dynamic";

// The company name/country are used in the header/footer on every page, so they're fetched
// once here rather than duplicated in every page component. If the Frappe backend is
// unreachable, the layout still renders with a clearly-labeled fallback instead of crashing
// the whole site — a real public site should never hard-fail just because one upstream call
// is briefly down. (Same defensive pattern as WEB-01's layout.tsx.)
async function loadHeaderProfile() {
  try {
    const profile = await getBrandProfile();
    return { companyName: profile.company_name, country: profile.country };
  } catch {
    return { companyName: "Brand Site (backend unavailable)", country: "" };
  }
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  // Enables static rendering for anything in this tree that CAN be static; the pages
  // themselves still force dynamic rendering for their own real backend calls (see each
  // page's own `export const dynamic = "force-dynamic"` comment).
  setRequestLocale(locale);

  const { companyName, country } = await loadHeaderProfile();

  return (
    <NextIntlClientProvider>
      <HtmlLangSync locale={locale} />
      <SiteHeader companyName={companyName} />
      <main className="flex-1">{children}</main>
      <SiteFooter companyName={companyName} country={country} />
    </NextIntlClientProvider>
  );
}
