import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("aboutTitle"),
    description: t("aboutDescription"),
  };
}

export default async function AboutPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("about");

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>

      {/* TODO: replace with a real About-page image once generated — see IMAGE_PROMPTS.md
          ("About-page image"). CSS-only placeholder in the real brand green, not a broken
          <img> tag, until real imagery exists. */}
      <div
        className="mt-8 flex h-56 items-center justify-center rounded-xl border border-[#158A57]/20 sm:h-72"
        style={{
          background:
            "linear-gradient(135deg, #3DBB89 0%, #158A57 45%, #0A4A2D 100%)",
        }}
        role="img"
        aria-label={t("heroImageAlt")}
      >
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
          <rect
            x="10"
            y="10"
            width="44"
            height="44"
            rx="6"
            fill="none"
            stroke="#ffffff"
            strokeOpacity="0.55"
            strokeWidth="2.5"
            transform="rotate(45 32 32)"
          />
        </svg>
      </div>

      <div className="mt-8 space-y-6 text-slate-700 leading-relaxed">
        <p>{t("p1")}</p>
        <p>{t("p2")}</p>
        <p>{t("p3")}</p>
        <p>{t("p4")}</p>

        <h2 className="text-xl font-semibold text-slate-900 pt-4">{t("contactHeading")}</h2>
        <p>
          {t("contactText")}{" "}
          <Link href="/contact" className="font-medium text-[#158A57] underline">
            {t("contactLink")}
          </Link>
        </p>
      </div>
    </div>
  );
}
