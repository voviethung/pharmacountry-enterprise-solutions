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
  const technologyPositioning =
    locale === "vi"
      ? "Nền tảng được xây dựng trên Frappe/ERPNext — một nền tảng công nghệ mã nguồn mở đã được kiểm chứng — và được PharmaCountry mở rộng bằng các capability engine, Industry Pack, workflow, mô hình dữ liệu, AI, cổng/website chuyên dụng và kiến trúc triển khai đa khách hàng. Giá trị sản phẩm nằm ở lớp nghiệp vụ, cấu hình ngành, tích hợp và triển khai được xây dựng trên nền tảng đó, không phải ở việc che giấu công nghệ lõi."
      : "The platform is built on Frappe/ERPNext — a proven open-source technology foundation — and extended by PharmaCountry with capability engines, Industry Packs, workflows, data models, AI, dedicated portals/web applications, and multi-tenant deployment architecture. The product value is in the business, industry, integration, and implementation layer built on that foundation, not in obscuring the underlying core technology.";

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>

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
        <p>{technologyPositioning}</p>
        <p>{t("p3")}</p>
        <p>{t("p4")}</p>

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
