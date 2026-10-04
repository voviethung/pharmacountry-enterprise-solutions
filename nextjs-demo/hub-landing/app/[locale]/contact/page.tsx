import type { Metadata } from "next";
import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Mail, MapPin, Phone } from "lucide-react";
import ContactForm from "@/components/ContactForm";

// Real, single, consistent contact details for this site. Not tied to any one person's
// name/direct line (per this rebrand's own honesty constraint: general company contact info is
// fine, a fabricated individual is not).
const CONTACT_EMAIL = "contact.pharmacountry@gmail.com";
const CONTACT_PHONE_DISPLAY = "0963 573 588";
const CONTACT_PHONE_TEL = "+84963573588";
// Zalo's own "start a chat" URL scheme: the leading 0 is replaced with the VN country code 84,
// no other formatting. Opens the Zalo app (or zalo.me's own web fallback) straight to this
// number's chat, same thing the QR code below encodes.
const ZALO_URL = "https://zalo.me/84963573588";

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

        {/* Company-info sidebar — real, honest contact facts (see this component's own build
            notes): no fabricated named individual or LinkedIn URL. */}
        <aside className="h-fit rounded-lg border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t("companyInfo.heading")}
          </h2>
          <p className="mt-2 font-semibold text-slate-900">{t("companyInfo.companyName")}</p>

          <div className="mt-6 space-y-5">
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
              <Phone className="mt-0.5 h-4 w-4 shrink-0 text-[#158A57]" strokeWidth={1.75} />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  {t("companyInfo.phoneLabel")}
                </p>
                <a
                  href={`tel:${CONTACT_PHONE_TEL}`}
                  className="mt-1 block text-sm font-medium text-[#158A57] hover:text-[#0A4A2D] hover:underline"
                >
                  {CONTACT_PHONE_DISPLAY}
                </a>
                <a
                  href={ZALO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 block text-xs text-slate-500 hover:text-[#158A57] hover:underline"
                >
                  {t("companyInfo.zaloLinkText")}
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

            <div className="border-t border-slate-200 pt-5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                {t("companyInfo.zaloQrLabel")}
              </p>
              <a href={ZALO_URL} target="_blank" rel="noopener noreferrer" className="mt-2 block w-fit">
                <Image
                  src="/images/zalo-qr.png"
                  alt={t("companyInfo.zaloQrAlt")}
                  width={120}
                  height={120}
                  className="rounded-md border border-slate-200 bg-white p-1.5"
                />
              </a>
              <p className="mt-2 text-xs text-slate-500">{t("companyInfo.zaloQrHint")}</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
