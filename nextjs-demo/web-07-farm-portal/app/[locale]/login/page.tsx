import { getTranslations, setRequestLocale } from "next-intl/server";
import { redirect } from "@/i18n/navigation";
import { getCurrentSession } from "@/lib/auth";
import LoginForm from "@/components/LoginForm";
import LocaleSwitcher from "@/components/LocaleSwitcher";

// Force dynamic rendering — this reads the session cookie (to bounce an already-logged-in
// farm straight to /dashboard). Without this, Next.js could prerender it once at Docker build
// time and bake in a stale "not logged in" snapshot forever.
export const dynamic = "force-dynamic";

export default async function LoginPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("login");

  const session = await getCurrentSession();
  if (session) redirect({ href: "/dashboard", locale });

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-4 flex justify-end">
          <LocaleSwitcher />
        </div>
        <div className="mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Demo Vet Pharma Co.
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{t("heading")}</h1>
          <p className="mt-2 text-sm text-slate-500">{t("subheading")}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <LoginForm />
        </div>
        <p className="mt-4 text-center text-xs text-slate-400">{t("footerNote")}</p>
      </div>
    </div>
  );
}
