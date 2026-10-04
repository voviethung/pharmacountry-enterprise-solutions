import { useTranslations } from "next-intl";

export default function SiteFooter() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-slate-500 space-y-1">
        <p>{t("line1")}</p>
        <p>{t("line2")}</p>
        <p>{t("line3")}</p>
      </div>
    </footer>
  );
}
