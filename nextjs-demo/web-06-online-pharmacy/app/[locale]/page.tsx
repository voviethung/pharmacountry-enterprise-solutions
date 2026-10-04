import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { getPharmacyCatalog, formatVnd } from "@/lib/api";

// Force dynamic rendering — this page calls the real Frappe backend on every request.
// Without this, Next.js prerenders it once at Docker build time (when the backend isn't
// reachable from inside the build container) and serves that stale/fallback snapshot forever.
export const dynamic = "force-dynamic";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");

  let items: Awaited<ReturnType<typeof getPharmacyCatalog>> = [];
  try {
    items = await getPharmacyCatalog();
  } catch {
    items = [];
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 space-y-12">
      <section className="text-center space-y-4">
        <p className="text-sm font-semibold uppercase tracking-wide text-sky-700">
          {t("eyebrow")}
        </p>
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">{t("title")}</h1>
        <p className="mx-auto max-w-2xl text-slate-600">{t("lead")}</p>
        <div>
          <Link
            href="/shop"
            className="inline-block rounded-md bg-sky-600 px-6 py-3 font-semibold text-white hover:bg-sky-700"
          >
            {t("ctaShopNow")}
          </Link>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-slate-900">{t("availableNow")}</h2>
        {items.length === 0 ? (
          <p className="text-slate-500">{t("catalogUnavailable")}</p>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2">
            {/* item_code/category/item_name/description/price/uom are real catalog data from the
                connected Frappe backend — never translated, shown exactly as returned. */}
            {items.map((item) => (
              <Link
                key={item.item_code}
                href="/shop"
                className="block rounded-lg border border-slate-200 p-5 hover:border-sky-400 hover:shadow-sm"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-sky-700">
                  {item.category}
                </p>
                <h3 className="mt-1 text-lg font-semibold text-slate-900">{item.item_name}</h3>
                <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                <p className="mt-3 text-lg font-bold text-slate-900">
                  {formatVnd(item.price)}{" "}
                  <span className="text-sm font-normal text-slate-500">/ {item.uom}</span>
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg bg-slate-50 p-6 text-sm text-slate-600">
        <p className="font-semibold text-slate-800">{t("howItWorks.heading")}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>{t("howItWorks.item1")}</li>
          <li>{t("howItWorks.item2")}</li>
          <li>{t("howItWorks.item3")}</li>
          <li>{t("howItWorks.item4")}</li>
          <li>
            {t.rich("howItWorks.item5", {
              trackLink: (chunks) => (
                <Link href="/track" className="mx-1 text-sky-700 underline">
                  {chunks}
                </Link>
              ),
            })}
          </li>
        </ul>
      </section>
    </div>
  );
}
