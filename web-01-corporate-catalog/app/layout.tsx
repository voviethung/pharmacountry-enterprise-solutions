import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { getCompanyProfile } from "@/lib/api";
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
  title: "WEB-01 Corporate Catalog Demo",
  description:
    "Enterprise Platform Phase 7 WEB-01 demo — corporate site + product catalog for a real distributor company, served from a guest-only Frappe API.",
};

// The company name/country are used in the header/footer on every page, so they're fetched
// once here rather than duplicated in every page component. If the Frappe backend is
// unreachable, the layout still renders with a clearly-labeled fallback instead of crashing
// the whole site — a real public site should never hard-fail just because one upstream call
// is briefly down.
async function loadHeaderProfile() {
  try {
    const profile = await getCompanyProfile();
    return { companyName: profile.company_name, country: profile.country };
  } catch {
    return { companyName: "Corporate Site (backend unavailable)", country: "" };
  }
}

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const { companyName, country } = await loadHeaderProfile();
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-slate-900">
        <SiteHeader companyName={companyName} />
        <main className="flex-1">{children}</main>
        <SiteFooter companyName={companyName} country={country} />
      </body>
    </html>
  );
}
