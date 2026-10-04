import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getBrandProfile } from "@/lib/api";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return { title: t("ourStoryTitle") };
}

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function OurStoryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("ourStory");
  const profile = await getBrandProfile();

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
        {profile.company_name}
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">{t("title")}</h1>

      <div className="mt-8 space-y-6 text-lg leading-relaxed text-stone-700">
        <p>{profile.mission}</p>
        <p>{profile.philosophy}</p>
      </div>

      <section className="mt-12 rounded-xl border border-stone-200 bg-stone-50 p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          {t("formulation.heading")}
        </h2>
        <p className="mt-3 text-stone-600 leading-relaxed">
          {t("formulation.before")}
          <Link href="/product" className="font-medium text-emerald-800 hover:underline">
            {t("formulation.linkText")}
          </Link>
          .
        </p>
      </section>

      <section className="mt-8 rounded-xl border border-stone-200 bg-stone-50 p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          {t("madeIn.heading", { country: profile.country })}
        </h2>
        <p className="mt-3 text-stone-600 leading-relaxed">
          {t("madeIn.before", { companyName: profile.company_name })}
          <Link href="/product" className="font-medium text-emerald-800 hover:underline">
            {t("madeIn.linkText")}
          </Link>
          .
        </p>
      </section>
    </div>
  );
}
