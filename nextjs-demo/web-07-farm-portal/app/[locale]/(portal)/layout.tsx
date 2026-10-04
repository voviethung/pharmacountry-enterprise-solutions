import { setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import PortalHeader from "@/components/PortalHeader";

// Force dynamic rendering for this entire route group — every page under it is login-gated and
// reads the session cookie via requireSession(). A login-gated segment can never be static; set
// here too (in addition to each page.tsx) so the whole subtree is unambiguously dynamic.
export const dynamic = "force-dynamic";

export default async function PortalLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  // Every page under this route group is protected: no valid session -> redirect("/login")
  // happens inside requireSession() itself (via @/i18n/navigation's locale-aware redirect),
  // before any farm data is ever fetched.
  const session = await requireSession();

  return (
    <div className="min-h-screen">
      <PortalHeader customerName={session.customerName} />
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
