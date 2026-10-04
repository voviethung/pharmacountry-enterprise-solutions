# PRODUCTIZATION AUDIT — PHASE 0 / EPIC DP-100

**Status:** IN PROGRESS (first pass)
**Scope:** DP-101…DP-107 per `00_demo_platform_master_plan.md` §20 (Phase 0) and §21 (EPIC DP-100)
**Date started:** 2026-09-28
**Read-only audit.** Nothing under `D:\ME\ERP_ENLIE\` was modified to produce this document, per master plan §0.4.

---

## 0. GROUND TRUTH — REPOSITORY MAP CORRECTIONS

The master plan's §0.1–§0.4 describe a *target* layout. Actual on-disk state differs in ways that change how every later phase should start. These are facts, not proposals — recorded here so no later session re-derives them from scratch or silently assumes the target layout is already real.

### 0.1. `enterprise-platform` repo is effectively empty

`D:\ME\ENTERPRISE_PLATFORM\enterprise-platform\` contains **only**:
```
documents/productization/00_demo_platform_master_plan.md
```
No `.git`, no `CLAUDE.md`, no `documents/project_status.md`, no `pharmacountry/` app, no `demo/`, no `frappe_docker_demo/`. It is not a git repository. None of the §0.13 bootstrap checklist items were satisfied when this session started.

**Also missing at `D:\ME\ENTERPRISE_PLATFORM\` level:** `frappe_docker_demo/`, `frappe_docker_dev/`, `local-data/` — none exist yet (Phase 1 work, not Phase 0).

### 0.2. The real Frappe reference app lives outside this repo

The custom Frappe app the master plan calls "pharmacountry" is **not** inside `enterprise-platform`. It lives at:

```
D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\        ← canonical, active app (git repo, branch `main`)
```

This matches the master plan's own §0.4 example path (`vnpharma-develop`), so the plan's author already anticipated this — but it means **DP-101→DP-107 must audit that external path**, not anything inside `enterprise-platform`, until a deliberate copy/link decision is made (see §7 below).

Confirmed via git log: most recent commit `2026-09-28 12:27:50 +0700` on branch `main`, with active `.claude/worktrees/agent-*` directories present — **another agent/session may be actively developing this app concurrently.** Per master plan §0.4, this audit did not and must not modify anything under `D:\ME\ERP_ENLIE\`.

### 0.3. A second, stale copy of the app exists — do not confuse it with the canonical one

```
D:\ME\ERP_ENLIE\vnpharma\vnpharma\        ← app_name="vnpharma", branch `develop`, last commit 2026-09-25
```
This predates the rename to `pharmacountry` and is 3 days stale relative to `vnpharma-develop`. Treat as legacy/reference-only. **Recommendation:** do not audit both in parallel; confirm with the team that `vnpharma-develop/pharmacountry` is the one to retire ENLIE-specifics from, and archive or delete the `vnpharma/vnpharma` copy once confirmed (DP-107 decision, not done here).

### 0.4. Unrelated products share the "Pharmacountry" name — do not conflate

Two other codebases named "Pharmacountry" exist on this machine and are **not** part of the ERP/demo-platform scope in the master plan:

```
D:\ME\Pharmacountry\Pharmacountry_BE\           ← NestJS + Prisma + Elasticsearch B2B directory/marketplace backend
D:\ME\Quantri-pharmacountry\                     ← its Next.js admin frontend
D:\ME\ERP_ENLIE\pharmacountry_be\ / _fe\ / _db\  ← apparent duplicate/newer copies of the same directory-site product
```
These are a separate B2B pharma-company directory/marketplace website (company profiles, supply forms, scraping pipeline) with no Frappe/ERPNext involvement. They are unrelated to the ERP productization effort and are **out of scope** for this master plan. Flagging this explicitly so no future session tries to "productize" or merge them by name-matching alone.

### 0.5. ENLIE Docker runtime confirmed separate

`D:\ME\ERP_ENLIE\frappe_docker\` (git repo) with a `pc-dev/docker-compose.yml` — matches master plan §0.4's expected shape. No `frappe_docker_demo` exists yet (Phase 1 scope). Rule "không dùng chung DB/Redis giữa ENLIE và DEMO" is currently trivially satisfied because the demo stack doesn't exist yet.

---

## 1. DP-101 — CUSTOM DOCTYPE INVENTORY

Source: `D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\pharmacountry\doctype\`

**258 custom DocTypes**, plus:
- **78** custom Reports
- **71** custom Print Formats
- **20** Workspaces (all role-scoped, see DP-103)
- **5** Dashboard Charts, **13** Number Cards
- **45** Property Setter / Custom Field overlays on standard Frappe/ERPNext DocTypes (`pharmacountry/custom/*.json`) — touches `BOM`, `Item`, `Customer`, `Supplier`, `Sales Order`, `Purchase Order/Receipt/Invoice`, `Delivery Note`, `Stock Entry`, `Work Order`, `Job Card`, `Batch`, `Quality Inspection`, `Employee`, `Department`, `Asset Maintenance`, etc.

### Grouping by domain (prefix-based, machine-derived — not exhaustive per-doctype classification yet, see DP-106)

| Domain grouping | Approx. count | Representative DocTypes | Likely Capability Engine |
|---|---|---|---|
| QC / Laboratory | 20 | `QC Test Method`, `QC Stability Result/Batch`, `QC Reagent Solution Log`, `QC Volumetric Instrument/Calibration Result`, `QC Chromatography Column`, `QC Proficiency Test`, `QC Working Standard Establishment`, `QC Su Co` (incident) | CE-08 LIMS |
| Equipment / Facility / CMMS | ~19 (`equipment_*` 13 + `facility_*` 3 + `instrument_*` 3) | `Equipment Downtime Log`, `Equipment Qualification Plan/Result`, `Equipment Maintenance Checklist/Monthly Plan`, `Facility Room`, `Facility Room Check Window`, `Instrument Calibration Log/Result` | CE-09 EAM/CMMS |
| Process/Analytical/Cleaning Validation | ~10 | `Process Validation Protocol/Plan/Batch/Critical Step`, `Analytical Method Validation`, `Cleaning Validation`, `Hold Time Validation` | CE-09 (Validation) |
| Batch Manufacturing Record / Production | ~15 | `Master Batch Record(+Component/Step Mapping)`, `Batch Manufacturing Record`, `BMR Quality Inspection/Material Consumption/Job Card Summary`, `Job Card Weighing Entry/Workforce Assignment/Execution Step`, `VN Pro Batch`, `VN Batch Item`, `VN Packing`, `VN Delivery Plan` | CE-05 Manufacturing / CE-11 Traceability |
| QMS (deviation/CAPA/complaint/recall/self-inspection) | ~20 | `Change Control` (+`CR Action Item/Affected Item/Effectiveness Review`), `Customer Complaint(+Investigation)`, `Non-Conformity Report`, `Product Recall(+Batch/Distribution/Warehouse Receipt/Committee Member)`, `Self Inspection(+Department/Finding)`, `Root Cause 6M`, `Risk Assessment Correction Report`, `Management Review(+Action/Department Report)` | CE-06 QMS |
| DMS / Document Control / Training | ~15 | `Document Change Request(+Review Party)`, `Document Distribution`, `Controlled Record Entry/Type/Related User`, `DMS Upload Session`, `GMP Training Program/Session/Participant`, `Destruction Participant/Certificate Participant`, `Label Artwork`, `Label Design Content Sheet` | CE-07 DMS & Training |
| RA (Regulatory Affairs) / Label | 5 | `RA Registration Dossier/Tracking/Change Log`, `RA Dossier Submission Log` | (not a numbered CE — RA/Label is called out separately in master plan §0.3) |
| R&D | ~15 (`rd_*` 10 + `rdop_*` 5) | `RD Manufacturing Process`, `RD Formulation Trial(+Item)`, `RD Design Request`, `RD BOM Amendment Log`, `RDOP Process Step/Production Step/QC Control/Formula Item/Specification Reference` | Not a numbered CE — R&D/formulation pipeline |
| **HR Performance & Competency** | ~30 | `Employee Competency/Performance Review/Qualification Assessment/Training Assignment/Incident`, `Job Scorecard(+Behavior/Compliance/Competency/KPI Item)`, `Job Position/Level/Qualification Requirement/Training Requirement`, `Competency(+Level)`, `Performance Cycle/KPI/Rating Band/Calibration Log/Review *Result`, `Development Plan/Action`, `PIP Action` | **Not one of the 13 CEs** — see finding F-1 below |
| Supplier evaluation | 8 | `Supplier Evaluation(+Delivery)`, `Supplier Classification(+Band)`, `Supplier Delivery Evaluation` | CE-03 Procurement |
| Product Quality Review | 3 | `Product Quality Review`, `PQR Batch Performance/Quality Result/Linked Record` | CE-06/CE-08 |
| VN-prefixed generic engines | ~32 (`vn_*` 11 + `vn*` 21) | `VN Naming Rule`, `VN Automation Setting/Log`, `VN Department(+User)`, `VN Storage`, `VN Stock Shelf`, `VN Du Tru NLBB/PP/Item` (material reservation), `VN Dang Bao Che`, `VN Duong Dung`, `VN Tieu Chuan` | Mixed CE-01 (naming/automation infra) + CE-04/05 (pharma-domain masters) |
| PPA (pre-production/purchase approval?) | 5 | `PPA Item`, `PPA Sales Order`, `PPA Issue`, `PPA Department User/Approval` | CE-02/CE-03 approval workflow |
| Misc (vehicle, water, pest control) | ~8 | `Vehicle Maintenance/Environmental Log`, `Water Sampling Reading`, `Pest Control Inspection Log`, `Insect Light Maintenance Log`, `Sharps Tool Log`, `Daily Balance Check(+Measurement/Profile/Requirement)` | CE-09 |

**F-1 (finding):** the HR Performance/Competency/Job-Scorecard subsystem (~30 DocTypes) is large, mature, and generic-looking (no company-specific fields spotted in the sampled files) but doesn't map cleanly onto any of the master plan's 13 Capability Engines. Recommend either folding it into CE-01 (HR master) scope explicitly, or registering it as a 14th capability engine (`CE-14 — HR Performance & Competency`) before industry packs start depending on it. This needs a decision, not a default — flagging per master plan §0.6 conflict-resolution rule rather than silently picking one.

**F-2:** R&D (`rd_*`/`rdop_*`, ~15 DocTypes) and RA (`ra_*`, 5 DocTypes) are similarly outside the 13 CE list but clearly reusable across every regulated-manufacturing industry pack (Pharma, Nutraceutical, Cosmetics, Medical Device, Veterinary). Same recommendation as F-1.

---

## 2. DP-102 — WORKFLOW INVENTORY

Workflows are **not** stored as per-doctype files under the app module; they are core Frappe `Workflow` records shipped via `hooks.py` fixtures (`pharmacountry/fixtures/workflow.json` + `workflow_state.json`). 24 workflows are pinned by name in `hooks.py`:

```
Quality Inspection, Pre-Production Approval, Sales Order, Stock Entry, Purchase Receipt,
QC Request, Quotation, Material Request, BOM, Stock Reconciliation,
Process Validation Protocol, Validation Master Plan, Spreadsheet Validation,
Hold Time Validation, Utility Qualification, Analytical Method Validation,
Cleaning Validation, SOP Document, Document Change Request, Record Destruction Request,
Record Loan Request, RA Label Design Request, Label Design Content Sheet,
Label Artwork, GMP Training Session
```

Note in `hooks.py` (lines 53–59): a companion `Workflow State` fixture is required because Frappe's Workflow Builder UI auto-creates these records but a plain fixture import does not — a documented gotcha the current team already hit (`LinkValidationError` on fresh-site install). Relevant for DP-400 (Demo Factory) — the site-creation script must import fixtures in dependency order or replicate this workaround.

---

## 3. DP-103 — PERMISSION / ROLE SCAN

### Workspaces (= role-scoped Desk views), 20 total
```
bgd_gdcl, bgd_gdkd, bgd_gdsx, bgd_tgd        ← 4 director/BOD views split by function (GDCL=Quality?, GDKD=Business, GDSX=Production, TGD=General Director)
design_label, document_control, hr_self_service, hr_user,
maintenance_qualification, manufacturing_user, production_planner,
purchase_user, qa_qms_dms, qa_validation, qc_user, rd_manager, rd_user,
sales_user, specification_leader, stock_user
```
This is a genuinely role-segmented Desk setup already — a good sign for reuse (CE-01 "back-office UI" requirement is largely met).

### Scripted permission hooks (`hooks.py` `permission_query_conditions` / `has_permission`) — 14 DocTypes gated by custom Python, not just role permissions:
```
File, Controlled Record Entry, SOP Document, QC Result Distribution,
RA Label Design Request, Label Design Content Sheet, Label Artwork,
GMP Training Session, Employee Performance Review, Employee Qualification Assessment,
Employee Training Assignment, Employee Incident, Development Plan,
Performance Improvement Plan
```
All route through `pharmacountry.utils.*_permissions.*` modules — i.e., permission logic is centralized in `utils/`, not scattered per-doctype controller. Good for reuse; needs per-module review (not done in this pass) to confirm none of these functions hardcode company/department names.

### `override_doctype_class` (2): `Job Card` → `CustomJobCard`, `Stock Entry` → `CustomStockEntry`.
### `override_whitelisted_methods` (1): ERPNext's `purchase_order.make_purchase_receipt` overridden.

---

## 4. DP-104 — HARD-CODED COMPANY VALUE SCAN

Searched all `.py` under the app for `ENLIE`, `company ==`, `company_name ==`, literal company-name assignment, and default-company shortcuts.

**Result: clean in production code paths.** No occurrence of the literal string `ENLIE` anywhere in `.py`. The one file matching a "hardcoded company" pattern closely (`utils/accounting_readiness.py`) turned out to be a **self-audit utility** that iterates `frappe.get_all("Company", …)` dynamically and checks every company's COA/warehouse/tax setup generically — this is itself a reusable, config-driven diagnostic tool (classification candidate: **A — reusable core**, potentially valuable as a generic "tenant readiness check" for the Demo Factory's DP-406 health test).

**Caveat / technical debt found:** a cluster of root-level scratch scripts (`_e2e1.py` … `_e2e16.py`, `_seed.py`, `_smoke_reports.py`, `_e2e8.py`, `_e2e3.py`, `_e2e6.py`, `_e2e7.py`, `_e2e10.py`, `_e2e11.py`, `_e2e16.py`) sitting directly under the app root (outside `pharmacountry/pharmacountry/doctype/*/test_*.py` and outside `tests/`) hardcode `company = "Công ty A"` repeatedly. `"Công ty A"` is a generic placeholder, not the real ENLIE company name, so this is **not** a data-leak risk — but these files:
- are not part of the installed app package (they live at repo root, likely bench-console / manual smoke-test scripts from the active dev session),
- are candidates for **classification E (technical debt)** if committed to git as permanent artifacts, or should be moved into `pharmacountry/tests/` / excluded via `.gitignore` if they're throwaway session scratch.
This is a call for whoever owns `vnpharma-develop` — out of scope for this repo to change, but worth surfacing since Demo Factory (DP-400) will want a canonical, company-parameterized seed/smoke-test script, and these `_e2e*.py` files look like an early, ad hoc version of exactly that.

No hardcoded warehouse codes, department codes, or `if company == "..."` branching found in `pharmacountry/utils/` or `pharmacountry/pharmacountry/doctype/**/*.py` in this pass. **This is a first-pass grep-based scan, not a line-by-line read of all 834 `.py` files — treat as high-confidence but not exhaustive.**

---

## 5. DP-105 — ENLIE-SPECIFIC MASTER DATA DEPENDENCIES (completed this pass)

Read in full: `pharmacountry/setup.py` (2195 lines — the `before_install`/`after_install`/`after_migrate` hook target) and all 3 files under `pharmacountry/patches/ppa/`.

`setup.py` is a large, well-documented collection of `setup_*()` idempotent seed functions ("only insert if missing, never overwrite customer edits" is a consistent, explicitly-stated pattern throughout — a genuinely good design). Most of it is generic. Two findings stand out as real ENLIE-specific data baked into code that runs unconditionally **for every company on every site**:

### F-3 (finding, classification C) — `VN Department` seed list is ENLIE's actual org chart

`setup_vn_departments()` seeds three constant lists into every site:
```python
_DEFAULT_DEPARTMENTS = [("pp","PP"),("ra","RA"),("rd","RD"),("sc","SC"),("qc","QC"),
                        ("ed","ED"),("pd","PD"),("kho","Kho"),("qa","QA"),
                        ("gdcl","GĐCL"),("gdsx","GĐSX")]                         # 11 PPA pipeline depts
_QAS024_ONLY_DEPARTMENTS = [("ps","PS"),("sd","SD"),("hr","HR")]                 # 8 risk-council depts (with 5 overlapping above)
_ACCOUNTING_DEPARTMENT = [("kt","KT")]                                            # Accounting, added 2026-09-14
```
The code comment for the accounting department is explicit: *"mã `kt` lấy đúng từ mã 19-đơn-vị Excel gốc (`Co_cau_to_chuc.xlsx`)"* — i.e. taken directly from ENLIE's real organizational-chart spreadsheet. This isn't gated by `if company == "ENLIE"` (which the master plan explicitly forbids), but the practical effect is the same: **any new site — demo or otherwise — installing this app inherits ENLIE's exact 11+8+1 department structure by default.** No `if company` branch to point at, but the master plan's underlying concern (ENLIE-specific org data silently becoming the product default) is real here.

### F-4 (finding, classification C) — warehouse/item-group foundation mirrors ENLIE's real 2-warehouse-keeper structure

`setup_stock_warehouse_foundation()` seeds, for **every company** on the site:
```python
_STOCK_ITEM_GROUPS = ["NGUYÊN LIỆU","BAO BÌ","THÀNH PHẨM","BÁN THÀNH PHẨM","VẬT TƯ","HÓA CHẤT","VĂN PHÒNG PHẨM"]
_ITEM_GROUP_DEFAULT_WAREHOUSE = {"NGUYÊN LIỆU":"Nguyên liệu","BAO BÌ":"Bao bì","THÀNH PHẨM":"Thành phẩm",
                                  "VẬT TƯ":"Vật tư","HÓA CHẤT":"Hoá chất","VĂN PHÒNG PHẨM":"Văn phòng phẩm"}
```
The surrounding comment (dated 2026-09-24) states this was *"promoted from `_seed.py` (a test script hardcoding 'Công ty A') into real install logic for every site"*, and describes it as matching *"đúng cơ cấu thủ kho thật công ty xác nhận 24/09/2026: 2 thủ kho..."* (the real warehouse-keeper split confirmed directly with the actual ENLIE team). Same pattern as F-3: generic mechanism, ENLIE-specific values, applied unconditionally.

### F-5 (finding, classification C, minor) — one maintenance-periodicity list sourced from ENLIE's SOPs
`_MAINTENANCE_PERIODICITIES` (3/12/24/48/96 months + 50/200/600 operating hours) is explicitly commented as *"chu kỳ CÓ THẬT trong SOP của Enlie: EDS 019... EDS 027"*. Lower-impact than F-3/F-4 (maintenance intervals are plausible generic GMP defaults too), but same pattern — worth knowing the source is ENLIE's SOP numbering, not an industry standard.

### For contrast — seed data confirmed generic/reusable (classification A/B), no action needed
- `_SEVERITY_LEVELS` (Minor/Major/Critical), `_SUPPLIER_CLASSIFICATIONS` (Approved/Monitoring/Rejected), `_UTILITY_TYPES` (HVAC/Purified Water/Compressed Air/…), `_ANALYTICAL_VALIDATION_CHARACTERISTICS` (Specificity/Accuracy/Repeatability/…), `_QUALIFICATION_SPECIFICATION_TYPES` (URS/DQ/FAT/SAT/IQ/OQ/PQ), `_VALIDATION_CATEGORIES` — all standard GMP/pharma vocabulary, safe to reuse as-is for CE-15/CE-09/CE-08 across any pharma-like industry pack.
- `_STORAGE_CONDITIONS` (3 tiers) cites Vietnamese circular **TT 36/2018/TT-BYT** — a real regulatory standard, not ENLIE-specific, but market-specific (Vietnam GSP) — worth tagging as `region: VN` in the eventual Industry Pack config rather than a universal default.
- `_RD_ITEM_GROUPS` ("Nguyên liệu RD", "Tá dược RD", "Hoá chất dung môi", "Chất chuẩn", "Thuốc mẫu") — generic pharma R&D item taxonomy, reusable for CE-15.
- `VN Naming Rule`, `VN Automation Setting/Log` — generic, data-driven config infrastructure, not ENLIE-specific.

### Net effect for Demo Factory (DP-400) design
Per master plan §6 ("Không được xuất hiện logic kiểu `if company == 'ENLIE'`... nếu behavior thực sự cần khác nhau, dùng feature flag/edition config"), F-3 and F-4 are exactly the pattern to fix **before** any DP-400 "create site" script reuses this `setup.py` as-is: it would silently stamp every new demo site (Pig Farm, Shrimp Farm, Cosmetics — anything) with ENLIE's pharma-specific department codes and warehouse-keeper split. When CE-01/CE-09 foundation-setup logic is eventually copied into `enterprise-platform` (per Decision 1, on demand), `_DEFAULT_DEPARTMENTS`/`_QAS024_ONLY_DEPARTMENTS`/`_ACCOUNTING_DEPARTMENT` and `_STOCK_ITEM_GROUPS`/`_ITEM_GROUP_DEFAULT_WAREHOUSE` must become **Industry Pack template data** (configurable per edition), not unconditional install-time seeding.

Patches (`pharmacountry/patches/ppa/*.py`) reviewed — pure schema-migration cleanup (moving 77 legacy fields into a child table), no additional master-data findings beyond confirming the same 11-department ordering as F-3.

---

## 6. DP-106 — REUSABLE / NON-REUSABLE CLASSIFICATION (first cut)

Full per-DocType classification (258 DocTypes × A/B/C/D/E) was **not** completed in this pass — that is a multi-session effort requiring each DocType's fields/controller to be read individually. What follows is a domain-level first cut to unblock later phases; treat every row as a hypothesis to confirm, not a final verdict.

| Group | Preliminary class | Rationale |
|---|---|---|
| CE-01 custom overlays (`custom/*.json` on standard doctypes) | **A** (reusable core) | Property setters/custom fields on `Item`, `BOM`, `Sales/Purchase` docs — generic ERP extensions, no company literals spotted |
| QC Lab (`qc_*`) | **B** (reusable industry capability → CE-08) | Pharma/nutra/cosmetics/vet all need lab QC; no ENLIE-specific naming found |
| Equipment/Facility/Validation (`equipment_*`, `facility_*`, `process_validation_*`) | **B** (→ CE-09) | Generic GMP facility/equipment lifecycle |
| QMS (`change_control`, `cr_*`, `product_recall*`, `self_inspection*`) | **B** (→ CE-06) | Standard QMS constructs |
| DMS/Training (`document_*`, `controlled_*`, `gmp_training_*`) | **B** (→ CE-07) | Generic document-control lifecycle |
| HR Performance/Competency (~30 doctypes) | **B, pending CE assignment** (see F-1) | Reusable but needs a home in the CE taxonomy |
| R&D / RA (`rd_*`, `rdop_*`, `ra_*`) | **B, pending CE assignment** (see F-2) | Reusable across regulated-manufacturing packs |
| `accounting_readiness.py` self-audit tool | **A** | Company-parameterized, generic, arguably promotable to a platform-wide health-check utility |
| Root-level `_e2e*.py` / `_seed.py` / `_smoke_reports.py` scratch scripts | **E** (technical debt) | Ad hoc, outside module/tests structure, uses placeholder company but not integrated into any test runner shown so far |
| `vnpharma/vnpharma` (legacy app copy) | **E / retire** | Superseded by `vnpharma-develop/pharmacountry`, 3 days stale, different branch |
| Everything else (~150 remaining DocTypes not yet individually reviewed) | **Unclassified** | Needs DP-106 continuation |

No DocType was found in this pass that looks like **D (ENLIE-only customization that should NOT enter product core)** — but absence of evidence is not evidence of absence given the scan depth; this needs a real second pass reading fixture/default data, not just controller code.

---

## 7. DP-107 — MIGRATION PLAN

### Decision log (resolved 2026-09-28, by project owner)

**Decision 1 — how does ENLIE code enter `enterprise-platform`? RESOLVED: option (c).**
`enterprise-platform` is a **fresh build**, not a fork/import of ENLIE. ENLIE (`D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry`) stays a **read-only reference**. No submodule, no wholesale copy. When a specific piece of ENLIE logic is needed for a specific demo/capability engine, it gets **copied and generalized on demand** (company/warehouse/department hard-codes removed, naming genericized) — never pulled in wholesale ahead of need. This means DP-106's per-DocType classification is not a blocking prerequisite for starting Phase 1/2 work; it becomes a **lookup reference** consulted each time a capability engine needs a specific DocType, rather than a big upfront migration.

**Decision 2 — HR Performance/Competency and R&D/RA taxonomy gap (F-1, F-2). RESOLVED: both split into new standalone capability engines**, added to the master plan (`00_demo_platform_master_plan.md` §3):
- **CE-14 — HR Performance & Competency Management** (~30 DocTypes: Competency, Job Scorecard, Performance Cycle/Review, Development Plan, PIP, etc.)
- **CE-15 — R&D & Regulatory Affairs (RA)** (~15 DocTypes: RD Formulation Trial, RD Manufacturing Process, RA Registration Dossier/Tracking, Label Design chain, etc.)

Rationale (why not fold into CE-01/CE-06): a standalone CE can be enabled/disabled per edition independently — folding into CE-01 (ERP Core) would force every demo to carry HR-performance overhead even when not needed; folding R&D/RA into CE-06 (QMS) would blur the line between in-progress formulation work and approved, submitted-for-manufacturing batch records. Master plan updated accordingly (13 → 15 capability engines).

**Decision 3 — legacy `vnpharma/vnpharma` app. RESOLVED: skip, no action.** It's reference-only; not worth spending effort to formally archive/retire. Leave it alone under `D:\ME\ERP_ENLIE\`; `enterprise-platform` tooling should simply never treat it as a source.

### What this unblocks

DP-107 is no longer blocked. Practical effect on later phases:
- **Phase 1 (Demo Infrastructure) and Phase 2 (Platform Config Layer)** can start without waiting on full DP-106 classification, since `enterprise-platform` isn't importing ENLIE code wholesale anyway.
- **DP-106 (per-DocType classification)** downgrades from "blocking prerequisite" to "reference work done incrementally, per capability engine, at the point a demo/pack actually needs to reuse a specific ENLIE DocType." Still worth finishing at group level (see next steps) so later phases know where to look.
- CE-14 and CE-15 now need their own entries wherever CE-01..CE-13 are enumerated going forward (industry pack definitions in §4, task breakdown in §21) — not retrofitted in this pass; do when those packs are actually scoped.

### Remaining next steps (proposed, not yet executed)
1. DP-105 continuation: read `pharmacountry/setup.py` + `patches/` for seeded master data (still useful to know what's ENLIE-specific *data*, separate from code).
2. DP-106 continuation, lower priority now: classify the ~150 unreviewed DocTypes at group level, so that when Phase 3+ needs to "copy and generalize" something, there's a lookup table instead of re-reading ENLIE from scratch each time.
3. When Phase 2/3 actually starts building a capability engine (e.g. CE-06 QMS for Demo 01 Pharma), pull the specific ENLIE DocTypes needed for *that* engine, generalize them, and land them under `enterprise-platform/pharmacountry/` (or whatever the fresh app is named) — this is where "copy and reuse if needed" actually happens, not upfront.

---

## Appendix — raw counts for reproducibility

```
Doctypes:        258
Reports:         78
Print formats:   71
Workspaces:      20
Dashboard charts: 5
Number cards:    13
Custom field/property-setter overlays on standard doctypes: 45
Python files in app: 834
Workflows (via fixtures): 24
Scripted permission hooks: 14 doctypes
Scheduled jobs: 6 daily, 1 hourly
```
Regenerate via `Glob`/`Grep` against `D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\` — do not hand-maintain these counts as the app evolves.
