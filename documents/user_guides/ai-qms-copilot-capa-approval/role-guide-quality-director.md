# Role Guide — Quality Director (AI QMS Copilot Approvals)

## Purpose

As Quality Director, you are the mandatory human checkpoint between an AI-drafted quality suggestion and an official quality record. The AI QMS Copilot can summarize deviations, find similar past deviations, suggest investigation questions, draft a CAPA action plan, or summarize an audit finding — but for every one of those, your explicit, attributable decision is what determines whether it becomes something the organization treats as authoritative.

## Prerequisites

- Login: `quality.director@pharmacountry.vn` (demo password `Demo@1234`).
- Native system role: **Quality Manager** (the same shared role used by QC Manager/QA Manager/QC Analyst — see the [Administrator Guide](../administrator-guide.md) for the honest disclosure about this platform-wide limitation).
- **Important, honest disclosure:** requesting a new AI draft, and formally approving or rejecting one, are performed via backend function calls today — there is no Desk button for either action yet. What you do directly, yourself, in the Desk UI is **open and read the AI Draft record**, and it is **your named decision that gets permanently recorded** once someone (you or a colleague acting on your instruction) executes the approve/reject call. Treat this guide as describing your responsibility and what you should verify, even though the trigger mechanism is not yet a single click.

## Roles

| Role | Responsibility |
|---|---|
| QA Manager / reporter | Records the original QMS Deviation. |
| AI QMS Copilot (a system, not a person) | Produces a draft suggestion from real deviation data — never a final answer. |
| **Quality Director (you)** | Reviews the draft and makes the binding approve/reject decision. |

## How to create

You don't create the AI Draft yourself — the Copilot does, once asked (today, via a backend call referencing a real Deviation). What you can influence at approval time is the final content: when approving a CAPA draft, specific fields (subject, owner, due date, action plan) can be overridden before the real CAPA record is created, so your judgment — not just the AI's suggestion — is what actually gets recorded.

## How to review

Open the **AI Draft** record. It is deliberately structured to keep two things visibly separate:
- **The real data** the Copilot was given (e.g. the deviation's severity, description, investigation notes, root cause) — pulled directly from the actual QMS Deviation record, untouched by the AI.
- **The AI's suggested text** — clearly labeled, and for a CAPA draft, opens with an explicit note that it is an AI-suggested draft requiring QA review before it becomes an approved action plan.

Also check: the draft's status (should be **Draft** until you decide), and that `requires_human_approval` is shown as true — confirming this specific suggestion cannot bypass your review.

## How to approve

Approving a **CAPA draft** is the one case with real consequence: your approval is the *only* action in the system that creates a real **QMS CAPA** record from an AI suggestion. This is enforced as a single atomic step — there is no separate code path that could create a CAPA from a draft without your named approval attached. Once approved:
- The QMS CAPA is created with the suggested (or your overridden) fields.
- The AI Draft's status becomes **Approved**, permanently recording your name and the time.
- The underlying AI activity log is updated to show the suggestion was accepted and which real record resulted from it.

Approving one of the **other four use cases** (summarizing a deviation, finding similar deviations, suggesting investigation questions, summarizing an audit finding) works differently: your approval marks the draft text itself as human-endorsed, but does **not** create any new record — those are informational/advisory outputs, not new quality documents.

## How to amend

If the AI's suggested CAPA fields aren't quite right (wrong owner, too-generous due date, etc.), you don't need to accept them as-is — specific fields can be overridden at the moment of approval, so the CAPA that's actually created reflects your correction, not a blind copy of the AI's suggestion.

## How to cancel

**Rejecting** a draft (any use case) marks it **Rejected** and — critically, for a CAPA draft — creates absolutely nothing. No CAPA record comes into existence from a rejected draft, ever. This is deliberately a real dead end, not a "reject but create anyway" compromise.

Once a draft has been decided (Approved or Rejected), it cannot be re-decided — the system blocks any attempt to flip an already-finalized draft to a different outcome, protecting the integrity of your original decision.

## Reports

- **AI Draft** list, filtered by `use_case = draft_capa` and `status`, to see what's pending your review versus already decided.
- The underlying AI activity log records every call's provider, model, and which tools were used — useful if you ever need to demonstrate exactly what data the AI saw before producing a given suggestion.
- **QMS CAPA** list, to review CAPAs that originated from an AI draft alongside ones raised manually.

## Common errors

| Situation | What it means |
|---|---|
| An attempt to save an AI Draft as "Approved" without a named reviewer is rejected | A deliberate safeguard — the system will not let a draft self-approve or be silently marked approved without an explicit, real human name attached. |
| An attempt to reject or re-approve an already-decided draft fails | Once a draft has been approved or rejected, that decision is final — the system will not let it be re-decided, protecting the audit trail. |
| A CAPA draft's approval attempt fails because it isn't a `draft_capa` draft | The CAPA-creating approval path only applies to CAPA-type drafts — the other four use cases use a separate, simpler "approve as endorsed" action that never creates a new record. |

## FAQ

**Can the AI ever create a CAPA without me?** No. There is no code path in this system where an AI Draft becomes a real QMS CAPA without your (or another named Quality Director's) explicit approval.

**What if I disagree with part of the AI's suggestion but not all of it?** You can override specific fields (owner, due date, subject, action plan) at approval time rather than accepting or rejecting the whole thing outright.

**Why can't I just click a button to trigger the AI draft myself yet?** That's a genuine, currently-open gap in this build — the underlying function is real and works correctly, it's simply not yet wired to a Desk button. It's worth asking your platform team whether adding that button is a priority, since your actual review-and-approve responsibility (the part that matters most) already works exactly as described here.
