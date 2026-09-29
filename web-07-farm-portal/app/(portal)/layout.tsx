import { requireSession } from "@/lib/auth";
import PortalHeader from "@/components/PortalHeader";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  // Every page under this route group is protected: no valid session -> redirect("/login")
  // happens inside requireSession() itself, before any farm data is ever fetched.
  const session = await requireSession();

  return (
    <div className="min-h-screen">
      <PortalHeader customerName={session.customerName} />
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
