import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { CartProvider } from "@/components/CartProvider";
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
    title: t("title"),
    description: t("description"),
  };
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
  // themselves still force dynamic rendering for their own real backend calls (see each page's
  // own `export const dynamic = "force-dynamic"` comment).
  setRequestLocale(locale);

  return (
    <NextIntlClientProvider>
      <HtmlLangSync locale={locale} />
      {/* CartProvider stays here, inside the locale tree but OUTSIDE/around the actual page
          content exactly as it wrapped children in the old single app/layout.tsx. Its
          localStorage key ("web05-cart-v1", see CartProvider.tsx) is not locale-scoped, so a
          cart built up on /vi/shop is still there after switching to /en/shop — switching locale
          only swaps the URL/translations, never the cart's own React state or storage key. */}
      <CartProvider>
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </CartProvider>
    </NextIntlClientProvider>
  );
}
