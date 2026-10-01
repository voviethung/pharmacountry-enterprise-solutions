import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import {
  getIndustryPackDetail,
  liveDemoUrlFor,
  type IndustryPackDetail,
} from "@/lib/api";
import { getPackContent, NOT_YET_BUILT_NOTE } from "@/lib/industryPackContent";
import { localizedPackName, localizedPackSummary, localizedDemoLabel } from "@/lib/packDisplayText";
import { visualForCategory } from "@/lib/industryIcons";
import {
  ArrowLeft,
  ArrowUpRight,
  CheckCircle2,
  ListChecks,
  Cog,
  AlertTriangle,
  ChevronDown,
  FlaskConical,
} from "lucide-react";

// This page calls the real Frappe backend on every request (get_industry_pack_detail) — see
// app/[locale]/page.tsx's own comment on the same requirement. Without this, Next.js would
// prerender it once at Docker build time, when the backend isn't reachable from inside the
// build container (no host.docker.internal mapping at build time — see this repo's Dockerfile),
// and every pack_code would serve whatever the build-time snapshot happened to be, or fail
// outright. `generateStaticParams` is deliberately NOT used here for the same reason: this page
// is genuinely dynamic per-request live data, not a static content page.
export const dynamic = "force-dynamic";

async function loadDetail(packCode: string): Promise<IndustryPackDetail | null> {
  try {
    return await getIndustryPackDetail(packCode);
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; packCode: string }>;
}): Promise<Metadata> {
  const { locale, packCode } = await params;
  const t = await getTranslations({ locale, namespace: "solutionDetail" });
  const detail = await loadDetail(packCode);
  if (!detail) {
    return { title: t("notFoundTitle") };
  }
  return {
    title: `${localizedPackName(detail.pack_code, detail.pack_name, locale)} — PharmaCountry Enterprise Solutions`,
    description: localizedPackSummary(detail.pack_code, detail.summary, locale),
  };
}

export default async function SolutionDetailPage({
  params,
}: {
  params: Promise<{ locale: string; packCode: string }>;
}) {
  const { locale, packCode } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("solutionDetail");
  const tSolutions = await getTranslations("solutions");
  const tCategories = await getTranslations("categories");

  const detail = await loadDetail(packCode);

  if (!detail) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <BackLink t={t} />
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 px-6 py-8 text-center">
          <h1 className="text-xl font-semibold text-amber-900">{t("notFoundTitle")}</h1>
          <p className="mt-2 text-sm text-amber-800">{t("notFoundBody")}</p>
        </div>
      </div>
    );
  }

  const content = getPackContent(detail.pack_code, locale);
  const { icon: Icon, bg, fg } = visualForCategory(detail.industry_category);
  const isNotYetBuilt = !detail.has_golden_demo;
  const packName = localizedPackName(detail.pack_code, detail.pack_name, locale);
  const packSummary = localizedPackSummary(detail.pack_code, detail.summary, locale);
  let categoryLabel = detail.industry_category;
  try {
    categoryLabel = tCategories(detail.industry_category);
  } catch {
    // fall back to the raw English category if it's ever missing from messages/*.json
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <BackLink t={t} />

      <div className="mt-6 flex items-start gap-4">
        <span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-lg ${bg}`}>
          <Icon className={`h-7 w-7 ${fg}`} strokeWidth={1.75} />
        </span>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[#158A57]">
            {categoryLabel}
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">{packName}</h1>
        </div>
      </div>

      <p className="mt-6 text-slate-700 leading-relaxed">{packSummary}</p>

      {detail.has_live_demo && (
        <div className="mt-8 rounded-lg border border-[#158A57]/30 bg-[#158A57]/5 p-6">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <ArrowUpRight className="h-4 w-4 text-[#0A4A2D]" strokeWidth={2} />
            {t("liveSiteHeading")}
          </h2>
          <p className="mt-2 text-sm text-slate-600">{t("liveSiteBody")}</p>
          <div className="mt-4 space-y-2">
            {detail.live_demos.map((demo) => {
              const url = liveDemoUrlFor(demo.key);
              const label = localizedDemoLabel(demo.key, demo.label, locale);
              if (!url) {
                return (
                  <p key={demo.key} className="text-sm font-medium text-slate-400">
                    {tSolutions("notDeployed", { label })}
                  </p>
                );
              }
              return (
                <a
                  key={demo.key}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md bg-[#158A57] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0A4A2D] transition-colors mr-2 mb-2"
                >
                  {label}
                  <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2} />
                  {demo.requires_login && (
                    <span className="ml-1 rounded-full bg-white/20 px-2 py-0.5 text-xs font-semibold">
                      {tSolutions("requiresLogin")}
                    </span>
                  )}
                </a>
              );
            })}
          </div>
        </div>
      )}

      {isNotYetBuilt && (
        <div className="mt-8 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6">
          <h2 className="font-semibold text-slate-900">{t("notBuiltHeading")}</h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">{NOT_YET_BUILT_NOTE}</p>
        </div>
      )}

      {!isNotYetBuilt && !detail.has_live_demo && (
        <p className="mt-6 text-xs text-slate-400 italic">{t("erpExploreNote")}</p>
      )}

      {content && (
        <>
          {/* Business-facing primary content: what the demo proves, in plain English — no
              test-ID codes or "Golden Demo #N" labels at this level (P1 #3). */}
          <section className="mt-10">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
              <CheckCircle2 className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              {t("provesHeading")}
            </h2>
            <p className="mt-3 text-sm text-slate-600">
              {t("provesIntro", { count: content.testIds.length })}
            </p>
            <ul className="mt-4 space-y-2.5">
              {content.testIds.map((id) => (
                <li key={id} className="flex gap-2.5 text-sm text-slate-700">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#3DBB89]" strokeWidth={2} />
                  <span>{content.testDescriptions[id]}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-10">
            <h2 className="text-lg font-semibold text-slate-900">{t("flowHeading")}</h2>
            <p className="mt-3 text-sm text-slate-700 leading-relaxed">
              {content.businessFlowSummary}
            </p>
          </section>

          {/* Issues found & fixed during testing: genuinely valuable (proves testing was real)
              but a business buyer shouldn't hit it before understanding the product — closed by
              default, positioned after the business-facing content above (P1 #5). */}
          {content.notableBugsFixed && content.notableBugsFixed.length > 0 && (
            <details className="mt-10 group rounded-lg border border-slate-200 bg-white">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm font-semibold text-slate-900 marker:content-none">
                {t("bugsHeading")}
                <ChevronDown
                  className="h-4 w-4 shrink-0 text-slate-400 transition-transform group-open:rotate-180"
                  strokeWidth={2}
                />
              </summary>
              <div className="border-t border-slate-100 px-5 py-4">
                <p className="text-xs text-slate-500">{t("bugsIntro")}</p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-700">
                  {content.notableBugsFixed.map((bug, i) => (
                    <li key={i}>{bug}</li>
                  ))}
                </ul>
              </div>
            </details>
          )}
        </>
      )}

      {/* Engineering Evidence: the raw test IDs, seed data steps, and capability engines a
          technical buyer (CTO/QA/IT) will specifically want — collapsed by default, a clearly
          labeled secondary disclosure rather than shown at the same priority as the
          business-facing content above (P1 #3). */}
      {(content || detail.seed_steps.length > 0 || detail.capability_engines.length > 0) && (
        <details className="mt-6 group rounded-lg border border-slate-200 bg-slate-50">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm font-semibold text-slate-900 marker:content-none">
            <span className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-[#158A57]" strokeWidth={1.75} />
              {t("engineeringEvidenceHeading")}
            </span>
            <ChevronDown
              className="h-4 w-4 shrink-0 text-slate-400 transition-transform group-open:rotate-180"
              strokeWidth={2}
            />
          </summary>
          <div className="space-y-8 border-t border-slate-200 px-5 py-5">
            <p className="text-xs text-slate-500">{t("engineeringEvidenceIntro")}</p>

            {content && (
              <div>
                <p className="text-xs font-mono text-slate-500">
                  {content.goldenDemoLabel}
                  {content.companyName ? ` · ${t("companyLabel")}: ${content.companyName}` : ""}
                </p>
                <p className="mt-3 text-sm font-medium text-slate-900">
                  {t("evidenceTestIdsIntro")}
                </p>
                <ul className="mt-3 space-y-2">
                  {content.testIds.map((id) => {
                    const unconfirmed = content.unconfirmedTestIds?.includes(id);
                    return (
                      <li key={id} className="flex gap-3 text-sm">
                        <span className="mt-0.5 shrink-0 rounded bg-white px-1.5 py-0.5 font-mono text-xs font-semibold text-slate-600 border border-slate-200">
                          {id}
                        </span>
                        <span className="text-slate-700">
                          {content.testDescriptions[id]}
                          {unconfirmed && (
                            <span
                              className="ml-1.5 inline-flex items-center gap-1 text-xs text-amber-700"
                              title={t("unconfirmedFlag")}
                            >
                              <AlertTriangle className="inline h-3 w-3" strokeWidth={2} />
                            </span>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {detail.seed_steps.length > 0 && (
              <div>
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <ListChecks className="h-4 w-4 text-[#158A57]" strokeWidth={1.75} />
                  {t("seedStepsHeading")}
                </h3>
                <p className="mt-2 text-xs text-slate-500">
                  {t("seedStepsIntro", { count: detail.seed_steps.length })}
                </p>
                <ol className="mt-3 space-y-1.5">
                  {detail.seed_steps.map((step) => (
                    <li
                      key={step.sequence}
                      className="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    >
                      <span className="w-7 shrink-0 text-right font-mono text-xs text-slate-400">
                        {step.sequence}
                      </span>
                      <span className="flex-1 text-slate-700">{step.label}</span>
                      <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                        {seedTypeLabel(step.seed_type, t)}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {detail.capability_engines.length > 0 && (
              <div>
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Cog className="h-4 w-4 text-[#158A57]" strokeWidth={1.75} />
                  {t("enginesHeading")}
                </h3>
                <p className="mt-2 text-xs text-slate-500">{t("enginesIntro")}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {detail.capability_engines.map((engine) => (
                    <span
                      key={engine.engine_code}
                      className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                    >
                      {engine.engine_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </details>
      )}

      {/* Technical identifiers, collapsed to a small monospace footer line rather than a
          headline (P1 #3). */}
      <p className="mt-10 border-t border-slate-100 pt-4 font-mono text-[11px] text-slate-400">
        {detail.pack_code}
        {content ? ` · ${content.goldenDemoLabel}` : ""}
      </p>
    </div>
  );
}

function seedTypeLabel(seedType: string, t: (key: string) => string): string {
  if (seedType === "Master Data") return t("seedTypeMasterData");
  if (seedType === "Transaction") return t("seedTypeTransaction");
  if (seedType === "Demo Scenario") return t("seedTypeDemoScenario");
  return seedType;
}

function BackLink({ t }: { t: (key: string) => string }) {
  return (
    <Link
      href="/solutions"
      className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-900"
    >
      <ArrowLeft className="h-4 w-4" strokeWidth={2} />
      {t("back")}
    </Link>
  );
}
