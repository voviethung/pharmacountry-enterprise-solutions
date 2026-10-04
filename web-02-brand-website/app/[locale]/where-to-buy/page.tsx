import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { getBrandProduct, getBrandProfile } from "@/lib/api";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return { title: t("whereToBuyTitle") };
}

// This page is intentionally narrative-only — see this app's README for why. It does not
// call out to, or claim integration with, any real distributor/retailer system. The platform
// already has a real distributor demo (WEB-01, nextjs-demo/web-01-corporate-catalog, backed
// by Golden Demo #25's "Demo Consumer Distribution Co.") that actually resells this exact
// product (VITC-1000-EFF) at a real price — this page references that relationship in plain
// prose, without wiring up a live cross-app integration that this demo stage doesn't need.
//
// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function WhereToBuyPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("whereToBuy");
  const [profile, product] = await Promise.all([getBrandProfile(), getBrandProduct()]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
        {profile.company_name}
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">
        {t("title", { productName: product.item_name })}
      </h1>
      <p className="mt-4 text-lg text-stone-600 leading-relaxed">
        {t("intro", { productName: product.item_name, country: profile.country })}
      </p>

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="rounded-lg border border-stone-200 bg-white p-6">
          <h2 className="font-semibold text-stone-900">{t("pharmacy.heading")}</h2>
          <p className="mt-2 text-sm text-stone-600">
            {t("pharmacy.body", { productName: product.item_name })}
          </p>
        </div>
        <div className="rounded-lg border border-stone-200 bg-white p-6">
          <h2 className="font-semibold text-stone-900">{t("retail.heading")}</h2>
          <p className="mt-2 text-sm text-stone-600">{t("retail.body")}</p>
        </div>
      </div>

      <section className="mt-12 rounded-xl border border-stone-200 bg-stone-50 p-6 text-sm text-stone-600">
        <p>
          <strong className="text-stone-900">{t("note.label")}</strong> {t("note.part1")}
          <strong>{t("note.strong")}</strong>
          {t("note.part2")}
        </p>
      </section>
    </div>
  );
}
