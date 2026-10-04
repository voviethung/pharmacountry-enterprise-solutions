# Role Guide — QA Manager (Cosmetics)

## Purpose

As QA Manager for a cosmetics product line, your job doesn't end when a batch is released — you're responsible for watching it afterward: keeping the stability-testing program on schedule, documenting any in-process correction (rework), and making sure any customer complaint is traced back to real data and handled appropriately.

## Prerequisites

- **Disclosed gap:** there is not yet a dedicated `qa.manager` login for the Cosmetics vertical (unlike Pharmaceutical manufacturing, which has five distinct demo accounts). Until one is provisioned, this role is exercised via an Administrator login. An administrator can add one following the same pattern used for the Pharma demo users — see the [Administrator Guide](../administrator-guide.md).
- Familiarity with the idea of a Batch (one produced lot of one product) and that a cosmetics product here is made in two stages: a **Bulk** batch (the formula, e.g. "Facial Cleanser - Bulk") that is itself quality-tested and released, and then a **Packed** batch (the bulk formula filled into retail bottles, e.g. "Facial Cleanser 150ml Bottle") that is tested and released again before it reaches customers.

## Roles

| Role | Responsibility |
|---|---|
| **QA Manager (you)** | Owns the post-release quality program: stability schedule, rework documentation, complaint handling/escalation decisions. |
| Production / QC (same "no dedicated login yet" caveat applies) | Executes the bulk and packed manufacturing + release steps that produce the batches you're monitoring. |

## How to create

You are usually reviewing records that the system or production staff already created, but two things genuinely originate with QA:

- **Escalation decisions.** When a complaint or an overdue stability check needs to become a formal corrective action, you decide to escalate it. Today, formal CAPA creation for this platform lives in the standalone Quality Management module (see the [AI QMS Copilot scenario](../ai-qms-copilot-capa-approval/process-guide.md) for a full worked example of a deviation becoming an AI-assisted, human-approved CAPA).
- **Rework sign-off.** A rework record documents *why* a batch needed correcting, what was done, and that it was re-tested and accepted — this is written up as part of your quality oversight even though the physical rework itself is executed by production.

## How to review

- **Cosmetics Stability Sample** list — this is your main recurring check. Each row shows the batch, the storage condition (Room Temperature / Accelerated), the time point (in months), the scheduled date, and whether it's been tested. Watch specifically for **Overdue** rows — a schedule item that passed its date with no test recorded.
- **Cosmetics Rework Record** — review the stated reason and outcome (e.g. a pH deviation caught on recheck, corrected, and re-tested Accepted) to confirm the correction was properly closed out, not just noted.
- **Cosmetics Complaint** — review the customer's description and the batch it's been traced to. Confirm the traceability (the batch number) actually corresponds to a real delivery to that customer, not an assumption.

## How to approve

There isn't a single "approve" button for a stability result — approval here means: reviewing the test result recorded against a scheduled stability check, and reviewing/accepting a rework's re-test result before treating the reworked batch as equivalent in quality to a normally-produced one.

## How to amend

If a stability sample's scheduled date or condition was set up incorrectly, correct the record directly before it has a recorded test result. Once a test date and result are recorded, treat that entry as historical — if a correction is needed after the fact, add a clarifying note rather than silently rewriting a completed test record, to preserve the audit trail.

## How to cancel

Complaints and rework records are typically not "cancelled" outright — a complaint that turns out to be unfounded is closed with that explanation documented, not deleted, so the traceability chain (which batch, which customer, what was reported) remains intact for future reference.

## Reports

- **Cosmetics Stability Sample** list, filtered by `status = Overdue`, is your most useful recurring report — it tells you exactly what's fallen behind schedule.
- **Cosmetics Complaint** list, filtered by `status`, to track open vs. closed customer issues.
- For full production genealogy (which raw batch went into which bulk batch went into which packed batch), the platform's batch traceability tools can trace a packed batch all the way back to the specific bulk batch consumed — useful when a complaint or stability failure needs root-cause investigation.

## Common errors

| Situation | What it means |
|---|---|
| A stability sample shows "Overdue" | A real, current signal — this exact time point/condition combination was due and hasn't been tested. Not a data-entry mistake; treat it as an action item. |
| A rework record exists for a batch you didn't expect | Check the reason field — reworks happen when a QC recheck (not the original release test) finds something like a minor formula deviation, and it's corrected before the batch is fully consumed or shipped. |
| A complaint references a batch number you don't recognize | Look up that Batch directly — the complaint's traceability is derived from the actual delivery record, so the batch number shown is accurate even if the number itself isn't one you have memorized. |

## FAQ

**Can a stability sample's status be changed by hand to hide an overdue check?** No — status is computed automatically from the scheduled date and whether a test date has been entered. There's no field to directly set "Overdue" to "Scheduled" without either entering a real test result or changing the underlying scheduled date itself (which would itself be an auditable change).

**What's the difference between a rework and a full re-manufacture?** A rework consumes the *existing* batch (or its remainder) plus a small corrective addition and produces a new batch version — it is not a fresh production run from raw materials, and the system's traceability tools can still show the new batch's genealogy running back through the original one, not just a note saying "this was reworked."

**When should a complaint become a CAPA instead of just being closed?** That's a judgment call for you as QA Manager, generally driven by severity, whether it points to a systemic issue (versus an isolated incident), and regulatory/customer-facing risk. See the AI QMS Copilot scenario for how a similar decision plays out with an AI-assisted CAPA draft that still requires your explicit human approval before it becomes official.
