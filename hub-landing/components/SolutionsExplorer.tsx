"use client";

// Client-side filter + card grid for the /solutions page (P1 reviewer feedback: 27 packs as one
// undifferentiated list is hard to navigate; cards were leading with engineering jargon instead
// of business value). Filtering runs entirely over the already-fetched 27-pack list the parent
// SERVER component passes in as plain, serializable props — no new backend endpoint, and
// deliberately NO import from `lib/api.ts` here (that file uses Node's `http` module for the
// Frappe Host-header workaround, which must never end up in a client bundle). The parent server
// component already resolved each live-demo's real URL server-side and passes the plain string
// through as `url`.

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { visualForCategory } from "@/lib/industryIcons";
import { OPERATION_KEYS, SOFTWARE_KEYS, type OperationKey, type SoftwareKey } from "@/lib/industryPackTags";
import { ArrowUpRight } from "lucide-react";

export interface ExplorerLiveDemo {
  key: string;
  label: string;
  requires_login: boolean;
  url: string | null;
}

export interface ExplorerCard {
  pack_code: string;
  pack_name: string;
  industry_category: string;
  summary: string;
  has_golden_demo: boolean;
  has_live_demo: boolean;
  live_demos: ExplorerLiveDemo[];
  operations: OperationKey[];
  software: SoftwareKey[];
}

type SolutionsT = ReturnType<typeof useTranslations>;

export default function SolutionsExplorer({ cards }: { cards: ExplorerCard[] }) {
  const t = useTranslations("solutions");
  const tCategories = useTranslations("categories");
  const [industry, setIndustry] = useState<string | null>(null);
  const [operation, setOperation] = useState<OperationKey | null>(null);
  const [software, setSoftware] = useState<SoftwareKey | null>(null);

  const industries = useMemo(() => {
    const seen = new Set<string>();
    for (const c of cards) seen.add(c.industry_category);
    return Array.from(seen).sort((a, b) => a.localeCompare(b));
  }, [cards]);

  const operations = useMemo(
    () => OPERATION_KEYS.filter((key) => cards.some((c) => c.operations.includes(key))),
    [cards]
  );
  const software_ = useMemo(
    () => SOFTWARE_KEYS.filter((key) => cards.some((c) => c.software.includes(key))),
    [cards]
  );

  const filtered = useMemo(() => {
    return cards.filter((c) => {
      if (industry && c.industry_category !== industry) return false;
      if (operation && !c.operations.includes(operation)) return false;
      if (software && !c.software.includes(software)) return false;
      return true;
    });
  }, [cards, industry, operation, software]);

  const hasActiveFilter = Boolean(industry || operation || software);

  function categoryLabel(category: string): string {
    try {
      return tCategories(category);
    } catch {
      return category;
    }
  }

  return (
    <div>
      <div className="mt-10 rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold text-slate-900">{t("filters.heading")}</p>
          {hasActiveFilter && (
            <button
              type="button"
              onClick={() => {
                setIndustry(null);
                setOperation(null);
                setSoftware(null);
              }}
              className="text-xs font-medium text-slate-500 hover:text-slate-900"
            >
              {t("filters.clear")}
            </button>
          )}
        </div>

        <FilterRow
          label={t("filters.industryLabel")}
          allLabel={t("filters.all")}
          active={industry}
          onSelect={setIndustry}
          options={industries.map((value) => ({ value, label: categoryLabel(value) }))}
        />
        <FilterRow
          label={t("filters.operationLabel")}
          allLabel={t("filters.all")}
          active={operation}
          onSelect={(v) => setOperation(v as OperationKey | null)}
          options={operations.map((value) => ({ value, label: t(`operations.${value}`) }))}
        />
        <FilterRow
          label={t("filters.softwareLabel")}
          allLabel={t("filters.all")}
          active={software}
          onSelect={(v) => setSoftware(v as SoftwareKey | null)}
          options={software_.map((value) => ({ value, label: t(`software.${value}`) }))}
        />
      </div>

      <p className="mt-4 text-sm text-slate-500">
        {t("filters.resultsCount", { count: filtered.length })}
      </p>

      {filtered.length === 0 ? (
        <p className="mt-6 rounded-md border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          {t("filters.noResults")}
        </p>
      ) : (
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((card) => (
            <SolutionCard key={card.pack_code} card={card} t={t} categoryLabel={categoryLabel} />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterRow({
  label,
  allLabel,
  active,
  onSelect,
  options,
}: {
  label: string;
  allLabel: string;
  active: string | null;
  onSelect: (value: string | null) => void;
  options: { value: string; label: string }[];
}) {
  if (options.length === 0) return null;
  return (
    <div className="mt-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        <Pill active={active === null} onClick={() => onSelect(null)}>
          {allLabel}
        </Pill>
        {options.map((opt) => (
          <Pill key={opt.value} active={active === opt.value} onClick={() => onSelect(opt.value)}>
            {opt.label}
          </Pill>
        ))}
      </div>
    </div>
  );
}

function Pill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
        active
          ? "border-[#158A57] bg-[#158A57]/10 text-[#0A4A2D]"
          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900"
      }`}
    >
      {children}
    </button>
  );
}

function SolutionCard({
  card,
  t,
  categoryLabel,
}: {
  card: ExplorerCard;
  t: SolutionsT;
  categoryLabel: (category: string) => string;
}) {
  const { icon: Icon, bg, fg } = visualForCategory(card.industry_category);
  const requestDemoHref = `/contact?intent=demo-request&pack=${encodeURIComponent(card.pack_code)}`;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col hover:border-[#3DBB89] hover:shadow-md transition-all">
      <span className={`flex h-11 w-11 items-center justify-center rounded-lg ${bg}`}>
        <Icon className={`h-5 w-5 ${fg}`} strokeWidth={1.75} />
      </span>

      {/* Business-facing headline first: category eyebrow + plain-English name + one-line
          value-prop summary — no pack_code/"Golden Demo #N" jargon at this level (P1 #3). */}
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-[#158A57]">
        {categoryLabel(card.industry_category)}
      </p>
      <h3 className="mt-1 text-lg font-semibold text-slate-900">{card.pack_name}</h3>
      <p className="mt-2 text-sm text-slate-600 flex-1">{card.summary}</p>

      {(card.operations.length > 0 || card.software.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {card.operations.map((op) => (
            <span
              key={op}
              className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700"
            >
              {t(`operations.${op}`)}
            </span>
          ))}
          {card.software.map((sw) => (
            <span
              key={sw}
              className="rounded-full border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-500"
            >
              {t(`software.${sw}`)}
            </span>
          ))}
        </div>
      )}

      <div className="mt-3">
        <StatusBadge card={card} t={t} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href={`/solutions/${card.pack_code}`}
          className="inline-flex items-center rounded-md bg-slate-900 px-3.5 py-2 text-sm font-semibold text-white hover:bg-slate-700 transition-colors"
        >
          {t("viewDetails")}
        </Link>
        <Link
          href={requestDemoHref}
          className="inline-flex items-center rounded-md border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:border-slate-400 hover:text-slate-900 transition-colors"
        >
          {t("requestDemo")}
        </Link>
      </div>

      {card.has_live_demo && (
        <div className="mt-4 space-y-2 border-t border-slate-100 pt-4">
          {card.live_demos.map((demo) =>
            demo.url ? (
              <a
                key={demo.key}
                href={demo.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm font-medium text-[#158A57] hover:text-[#0A4A2D]"
              >
                <ArrowUpRight className="h-3.5 w-3.5 shrink-0" strokeWidth={2} />
                {demo.label}
                {demo.requires_login && (
                  <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                    {t("requiresLogin")}
                  </span>
                )}
              </a>
            ) : (
              <p key={demo.key} className="text-sm font-medium text-slate-400">
                {t("notDeployed", { label: demo.label })}
              </p>
            )
          )}
        </div>
      )}

      {/* Technical identifier, de-emphasized to a small monospace footer line rather than
          shown at the same visual priority as the business content above (P1 #3). */}
      <p className="mt-3 font-mono text-[10px] text-slate-300">{card.pack_code}</p>
    </div>
  );
}

function StatusBadge({ card, t }: { card: ExplorerCard; t: SolutionsT }) {
  if (card.has_live_demo) {
    return (
      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-[#158A57]/10 px-2.5 py-1 text-xs font-semibold text-[#0A4A2D]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#1FA76B]" />
        {t("badge.live")}
      </span>
    );
  }
  if (card.has_golden_demo) {
    return (
      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
        {t("badge.erp")}
      </span>
    );
  }
  return (
    <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">
      {t("badge.planned")}
    </span>
  );
}
