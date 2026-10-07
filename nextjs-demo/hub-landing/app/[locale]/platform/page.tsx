import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { ArrowRight, Layers3, Network, ShieldCheck } from "lucide-react";

const LAYERS = [
  {
    titleVi: "1. Frappe / ERPNext business core",
    titleEn: "1. Frappe / ERPNext business core",
    textVi: "Lõi giao dịch doanh nghiệp, dữ liệu chủ, chứng từ, workflow, quyền và nền tảng Frappe/ERPNext đã được kiểm chứng.",
    textEn: "Enterprise transactions, master data, documents, workflows, permissions, and the proven Frappe/ERPNext foundation.",
  },
  {
    titleVi: "2. 15 Capability Engines",
    titleEn: "2. 15 Capability Engines",
    textVi: "ERP, CRM, Procurement, WMS, Manufacturing, QMS, DMS, LIMS, EAM, Farm, Traceability, Commerce, AI, HR và R&D/RA dùng chung giữa nhiều ngành.",
    textEn: "ERP, CRM, Procurement, WMS, Manufacturing, QMS, DMS, LIMS, EAM, Farm, Traceability, Commerce, AI, HR, and R&D/RA reused across industries.",
  },
  {
    titleVi: "3. Product Editions",
    titleEn: "3. Product Editions",
    textVi: "Starter, Professional và Enterprise quyết định tập capability được bật cho một site khách hàng.",
    textEn: "Starter, Professional, and Enterprise determine the capability set enabled for a customer site.",
  },
  {
    titleVi: "4. Industry Packs",
    titleEn: "4. Industry Packs",
    textVi: "Ngành dược, TPCN & mỹ phẩm, thiết bị y tế, thú y, thức ăn chăn nuôi, chăn nuôi, thủy sản và chế biến dùng cùng một nền tảng nhưng có vai trò, dữ liệu và quy trình chuyên ngành khác nhau.",
    textEn: "Pharma, nutraceuticals & cosmetics, medical devices, veterinary, animal feed, livestock, aquaculture, and processing share one platform with industry-specific roles, data, and workflows.",
  },
  {
    titleVi: "5. Tenant & Subscription",
    titleEn: "5. Tenant & Subscription",
    textVi: "Mỗi khách hàng có site riêng, Edition riêng và vòng đời subscription riêng; provisioning site mới đã được kiểm thử end-to-end trên fresh sites.",
    textEn: "Each customer has a separate site, Edition, and subscription lifecycle; fresh-site provisioning has been tested end to end.",
  },
  {
    titleVi: "6. Public apps & portals",
    titleEn: "6. Public apps & portals",
    textVi: "Next.js được dùng khi cần UX riêng cho website, commerce, cổng đại lý, cổng nhà cung cấp, nhà thuốc hoặc farm portal; nghiệp vụ lõi vẫn nằm ở Frappe/ERPNext.",
    textEn: "Next.js is used when a dedicated UX is justified for websites, commerce, dealer/supplier portals, pharmacy, or farm portals; the business core stays in Frappe/ERPNext.",
  },
] as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const vi = locale === "vi";
  return {
    title: vi
      ? "Nền tảng — PharmaCountry Enterprise Solutions"
      : "Platform — PharmaCountry Enterprise Solutions",
    description: vi
      ? "Kiến trúc nền tảng đa ngành của PharmaCountry: capability engines, Editions, Industry Packs, tenant provisioning và subscription."
      : "PharmaCountry's multi-industry platform architecture: capability engines, Editions, Industry Packs, tenant provisioning, and subscriptions.",
  };
}

export default async function PlatformPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const vi = locale === "vi";

  return (
    <div>
      <section className="border-b border-slate-200 bg-slate-900 text-white">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-[#3DBB89]">
            <Network className="h-4 w-4" strokeWidth={1.75} />
            {vi ? "Kiến trúc nền tảng" : "Platform architecture"}
          </p>
          <h1 className="mt-4 max-w-4xl text-3xl font-bold tracking-tight sm:text-4xl">
            {vi ? "Một product platform dùng chung cho nhiều ngành — không phải hàng chục ERP tách rời." : "One shared product platform for many industries — not dozens of separate ERPs."}
          </h1>
          <p className="mt-5 max-w-3xl text-lg leading-relaxed text-slate-300">
            {vi
              ? "PharmaCountry tách năng lực dùng chung, cấu hình sản phẩm và cấu hình ngành thành các lớp rõ ràng. Nhờ vậy cùng một codebase có thể phục vụ doanh nghiệp sản xuất, phân phối, bán lẻ và trang trại với mức độ kiểm soát khác nhau."
              : "PharmaCountry separates shared capabilities, product packaging, and industry configuration into clear layers. The same codebase can therefore serve manufacturing, distribution, retail, and farm operations with different control requirements."}
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {LAYERS.map((layer, index) => (
            <article key={index} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#158A57]/10">
                  {index < 4 ? (
                    <Layers3 className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
                  ) : (
                    <ShieldCheck className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
                  )}
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900">{vi ? layer.titleVi : layer.titleEn}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{vi ? layer.textVi : layer.textEn}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-14">
          <h2 className="text-2xl font-semibold text-slate-900">
            {vi ? "Từ nền tảng đến gói khách hàng sử dụng" : "From platform architecture to the customer's plan"}
          </h2>
          <div className="mt-7 overflow-x-auto rounded-lg border border-slate-200 bg-white p-6">
            <div className="min-w-[720px] text-center font-medium text-slate-700">
              Capability Engines <span className="mx-3 text-slate-400">+</span> Edition
              <span className="mx-3 text-slate-400">+</span> Industry Pack
              <span className="mx-3 text-slate-400">→</span> Tenant Site
              <span className="mx-3 text-slate-400">→</span> Subscription
            </div>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/products" className="inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white hover:bg-[#0A4A2D]">
              {vi ? "Xem sản phẩm" : "Explore products"}
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/pricing" className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:border-slate-400">
              {vi ? "Xem Edition & bảng giá" : "View Editions & pricing"}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
