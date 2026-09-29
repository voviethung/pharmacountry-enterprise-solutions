import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Supplier Portal — Demo Ingredient Trading Co.",
  description:
    "Enterprise Platform Phase 7 WEB-04 demo — an authenticated Supplier/RFQ portal: real per-supplier RFQs, quotations, purchase orders, deliveries, documents and qualification status, backed by real Frappe session login and per-supplier permission scoping.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-[#f7f8fa] text-[#14181f]">{children}</body>
    </html>
  );
}
