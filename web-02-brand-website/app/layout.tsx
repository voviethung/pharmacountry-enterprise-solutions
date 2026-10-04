import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// True Next.js ROOT layout — required to own <html>/<body> for every route, including the
// top-level redirect stubs (app/page.tsx, app/our-story/page.tsx, app/product/page.tsx,
// app/product/[item_code]/page.tsx, app/products/page.tsx, app/where-to-buy/page.tsx don't
// exist at this level anymore — they moved under app/[locale]/...) that exist only as a
// defensive fallback in case a request ever reaches this app without a locale prefix (normally
// impossible — middleware.ts redirects every un-prefixed path to /vi/... or /en/... before
// Next.js routing even runs). The REAL page content, header, footer, and next-intl provider all
// live one level down in app/[locale]/layout.tsx, which cannot declare its own <html>/<body>
// (nested layouts render inside this one). `lang` here is a static default; app/[locale]/
// layout.tsx corrects `document.documentElement.lang` on the client once the real locale is
// known.
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="vi"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#fffaf0] text-stone-900">{children}</body>
    </html>
  );
}
