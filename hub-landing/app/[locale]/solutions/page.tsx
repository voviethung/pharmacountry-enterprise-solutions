import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { getIndustrySolutions, liveDemoUrlFor, type IndustrySolution } from "@/lib/api";
import { getPackTags } from "@/lib/industryPackTags";
import SolutionsExplorer, { type ExplorerCard } from "@/components/SolutionsExplorer";

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

  // Resolve each live-demo's real URL SERVER-SIDE (liveDemoUrlFor() reads env vars via
  // lib/api.ts, which uses Node's `http` module and must never reach the client bundle) and
  // attach curated Operation/Software tags, producing a plain, fully-serializable array to hand
  // to the client-side filter component below.
  const cards: ExplorerCard[] = sorted.map((solution) => {
    const tags = getPackTags(solution.pack_code) ?? { operations: [], software: [] };
    return {
      pack_code: solution.pack_code,
      pack_name: solution.pack_name,
      industry_category: solution.industry_category,
      summary: solution.summary,
      has_golden_demo: solution.has_golden_demo,
      has_live_demo: solution.has_live_demo,
      live_demos: solution.live_demos.map((demo) => ({
        ...demo,
        url: liveDemoUrlFor(demo.key),
      })),
      operations: tags.operations,
      software: tags.software,
    };
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

      <SolutionsExplorer cards={cards} />

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
