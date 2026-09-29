import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description: "What ENTERPRISE_PLATFORM is, and what it is not.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">About ENTERPRISE_PLATFORM</h1>

      <div className="mt-8 space-y-6 text-slate-700 leading-relaxed">
        <p>
          ENTERPRISE_PLATFORM is a demonstration platform built on{" "}
          <strong>Frappe/ERPNext v16.36.0</strong>, showing how a single ERP foundation can
          be configured into many real, working industry-specific solutions &mdash;
          pharmaceutical manufacturing, quality and document management, laboratory
          information management, equipment/asset management, animal feed and premix
          manufacturing, livestock and aquaculture farm management, cosmetics and medical
          device manufacturing, pharmacy retail, 3PL cold-chain warehousing, and consumer
          product distribution, among others.
        </p>

        <p>
          Every industry listed on the{" "}
          <Link href="/solutions" className="font-medium text-slate-900 underline">
            Industries &amp; Solutions
          </Link>{" "}
          page is backed by a real, seeded ERP dataset and verified end-to-end business
          flows &mdash; not mockups or placeholder screenshots. Two of those industries also
          have their own dedicated public website, built as separate, real Next.js
          applications that call this platform&apos;s own guest-accessible data API.
        </p>

        <h2 className="text-xl font-semibold text-slate-900 pt-4">
          What this hub is, honestly
        </h2>
        <p>
          This page and the rest of the hub site were built in direct response to feedback
          that the platform&apos;s various demo pieces needed one shared entry point &mdash;
          a single site representing ENTERPRISE_PLATFORM itself, with each industry
          presented as a case study a visitor can select into, rather than a set of
          disconnected demo sites with no home page. It is not itself a numbered item in
          this project&apos;s own master plan; it exists because a real user asked for it.
        </p>
        <p>
          ENTERPRISE_PLATFORM is a portfolio/demo project, not a commercial product with a
          real sales organization behind it. All company names, products, and figures shown
          throughout this platform&apos;s demos are fictional or illustrative seed data
          created for demonstration purposes.
        </p>

        <h2 className="text-xl font-semibold text-slate-900 pt-4">Contact</h2>
        <p>
          This is a demo environment without a live support desk. For questions about this
          platform, refer to the project&apos;s own documentation
          (<code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm">
            documents/project_status.md
          </code>
          ) alongside the codebase.
        </p>
      </div>
    </div>
  );
}
