import type { Metadata } from "next";
import Image from "next/image";
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

      {/* Real About-page image (generated from IMAGE_PROMPTS.md's "About-page image" prompt). */}
      <div className="mt-8 relative h-56 overflow-hidden rounded-xl border border-[#158A57]/20 sm:h-72">
        <Image
          src="/images/about-team.webp"
          alt={t("heroImageAlt")}
          fill
          sizes="(min-width: 768px) 768px, 100vw"
          className="object-cover"
        />
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
