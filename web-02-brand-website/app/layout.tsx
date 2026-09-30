import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { getBrandProfile } from "@/lib/api";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Demo Supplement Co. — Vitamin C Effervescent Tablets",
  description:
    "Enterprise Platform Phase 7 WEB-02 demo — a consumer brand site for a demo supplement manufacturer, telling the brand's own story with live demo formula and lab-verification data generated and managed by the connected ERP system, served from a guest-only Frappe API.",
};

// This root layout also calls the real Frappe backend directly (see loadHeaderProfile below)
// on every request. Force dynamic rendering here too so it (and any future page that doesn't
// set this itself) never gets baked into a static snapshot taken at Docker build time, when
// the backend may not even be reachable.
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

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const { companyName, country } = await loadHeaderProfile();
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#fffaf0] text-stone-900">
        <SiteHeader companyName={companyName} />
        <main className="flex-1">{children}</main>
        <SiteFooter companyName={companyName} country={country} />
      </body>
    </html>
  );
}
