import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/auth";
import LoginForm from "@/components/LoginForm";

export default async function LoginPage() {
  const session = await getCurrentSession();
  if (session) redirect("/dashboard");

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
            Demo Ingredient Trading Co.
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Supplier Portal</h1>
          <p className="mt-2 text-sm text-slate-500">
            Sign in with your supplier account to see your own RFQs, quotations, purchase orders,
            deliveries, documents and qualification status.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <LoginForm />
        </div>
        <p className="mt-4 text-center text-xs text-slate-400">
          Test supplier credentials are documented in this app&apos;s README — never hardcoded on
          this page.
        </p>
      </div>
    </div>
  );
}
