# DEMO PLATFORM MASTER PLAN — VIETNAM ENTERPRISE SOFTWARE

**Version:** V4 — Repository Map + AI/Automation Architecture  
**Recommended repository path:** `D:\ME\ENTERPRISE_PLATFORM\enterprise-platform\documents\productization\00_demo_platform_master_plan.md`  
**Repository:** `enterprise-platform`  
**Primary runtime for public demos:** `D:\ME\ENTERPRISE_PLATFORM\frappe_docker_demo\`


**Mục đích tài liệu:** Tài liệu master để giao trực tiếp cho Claude Code/đội phát triển nhằm productize hệ thống ERP ENLIE hiện tại thành một nền tảng phần mềm doanh nghiệp đa ngành, đa site demo, tập trung thị trường Việt Nam.

# 0. REPOSITORY & REFERENCE MAP — ĐỌC TRƯỚC KHI CODE

Phần này là bản đồ tham khảo để AI/Claude Code không phải tự mò toàn bộ hệ thống trước khi hiểu cấu trúc.

> **Lưu ý:** Các đường dẫn bên dưới là cấu trúc mục tiêu/tham khảo. Nếu thực tế khác, phải kiểm tra bằng `git status`, `git rev-parse --show-toplevel`, `find`, `ls` hoặc công cụ tương đương trước khi sửa. Không được tự suy đoán và tạo duplicate folder chỉ vì không thấy ngay file.

## 0.1. Folder gốc trên máy phát triển

Cấu trúc khuyến nghị:

```text
D:\ME\ENTERPRISE_PLATFORM\
│
├── enterprise-platform\              ← GitHub repository chính
│
├── frappe_docker_demo\               ← Docker runtime riêng cho demo
│
├── frappe_docker_dev\                ← optional: dev runtime riêng
│
└── local-data\                       ← local backup/cache, không push Git
```

Không đặt source code chính bên trong `frappe_docker_demo`.

Không đưa database dump, backup production, API key hoặc secret vào Git.

---

## 0.2. GitHub repository chính

Tên repo khuyến nghị:

```text
enterprise-platform
```

Repository này là **source of truth cho product code + documentation + demo definitions + tests**.

Cấu trúc mục tiêu:

```text
enterprise-platform/
│
├── CLAUDE.md
│
├── README.md
│
├── pharmacountry/                    ← custom Frappe app hiện tại; chưa rename vội
│   ├── hooks.py
│   ├── modules.txt
│   ├── patches.txt
│   ├── pharmacountry/
│   │   ├── doctype/
│   │   ├── report/
│   │   ├── workspace/
│   │   ├── page/
│   │   ├── utils/
│   │   └── ...
│   └── public/
│
├── documents/
│   ├── project_status.md
│   ├── general/
│   │   └── ...                       ← tài liệu nghiệp vụ/flow hiện tại từ ERP ENLIE
│   │
│   └── productization/
│       ├── 00_demo_platform_master_plan.md   ← TÀI LIỆU NÀY
│       ├── 01_productization_audit.md
│       ├── 02_demo_infrastructure.md
│       ├── 03_platform_configuration.md
│       ├── 04_ai_automation_architecture.md
│       ├── 05_demo_factory.md
│       └── 06_demo_catalog_status.md
│
├── demo/
│   ├── templates/
│   ├── seeds/
│   ├── roles/
│   ├── workspaces/
│   ├── scenarios/
│   └── scripts/
│
├── tests/
│   └── ...                           ← nếu test không nằm trong từng Frappe module
│
├── frontends/                        ← chỉ tạo khi có Next.js use case thật
│   ├── dealer-portal/
│   ├── farm-app/
│   ├── shopfloor/
│   └── ...
│
└── services/                         ← chỉ tạo khi có service integration thật
    └── integration-api/              ← NestJS optional
```

### Quy tắc

- Không rename `pharmacountry` app chỉ để tên đẹp.
- Chỉ rename sau khi có audit đầy đủ về imports, hooks, DocType module, fixtures, patches, workspace, test và migration.
- Không tạo `enterprise_core` song song nếu capability đang tồn tại trong `pharmacountry`; phải audit/refactor trước.
- Không copy một module sang app khác rồi giữ hai bản.

---

## 0.3. ERP ENLIE hiện tại — nguồn tham khảo nghiệp vụ/code

ERP ENLIE hiện tại là **reference implementation**, không phải demo public.

AI phải tìm và đọc trước các khu vực sau:

```text
pharmacountry/
├── pharmacountry/doctype/
├── pharmacountry/report/
├── pharmacountry/workspace/
├── pharmacountry/page/
├── pharmacountry/utils/
├── public/js/
├── hooks.py
└── patches.txt
```

Và tài liệu:

```text
documents/
├── project_status.md
└── general/
    ├── QMS / DMS
    ├── Manufacturing / Production
    ├── Facility / Utilities
    ├── Equipment / Calibration / Qualification
    ├── HR / Administration
    ├── RA / Label Design
    ├── QC / R&D
    └── các file capability audit / roadmap liên quan
```

Không assume tên file cụ thể nếu chưa kiểm tra cây thư mục.

### Mục tiêu audit

Với mỗi DocType/workflow/report/script hiện hữu, phân loại:

```text
A. Reusable core
B. Reusable industry capability
C. ENLIE-specific configuration
D. ENLIE-only customization
E. Technical debt
```

Kết quả phải ghi vào:

```text
documents/productization/01_productization_audit.md
```

---

## 0.4. Docker ENLIE hiện tại

Runtime ERP ENLIE hiện tại **không được dùng làm demo public**.

Ví dụ cấu trúc cũ có thể tương tự:

```text
D:\ME\ERP_ENLIE\
├── frappe_docker/
│   └── pc-dev/
│
└── vnpharma-develop/
```

Đây chỉ là **reference từ dự án cũ**.

Claude Code phải:
1. Kiểm tra path thực tế.
2. Không sửa nhầm Docker ENLIE khi task là demo platform.
3. Không dùng DB ENLIE làm seed public.
4. Không copy private attachments sang demo.

Nếu phải đọc code cũ để productize, ưu tiên source Git/repo thay vì sửa trực tiếp runtime folder.

---

## 0.5. Docker demo mới

Runtime mới đề xuất:

```text
D:\ME\ENTERPRISE_PLATFORM\frappe_docker_demo\
```

Mục tiêu:

```text
frappe_docker_demo/
├── compose.yaml
├── .env                        ← không commit secret
├── sites/
├── logs/
├── backups/
├── scripts/
└── README.md
```

Docker demo phải có:
- MariaDB riêng.
- Redis riêng.
- workers riêng.
- scheduler riêng.
- site storage riêng.
- backup riêng.

Không dùng chung database container với ENLIE production/UAT.

---

## 0.6. Source of truth hierarchy

Khi tài liệu/code mâu thuẫn, ưu tiên đọc và đối chiếu theo thứ tự:

```text
1. Runtime behavior + current source code
2. Approved/current business flow documents
3. documents/project_status.md
4. documents/productization/00_demo_platform_master_plan.md
5. Older audit/roadmap notes
```

**Nhưng:** master plan này quyết định **kiến trúc productization tương lai**.  
Code cũ chỉ chứng minh hiện trạng, không được tự động coi mọi design cũ là design sản phẩm cuối.

Nếu phát hiện mâu thuẫn:
- không âm thầm chọn một bên;
- ghi rõ vào audit;
- đề xuất migration/refactor;
- giữ backward compatibility cho ENLIE nếu chưa có quyết định khác.

---

## 0.7. File AI phải đọc trước mỗi session lớn

Tối thiểu:

```text
1. CLAUDE.md
2. documents/productization/00_demo_platform_master_plan.md
3. documents/project_status.md
4. file nghiệp vụ liên quan trực tiếp đến task
5. code/module liên quan trực tiếp
```

Không cần đọc toàn bộ repository cho mỗi task.

Ví dụ task QMS:

```text
00_demo_platform_master_plan.md
project_status.md
QMS/DMS related docs
QMS DocTypes/workflows/reports
```

Ví dụ task Shrimp Farm mới:

```text
00_demo_platform_master_plan.md
platform_configuration.md
demo_factory.md
existing reusable core
CE-10 Farm Management spec
CE-11 Traceability spec
CE-13 AI/Automation spec nếu task có AI
```

---

## 0.8. Search strategy cho Claude Code

Trước khi tạo mới một DocType/function/report:

1. Search exact concept.
2. Search synonyms.
3. Search related DocTypes.
4. Check custom fields/workflows.
5. Check server/client scripts.
6. Check reports/workspaces.
7. Check documentation.
8. Chỉ tạo mới khi đã xác nhận không duplicate.

Ví dụ trước khi tạo `Equipment Qualification`:

```text
search:
Qualification
Validation
Equipment
Asset
Calibration
Facility
Utility
IQ
OQ
PQ
```

Mục tiêu: tránh tạo hai flow cho cùng nghiệp vụ.

---

## 0.9. Không gian trách nhiệm giữa các folder

```text
pharmacountry/
→ business/domain code Frappe

documents/
→ specification, audit, status, user/process docs

demo/templates/
→ edition/industry/demo definitions

demo/seeds/
→ dữ liệu giả lập

demo/scenarios/
→ guided sales demo scenario

demo/scripts/
→ create/reset/health/seed automation

frontends/
→ Next.js UX riêng khi justified

services/
→ NestJS/integration service khi justified

frappe_docker_demo/
→ runtime/deployment, không chứa domain source chính
```

---

## 0.10. Quy tắc Git branch/commit

Khuyến nghị:

```text
main
├── feature/productization-core
├── feature/demo-factory
├── feature/pharma-demo
├── feature/feed-demo
├── feature/shrimp-demo
└── feature/ai-platform
```

Mỗi commit nên:
- scope nhỏ;
- có task ID DP-xxx;
- không mix refactor lớn với data seed không liên quan;
- update `.md` liên quan khi task thay đổi trạng thái.

Ví dụ:

```text
DP-301: add edition registry
DP-406: add demo site health check
DP-1003: add AI provider adapter interface
```

---

## 0.11. Project status bắt buộc

`documents/project_status.md` phải có section Productization/Demo Platform với trạng thái tối thiểu:

```text
Task ID
Description
Code
Migration
Automated Test
Runtime Test
Documentation
Status
Notes
```

Status chuẩn:

```text
PLANNED
IN PROGRESS
CODE COMPLETE
MIGRATED
TESTED
UAT READY
DEMO READY
BLOCKED
```

Không dùng từ `DONE` nếu chỉ mới code xong.

---

## 0.12. CLAUDE.md khuyến nghị

Tạo file root:

```text
enterprise-platform/CLAUDE.md
```

Nội dung tối thiểu:

```text
Before modifying this repository:

1. Read documents/productization/00_demo_platform_master_plan.md
2. Read documents/project_status.md
3. Read only the business-flow documents relevant to the current task.
4. Search existing code before creating new DocTypes/modules.
5. Do not modify the ENLIE runtime stack for demo-platform tasks.
6. Do not copy ENLIE production data into public demos.
7. Keep Frappe/ERPNext as the default business core.
8. Add Next.js only for justified UX use cases.
9. Add NestJS only for justified integration/service use cases.
10. All AI calls must go through the provider-agnostic AI Gateway.
11. Update relevant documentation and project_status.md after each task.
12. Distinguish CODE COMPLETE, MIGRATED, TESTED and DEMO READY.
```

---

## 0.13. Bootstrap checklist cho AI khi bắt đầu project

Trước khi code:

- [ ] Xác nhận Git root.
- [ ] Xác nhận current branch.
- [ ] `git status`.
- [ ] Xác nhận path của custom Frappe app.
- [ ] Xác nhận path tài liệu.
- [ ] Xác nhận Docker ENLIE và Docker demo là hai stack khác nhau.
- [ ] Đọc master plan.
- [ ] Đọc project status.
- [ ] Audit code liên quan trước khi tạo mới.
- [ ] Ghi task ID đang thực hiện.
- [ ] Không sửa ngoài scope nếu chưa ghi nhận dependency.

Sau khi code:

- [ ] Run migration nếu schema đổi.
- [ ] Run tests.
- [ ] Runtime test bằng role thật.
- [ ] Update tài liệu.
- [ ] Update project status.
- [ ] Note rõ phần chưa test.
- [ ] `git status` và liệt kê file đã thay đổi.

---


**Phạm vi ngành:** Dược phẩm, thực phẩm bảo vệ sức khỏe/thực phẩm bổ sung, mỹ phẩm, trang thiết bị y tế, thuốc thú y, vaccine/sinh phẩm thú y, thức ăn chăn nuôi, premix/feed additive, chăn nuôi, thủy sản, aquafeed, sản phẩm xử lý môi trường nuôi trồng thủy sản, logistics/kho lạnh, chuỗi nhà thuốc, phân phối, bán lẻ, chế biến thịt/thủy sản, laboratory/QC, QMS, DMS, CMMS/EAM, procurement, portal và website.

**Nguyên tắc quan trọng:**  
- 32 demo experience **không đồng nghĩa 32 codebase**.  
- 32 demo experience **không đồng nghĩa 32 Docker Compose**.  
- Mục tiêu là **1 product platform + khoảng 15 capability engines + industry packs + nhiều Frappe sites độc lập + một số frontend chuyên biệt khi thật sự cần**.  
- **Frappe/ERPNext là business core mặc định** cho transaction, workflow, permission, audit trail, master data, report và back-office UI.  
- **Next.js không phải thành phần bắt buộc của mọi demo**; chỉ dùng khi Frappe Desk không phù hợp với trải nghiệm người dùng như shopfloor, farm/mobile, dealer/customer/supplier portal, public commerce hoặc executive UX riêng.  
- **NestJS không phải lớp bắt buộc giữa Next.js và Frappe**; chỉ đưa vào khi có integration phức tạp, IoT, API gateway, event processing, realtime, external services hoặc một backend-for-frontend thực sự cần thiết.  
- Ưu tiên kiến trúc đơn giản nhất có thể: `Frappe UI → Frappe` trước; nếu cần UX riêng thì `Next.js → Frappe API`; chỉ khi có lý do kỹ thuật rõ ràng mới dùng `Next.js → NestJS → Frappe`.  
- ERP ENLIE hiện tại là nguồn capability để tái sử dụng, **không được fork thành nhiều sản phẩm riêng**.  
- Mọi logic riêng của ENLIE phải được nhận diện, cấu hình hóa hoặc tách khỏi product core trước khi dùng cho demo thương mại.

---

# 1. MỤC TIÊU KINH DOANH

Xây dựng một hệ sinh thái phần mềm có thể giới thiệu, demo và triển khai cho doanh nghiệp Việt Nam theo 3 cách tiếp cận:

1. **Theo ngành**
   - Pharmaceutical
   - Nutraceutical / TPBVSK
   - Cosmetics
   - Medical Device
   - Veterinary
   - Animal Feed
   - Livestock
   - Aquaculture
   - Food/Animal Product Processing

2. **Theo mô hình doanh nghiệp**
   - Manufacturing
   - Import/Distribution
   - Warehouse/3PL
   - Retail/Chain
   - Farm
   - Laboratory
   - Service/Maintenance
   - Procurement
   - Portal/Commerce

3. **Theo sản phẩm phần mềm**
   - ERP
   - CRM
   - Procurement
   - WMS
   - Manufacturing/MRP
   - QMS
   - DMS
   - LIMS
   - EAM/CMMS
   - Farm Management
   - Traceability
   - Commerce/Portal

Mục tiêu thương mại là để khách hàng truy cập website công ty và nhận ra ngay:
- “Đây đúng là hệ thống cho ngành của tôi.”
- “Tôi có thể xem demo ngay.”
- “Tôi không phải mua toàn bộ; có thể chọn module.”
- “Hệ thống có thể mở rộng theo quy mô doanh nghiệp.”
- “Có thể triển khai cloud, dedicated cloud hoặc on-premise.”

---

# 2. QUYẾT ĐỊNH KIẾN TRÚC BẮT BUỘC

## 2.1. Một codebase, nhiều edition

Không tạo các repository kiểu:

```text
erp-pharma
erp-cosmetics
erp-feed
erp-veterinary
erp-aqua
...
```

Phải hướng tới:

```text
ONE PRODUCT CODEBASE
│
├── Core
├── Capability Engines
├── Industry Packs
├── Edition / Feature Configuration
└── Demo Seed Data
```

## 2.2. Docker Compose

Tối thiểu tách 3 môi trường:

```text
frappe_docker_dev
frappe_docker_enlie
frappe_docker_demo
```

### DEV
Dùng cho phát triển và kiểm thử kỹ thuật.

### ENLIE
Dùng cho ERP ENLIE/UAT/production, không để demo public ảnh hưởng.

### DEMO
Dùng cho tất cả site demo thương mại.

Không dùng chung MariaDB/Redis giữa ENLIE và DEMO.

## 2.3. Multi-site demo

Một demo stack có thể chứa nhiều site:

```text
pharma-mfg.demo.example.com
pharma-dist.demo.example.com
qms.demo.example.com
dms.demo.example.com
lims.demo.example.com
feed-mfg.demo.example.com
pig-farm.demo.example.com
shrimp-farm.demo.example.com
...
```

Mỗi site phải có:
- Database riêng.
- Site config riêng.
- Users/roles riêng.
- Demo dataset riêng.
- Workflow/config riêng.
- Có thể cùng dùng một version source code.

## 2.4. Frontend demo

Một số demo là Next.js frontend kết nối ERP/Frappe site:

```text
corporate.demo.example.com
brand.demo.example.com
dealer.demo.example.com
commerce.demo.example.com
pharmacy-online.demo.example.com
```

Không cần DB ERP mới nếu frontend có thể dùng backend site tương ứng.


## 2.5. Quy tắc chọn công nghệ

### Mặc định số 1 — Frappe/ERPNext

Mọi capability nghiệp vụ phải được đánh giá khả năng triển khai trong Frappe trước.

Dùng Frappe/ERPNext khi bài toán chủ yếu cần:
- Master data.
- Transaction.
- Workflow.
- Approval.
- Role/permission.
- Audit trail.
- Print/PDF.
- Report/dashboard.
- Background job.
- Attachment.
- Business rule.
- Back-office UI.

Các nhóm người dùng mặc định dùng Frappe Desk:
- Ban giám đốc/back-office.
- QA/QC.
- Kế toán.
- Mua hàng.
- Kho.
- Kế hoạch.
- R&D.
- Bảo trì.
- Quản lý sản xuất.
- HR/Admin.

### Mặc định số 2 — Next.js chỉ khi UX cần tách

Dùng Next.js khi có ít nhất một trong các lý do:
- Người dùng bên ngoài doanh nghiệp.
- Người dùng thao tác chủ yếu bằng điện thoại/tablet.
- Cần UI tối giản theo tác vụ.
- Cần public website/SEO.
- Cần e-commerce.
- Cần customer/dealer/supplier portal.
- Cần shopfloor UI lớn, ít nút, thao tác nhanh.
- Cần farm/field app tối ưu mobile.
- Cần executive dashboard UX khác hẳn ERP Desk.

Không được tạo Next.js frontend chỉ để thay giao diện Frappe nếu không có lợi ích nghiệp vụ rõ ràng.

### Mặc định số 3 — NestJS chỉ khi có service/integration need

NestJS chỉ được đưa vào khi có một trong các nhu cầu:
- Tích hợp nhiều hệ thống ngoài.
- API gateway.
- IoT/MQTT.
- Realtime/websocket ngoài khả năng hợp lý của Frappe.
- Event processing/stream.
- Queue/service orchestration phức tạp.
- Backend-for-frontend cần aggregate nhiều nguồn dữ liệu.
- Mobile API cần tách lifecycle/version riêng.
- Payment/logistics/e-invoice/SMS/Zalo/external services quy mô lớn.
- Multi-system identity/token mediation.

Nếu Next.js có thể gọi Frappe REST/RPC API trực tiếp và vẫn sạch, an toàn, maintainable thì **không thêm NestJS**.

## 2.6. Technology architecture chuẩn

### Pattern A — Frappe-first

```text
Browser
  ↓
Frappe Desk / Frappe Web
  ↓
Frappe Business Logic
  ↓
MariaDB
```

Dùng cho phần lớn ERP/QMS/DMS/LIMS/CMMS/back-office.

### Pattern B — Custom UX

```text
Next.js
   ↓
Frappe REST/RPC API
   ↓
Frappe Business Logic
   ↓
MariaDB
```

Dùng cho farm/mobile/shopfloor/portal/public commerce khi integration chưa phức tạp.

### Pattern C — Integration-heavy

```text
Next.js / Mobile / Device
          ↓
        NestJS
          ↓
   ┌──────┼────────┐
   ↓      ↓        ↓
Frappe   IoT   External APIs
```

Chỉ dùng khi Pattern B không còn phù hợp.

## 2.7. Quy tắc source code

Khuyến nghị logical structure:

```text
enterprise-platform/
├── frappe-app/
│   └── pharmacountry_enterprise/
├── frontends/
│   ├── dealer-portal/
│   ├── farm-app/
│   ├── shopfloor/
│   └── public-commerce/
├── services/
│   └── integration-api/      # chỉ tạo khi cần NestJS
└── demo/
    ├── templates/
    ├── seeds/
    └── scripts/
```

Không bắt buộc chuyển ngay sang monorepo. Đây là target organization; Claude Code phải ưu tiên ổn định code hiện hữu trước.

---

# 3. 15 CAPABILITY ENGINES

> **Cập nhật 2026-09-28:** CE-14 và CE-15 được thêm sau khi audit ERP ENLIE (xem `01_productization_audit.md` findings F-1/F-2 và quyết định của chủ dự án). Hai nhóm DocType lớn (HR Performance/Competency, R&D+RA) không khớp CE-01..CE-13 gốc; quyết định là tách riêng để tối đa khả năng tái sử dụng/bật-tắt độc lập theo edition, thay vì gộp vào CE-01/CE-06.

## CE-01 — ERP Core
Phạm vi:
- Company
- Fiscal Year
- Chart of Accounts
- Cost Center
- Customer
- Supplier
- Item
- Tax
- Currency
- Accounting
- Basic HR master
- Common workflow
- Permission
- Audit trail
- Notification
- Attachment
- Print format

Yêu cầu:
- Không hard-code tên ENLIE.
- Không hard-code company.
- Không hard-code mã phòng ban.
- Không hard-code warehouse.
- Mọi giá trị tổ chức phải cấu hình.

## CE-02 — CRM & Sales
- Lead
- Opportunity
- Quotation
- Sales Order
- Customer
- Territory
- Sales Person
- Promotion
- Contract
- Sales target
- Price list
- Customer credit
- Return

## CE-03 — Procurement
- Material/Purchase Request
- Approval matrix
- RFQ
- Supplier quotation
- Comparison
- Supplier selection
- Purchase Order
- Contract
- Receipt
- Invoice
- Supplier performance
- Approved vendor

## CE-04 — WMS & Logistics
- Warehouse hierarchy
- Bin/location
- Batch/lot
- Serial
- Expiry
- FEFO/FIFO
- Quarantine/released/rejected
- Picking
- Packing
- Delivery
- Stock transfer
- Barcode/QR
- Temperature/condition
- Traceability

## CE-05 — Manufacturing / MRP
- BOM/formula
- Routing
- Workstation
- Capacity
- Production plan
- Material requirement
- Work order
- Batch manufacturing
- Consumption
- Output
- Yield
- Rework
- Scrap
- Packaging
- Production reconciliation

## CE-06 — QMS
- Deviation
- CAPA
- Change Control
- OOS/OOT
- Complaint
- Recall
- Risk Assessment
- Audit
- Supplier Quality
- Effectiveness check
- Investigation
- Root cause

## CE-07 — DMS & Training
- Document request/change request
- Draft
- Review
- Approval
- Effective
- Distribution
- Training assignment
- Training acknowledgement
- Periodic review
- Revision
- Obsolete
- Controlled copy
- Record location

## CE-08 — LIMS / Laboratory
- Sample
- Specification
- Test parameter
- Method
- Analyst assignment
- Result
- Calculation
- Review
- Approval
- COA
- Reference standard
- Reagent
- Instrument
- Stability
- OOS/OOT integration

## CE-09 — EAM / CMMS / Validation
- Asset/equipment
- Utility
- Facility
- Calibration
- Preventive maintenance
- Breakdown
- Spare parts
- Qualification
- Validation
- Schedule
- Work order
- Service history
- Status and lifecycle

## CE-10 — Farm Management
- Farm
- Production unit
- Barn/house/pond/cage
- Biological batch/flock/herd
- Animal
- Breed/genetics
- Feed
- Medicine
- Vaccination
- Health
- Environment
- Growth
- Mortality
- Harvest
- Cost

## CE-11 — Traceability
Mục tiêu:
- Truy xuôi từ nguyên liệu/con giống đến thành phẩm.
- Truy ngược từ thành phẩm đến nguồn đầu vào.
- Batch genealogy.
- Recall simulation.
- Traceability report.
- Cross-site/process chain.

## CE-12 — Commerce / Portal
- Customer portal
- Dealer portal
- Supplier portal
- Product catalog
- Customer-specific price
- Stock availability
- Order
- Invoice/debt
- Return
- RFQ/quotation
- Documents
- B2C e-commerce integration


## CE-13 — AI & Automation Platform

### Mục đích

Tạo một capability dùng chung cho toàn bộ platform, không gắn cứng với OpenAI, Claude, Groq, Gemini hay bất kỳ model cụ thể nào.

Nguyên tắc:

```text
Business Modules
ERP / QMS / DMS / LIMS / EAM / Farm / WMS
                      │
                      ▼
             AI & Automation Layer
                      │
       ┌──────────────┴──────────────┐
       │                             │
 Deterministic Automation        AI Gateway
       │                             │
 Frappe Rules/Jobs             Provider Router
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
                   OpenAI         Anthropic         Groq
                     │               │               │
                  Gemini          Local AI        Custom AI
```

### 13.1. Tách Automation và AI

**Automation** dùng khi rule xác định được:

```text
CAPA overdue
→ create task
→ notify owner
→ escalate manager
```

```text
Calibration due in 7 days
→ create calibration task
→ notify equipment owner
```

```text
DO < threshold
→ send alert
```

Automation mặc định phải ưu tiên:
- Workflow.
- Scheduled job.
- Background job.
- Notification.
- Rule engine.
- Event hook.
- Threshold rule.

Không dùng LLM cho rule deterministic nếu không cần.

**AI** dùng cho:
- Summarization.
- Classification.
- Extraction.
- Comparison.
- Natural-language querying.
- Similar-case retrieval.
- Draft generation.
- Anomaly explanation.
- Pattern detection.
- Decision support.
- Document Q&A.

### 13.2. Provider-agnostic architecture

Business module không được gọi trực tiếp SDK/API provider.

Không làm:

```python
openai.chat(...)
anthropic.messages(...)
groq.chat(...)
```

trong QMS/Manufacturing/Farm module.

Phải gọi abstraction:

```python
run_ai_action(
    action="deviation_analysis",
    context=...
)
```

AI Gateway chịu trách nhiệm:
- chọn provider;
- chọn model;
- kiểm tra capability;
- retry;
- fallback;
- timeout;
- usage/cost logging;
- structured output validation;
- audit.

### 13.3. AI Provider Registry

Tạo cấu trúc cấu hình tương đương:

```text
AI Provider
├── provider_code
├── provider_type
├── display_name
├── base_url
├── api_key_secret
├── enabled
├── timeout
├── rate_limit
├── data_policy
├── region
├── supports_streaming
├── supports_tools
├── supports_structured_output
├── supports_embeddings
├── supports_vision
└── notes
```

Provider type dự kiến:
- OpenAI.
- Anthropic.
- Groq.
- Google Gemini.
- OpenAI-compatible.
- Local/private.
- Custom.

Không hard-code API key trong source.

### 13.4. AI Model Registry

```text
AI Model
├── provider
├── model_code
├── context_window
├── input_types
├── output_types
├── capabilities
├── cost_input
├── cost_output
├── latency_class
├── privacy_class
├── enabled
└── priority
```

Capability examples:
- chat
- reasoning
- structured_output
- tool_use
- long_context
- embeddings
- vision
- classification
- extraction

### 13.5. AI Action Registry

Mỗi nghiệp vụ AI phải khai báo thành action, ví dụ:

```text
AI Action: DEVIATION_ANALYSIS
├── required_capabilities
│   ├── long_context
│   ├── reasoning
│   └── structured_output
├── preferred_provider
├── fallback_policy
├── prompt_template
├── allowed_tools
├── required_permission
├── human_review_required
├── max_cost
└── retention_policy
```

Các action tiêu chuẩn:
- summarize_document
- compare_document_versions
- classify_complaint
- deviation_analysis
- find_similar_deviations
- draft_capa
- analyze_oos_context
- explain_production_delay
- analyze_yield_anomaly
- review_batch_record
- compare_supplier_quotations
- analyze_inventory_risk
- analyze_feed_cost
- analyze_farm_fcr
- analyze_shrimp_pond
- ask_enterprise

### 13.6. AI Router

Router không chọn model chỉ bằng tên action.

Phải dựa trên:
- required capabilities;
- tenant/customer policy;
- privacy requirement;
- allowed provider;
- latency;
- cost limit;
- model health;
- fallback priority.

Ví dụ:

```text
Simple classification
→ low-cost/fast model

Long SOP comparison
→ long-context capable model

Confidential customer data
→ provider permitted by customer policy

Private-only customer
→ local/private model
```

### 13.7. Fallback

Ví dụ:

```text
Primary: Groq
↓ fail/rate limit
Secondary: OpenAI
↓ fail
Tertiary: Anthropic
```

Fallback phải:
- log rõ model/provider thực tế;
- không vượt privacy policy;
- không fallback sang external provider nếu customer chỉ cho private/local.

### 13.8. Private / Local AI support

Phải hỗ trợ endpoint nội bộ hoặc OpenAI-compatible API:

```text
AI Gateway
    ↓
http://private-ai.internal/v1
```

Mục tiêu để sau này có thể dùng:
- open-weight model;
- model self-hosted;
- fine-tuned model;
- AI riêng của công ty;
- customer-owned model.

ERP/QMS/Farm không cần thay code.

### 13.9. RAG / Enterprise Knowledge

Nguồn dữ liệu:
- SOP.
- Specification.
- Policy.
- Training material.
- Equipment manual.
- Quality records.
- Audit records.
- Approved reports.
- Business records được phép.

Pipeline:

```text
Approved content
→ extract
→ normalize
→ chunk
→ embedding
→ vector index
→ retrieval
→ permission filter
→ LLM answer
```

Bắt buộc:
- Permission-aware retrieval.
- Không index nội dung obsolete như current knowledge.
- Version metadata.
- Source citation trong UI.
- Re-index khi document revision/effective status thay đổi.
- Không cho user truy cập thông tin ngoài quyền của họ.

### 13.10. Tool Registry / Agent Tools

AI không được query SQL production tùy ý.

Phải thông qua tool được kiểm soát:

```text
Tool Registry
├── get_sales_summary
├── get_inventory_risk
├── get_batch_genealogy
├── get_open_capa
├── get_document
├── find_similar_deviation
├── get_equipment_status
├── get_farm_kpi
└── get_pond_water_trend
```

Mỗi tool:
- có permission;
- validate input;
- giới hạn scope;
- log invocation;
- trả structured output;
- không cho arbitrary SQL.

### 13.11. Human-in-the-loop

AI có thể:
- suggest;
- summarize;
- classify;
- draft;
- detect;
- explain;
- recommend.

AI không được tự động thay con người trong các quyết định regulated/high-impact mặc định như:
- batch release;
- final QA approval;
- CAPA closure;
- deviation closure;
- OOS final disposition;
- document approval;
- supplier approval;
- final change-control approval.

Nếu một customer muốn automation sâu hơn, phải là configuration riêng + risk assessment + explicit approval.

### 13.12. AI Audit Log

Mỗi AI execution phải lưu:

```text
AI Job
├── user
├── tenant/site
├── action
├── timestamp
├── provider
├── model
├── prompt_template_version
├── input_source_refs
├── retrieved_sources
├── tool_calls
├── output
├── tokens
├── estimated_cost
├── latency
├── status
├── user_feedback
├── accepted
├── edited
└── final_record_reference
```

Không bắt buộc lưu raw sensitive prompt nếu policy không cho phép; khi đó lưu hash/reference/metadata phù hợp.

### 13.13. AI Usage / Cost

Dashboard:
- cost by site;
- cost by action;
- cost by user;
- cost by provider;
- cost by model;
- latency;
- error rate;
- fallback rate;
- acceptance rate.

Cho phép:
- monthly budget;
- action budget;
- provider quota;
- tenant quota;
- disable expensive actions.

### 13.14. AI Evaluation

Mỗi action quan trọng phải có evaluation dataset.

Ví dụ `classify_complaint`:
- 100 labeled cases.
- expected category.
- expected severity range.
- false-positive/negative tracking.

`deviation_analysis`:
- human-review rubric.
- groundedness.
- source support.
- hallucination flag.
- actionability.

Không đổi model production chỉ vì benchmark chung tốt hơn; phải chạy regression trên evaluation set nội bộ.

### 13.15. Prompt Management

Prompt không hard-code rải rác.

Tạo:
```text
AI Prompt Template
├── code
├── version
├── system_instruction
├── input_schema
├── output_schema
├── enabled
└── change_history
```

Prompt change ở regulated workflow phải có version và audit.

### 13.16. Automation Rule Engine

Tạo model tương đương:

```text
Automation Rule
├── trigger_type
├── source_doctype
├── event
├── conditions
├── actions
├── delay
├── escalation
├── retry
├── enabled
└── audit_log
```

Trigger types:
- Event-based.
- Schedule-based.
- Threshold-based.
- AI-assisted.

### 13.17. AI-assisted automation

Ví dụ complaint:

```text
Complaint submitted
→ AI classifies category/severity suggestion
→ human confirms
→ deterministic workflow continues
```

Ví dụ deviation:

```text
Deviation created
→ AI summarizes
→ AI finds similar events
→ investigator reviews
→ AI drafts CAPA proposal
→ human approves
→ automation monitors due date
```

### 13.18. Security & Privacy

Bắt buộc:
- Provider permission by tenant.
- Secret management.
- No API key in client.
- PII/sensitive-field filtering where required.
- Data residency setting where applicable.
- Tool-level authorization.
- Prompt injection protection for retrieved documents.
- Max context/token limits.
- File type restrictions.
- Usage logging.
- Ability to disable external AI entirely.

### 13.19. AI configuration per customer

Customer có thể chọn:

```text
AI Mode
├── Disabled
├── External Providers
├── Customer API Key
├── Platform Managed
├── Private Endpoint
└── Hybrid
```

Ví dụ:
- Customer A → OpenAI.
- Customer B → Claude only.
- Customer C → Groq for low-cost tasks.
- Customer D → private local model only.

### 13.20. Future company-owned AI

Architecture phải cho phép:

```text
Current:
AI Gateway → third-party model

Future:
AI Gateway → company private model
```

Không thay đổi business module.

Roadmap AI riêng:
1. RAG trên model thương mại.
2. Fine-tuning cho task lặp lại.
3. Self-host open-weight model.
4. AI platform riêng nếu business case đủ lớn.

Không đặt mục tiêu train foundation model từ đầu ở phase đầu.

---

## CE-14 — HR Performance & Competency Management

Nguồn gốc: phát hiện từ audit ERP ENLIE (~30 DocType), không thuộc HR master cơ bản của CE-01.

Phạm vi:
- Competency / Competency Level
- Job Position / Job Level
- Job Qualification Requirement / Job Training Requirement
- Job Scorecard (KPI item, Competency item, Behavior item, Compliance item)
- Performance Cycle / Performance KPI / Performance Rating Band
- Employee Performance Review (+ KPI/Competency/Behavior/Compliance result)
- Employee Qualification Assessment
- Employee Training Assignment
- Employee Incident
- Development Plan / Development Action
- Performance Improvement Plan (PIP Action)
- Performance Calibration Log

Yêu cầu:
- Bật/tắt độc lập với CE-01 (ERP Core); không bắt buộc cho mọi demo.
- Không hard-code job title/department/tiêu chí đánh giá theo ENLIE; mọi tiêu chí phải cấu hình qua Competency/Job Scorecard template.
- Áp dụng permission-per-record như ENLIE đã làm (`has_permission`/`permission_query_conditions` theo Employee Performance Review, Employee Incident, Development Plan, PIP) — không lộ dữ liệu đánh giá nhân sự cho người không liên quan.

## CE-15 — R&D & Regulatory Affairs (RA)

Nguồn gốc: phát hiện từ audit ERP ENLIE (~15 DocType), dùng chung cho mọi ngành sản xuất có đăng ký lưu hành (dược, TPBVSK, mỹ phẩm, TBYT, thú y).

Phạm vi:
- RD Manufacturing Process
- RD Formulation Trial (+ Formulation Trial Item)
- RD Design Request
- RD BOM Amendment Log
- RD Project Document / RD Research Time Log
- Specification Type / Specification Detail
- RA Registration Dossier / RA Registration Tracking / RA Registration Change Log
- RA Dossier Submission Log
- RA Label Design Request / Label Design Content Sheet / Label Artwork

Yêu cầu:
- Formula/process ở trạng thái draft (R&D) phải tách rõ khỏi Master Batch Record đã approved (CE-05); không để R&D pha trộn với batch record đang sản xuất.
- Registration dossier/tracking không hard-code cơ quan quản lý hay quốc gia cụ thể; phải cấu hình được (phục vụ mở rộng ngoài Việt Nam sau này nếu cần).
- Label Design workflow tái sử dụng nguyên trạng permission/workflow đã có trong ENLIE (`RA Label Design Request`, `Label Design Content Sheet`, `Label Artwork` đã có sẵn permission hook + workflow).

---

# 4. INDUSTRY PACKS

Mỗi pack phải là cấu hình + workflow + terminology + seed data + dashboard + report; không copy core code.

```text
IP-PHARMA
IP-SUPPLEMENT
IP-COSMETICS
IP-MEDICAL-DEVICE
IP-VETERINARY
IP-VETERINARY-BIOLOGICAL
IP-FEED
IP-PREMIX
IP-LIVESTOCK-PIG
IP-LIVESTOCK-POULTRY
IP-LIVESTOCK-CATTLE
IP-HATCHERY
IP-AQUAFEED
IP-AQUA-ENVIRONMENT
IP-SHRIMP
IP-FISH
IP-AQUA-HATCHERY
IP-MEAT-PROCESSING
IP-SEAFOOD-PROCESSING
```

Mỗi industry pack phải khai báo:
- Enabled modules.
- Role template.
- Workspace template.
- Workflow template.
- Default document types.
- Master-data template.
- Sample/demo data.
- Reports/dashboard.
- Terminology overrides.
- Optional compliance checklist.

---

# 5. DEMO SITE STANDARD

Mọi demo site phải đáp ứng cùng chuẩn.

## 5.1. Demo users

Tối thiểu:
- `admin.demo`
- `director.demo`
- `manager.demo`
- 2–5 role users phù hợp demo

Ví dụ Pharma:
- qa.manager.demo
- qc.analyst.demo
- production.manager.demo
- warehouse.demo
- procurement.demo

Không dùng mật khẩu giống production. Demo account phải read/write trong phạm vi cho phép nhưng không được System Manager trừ account nội bộ.

## 5.2. Demo data

Mỗi site phải có:
- 1 company.
- 5–20 users.
- 20–100 master records.
- 10–50 transaction records.
- Ít nhất 3 workflow ở nhiều trạng thái.
- 1 dashboard có số liệu.
- 1 scenario từ đầu đến cuối.
- Ít nhất 1 tình huống ngoại lệ.

## 5.3. Reset demo

Phải có quy trình:
- Snapshot “golden demo”.
- Reset tự động theo lịch hoặc bằng script.
- Không reset trong khi có guided demo sales.
- Log lần reset.
- Backup trước reset.
- Không cho khách upload file nguy hiểm.

Script mục tiêu:

```bash
demo reset pharma-mfg
demo reset qms
demo reset shrimp-farm
```

## 5.4. Demo health check

Mỗi site:
- HTTP 200.
- Login được.
- Background jobs hoạt động.
- Scheduler hoạt động.
- Database reachable.
- Redis reachable.
- Home workspace load.
- 1 API smoke check.

---

# 6. QUY TẮC PRODUCTIZATION ERP ENLIE

Claude Code phải rà toàn bộ current custom app và phân loại mọi custom object thành:

### A. Reusable core
Giữ lại và tổng quát hóa.

### B. Reusable industry capability
Đưa vào industry pack/module.

### C. ENLIE-specific configuration
Chuyển từ code thành data/config.

### D. ENLIE-only customization
Không đưa vào product core.

### E. Technical debt
Refactor trước khi clone sang demo.

Không được xuất hiện logic kiểu:

```python
if company == "ENLIE":
```

Nếu behavior thực sự cần khác nhau, dùng:
- feature flag
- edition config
- company setting
- industry setting
- hook registry
- policy/rule table

---

# 7. DANH MỤC 32 DEMO EXPERIENCES

---

## DEMO 01 — PHARMACEUTICAL MANUFACTURING ERP

### Mục đích
Demo end-to-end cho nhà máy dược từ kế hoạch, mua nguyên liệu, kho, sản xuất, IPC/QC, hồ sơ lô, release, bán hàng và chất lượng.

### Khách hàng mục tiêu
- Nhà máy thuốc generic.
- Nhà máy thuốc không vô trùng.
- Nhà máy dược có QA/QC/R&D.
- Doanh nghiệp vừa và lớn.

### Capability
CE-01, 03, 04, 05, 06, 07, 08, 09, 11.

### Vai trò
- General Director
- Quality Director
- QA Manager
- QC Manager
- Production Manager
- Planning Officer
- Warehouse Officer
- Procurement Officer
- Maintenance
- Analyst
- Operator

### Master data bắt buộc
- Paracetamol API
- MCC
- PVP K30
- Magnesium Stearate
- PVC/Alu
- Printed carton
- Paracetamol 500 mg tablet
- BOM
- Routing
- RM Quarantine/Approved/Rejected warehouse
- FG Quarantine/Released
- Equipment
- SOP
- Specification

### Workflow demo chính
```text
Sales Forecast
→ Production Plan
→ Material Requirement
→ Purchase Request
→ RFQ/PO
→ Receipt
→ Quarantine
→ Sampling/QC
→ Material Release
→ Work Order
→ Dispensing
→ Manufacturing
→ IPC
→ Packing
→ FG QC
→ Batch Release
→ FG Warehouse
→ Sales Order
→ Delivery
```

### Cách build
1. Clone cấu hình reusable từ ENLIE.
2. Xóa toàn bộ company-specific code/data.
3. Tạo Pharma demo company.
4. Seed master data.
5. Tạo workflow QA/QC/Production.
6. Bật batch, expiry, quality status.
7. Link QMS/DMS/Equipment.
8. Tạo dashboard.
9. Tạo 3 completed batches + 1 batch đang sản xuất + 1 batch có deviation.
10. Tạo guided demo route.

### Test bắt buộc
- P01: Không thể xuất nguyên liệu Quarantine vào production.
- P02: Batch nguyên liệu Released mới được issue.
- P03: Work Order lấy đúng BOM version effective.
- P04: Consumption vượt tolerance phải cảnh báo/phê duyệt.
- P05: IPC out-of-limit sinh quality event theo config.
- P06: FG chưa QA release không được chuyển sang Released warehouse.
- P07: Batch genealogy truy được raw materials → FG.
- P08: Recall report truy FG → customers.
- P09: User Production không được tự approve QA release.
- P10: Document obsolete không được dùng làm current instruction.

### Hướng dẫn demo người dùng
1. Login Planning → mở Production Plan.
2. Xem material shortage.
3. Login Procurement → tạo RFQ/PO.
4. Login Warehouse → receive batch.
5. Login QC → sampling, result, approve.
6. Login Production → Work Order, material issue, process.
7. Login QA → review record, release batch.
8. Login Director → dashboard KPI.

### Acceptance criteria
- End-to-end hoàn tất không cần System Manager.
- Permission đúng role.
- Audit trail đủ.
- Print/PDF của batch summary sử dụng được.
- Dashboard hiển thị ít nhất production, quality, inventory, overdue.

---

## DEMO 02 — TPBVSK / NUTRACEUTICAL MANUFACTURING

### Mục đích
Demo cho doanh nghiệp sản xuất viên nang, viên nén, bột, cốm, siro hoặc dạng lỏng TPBVSK.

### Khác Pharma
- Công thức thiên về ingredient blend.
- Quản lý claim/label/product dossier.
- Batch/QC vẫn quan trọng nhưng workflow release có thể cấu hình nhẹ hơn pharma.
- Quản lý packaging/artwork mạnh.

### Capability
CE-01, 03, 04, 05, 06, 07, 08, 09, 11.

### Sample products
- Vitamin C 1000 mg effervescent tablet.
- Multivitamin capsule.
- Collagen powder sachet.

### Workflow
Raw material → QC → Formula → Production → Filling/Packing → QC → Release → Distribution.

### Test
- S01 Formula revision không làm thay đổi batch đã tạo trước đó.
- S02 Allergen/critical ingredient flag hiển thị đúng.
- S03 Artwork version phải đúng product version.
- S04 Batch expiry tính theo rule.
- S05 COA thành phẩm sinh từ approved results.
- S06 Traceability ingredient → lots → customers.

### User guide
Product Development → formula → approved version → planning → manufacturing → QC → release → sales.

---

## DEMO 03 — COSMETICS MANUFACTURING

### Mục đích
Cho nhà máy mỹ phẩm OEM/ODM hoặc brand tự sản xuất.

### Đặc thù
- Formula/bulk.
- Pilot/lab formula.
- Scale-up.
- Filling.
- Packaging.
- Artwork.
- Stability.
- Batch sample.
- Complaint.

### Sample
- Facial cleanser.
- Serum.
- Shampoo.
- Cream.

### Workflow
Formula → approve → bulk batch → bulk QC → filling → packing → final QC → release.

### Test
- C01 Formula revision.
- C02 Bulk batch và packed batch genealogy.
- C03 Packaging/artwork version.
- C04 Stability sample schedule.
- C05 Complaint trace về batch.
- C06 Rework không mất genealogy.

### User guide
R&D/Formula → Production → QC → Packaging → QA Release → Sales.

---

## DEMO 04 — MEDICAL DEVICE MANUFACTURING

### Mục đích
Cho doanh nghiệp sản xuất TBYT.

### Đặc thù
- BOM/assembly.
- Serial/lot.
- Design history/change.
- Supplier quality.
- Inspection.
- Device record.
- Calibration.
- Complaint/field action.

### Sample
- Infusion pump accessory.
- Examination lamp.
- Disposable medical kit.

### Test
- MD01 Serial unique.
- MD02 Approved BOM revision only.
- MD03 Critical supplier approval.
- MD04 Incoming inspection failure blocks use.
- MD05 Finished serial trace components.
- MD06 Complaint links serial/lot.
- MD07 Calibration overdue equipment blocks configured operation.

### User guide
Design/BOM → sourcing → incoming inspection → assembly → final inspection → serial → release → customer.

---

## DEMO 05 — PHARMACEUTICAL IMPORT & DISTRIBUTION

### Mục đích
Cho doanh nghiệp nhập khẩu, bán buôn thuốc.

### Capability
CE-01, 02, 03, 04, 06, 11.

### Workflow
Supplier → import/purchase → receipt → batch/expiry → quarantine/release → sales order → FEFO picking → delivery → invoice → receivable.

### Test
- PD01 FEFO suggestion.
- PD02 Expired batch cannot ship.
- PD03 Recalled batch blocks delivery.
- PD04 Credit limit.
- PD05 Customer return restores correct batch.
- PD06 Trace customer by batch.
- PD07 Near-expiry alert.

### User guide
Procurement → warehouse → release → sales → delivery → debt → recall report.

---

## DEMO 06 — CONSUMER HEALTH / COSMETICS DISTRIBUTION

### Mục đích
Cho distributor TPBVSK, mỹ phẩm, personal care.

### Đặc thù
- Dealer.
- Promotion.
- Sales target.
- Territory.
- Price policy.
- Salesperson.
- Returns.

### Test
- CD01 Customer price list.
- CD02 Promotion period.
- CD03 Sales territory.
- CD04 Dealer credit.
- CD05 Return linked original lot.
- CD06 Commission report.

### User guide
Create campaign → sales order → warehouse → delivery → receivable → sales dashboard.

---

## DEMO 07 — MEDICAL DEVICE DISTRIBUTION & FIELD SERVICE

### Mục đích
Cho distributor thiết bị bán kèm lắp đặt, bảo trì.

### Flow
RFQ/Quotation → order → serial-controlled delivery → installation → acceptance → warranty → service → calibration/maintenance → spare part.

### Test
- MDD01 Serial assigned at delivery.
- MDD02 Installation creates installed base.
- MDD03 Warranty period.
- MDD04 Service history by serial.
- MDD05 Spare part consumption.
- MDD06 Preventive service schedule.
- MDD07 Complaint linked installed device.

### User guide
Sales → delivery → install → warranty → service ticket → work order → service report.

---

## DEMO 08 — PHARMA 3PL / GSP / COLD CHAIN

### Mục đích
Cho kho thuê, logistics, cold-chain healthcare.

### Capability
CE-04, 11, CE-01 billing.

### Đặc thù
- Stock ownership by client.
- Temperature condition.
- FEFO.
- Quarantine.
- Inbound/outbound SLA.
- Storage fee.
- Picking fee.
- Transport.

### Test
- W01 Customer A cannot see B stock.
- W02 Temperature excursion creates event.
- W03 FEFO.
- W04 Quarantine block.
- W05 Inventory reconciliation.
- W06 Billing by service rule.

---

## DEMO 09 — PHARMACY CHAIN

### Mục đích
Cho chuỗi nhà thuốc nhiều chi nhánh.

### Core
- HQ.
- Central warehouse.
- Store.
- POS.
- Batch/expiry.
- Inter-store transfer.
- Replenishment.
- Loyalty.
- Promotions.
- Online integration.

### Test
- RX01 Store sees own stock.
- RX02 HQ replenishment.
- RX03 Expired product blocked.
- RX04 Inter-store batch transfer.
- RX05 POS return.
- RX06 Promotion.
- RX07 Central dashboard.

### User guide
HQ purchase → central warehouse → store replenishment → POS → customer/loyalty → return → dashboard.

---

## DEMO 10 — QMS

### Mục đích
Sản phẩm QMS standalone có thể bán cho nhiều ngành regulated.

### Modules
Deviation, CAPA, Change, OOS/OOT, Complaint, Recall, Risk, Audit, Supplier Quality.

### Flow mẫu
Deviation → Investigation → Root Cause → CAPA → Effectiveness → Closure.

### Test
- Q01 Required fields by stage.
- Q02 Segregation of duties.
- Q03 CAPA due date escalation.
- Q04 Effectiveness cannot close before due/evidence.
- Q05 Change impacts documents/training/equipment.
- Q06 OOS can create CAPA/deviation.
- Q07 Audit finding → CAPA.
- Q08 Full audit trail.

### User guide
Reporter → QA triage → investigator → approver → CAPA owner → effectiveness → QA closure.

---

## DEMO 11 — DMS & TRAINING

### Mục đích
Quản lý vòng đời SOP/spec/form/template và đào tạo.

### Flow
Document request → draft → review → approve → effective → training → periodic review → revision/obsolete.

### Test
- D01 Version immutable after effective.
- D02 Only effective document visible as current.
- D03 Training assignment on effective.
- D04 Obsolete version archived.
- D05 Controlled print logged.
- D06 Revision keeps history.
- D07 User without training flagged where configured.

### User guide
Request → author → review → approval → issue → training → periodic review.

---

## DEMO 12 — LIMS / QC LABORATORY

### Mục đích
Quản lý mẫu, specification, method, test, result, OOS/OOT, COA.

### Test
- L01 Sample unique.
- L02 Only effective spec/method.
- L03 Analyst permission.
- L04 Calculation reproducible.
- L05 OOS trigger.
- L06 Reviewed result cannot be silently edited.
- L07 COA only approved results.
- L08 Instrument calibration check.

### User guide
Receive sample → assign → test → result → review → approve → COA.

---

## DEMO 13 — EAM / CMMS / CALIBRATION / VALIDATION

### Mục đích
Quản lý vòng đời thiết bị, utility, facility, maintenance, calibration, qualification.

### Test
- E01 PM auto schedule.
- E02 Overdue calibration visible.
- E03 Breakdown creates work order.
- E04 Spare part issue.
- E05 Qualification linked equipment.
- E06 Equipment status prevents unauthorized use.
- E07 Service history complete.

### User guide
Register asset → qualification → in service → PM/calibration → breakdown → repair → requalification if required.

---

## DEMO 14 — VETERINARY PHARMACEUTICAL MANUFACTURING

### Mục đích
Nhà máy thuốc thú y dạng bột, dung dịch, tiêm, premix thuốc.

### Core
Tương tự pharma manufacturing nhưng terminology/product master phù hợp thú y, species/indication, withdrawal info và veterinary distribution linkage.

### Test
- VPM01 Species/indication master.
- VPM02 Formula/BOM revision.
- VPM03 Batch/expiry.
- VPM04 QC release.
- VPM05 Traceability.
- VPM06 Recall.
- VPM07 Label version.

### User guide
Product master → planning → raw material → production → QC → release → dealer/distributor.

---

## DEMO 15 — VETERINARY VACCINE / BIOLOGICAL MANUFACTURING

### Mục đích
Demo category cho vaccine/sinh phẩm thú y.

### Scope phase 1
- Biological lot genealogy.
- Seed/strain master.
- Batch stages.
- Cold chain.
- Potency/sterility result placeholders.
- Controlled storage.
- Release.

### Test
- VB01 Seed/strain lot trace.
- VB02 Biological batch genealogy.
- VB03 Cold-storage rule.
- VB04 QC required.
- VB05 Batch release segregation.
- VB06 Recall trace.

### Note
Không tuyên bố đây là full biopharma MES ở phase đầu. Demo phải ghi rõ scope.

---

## DEMO 16 — VETERINARY DISTRIBUTION

### Mục đích
Manufacturer/distributor → regional dealer → veterinary shop/farm.

### Core
Territory, dealer, sales rep, credit, promotion, batch/expiry, technical visit, cold-chain optional.

### Test
- VD01 Territory ownership.
- VD02 Dealer price.
- VD03 Batch expiry.
- VD04 Credit.
- VD05 Sales target.
- VD06 Recall.
- VD07 Technical visit linked customer.

---

## DEMO 17 — VETERINARY CLINIC / ANIMAL HOSPITAL

### Mục đích
Pet clinic hoặc veterinary service operation.

### Entities
Animal, Owner/Farm, Appointment, Encounter, Diagnosis, Prescription, Vaccination, Lab Order, Treatment, Invoice.

### Test
- VC01 Animal unique record.
- VC02 Vaccination history.
- VC03 Prescription stock deduction.
- VC04 Lab result linked encounter.
- VC05 Follow-up.
- VC06 Invoice/payment.
- VC07 Farm account may own many animals.

---

## DEMO 18 — COMPOUND FEED MANUFACTURING

### Mục đích
Nhà máy cám heo/gà/bò.

### Flow
Raw material → formula → planning → weighing → grinding → mixing → pelleting → cooling → packing → QC → warehouse.

### Entities
Ingredient, Formula, Nutrition target, Species, Life stage, Silo, Batch, Line, Pellet specification.

### Test
- F01 Formula revision.
- F02 Ingredient substitution approval.
- F03 Weighing tolerance.
- F04 Batch genealogy.
- F05 Yield.
- F06 QC release.
- F07 Cross-contamination/sequencing flag.
- F08 Silo stock.

---

## DEMO 19 — PREMIX / FEED ADDITIVE MANUFACTURING

### Mục đích
Premix vitamin/mineral/additives.

### Đặc thù
- Micro ingredients.
- Precision weighing.
- Carrier.
- Sequencing.
- Cross-contamination.
- Potency/concentration.
- Lot trace.

### Test
- PM01 Micro-weigh tolerance.
- PM02 Critical ingredient double-check.
- PM03 Sequence rule.
- PM04 Formula revision.
- PM05 Lot trace.
- PM06 COA.
- PM07 Reconciliation.

---

## DEMO 20 — FEED DISTRIBUTION & DEALER MANAGEMENT

### Mục đích
Quản lý hệ thống nhà phân phối/đại lý.

### Flow
Factory → distributor → dealer → farm.

### Features
Territory, route, salesperson, dealer tier, credit, debt, target, promotion, delivery, technical support.

### Test
- FD01 Dealer tier price.
- FD02 Territory.
- FD03 Credit/debt.
- FD04 Promotion.
- FD05 Sales target.
- FD06 Route delivery.
- FD07 Technical visit.

---

## DEMO 21 — FEED / INGREDIENT TRADING

### Mục đích
Doanh nghiệp thương mại nguyên liệu/feed additives.

### Features
Import, supplier, shipment, currency, contract, QC, warehouse, customer contract, price history.

### Test
- FT01 Shipment quantity reconciliation.
- FT02 FX handling.
- FT03 Supplier lot.
- FT04 Incoming QC.
- FT05 Contract quantity.
- FT06 Price history.
- FT07 Margin report.

---

## DEMO 22 — PIG FARM MANAGEMENT

### Mục đích
Trang trại heo giống/heo thịt.

### Entities
Farm, Barn, Pen, Animal/Batch, Sow, Boar, Breed, Service, Pregnancy, Farrowing, Weaning, Feed, Medicine, Vaccination, Weight, Mortality.

### KPI
- Farrowing rate.
- Born alive.
- Weaned/sow.
- ADG.
- FCR.
- Mortality.
- Feed cost/kg.
- Days to market.

### Test
- PF01 Animal/batch unique.
- PF02 Breeding lifecycle.
- PF03 Feed consumption.
- PF04 Vaccination due.
- PF05 Medicine withdrawal.
- PF06 Mortality.
- PF07 Cost allocation.
- PF08 Trace to sale lot.

### User guide
Create herd → breeding/farrowing → nursery → grower → treatment/feed → weighing → sale.

---

## DEMO 23 — POULTRY FARM MANAGEMENT

### Mục đích
Broiler/layer farm.

### Entities
House, Flock, Placement, Feed, Water, Weight, Mortality, Vaccination, Egg production, Culling, Sale.

### KPI
FCR, mortality, livability, body weight, egg production, feed/bird/day.

### Test
- PO01 Flock lifecycle.
- PO02 Daily mortality.
- PO03 Feed consumption.
- PO04 Vaccine schedule.
- PO05 Weight curve.
- PO06 Egg output for layer.
- PO07 Sale/harvest.

---

## DEMO 24 — CATTLE / DAIRY FARM MANAGEMENT

### Mục đích
Bò sữa/bò thịt.

### Entities
Animal, pedigree, breeding, pregnancy, calving, lactation, milking, health, feed ration, body condition.

### Test
- CT01 Pedigree.
- CT02 Reproduction.
- CT03 Milk record.
- CT04 Treatment.
- CT05 Feed ration.
- CT06 Culling/sale.
- CT07 Cost per animal/group.

---

## DEMO 25 — HATCHERY / BREEDING MANAGEMENT

### Mục đích
Gia cầm giống/con giống.

### Entities
Parent stock, egg batch, incubation, hatch, chick batch, grading, vaccination, dispatch.

### Test
- H01 Egg batch trace.
- H02 Incubator assignment.
- H03 Hatch rate.
- H04 Chick grading.
- H05 Vaccine.
- H06 Customer dispatch trace.

---

## DEMO 26 — AQUAFEED MANUFACTURING

### Mục đích
Nhà máy thức ăn tôm/cá.

### Đặc thù
Species, life stage, pellet size, floating/sinking, extrusion, drying, oil coating, water stability.

### Test
- AF01 Formula by species/stage.
- AF02 Pellet specification.
- AF03 Extrusion process record.
- AF04 Batch QC.
- AF05 Lot trace.
- AF06 Finished feed release.
- AF07 Yield.

---

## DEMO 27 — AQUACULTURE ENVIRONMENTAL PRODUCT MANUFACTURING

### Mục đích
Probiotic, mineral, disinfectant, water-treatment products.

### Features
Formula, batch, raw material, QC, label, finished product, dealer distribution.

### Test
- AE01 Formula revision.
- AE02 Batch/lot.
- AE03 QC.
- AE04 Label version.
- AE05 Release.
- AE06 Distribution trace.

---

## DEMO 28 — SHRIMP FARM MANAGEMENT

### Mục đích
Quản lý nuôi tôm thâm canh/công nghiệp.

### Entities
Farm, Pond, Water source, Stocking batch, Feed, Water parameter, Growth sample, Health, Treatment, Mortality, Harvest.

### KPI
- Survival rate.
- Biomass.
- ADG.
- FCR.
- Feed/day.
- Cost/kg.
- Days of culture.
- Water trend.

### Water parameters
DO, pH, temperature, salinity, alkalinity, NH3, NO2 và các trường cấu hình khác.

### Test
- SF01 Pond crop lifecycle.
- SF02 Stocking batch.
- SF03 Daily feed.
- SF04 Water measurement.
- SF05 Growth sample.
- SF06 Treatment.
- SF07 Mortality.
- SF08 Harvest trace.
- SF09 Cost.
- SF10 Alert threshold.

### User guide
Prepare pond → stock → feed → water monitoring → sampling → health/treatment → harvest → cost/traceability report.

---

## DEMO 29 — FISH FARM MANAGEMENT

### Mục đích
Cá tra, rô phi, cá lồng và các mô hình có thể cấu hình.

### Entities
Pond/cage, stocking, biomass, feed, growth, health, treatment, harvest.

### Test
- FF01 Stocking.
- FF02 Biomass estimate.
- FF03 Feed.
- FF04 Growth sample.
- FF05 Mortality.
- FF06 Harvest.
- FF07 Traceability.

---

## DEMO 30 — AQUACULTURE HATCHERY / SEED MANAGEMENT

### Mục đích
Trại giống tôm/cá.

### Entities
Broodstock, spawning, larval batch, nursery, feed, water, health, grading, seed batch, customer.

### Test
- AH01 Parent/broodstock trace.
- AH02 Spawning batch.
- AH03 Larval survival.
- AH04 Nursery.
- AH05 Health record.
- AH06 Seed batch dispatch.

---

## DEMO 31 — MEAT / ANIMAL PRODUCT PROCESSING

### Mục đích
Kết nối livestock → slaughter/processing → packed product → cold storage.

### Flow
Farm/lot → receiving → inspection → slaughter → processing → packing → QC → cold storage → distribution.

### Test
- MP01 Incoming lot.
- MP02 Yield.
- MP03 Process lot genealogy.
- MP04 QC hold/release.
- MP05 Cold storage.
- MP06 Finished lot → source animal/farm.
- MP07 Recall.

---

## DEMO 32 — SEAFOOD PROCESSING & EXPORT

### Mục đích
Kết nối aquaculture → harvest → seafood plant → cold storage → export.

### Flow
Farm/pond → harvest lot → receiving → grading → processing → freezing → packing → cold storage → shipment/export.

### Test
- SP01 Harvest lot receiving.
- SP02 Grade/yield.
- SP03 Processing batch.
- SP04 Packing lot.
- SP05 Cold storage.
- SP06 Shipment.
- SP07 Carton → batch → harvest → pond trace.
- SP08 Recall simulation.

---

# 8. 7 WEBSITE / PORTAL EXPERIENCE — CHỈ XÂY FRONTEND RIÊNG KHI CẦN

Các experience dưới đây có thể dùng chung backend từ các demo ở trên.  
**Không mặc định tất cả phải dùng Next.js.** Với public website, portal, e-commerce hoặc mobile/field UX thì Next.js là lựa chọn ưu tiên; với back-office workflow thì tiếp tục dùng Frappe Desk.

## WEB-01 Corporate + Product Catalog
Cho nhà máy/nhà phân phối.

## WEB-02 Brand / Consumer Product Website
Cho supplement/cosmetics/veterinary brand.

## WEB-03 B2B Customer / Dealer Portal
Catalog, price, stock, order, invoice, debt, return.

## WEB-04 Supplier / RFQ Portal
RFQ, quotation, PO, delivery, documents, qualification.

## WEB-05 B2C Commerce
Consumer products.

## WEB-06 Online Pharmacy
Frontend riêng, tích hợp pharmacy ERP.

## WEB-07 Farm Customer / Technical Service Portal
Farm account, orders, technical visits, treatment/feed recommendations, service history.

---

# 9. DEMO DEPLOYMENT TOPOLOGY

## 9.1. Khuyến nghị phase đầu

Phase đầu **chỉ cần Frappe demo stack**:

```text
frappe_docker_demo/
├── compose.yaml
├── .env
├── sites/
├── logs/
├── backups/
└── scripts/
```

Services dự kiến:
- backend
- frappe frontend/web
- websocket
- queue-short
- queue-long
- scheduler
- redis-cache
- redis-queue
- mariadb
- reverse proxy/nginx nếu cần

**Không thêm Next.js/NestJS vào compose này chỉ để “đủ stack”.**

Khi có frontend thực sự cần Next.js, deploy độc lập:

```text
demo-platform/
├── frappe_docker_demo/
│
├── nextjs-demo/
│   ├── farm-app
│   ├── dealer-portal
│   └── shopfloor
│
└── nestjs-services/
    └── integration-api   # chỉ khi thật sự cần
```

Có thể cùng server ở phase đầu nhưng lifecycle deployment phải tách logic:
- Frappe release.
- Frontend release.
- Integration service release.

Không để lỗi Next.js/NestJS kéo sập Frappe business core.

## 9.2. Naming

```text
pharma-mfg.demo.domain.vn
pharma-dist.demo.domain.vn
qms.demo.domain.vn
dms.demo.domain.vn
lims.demo.domain.vn
vet-mfg.demo.domain.vn
feed-mfg.demo.domain.vn
pig-farm.demo.domain.vn
shrimp-farm.demo.domain.vn
...
```

## 9.3. Không mở 32 site cùng lúc nếu server nhỏ

Hỗ trợ 3 trạng thái:
- Active always-on.
- Active on demand.
- Template only.

Phase đầu chỉ bật 8–12 demo quan trọng; các site còn lại tạo khi cần.

---

# 10. SITE FACTORY / AUTOMATION

Mục tiêu cuối:

```bash
demo create pharma-mfg
demo create feed-mfg
demo create pig-farm
demo reset qms
demo seed shrimp-farm
demo health
```

Mỗi template phải định nghĩa:

```yaml
edition: pharma_manufacturing
industry_pack: pharma
apps:
  - erpnext
  - pharmacountry
features:
  qms: true
  dms: true
  lims: true
  manufacturing: true
seed: seeds/pharma_mfg
users: roles/pharma_mfg
workspaces: workspaces/pharma_mfg
```

Không bắt buộc YAML; có thể JSON/DocType. Quan trọng là declarative.

---

# 11. SEED DATA FRAMEWORK

Cấu trúc đề xuất:

```text
demo/
├── common/
│   ├── countries
│   ├── currencies
│   └── common_users
├── pharma_mfg/
│   ├── company.json
│   ├── users.json
│   ├── items.json
│   ├── warehouses.json
│   ├── suppliers.json
│   ├── customers.json
│   ├── bom.json
│   ├── equipment.json
│   ├── documents.json
│   └── transactions/
├── pig_farm/
├── shrimp_farm/
└── ...
```

Seed phải:
- Idempotent nếu có thể.
- Có deterministic naming.
- Không chứa dữ liệu thật của ENLIE.
- Không chứa thông tin cá nhân thật.
- Có version.
- Có validation sau seed.

---

# 12. WORKSPACE / UX STANDARD

Mỗi site phải có landing workspace riêng theo vai trò.

Ví dụ Pharma Production Manager:

```text
Today
├── Planned batches
├── Running batches
├── Delayed batches
├── Material shortage
├── Yield exception
└── Pending review
```

QA:

```text
Pending
├── Deviation
├── CAPA
├── Change Control
├── OOS
├── Batch Release
├── Document Approval
└── Training overdue
```

Farm manager:

```text
Today
├── Feed due
├── Vaccination due
├── Mortality alert
├── Water alert
├── Harvest forecast
└── Cost trend
```

Không để khách demo đi qua desk mặc định với hàng trăm menu không liên quan.

---

# 13. ROLE & PERMISSION STANDARD

Mỗi module cần:
- Viewer
- Operator
- Reviewer
- Approver
- Manager
- System administrator

Segregation-of-duties test bắt buộc ở:
- QA release.
- QC review.
- Purchase approval.
- CAPA closure.
- Change approval.
- Payment/accounting.
- Batch release.

Không dùng System Manager để chứng minh flow nghiệp vụ.

---

# 14. TEST STRATEGY

## 14.1. Unit test
Cho business rules và helper.

## 14.2. DocType test
- Validation.
- State transition.
- Permission.
- Calculated fields.
- Link integrity.

## 14.3. Workflow test
Test từng transition với đúng/sai role.

## 14.4. Integration test
Ví dụ:
- Purchase Receipt → Batch → QC.
- Work Order → QC → Release.
- Deviation → CAPA.
- Farm harvest → processing receiving.
- Device delivery → installed base → maintenance.

## 14.5. E2E
Tối thiểu 1 end-to-end scenario/site.

## 14.6. Security
- Cross-company data.
- Cross-role access.
- Guest API.
- File upload.
- Demo credential.
- CSRF/auth.
- Rate limiting ở public demo nếu cần.

## 14.7. Performance
- Workspace < mục tiêu nội bộ.
- List pages với 10k records test ở representative sites.
- Batch trace report kiểm tra thời gian.
- Dashboard query không N+1 nghiêm trọng.

## 14.8. Upgrade/migration
Mọi schema change phải:
- migrate sạch.
- test seed.
- test existing ENLIE migration.
- không phá demo templates.

---

# 15. COMMON ACCEPTANCE CHECKLIST CHO MỖI DEMO

Mỗi demo chỉ được đánh dấu READY khi tất cả đạt:

- [ ] Site migrate thành công.
- [ ] Seed thành công.
- [ ] Login tất cả demo roles.
- [ ] Workspace đúng role.
- [ ] Không thấy menu không liên quan.
- [ ] Core scenario chạy end-to-end.
- [ ] Negative permission tests pass.
- [ ] Audit trail pass.
- [ ] Print format chính dùng được.
- [ ] Dashboard có dữ liệu.
- [ ] Traceability report nếu applicable.
- [ ] Backup/restore tested.
- [ ] Demo reset tested.
- [ ] No ENLIE private data.
- [ ] No hard-coded ENLIE company logic.
- [ ] Mobile/responsive smoke test.
- [ ] Sales guided script hoàn chỉnh.

---

# 16. GUIDED DEMO MODE

Mỗi site cần tạo trang “Start Demo” có:
- Mục tiêu.
- Tài khoản role.
- 5–10 bước.
- Link mở thẳng record.
- Nút reset scenario nếu cho phép.
- “What this demonstrates”.

Ví dụ:

```text
Scenario: Pharmaceutical Batch Release

1. Login Warehouse
2. Open RM Receipt PR-0001
3. Review batch status
4. Login QC Analyst
5. Enter result
6. Login QC Manager
7. Approve
8. Login Production
9. Start batch
10. Login QA
11. Release FG
```

Salesperson không được phải giải thích toàn bộ menu từ đầu.

---

# 17. DOCUMENTATION CHO NGƯỜI DÙNG

Mỗi capability phải có 4 cấp tài liệu:

## Level 1 — Quick Start
5–10 phút.

## Level 2 — Role Guide
Ví dụ QA Manager Guide, Farm Manager Guide.

## Level 3 — Process Guide
Ví dụ Deviation Process, Pig Breeding Cycle.

## Level 4 — Administrator Guide
Cấu hình workflow, master, permissions, numbering, templates.

Template mỗi guide:

```text
Purpose
Prerequisites
Roles
How to create
How to review
How to approve
How to amend
How to cancel
Reports
Common errors
FAQ
```

---

# 18. REPORT & DASHBOARD STANDARD

## Manufacturing
- Plan vs actual.
- OEE-lite nếu có data.
- Yield.
- Material shortage.
- Batch cycle time.
- Reject/rework.

## Quality
- Open deviation.
- CAPA overdue.
- OOS trend.
- Complaint trend.
- Change overdue.

## Distribution
- Sales.
- Gross margin.
- Inventory aging.
- Near expiry.
- Receivable aging.
- Dealer performance.

## Farm
- FCR.
- Mortality.
- Growth.
- Feed cost.
- Production.
- Harvest.
- Cost/kg.

## Aquaculture
- Biomass.
- Survival.
- Feed.
- Water trends.
- FCR.
- Harvest forecast.

---

# 19. TRACEABILITY STANDARD

Traceability engine phải hỗ trợ ít nhất:

```text
Source
→ Input Lot
→ Process Batch
→ Intermediate
→ Finished Lot
→ Warehouse
→ Delivery
→ Customer
```

Với farm:

```text
Parent/Seed
→ Stocking/Flock
→ Feed/Medicine
→ Production Unit
→ Harvest
→ Processing
→ Finished Product
→ Customer
```

Phải có 2 report:
- Trace Backward.
- Trace Forward.

Và 1 Recall Simulation.

---

# 19A. TECHNOLOGY DECISION MATRIX CHO 32 DEMO

Ký hiệu:
- **CORE** = công nghệ chính.
- **YES** = nên có trong phiên bản thương mại/demo trưởng thành.
- **OPTIONAL** = chỉ khi UX/integration yêu cầu.
- **NO** = không cần trong scope mặc định.
- **LATER** = nên để phase sau.

| Demo | Frappe/ERPNext | Next.js | NestJS | Ghi chú |
|---|---|---|---|---|
| 01 Pharma Manufacturing | CORE | OPTIONAL | OPTIONAL | Frappe Desk cho back-office; Next.js shopfloor/tablet về sau |
| 02 TPBVSK Manufacturing | CORE | OPTIONAL | NO/LATER | Frontend riêng chỉ khi có shopfloor |
| 03 Cosmetics Manufacturing | CORE | OPTIONAL | NO/LATER | Formula/QA/QC trên Frappe |
| 04 Medical Device Manufacturing | CORE | OPTIONAL | OPTIONAL | Field/device integration có thể cần service sau |
| 05 Pharma Distribution | CORE | OPTIONAL | NO/LATER | Portal khách hàng có thể tách Next.js |
| 06 Consumer Health Distribution | CORE | YES cho dealer portal | OPTIONAL | Back-office vẫn Frappe |
| 07 Medical Device Distribution & Field Service | CORE | YES cho field/mobile nếu cần | OPTIONAL | Technician mobile có lợi |
| 08 3PL/GSP/Cold Chain | CORE | OPTIONAL | OPTIONAL | IoT temperature integration có thể cần NestJS |
| 09 Pharmacy Chain | CORE | YES cho online/mobile | OPTIONAL | ERP/POS core ở Frappe; commerce UX riêng |
| 10 QMS | CORE | NO mặc định | NO | Không dựng frontend riêng ở phase đầu |
| 11 DMS & Training | CORE | NO mặc định | NO | Frappe phù hợp |
| 12 LIMS | CORE | OPTIONAL | OPTIONAL | Instrument integration có thể cần service |
| 13 EAM/CMMS/Validation | CORE | OPTIONAL mobile | OPTIONAL | Field technician app chỉ khi cần |
| 14 Vet Pharma Manufacturing | CORE | OPTIONAL | NO/LATER | Giống manufacturing core + industry pack |
| 15 Vet Vaccine/Biological | CORE | OPTIONAL | OPTIONAL | Instrument/cold-chain integration về sau |
| 16 Veterinary Distribution | CORE | YES dealer/mobile | OPTIONAL | Sales/technical field UX |
| 17 Veterinary Clinic | CORE | OPTIONAL/YES | OPTIONAL | Có thể dùng custom Frappe UI trước |
| 18 Compound Feed Manufacturing | CORE | YES shopfloor về sau | OPTIONAL | IoT/PLC integration nếu triển khai sâu |
| 19 Premix/Additive Manufacturing | CORE | OPTIONAL | OPTIONAL | Precision weighing/device integration |
| 20 Feed Dealer Management | CORE | YES | OPTIONAL | Dealer/sales mobile rất phù hợp Next.js |
| 21 Feed Ingredient Trading | CORE | OPTIONAL | NO/LATER | ERP trading core đủ |
| 22 Pig Farm | CORE backend | YES | OPTIONAL | Mobile/field UI rất nên |
| 23 Poultry Farm | CORE backend | YES | OPTIONAL | Mobile/field UI rất nên |
| 24 Cattle/Dairy Farm | CORE backend | YES | OPTIONAL | Mobile/field UI rất nên |
| 25 Hatchery/Breeding | CORE backend | YES | OPTIONAL | Tablet/mobile operational UX |
| 26 Aquafeed Manufacturing | CORE | OPTIONAL/YES | OPTIONAL | Shopfloor/IoT phase sau |
| 27 Aqua Environmental Products | CORE | OPTIONAL | NO/LATER | Frappe manufacturing đủ phase đầu |
| 28 Shrimp Farm | CORE backend | YES | YES/LATER | IoT water sensor là use case mạnh |
| 29 Fish Farm | CORE backend | YES | OPTIONAL/LATER | IoT tùy mô hình |
| 30 Aqua Hatchery | CORE backend | YES | OPTIONAL | Mobile operations |
| 31 Meat Processing | CORE | OPTIONAL/YES | OPTIONAL | Shopfloor/barcode/scanner |
| 32 Seafood Processing & Export | CORE | OPTIONAL/YES | OPTIONAL | Shopfloor + cold-chain integrations |

## 19A.1. AI/AUTOMATION SUITABILITY MATRIX

| Demo | Automation | AI value | AI examples |
|---|---|---|---|
| Pharma Manufacturing | HIGH | HIGH | batch review, delay/yield analysis |
| TPBVSK Manufacturing | HIGH | MEDIUM | batch summary, document compare |
| Cosmetics Manufacturing | HIGH | MEDIUM | formula/change summary, complaint |
| Medical Device Manufacturing | HIGH | HIGH | complaint/device history analysis |
| Pharma Distribution | HIGH | HIGH | inventory risk, near-expiry, demand insight |
| Consumer Distribution | HIGH | HIGH | promotion/sales/return analysis |
| Medical Device Distribution | HIGH | MEDIUM | service history summarization |
| 3PL/Cold Chain | HIGH | HIGH | excursion/anomaly analysis |
| Pharmacy Chain | HIGH | HIGH | stockout, expiry, sales insight |
| QMS | HIGH | VERY HIGH | deviation/CAPA/OOS copilot |
| DMS | HIGH | VERY HIGH | revision compare, Q&A, impact |
| LIMS | HIGH | HIGH | trend/OOS/stability context |
| EAM/CMMS | HIGH | HIGH | failure trend, overdue analysis |
| Vet Pharma | HIGH | HIGH | batch/QMS assistant |
| Vet Biological | HIGH | HIGH | lot/cold-chain/QC context |
| Vet Distribution | HIGH | HIGH | dealer/sales/expiry analysis |
| Vet Clinic | HIGH | MEDIUM | encounter summary, follow-up draft |
| Feed Manufacturing | HIGH | HIGH | cost/yield/ingredient analysis |
| Premix | HIGH | HIGH | precision exception analysis |
| Feed Dealer | HIGH | HIGH | dealer/debt/territory insight |
| Ingredient Trading | HIGH | HIGH | quotation/shipment/margin analysis |
| Pig Farm | HIGH | HIGH | FCR/mortality/health analysis |
| Poultry Farm | HIGH | HIGH | flock anomaly/FCR analysis |
| Cattle/Dairy | HIGH | HIGH | reproduction/milk/health trends |
| Hatchery | HIGH | MEDIUM/HIGH | hatch-rate anomaly |
| Aquafeed | HIGH | HIGH | formula/cost/yield |
| Aqua Environmental Products | HIGH | MEDIUM | batch/complaint analysis |
| Shrimp Farm | VERY HIGH | VERY HIGH | pond/water/FCR/anomaly |
| Fish Farm | HIGH | HIGH | growth/FCR/water trends |
| Aqua Hatchery | HIGH | HIGH | survival/water/health trends |
| Meat Processing | HIGH | HIGH | yield/traceability/quality |
| Seafood Processing | VERY HIGH | HIGH | yield/cold-chain/traceability |


# 19B. Quy tắc quyết định trước khi tạo Next.js

Claude Code phải trả lời **YES** cho ít nhất một câu sau:
1. User bên ngoài doanh nghiệp có cần dùng?
2. Mobile/tablet có phải kênh thao tác chính?
3. Frappe Desk tạo quá nhiều bước/field cho tác vụ?
4. Public SEO/e-commerce có phải yêu cầu?
5. Cần UI shopfloor/fullscreen/kiosk?
6. Cần offline/PWA?
7. Executive UX phải khác hoàn toàn back-office?

Nếu tất cả đều NO → **không tạo Next.js**.

## 19C. Quy tắc quyết định trước khi tạo NestJS

Claude Code phải chỉ ra ít nhất một requirement cụ thể:
- IoT/MQTT.
- Aggregate nhiều backend.
- External API orchestration.
- API versioning độc lập.
- High-volume event ingestion.
- Realtime service.
- Dedicated auth mediation.
- Queue/event service tách biệt.
- Integration lifecycle độc lập Frappe.

Nếu không có requirement cụ thể → **không tạo NestJS**.

## 19D. Ownership của business logic

Quy tắc bắt buộc:

```text
Business rule cốt lõi
→ nằm trong Frappe/backend domain

Next.js
→ presentation + task-focused interaction

NestJS
→ integration/orchestration, không duplicate business rule
```

Ví dụ:
- Quy tắc batch không được release khi QC fail phải nằm ở Frappe.
- Next.js chỉ hiển thị nút Release hoặc gọi API.
- NestJS không được tự tái lập một bộ rule release khác.

Điều này tránh 3 codebase có 3 logic khác nhau.


# 19E. AI & AUTOMATION DEMO STRATEGY

Không cần nhét AI vào tất cả 32 demo ngay lập tức. Phase đầu chọn các use case có giá trị rõ và dễ chứng minh.

## AI-DEMO-01 — Executive Assistant

Người dùng hỏi:
- “Doanh thu tháng này giảm vì sao?”
- “Những CAPA nào đang quá hạn?”
- “Batch nào đang bị hold?”
- “Tồn kho nào có nguy cơ hết hạn?”
- “Ao nào có FCR xấu nhất tháng này?”

Kiến trúc:

```text
User
→ Ask Enterprise
→ AI Action
→ approved tools/reports
→ structured business data
→ AI synthesis
```

Không cho AI arbitrary SQL.

Acceptance:
- Permission-aware.
- Có nguồn dữ liệu.
- Không trả dữ liệu ngoài quyền.
- Log provider/model/tool.
- Câu trả lời phải phân biệt data fact và AI interpretation.

## AI-DEMO-02 — QMS Copilot

Use cases:
- summarize deviation;
- find similar deviation;
- suggest investigation questions;
- draft CAPA;
- summarize audit finding.

Human approval bắt buộc.

## AI-DEMO-03 — DMS Copilot

Use cases:
- compare SOP revisions;
- create change summary;
- suggest impacted documents;
- suggest training impact;
- Q&A trên effective documents.

## AI-DEMO-04 — LIMS Insight

Use cases:
- OOS context summary;
- historical result trend;
- similar OOS;
- stability trend narrative.

AI không được generate laboratory result.

## AI-DEMO-05 — Manufacturing Insight

Use cases:
- explain production delay;
- yield anomaly analysis;
- batch-record completeness review;
- downtime summary.

## AI-DEMO-06 — Procurement Assistant

Use cases:
- extract supplier quotation;
- normalize terms;
- compare quotations;
- summarize price/delivery/payment/quality history.

AI không tự approve supplier.

## AI-DEMO-07 — Inventory Risk Assistant

Use cases:
- near expiry;
- slow moving;
- stockout risk;
- overstock;
- unusual returns.

## AI-DEMO-08 — Feed Manufacturing Assistant

Use cases:
- cost-driver analysis;
- ingredient price impact;
- yield anomaly;
- batch comparison.

Không tự đổi approved formula.

## AI-DEMO-09 — Livestock Farm Assistant

Use cases:
- FCR deterioration explanation;
- mortality anomaly;
- barn/flock requiring attention;
- feed-cost analysis.

## AI-DEMO-10 — Shrimp/Aquaculture Assistant

Use cases:
- pond instability analysis;
- feed/FCR trend;
- water trend analysis;
- anomaly explanation.

Automation handles hard thresholds.
AI handles interpretation.

## AI-DEMO-11 — IoT Automation

Target phase later:

```text
Sensor
→ MQTT
→ integration service
→ Frappe time-series/event record
→ threshold automation
→ AI anomaly analysis
```

NestJS becomes justified here if ingestion/orchestration load requires it.

---

# 19F. AI TEST STRATEGY

## Provider tests
- Enable/disable provider.
- Invalid key.
- Timeout.
- Rate limit.
- Fallback.
- Private-only mode.
- Provider blocked by tenant policy.

## Model router tests
- Capability mismatch.
- Cost ceiling.
- Preferred provider unavailable.
- Fallback respects privacy.
- Structured-output validation.

## RAG tests
- Effective doc retrieved.
- Obsolete doc not used as current.
- User without permission cannot retrieve.
- Version update triggers re-index.
- Source citations correct.

## Tool tests
- Unauthorized tool denied.
- Invalid params denied.
- Cross-company access denied.
- SQL injection-like input does not become SQL execution.
- Tool result schema validated.

## Human-review tests
- AI draft cannot auto-finalize regulated record.
- Accepted output records user/timestamp.
- Edited output tracks delta/reference.
- Rejected output does not modify final record.

## Automation tests
- Event trigger.
- Schedule trigger.
- Threshold trigger.
- Retry.
- Escalation.
- Duplicate-event protection/idempotency.

## Evaluation regression
Before changing default model:
- run action-specific eval dataset;
- compare accuracy/groundedness;
- compare cost;
- compare latency;
- record approval before rollout.

---

# 19G. AI ACCEPTANCE CRITERIA

CE-13 chỉ được coi là ready khi:

- [ ] Có Provider Registry.
- [ ] Có Model Registry.
- [ ] Có AI Action Registry.
- [ ] Có Prompt Template versioning.
- [ ] Có router.
- [ ] Có fallback.
- [ ] Có tenant/site AI policy.
- [ ] Có secrets management.
- [ ] Có AI Job/Audit Log.
- [ ] Có usage/cost tracking.
- [ ] Có permission-aware tool calls.
- [ ] Có permission-aware RAG.
- [ ] Có human-review mechanism.
- [ ] Có provider disable switch.
- [ ] Có private/custom endpoint support.
- [ ] Có at least 3 AI demo actions runtime-tested.
- [ ] Có deterministic automation engine/runtime-tested.
- [ ] Có failure-mode tests.
- [ ] Không có direct provider calls trong domain modules.
- [ ] Không có unrestricted SQL agent.
- [ ] Không có auto-approval cho regulated final decisions mặc định.


# 20. PHASE IMPLEMENTATION

## PHASE 0 — Freeze & Audit ENLIE
Mục tiêu: xác định reusable capability.

Tasks:
- Inventory custom DocTypes.
- Inventory workflows.
- Inventory server/client scripts.
- Inventory hooks.
- Inventory reports.
- Inventory workspaces.
- Inventory print formats.
- Find ENLIE hard-coded logic.
- Classify A/B/C/D/E theo mục 6.

Deliverable:
`productization_audit.md`

## PHASE 1 — Demo Infrastructure
- Tạo `frappe_docker_demo`.
- MariaDB riêng.
- Redis riêng.
- Worker riêng.
- Reverse proxy/domain.
- Create/reset/health scripts.
- Backup.
- Demo security baseline.
- **Không triển khai Next.js/NestJS ở phase này nếu chưa có demo cụ thể yêu cầu.**

Deliverable:
`demo_infrastructure.md`

## PHASE 2 — Platform Config Layer
- Edition.
- Feature flags.
- Industry Pack.
- Demo template registry.
- Seed runner.
- Role/workspace setup.
- AI feature flags/policy placeholders.
- Automation rule registry baseline.

Deliverable:
`platform_configuration.md`

## PHASE 2A — AI & Automation Foundation

Không cần hoàn thiện toàn bộ AI trước Golden Demos, nhưng phải tạo abstraction đúng ngay từ đầu.

Tasks:
- AI Provider Registry.
- AI Model Registry.
- AI Action abstraction.
- Prompt Template.
- AI Job/Audit Log.
- Provider adapter interface.
- OpenAI-compatible adapter.
- Anthropic adapter.
- Groq adapter.
- Custom/private endpoint adapter.
- Router/fallback baseline.
- Automation Rule baseline.
- Secrets/config.
- Tenant/site AI policy.

Chưa cần build RAG/agent phức tạp ở bước này nếu chưa có demo cần.

Deliverable:
`ai_automation_architecture.md`

## PHASE 3 — First 8 Golden Demos
Ưu tiên:
1. Pharmaceutical Manufacturing.
2. Pharma Distribution.
3. QMS.
4. DMS.
5. LIMS.
6. EAM/CMMS.
7. Feed Manufacturing.
8. Shrimp Farm.

Lý do: vừa tận dụng ENLIE vừa chứng minh được vertical Agri/Animal Health.

## PHASE 4 — Veterinary + Livestock
9. Vet manufacturing.
10. Vet distribution.
11. Pig.
12. Poultry.
13. Cattle.
14. Hatchery.

## PHASE 5 — Aqua Expansion
15. Aquafeed.
16. Aqua environmental product.
17. Fish farm.
18. Aqua hatchery.
19. Seafood processing.

## PHASE 6 — Remaining Commercial Verticals
- Supplement.
- Cosmetics.
- Medical device.
- Pharmacy.
- 3PL.
- Consumer distribution.
- Premix.
- Ingredient trading.
- Meat processing.

## PHASE 6A — AI Demo Expansion
Sau khi các Golden Demo có business data thật:
- Executive Assistant.
- QMS Copilot.
- DMS revision comparison.
- Manufacturing insight.
- Procurement comparison.
- Farm/Aquaculture insight.
- Permission-aware RAG.
- Tool registry.
- Evaluation datasets.

Không dùng AI để che lấp business workflow chưa hoàn thiện.

## PHASE 7 — Specialized UX / Portal / Web
Chỉ sau khi business core ổn:
- B2B dealer.
- Supplier/RFQ.
- Corporate/public web.
- Brand.
- Commerce.
- Online pharmacy.
- Farm/mobile.
- Shopfloor.

Technology:
- Next.js là lựa chọn ưu tiên cho các UX này.
- Gọi Frappe API trực tiếp khi hợp lý.
- Chỉ đưa NestJS vào những integration đã chứng minh cần service riêng.

---

# 21. TASK BREAKDOWN ĐỂ GIAO CLAUDE CODE

## EPIC DP-100 — Productization Audit
- DP-101 Scan custom DocTypes.
- DP-102 Scan workflows.
- DP-103 Scan permissions.
- DP-104 Scan hard-coded company values.
- DP-105 Scan ENLIE-specific master dependencies.
- DP-106 Classify reusable/non-reusable.
- DP-107 Write migration plan.

## EPIC DP-200 — Demo Docker
- DP-201 New compose directory.
- DP-202 Isolated DB.
- DP-203 Isolated Redis.
- DP-204 Site routing.
- DP-205 Backup.
- DP-206 Reset.
- DP-207 Healthcheck.
- DP-208 Logging.

## EPIC DP-300 — Edition / Industry Pack
- DP-301 Edition model.
- DP-302 Feature registry.
- DP-303 Industry pack registry.
- DP-304 Role template.
- DP-305 Workspace template.
- DP-306 Seed registry.
- DP-307 Idempotent setup.

## EPIC DP-400 — Demo Factory
- DP-401 Create site command.
- DP-402 Install app command.
- DP-403 Apply edition.
- DP-404 Seed.
- DP-405 Create users.
- DP-406 Health test.
- DP-407 Snapshot golden state.
- DP-408 Reset.

## EPIC DP-500 — Golden Pharma Demo
- DP-501 Pharma master.
- DP-502 Purchase flow.
- DP-503 Warehouse flow.
- DP-504 Manufacturing.
- DP-505 QC.
- DP-506 QA release.
- DP-507 QMS integration.
- DP-508 DMS.
- DP-509 EAM.
- DP-510 Dashboard.
- DP-511 E2E tests.
- DP-512 Guided demo.

## EPIC DP-600 — Agri Core
- DP-601 Farm master.
- DP-602 Biological batch.
- DP-603 Feed usage.
- DP-604 Medicine/vaccination.
- DP-605 Growth.
- DP-606 Mortality.
- DP-607 Environment.
- DP-608 Harvest.
- DP-609 Farm costing.
- DP-610 Traceability.

## EPIC DP-700 — Pig/Poultry/Cattle Packs
Industry-specific lifecycle, KPIs, seed, tests.

## EPIC DP-800 — Aqua Core
- Pond/cage.
- Stocking.
- Feed.
- Water.
- Growth.
- Health.
- Treatment.
- Harvest.
- Cost.
- Alerts.

## EPIC DP-900 — Portal
- Dealer.
- Supplier.
- Customer.
- Public catalog.
- Commerce.


## EPIC DP-1000 — AI Platform Foundation
- DP-1001 AI Provider DocType/config.
- DP-1002 AI Model registry.
- DP-1003 Provider adapter interface.
- DP-1004 OpenAI-compatible adapter.
- DP-1005 Anthropic adapter.
- DP-1006 Groq adapter.
- DP-1007 Private/custom adapter.
- DP-1008 AI Action registry.
- DP-1009 Prompt Template versioning.
- DP-1010 AI Job/Audit Log.
- DP-1011 Router.
- DP-1012 Fallback.
- DP-1013 Cost/usage tracking.
- DP-1014 Tenant AI policy.
- DP-1015 Secrets handling.
- DP-1016 Failure-mode tests.

## EPIC DP-1100 — Automation Engine
- DP-1101 Automation Rule model.
- DP-1102 Event trigger.
- DP-1103 Schedule trigger.
- DP-1104 Threshold trigger.
- DP-1105 Retry.
- DP-1106 Escalation.
- DP-1107 Idempotency.
- DP-1108 Audit log.
- DP-1109 Runtime tests.

## EPIC DP-1200 — RAG & Tooling
- DP-1201 Knowledge source registry.
- DP-1202 Document extraction.
- DP-1203 Chunking.
- DP-1204 Embedding abstraction.
- DP-1205 Vector store abstraction.
- DP-1206 Permission-aware retrieval.
- DP-1207 Tool registry.
- DP-1208 Tool authorization.
- DP-1209 Source citation.
- DP-1210 Re-index lifecycle.
- DP-1211 Prompt-injection controls.
- DP-1212 RAG regression tests.

## EPIC DP-1300 — AI Golden Demos
- DP-1301 Executive Assistant.
- DP-1302 QMS Copilot.
- DP-1303 DMS comparison assistant.
- DP-1304 Manufacturing insight.
- DP-1305 Procurement assistant.
- DP-1306 Inventory risk assistant.
- DP-1307 Feed assistant.
- DP-1308 Farm assistant.
- DP-1309 Shrimp pond assistant.
- DP-1310 Evaluation datasets.

---

# 22. CLAUDE CODE OPERATING RULES

Khi triển khai tài liệu này, Claude Code phải:

1. Không sửa ENLIE production stack để tạo demo.
2. Không copy database thật sang public demo.
3. Không fork app theo từng ngành.
4. Mọi thay đổi schema phải migrate được.
5. Mọi custom logic phải có test khi hợp lý.
6. Mỗi epic xong phải cập nhật status `.md`.
7. Không đánh dấu COMPLETE nếu chưa runtime test.
8. Phân biệt:
   - code complete
   - migrate complete
   - unit tested
   - runtime tested
   - UAT ready
   - demo ready
9. Không dùng System Manager để “test thay” role thật.
10. Không xóa/tắt logic ENLIE nếu chưa chứng minh backward compatibility.
11. Khi phát hiện hard-code hoặc technical debt, phải note thành task ID.
12. Mỗi site mới phải được tạo bằng automation/template, không setup thủ công dài hạn.
13. **Frappe-first:** không tạo frontend/service mới nếu Frappe đáp ứng tốt yêu cầu.
14. Không tạo NestJS chỉ để proxy API từ Next.js sang Frappe.
15. Không duplicate business logic giữa Frappe, Next.js và NestJS.
16. Next.js phải được coi là UX layer, không phải source of truth nghiệp vụ.
17. NestJS phải được coi là integration/orchestration layer, không phải ERP domain engine.
18. Mỗi đề xuất thêm technology mới phải ghi rõ requirement, lợi ích và chi phí vận hành.
19. Không hard-code OpenAI/Claude/Groq/Gemini trong domain module.
20. Mọi AI call phải đi qua AI Action/Gateway abstraction.
21. Không cho AI arbitrary SQL trên production database.
22. Mọi tool call phải permission-aware.
23. Automation deterministic phải ưu tiên rule/workflow/job trước LLM.
24. AI output ở regulated workflow mặc định là suggestion/draft, không auto-final approval.
25. Provider fallback phải tuân thủ customer privacy policy.
26. Mọi prompt quan trọng phải versioned.
27. Mọi model change phải regression-test action quan trọng.
28. Phải hỗ trợ custom/private AI endpoint để tương lai dùng AI riêng.

---

# 23. DEFINITION OF DONE CẤP PLATFORM

Platform chỉ được coi là productized phase 1 khi:

- [ ] Có demo Docker stack độc lập.
- [ ] Có ít nhất 8 golden demos.
- [ ] Có edition/industry pack mechanism.
- [ ] Có seed/reset mechanism.
- [ ] Có role/workspace templates.
- [ ] Có automated smoke test.
- [ ] Có traceability engine usable.
- [ ] Có common QMS/DMS/EAM reusable.
- [ ] ENLIE vẫn migrate/run bình thường.
- [ ] Không có private ENLIE data trong demo.
- [ ] Có documentation cho admin/user.
- [ ] Có guided sales demo.
- [ ] Có version/release process.
- [ ] Có backup/restore.
- [ ] Có monitoring/logging.
- [ ] AI Provider/Model abstraction tồn tại nếu CE-13 được bật.
- [ ] Không có domain module gọi trực tiếp provider SDK.
- [ ] Có AI audit/usage log.
- [ ] Có customer/site AI policy.
- [ ] Có ít nhất 3 AI actions runtime-tested ở phase AI.
- [ ] Có automation deterministic runtime-tested.

---

# 24. ĐỊNH HƯỚNG DOMAIN PUBLIC

Ví dụ:

```text
software.example.vn
│
├── /industries/pharmaceutical
├── /industries/supplements
├── /industries/cosmetics
├── /industries/medical-device
├── /industries/veterinary
├── /industries/animal-feed
├── /industries/livestock
├── /industries/aquaculture
│
├── /products/erp
├── /products/qms
├── /products/dms
├── /products/lims
├── /products/cmms
├── /products/wms
├── /products/procurement
├── /products/farm-management
└── /demos
```

Demo entry page phải có:
- Overview.
- Industries.
- Modules.
- Screenshots.
- Guided scenarios.
- Open live demo.
- Request consultation.

---

# 25. CUỐI CÙNG: NGUYÊN TẮC PHÁT TRIỂN DÀI HẠN

Nền tảng phải cho phép một capability xuất hiện ở nhiều ngành mà không duplicate code.

Ví dụ:

```text
Batch/Lot
├── Pharma
├── Veterinary
├── Feed
├── Aquafeed
├── Cosmetics
└── Seafood
```

Nhưng business rules được extension qua pack.

Tương tự:

```text
QMS Core
├── Pharma QMS Pack
├── Medical Device Pack
├── Veterinary Pack
├── Feed Pack
└── Seafood Pack
```

Và:

```text
Farm Core
├── Pig Pack
├── Poultry Pack
├── Cattle Pack
├── Shrimp Pack
└── Fish Pack
```

Mục tiêu cuối cùng không phải “có 32 site demo”, mà là chứng minh:

> **Một Enterprise Software Platform có thể cấu hình cho nhiều ngành regulated tại Việt Nam, từ nhà máy, laboratory, kho, phân phối, retail đến farm và processing, trên cùng một kiến trúc sản phẩm.**

---

# 25A. KIẾN TRÚC CÔNG NGHỆ MỤC TIÊU

## Cấp 1 — Tối giản, dùng mặc định

```text
User
 ↓
Frappe Desk
 ↓
Frappe/ERPNext
 ↓
MariaDB
```

Đây là kiến trúc mặc định của hầu hết module enterprise.

## Cấp 2 — Có custom experience

```text
Back-office users ──→ Frappe Desk
                         │
                         ▼
                    Frappe Core
                         ▲
                         │ API
External/mobile users → Next.js
```

Đây là target cho farm, shopfloor, dealer/customer/supplier portal.

## Cấp 3 — Integration heavy

```text
                         ┌── IoT
                         │
Next.js / Mobile → NestJS ├── External services
                         │
                         └── Frappe API
                                ↓
                           Frappe Core
```

Chỉ dùng khi có nhu cầu integration rõ ràng.

## Nguyên tắc tối thượng

```text
Frappe = System of Record + Domain Logic
Next.js = Experience Layer
NestJS = Integration Layer
AI Gateway = Model-independent AI capability layer
Automation Engine = Deterministic execution layer
```

Kiến trúc tổng thể:

```text
Users
│
├── Frappe Desk
├── Next.js
└── Mobile/PWA
        │
        ▼
Frappe / ERPNext Domain Core
        │
        ├── Automation Engine
        │      ├── Event
        │      ├── Schedule
        │      └── Threshold
        │
        ├── AI Gateway
        │      ├── Provider Registry
        │      ├── Model Router
        │      ├── RAG
        │      ├── Tools
        │      └── Audit/Cost/Eval
        │
        └── Integration Layer
               └── NestJS only when justified
                        │
                 IoT / External APIs
```

Không đảo ngược trách nhiệm này nếu chưa có architectural decision record giải thích lý do.


# 26. NEXT ACTION CHO CLAUDE CODE

Thứ tự chạy việc nên là:

```text
STEP 1
Audit ERP ENLIE hiện tại
↓
STEP 2
Tạo productization_audit.md
↓
STEP 3
Tạo frappe_docker_demo độc lập
↓
STEP 4
Tạo edition / industry-pack framework
↓
STEP 5
Tạo demo factory
↓
STEP 6
Tạo Pharmaceutical Manufacturing golden demo
↓
STEP 7
Tách QMS/DMS/EAM demo
↓
STEP 8
Tạo Agri/Farm Core
↓
STEP 9
Tạo Feed Manufacturing golden demo
↓
STEP 10
Tạo Shrimp Farm golden demo
↓
STEP 11
Mở rộng Veterinary/Livestock/Aquaculture
↓
STEP 12
Portal / website / mobile / shopfloor UX bằng Next.js khi cần
↓
STEP 13
Bổ sung AI Gateway + provider abstraction + automation foundation
↓
STEP 14
Tạo 3–5 AI golden use cases trên dữ liệu demo thật
↓
STEP 15
Chỉ bổ sung NestJS cho IoT/integration/service use case đã được xác nhận
↓
STEP 16
Mở rộng private/custom AI, RAG, tool calling và evaluation
```

**Không bắt đầu bằng việc tạo 32 site thủ công.**  
Phải xây platform/factory trước, rồi mới sinh site theo template.

**Không bắt đầu bằng việc dựng sẵn Next.js/NestJS cho mọi demo.**  
Phải hoàn thiện business core trên Frappe trước, sau đó chỉ tách UX/service ở nơi có lý do thực tế.

**Không hard-code AI provider.**  
Groq, OpenAI, Claude, Gemini, local model hay AI riêng trong tương lai đều phải chỉ là provider phía sau cùng một AI Gateway.

