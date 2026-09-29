# Process Guide — Cosmetics Batch Stability & Complaint Traceability (End to End)

## Purpose

This is the full lifecycle of one cosmetics product batch — from formula through manufacturing, release, distribution, ongoing stability monitoring, an in-process rework, and finally a customer complaint traced back to it. It's a second, differently-flavored example of the same manufacturing-quality discipline shown in the Pharmaceutical Batch Release process, proving the platform's approach isn't specific to one industry.

## Prerequisites

- No dedicated per-role Cosmetics demo logins exist yet — this walkthrough is typically run as Administrator. See the [Administrator Guide](../administrator-guide.md) for how to add them.
- Understand the two-stage production model: a **Bulk** batch (the mixed formula, tracked in kilograms) is manufactured, tested, and released first; it is then consumed as an ingredient to produce a **Packed** batch (the retail bottle, tracked in units), which is separately tested and released before it can be sold.

## Roles involved

| Role | Responsibility |
|---|---|
| Production | Manufactures the bulk formula, then the packed product; executes reworks when needed. |
| QC | Tests each batch (bulk and packed) before it can be released. |
| **QA Manager** | Owns the post-release stability program, rework sign-off, and complaint handling/escalation. |

## The process, step by step

### 1. The bulk formula is manufactured, tested, and released

A Work Order produces a batch of the bulk formula ("Facial Cleanser - Bulk") from its raw ingredients (water, glycerin, a mild surfactant, a preservative, fragrance, and a small amount of citric acid for pH balance). The resulting batch is tested by QC and, once Accepted, transferred into the Bulk Released warehouse — the same release-gating rule used in the Pharmaceutical flow applies here too: a batch cannot move into a warehouse whose name contains "Released" without an Accepted Quality Inspection for that exact batch.

### 2. The bulk batch is packed into the retail product

Released bulk formula, along with bottles, pump caps, and labels, is staged into the Packing Store and consumed by a second Work Order that produces the retail packed batch ("Facial Cleanser 150ml Bottle"). This packed batch is tested and released the same way — the release-blocking rule fires here for a second time, on a completely different warehouse, with no special-case code needed to support it.

Crucially, the system remembers *which specific bulk batch* went into *which specific packed batch* — not just "some bulk formula," but the traceable batch number. This genealogy is what makes the complaint traceability later in this process possible.

### 3. A formula revision happens — and doesn't rewrite history

At some point, the bulk formula recipe is revised slightly (a small adjustment to fragrance and water ratio). The system creates this as a *new version* of the formula and marks the old one inactive, but the batch that was already produced under the old formula keeps its original recorded ingredients unchanged — a formula revision never silently alters what a historical batch actually contained.

### 4. The packed batch goes out to a customer

The packed batch is sold and delivered to a retail customer. The delivery record captures exactly which batch number was shipped.

### 5. The stability-testing program runs — and one check falls overdue

Separately, the packed batch enters a stability-testing schedule: multiple time points (immediate, 1 month, 3 months, 12 months) under two storage conditions (room temperature and an accelerated/hot condition), simulating how the product ages on a shelf. Most scheduled checks have been completed and passed. One of the 3-month checks, however, was scheduled in the past and never actually tested — the system marks it **Overdue** automatically, because its status is always computed from the scheduled date and whether a test result has been entered, never set by hand.

### 6. A minor in-process issue is caught and reworked

Separately from the stability program, a QC recheck of the bulk batch's remaining stock finds a minor pH deviation. Rather than discarding the material, production performs a documented rework: the remaining bulk stock plus a small corrective addition of citric acid is reprocessed into a *new* bulk batch, re-tested by QC, and released again. A **Cosmetics Rework Record** documents the reason and outcome. Even though this creates a new batch number, the system's batch-genealogy tools can still trace the new batch back through the rework to the original one — the correction is fully auditable, not a fresh start that loses history.

### 7. A customer complaint arrives — and is traced to its exact batch

A customer reports an unusual fragrance change after using the product for about two months. QA records this as a **Cosmetics Complaint**, linked to the customer and marked "Investigating." Using the real delivery record from step 4, the complaint is traced back to the *precise* batch number that customer received — not an assumption based on typical shipping patterns, but the actual recorded batch.

### 8. QA decides: close, or escalate

This is the process's decision point. QA Manager reviews the complaint (and, if relevant, the stability and rework history for that product line) and decides whether it's an isolated, low-risk incident to close out, or whether it points to something systemic that warrants a formal Corrective and Preventive Action (CAPA). The platform's standalone Quality Management module is where a formal CAPA would be raised for a decision like this — see the [AI QMS Copilot scenario](../ai-qms-copilot-capa-approval/process-guide.md) for a full, real example of exactly that kind of escalation, including an AI-assisted draft that still requires an explicit human approval before it becomes an official CAPA.

## Reports

- **Cosmetics Stability Sample**, filtered by `status = Overdue`, to catch anything falling behind schedule.
- **Cosmetics Rework Record** list, to review documented corrections over time.
- **Cosmetics Complaint** list, filtered by `status`, for open vs. closed customer issues.
- Batch genealogy tracing (bulk → packed, and original → reworked) for root-cause investigation.

## Common errors across the process

| Message / situation | Root cause |
|---|---|
| A release transfer is blocked with "No Accepted Quality Inspection found for this batch..." | Same rule as the Pharmaceutical flow — a batch (bulk or packed) can't move into a "Released" warehouse without a passing quality result for that exact batch. |
| A stability sample shows Overdue | A real, current gap in the testing schedule — action needed, not a data error. |
| A rework's new batch doesn't show the expected genealogy | Check that the rework was recorded as consuming the *original* batch specifically (not just the item in general) — the traceability depends on the batch number being carried through, which the system does automatically when the rework is entered correctly. |

## FAQ

**Why does the same release-blocking rule apply to a completely different industry's warehouses?** Because the rule isn't hardcoded to pharmaceutical warehouse names — it fires on any warehouse whose name contains "Released," so the exact same protection extends to a new product line with zero additional configuration.

**Does a formula revision affect batches already in the field?** No — a formula version change only affects future production. Batches already manufactured keep their own recorded ingredient list exactly as it was at the time, permanently.

**Is the complaint's batch traceability guessed or exact?** Exact — it's derived from the real delivery record for that customer's actual order, not inferred from typical inventory turnover.
