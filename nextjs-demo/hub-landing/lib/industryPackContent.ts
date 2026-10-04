// Curated, per-Industry-Pack "what this demo actually proves" content for the Hub's
// `/solutions/[packCode]` detail page.
//
// SOURCING (read before editing): every field below is transcribed/paraphrased from this
// platform's own real, already-written engineering documentation —
// `documents/project_status.md`'s Phase 3-6 Golden Demo write-ups and
// `documents/productization/00_demo_platform_master_plan.md`'s DEMO 01-32 test-ID sections
// (both in the `enterprise-platform` repo) — never invented marketing copy. Test IDs
// (e.g. "Q01"-"Q08") are this platform's own real, documented acceptance-criteria codes;
// `testDescriptions` paraphrase the real text next to each ID; `businessFlowSummary` paraphrases
// project_status.md's own real narrative for that golden demo; `notableBugsFixed` are real,
// documented incidents from that demo's build, not illustrative examples.
//
// WHY A CURATED FILE, NOT A LIVE BACKEND CALL: this content's source of truth
// (`project_status.md`) is static engineering documentation, not live transactional data — it
// changes only when a human writes a new demo up, not per-request. Building a new backend
// endpoint that re-parses a markdown file at runtime would add real fragility (markdown
// structure drift, Docker build-time-vs-runtime path issues — see this repo's own Dockerfile
// comments) for zero benefit over checking a reviewed extract into this frontend's own repo,
// which is exactly how `public_api.py`'s own `_PACK_SUMMARIES` dict already treats this same
// class of content one step up (a short one-liner instead of this page's fuller detail).
//
// LANGUAGE: fully bilingual. Each pack's translatable prose (`testDescriptions`,
// `businessFlowSummary`, `notableBugsFixed`) is authored twice — once in English (the original,
// sourced directly from the internal engineering documentation described above) and once in
// Vietnamese (a careful, meaning-accurate translation for a Vietnamese-speaking business/
// technical audience, not a literal or machine translation). Internationally-used ERP/pharma/
// manufacturing acronyms that a real Vietnamese-language industry document would keep as-is
// (FEFO, BOM, QC/QA, CAPA, SOP, OOS, IQ/OQ/PQ, CoA, FCR, 3PL, etc.) are kept in their English
// form in the Vietnamese text too, exactly as real bilingual Vietnamese ERP/pharma writing does.
// Test IDs (e.g. "Q01") and demo/company proper nouns are identifiers, not prose, and are shared
// unchanged across both languages. `getPackContent(packCode, locale)` selects the right language,
// falling back to English if a Vietnamese variant is ever missing for a given pack. The detail
// page's own STATIC chrome (headings, labels) has always been fully bilingual via
// messages/{vi,en}.json, independent of this file.
//
// COVERAGE: all 26 of the 27 real Industry Packs that have an actual golden demo (has_golden_demo
// = true, confirmed live) have an entry here, each with full English AND Vietnamese content. The
// 27th, IP-VETERINARY-BIOLOGICAL, genuinely has zero seed data (confirmed live via `Industry Pack
// Seed` query) — it deliberately has NO entry in this map; see `NOT_YET_BUILT_NOTE` below for the
// one honest, sourced sentence the detail page shows for it instead (the master plan's own
// phase-1-scoped, never-built VB01-VB06 intent). `NOT_YET_BUILT_NOTE` itself remains English-only
// for the same reason it always did not carry curated bilingual content: it is a single narrow
// disclosure sentence rather than demo content, and is intentionally kept in one place; a
// Vietnamese rendering can be added the same way as the rest of this file if desired later.

/** One language's worth of a pack's translatable prose. */
export interface LocalizedPackText {
  /** id -> short, real, paraphrased description of what that test proves, in this language. */
  testDescriptions: Record<string, string>;
  /** 2-4 real sentences paraphrasing the demo's actual business flow, in this language. */
  businessFlowSummary: string;
  /** Real, documented bugs found/fixed while building this demo (0-3 items), in this language. */
  notableBugsFixed?: string[];
}

interface IndustryPackContentSource {
  /** e.g. "Golden Demo #1" or "Golden Demo #9 & #10" when a pack spans two numbered demos. */
  goldenDemoLabel: string;
  /** Real demo company/site name used in the seed data, when the source text names one. Kept
   *  unchanged across locales — it is a proper noun/identifier, not prose. */
  companyName?: string;
  /** Real, documented acceptance-criteria/test IDs for this demo (e.g. ["Q01", ..., "Q08"]).
   *  Kept unchanged across locales — identifiers, not prose. */
  testIds: string[];
  /**
   * Test IDs in `testIds` that the master plan documents as intended scope, but which
   * project_status.md's own write-up does not separately confirm as built-and-verified for
   * this specific golden demo (usually because a later, related golden demo realized the same
   * proof instead). Rendered with a distinct, honest "spec'd" marker rather than silently
   * listed as equally proven as everything else. Kept unchanged across locales.
   */
  unconfirmedTestIds?: string[];
  en: LocalizedPackText;
  vi: LocalizedPackText;
}

/** Locale-resolved shape the detail page actually renders. */
export interface IndustryPackContent {
  goldenDemoLabel: string;
  companyName?: string;
  testIds: string[];
  testDescriptions: Record<string, string>;
  unconfirmedTestIds?: string[];
  businessFlowSummary: string;
  notableBugsFixed?: string[];
}

export const NOT_YET_BUILT_PACK_CODE = "IP-VETERINARY-BIOLOGICAL";

// The one honest, sourced sentence for the pack with no golden demo at all — paraphrased from
// the master plan's own DEMO 15 section, which documents an INTENDED (never built) VB01-VB06
// test scope explicitly marked "Scope phase 1" with the caveat "do not claim this is a full
// biopharma MES at this phase."
export const NOT_YET_BUILT_NOTE =
  "This pack has zero seed data or documented test IDs — confirmed directly against the live registry, not assumed. The platform's own master plan does describe an intended future scope for it (seed/strain traceability, biological batch genealogy, cold-storage handling, QC-gated release, and recall trace, referenced there as tests VB01–VB06), explicitly scoped as \"phase 1\" and explicitly not claimed to be a full biopharma manufacturing execution system — but none of that was ever actually built: no seed function, no seeded company, no verifiable demo.";

const PACK_CONTENT_SOURCE: Record<string, IndustryPackContentSource> = {
  "IP-PHARMA": {
    goldenDemoLabel: "Golden Demo #1 & #2",
    companyName: "Demo Pharma Co.",
    testIds: [
      "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10",
      "PD01", "PD02", "PD03", "PD04", "PD05", "PD06", "PD07",
    ],
    unconfirmedTestIds: ["P02", "P03", "P04", "P07", "P08", "P09", "P10"],
    en: {
      testDescriptions: {
        P01: "Raw material can't be issued from Quarantine straight into production",
        P02: "Only a Released-status batch may be issued",
        P03: "A Work Order must use the currently effective BOM version",
        P04: "Consumption beyond tolerance needs a warning or approval",
        P05: "An out-of-limit in-process QC check raises a real quality event",
        P06: "Finished goods without QA release can't move to the Released warehouse",
        P07: "Batch genealogy traces raw material through to finished goods",
        P08: "A recall report traces finished goods to the customers who received them",
        P09: "The production user can't self-approve their own QA release",
        P10: "An obsolete document can't remain a current work instruction",
        PD01: "FEFO (first-expiry-first-out) picking suggestion on delivery",
        PD02: "An expired batch cannot be shipped",
        PD03: "A recalled batch blocks delivery",
        PD04: "Customer credit limit is enforced before a sale",
        PD05: "A customer return restores stock to the correct original batch",
        PD06: "Trace which customers received a given batch",
        PD07: "Near-expiry batches raise an alert",
      },
      businessFlowSummary:
        "Demo Pharma Co. runs the full pharma chain: purchasing raw materials into Quarantine, QC-releasing them to Approved, manufacturing PARA-500-TAB tablets against a BOM, in-process QC, and QA batch release to a Released finished-goods warehouse. Golden Demo #2 extends the same company into wholesale distribution — a genuine second manufacturing batch (deliberately backdated expiry) gives FEFO picking a real choice, then sells to wholesale customer \"ABC Pharmacy Chain Co.\" with expiry blocking, recall blocking, credit-limit enforcement, returns, and batch-to-customer traceability all proven live.",
      notableBugsFixed: [
        "A missing shelf_life_in_days value blocked expiry tracking until set explicitly.",
        "BOM packaging quantities were wrongly set per-tablet instead of per-batch, leaving packaging consumption near zero until corrected.",
        "A partially-applied stock receipt (submitted but only some ledger entries posted) was resolved by cancelling the document rather than force-deleting it.",
      ],
    },
    vi: {
      testDescriptions: {
        P01: "Nguyên liệu đang trong khu Biệt trữ không thể được xuất thẳng vào sản xuất",
        P02: "Chỉ lô đã ở trạng thái Đã xuất xưởng mới được phép xuất dùng",
        P03: "Lệnh sản xuất phải sử dụng đúng phiên bản BOM đang có hiệu lực",
        P04: "Tiêu hao vượt dung sai cho phép sẽ phát cảnh báo hoặc cần phê duyệt",
        P05: "Kết quả kiểm tra chất lượng trong quá trình (in-process QC) vượt giới hạn sẽ tạo ra một sự kiện chất lượng thực sự",
        P06: "Thành phẩm chưa được QA xuất xưởng không thể chuyển vào kho Đã xuất xưởng",
        P07: "Phả hệ lô (batch genealogy) truy vết từ nguyên liệu đến thành phẩm",
        P08: "Báo cáo thu hồi truy vết từ thành phẩm đến các khách hàng đã nhận hàng",
        P09: "Người dùng sản xuất không thể tự phê duyệt xuất xưởng QA cho chính lô mình sản xuất",
        P10: "Tài liệu đã hết hiệu lực không thể tiếp tục là hướng dẫn công việc hiện hành",
        PD01: "Gợi ý lấy hàng theo nguyên tắc FEFO (hết hạn trước - xuất trước) khi giao hàng",
        PD02: "Lô đã hết hạn không thể được giao hàng",
        PD03: "Lô đang bị thu hồi sẽ chặn việc giao hàng",
        PD04: "Hạn mức công nợ của khách hàng được kiểm soát trước khi bán hàng",
        PD05: "Hàng khách trả được hoàn trả đúng vào lô gốc ban đầu",
        PD06: "Truy vết những khách hàng nào đã nhận một lô hàng cụ thể",
        PD07: "Lô sắp hết hạn sẽ phát cảnh báo",
      },
      businessFlowSummary:
        "Demo Pharma Co. vận hành toàn bộ chuỗi dược phẩm: mua nguyên liệu về khu Biệt trữ, kiểm tra chất lượng (QC) để chuyển sang trạng thái Đã duyệt, sản xuất viên nén PARA-500-TAB theo đúng BOM, kiểm tra chất lượng trong quá trình sản xuất (in-process QC), và xuất xưởng lô hàng qua QA vào kho thành phẩm Đã xuất xưởng. Golden Demo #2 mở rộng cùng công ty này sang khâu phân phối bán buôn — một lô sản xuất thứ hai thực sự (được cố tình lùi ngày hết hạn) tạo ra một lựa chọn thực tế cho việc lấy hàng theo FEFO, sau đó bán cho khách hàng bán buôn \"ABC Pharmacy Chain Co.\" với đầy đủ các cơ chế đã được kiểm chứng trực tiếp: chặn hàng hết hạn, chặn lô bị thu hồi, kiểm soát hạn mức công nợ, xử lý hàng trả lại, và truy vết lô hàng đến từng khách hàng.",
      notableBugsFixed: [
        "Trường shelf_life_in_days (số ngày hạn sử dụng) bị bỏ trống khiến việc theo dõi hạn dùng không hoạt động cho đến khi được thiết lập rõ ràng.",
        "Định mức bao bì trong BOM bị thiết lập nhầm theo từng viên thay vì theo cả lô, khiến lượng bao bì tiêu hao gần như bằng không cho đến khi được sửa lại.",
        "Một phiếu nhập kho bị áp dụng dở dang (đã xác nhận nhưng chỉ một phần bút toán sổ kho được ghi nhận) được xử lý bằng cách hủy chứng từ thay vì xóa cưỡng bức.",
      ],
    },
  },

  "IP-QMS": {
    goldenDemoLabel: "Golden Demo #3",
    testIds: ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08"],
    en: {
      testDescriptions: {
        Q01: "A Deviation can't reach Closed without a recorded root cause",
        Q02: "A CAPA's owner can't also be the person who closes it (segregation of duties)",
        Q03: "An overdue CAPA automatically escalates to Overdue status",
        Q04: "A CAPA can't close without an effectiveness check and evidence, on or after its due date",
        Q05: "Change Control impact flags drive its Draft → Under Review → Approved workflow",
        Q06: "An out-of-spec lab result automatically creates a linked CAPA and Deviation",
        Q07: "A Major audit finding links to a CAPA",
        Q08: "Every QMS record keeps a full, real audit trail",
      },
      businessFlowSummary:
        "A cold-storage temperature excursion is investigated as a Deviation, root-caused, and linked to a CAPA that can only close after a genuine effectiveness check performed by someone other than the CAPA's own owner. The same run also seeds a Change Control flagging an SOP for revision (picked up later by the DMS golden demo), an out-of-spec lab result, an audit finding, and a recall/risk/supplier-quality record, for full coverage of all 9 QMS modules.",
      notableBugsFixed: [
        "The CAPA-escalation step originally bypassed the platform's own audit trail, silently defeating the full-audit-trail test for that one event.",
        "Cross-module link fields used friendly labels instead of the literal DocType names the linking mechanism actually validates against, breaking every cross-module link until fixed.",
        "None of the 9 new QMS doctypes had change tracking enabled, so the audit-trail test initially showed zero history despite everything else working correctly.",
      ],
    },
    vi: {
      testDescriptions: {
        Q01: "Một Sai lệch (Deviation) không thể chuyển sang trạng thái Đã đóng nếu chưa ghi nhận nguyên nhân gốc rễ",
        Q02: "Người phụ trách CAPA không thể đồng thời là người đóng CAPA đó (nguyên tắc phân tách nhiệm vụ)",
        Q03: "CAPA quá hạn sẽ tự động chuyển sang trạng thái Quá hạn",
        Q04: "CAPA không thể đóng nếu chưa có đánh giá hiệu quả kèm bằng chứng, và phải thực hiện vào đúng hạn hoặc sau hạn",
        Q05: "Các cờ đánh giá tác động trong Kiểm soát thay đổi (Change Control) điều khiển luồng xử lý Dự thảo → Đang xem xét → Đã phê duyệt",
        Q06: "Kết quả xét nghiệm ngoài tiêu chuẩn (OOS) sẽ tự động tạo ra CAPA và Sai lệch liên kết",
        Q07: "Phát hiện đánh giá (audit) mức độ Nghiêm trọng được liên kết với một CAPA",
        Q08: "Mọi bản ghi trong hệ thống QMS đều lưu giữ đầy đủ nhật ký kiểm toán (audit trail) thực tế",
      },
      businessFlowSummary:
        "Một sự cố nhiệt độ vượt ngưỡng tại kho lạnh được điều tra dưới dạng Sai lệch (Deviation), xác định nguyên nhân gốc rễ, và liên kết với một CAPA — CAPA này chỉ có thể đóng sau khi có đánh giá hiệu quả thực sự, được thực hiện bởi người khác chứ không phải chính người phụ trách CAPA đó. Cùng kịch bản demo này còn khởi tạo một Kiểm soát thay đổi (Change Control) đánh dấu một SOP cần sửa đổi (được Golden Demo DMS tiếp nhận sau đó), một kết quả xét nghiệm ngoài tiêu chuẩn, một phát hiện đánh giá (audit finding), và một bản ghi thu hồi/rủi ro/chất lượng nhà cung cấp — đảm bảo bao phủ đầy đủ cả 9 phân hệ của QMS.",
      notableBugsFixed: [
        "Bước tự động chuyển trạng thái quá hạn của CAPA ban đầu bỏ qua cơ chế audit trail gốc của nền tảng, khiến bài kiểm thử về nhật ký kiểm toán đầy đủ bị vô hiệu một cách âm thầm đối với riêng sự kiện đó.",
        "Các trường liên kết giữa các phân hệ sử dụng nhãn hiển thị thân thiện thay vì đúng tên DocType mà cơ chế liên kết thực sự kiểm tra, khiến mọi liên kết liên phân hệ bị lỗi cho đến khi được sửa.",
        "Cả 9 DocType mới của QMS đều chưa bật tính năng theo dõi thay đổi, khiến bài kiểm thử audit trail ban đầu không hiển thị lịch sử nào dù mọi thứ khác đều hoạt động đúng.",
      ],
    },
  },

  "IP-DMS": {
    goldenDemoLabel: "Golden Demo #4",
    testIds: ["D01", "D02", "D03", "D04", "D05", "D06", "D07"],
    en: {
      testDescriptions: {
        D01: "An Effective or Obsolete document version's content is immutable",
        D02: "Only the Effective version shows as the current one",
        D03: "Going Effective auto-creates a training assignment for every relevant user",
        D04: "A superseded version automatically flips to Obsolete, archived rather than deleted",
        D05: "A controlled print event is logged",
        D06: "Revising a document keeps its full version history",
        D07: "Users who are assigned training but haven't completed it are flagged",
      },
      businessFlowSummary:
        "The exact SOP the QMS golden demo's Change Control flagged for revision goes through Draft → Under Review → Approved → Effective as Version 1, auto-assigning training to every demo user. A Version 2 revision (referencing the earlier audit finding) then supersedes it, flipping Version 1 to Obsolete while preserving its full history.",
      notableBugsFixed: [
        "One integrity check used an existence query with no real filter, so it always returned true regardless of the actual data — a bug pattern later swept and fixed platform-wide.",
      ],
    },
    vi: {
      testDescriptions: {
        D01: "Nội dung của một phiên bản tài liệu ở trạng thái Đang hiệu lực hoặc Đã hết hiệu lực không thể bị thay đổi",
        D02: "Chỉ phiên bản Đang hiệu lực mới được hiển thị là phiên bản hiện hành",
        D03: "Khi tài liệu chuyển sang hiệu lực, hệ thống tự động tạo phân công đào tạo cho tất cả người dùng liên quan",
        D04: "Phiên bản bị thay thế sẽ tự động chuyển sang trạng thái Đã hết hiệu lực, được lưu trữ chứ không bị xóa",
        D05: "Sự kiện in bản kiểm soát được ghi nhận lại",
        D06: "Việc sửa đổi tài liệu vẫn giữ nguyên toàn bộ lịch sử các phiên bản",
        D07: "Người dùng được phân công đào tạo nhưng chưa hoàn thành sẽ bị đánh dấu cảnh báo",
      },
      businessFlowSummary:
        "Chính SOP đã được Kiểm soát thay đổi trong Golden Demo QMS đánh dấu cần sửa đổi sẽ đi qua đầy đủ các bước Dự thảo → Đang xem xét → Đã phê duyệt → Đang hiệu lực với vai trò Phiên bản 1, đồng thời tự động phân công đào tạo cho toàn bộ người dùng demo. Sau đó, một bản sửa đổi Phiên bản 2 (tham chiếu đến phát hiện đánh giá trước đó) thay thế Phiên bản 1, chuyển phiên bản này sang trạng thái Đã hết hiệu lực trong khi vẫn giữ nguyên toàn bộ lịch sử.",
      notableBugsFixed: [
        "Một bài kiểm tra tính toàn vẹn dữ liệu sử dụng truy vấn kiểm tra sự tồn tại nhưng không có điều kiện lọc thực sự, nên luôn trả về đúng bất kể dữ liệu thực tế — một dạng lỗi sau này được rà soát và khắc phục trên toàn nền tảng.",
      ],
    },
  },

  "IP-LIMS": {
    goldenDemoLabel: "Golden Demo #5",
    testIds: ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08"],
    en: {
      testDescriptions: {
        L01: "A duplicate sample (same batch, type, and date) is blocked",
        L02: "Testing against a Draft (not yet approved) specification is blocked",
        L03: "An analyst can't review their own test result (segregation of duties)",
        L04: "Pass/fail is always recomputed server-side from spec limits, never trusted from manual entry",
        L05: "An out-of-spec result automatically creates a linked QMS out-of-spec record",
        L06: "A reviewed test result can't be silently edited afterward",
        L07: "A Certificate of Analysis can only be approved once its test is Approved",
        L08: "Testing on an instrument with overdue calibration is blocked",
      },
      businessFlowSummary:
        "The standalone LIMS runs a full sample lifecycle — receive, assign, test, record result, review, approve — for a Paracetamol tablet batch, then deliberately produces an out-of-spec assay result to prove it automatically raises a real linked quality record, finally issuing a Certificate of Analysis once the test is Approved.",
      notableBugsFixed: [
        "An automated quality-event hook updated the very document that triggered it from inside its own save event, causing a timestamp-conflict error and a real partial-write incident.",
        "A later, unrelated demo's reuse of the same shared analyst account broke this demo's own segregation-of-duties check by matching the wrong specification — fixed by scoping the check explicitly.",
      ],
    },
    vi: {
      testDescriptions: {
        L01: "Mẫu trùng lặp (cùng lô, cùng loại, cùng ngày) sẽ bị chặn",
        L02: "Việc xét nghiệm theo một tiêu chuẩn còn ở trạng thái Dự thảo (chưa được phê duyệt) sẽ bị chặn",
        L03: "Kiểm nghiệm viên không thể tự soát xét kết quả xét nghiệm do chính mình thực hiện (nguyên tắc phân tách nhiệm vụ)",
        L04: "Kết quả đạt/không đạt luôn được máy chủ tính toán lại dựa trên giới hạn tiêu chuẩn, không bao giờ tin vào giá trị nhập tay",
        L05: "Kết quả ngoài tiêu chuẩn sẽ tự động tạo ra một bản ghi OOS liên kết trong hệ thống QMS",
        L06: "Kết quả xét nghiệm đã được soát xét không thể bị chỉnh sửa âm thầm sau đó",
        L07: "Phiếu kiểm nghiệm (CoA) chỉ có thể được phê duyệt khi xét nghiệm tương ứng đã ở trạng thái Đã phê duyệt",
        L08: "Việc xét nghiệm trên thiết bị đã quá hạn hiệu chuẩn sẽ bị chặn",
      },
      businessFlowSummary:
        "Hệ thống LIMS độc lập vận hành trọn vẹn vòng đời của một mẫu — tiếp nhận, phân công, xét nghiệm, ghi nhận kết quả, soát xét, phê duyệt — cho một lô viên nén Paracetamol, sau đó cố tình tạo ra một kết quả định lượng ngoài tiêu chuẩn để chứng minh hệ thống tự động tạo ra một bản ghi chất lượng liên kết thực sự, và cuối cùng phát hành Phiếu kiểm nghiệm (CoA) khi xét nghiệm đã được phê duyệt.",
      notableBugsFixed: [
        "Một hook tự động tạo sự kiện chất lượng lại cập nhật ngược vào chính tài liệu đã kích hoạt nó ngay trong sự kiện lưu của tài liệu đó, gây ra lỗi xung đột dấu thời gian (timestamp) và một sự cố ghi dữ liệu dở dang thực sự.",
        "Một demo khác không liên quan, sử dụng lại cùng tài khoản kiểm nghiệm viên dùng chung, đã làm hỏng bài kiểm tra phân tách nhiệm vụ của chính demo này do khớp nhầm tiêu chuẩn — được khắc phục bằng cách giới hạn phạm vi kiểm tra một cách tường minh.",
      ],
    },
  },

  "IP-EAM": {
    goldenDemoLabel: "Golden Demo #6",
    testIds: ["E01", "E02", "E03", "E04", "E05", "E06", "E07"],
    en: {
      testDescriptions: {
        E01: "Preventive maintenance auto-schedules",
        E02: "Overdue calibration is visible and queryable",
        E03: "A breakdown creates a real repair work order",
        E04: "Spare-part consumption is recorded on the repair",
        E05: "A qualification (IQ/OQ/PQ) links to specific equipment",
        E06: "Equipment can't be qualified or used while its calibration is overdue",
        E07: "Full equipment service history is retained",
      },
      businessFlowSummary:
        "Built almost entirely on native ERP asset-management machinery plus two new records (Calibration Record, Qualification): a passing calibration lets an equipment qualification succeed; a real breakdown (a drive-belt failure) creates a repair consuming a spare part; a second qualification attempt against deliberately overdue calibration is correctly blocked.",
      notableBugsFixed: [
        "A \"latest calibration\" lookup ordered by the wrong date field, which could have let a block-worthy qualification through — caught before it ever ran live.",
      ],
    },
    vi: {
      testDescriptions: {
        E01: "Bảo trì phòng ngừa được tự động lên lịch",
        E02: "Thiết bị quá hạn hiệu chuẩn có thể được xem và tra cứu",
        E03: "Sự cố hỏng hóc sẽ tạo ra một lệnh sửa chữa thực sự",
        E04: "Vật tư phụ tùng tiêu hao được ghi nhận trên lệnh sửa chữa",
        E05: "Một hồ sơ thẩm định (IQ/OQ/PQ) được liên kết với thiết bị cụ thể",
        E06: "Thiết bị không thể được thẩm định hoặc sử dụng khi đang quá hạn hiệu chuẩn",
        E07: "Toàn bộ lịch sử bảo trì, sửa chữa thiết bị được lưu giữ đầy đủ",
      },
      businessFlowSummary:
        "Được xây dựng gần như hoàn toàn trên nền cơ chế quản lý tài sản sẵn có của ERP, cùng với hai loại bản ghi mới (Hồ sơ hiệu chuẩn, Hồ sơ thẩm định): một lần hiệu chuẩn đạt yêu cầu cho phép thẩm định thiết bị thành công; một sự cố hỏng hóc thực sự (đứt dây curoa) tạo ra một lệnh sửa chữa có tiêu hao phụ tùng; lần thẩm định thứ hai được thử với thiết bị cố tình để quá hạn hiệu chuẩn đã bị chặn đúng như thiết kế.",
      notableBugsFixed: [
        "Truy vấn tìm \"lần hiệu chuẩn gần nhất\" sắp xếp theo sai trường ngày tháng, có thể khiến một thẩm định đáng lẽ phải bị chặn lại được thông qua — lỗi này đã được phát hiện trước khi chạy trên hệ thống thực.",
      ],
    },
  },

  "IP-FEED": {
    goldenDemoLabel: "Golden Demo #7",
    companyName: "Demo Feed Mill Co.",
    testIds: ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
    en: {
      testDescriptions: {
        F01: "Formula (BOM) revision",
        F02: "Ingredient substitution requires a Pending → Approved workflow",
        F03: "Weighing tolerance (±3%) is enforced during manufacture",
        F04: "Batch genealogy is traceable",
        F05: "Yield is computed from actual manufacturing output",
        F06: "The QC release gate reuses the pharma golden demo's own hook unmodified",
        F07: "A cross-contamination sequencing flag blocks running an allergen-free feed right after an allergen feed",
        F08: "Silo stock can be queried",
      },
      businessFlowSummary:
        "Demo Feed Mill Co. produces an allergen-containing Pig Starter Feed and an allergen-free Pig Grower Feed through weighing, mixing, QC, and release. The demo proves a formula revision, an approved ingredient substitution, and that running the allergen-free feed right after the allergen feed on the same line is blocked unless a line-cleaning log resolves it.",
      notableBugsFixed: [
        "An item's allergen flag was left off by default, so the cross-contamination check initially had nothing to block.",
        "The same always-true existence-check bug from the QMS build recurred here, prompting a platform-wide grep sweep for the pattern.",
        "The pharma golden demo's own integrity check had a stale hardcoded assumption (a single batch size) that broke once a second batch existed — rewritten to derive expectations dynamically from ledger data.",
      ],
    },
    vi: {
      testDescriptions: {
        F01: "Sửa đổi công thức (BOM)",
        F02: "Thay thế nguyên liệu phải qua quy trình Chờ duyệt → Đã phê duyệt",
        F03: "Dung sai cân định lượng (±3%) được kiểm soát chặt trong quá trình sản xuất",
        F04: "Phả hệ lô sản xuất có thể truy vết được",
        F05: "Hiệu suất (yield) được tính toán từ sản lượng thực tế",
        F06: "Cổng kiểm soát xuất xưởng QC tái sử dụng nguyên vẹn cơ chế đã dùng trong Golden Demo dược phẩm, không cần chỉnh sửa",
        F07: "Cờ cảnh báo trình tự sản xuất ngăn chặn nhiễm chéo, không cho sản xuất thức ăn không chứa dị nguyên ngay sau lô thức ăn có chứa dị nguyên",
        F08: "Tồn kho tại silo có thể được tra cứu",
      },
      businessFlowSummary:
        "Demo Feed Mill Co. sản xuất thức ăn tập ăn cho heo con (có chứa dị nguyên) và thức ăn cho heo choai (không chứa dị nguyên) qua các bước cân định lượng, trộn, kiểm tra chất lượng (QC) và xuất xưởng. Demo này chứng minh việc sửa đổi công thức, việc thay thế nguyên liệu đã được phê duyệt, và việc chạy lô thức ăn không chứa dị nguyên ngay sau lô có chứa dị nguyên trên cùng một dây chuyền sẽ bị chặn trừ khi có nhật ký vệ sinh dây chuyền xác nhận.",
      notableBugsFixed: [
        "Cờ đánh dấu dị nguyên của mặt hàng mặc định không được bật, khiến bài kiểm tra nhiễm chéo ban đầu không có gì để chặn.",
        "Lỗi kiểm tra sự tồn tại luôn trả về đúng, từng gặp khi xây dựng QMS, lại tái diễn ở đây — dẫn đến việc rà soát toàn nền tảng để tìm và sửa triệt để dạng lỗi này.",
        "Bài kiểm tra tính toàn vẹn của chính Golden Demo dược phẩm có một giả định cứng đã lỗi thời (chỉ tính cho một cỡ lô duy nhất), gây lỗi khi có lô thứ hai xuất hiện — được viết lại để suy ra kỳ vọng một cách động từ dữ liệu sổ kho thực tế.",
      ],
    },
  },

  "IP-SHRIMP": {
    goldenDemoLabel: "Golden Demo #8",
    companyName: "Demo Shrimp Farm — Bac Lieu",
    testIds: ["SF01", "SF02", "SF03", "SF04", "SF05", "SF06", "SF07", "SF08", "SF09", "SF10"],
    en: {
      testDescriptions: {
        SF01: "A pond correctly flips from Empty to Stocked on stocking",
        SF02: "An already-stocked pond can't be double-stocked",
        SF03: "Daily feed log recorded",
        SF04: "Water-quality reading recorded",
        SF05: "Growth sample recorded",
        SF06: "Health treatment recorded",
        SF07: "Mortality recorded",
        SF08: "Harvest KPIs computed from the batch's own recorded history",
        SF09: "Cost per kilogram computed server-side",
        SF10: "A water reading below a safe threshold raises an alert",
      },
      businessFlowSummary:
        "A full shrimp crop cycle at Demo Shrimp Farm — Bac Lieu: an empty pond is stocked with 250,000 post-larvae, then feed, water quality, growth, health, and mortality are logged (including one deliberately below-threshold water reading) before harvest, with survival rate, feed-conversion ratio, and cost per kilogram computed from the batch's own recorded operational history.",
      notableBugsFixed: [
        "Early feed-log entries were sized unrealistically small, producing an impossible feed-conversion ratio, later rescaled to a realistic value with an added sanity check.",
        "A water-reading duplicate check used the current timestamp instead of the reading's own date, letting readings silently duplicate on every re-run.",
        "The stocking idempotency check only matched still-active batches, so re-running the seed after a crop finished tried to re-stock the same pond and hit its own block.",
      ],
    },
    vi: {
      testDescriptions: {
        SF01: "Ao chuyển đúng trạng thái từ Trống sang Đã thả giống khi thả nuôi",
        SF02: "Ao đã thả giống không thể bị thả giống lần thứ hai",
        SF03: "Nhật ký cho ăn hàng ngày được ghi nhận",
        SF04: "Chỉ số chất lượng nước được ghi nhận",
        SF05: "Mẫu kiểm tra tăng trưởng được ghi nhận",
        SF06: "Việc điều trị sức khỏe được ghi nhận",
        SF07: "Tỷ lệ hao hụt (chết) được ghi nhận",
        SF08: "Các chỉ số thu hoạch (KPI) được tính toán từ chính lịch sử ghi nhận của lô nuôi",
        SF09: "Giá thành trên mỗi kilogram được máy chủ tính toán",
        SF10: "Chỉ số nước dưới ngưỡng an toàn sẽ phát cảnh báo",
      },
      businessFlowSummary:
        "Trọn vẹn một vụ nuôi tôm tại Demo Shrimp Farm — Bạc Liêu: một ao trống được thả 250.000 con tôm giống (post-larvae), sau đó các dữ liệu cho ăn, chất lượng nước, tăng trưởng, sức khỏe và hao hụt được ghi nhận (bao gồm một lần cố tình ghi chỉ số nước dưới ngưỡng an toàn) trước khi thu hoạch, với tỷ lệ sống, hệ số chuyển đổi thức ăn (FCR) và giá thành trên mỗi kilogram được tính toán từ chính lịch sử vận hành đã ghi nhận của lô nuôi.",
      notableBugsFixed: [
        "Các bản ghi cho ăn ban đầu có khối lượng quá nhỏ một cách phi thực tế, tạo ra hệ số chuyển đổi thức ăn (FCR) không thể xảy ra trong thực tế — sau đó được hiệu chỉnh lại về giá trị hợp lý và bổ sung kiểm tra tính hợp lệ.",
        "Bài kiểm tra trùng lặp chỉ số nước sử dụng thời điểm hệ thống hiện tại thay vì ngày của chính bản ghi đo, khiến dữ liệu bị trùng lặp âm thầm mỗi khi chạy lại.",
        "Bài kiểm tra chống thả giống trùng lặp chỉ đối chiếu với các lô nuôi còn đang hoạt động, nên khi chạy lại dữ liệu mẫu sau khi vụ nuôi đã kết thúc, hệ thống cố thả giống lại cùng một ao và tự vướng vào chính cơ chế chặn của mình.",
      ],
    },
  },

  "IP-VETERINARY": {
    goldenDemoLabel: "Golden Demo #9 & #10",
    companyName: "Demo Vet Pharma Co.",
    testIds: [
      "VPM01", "VPM02", "VPM03", "VPM04", "VPM05", "VPM06", "VPM07",
      "VD01", "VD02", "VD03", "VD04", "VD05", "VD06", "VD07",
    ],
    unconfirmedTestIds: ["VPM05"],
    en: {
      testDescriptions: {
        VPM01: "Species/indication/withdrawal-period master data",
        VPM02: "Formula/BOM revision",
        VPM03: "Batch and expiry tracked through production",
        VPM04: "QC release gate, reusing the pharma golden demo's own hook unmodified",
        VPM05: "Traceability",
        VPM06: "Recall, reusing the QMS golden demo's recall mechanism directly",
        VPM07: "Label version, reusing the DMS golden demo's document lifecycle",
        VD01: "Territory ownership",
        VD02: "Dealer-tier pricing",
        VD03: "Batch and expiry tracked on delivery to a dealer",
        VD04: "Dealer credit limit enforcement",
        VD05: "Territory sales target",
        VD06: "Recall trace to a dealer",
        VD07: "A technical visit log linked to a specific dealer",
      },
      businessFlowSummary:
        "Demo Vet Pharma Co. manufactures an injectable oxytetracycline product, reusing the pharma golden demo's own manufacturing, QC, and QA-release machinery almost unmodified. Golden Demo #10 then distributes that same product to a regional dealer, \"VetCare Mekong Dealer Co.,\" proving territory ownership, dealer credit limits, batch-tracked delivery, a technical-visit log, and a full recall-to-dealer trace.",
      notableBugsFixed: [
        "An invalid unit-of-measure code for liters had to be corrected to the platform's real unit name.",
        "A BOM revision on a batch with an already-submitted work order couldn't be cancelled outright — fixed by flipping which version is the default, the correct pattern for revising legitimate history rather than fixing a mistake.",
        "A sales-territory distribution required its percentages to sum to exactly 100%, and required a new leaf-level customer group rather than reusing a group-level node.",
      ],
    },
    vi: {
      testDescriptions: {
        VPM01: "Dữ liệu chủ (master data) về loài vật nuôi, chỉ định điều trị và thời gian ngừng sử dụng thuốc",
        VPM02: "Sửa đổi công thức/BOM",
        VPM03: "Theo dõi lô và hạn sử dụng xuyên suốt quá trình sản xuất",
        VPM04: "Cổng kiểm soát xuất xưởng QC, tái sử dụng nguyên vẹn cơ chế từ Golden Demo dược phẩm",
        VPM05: "Khả năng truy vết",
        VPM06: "Thu hồi sản phẩm, tái sử dụng trực tiếp cơ chế thu hồi từ Golden Demo QMS",
        VPM07: "Phiên bản nhãn sản phẩm, tái sử dụng vòng đời tài liệu từ Golden Demo DMS",
        VD01: "Phân vùng quyền quản lý theo khu vực (territory)",
        VD02: "Bảng giá theo cấp bậc đại lý",
        VD03: "Theo dõi lô và hạn sử dụng khi giao hàng cho đại lý",
        VD04: "Kiểm soát hạn mức công nợ của đại lý",
        VD05: "Chỉ tiêu doanh số theo khu vực",
        VD06: "Truy vết thu hồi đến từng đại lý",
        VD07: "Nhật ký thăm khám kỹ thuật được liên kết với một đại lý cụ thể",
      },
      businessFlowSummary:
        "Demo Vet Pharma Co. sản xuất một sản phẩm thuốc tiêm oxytetracycline, tái sử dụng gần như nguyên vẹn toàn bộ cơ chế sản xuất, kiểm tra chất lượng (QC) và xuất xưởng QA đã có từ Golden Demo dược phẩm. Golden Demo #10 sau đó phân phối chính sản phẩm này đến một đại lý khu vực, \"VetCare Mekong Dealer Co.\", chứng minh việc phân vùng quyền quản lý theo khu vực, kiểm soát hạn mức công nợ đại lý, giao hàng có theo dõi lô, nhật ký thăm khám kỹ thuật, và khả năng truy vết thu hồi đầy đủ đến tận đại lý.",
      notableBugsFixed: [
        "Mã đơn vị tính cho lít không hợp lệ, phải được sửa lại đúng theo tên đơn vị thực tế của nền tảng.",
        "Việc sửa đổi BOM cho một lô đã có lệnh sản xuất được xác nhận không thể hủy trực tiếp — được khắc phục bằng cách chuyển đổi phiên bản mặc định, đúng theo cách xử lý chuẩn khi sửa đổi lịch sử hợp lệ thay vì sửa một sai sót.",
        "Việc phân bổ khu vực bán hàng yêu cầu tổng tỷ lệ phần trăm phải đúng bằng 100%, và cần tạo một nhóm khách hàng cấp thấp nhất (leaf-level) mới thay vì dùng lại một nút ở cấp nhóm.",
      ],
    },
  },

  "IP-LIVESTOCK-PIG": {
    goldenDemoLabel: "Golden Demo #11",
    testIds: ["PF01", "PF02", "PF03", "PF04", "PF05", "PF06", "PF07", "PF08"],
    en: {
      testDescriptions: {
        PF01: "Animal/batch tag uniqueness",
        PF02: "Breeding lifecycle: service → confirmed pregnant → farrowing → grower batch",
        PF03: "Feed consumption logged",
        PF04: "Vaccination due/administered/overdue, always recomputed server-side",
        PF05: "Medicine withdrawal period computed and enforced before sale",
        PF06: "Mortality recorded",
        PF07: "Cost allocation (feed, medicine, other) and profit computed server-side",
        PF08: "Trace to the real customer sale lot",
      },
      businessFlowSummary:
        "A sow and boar are bred through service, confirmed pregnancy, and farrowing, producing a grower batch in a pen; feed, vaccination (one deliberately overdue), medicine treatment with a computed withdrawal period, and mortality are logged; the batch is sold only after its withdrawal period has elapsed, with cost and profit computed from its own recorded history.",
      notableBugsFixed: [
        "A duplicate-tag negative test initially caught the wrong exception type, since the real duplicate-entry error is a different error class than expected — the fix was then reused by five later farm golden demos.",
      ],
    },
    vi: {
      testDescriptions: {
        PF01: "Tính duy nhất của mã thẻ tai vật nuôi/lô",
        PF02: "Vòng đời sinh sản: phối giống → xác nhận mang thai → đẻ → lô heo choai",
        PF03: "Tiêu thụ thức ăn được ghi nhận",
        PF04: "Lịch tiêm phòng đến hạn/đã tiêm/quá hạn luôn được máy chủ tính toán lại",
        PF05: "Thời gian ngừng sử dụng thuốc được tính toán và kiểm soát bắt buộc trước khi xuất bán",
        PF06: "Tỷ lệ hao hụt (chết) được ghi nhận",
        PF07: "Phân bổ chi phí (thức ăn, thuốc, chi phí khác) và lợi nhuận được máy chủ tính toán",
        PF08: "Truy vết đến đúng lô hàng bán cho khách hàng thực tế",
      },
      businessFlowSummary:
        "Một heo nái và heo đực giống được phối giống, qua các bước xác nhận mang thai và đẻ, tạo ra một lô heo choai trong chuồng nuôi; dữ liệu cho ăn, tiêm phòng (cố tình để một mũi quá hạn), điều trị thuốc với thời gian ngừng thuốc được tính toán, và hao hụt đều được ghi nhận; lô heo chỉ được phép xuất bán sau khi thời gian ngừng thuốc đã kết thúc, với chi phí và lợi nhuận được tính toán từ chính lịch sử ghi nhận của lô.",
      notableBugsFixed: [
        "Bài kiểm thử phủ định về mã thẻ trùng lặp ban đầu bắt sai loại ngoại lệ (exception), do lỗi trùng dữ liệu thực tế thuộc một nhóm lỗi khác với dự kiến — bản sửa lỗi này sau đó được tái sử dụng ở năm Golden Demo chăn nuôi tiếp theo.",
      ],
    },
  },

  "IP-LIVESTOCK-POULTRY": {
    goldenDemoLabel: "Golden Demo #12",
    testIds: ["PO01", "PO02", "PO03", "PO04", "PO05", "PO06", "PO07"],
    en: {
      testDescriptions: {
        PO01: "Flock lifecycle and unique flock code",
        PO02: "Daily mortality recorded",
        PO03: "Feed consumption logged",
        PO04: "Vaccine schedule, with one flock deliberately overdue",
        PO05: "Weight curve recorded",
        PO06: "Egg output tested as Layer-only, with a real negative test against a Broiler flock",
        PO07: "Sale/harvest with server-recomputed cost, profit, and livability",
      },
      businessFlowSummary:
        "One Broiler flock and one Layer flock are placed as day-old chicks into empty houses, tracked through feed, vaccination, weight, mortality, and (Layer-only) egg production, then both sold as poultry sale lots with cost, profit, and livability computed from recorded history.",
    },
    vi: {
      testDescriptions: {
        PO01: "Vòng đời của đàn gia cầm và mã đàn duy nhất",
        PO02: "Tỷ lệ hao hụt hàng ngày được ghi nhận",
        PO03: "Tiêu thụ thức ăn được ghi nhận",
        PO04: "Lịch tiêm vắc-xin, với một đàn cố tình để quá hạn",
        PO05: "Đường cong tăng trọng được ghi nhận",
        PO06: "Sản lượng trứng chỉ áp dụng cho đàn gà đẻ, có kiểm thử phủ định thực tế đối với đàn gà thịt",
        PO07: "Xuất bán/thu hoạch với chi phí, lợi nhuận và tỷ lệ nuôi sống được máy chủ tính toán lại",
      },
      businessFlowSummary:
        "Một đàn gà thịt (Broiler) và một đàn gà đẻ (Layer) được thả nuôi từ gà con một ngày tuổi vào chuồng trống, được theo dõi qua các dữ liệu cho ăn, tiêm phòng, cân nặng, hao hụt, và (chỉ với đàn gà đẻ) sản lượng trứng, sau đó cả hai đàn được xuất bán dưới dạng các lô gia cầm với chi phí, lợi nhuận và tỷ lệ nuôi sống được tính toán từ lịch sử ghi nhận.",
    },
  },

  "IP-LIVESTOCK-CATTLE": {
    goldenDemoLabel: "Golden Demo #13",
    testIds: ["CT01", "CT02", "CT03", "CT04", "CT05", "CT06", "CT07"],
    en: {
      testDescriptions: {
        CT01: "Pedigree: sire/dam linkage, sex-validated and unique",
        CT02: "Reproduction lifecycle: service → confirmed pregnant → calving",
        CT03: "Milk record, female-only",
        CT04: "Treatment (e.g. mastitis) recorded",
        CT05: "Feed ration logs",
        CT06: "Culling or sale as two distinct terminal outcomes",
        CT07: "Cost per animal or group, computed server-side",
      },
      businessFlowSummary:
        "An individually-tracked dairy herd (no pen/batch grouping, unlike the other farm demos) — a registered sire and dam are bred, producing a calf whose pedigree links back automatically; milking, mastitis treatment, and feed ration logs accrue against the dam; the calf is eventually sold to a dairy cooperative and the dam is culled to a meat trader, each with server-computed cost and profit.",
    },
    vi: {
      testDescriptions: {
        CT01: "Phả hệ: liên kết bố/mẹ, được kiểm tra giới tính hợp lệ và tính duy nhất",
        CT02: "Vòng đời sinh sản: phối giống → xác nhận mang thai → đẻ bê",
        CT03: "Ghi nhận sản lượng sữa, chỉ áp dụng cho bò cái",
        CT04: "Ghi nhận điều trị bệnh (ví dụ: viêm vú)",
        CT05: "Nhật ký khẩu phần ăn",
        CT06: "Loại thải hoặc xuất bán là hai kết quả cuối cùng riêng biệt",
        CT07: "Chi phí theo từng cá thể hoặc theo nhóm, được máy chủ tính toán",
      },
      businessFlowSummary:
        "Một đàn bò sữa được theo dõi theo từng cá thể riêng lẻ (không nhóm theo chuồng/lô như các demo chăn nuôi khác) — một cặp bố mẹ đã đăng ký được phối giống, sinh ra một bê con có phả hệ tự động liên kết ngược lại; dữ liệu vắt sữa, điều trị viêm vú và khẩu phần ăn được tích lũy trên bò mẹ; bê con cuối cùng được bán cho một hợp tác xã sữa, còn bò mẹ được loại thải bán cho thương lái thịt, mỗi trường hợp đều có chi phí và lợi nhuận do máy chủ tính toán.",
    },
  },

  "IP-HATCHERY": {
    goldenDemoLabel: "Golden Demo #14",
    testIds: ["H01", "H02", "H03", "H04", "H05", "H06"],
    en: {
      testDescriptions: {
        H01: "Egg batch traced to its parent stock",
        H02: "Incubator assignment follows an Empty → Occupied lifecycle guard",
        H03: "Hatch rate computed server-side from egg count",
        H04: "Chick grading total can't exceed the batch's initial count",
        H05: "Vaccination, with one deliberately overdue",
        H06: "Customer dispatch is traceable",
      },
      businessFlowSummary:
        "The deepest farm pipeline in the platform's demos — parent stock, egg batch, incubation, hatch result, chick batch, grading, vaccination, and dispatch — with one trace function walking the whole chain from parent stock through to the receiving customer.",
    },
    vi: {
      testDescriptions: {
        H01: "Lô trứng được truy vết về đàn bố mẹ",
        H02: "Việc phân công máy ấp tuân theo cơ chế kiểm soát vòng đời Trống → Đang sử dụng",
        H03: "Tỷ lệ nở được máy chủ tính toán từ số lượng trứng",
        H04: "Tổng số gà con sau phân loại không thể vượt quá số lượng ban đầu của lô",
        H05: "Tiêm phòng, với một trường hợp cố tình để quá hạn",
        H06: "Việc giao hàng cho khách có thể truy vết được",
      },
      businessFlowSummary:
        "Quy trình chăn nuôi có chiều sâu nhất trong toàn bộ các demo của nền tảng — đàn bố mẹ, lô trứng, ấp trứng, kết quả nở, lô gà con, phân loại, tiêm phòng và giao hàng — với một hàm truy vết duy nhất đi xuyên suốt toàn bộ chuỗi, từ đàn bố mẹ đến tận khách hàng nhận hàng.",
    },
  },

  "IP-AQUAFEED": {
    goldenDemoLabel: "Golden Demo #15",
    testIds: ["AF01", "AF02", "AF03", "AF04", "AF05", "AF06", "AF07"],
    en: {
      testDescriptions: {
        AF01: "Formula by species and life stage",
        AF02: "Pellet specification (size, buoyancy)",
        AF03: "Extrusion process recorded",
        AF04: "Batch QC",
        AF05: "Lot trace, reusing the compound feed golden demo's genealogy logic unmodified",
        AF06: "Finished-feed release gate, reusing the pharma golden demo's own hook",
        AF07: "Yield computed from actual output",
      },
      businessFlowSummary:
        "One of the most reuse-heavy golden demos in the platform — two shrimp feed products (a post-larvae stage and a grower stage, with different pellet specs) go through the same purchase, manufacture, extrusion-log, QC, and release pipeline every prior manufacturing golden demo already proved.",
    },
    vi: {
      testDescriptions: {
        AF01: "Công thức theo từng loài và từng giai đoạn phát triển",
        AF02: "Tiêu chuẩn viên thức ăn (kích thước, độ nổi)",
        AF03: "Quy trình ép đùn (extrusion) được ghi nhận",
        AF04: "Kiểm tra chất lượng (QC) theo lô",
        AF05: "Truy vết theo lô, tái sử dụng nguyên vẹn logic phả hệ từ Golden Demo thức ăn chăn nuôi hỗn hợp",
        AF06: "Cổng xuất xưởng thức ăn thành phẩm, tái sử dụng cơ chế từ Golden Demo dược phẩm",
        AF07: "Hiệu suất được tính toán từ sản lượng thực tế",
      },
      businessFlowSummary:
        "Một trong những Golden Demo tái sử dụng nhiều nhất trong toàn nền tảng — hai sản phẩm thức ăn cho tôm (giai đoạn hậu ấu trùng và giai đoạn tăng trưởng, với tiêu chuẩn viên thức ăn khác nhau) đi qua cùng một quy trình mua hàng, sản xuất, ghi nhận ép đùn, kiểm tra chất lượng và xuất xưởng mà mọi Golden Demo sản xuất trước đó đã chứng minh.",
    },
  },

  "IP-AQUA-ENVIRONMENT": {
    goldenDemoLabel: "Golden Demo #16",
    testIds: ["AE01", "AE02", "AE03", "AE04", "AE05", "AE06"],
    en: {
      testDescriptions: {
        AE01: "Formula revision",
        AE02: "Batch/lot tracking",
        AE03: "QC",
        AE04: "Label version, reusing the DMS document lifecycle",
        AE05: "Release gate, reusing the pharma golden demo's own hook",
        AE06: "Distribution trace, reusing the pharma distribution golden demo's own trace function unmodified",
      },
      businessFlowSummary:
        "The leanest golden demo in the platform (zero new record types) — a pond-water probiotic (Bacillus subtilis) is purchased, manufactured, QC'd, released, revised to a new formula version, given a labeled document version, and distributed to a new dealer, entirely through machinery already proven by 15 prior golden demos.",
    },
    vi: {
      testDescriptions: {
        AE01: "Sửa đổi công thức",
        AE02: "Theo dõi lô sản xuất",
        AE03: "Kiểm tra chất lượng (QC)",
        AE04: "Phiên bản nhãn sản phẩm, tái sử dụng vòng đời tài liệu từ DMS",
        AE05: "Cổng xuất xưởng, tái sử dụng cơ chế từ Golden Demo dược phẩm",
        AE06: "Truy vết phân phối, tái sử dụng nguyên vẹn hàm truy vết từ Golden Demo phân phối dược phẩm",
      },
      businessFlowSummary:
        "Golden Demo gọn nhẹ nhất trên toàn nền tảng (không có loại bản ghi mới nào) — một chế phẩm vi sinh xử lý nước ao (Bacillus subtilis) được mua vào, sản xuất, kiểm tra chất lượng, xuất xưởng, sửa đổi sang phiên bản công thức mới, gắn phiên bản tài liệu nhãn, và phân phối đến một đại lý mới — tất cả đều thông qua cơ chế đã được 15 Golden Demo trước đó chứng minh.",
    },
  },

  "IP-FISH": {
    goldenDemoLabel: "Golden Demo #17",
    testIds: ["FF01", "FF02", "FF03", "FF04", "FF05", "FF06", "FF07"],
    en: {
      testDescriptions: {
        FF01: "Pond stocking flips it from Empty to Stocked",
        FF02: "Biomass estimate, computed server-side as part of growth sampling",
        FF03: "Feed logged",
        FF04: "Growth sample recorded",
        FF05: "Mortality recorded",
        FF06: "Harvest KPIs: survival rate, feed-conversion ratio, cost per kilogram",
        FF07: "Traceability from farm through pond, species, and harvest",
      },
      businessFlowSummary:
        "A Pangasius (Cá Tra) pond in An Giang province is stocked, tracked through feed, growth sampling, and mortality, before a harvest computes realistic survival-rate, feed-conversion, and cost KPIs from the batch's own recorded history.",
      notableBugsFixed: [
        "A biomass-estimate calculation summed all mortality with no date filter, and growth samples were seeded out of chronological order, producing two identical (wrong) population estimates — fixed by filtering by date and reordering the seed sequence.",
      ],
    },
    vi: {
      testDescriptions: {
        FF01: "Việc thả giống chuyển trạng thái ao từ Trống sang Đã thả giống",
        FF02: "Ước tính sinh khối, được máy chủ tính toán như một phần của việc lấy mẫu tăng trưởng",
        FF03: "Dữ liệu cho ăn được ghi nhận",
        FF04: "Mẫu kiểm tra tăng trưởng được ghi nhận",
        FF05: "Tỷ lệ hao hụt được ghi nhận",
        FF06: "Các chỉ số thu hoạch (KPI): tỷ lệ sống, hệ số chuyển đổi thức ăn (FCR), giá thành trên mỗi kilogram",
        FF07: "Khả năng truy vết từ trang trại, qua ao nuôi, loài nuôi, đến tận khi thu hoạch",
      },
      businessFlowSummary:
        "Một ao nuôi cá Tra (Pangasius) tại tỉnh An Giang được thả giống, theo dõi qua các dữ liệu cho ăn, lấy mẫu tăng trưởng và hao hụt, trước khi thu hoạch với các chỉ số tỷ lệ sống, hệ số chuyển đổi thức ăn và giá thành được tính toán một cách thực tế từ chính lịch sử ghi nhận của lô nuôi.",
      notableBugsFixed: [
        "Phép tính ước tính sinh khối cộng dồn toàn bộ số lượng hao hụt mà không lọc theo ngày, đồng thời dữ liệu mẫu tăng trưởng được nạp không đúng trình tự thời gian, dẫn đến hai kết quả ước tính số lượng đàn giống hệt nhau (và đều sai) — đã được khắc phục bằng cách lọc theo ngày và sắp xếp lại đúng trình tự dữ liệu mẫu.",
      ],
    },
  },

  "IP-AQUA-HATCHERY": {
    goldenDemoLabel: "Golden Demo #18",
    testIds: ["AH01", "AH02", "AH03", "AH04", "AH05", "AH06"],
    en: {
      testDescriptions: {
        AH01: "Broodstock trace and duplicate-tag uniqueness",
        AH02: "Spawning batch, sex-validated parents",
        AH03: "Larval survival rate computed server-side from egg count",
        AH04: "Nursery batch creation, grading total constrained to the initial count",
        AH05: "Health record",
        AH06: "Seed batch dispatch to a real customer",
      },
      businessFlowSummary:
        "A whiteleg-shrimp broodstock hatchery in Ninh Thuan province: broodstock → spawning → larval batch → nursery → graded seed batch (Grade A, Grade B, and reject) → dispatch to a new dealer customer group.",
    },
    vi: {
      testDescriptions: {
        AH01: "Truy vết đàn bố mẹ và tính duy nhất của mã thẻ, tránh trùng lặp",
        AH02: "Lô sinh sản, với bố mẹ được kiểm tra giới tính hợp lệ",
        AH03: "Tỷ lệ sống của ấu trùng được máy chủ tính toán từ số lượng trứng",
        AH04: "Tạo lô ương giống, với tổng số lượng sau phân loại bị giới hạn không vượt quá số lượng ban đầu",
        AH05: "Bản ghi sức khỏe",
        AH06: "Giao lô con giống cho khách hàng thực tế",
      },
      businessFlowSummary:
        "Một trại giống tôm thẻ chân trắng (whiteleg shrimp) tại tỉnh Ninh Thuận: đàn bố mẹ → sinh sản → lô ấu trùng → ương giống → lô con giống đã phân loại (Loại A, Loại B, và loại bỏ) → giao hàng cho một nhóm khách hàng đại lý mới.",
    },
  },

  "IP-SEAFOOD-PROCESSING": {
    goldenDemoLabel: "Golden Demo #19",
    testIds: ["SP01", "SP02", "SP03", "SP04", "SP05", "SP06", "SP07", "SP08"],
    en: {
      testDescriptions: {
        SP01: "Harvest lot receiving, sourced from a real upstream shrimp harvest record",
        SP02: "Grade/yield computed server-side, blocked from exceeding received weight",
        SP03: "Processing batch (e.g. peeled)",
        SP04: "Packing lot",
        SP05: "Cold storage record",
        SP06: "Shipment closes the packing/cold-storage lifecycle",
        SP07: "One consolidated trace from carton back through batch, harvest, and pond",
        SP08: "Recall simulation, reusing the QMS golden demo's recall record as-is",
      },
      businessFlowSummary:
        "Plugs directly into the shrimp farm golden demo's real harvest record (not synthetic data) — receiving, grading, processing, packing into cartons, cold storage, and shipment to a Japanese export customer, with a full farm-to-carton trace resolving all the way back to the originating pond.",
    },
    vi: {
      testDescriptions: {
        SP01: "Tiếp nhận lô nguyên liệu thu hoạch, lấy nguồn từ một bản ghi thu hoạch tôm thực tế ở khâu thượng nguồn",
        SP02: "Phân loại/hiệu suất được máy chủ tính toán, không cho phép vượt quá khối lượng đã tiếp nhận",
        SP03: "Lô chế biến (ví dụ: bóc vỏ)",
        SP04: "Lô đóng gói",
        SP05: "Bản ghi lưu kho lạnh",
        SP06: "Xuất hàng khép kín vòng đời đóng gói/lưu kho lạnh",
        SP07: "Một truy vết tổng hợp duy nhất từ thùng carton ngược về lô, đợt thu hoạch, và tận ao nuôi",
        SP08: "Mô phỏng thu hồi sản phẩm, tái sử dụng nguyên trạng bản ghi thu hồi từ Golden Demo QMS",
      },
      businessFlowSummary:
        "Kết nối trực tiếp với bản ghi thu hoạch thực tế từ Golden Demo trại tôm (không phải dữ liệu giả lập) — tiếp nhận, phân loại, chế biến, đóng gói vào thùng carton, lưu kho lạnh, và xuất hàng cho một khách hàng xuất khẩu Nhật Bản, với khả năng truy vết đầy đủ từ trang trại đến tận thùng carton, ngược về đúng ao nuôi ban đầu.",
    },
  },

  "IP-SUPPLEMENT": {
    goldenDemoLabel: "Golden Demo #20",
    testIds: ["S01", "S02", "S03", "S04", "S05", "S06"],
    en: {
      testDescriptions: {
        S01: "A formula revision doesn't retroactively change an already-manufactured batch",
        S02: "Allergen/critical-ingredient flag on a formula component",
        S03: "Artwork version, reusing the DMS document lifecycle",
        S04: "Batch expiry computed by a shelf-life rule",
        S05: "Certificate of Analysis generated from an Approved LIMS result, full chain",
        S06: "Traceability from ingredient through lots to customers",
      },
      businessFlowSummary:
        "Produces a Vitamin C effervescent tablet (a formula that genuinely contains the allergen soy lecithin) through purchase, manufacture, QC, and release; revises the formula without altering the already-manufactured batch; versions its artwork document; runs the batch through the full LIMS chain to produce a Certificate of Analysis; and distributes it with full traceability.",
      notableBugsFixed: [
        "Reusing a shared LIMS analyst account across demos broke an earlier golden demo's own review-segregation check by non-deterministically matching this demo's own result instead — fixed by scoping the check to a specific specification.",
      ],
    },
    vi: {
      testDescriptions: {
        S01: "Việc sửa đổi công thức không làm thay đổi hồi tố đối với lô đã sản xuất trước đó",
        S02: "Cờ đánh dấu dị nguyên/nguyên liệu trọng yếu trên một thành phần của công thức",
        S03: "Phiên bản thiết kế bao bì (artwork), tái sử dụng vòng đời tài liệu từ DMS",
        S04: "Hạn sử dụng của lô được tính toán theo quy tắc hạn dùng",
        S05: "Phiếu kiểm nghiệm (CoA) được tạo từ kết quả LIMS đã phê duyệt, theo đúng toàn bộ chuỗi quy trình",
        S06: "Khả năng truy vết từ nguyên liệu, qua các lô, đến tận khách hàng",
      },
      businessFlowSummary:
        "Sản xuất viên sủi Vitamin C (với công thức thực sự có chứa dị nguyên lecithin đậu nành) qua các bước mua hàng, sản xuất, kiểm tra chất lượng và xuất xưởng; sửa đổi công thức mà không làm thay đổi lô đã sản xuất trước đó; quản lý phiên bản tài liệu thiết kế bao bì; đưa lô hàng qua toàn bộ chuỗi LIMS để tạo ra Phiếu kiểm nghiệm (CoA); và phân phối sản phẩm với khả năng truy vết đầy đủ.",
      notableBugsFixed: [
        "Việc dùng chung tài khoản kiểm nghiệm viên LIMS giữa các demo đã làm hỏng bài kiểm tra phân tách soát xét của một Golden Demo trước đó, do khớp không xác định (non-deterministic) với kết quả của chính demo này — được khắc phục bằng cách giới hạn bài kiểm tra theo đúng một tiêu chuẩn cụ thể.",
      ],
    },
  },

  "IP-COSMETICS": {
    goldenDemoLabel: "Golden Demo #21",
    companyName: "Demo Cosmetics Co.",
    testIds: ["C01", "C02", "C03", "C04", "C05", "C06"],
    en: {
      testDescriptions: {
        C01: "Formula revision",
        C02: "Bulk-batch and packed-batch genealogy across a two-stage manufacturing process",
        C03: "Packaging/artwork version",
        C04: "Stability sample schedule across multiple conditions and time points",
        C05: "A complaint traces back to the specific batch and customer",
        C06: "Rework doesn't lose genealogy",
      },
      businessFlowSummary:
        "Demo Cosmetics Co.'s first genuine two-stage manufacturing flow: a Bulk batch is QC-released, then consumed as an ingredient by a Packed batch, itself QC-released — the finished-goods release gate fires twice with no changes to the underlying mechanism. A stability schedule, a customer complaint tied to a real delivered batch, and a rework (reprocessing remaining Bulk stock) all prove genealogy survives real stock movements.",
      notableBugsFixed: [
        "A manufacturing work order defaulted to multi-level explosion, silently exploding the Bulk ingredient into its own raw materials instead of consuming it as a single item.",
        "A rework step tried to consume the full original batch quantity, but most was already used by packed production — fixed to compute the actual remaining quantity dynamically.",
        "Batch-lookup logic picked the wrong batch once a second batch of the same item existed — fixed to identify the batch by which work order actually produced it.",
      ],
    },
    vi: {
      testDescriptions: {
        C01: "Sửa đổi công thức",
        C02: "Phả hệ lô bán thành phẩm (bulk) và lô thành phẩm đóng gói xuyên suốt quy trình sản xuất hai giai đoạn",
        C03: "Phiên bản bao bì/thiết kế (artwork)",
        C04: "Lịch lấy mẫu thử độ ổn định theo nhiều điều kiện và mốc thời gian khác nhau",
        C05: "Khiếu nại được truy vết ngược về đúng lô và khách hàng cụ thể",
        C06: "Tái chế (rework) không làm mất phả hệ lô",
      },
      businessFlowSummary:
        "Quy trình sản xuất hai giai đoạn thực sự đầu tiên của Demo Cosmetics Co.: một lô bán thành phẩm (Bulk) được kiểm tra chất lượng và xuất xưởng, sau đó được tiêu thụ như một nguyên liệu đầu vào cho lô thành phẩm đóng gói (Packed) — bản thân lô này cũng được kiểm tra chất lượng và xuất xưởng — cổng xuất xưởng thành phẩm được kích hoạt hai lần mà không cần thay đổi gì trong cơ chế nền. Một lịch thử độ ổn định, một khiếu nại khách hàng gắn với một lô hàng đã giao thực tế, và một lần tái chế (xử lý lại phần tồn kho Bulk còn lại) đều chứng minh phả hệ lô vẫn được giữ nguyên qua các lần dịch chuyển tồn kho thực tế.",
      notableBugsFixed: [
        "Lệnh sản xuất mặc định bung định mức nhiều cấp (multi-level explosion), khiến nguyên liệu Bulk bị bung ngược thành các nguyên liệu thô cấu thành của chính nó một cách âm thầm, thay vì được tiêu thụ như một mặt hàng đơn lẻ.",
        "Bước tái chế cố gắng tiêu thụ toàn bộ số lượng ban đầu của lô, trong khi phần lớn đã được dùng cho sản xuất đóng gói — được khắc phục bằng cách tính toán động số lượng thực tế còn lại.",
        "Logic tìm kiếm lô đã chọn nhầm lô khi có lô thứ hai của cùng mặt hàng xuất hiện — được khắc phục bằng cách xác định lô dựa theo chính lệnh sản xuất đã tạo ra nó.",
      ],
    },
  },

  "IP-MEDICAL-DEVICE": {
    goldenDemoLabel: "Golden Demo #22",
    companyName: "Demo MedDevice Co.",
    testIds: ["MD01", "MD02", "MD03", "MD04", "MD05", "MD06", "MD07"],
    en: {
      testDescriptions: {
        MD01: "Serial number uniqueness",
        MD02: "Only an Approved design-change record's BOM can become the default",
        MD03: "A critical supplier must be Approved before a purchase order is allowed",
        MD04: "A failed incoming inspection blocks moving material into work-in-progress",
        MD05: "A finished serial number traces back to its consumed components",
        MD06: "A complaint links to a specific serial number or lot",
        MD07: "Overdue equipment calibration blocks a configured work-order operation",
      },
      businessFlowSummary:
        "Dual-tracks a finished device by both batch AND serial number. A critical supplier must be Approved before purchasing; a BOM revision needs an Approved design-change record; components pass incoming inspection (one batch deliberately rejected) before reaching work-in-progress; assembly is blocked against equipment with overdue calibration; the finished serialized device traces back to its components and to a customer complaint.",
      notableBugsFixed: [
        "A material transfer into work-in-progress moved only one of four required components, causing an opaque valuation error during assembly.",
        "Asset-category setup initially omitted a required accounts table, a gap first found back in the pharma golden demo's own EAM step.",
      ],
    },
    vi: {
      testDescriptions: {
        MD01: "Tính duy nhất của số seri (serial number)",
        MD02: "Chỉ BOM thuộc bản ghi thay đổi thiết kế đã được phê duyệt mới có thể trở thành mặc định",
        MD03: "Nhà cung cấp trọng yếu phải được phê duyệt trước khi được phép lập đơn mua hàng",
        MD04: "Kiểm tra đầu vào không đạt sẽ chặn việc chuyển nguyên vật liệu vào sản xuất dở dang",
        MD05: "Số seri thành phẩm được truy vết ngược về các linh kiện đã tiêu thụ để tạo ra nó",
        MD06: "Khiếu nại được liên kết với một số seri hoặc một lô cụ thể",
        MD07: "Thiết bị quá hạn hiệu chuẩn sẽ chặn công đoạn tương ứng đã được cấu hình trong lệnh sản xuất",
      },
      businessFlowSummary:
        "Theo dõi song song thiết bị thành phẩm bằng cả lô VÀ số seri. Nhà cung cấp trọng yếu phải được phê duyệt trước khi mua hàng; việc sửa đổi BOM cần có bản ghi thay đổi thiết kế đã được phê duyệt; linh kiện phải qua kiểm tra đầu vào (với một lô cố tình bị từ chối) trước khi được chuyển vào sản xuất dở dang; công đoạn lắp ráp bị chặn nếu dùng thiết bị đã quá hạn hiệu chuẩn; thiết bị thành phẩm có số seri được truy vết ngược về các linh kiện cấu thành và về khiếu nại của khách hàng.",
      notableBugsFixed: [
        "Việc chuyển vật tư vào sản xuất dở dang chỉ chuyển một trong bốn linh kiện cần thiết, gây ra lỗi định giá khó hiểu trong quá trình lắp ráp.",
        "Cấu hình nhóm tài sản ban đầu thiếu một bảng tài khoản kế toán bắt buộc — lỗ hổng này lần đầu được phát hiện từ chính bước EAM trong Golden Demo dược phẩm.",
      ],
    },
  },

  "IP-PHARMACY": {
    goldenDemoLabel: "Golden Demo #23",
    testIds: ["RX01", "RX02", "RX03", "RX04", "RX05", "RX06", "RX07"],
    en: {
      testDescriptions: {
        RX01: "A store sees only its own stock",
        RX02: "Head-office replenishment to a store",
        RX03: "An expired product is blocked at the point of sale",
        RX04: "Inter-store batch transfer",
        RX05: "Point-of-sale return, correctly reversing payment records",
        RX06: "Promotion pricing applies automatically",
        RX07: "A central dashboard aggregates stock and sales across stores",
      },
      businessFlowSummary:
        "A multi-branch pharmacy chain: head office purchases centrally, replenishes Store A, transfers stock from Store A to Store B, sells and returns through point-of-sale, applies a promotion, and blocks an expired-batch sale at the register — rolled into a central stock/sales dashboard.",
      notableBugsFixed: [
        "A site-level point-of-sale configuration setting blocked any non-return sale outright until corrected.",
        "A point-of-sale return correctly reversed line items but not its own payment record, a mismatch caught immediately on save.",
        "An idempotency guard checked live stock balance instead of whether the transaction already existed, silently re-triggering replenishment on every re-run.",
      ],
    },
    vi: {
      testDescriptions: {
        RX01: "Mỗi cửa hàng chỉ nhìn thấy tồn kho của chính mình",
        RX02: "Trụ sở chính bổ sung hàng cho cửa hàng",
        RX03: "Sản phẩm hết hạn bị chặn ngay tại quầy bán hàng",
        RX04: "Chuyển lô hàng giữa các cửa hàng",
        RX05: "Trả hàng tại quầy bán hàng, hoàn tác đúng các bản ghi thanh toán",
        RX06: "Giá khuyến mãi được áp dụng tự động",
        RX07: "Bảng điều khiển trung tâm tổng hợp tồn kho và doanh số của toàn bộ chuỗi cửa hàng",
      },
      businessFlowSummary:
        "Một chuỗi nhà thuốc đa chi nhánh: trụ sở chính mua hàng tập trung, bổ sung hàng cho Cửa hàng A, chuyển hàng từ Cửa hàng A sang Cửa hàng B, bán hàng và xử lý trả hàng tại quầy, áp dụng khuyến mãi, và chặn việc bán một lô hàng đã hết hạn ngay tại quầy thu ngân — toàn bộ được tổng hợp trên một bảng điều khiển tồn kho/doanh số tập trung.",
      notableBugsFixed: [
        "Một cấu hình quầy bán hàng ở cấp cơ sở đã chặn hoàn toàn mọi giao dịch bán hàng thông thường (không phải trả hàng) cho đến khi được sửa lại.",
        "Việc trả hàng tại quầy hoàn tác đúng các dòng chi tiết hàng hóa nhưng không hoàn tác bản ghi thanh toán tương ứng — sự lệch pha này được phát hiện ngay khi lưu chứng từ.",
        "Cơ chế chống chạy trùng lặp kiểm tra số dư tồn kho thực tế thay vì kiểm tra giao dịch đã tồn tại hay chưa, khiến việc bổ sung hàng bị kích hoạt lại âm thầm mỗi lần chạy lại.",
      ],
    },
  },

  "IP-3PL-COLDCHAIN": {
    goldenDemoLabel: "Golden Demo #24",
    testIds: ["W01", "W02", "W03", "W04", "W05", "W06"],
    en: {
      testDescriptions: {
        W01: "One client cannot see another client's stock",
        W02: "A temperature excursion automatically creates an event",
        W03: "FEFO outbound picking",
        W04: "Quarantined stock is blocked from shipping until QC-released",
        W05: "Inventory reconciliation corrects a count discrepancy",
        W06: "Billing aggregates real service usage per client",
      },
      businessFlowSummary:
        "A cold-chain 3PL warehouse operator holds segregated stock for two clients, each with its own quarantine/released pair and temperature band: portal users see only their own client's stock, temperature excursions are flagged automatically, outbound follows FEFO, quarantined stock can't ship until released, a stock reconciliation corrects a count discrepancy, and billing is aggregated per client from real ledger and delivery data.",
      notableBugsFixed: [
        "Auto-generated batch expiry dates didn't read the actual expiry entered at receiving, silently defeating the FEFO test until fixed.",
        "A stock reconciliation scoped to one batch initially set that batch's absolute quantity rather than adjusting the warehouse total correctly.",
        "The first sales invoice on this pack required a company accounting setting no prior golden demo had ever needed.",
      ],
    },
    vi: {
      testDescriptions: {
        W01: "Khách hàng này không thể nhìn thấy tồn kho của khách hàng khác",
        W02: "Sự cố vượt ngưỡng nhiệt độ sẽ tự động tạo ra một sự kiện",
        W03: "Lấy hàng xuất kho theo nguyên tắc FEFO",
        W04: "Hàng đang biệt trữ bị chặn xuất kho cho đến khi được QC xuất xưởng",
        W05: "Đối chiếu tồn kho giúp điều chỉnh sai lệch số lượng kiểm kê",
        W06: "Hóa đơn dịch vụ được tổng hợp từ dữ liệu sử dụng dịch vụ thực tế theo từng khách hàng",
      },
      businessFlowSummary:
        "Một đơn vị vận hành kho lạnh logistics bên thứ ba (3PL) lưu trữ tồn kho tách biệt cho hai khách hàng, mỗi khách hàng có cặp trạng thái biệt trữ/đã xuất xưởng và dải nhiệt độ riêng: người dùng cổng thông tin chỉ nhìn thấy tồn kho của chính khách hàng mình, sự cố vượt ngưỡng nhiệt độ được tự động gắn cờ cảnh báo, xuất kho tuân theo nguyên tắc FEFO, hàng đang biệt trữ không thể xuất cho đến khi được xuất xưởng, việc đối chiếu tồn kho giúp điều chỉnh sai lệch kiểm kê, và hóa đơn dịch vụ được tổng hợp theo từng khách hàng từ dữ liệu sổ kho và giao hàng thực tế.",
      notableBugsFixed: [
        "Hạn sử dụng của lô được tạo tự động không đọc đúng hạn sử dụng thực tế đã nhập khi nhận hàng, khiến bài kiểm tra FEFO bị vô hiệu một cách âm thầm cho đến khi được sửa.",
        "Việc đối chiếu tồn kho giới hạn theo một lô ban đầu thiết lập số lượng tuyệt đối của lô đó thay vì điều chỉnh đúng tổng tồn kho của cả kho.",
        "Hóa đơn bán hàng đầu tiên trong gói ngành này đòi hỏi một cấu hình kế toán công ty mà chưa Golden Demo nào trước đó từng cần đến.",
      ],
    },
  },

  "IP-CONSUMER-DIST": {
    goldenDemoLabel: "Golden Demo #25",
    companyName: "Demo Consumer Distribution Co.",
    testIds: ["CD01", "CD02", "CD03", "CD04", "CD05", "CD06"],
    en: {
      testDescriptions: {
        CD01: "Dealer-specific price list",
        CD02: "Promotion validity window, tested on both edges",
        CD03: "Sales correctly attributed to a sales territory",
        CD04: "Dealer credit limit enforcement",
        CD05: "A return automatically carries forward the original batch",
        CD06: "Commission report aggregated from real sales data",
      },
      businessFlowSummary:
        "Distributes finished goods from two upstream golden demos (the Vitamin C effervescent tablet and the facial cleanser) through a two-territory dealer network — dealer-tier pricing, a time-boxed promotion, territory-attributed sales, dealer credit limits, a partial return, and a commission report all resolve from the platform's native schema with essentially no custom code.",
      notableBugsFixed: [
        "Two prior golden demos' own integrity checks did unscoped batch lookups that had worked until this demo created a second batch of the same shared item — fixed with a proper batch-to-ledger join.",
        "A sales-flow lookup wasn't scoped to exclude returns, so once a return existed it created a bogus second invoice from the return itself, corrupting commission totals.",
      ],
    },
    vi: {
      testDescriptions: {
        CD01: "Bảng giá riêng theo từng đại lý",
        CD02: "Thời hạn hiệu lực khuyến mãi, được kiểm thử ở cả hai mốc biên",
        CD03: "Doanh số được ghi nhận đúng theo khu vực bán hàng",
        CD04: "Kiểm soát hạn mức công nợ của đại lý",
        CD05: "Hàng trả lại tự động được gắn về đúng lô gốc ban đầu",
        CD06: "Báo cáo hoa hồng được tổng hợp từ dữ liệu bán hàng thực tế",
      },
      businessFlowSummary:
        "Phân phối thành phẩm từ hai Golden Demo ở khâu thượng nguồn (viên sủi Vitamin C và sữa rửa mặt) qua một mạng lưới đại lý gồm hai khu vực — bảng giá theo cấp bậc đại lý, một chương trình khuyến mãi có thời hạn, doanh số được ghi nhận theo khu vực, kiểm soát hạn mức công nợ đại lý, một trường hợp trả hàng một phần, và báo cáo hoa hồng — tất cả đều được xử lý từ đúng cấu trúc dữ liệu gốc của nền tảng mà gần như không cần viết thêm mã tùy chỉnh.",
      notableBugsFixed: [
        "Các bài kiểm tra tính toàn vẹn của hai Golden Demo trước đó thực hiện tra cứu lô mà không giới hạn phạm vi, vốn vẫn hoạt động bình thường cho đến khi demo này tạo ra lô thứ hai của cùng một mặt hàng dùng chung — được khắc phục bằng cách kết nối đúng giữa lô và sổ kho.",
        "Truy vấn luồng bán hàng không loại trừ các giao dịch trả hàng, nên khi có một giao dịch trả hàng, hệ thống lại tạo ra một hóa đơn giả thứ hai từ chính giao dịch trả hàng đó, làm sai lệch tổng hoa hồng.",
      ],
    },
  },

  "IP-PREMIX": {
    goldenDemoLabel: "Golden Demo #26",
    companyName: "Demo Premix Co.",
    testIds: ["PM01", "PM02", "PM03", "PM04", "PM05", "PM06", "PM07"],
    en: {
      testDescriptions: {
        PM01: "Micro-ingredient weighing tolerance, tighter than compound feed's generic tolerance",
        PM02: "A critical ingredient requires a second person's verification before manufacture",
        PM03: "Mixing must follow the formula's declared sequence order",
        PM04: "A formula requires Approved status to become the default",
        PM05: "Lot trace, reusing the compound feed golden demo's genealogy logic unmodified",
        PM06: "Potency stays within tolerance on the Certificate of Analysis",
        PM07: "Yield and reconciliation",
      },
      businessFlowSummary:
        "Demo Premix Co. produces a vitamin/mineral concentrate for feed mills: a bulk carrier dilutes several gram-scale micro-ingredients (including safety-critical selenium) mixed in a specific declared sequence, with the critical ingredient requiring a second person's verification before manufacture, tighter micro-weighing tolerance than generic feed manufacturing, and a Certificate of Analysis confirming potency.",
      notableBugsFixed: [
        "An unrelated demo's own BOM-approval check was unscoped and blocked any new default formula platform-wide until scoped correctly to its own company.",
        "An initial tolerance test picked a deviation value that was intercepted by a different, more generic tolerance check before ever reaching this demo's own tighter check — fixed by choosing a value strictly between the two thresholds.",
      ],
    },
    vi: {
      testDescriptions: {
        PM01: "Dung sai cân định lượng vi lượng, chặt hơn so với dung sai thông thường của thức ăn chăn nuôi hỗn hợp",
        PM02: "Nguyên liệu trọng yếu đòi hỏi phải có người thứ hai xác nhận trước khi sản xuất",
        PM03: "Việc trộn phải tuân theo đúng trình tự đã khai báo trong công thức",
        PM04: "Công thức phải ở trạng thái Đã phê duyệt mới có thể trở thành công thức mặc định",
        PM05: "Truy vết theo lô, tái sử dụng nguyên vẹn logic phả hệ từ Golden Demo thức ăn chăn nuôi hỗn hợp",
        PM06: "Hàm lượng hoạt chất (potency) nằm trong dung sai cho phép trên Phiếu kiểm nghiệm (CoA)",
        PM07: "Hiệu suất và đối chiếu sản lượng",
      },
      businessFlowSummary:
        "Demo Premix Co. sản xuất chất cô đặc vitamin/khoáng chất cung cấp cho các nhà máy thức ăn chăn nuôi: một chất mang khối lượng lớn (bulk carrier) được pha loãng với nhiều nguyên liệu vi lượng ở quy mô gram (bao gồm selen — một nguyên liệu quan trọng về an toàn), được trộn theo đúng trình tự đã khai báo, với nguyên liệu trọng yếu đòi hỏi người thứ hai xác nhận trước khi sản xuất, dung sai cân định lượng vi lượng chặt hơn so với sản xuất thức ăn chăn nuôi thông thường, và một Phiếu kiểm nghiệm (CoA) xác nhận hàm lượng hoạt chất.",
      notableBugsFixed: [
        "Bài kiểm tra phê duyệt BOM của một demo khác không liên quan không được giới hạn phạm vi, khiến mọi công thức mặc định mới trên toàn nền tảng đều bị chặn, cho đến khi được giới hạn đúng theo phạm vi công ty của chính nó.",
        "Bài kiểm tra dung sai ban đầu chọn một giá trị lệch bị một bài kiểm tra dung sai khác, tổng quát hơn, chặn lại trước khi kịp đến được bài kiểm tra chặt hơn của chính demo này — được khắc phục bằng cách chọn một giá trị nằm đúng giữa hai ngưỡng.",
      ],
    },
  },

  "IP-INGREDIENT-TRADING": {
    goldenDemoLabel: "Golden Demo #27",
    companyName: "Demo Ingredient Trading Co.",
    testIds: ["FT01", "FT02", "FT03", "FT04", "FT05", "FT06", "FT07"],
    en: {
      testDescriptions: {
        FT01: "Shipment quantity reconciliation: ordered vs. received vs. invoiced",
        FT02: "Foreign-exchange handling on an import purchase",
        FT03: "Supplier lot is traceable",
        FT04: "Incoming QC gates release",
        FT05: "A committed-quantity contract blocks over-commitment",
        FT06: "Price history across multiple dated price records",
        FT07: "Margin report from real purchase vs. sales data",
      },
      businessFlowSummary:
        "A pure trading company (no manufacturing) importing soybean meal and fish meal with real FX exposure and transit shrinkage, receiving with incoming QC, reselling to domestic feed mills under a committed-quantity contract, and tracking price history and margin per ingredient.",
      notableBugsFixed: [
        "An early draft referenced a field that only exists on sales orders, not purchase orders, causing a database error.",
        "A foreign-currency purchase invoice failed against the company's local-currency-only default account until a dedicated foreign-currency account was set up.",
        "A quality-inspection reading value that worked on the development site was rejected on the production site because of a locale-specific number format difference.",
      ],
    },
    vi: {
      testDescriptions: {
        FT01: "Đối chiếu số lượng lô hàng: đặt hàng so với thực nhận so với hóa đơn",
        FT02: "Xử lý chênh lệch tỷ giá ngoại tệ trên đơn mua hàng nhập khẩu",
        FT03: "Lô hàng của nhà cung cấp có thể truy vết được",
        FT04: "Kiểm tra chất lượng đầu vào là điều kiện để xuất xưởng",
        FT05: "Hợp đồng cam kết số lượng ngăn chặn việc cam kết vượt mức",
        FT06: "Lịch sử giá qua nhiều bản ghi giá theo từng thời điểm",
        FT07: "Báo cáo biên lợi nhuận từ dữ liệu mua và bán thực tế",
      },
      businessFlowSummary:
        "Một công ty thương mại thuần túy (không sản xuất) nhập khẩu khô đậu tương và bột cá với rủi ro tỷ giá ngoại tệ thực tế và hao hụt trong vận chuyển, tiếp nhận hàng kèm kiểm tra chất lượng đầu vào, bán lại cho các nhà máy thức ăn chăn nuôi trong nước theo hợp đồng cam kết số lượng, đồng thời theo dõi lịch sử giá và biên lợi nhuận theo từng loại nguyên liệu.",
      notableBugsFixed: [
        "Bản nháp ban đầu tham chiếu đến một trường chỉ tồn tại trên đơn bán hàng chứ không phải đơn mua hàng, gây ra lỗi cơ sở dữ liệu.",
        "Hóa đơn mua hàng bằng ngoại tệ bị lỗi khi đối chiếu với tài khoản mặc định chỉ hỗ trợ nội tệ của công ty, cho đến khi một tài khoản ngoại tệ riêng được thiết lập.",
        "Giá trị đo kiểm tra chất lượng hoạt động bình thường trên môi trường phát triển lại bị từ chối trên môi trường thực tế, do khác biệt định dạng số theo từng vùng (locale).",
      ],
    },
  },

  "IP-MEAT-PROCESSING": {
    goldenDemoLabel: "Golden Demo #28",
    companyName: "Dong Nai Meat Processing Plant",
    testIds: ["MP01", "MP02", "MP03", "MP04", "MP05", "MP06", "MP07"],
    en: {
      testDescriptions: {
        MP01: "Incoming lot sourced from a real upstream pig sale lot",
        MP02: "Two-stage yield (live weight → carcass → cut), each stage blocked from exceeding its input",
        MP03: "Multi-source processing-batch genealogy, one batch consuming two incoming lots",
        MP04: "A QC hold blocks packing until released",
        MP05: "Cold storage record",
        MP06: "A finished lot traces back to its source animal and farm",
        MP07: "A recall-impact query resolves either upstream lot to the same downstream distributed lot",
      },
      businessFlowSummary:
        "Dong Nai Meat Processing Plant receives two incoming pig lots — one a real, already-sold lot from the pig-farm golden demo, the other a self-contained direct-farm intake — processes both together into one batch, holds it for QC before packing, cold-stores it, and distributes it to a customer, with a recall-impact query proving either incoming lot traces to the same finished, distributed lot.",
      notableBugsFixed: [
        "A finished-lot's total packed weight was marked read-only but nothing computed it server-side, so it silently saved as empty on the first run.",
      ],
    },
    vi: {
      testDescriptions: {
        MP01: "Lô hàng đầu vào lấy nguồn từ một lô bán heo thực tế ở khâu thượng nguồn",
        MP02: "Hiệu suất hai giai đoạn (trọng lượng hơi → thân thịt → thịt pha lóc), mỗi giai đoạn đều bị chặn không cho vượt quá đầu vào",
        MP03: "Phả hệ lô chế biến từ nhiều nguồn, một lô tiêu thụ từ hai lô đầu vào",
        MP04: "Việc tạm giữ chờ kiểm tra chất lượng (QC hold) chặn đóng gói cho đến khi được xuất xưởng",
        MP05: "Bản ghi lưu kho lạnh",
        MP06: "Lô thành phẩm được truy vết ngược về đúng con vật và trang trại nguồn",
        MP07: "Truy vấn phạm vi ảnh hưởng khi thu hồi cho phép xác định cả hai lô đầu vào đều dẫn đến cùng một lô phân phối ở hạ nguồn",
      },
      businessFlowSummary:
        "Nhà máy chế biến thịt Đồng Nai tiếp nhận hai lô heo đầu vào — một lô thực tế đã được bán từ Golden Demo trang trại heo, lô còn lại là hàng nhập trực tiếp từ trang trại một cách độc lập — chế biến cả hai cùng nhau thành một lô duy nhất, tạm giữ chờ kiểm tra chất lượng trước khi đóng gói, lưu kho lạnh, và phân phối cho khách hàng, với một truy vấn phạm vi ảnh hưởng khi thu hồi chứng minh rằng cả hai lô đầu vào đều truy vết được đến cùng một lô thành phẩm đã phân phối.",
      notableBugsFixed: [
        "Tổng trọng lượng đóng gói của lô thành phẩm được đánh dấu chỉ đọc (read-only) nhưng không có cơ chế nào tính toán giá trị này phía máy chủ, khiến trường này bị lưu trống một cách âm thầm trong lần chạy đầu tiên.",
      ],
    },
  },
};

/**
 * Resolves a pack's content for the given locale. Falls back to English for any pack whose
 * Vietnamese variant is missing (defensive only — every pack above has both `en` and `vi`).
 */
export function getPackContent(packCode: string, locale: string): IndustryPackContent | undefined {
  const source = PACK_CONTENT_SOURCE[packCode];
  if (!source) return undefined;

  const localized = (locale === "vi" ? source.vi : source.en) ?? source.en;

  return {
    goldenDemoLabel: source.goldenDemoLabel,
    companyName: source.companyName,
    testIds: source.testIds,
    unconfirmedTestIds: source.unconfirmedTestIds,
    testDescriptions: localized.testDescriptions,
    businessFlowSummary: localized.businessFlowSummary,
    notableBugsFixed: localized.notableBugsFixed,
  };
}
