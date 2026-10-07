import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { ArrowRight, Boxes, CheckCircle2 } from "lucide-react";

const PRODUCTS = [
  ["ERP Core", "Nền tảng ERP lõi cho tài chính, dữ liệu chủ, giao dịch và vận hành doanh nghiệp.", "Core ERP foundation for finance, master data, transactions, and enterprise operations."],
  ["CRM & Sales", "Quản lý khách hàng, cơ hội, báo giá và bán hàng.", "Customer, opportunity, quotation, and sales management."],
  ["Procurement", "Yêu cầu mua, nhà cung cấp, báo giá, đơn mua và phê duyệt.", "Purchase requests, suppliers, quotations, purchase orders, and approvals."],
  ["WMS & Logistics", "Kho, vị trí, tồn kho, luân chuyển và vận hành logistics.", "Warehouse, location, inventory, movement, and logistics operations."],
  ["Manufacturing / MRP", "BOM, kế hoạch, lệnh sản xuất, cấp phát và thực thi sản xuất.", "BOM, planning, work orders, material issue, and manufacturing execution."],
  ["QMS", "Deviation, CAPA, change control, complaint, recall và quản lý chất lượng.", "Deviation, CAPA, change control, complaints, recalls, and quality management."],
  ["DMS & Training", "Kiểm soát tài liệu, hồ sơ, phân phối, đào tạo và hiệu lực tài liệu.", "Controlled documents, records, distribution, training, and document effectiveness."],
  ["LIMS / Laboratory", "Quản lý kiểm nghiệm, phương pháp, tiêu chuẩn, thiết bị và dữ liệu phòng thí nghiệm.", "Laboratory testing, methods, standards, instruments, and laboratory data."],
  ["EAM / CMMS / Validation", "Thiết bị, bảo trì, hiệu chuẩn, qualification và validation.", "Assets, maintenance, calibration, qualification, and validation."],
  ["Farm Management", "Quản lý trang trại, đàn/ao, thức ăn, tăng trưởng, FCR và thu hoạch.", "Farm, flock/pond, feed, growth, FCR, and harvest management."],
  ["Traceability", "Truy xuất lô, nguyên liệu, sản xuất, kho và phân phối đầu-cuối.", "End-to-end batch, material, manufacturing, inventory, and distribution traceability."],
  ["Commerce / Portal", "Website, cổng đại lý, nhà cung cấp, thương mại điện tử và ứng dụng khách hàng.", "Websites, dealer portals, supplier portals, commerce, and customer applications."],
  ["AI & Automation Platform", "AI Gateway, trợ lý nghiệp vụ, RAG theo phân quyền và tự động hóa có kiểm soát.", "AI Gateway, business copilots, permission-aware RAG, and governed automation."],
  ["HR Performance & Competency", "Năng lực, KPI, đánh giá hiệu suất, đào tạo và phát triển nhân sự.", "Competency, KPI, performance review, training, and people development."],
  ["R&D & Regulatory Affairs (RA)", "Công thức, thử nghiệm, tiêu chuẩn, hồ sơ đăng ký và quản lý thay đổi sản phẩm.", "Formulation, trials, specifications, regulatory dossiers, and product-change management."],
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
      ? "Sản phẩm — PharmaCountry Enterprise Solutions"
      : "Products — PharmaCountry Enterprise Solutions",
    description: vi
      ? "15 capability engine dùng chung tạo thành nền tảng phần mềm doanh nghiệp đa ngành của PharmaCountry."
      : "The 15 shared capability engines that form PharmaCountry's multi-industry enterprise software platform.",
  };
}

export default async function ProductsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const vi = locale === "vi";

  return (
    <div>
      <section className="border-b border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-[#158A57]">
            <Boxes className="h-4 w-4" strokeWidth={1.75} />
            {vi ? "Danh mục sản phẩm" : "Product catalog"}
          </p>
          <h1 className="mt-3 max-w-3xl text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {vi ? "Một nền tảng. Chọn đúng năng lực doanh nghiệp cần." : "One platform. Choose the capabilities your business needs."}
          </h1>
          <p className="mt-5 max-w-3xl text-lg leading-relaxed text-slate-600">
            {vi
              ? "PharmaCountry không phải một ERP chỉ dành cho ngành dược. Nền tảng gồm 15 capability engine dùng chung; Edition và Industry Pack quyết định doanh nghiệp nào sử dụng những năng lực nào."
              : "PharmaCountry is not a pharma-only ERP. The platform is built from 15 shared capability engines; Editions and Industry Packs determine which capabilities each business uses."}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/pricing" className="inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white hover:bg-[#0A4A2D]">
              {vi ? "Xem gói & bảng giá" : "View plans & pricing"}
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/solutions" className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:border-slate-400">
              {vi ? "Xem giải pháp theo ngành" : "Explore industry solutions"}
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {PRODUCTS.map(([name, viText, enText]) => (
            <article key={name} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#158A57]/10">
                  <CheckCircle2 className="h-5 w-5 text-[#0A4A2D]" strokeWidth={1.75} />
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900">{name}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{vi ? viText : enText}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 bg-slate-900">
        <div className="mx-auto max-w-6xl px-6 py-14 text-white">
          <h2 className="text-2xl font-semibold">
            {vi ? "Không cần mua toàn bộ nền tảng ngay từ đầu." : "You do not need to buy the whole platform on day one."}
          </h2>
          <p className="mt-3 max-w-3xl text-slate-300">
            {vi
              ? "Starter, Professional và Enterprise kết hợp các capability engine theo mức độ sử dụng và ngành. Doanh nghiệp có thể bắt đầu nhỏ rồi mở rộng khi quy trình tăng lên."
              : "Starter, Professional, and Enterprise combine capability engines by operating depth and industry. A business can start smaller and expand as its processes grow."}
          </p>
          <Link href="/pricing" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#3DBB89] hover:text-white">
            {vi ? "So sánh các Edition" : "Compare Editions"}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
