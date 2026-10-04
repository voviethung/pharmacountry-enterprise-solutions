import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// True Next.js ROOT layout — required to own <html>/<body> for every route. The REAL page
// content, header, and next-intl provider all live one level down in app/[locale]/layout.tsx,
// which cannot declare its own <html>/<body> (nested layouts render inside this one). `lang` here
// is a static default; app/[locale]/layout.tsx corrects `document.documentElement.lang` on the
// client once the real locale is known. In normal operation this layout's own children are never
// actually rendered for an un-prefixed path — middleware.ts redirects every un-prefixed request to
// /vi/... or /en/... before Next.js routing ever runs — but the root layout itself must still
// exist to host <html>/<body> for the [locale] segment beneath it.
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
    <html lang="vi" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-[#f7f8fa] text-[#14181f]">{children}</body>
    </html>
  );
}
