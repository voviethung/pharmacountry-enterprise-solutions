import type { Metadata } from "next";
import type { ReactNode } from "react";
import { getIndustrySolutions, liveDemoUrlFor, type IndustrySolution } from "@/lib/api";

export const metadata: Metadata = {
  title: "Industries & Solutions",
  description:
    "Every real Industry Pack built into ENTERPRISE_PLATFORM, pulled live from the platform's own registry.",
};

export default async function SolutionsPage() {
  let solutions: IndustrySolution[] = [];
  let loadError = false;
  try {
    solutions = await getIndustrySolutions();
  } catch {
    loadError = true;
  }

  // Live public demos first, then fully-built ERP-only golden demos, then anything
  // registered but not yet built out — real signals from the API, not a hardcoded order.
  const sorted = [...solutions].sort((a, b) => {
    const rank = (s: IndustrySolution) =>
      s.has_live_demo ? 0 : s.has_golden_demo ? 1 : 2;
    const diff = rank(a) - rank(b);
    return diff !== 0 ? diff : a.pack_name.localeCompare(b.pack_name);
  });

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Industries &amp; Solutions</h1>
      <p className="mt-3 max-w-2xl text-slate-600">
        {solutions.length > 0
          ? `${solutions.length} real, enabled Industry Packs, pulled live from this platform's own Industry Pack registry — not a hardcoded list.`
          : "Loading the platform's real Industry Pack registry."}
      </p>

      {loadError && (
        <p className="mt-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          The live Industry Pack data is temporarily unavailable. Please try again shortly.
        </p>
      )}

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {sorted.map((solution) => (
          <SolutionCard key={solution.pack_code} solution={solution} />
        ))}
      </div>

      <div className="mt-16 rounded-lg border border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
        <p className="font-semibold text-slate-900">How to read these cards</p>
        <ul className="mt-3 list-disc pl-5 space-y-1.5">
          <li>
            <span className="font-medium text-emerald-700">Live Demo</span> &mdash; this
            industry also has its own dedicated public website (a real, standalone Next.js
            app), which the card links to directly.
          </li>
          <li>
            <span className="font-medium text-slate-700">ERP System Demo</span> &mdash; a
            complete, verified golden demo exists (real seeded master data and end-to-end
            business transactions), explored directly inside the Frappe/ERPNext backend
            rather than through a public marketing site. Per this platform&apos;s own build
            plan, a public website is only built for an industry &quot;when genuinely
            needed&quot; &mdash; most industries are meant to be explored via the ERP system
            itself.
          </li>
          <li>
            <span className="font-medium text-slate-500">Not Yet Built</span> &mdash; this
            Industry Pack is registered in the platform&apos;s own configuration but has no
            golden demo seed data built yet.
          </li>
        </ul>
      </div>
    </div>
  );
}

function SolutionCard({ solution }: { solution: IndustrySolution }) {
  if (solution.has_live_demo) {
    // A pack can now have MORE THAN ONE dedicated site (IP-CONSUMER-DIST has WEB-01, guest-only,
    // AND WEB-03, login-required) — render one link per demo rather than assuming exactly one.
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 hover:border-emerald-400 hover:shadow-sm transition-all flex flex-col">
        <CardBadge tone="live">Live Demo</CardBadge>
        <CardBody solution={solution} />
        <div className="mt-4 space-y-2">
          {solution.live_demos.map((demo) => {
            const url = liveDemoUrlFor(demo.key);
            return (
              <a
                key={demo.key}
                href={url ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm font-medium text-emerald-700 hover:text-emerald-800"
              >
                {demo.label} &rarr;
                {demo.requires_login && (
                  <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                    Requires login
                  </span>
                )}
              </a>
            );
          })}
        </div>
      </div>
    );
  }

  if (solution.has_golden_demo) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col">
        <CardBadge tone="erp">ERP System Demo</CardBadge>
        <CardBody solution={solution} />
        <p className="mt-4 text-xs text-slate-400">
          Explored via Frappe Desk (internal login) &mdash; not a public website in this
          environment.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 flex flex-col opacity-80">
      <CardBadge tone="planned">Not Yet Built</CardBadge>
      <CardBody solution={solution} />
    </div>
  );
}

function CardBody({ solution }: { solution: IndustrySolution }) {
  return (
    <>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-amber-600">
        {solution.industry_category}
      </p>
      <h3 className="mt-2 font-semibold text-slate-900">{solution.pack_name}</h3>
      <p className="mt-2 text-sm text-slate-600 flex-1">{solution.summary}</p>
      <p className="mt-3 text-xs text-slate-400">{solution.pack_code}</p>
    </>
  );
}

function CardBadge({
  tone,
  children,
}: {
  tone: "live" | "erp" | "planned";
  children: ReactNode;
}) {
  const styles = {
    live: "bg-emerald-100 text-emerald-800",
    erp: "bg-slate-100 text-slate-700",
    planned: "bg-slate-100 text-slate-500",
  } as const;
  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${styles[tone]}`}
    >
      {tone === "live" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
      {children}
    </span>
  );
}
