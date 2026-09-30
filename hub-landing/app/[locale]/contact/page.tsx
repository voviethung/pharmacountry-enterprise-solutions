import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import ContactForm from "@/components/ContactForm";

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
    <div className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
      <p className="mt-3 text-slate-600">{t("intro")}</p>

      <div className="mt-10">
        <ContactForm />
      </div>
    </div>
  );
}
