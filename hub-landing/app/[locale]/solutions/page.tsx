import type { Metadata } from "next";
import type { ReactNode } from "react";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { getIndustrySolutions, liveDemoUrlFor, type IndustrySolution } from "@/lib/api";
import { visualForCategory } from "@/lib/industryIcons";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("solutionsTitle"),
    description: t("solutionsDescription"),
  };
}

// Force dynamic rendering — see app/[locale]/page.tsx's own comment on the same requirement.
export const dynamic = "force-dynamic";

export default async function SolutionsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("solutions");

  let solutions: IndustrySolution[] = [];
  let loadError = false;
  try {
    solutions = await getIndustrySolutions();
  } catch {
    loadError = true;
  }

  const sorted = [...solutions].sort((a, b) => {
    const rank = (s: IndustrySolution) =>
      s.has_live_demo ? 0 : s.has_golden_demo ? 1 : 2;
    const diff = rank(a) - rank(b);
    return diff !== 0 ? diff : a.pack_name.localeCompare(b.pack_name);
  });

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 max-w-2xl text-slate-600">
        {solutions.length > 0
          ? t("introWithCount", { count: solutions.length })
          : t("introLoading")}
      </p>

      {loadError && (
        <p className="mt-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {t("loadError")}
        </p>
      )}

      {solutions.length > 0 && (
        <p className="mt-3 max-w-2xl text-xs text-slate-400 italic">{t("languageNote")}</p>
      )}

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {sorted.map((solution) => (
          <SolutionCard key={solution.pack_code} solution={solution} t={t} />
        ))}
      </div>

      <div className="mt-16 rounded-lg border border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
        <p className="font-semibold text-slate-900">{t("legend.heading")}</p>
        <ul className="mt-3 list-disc pl-5 space-y-1.5">
          <li>
            <span className="font-medium text-[#0A4A2D]">{t("badge.live")}</span> &mdash;{" "}
            {t("legend.live")}
          </li>
          <li>
            <span className="font-medium text-slate-700">{t("badge.erp")}</span> &mdash;{" "}
            {t("legend.erp")}
          </li>
          <li>
            <span className="font-medium text-slate-500">{t("badge.planned")}</span> &mdash;{" "}
            {t("legend.planned")}
          </li>
        </ul>
      </div>
    </div>
  );
}

type T = (key: string, values?: Record<string, string | number>) => string;

function SolutionCard({ solution, t }: { solution: IndustrySolution; t: T }) {
  if (solution.has_live_demo) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 hover:border-[#3DBB89] hover:shadow-md transition-all flex flex-col">
        <div className="flex items-start justify-between">
          <CategoryIcon category={solution.industry_category} />
          <CardBadge tone="live">{t("badge.live")}</CardBadge>
        </div>
        <CardBody solution={solution} />
        <div className="mt-4 space-y-2">
          {solution.live_demos.map((demo) => {
            const url = liveDemoUrlFor(demo.key);
            if (!url) {
              return (
                <p key={demo.key} className="text-sm font-medium text-slate-400">
                  {t("notDeployed", { label: demo.label })}
                </p>
              );
            }
            return (
              <a
                key={demo.key}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm font-medium text-[#158A57] hover:text-[#0A4A2D]"
              >
                {demo.label} &rarr;
                {demo.requires_login && (
                  <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                    {t("requiresLogin")}
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
      <div className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col hover:shadow-sm transition-all">
        <div className="flex items-start justify-between">
          <CategoryIcon category={solution.industry_category} />
          <CardBadge tone="erp">{t("badge.erp")}</CardBadge>
        </div>
        <CardBody solution={solution} />
        <p className="mt-4 text-xs text-slate-400">{t("erpNote")}</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 flex flex-col opacity-80">
      <div className="flex items-start justify-between">
        <CategoryIcon category={solution.industry_category} muted />
        <CardBadge tone="planned">{t("badge.planned")}</CardBadge>
      </div>
      <CardBody solution={solution} />
    </div>
  );
}

function CategoryIcon({ category, muted }: { category: string; muted?: boolean }) {
  const { icon: Icon, bg, fg } = visualForCategory(category);
  return (
    <span
      className={`flex h-11 w-11 items-center justify-center rounded-lg ${
        muted ? "bg-slate-100" : bg
      }`}
    >
      <Icon className={`h-5 w-5 ${muted ? "text-slate-400" : fg}`} strokeWidth={1.75} />
    </span>
  );
}

function CardBody({ solution }: { solution: IndustrySolution }) {
  return (
    <>
      {/* industry_category/pack_name/summary are real, live backend data (Industry Pack
          registry), authored in English only — see this page's own "languageNote" translation
          above documenting that honestly, rather than silently mistranslating live data. */}
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-[#158A57]">
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
    live: "bg-[#158A57]/10 text-[#0A4A2D]",
    erp: "bg-slate-100 text-slate-700",
    planned: "bg-slate-100 text-slate-500",
  } as const;
  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${styles[tone]}`}
    >
      {tone === "live" && <span className="h-1.5 w-1.5 rounded-full bg-[#1FA76B]" />}
      {children}
    </span>
  );
}
