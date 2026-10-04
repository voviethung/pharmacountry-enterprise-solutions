import { requireSession } from "@/lib/auth";
import PortalHeader from "@/components/PortalHeader";

// Force dynamic rendering — every page under this route group is session/login-gated
// (requireSession() reads the session cookie and redirects to /login if absent). A
// login-gated layout/page must never be statically prerendered at Docker build time.
export const dynamic = "force-dynamic";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  // Every page under this route group is protected: no valid session -> redirect("/login")
  // happens inside requireSession() itself, before any dealer data is ever fetched.
  const session = await requireSession();

  return (
    <div className="min-h-screen">
      <PortalHeader customerName={session.customerName} />
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
