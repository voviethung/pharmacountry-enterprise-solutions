import type { Metadata } from "next";
import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import {
  MapPin,
  Layers,
  Cloud,
  ListChecks,
  LifeBuoy,
  ShieldCheck,
} from "lucide-react";

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

        {/* Enterprise-vendor-profile sections (P2 addition) — company/location, technology,
            deployment options, implementation methodology, support, and security/data isolation.
            Each section is grounded in what this platform actually runs on and what has actually
            been built and verified (see this file's own build notes for the sourcing). */}
        <div className="pt-4 space-y-10">
          <section>
            <div className="flex items-center gap-2.5">
              <MapPin className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.companyHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.companyText")}</p>
          </section>

          <section>
            <div className="flex items-center gap-2.5">
              <Layers className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.techHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.techText")}</p>
          </section>

          <section>
            <div className="flex items-center gap-2.5">
              <Cloud className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.deploymentHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.deploymentIntro")}</p>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              {(["Cloud", "Dedicated", "OnPrem"] as const).map((key) => (
                <div key={key} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">
                    {t(`vendorProfile.deployment${key}Label`)}
                  </p>
                  <p className="mt-1.5 text-sm text-slate-600">
                    {t(`vendorProfile.deployment${key}Text`)}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-sm text-slate-500">{t("vendorProfile.deploymentNote")}</p>
          </section>

          <section>
            <div className="flex items-center gap-2.5">
              <ListChecks className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.methodologyHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.methodologyIntro")}</p>
            <ol className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-5">
              {(["discovery", "configuration", "migration", "training", "goLive"] as const).map(
                (step, i) => (
                  <li key={step} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold text-[#158A57]">{i + 1}</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {t(`vendorProfile.methodologySteps.${step}.label`)}
                    </p>
                    <p className="mt-1.5 text-sm text-slate-600">
                      {t(`vendorProfile.methodologySteps.${step}.text`)}
                    </p>
                  </li>
                )
              )}
            </ol>
          </section>

          <section>
            <div className="flex items-center gap-2.5">
              <LifeBuoy className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.supportHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.supportText")}</p>
          </section>

          <section>
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="h-5 w-5 text-[#158A57]" strokeWidth={1.75} />
              <h2 className="text-xl font-semibold text-slate-900">
                {t("vendorProfile.securityHeading")}
              </h2>
            </div>
            <p className="mt-3">{t("vendorProfile.securityText")}</p>
          </section>
        </div>

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
