# Quick Start — Cosmetics Batch Stability & Complaint Traceability

**Time needed:** 5–10 minutes
**What you'll see:** how a cosmetics manufacturer keeps watching a product batch *after* it's released — scheduled stability testing over time, a documented in-process rework, and a real customer complaint traced back to the exact batch that customer actually received.

## Purpose

Releasing a batch isn't the end of quality management for a consumer product — it's ongoing. This quick start shows you the post-release side of the quality system, using one real batch of Facial Cleanser (150ml bottle) as the example.

## Prerequisites

- A working login. **Note:** unlike the Pharmaceutical Batch Release scenario, there is not yet a dedicated Cosmetics demo login for each role (QA, Production, etc.) — for now, this scenario is viewed by an Administrator account. See the [Administrator Guide](../administrator-guide.md) for how a platform admin can add dedicated logins the same way it was done for the Pharma scenario.
- No special setup beyond being logged in to the demo site.

## The fastest path

1. Open the **Batch** record for **Facial Cleanser 150ml** — the packed, released retail product.
2. Open its **Cosmetics Stability Sample** records. This batch is on a stability-testing schedule that checks it at multiple points in time (immediately, at 1 month, at 3 months, at 12 months), under two storage conditions (room temperature and an accelerated/hot condition). One of the 3-month checks is genuinely **Overdue** — it was scheduled in the past and nobody has recorded a test result for it yet. That's real, current data, not a staged example.
3. Open the **Cosmetics Rework Record** for this product line. A minor pH deviation was caught on a QC recheck of an earlier production run, corrected with a small ingredient addition, and re-tested as Accepted — the system keeps this as part of the batch's permanent history rather than letting it disappear.
4. Open the **Cosmetics Complaint** record. A customer reported an unusual fragrance change after using the product for two months — and the complaint is traced, through real delivery records, back to the *exact* batch that customer received.
5. Consider the decision point every QA reviewer faces here: is this complaint something to close out, or does it need to escalate into a formal Corrective and Preventive Action (CAPA)? See the [Role Guide](role-guide-qa-manager.md) for how that decision gets made, and the [AI QMS Copilot scenario](../ai-qms-copilot-capa-approval/quick-start.md) to see a real CAPA get raised and approved from a similar deviation.

## Where to go next

- **[Role Guide — QA Manager](role-guide-qa-manager.md)** — the day-to-day responsibilities of the QA role in this workflow.
- **[Process Guide](process-guide.md)** — the full production-to-complaint story, including how the batch was made in the first place.

## Common errors / things that look like errors but aren't

| What you see | What it means |
|---|---|
| A stability sample shows status "Overdue" | This is expected, real data — a scheduled check that hasn't happened yet. It's not a bug; it's the point of the demo — the system surfaces this instead of letting it go unnoticed. |
| No dedicated "QA Manager (Cosmetics)" login exists | A genuine, disclosed gap — this vertical hasn't had role-specific demo accounts built yet (unlike Pharma's five). Run this scenario as Administrator for now. |

## FAQ

**Is the stability sample status set manually?** No — it's always computed by the system from the scheduled date and whether a test date has been recorded (Tested if a test date exists, Overdue if the scheduled date has already passed with no test, otherwise Scheduled). Nobody can accidentally (or deliberately) mark something "not overdue" that actually is.

**Does the rework record affect the original batch's history?** No — a rework produces a *new* batch (with a corrected formula step) while the system still remembers exactly which original batch it came from. Nothing about the original batch's record is rewritten or lost.

**How does a complaint get traced to "the exact batch"?** Through the real delivery record for that customer's order — the same batch number that was actually picked and shipped to them is the one the complaint links to. It isn't a guess based on which batch was probably in stock at the time.
