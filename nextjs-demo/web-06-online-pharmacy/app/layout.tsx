import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// True Next.js ROOT layout — required to own <html>/<body> for every route. Normally every
// request is redirected by middleware.ts to /vi/... or /en/... before Next.js routing even
// runs, so this layout never renders page content directly — the real page content, header,
// footer, cart provider, and next-intl provider all live one level down in
// app/[locale]/layout.tsx, which cannot declare its own <html>/<body> (nested layouts render
// inside this one). `lang` here is a static default; app/[locale]/layout.tsx corrects
// `document.documentElement.lang` on the client once the real locale is known.
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
      <body className="min-h-full flex flex-col bg-white text-slate-900">{children}</body>
    </html>
  );
}
