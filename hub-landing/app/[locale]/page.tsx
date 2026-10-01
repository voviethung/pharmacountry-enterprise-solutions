import { getTranslations, setRequestLocale } from "next-intl/server";
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import {
  getPlatformStats,
  getIndustrySolutions,
  liveDemoUrlFor,
} from "@/lib/api";
import { visualForCategory } from "@/lib/industryIcons";
import {
  Boxes,
  Network,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  ShieldAlert,
  MessageSquareText,
  FileSearch,
  Factory,
  ClipboardCheck,
  Fish,
  Search,
} from "lucide-react";

// The 9 real `industry_category` values this platform's own Industry Pack registry actually
// uses (grepped live from get_industry_solutions() — not invented), rendered as a stable
// frontend-owned list (not re-fetched, since it's a fixed taxonomy). These labels ARE
// translated below (this list is authored in this frontend, unlike the live industry_category
// strings rendered on the Solutions page, which come straight from the backend and stay in
// their original English per this rebrand's documented limitation).
const HERO_CATEGORIES = [
  "Pharmaceutical",
  "Animal Feed",
  "Aquaculture",
  "Cosmetics",
  "Medical Device",
  "Livestock",
  "Nutraceutical",
  "Processing",
  "Veterinary",
] as const;

// The 7 real Phase 6A AI capabilities this platform actually built (see project_status.md's
// Phase 6A section, AI-DEMO-01 through Evaluation Datasets) — a frontend-owned, stable list
// (these are shipped modules, not live-fetched data). `humanApproval` marks the 2 items whose
// own build docs describe a mandatory human-approval gate before an AI draft becomes a real
// record (QMS Copilot's AI Draft mechanism, Procurement Assistant's "never auto-approves").
const AI_ITEMS = [
  { key: "executiveAssistant", icon: MessageSquareText, humanApproval: false },
  { key: "qmsCopilot", icon: ShieldAlert, humanApproval: true },
  { key: "dmsCopilot", icon: FileSearch, humanApproval: false },
  { key: "manufacturingInsight", icon: Factory, humanApproval: false },
  { key: "procurementAssistant", icon: ClipboardCheck, humanApproval: true },
  { key: "farmAssistant", icon: Fish, humanApproval: false },
  { key: "enterpriseSearch", icon: Search, humanApproval: false },
] as const;

// Real photos for the Live Demo pack cards (generated from IMAGE_PROMPTS.md's 5
// per-category prompts), keyed by the live pack's own `pack_code`. Any pack not listed here
// (none currently) falls back to the colored icon band below.
const LIVE_PACK_IMAGES: Record<string, string> = {
  "IP-CONSUMER-DIST": "/images/live-consumer-dist.png",
  "IP-SUPPLEMENT": "/images/live-supplement.png",
  "IP-INGREDIENT-TRADING": "/images/live-ingredient-trading.png",
  "IP-PHARMACY": "/images/live-pharmacy.png",
  "IP-VETERINARY": "/images/live-farm.png",
};

// Force dynamic rendering — this page calls the real Frappe backend on every request. Without
// this, Next.js prerenders it once at Docker build time (when the backend isn't reachable from
// inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

async function loadStats() {
  try {
    return await getPlatformStats();
  } catch {
    return null;
  }
}

// One card PER PACK, not per demo — a pack like IP-CONSUMER-DIST has 3 real dedicated sites
// (WEB-01/03/05), and showing 3 near-identical cards with the same name/summary read as
// confusing duplication rather than 3 distinct offerings. Each returned entry carries its own
// `demos[]` list so the card can render every real link without repeating the pack's own copy.
async function loadLiveDemoPacks() {
  try {
    const solutions = await getIndustrySolutions();
    return solutions
      .filter((s) => s.live_demos.length > 0)
      .map((s) => ({
        pack_code: s.pack_code,
        pack_name: s.pack_name,
        summary: s.summary,
        industry_category: s.industry_category,
        demos: s.live_demos,
      }));
  } catch {
    return [];
  }
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");
  const tCategories = await getTranslations("categories");

  const [stats, livePacks] = await Promise.all([
    loadStats(),
    loadLiveDemoPacks(),
  ]);
  const totalLiveDemoCount = livePacks.reduce((sum, p) => sum + p.demos.length, 0);

  return (
    <div>
      <section className="relative overflow-hidden border-b border-slate-200 bg-slate-900">
        {/* Real hero image (generated from IMAGE_PROMPTS.md's "Homepage hero banner" prompt),
            tinted by the gradient/grid overlays below for white-text legibility on the left. */}
        <Image
          src="/images/hero-control-room.webp"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-70"
        />
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "radial-gradient(circle at 15% 20%, rgba(61,187,137,0.35), transparent 40%), radial-gradient(circle at 85% 0%, rgba(21,138,87,0.30), transparent 45%), radial-gradient(circle at 50% 100%, rgba(10,74,45,0.35), transparent 40%)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        {/* Left-to-right darkening so the headline stays legible over the photo regardless of
            its own content on the right two-thirds. */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.55) 45%, rgba(15,23,42,0.25) 100%)",
          }}
        />

        <div className="relative mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <p className="inline-flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-[#3DBB89]">
            <Network className="h-4 w-4" strokeWidth={2} />
            {t("eyebrow")}
          </p>
          <h1 className="mt-4 text-3xl sm:text-5xl font-bold tracking-tight text-white max-w-3xl break-words">
            {t("title")}
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-300 leading-relaxed">
            {t("lead")}
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            {/* Primary CTA: straight into the platform's strongest, most concrete proof — the
                real live demo sites, one scroll down on this same page — rather than a generic
                catalog link. */}
            <a
              href="#live-demos"
              className="inline-flex items-center gap-2 rounded-md bg-white px-5 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-100 transition-colors"
            >
              {t("ctaExploreDemos")}
              <ArrowRight className="h-4 w-4" strokeWidth={2} />
            </a>
            {/* Secondary CTA: reuses the existing /contact page (real Contact -> ERPNext CRM
                Lead pipeline) rather than a new/duplicate contact mechanism. */}
            <Link
              href="/contact?intent=demo-request"
              className="rounded-md border border-slate-600 px-5 py-3 text-sm font-semibold text-slate-200 hover:border-slate-400 hover:text-white transition-colors"
            >
              {t("ctaRequestDemo")}
            </Link>
            {/* Tertiary: kept as a lower-emphasis text link (also already in the header nav). */}
            <Link
              href="/about"
              className="text-sm font-medium text-slate-300 underline decoration-slate-500 underline-offset-4 hover:text-white transition-colors"
            >
              {t("ctaAbout")}
            </Link>
          </div>

          <div className="mt-14 flex flex-wrap gap-3">
            {HERO_CATEGORIES.map((category) => {
              const { icon: Icon } = visualForCategory(category);
              return (
                <span
                  key={category}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-medium text-slate-200 backdrop-blur-sm"
                >
                  <Icon className="h-3.5 w-3.5 text-[#3DBB89]" strokeWidth={1.75} />
                  {tCategories(category)}
                </span>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          <StatTile value={stats?.industry_pack_count} label={t("stats.industryPacks")} />
          <StatTile value={stats?.golden_demo_pack_count} label={t("stats.goldenDemos")} />
          <StatTile value={stats?.capability_engine_count} label={t("stats.capabilityEngines")} />
          <StatTile value={stats?.live_demo_count} label={t("stats.liveDemos")} />
        </div>
        {!stats && (
          <p className="mt-4 text-center text-sm text-[#158A57]">{t("stats.unavailable")}</p>
        )}
      </section>

      <section id="live-demos" className="border-t border-slate-200 bg-slate-50 scroll-mt-16">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">
                {t("liveDemos.heading")}
              </h2>
              <p className="mt-2 max-w-2xl text-slate-600">
                {t("liveDemos.description", { count: totalLiveDemoCount })}
              </p>
            </div>
            <Link
              href="/solutions"
              className="hidden sm:inline text-sm font-medium text-slate-600 hover:text-slate-900 whitespace-nowrap"
            >
              {t("liveDemos.viewAll")}
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* One card PER PACK (not per demo) — see loadLiveDemoPacks()'s own comment. A real
                photo (generated from IMAGE_PROMPTS.md's 5 per-category prompts) heads each card;
                a colored icon band remains as a fallback for any pack not in LIVE_PACK_IMAGES. */}
            {livePacks.map((pack) => {
              const { icon: PackIcon, bg, fg } = visualForCategory(pack.industry_category);
              const photo = LIVE_PACK_IMAGES[pack.pack_code];
              return (
                <div
                  key={pack.pack_code}
                  className="group overflow-hidden rounded-lg border border-slate-200 bg-white hover:border-[#3DBB89] hover:shadow-sm transition-all"
                >
                  {photo ? (
                    <div className="relative h-36 w-full overflow-hidden">
                      <Image
                        src={photo}
                        alt=""
                        fill
                        sizes="(min-width: 640px) 50vw, 100vw"
                        className="object-cover transition-transform group-hover:scale-105"
                      />
                    </div>
                  ) : (
                    <div className={`flex h-28 items-center justify-center ${bg}`}>
                      <PackIcon className={`h-12 w-12 ${fg}`} strokeWidth={1.25} />
                    </div>
                  )}
                  <div className="p-6">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#158A57]/10 px-2.5 py-1 text-xs font-semibold text-[#0A4A2D]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#1FA76B]" />
                      {t("liveDemos.liveBadge")}
                    </span>
                    <h3 className="mt-3 font-semibold text-slate-900">{pack.pack_name}</h3>
                    <p className="mt-2 text-sm text-slate-600">{pack.summary}</p>
                    <div className="mt-4 space-y-2">
                      {pack.demos.map((demo) => {
                        const url = liveDemoUrlFor(demo.key);
                        if (!url) {
                          return (
                            <p key={demo.key} className="text-sm font-medium text-slate-400">
                              {demo.label} — {t("liveDemos.builtBadge")}
                            </p>
                          );
                        }
                        return (
                          <a
                            key={demo.key}
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-between text-sm font-medium text-[#0A4A2D] hover:text-[#158A57]"
                          >
                            <span>
                              {demo.label}
                              {demo.requires_login && (
                                <span className="ml-2 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                                  {t("liveDemos.loginBadge")}
                                </span>
                              )}
                            </span>
                            <ArrowRight className="h-4 w-4 shrink-0" strokeWidth={2} />
                          </a>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
            {livePacks.length === 0 && (
              <p className="text-slate-500">{t("liveDemos.empty")}</p>
            )}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-2xl font-semibold text-slate-900">{t("howBuilt.heading")}</h2>
        {/* Real multi-industry illustration (generated from IMAGE_PROMPTS.md's "Multi-industry
            breadth illustration" prompt), anchoring this section visually. */}
        <div className="mt-8 relative mx-auto h-56 w-full max-w-xl sm:h-64">
          <Image
            src="/images/multi-industry.webp"
            alt=""
            fill
            sizes="(min-width: 640px) 576px, 100vw"
            className="object-contain"
          />
        </div>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#158A57]/10">
              <Network className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
            </span>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-[#158A57]">
              {t("howBuilt.engines.label")}
            </p>
            <p className="mt-2 text-slate-600">{t("howBuilt.engines.text")}</p>
          </div>
          <div>
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#158A57]/10">
              <Boxes className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
            </span>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-[#158A57]">
              {t("howBuilt.packs.label")}
            </p>
            <p className="mt-2 text-slate-600">{t("howBuilt.packs.text")}</p>
          </div>
          <div>
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#158A57]/10">
              <CheckCircle2 className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
            </span>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-[#158A57]">
              {t("howBuilt.demos.label")}
            </p>
            <p className="mt-2 text-slate-600">{t("howBuilt.demos.text")}</p>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="inline-flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-[#158A57]">
            <Sparkles className="h-4 w-4" strokeWidth={2} />
            {t("aiAutomation.heading")}
          </p>
          <h2 className="mt-2 max-w-2xl text-2xl font-semibold text-slate-900">
            {t("aiAutomation.lead")}
          </h2>

          {/* Honesty callout — the mock-vs-real framing lives here, once, rather than repeated
              on every card below. See this section's own build notes for why: the underlying
              LLM provider call is a deliberately-labeled mock adapter (`ai_core.py`), while the
              routing/policy/tool-registry/permission/audit architecture around it is real. */}
          <div className="mt-6 rounded-lg border border-[#158A57]/25 bg-white p-5 max-w-3xl">
            <h3 className="text-sm font-semibold text-slate-900">
              {t("aiAutomation.honesty.heading")}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              {t("aiAutomation.honesty.text")}
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {AI_ITEMS.map(({ key, icon: Icon, humanApproval }) => (
              <div key={key} className="rounded-lg border border-slate-200 bg-white p-6">
                <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#158A57]/10">
                  <Icon className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
                </span>
                <h3 className="mt-3 font-semibold text-slate-900">
                  {t(`aiAutomation.items.${key}.title`)}
                </h3>
                <p className="mt-2 text-sm text-slate-600">
                  {t(`aiAutomation.items.${key}.text`)}
                </p>
                {humanApproval && (
                  <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">
                    {t("aiAutomation.humanApprovalBadge")}
                  </span>
                )}
              </div>
            ))}
          </div>

          <p className="mt-8 max-w-3xl text-sm text-slate-500">{t("aiAutomation.governanceNote")}</p>

          <Link
            href="/contact?intent=ai-architecture"
            className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-[#158A57] hover:text-[#0A4A2D] hover:underline"
          >
            {t("aiAutomation.cta")}
            <ArrowRight className="h-4 w-4" strokeWidth={2} />
          </Link>
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
