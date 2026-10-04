# Process Guide — Pharmaceutical Batch Release (End to End)

## Purpose

This is the full, end-to-end story of one pharmaceutical batch — Paracetamol 500mg Tablets (item PARA-500-TAB) — from the moment its raw materials arrive at the warehouse to the moment the finished batch is authorized for sale. It cuts across five roles and two hard system-enforced quality gates. Read this when you need to understand (or explain to someone else) the *whole* process, not just one person's slice of it.

## Prerequisites

- The five demo logins described in the [Quick Start](quick-start.md), all password `Demo@1234`.
- Familiarity with the idea of a "batch" and a "warehouse" as used in manufacturing — each raw material and each finished product lot is tracked as its own numbered Batch, and every Batch physically sits in exactly one Warehouse at a time (Quarantine, Approved, or Released, depending on where it is in its lifecycle).

## Roles involved

| Role | Login | Responsibility in this process |
|---|---|---|
| Warehouse Officer | `warehouse.officer@pharmacountry.vn` | Receives raw material, executes physical stock transfers. |
| QC Analyst | `analyst@pharmacountry.vn` | Performs incoming and in-process quality testing. |
| QC Manager | `qc.manager@pharmacountry.vn` | Reviews QC results, authorizes release from quarantine. |
| Production Manager | `production.manager@pharmacountry.vn` | Runs the manufacturing Work Order. |
| QA Manager | `qa.manager@pharmacountry.vn` | Gives final authorization to release the finished batch for sale. |

## The process, step by step

### 1. Procurement (already done before this walkthrough starts)

A Purchase Order was placed with supplier **"ABC Pharma Chemicals Co."** for six raw and packaging items needed to make PARA-500-TAB. This part of the process (demand planning, RFQ, purchase ordering) is upstream of where this walkthrough begins — treat it as already complete.

### 2. Warehouse receives the raw material

**Login as Warehouse Officer.** Open the **Purchase Receipt** against that Purchase Order. All six items — including the active ingredient (PARA-API) and key excipients — are received into the **RM Quarantine** warehouse, each batch-tracked item getting its own **Batch** record with an expiry date.

Nothing received this way is usable yet. This is the first quality gate: material sits in quarantine by default, and the system will not let it be issued for production from there.

*What the system enforces here:* if anyone tries to create a Stock Entry issuing an item straight from a warehouse whose name contains "Quarantine" for a manufacturing purpose, it is blocked immediately with:

> "Cannot issue item {item} from Quarantine warehouse {warehouse} for production. Material must be QC-approved and moved to an Approved warehouse first."

### 3. QC tests the material

**Login as QC Analyst.** Open the **Quality Inspection** list filtered to `Inspection Type = Incoming`. Each raw material has its own Accepted incoming inspection, linked to the exact Purchase Receipt and Batch it came from. The analyst records the test result here — this is the origin of the "QC-approved" status the earlier block message refers to.

### 4. QC Manager authorizes the release from quarantine

**Login as QC Manager.** Review the Accepted Quality Inspection, then confirm (or, if you have Stock Entry rights, execute) the **Material Transfer** Stock Entry that moves the accepted material from **RM Quarantine** to **RM Approved**. This is the one action that actually satisfies the earlier block — production can only draw material from the Approved warehouse.

> Note: the native Quality Manager permission set can submit a Quality Inspection but not a Stock Entry — so in practice, the Warehouse Officer or Production Manager is often the one who executes this transfer once QC Manager has confirmed the result. See the [QC Manager Role Guide](role-guide-qc-manager.md) for the full explanation.

### 5. Production manufactures the batch

**Login as Production Manager.** Open the **Work Order** for PARA-500-TAB, quantity 1,000 tablets. Its Bill of Materials sources every ingredient exclusively from the RM Approved warehouse — there is no configuration path that lets it draw from Quarantine. Running the manufacture step consumes the approved raw materials and produces a new finished-goods **Batch**, which lands in the **FG Quarantine** warehouse — the finished product starts in quarantine too, exactly like the raw material did.

Any in-process deviation observed during manufacturing (for example, a minor temperature excursion during sampling) is recorded as a **Non Conformance**, investigated, and resolved before the batch proceeds — the platform tracks this as part of the batch's full quality history, not as a separate, disconnected complaint.

### 6. QA reviews and authorizes final release

**Login as QA Manager.** Open the **Quality Inspection** for the finished batch (an in-process or final inspection), confirm it is Accepted, then authorize the **Material Transfer** that moves the batch from **FG Quarantine** to **FG Released**.

*What the system enforces here — the second hard gate:* if anyone tries to move a batch into a warehouse whose name contains "Released" without an Accepted Quality Inspection for that exact item and batch, it is blocked with:

> "Cannot move batch {batch} of item {item} into Released warehouse {warehouse}. No Accepted Quality Inspection found for this batch — QA release requires QC approval first."

Once this transfer is submitted, the batch is in the Released warehouse — the point at which it becomes available to sell.

### 7. Director-level visibility (optional)

Someone with the Analytics role (the demo's `general.director@pharmacountry.vn` account) can open the **"Pharma Golden Demo" Dashboard** to see this batch's activity reflected in real numbers: a count of Accepted Quality Inspections, resolved deviations, and purchase order volume against this supplier, alongside a Quality Inspection trend chart. This is where a plant director would check that the process is running healthily without reading every individual record.

## Reports

- **Quality Inspection** list (filter by `inspection_type`, `status`, `item_code`, `batch_no`).
- **Stock Entry** list (filter by `purpose = Material Transfer` and warehouse name) to see every quarantine-to-approved or quarantine-to-released movement.
- **Work Order** list for production status and completion.
- **"Pharma Golden Demo" Dashboard** for the aggregate, director-level view.

## Common errors across the process

| Message | Where it happens | Root cause |
|---|---|---|
| "Cannot issue item ... from Quarantine warehouse ... for production." | Attempting to issue raw material to manufacturing before QC approval. | The Quarantine → Approved transfer hasn't happened yet. |
| "No Accepted Quality Inspection found for this batch — QA release requires QC approval first." | Attempting to release finished goods without a passing quality result. | The batch's final Quality Inspection isn't Accepted yet, or hasn't been entered. |

Both messages are the system doing exactly what it's supposed to — they mean the process is being followed correctly, not that something is broken.

## FAQ

**Can this whole process be done by one person?** No, by design. Five different accounts are involved because segregation of duties (the person testing quality isn't the person authorizing release, isn't the person running production) is a genuine regulatory expectation in pharmaceutical manufacturing, and the platform enforces it with real, separate logins and real, separate permissions — not just written procedure.

**What's upstream and downstream of this process?** Upstream: demand planning and purchasing (not covered by this walkthrough). Downstream: once a batch is in the Released warehouse, it becomes available for Sales Orders and delivery to customers — a separate process not covered here either.

**Where do I see the underlying asset/equipment side of this?** Worth a look if you have time: the **Asset** record for the tablet compression machine used in this process, with its own preventive maintenance schedule — a reminder that equipment calibration is part of the same quality chain, even though it isn't one of the batch-release gates itself.
