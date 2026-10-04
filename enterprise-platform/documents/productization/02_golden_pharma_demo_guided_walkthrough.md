# DP-512 — Golden Pharma Demo: Guided Walkthrough

Maps master plan §7 DEMO 01's 8-step "Hướng dẫn demo người dùng" onto the real records this
session's seed functions actually created, on both `test.demo.local` and public
`pharmacountry.vn` (Company **Demo Pharma Co** / DPC). Record names below are from
`pharmacountry.vn`; `test.demo.local` has the same data under different auto-numbered
document names.

**Update (DP-405, 2026-09-28):** 11 demo user accounts now exist (`<role>@pharmacountry.vn`,
password `Demo@1234`), each with a real native Frappe Role and deliberately no System Manager —
see project_status.md's Phase 3.5/DP-405 entry for the full mapping and its one known
limitation (ERPNext's Quality module doesn't distinguish Director/Manager/Analyst seniority).
Role *assignment* and login (password authentication) were verified directly; actually walking
through each step below AS each specific user has not yet been re-tested end-to-end — one real
finding from checking document permissions directly: `Quality Manager` (used by
qa.manager/qc.manager) can create/submit **Quality Inspection** but NOT **Stock Entry** — so
step 7 (QA release) genuinely needs two people in sequence: `qa.manager` approves the QC record,
then `warehouse.officer` or `production.manager` (both have Stock Entry submit rights) actually
executes the Quarantine→Released transfer. This matches real GMP segregation-of-duties intent
(master plan's non-negotiable "QA release" segregation rule) rather than being a bug to fix.

## Walkthrough

### 1–2. Planning — Production Plan / material shortage
**Not built.** Master plan's step 1–2 (Sales Forecast → Production Plan → Material Requirement)
is upstream of where this session's scope (DP-501 onward) started; the demo currently begins
from a pre-decided Purchase Order rather than a generated one. Skip these two steps for now, or
narrate them as "already done" before the tour starts.

### 3. Procurement — RFQ/PO
Open **Purchase Order `PUR-ORD-2026-00011`** — Supplier "ABC Pharma Chemicals Co.", 6 line
items (4 raw materials + 2 packaging), submitted.

### 4. Warehouse — receive batch
Open **Purchase Receipt `MAT-PRE-2026-00001`** — all 6 items received into **RM Quarantine -
DPC**, batch-tracked items (PARA-API/MCC/PVP-K30/MG-STEARATE) each got a fresh Batch with
2028-09-27 expiry.

*Live proof point (P01):* try creating a Stock Entry that issues any item straight from RM
Quarantine to Manufacture — it's blocked with "Cannot issue item ... from Quarantine warehouse
... Material must be QC-approved and moved to an Approved warehouse first."

### 5. QC — sampling, result, approve
Two things to show:
- **Quality Inspection** list, filtered `inspection_type = Incoming` — 4 Accepted records, one
  per raw material, each linked to the Purchase Receipt and its specific batch.
- The Material Transfer that actually moved stock **RM Quarantine → RM Approved** for all 6
  items (search Stock Entry, purpose "Material Transfer", target warehouse "RM Approved - DPC").

### 6. Production — Work Order, material issue, process
Open **Work Order `MFG-WO-2026-00002`** — production item PARA-500-TAB, qty 1000, status
Completed, BOM sourced from RM Approved. Open its linked Manufacture **Stock Entry** to show
consumption (raw materials in small kg amounts, packaging at 1000 units each — see project_status.md's
DP-504 write-up for why those look different but are both correct) and the finished-goods batch
landing in **FG Quarantine - DPC**.

Also show the **Non Conformance `QA-NC-00001`** ("Minor temperature excursion during IPC
sampling") — a deviation raised during this batch, investigated and resolved, referencing the
**Quality Procedure** "SOP - Paracetamol 500 mg Tablet Manufacturing".

### 7. QA — review record, release batch
Login as `qa.manager@pharmacountry.vn` to open the **Quality Inspection** list filtered
`inspection_type = In Process` — the Accepted in-process QC for the PARA-500-TAB batch. Then
switch to `warehouse.officer@pharmacountry.vn` (or `production.manager@pharmacountry.vn`) —
neither Quality Manager nor Stock User alone can do both halves — to show the Stock Entry that
actually moved it **FG Quarantine → FG Released**. This two-step handoff mirrors the master
plan's segregation-of-duties requirement, not a permission gap.

*Live proof point (P06):* as `warehouse.officer`, try releasing a batch to FG Released without
an Accepted Quality Inspection for it — blocked with "No Accepted Quality Inspection found for
this batch — QA release requires QC approval first."

### 8. Director — dashboard KPI
Login as `general.director@pharmacountry.vn` (Analytics role) to open the **"Pharma Golden
Demo"** Dashboard — 3 Number Cards (Accepted Quality Inspections, Resolved Deviations, Purchase
Orders for this Supplier) plus a Quality Inspection count chart.

### Bonus — EAM
Not in the master plan's 8-step script, but worth showing if there's time: **Asset**
"Tablet Compression Machine #1" (submitted, Plants and Machineries account) with its **Asset
Maintenance** schedule (monthly calibration task, assigned to `maintenance@pharmacountry.vn`).

## Acceptance criteria — status against master plan §7 DEMO 01

| Criterion | Status |
|---|---|
| End-to-end hoàn tất không cần System Manager | **Partial** — 11 demo accounts exist, none has System Manager (verified directly); the walkthrough above has not yet been re-run live end-to-end logged in as each specific user |
| Permission đúng role | **Partial** — role *assignment* verified (each user has the intended native Frappe Role, e.g. `qa.manager` → Quality Manager); step-by-step document permissions spot-checked (Stock Entry vs Quality Inspection — see the DP-405 update above), but not every step in this walkthrough has been executed live as its assigned user |
| Audit trail đủ | **Yes** — every document above is a real submitted transaction with owner/timestamp, not synthetic data |
| Print/PDF của batch summary sử dụng được | **Not verified** — ERPNext's standard print formats exist for these doctypes but haven't been checked for this specific batch |

## What DP-512 deliberately does not cover

Sales Order/Delivery (right side of the master plan's workflow diagram) is out of scope for this
pass — this document covers exactly DP-501 through DP-510 plus the DP-405 demo-user layer, the
pieces actually built and verified via `verify_pharma_golden_demo()` (DP-511). A live, logged-in
walkthrough as each of the 11 demo users (rather than permission spot-checks) is the next honest
gap to close here.
