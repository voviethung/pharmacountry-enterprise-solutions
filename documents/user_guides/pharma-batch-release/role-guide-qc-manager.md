# Role Guide — QC Manager (Pharmaceutical Manufacturing)

## Purpose

As QC Manager, you are the gate between "material has been tested" and "material may be used." Nothing moves out of a Quarantine warehouse into production, and no finished batch reaches the Released warehouse, without a decision that traces back to your role. This guide covers what you do, day to day, using the Pharmaceutical Batch Release flow as the working example.

## Prerequisites

- Login: `qc.manager@pharmacountry.vn` (demo password `Demo@1234`).
- Native system role: **Quality Manager**.

> **A known platform limitation, disclosed honestly:** the underlying system's Quality module does not currently distinguish QC Analyst / QC Manager / QA Manager / Quality Director as separate permission levels — all four demo accounts share the same native **Quality Manager** role. In a real production deployment, an administrator would split these into distinct permission profiles (see the [Administrator Guide](../administrator-guide.md)) so that, for example, only a QC Manager (not a QC Analyst) can move a batch out of quarantine. Today, the roles are separated by *who is expected to act at each step* in the process, not yet by hard permission boundaries between QC Analyst and QC Manager specifically.

## Roles

| Role | What it does in this flow |
|---|---|
| QC Analyst | Performs the test, records the **Quality Inspection** result. |
| **QC Manager (you)** | Reviews the Accepted result and authorizes moving the material out of quarantine. |
| QA Manager | Gives final release authorization for the finished batch. |

## How to create

You don't originate the Quality Inspection yourself — the QC Analyst does that. Your first real action in the flow is reviewing and then creating the **Stock Entry** that physically executes the release:

1. Go to **Quality Inspection**, filter `Inspection Type = Incoming`, and confirm the result for the batch in question is **Accepted**.
2. Go to **Stock Entry**, create a new one with **Purpose = Material Transfer**.
3. Set the **Source Warehouse** to the item's Quarantine warehouse (e.g. "RM Quarantine") and the **Target Warehouse** to the matching Approved warehouse (e.g. "RM Approved"), select the exact batch, and submit.

> **A real permission nuance worth knowing:** the native **Quality Manager** role can create and submit a **Quality Inspection**, but it does **not** have permission to submit a **Stock Entry**. In practice this means the QC Manager reviews and authorizes the release, but a **Warehouse Officer** or **Production Manager** login is needed to actually execute the Stock Entry that moves the stock. This isn't a bug — it mirrors the real-world separation between "who approves quality" and "who moves physical inventory."

## How to review

- **Quality Inspection list**, filtered `Inspection Type = Incoming` (raw materials arriving) or `In Process` (in-process checks during manufacturing) — each row links back to its Purchase Receipt or Work Order and its exact Batch.
- Before authorizing any release, confirm: the inspection status is **Accepted**, the batch number matches, and the item code matches what you're about to move.

## How to approve

"Approval" here has two parts:
1. **Quality sign-off** — the Quality Inspection itself being marked Accepted is the quality decision. As QC Manager you review this before the physical release happens.
2. **Physical release** — the Stock Entry moving material from Quarantine to Approved (or, for QA, from FG Quarantine to FG Released) is what the system actually checks before allowing production or sale to proceed. See the permission nuance above — this half of the action may need a second login.

## How to amend

Frappe documents follow a standard submit/cancel/amend pattern: once a Quality Inspection or Stock Entry is submitted, you cannot edit it directly. If a genuine mistake was made (wrong batch selected, wrong result entered), the correct path is:
1. **Cancel** the submitted document (see below).
2. Use the **Amend** option that appears after cancellation — this creates a new editable draft that references the cancelled one, preserving a full audit trail rather than silently overwriting history.

## How to cancel

- You can cancel a Quality Inspection you created in error, provided nothing downstream has already relied on it (e.g. a release Stock Entry that required this exact Accepted result).
- **Before cancelling anything already tied to a release**, check whether a downstream Material Transfer or Work Order already used it — cancelling a Quality Inspection does not retroactively re-lock stock that has already moved. Flag any such situation to your QA Manager before cancelling.

## Reports

- **Quality Inspection** list report — filter by `status`, `inspection_type`, `item_code`, or `batch_no` to find exactly the record you need.
- The **"Pharma Golden Demo" Dashboard** (viewed by the Director role) shows a live count of Accepted Quality Inspections alongside resolved deviations and purchase order volume for a given supplier — useful context for spotting trends, even though you won't typically be the one opening it.

## Common errors

| Message | What it means | What to do |
|---|---|---|
| "Cannot issue item ... from Quarantine warehouse ... Material must be QC-approved and moved to an Approved warehouse first." | Someone tried to send quarantined material straight to production. | Confirm QC has actually tested and accepted the batch, then perform the Quarantine → Approved transfer first. |
| "No Accepted Quality Inspection found for this batch — QA release requires QC approval first." | Someone tried to release a finished batch to the sellable warehouse without an Accepted result for that exact batch. | Make sure the in-process or final Quality Inspection for that specific batch is Accepted before attempting the release transfer. |
| You can't submit the release Stock Entry yourself. | Your Quality Manager role doesn't include Stock Entry submission rights. | Ask a Warehouse Officer or Production Manager to execute the transfer once you've confirmed the quality result. |

## FAQ

**What happens if a batch fails QC?** The Quality Inspection is recorded as Rejected rather than Accepted. Because the release-blocking rule checks specifically for an *Accepted* result on that batch, a Rejected batch simply cannot be moved into an Approved or Released warehouse — there's nothing further for you to configure to enforce that.

**Can I skip straight from "material received" to "approved" without an inspection?** No — there's no path in the system that bypasses the Quality Inspection requirement for a Quarantine → Approved transfer once the item is tracked this way.

**Do I need to personally execute every Material Transfer?** No — your job is the quality decision. Depending on staffing, the Warehouse Officer or Production Manager typically executes the physical transfer once you've confirmed the result is Accepted.
