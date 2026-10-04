// Vietnamese translations for the three short, backend-sourced strings that `public_api.py`'s
// `get_industry_solutions()`/`get_industry_pack_detail()` always return in English (pack_name,
// summary, and each live_demos[].label) — the backend has no locale concept, so the raw API
// response is English regardless of which site locale the visitor is on. Everything else on the
// bilingual pages (`messages/{vi,en}.json`'s static chrome, `industryPackContent.ts`'s curated
// business-flow prose) was already fully bilingual; this file closes the one remaining gap: a
// Vietnamese visitor was seeing English pack titles/summaries/demo names on an otherwise-Vietnamese
// page. Translations here are meaning-accurate, not literal/machine translations, and keep
// internationally-used acronyms/proper nouns unchanged (GMP, QA/QC, CAPA, OOS, COA, FEFO, TPBVSK,
// "Golden Demo #N", demo company names) exactly as `industryPackContent.ts` already does.
//
// Every helper falls back to the raw (English) string whenever a pack_code/demo key isn't in the
// map below — this can only be reached if a 28th pack or demo is added to the backend before this
// file is updated to match, never for a key that exists today (all 27 packs and 7 demo keys,
// confirmed live via get_industry_solutions(), are covered).

const PACK_NAME_VI: Record<string, string> = {
  "IP-3PL-COLDCHAIN": "Dược phẩm 3PL / GSP / Chuỗi lạnh",
  "IP-AQUA-ENVIRONMENT": "Xử lý môi trường nuôi trồng thủy sản",
  "IP-AQUA-HATCHERY": "Trại giống thủy sản",
  "IP-AQUAFEED": "Thức ăn thủy sản",
  "IP-CONSUMER-DIST": "Phân phối Chăm sóc sức khỏe / Mỹ phẩm tiêu dùng",
  "IP-COSMETICS": "Mỹ phẩm",
  "IP-DMS": "Hệ thống Quản lý Tài liệu & Đào tạo (độc lập)",
  "IP-EAM": "EAM / CMMS / Hiệu chuẩn / Thẩm định (độc lập)",
  "IP-FEED": "Thức ăn chăn nuôi",
  "IP-FISH": "Nuôi cá",
  "IP-HATCHERY": "Trại ấp (Chăn nuôi)",
  "IP-INGREDIENT-TRADING": "Giao dịch nguyên liệu thức ăn chăn nuôi",
  "IP-LIMS": "Hệ thống Quản lý Thông tin Phòng thí nghiệm (độc lập)",
  "IP-LIVESTOCK-CATTLE": "Chăn nuôi — Bò",
  "IP-LIVESTOCK-PIG": "Chăn nuôi — Lợn",
  "IP-LIVESTOCK-POULTRY": "Chăn nuôi — Gia cầm",
  "IP-MEAT-PROCESSING": "Chế biến thịt",
  "IP-MEDICAL-DEVICE": "Thiết bị y tế",
  "IP-PHARMA": "Dược phẩm",
  "IP-PHARMACY": "Chuỗi nhà thuốc (bán lẻ/POS)",
  "IP-PREMIX": "Premix / Phụ gia thức ăn chăn nuôi",
  "IP-QMS": "Hệ thống Quản lý Chất lượng (độc lập)",
  "IP-SEAFOOD-PROCESSING": "Chế biến thủy hải sản",
  "IP-SHRIMP": "Nuôi tôm",
  "IP-SUPPLEMENT": "Thực phẩm bảo vệ sức khỏe / TPBVSK",
  "IP-VETERINARY": "Thú y",
  "IP-VETERINARY-BIOLOGICAL": "Sinh phẩm thú y / Vắc-xin",
};

const PACK_SUMMARY_VI: Record<string, string> = {
  "IP-3PL-COLDCHAIN":
    "Kho vận 3PL dược phẩm / GSP / chuỗi lạnh — nhận hàng đầu vào, kiểm dịch/giải phóng, xuất hàng theo FEFO, giám sát nhiệt độ và tính cước (Golden Demo #24).",
  "IP-AQUA-ENVIRONMENT":
    "Sản xuất sản phẩm xử lý môi trường nuôi trồng thủy sản — sửa đổi công thức, sản xuất, quản lý phiên bản nhãn và truy vết phân phối (Golden Demo #16).",
  "IP-AQUA-HATCHERY":
    "Quản lý trại giống thủy sản — sinh sản, ương nuôi ấu trùng/con giống và xuất bán (Golden Demo #18).",
  "IP-AQUAFEED":
    "Sản xuất thức ăn thủy sản — dữ liệu nền và quy trình sản xuất đầy đủ cho thức ăn nuôi trồng thủy sản (Golden Demo #15).",
  "IP-CONSUMER-DIST":
    "Phân phối hàng tiêu dùng chăm sóc sức khỏe/mỹ phẩm — chính sách giá, khuyến mãi, kiểm soát khu vực và hạn mức công nợ đại lý, quy trình bán hàng và đổi trả (Golden Demo #25).",
  "IP-COSMETICS":
    "Sản xuất mỹ phẩm — sản xuất bán thành phẩm và thành phẩm đóng gói, sửa đổi công thức/thiết kế bao bì, nghiên cứu độ ổn định, khiếu nại phân phối và tái chế (Golden Demo #21).",
  "IP-DMS":
    "Hệ thống Quản lý Tài liệu & Đào tạo (độc lập) — vòng đời tài liệu, kiểm soát phiên bản và phân công đào tạo (Golden Demo #4).",
  "IP-EAM":
    "EAM / CMMS / hiệu chuẩn / thẩm định (độc lập) — hiệu chuẩn thiết bị, đánh giá đạt chuẩn và theo dõi hỏng hóc/sửa chữa (Golden Demo #6).",
  "IP-FEED":
    "Sản xuất thức ăn chăn nuôi hỗn hợp — sửa đổi công thức, thay thế nguyên liệu, sản xuất và sắp xếp trình tự dây chuyền sản xuất (Golden Demo #7).",
  "IP-FISH": "Quản lý trại nuôi cá — thả giống, vận hành và thu hoạch (Golden Demo #17).",
  "IP-HATCHERY":
    "Quản lý trại ấp / nhân giống — lô trứng, ấp trứng, nở/phân loại, tiêm phòng và xuất bán (Golden Demo #14).",
  "IP-INGREDIENT-TRADING":
    "Giao dịch nguyên liệu/thức ăn chăn nuôi — lô hàng nhập khẩu, kiểm tra chất lượng lô của nhà cung cấp, hợp đồng và bán hàng, lịch sử giá và báo cáo lợi nhuận (Golden Demo #27).",
  "IP-LIMS":
    "Hệ thống Quản lý Thông tin Phòng thí nghiệm (độc lập) — chỉ tiêu, quy trình lấy mẫu/kiểm nghiệm, quy trình OOS và cấp CoA (Golden Demo #5).",
  "IP-LIVESTOCK-CATTLE":
    "Quản lý trang trại bò/bò sữa — phối giống, vận hành và quy trình bán hàng (Golden Demo #13).",
  "IP-LIVESTOCK-PIG":
    "Quản lý trang trại lợn — quy trình phối giống, vận hành trang trại và bán hàng, cùng đầy đủ các kiểm tra chất lượng dữ liệu (Golden Demo #11).",
  "IP-LIVESTOCK-POULTRY":
    "Quản lý trang trại gia cầm — thả nuôi, vận hành và quy trình bán hàng (Golden Demo #12).",
  "IP-MEAT-PROCESSING":
    "Chế biến thịt/sản phẩm động vật — nhận hàng, chế biến theo lô, kiểm tra chất lượng/đóng gói và truy vết phân phối/thu hồi (Golden Demo #28).",
  "IP-MEDICAL-DEVICE":
    "Sản xuất thiết bị y tế — đánh giá nhà cung cấp, kiểm tra đầu vào, lắp ráp, giải phóng và xử lý khiếu nại/truy vết (Golden Demo #22).",
  "IP-PHARMA":
    "Sản xuất dược phẩm GMP đầy đủ — sản xuất theo lô, giải phóng QA/QC, sai lệch/CAPA, kiểm soát tài liệu và hiệu chuẩn thiết bị (Golden Demo #1, demo chủ lực của nền tảng).",
  "IP-PHARMACY":
    "Chuỗi nhà thuốc bán lẻ/POS — bổ sung hàng, chuyển hàng liên cửa hàng, bán hàng/đổi trả tại POS, chặn hàng hết hạn và bảng điều khiển trung tâm (Golden Demo #23).",
  "IP-PREMIX":
    "Sản xuất premix / phụ gia thức ăn chăn nuôi — kiểm soát dung sai cân vi lượng, xác minh cân, sắp xếp trình tự và sản xuất (Golden Demo #26).",
  "IP-QMS":
    "Hệ thống Quản lý Chất lượng (độc lập) — sai lệch/CAPA, kiểm soát thay đổi, OOS/OOT, đánh giá nội bộ và thu hồi/rủi ro/chất lượng nhà cung cấp (Golden Demo #3).",
  "IP-SEAFOOD-PROCESSING":
    "Chế biến và xuất khẩu thủy hải sản — nhận hàng/phân loại, chế biến/đóng gói, giao hàng và thu hồi (Golden Demo #19).",
  "IP-SHRIMP": "Quản lý trại nuôi tôm — thả giống, vận hành trang trại và thu hoạch (Golden Demo #8).",
  "IP-SUPPLEMENT":
    "Sản xuất thực phẩm bảo vệ sức khỏe/TPBVSK — sửa đổi công thức, quản lý phiên bản thiết kế bao bì và giải phóng lô theo CoA (Golden Demo #20).",
  "IP-VETERINARY":
    "Sản xuất và phân phối dược phẩm thú y — sản xuất, sửa đổi công thức, thu hồi, quản lý phiên bản nhãn và thăm khám kỹ thuật đại lý/thú y (Golden Demo #9).",
  "IP-VETERINARY-BIOLOGICAL":
    "Sản xuất sinh phẩm/vắc-xin thú y — đã đăng ký là một Industry Pack, chưa có dữ liệu demo mẫu nào được xây dựng (dành cho một demo trong tương lai).",
};

// Keyed by the real, stable demo `key` (e.g. "WEB-01"), not pack_code — matches lib/api.ts's own
// LIVE_DEMO_URLS map. Demo/company proper nouns (e.g. "Demo Consumer Distribution Co.") are kept
// unchanged, same convention as industryPackContent.ts.
const DEMO_LABEL_VI: Record<string, string> = {
  "WEB-01": "WEB-01 — Trang doanh nghiệp + Danh mục sản phẩm (Demo Consumer Distribution Co., Golden Demo #25)",
  "WEB-02": "WEB-02 — Website thương hiệu / sản phẩm tiêu dùng (Demo Supplement Co., Golden Demo #20)",
  "WEB-03": "WEB-03 — Cổng khách hàng B2B / Đại lý (Demo Consumer Distribution Co., Golden Demo #25)",
  "WEB-04": "WEB-04 — Cổng nhà cung cấp / Báo giá (RFQ) (Demo Ingredient Trading Co., Golden Demo #27)",
  "WEB-05": "WEB-05 — Thương mại điện tử B2C (Demo Consumer Distribution Co., Golden Demo #25)",
  "WEB-06": "WEB-06 — Nhà thuốc trực tuyến (Demo Pharmacy Chain Co., Store A, Golden Demo #23)",
  "WEB-07": "WEB-07 — Cổng khách hàng trang trại / Dịch vụ kỹ thuật (Demo Vet Pharma Co., Golden Demo #10)",
};

export function localizedPackName(packCode: string, fallbackEn: string, locale: string): string {
  if (locale === "vi") return PACK_NAME_VI[packCode] ?? fallbackEn;
  return fallbackEn;
}

export function localizedPackSummary(packCode: string, fallbackEn: string, locale: string): string {
  if (locale === "vi") return PACK_SUMMARY_VI[packCode] ?? fallbackEn;
  return fallbackEn;
}

export function localizedDemoLabel(demoKey: string, fallbackEn: string, locale: string): string {
  if (locale === "vi") return DEMO_LABEL_VI[demoKey] ?? fallbackEn;
  return fallbackEn;
}
