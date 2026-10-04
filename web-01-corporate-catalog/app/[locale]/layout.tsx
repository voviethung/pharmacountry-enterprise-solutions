import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { getCompanyProfile } from "@/lib/api";
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

// The company name/country are used in the header/footer on every page, so they're fetched
// once here rather than duplicated in every page component. If the Frappe backend is
// unreachable, the layout still renders with a clearly-labeled fallback instead of crashing
// the whole site — a real public site should never hard-fail just because one upstream call
// is briefly down.
async function loadHeaderProfile(locale: string) {
  try {
    const profile = await getCompanyProfile();
    return { companyName: profile.company_name, country: profile.country };
  } catch {
    const t = await getTranslations({ locale, namespace: "layout" });
    return { companyName: t("fallbackCompanyName"), country: "" };
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

  const { companyName, country } = await loadHeaderProfile(locale);

  return (
    <NextIntlClientProvider>
      <HtmlLangSync locale={locale} />
      <SiteHeader companyName={companyName} />
      <main className="flex-1">{children}</main>
      <SiteFooter companyName={companyName} country={country} />
    </NextIntlClientProvider>
  );
}
