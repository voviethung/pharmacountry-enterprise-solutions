import Link from "next/link";
import {
  getPlatformStats,
  getIndustrySolutions,
  liveDemoUrlFor,
} from "@/lib/api";

// Real platform-scale numbers (from the guest-whitelisted `get_platform_stats()` endpoint)
// render if the backend is reachable; if it's briefly down, the page still renders with
// clearly-labeled fallback numbers instead of crashing — same "never hard-fail a public page
// on one upstream call" discipline WEB-01's layout established.
async function loadStats() {
  try {
    return await getPlatformStats();
  } catch {
    return null;
  }
}

// Flattens "solutions with live demos" into one row PER DEMO (not per pack) — IP-CONSUMER-DIST
// alone now has 2 (WEB-01 guest-only, WEB-03 login-required), so a pack-level list would need a
// second nested loop; flattening here keeps every consumer of this data simple.
async function loadLiveDemoEntries() {
  try {
    const solutions = await getIndustrySolutions();
    return solutions.flatMap((s) =>
      s.live_demos.map((demo) => ({
        ...demo,
        pack_code: s.pack_code,
        pack_name: s.pack_name,
        summary: s.summary,
      }))
    );
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const [stats, liveDemos] = await Promise.all([
    loadStats(),
    loadLiveDemoEntries(),
  ]);

  return (
    <div>
      <section className="border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <p className="text-sm font-medium uppercase tracking-wide text-amber-600">
            Multi-Industry ERP Demo Platform &middot; Built on Frappe/ERPNext
          </p>
          <h1 className="mt-3 text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 max-w-3xl">
            ENTERPRISE_PLATFORM
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-600 leading-relaxed">
            One platform, real ERP data, and a growing set of fully-built industry
            solutions &mdash; from pharmaceutical manufacturing and quality systems to
            livestock, aquaculture, cosmetics, medical devices, pharmacy retail, 3PL cold
            chain, and consumer distribution. Every industry below is a real, working
            Frappe/ERPNext backend, not a mockup.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/solutions"
              className="rounded-md bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700 transition-colors"
            >
              Explore Industries &amp; Solutions
            </Link>
            <Link
              href="/about"
              className="rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:border-slate-400 transition-colors"
            >
              About This Platform
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          <StatTile
            value={stats?.industry_pack_count}
            label="Industry Packs"
          />
          <StatTile
            value={stats?.golden_demo_pack_count}
            label="Fully-Built Golden Demos"
          />
          <StatTile
            value={stats?.capability_engine_count}
            label="Capability Engines"
          />
          <StatTile value={stats?.live_demo_count} label="Live Public Sites" />
        </div>
        {!stats && (
          <p className="mt-4 text-center text-sm text-amber-600">
            Live platform stats are temporarily unavailable &mdash; showing this page without
            them rather than failing to load.
          </p>
        )}
      </section>

      <section className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">
                Live Public Demo Sites
              </h2>
              <p className="mt-2 max-w-2xl text-slate-600">
                {liveDemos.length} dedicated sites across this platform&apos;s industries so
                far, built as real standalone Next.js apps against this platform&apos;s own
                ERP data — most are guest-accessible public sites; two require a real login
                (a dealer portal and a supplier portal), clearly marked below.
              </p>
            </div>
            <Link
              href="/solutions"
              className="hidden sm:inline text-sm font-medium text-slate-600 hover:text-slate-900 whitespace-nowrap"
            >
              View all industries &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {liveDemos.map((demo) => {
              const url = liveDemoUrlFor(demo.key);
              return (
                <a
                  key={demo.key}
                  href={url ?? "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group rounded-lg border border-slate-200 bg-white p-6 hover:border-slate-400 hover:shadow-sm transition-all"
                >
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    Live Demo
                  </span>
                  {demo.requires_login && (
                    <span className="ml-2 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">
                      Requires login
                    </span>
                  )}
                  <h3 className="mt-3 font-semibold text-slate-900 group-hover:text-slate-700">
                    {demo.pack_name}
                  </h3>
                  <p className="mt-2 text-sm text-slate-600">{demo.summary}</p>
                  <p className="mt-4 text-sm font-medium text-slate-900">
                    {demo.label} &rarr;
                  </p>
                </a>
              );
            })}
            {liveDemos.length === 0 && (
              <p className="text-slate-500">Live demo data is temporarily unavailable.</p>
            )}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-2xl font-semibold text-slate-900">
          How this platform is put together
        </h2>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
              Capability Engines
            </p>
            <p className="mt-2 text-slate-600">
              15 shared capability engines (ERP core, CRM, procurement, WMS, manufacturing,
              QMS, DMS, LIMS, EAM, farm management, traceability, commerce, AI, HR, R&amp;D)
              power every industry pack &mdash; not rebuilt per industry.
            </p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
              Industry Packs
            </p>
            <p className="mt-2 text-slate-600">
              27 registered Industry Packs pair a real vertical (pharma, feed, livestock,
              aquaculture, cosmetics, medical device, pharmacy, 3PL, and more) with the
              engines, roles, and seed data it needs.
            </p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
              Golden Demos
            </p>
            <p className="mt-2 text-slate-600">
              Most industry packs already have a complete, verified golden demo &mdash; real
              seeded data and end-to-end business flows explored directly in the ERP system.
              A select few also get a dedicated public website, like the ones above.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatTile({ value, label }: { value: number | undefined; label: string }) {
  return (
    <div>
      <p className="text-3xl font-bold text-slate-900">{value ?? "—"}</p>
      <p className="mt-1 text-sm text-slate-600">{label}</p>
    </div>
  );
}
