import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Mail, MapPin, Link2 } from "lucide-react";
import ContactForm from "@/components/ContactForm";

// Real, single, consistent contact address for this site — matches the pharmacountry.vn domain
// this Hub is deployed on. Not tied to any one person's name/direct line (per this rebrand's own
// honesty constraint: general company contact info is fine, a fabricated individual is not).
const CONTACT_EMAIL = "hello@pharmacountry.vn";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: t("contactTitle"),
    description: t("contactDescription"),
  };
}

// The form itself submits client-side to /api/contact (a real POST, see that route handler and
// lib/api.ts's submitContactLead()) — this page's own render has no per-request backend read, so
// it does not strictly need force-dynamic, but marking it explicitly anyway keeps this app's own
// established discipline ("never let Next.js silently prerender a page touching the backend")
// unambiguous for anyone editing this later.
export const dynamic = "force-dynamic";

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("contact");

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 max-w-2xl text-slate-600">{t("intro")}</p>

      <div className="mt-10 grid grid-cols-1 gap-10 md:grid-cols-[1fr_320px]">
        <ContactForm />

        {/* Company-info sidebar — real, honest, general-region contact facts (see this component's
            own build notes): no fabricated street address, phone number, named individual, or
            LinkedIn URL. */}
        <aside className="h-fit rounded-lg border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t("companyInfo.heading")}
          </h2>
          <p className="mt-3 text-sm text-slate-600">{t("companyInfo.intro")}</p>

          <div className="mt-6 space-y-5">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                {t("companyInfo.companyLabel")}
              </p>
              <p className="mt-1 font-semibold text-slate-900">{t("companyInfo.companyName")}</p>
              <p className="mt-1 text-sm text-slate-600">{t("companyInfo.companyDescription")}</p>
            </div>

            <div className="flex items-start gap-3">
              <Mail className="mt-0.5 h-4 w-4 shrink-0 text-[#158A57]" strokeWidth={1.75} />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  {t("companyInfo.emailLabel")}
                </p>
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="mt-1 block text-sm font-medium text-[#158A57] hover:text-[#0A4A2D] hover:underline"
                >
                  {CONTACT_EMAIL}
                </a>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[#158A57]" strokeWidth={1.75} />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  {t("companyInfo.locationLabel")}
                </p>
                <p className="mt-1 text-sm text-slate-900">{t("companyInfo.locationValue")}</p>
              </div>
            </div>

            {/* No real LinkedIn URL exists for this account yet — shown as a plain label (no
                href) rather than a fabricated link, per this rebrand's own honesty constraint. */}
            <div className="flex items-start gap-3">
              <Link2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" strokeWidth={1.75} />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  {t("companyInfo.linkedinLabel")}
                </p>
                <p className="mt-1 text-sm text-slate-500">{t("companyInfo.linkedinNote")}</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
