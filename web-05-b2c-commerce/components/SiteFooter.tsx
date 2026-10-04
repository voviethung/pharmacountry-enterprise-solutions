import { getTranslations } from "next-intl/server";

export default async function SiteFooter() {
  const t = await getTranslations("footer");

  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-slate-500 space-y-1">
        <p>{t("line1")}</p>
        <p>{t("line2")}</p>
      </div>
    </footer>
  );
}
