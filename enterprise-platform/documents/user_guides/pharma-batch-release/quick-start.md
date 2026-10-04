# Quick Start — Pharmaceutical Batch Release

**Time needed:** 5–10 minutes
**What you'll see:** how a pharmaceutical manufacturer physically stops a batch from being sold until it has passed every required quality gate — not because a procedure says so, but because the system itself blocks the wrong move.

## Purpose

This is the flagship example of the platform's manufacturing quality-control model. A batch of Paracetamol 500mg tablets moves from raw material receipt, through QC testing, into production, and finally to a QA-authorized release — and at two points along the way, the system will physically refuse to let the batch skip a step. This quick start gets you oriented on that flow fast.

## Prerequisites

- A working login to the platform (ask your administrator for a demo account if you don't have one).
- Five demo accounts exist for this walkthrough, all sharing the password `Demo@1234` (a demo-only password — never used in a real deployment):
  | Step in the flow | Login |
  |---|---|
  | Warehouse receiving | `warehouse.officer@pharmacountry.vn` |
  | QC testing | `analyst@pharmacountry.vn` |
  | QC approval | `qc.manager@pharmacountry.vn` |
  | Production | `production.manager@pharmacountry.vn` |
  | QA release | `qa.manager@pharmacountry.vn` |
- None of these accounts is a system administrator — each one only has the access a real person in that job would have. That's deliberate: it's how you can trust that what you're seeing is a genuine permission boundary, not a demo trick.

## The fastest path

1. **Log in as the Warehouse Officer.** Open the raw-material **Purchase Receipt** from supplier "ABC Pharma Chemicals Co." — six raw and packaging items have just arrived into the **RM Quarantine** warehouse. Nothing arriving from a supplier is usable yet; it all starts in quarantine.
2. Open the **Batch** record for the API ingredient (PARA-API). It's sitting in quarantine, waiting on QC.
3. **Switch login to the QC Analyst.** Open the **Quality Inspection** for that batch — it's already been tested and marked **Accepted**.
4. **Switch login to the QC Manager.** Open the **Stock Entry** (a Material Transfer) that actually moves the accepted material from RM Quarantine into RM Approved. This is the one action that legally clears the material for production.
5. **Switch login to the Production Manager.** Open the **Work Order** for PARA-500-TAB (1,000 tablets) — its Bill of Materials only draws from the RM Approved warehouse, never from Quarantine.
6. **Switch login to the QA Manager.** Open the final **Stock Entry** that moves the finished, tested batch from FG Quarantine into FG Released — the point at which the batch becomes sellable.

That's the whole chain: **Quarantine → QC tested → QC approved → manufactured → QA released.**

## See it actually enforced (optional, 2 more minutes)

If you want proof this isn't just a diagram:
- As anyone, try creating a Stock Entry that issues raw material for production straight out of a warehouse with "Quarantine" in its name. The system blocks it: *"Cannot issue item ... from Quarantine warehouse ... Material must be QC-approved and moved to an Approved warehouse first."*
- Try moving a finished-goods batch into a "Released" warehouse without an Accepted Quality Inspection for that exact batch. Blocked again: *"No Accepted Quality Inspection found for this batch — QA release requires QC approval first."*

Both of these are real validation rules running on every Stock Entry in the system, not something staged only for this demo.

## Where to go next

- **[Role Guide — QC Manager](role-guide-qc-manager.md)** — what a QC Manager does day to day in this system.
- **[Process Guide](process-guide.md)** — the full end-to-end story, every role, every record, in order.
- If someone is showing you this live, ask them to use the **Guided Demo Scenario "Pharmaceutical Batch Release"** in the Desk — its "Start Demo" button gives a click-through version of exactly this walkthrough with direct links to each record.

## Common errors at this stage

| What you see | What it means |
|---|---|
| "Cannot issue item ... from Quarantine warehouse ... for production." | Correct behavior — material hasn't been QC-approved yet. |
| "No Accepted Quality Inspection found for this batch — QA release requires QC approval first." | Correct behavior — the batch hasn't passed final QA release testing yet. |
| You can't submit a Stock Entry as `qc.manager@pharmacountry.vn` | Expected — see the FAQ below. |

## FAQ

**Why do I need five different logins instead of one?** Because segregation of duties is a real GMP requirement, not a UI choice — the person who tests a batch shouldn't be the same person who approves its release, and the person who approves quality shouldn't necessarily be the one who physically moves stock. The platform enforces this with real, separate accounts and real, separate permissions.

**Can I just log in as Administrator and click through everything myself?** You could, but you'd be missing the point — none of the five demo accounts has administrator access, and that's exactly what makes this demonstration credible: each person can only do what their role allows.

**Where do I find the exact record names (Purchase Receipt number, Batch number, etc.)?** They differ between environments (the internal test system vs. the public demo site) because each environment auto-numbers its own documents. Open the relevant list view (Purchase Receipt, Quality Inspection, Stock Entry) filtered as described above and you'll find the current one quickly — or use the Guided Demo Scenario's "Start Demo" dialog, which links directly to the live records.
