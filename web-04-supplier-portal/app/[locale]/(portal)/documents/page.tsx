import { getTranslations, setRequestLocale } from "next-intl/server";
import { requireSession } from "@/lib/auth";
import { getMyDocuments } from "@/lib/api";

// Force dynamic rendering — login-gated page, fetches this supplier's own live documents on
// every request. See app/[locale]/(portal)/dashboard/page.tsx for the full reasoning.
export const dynamic = "force-dynamic";

export default async function DocumentsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("documents");

  const session = await requireSession();
  const docs = await getMyDocuments(session.frappeSid);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("heading")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("subhead", { supplierName: session.supplierName })}
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <Th>{t("table.type")}</Th>
              <Th>{t("table.reference")}</Th>
              <Th>{t("table.date")}</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {docs.map((d, i) => (
              <tr key={i}>
                <td className="px-4 py-3 text-slate-600">{d.type}</td>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{d.title}</p>
                  <p className="text-xs text-slate-400">
                    {d.reference_doctype} · {d.reference_name}
                  </p>
                </td>
                <td className="px-4 py-3 text-slate-600">{d.date || "—"}</td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-slate-400">
                  {t("empty")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
