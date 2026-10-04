# Process Guide — AI QMS Copilot: Deviation to CAPA, With a Real Human Approval Gate (End to End)

## Purpose

This is the complete story of how an AI-assisted suggestion becomes (or doesn't become) an official quality record on this platform — the platform's clearest example of "human-in-the-loop" AI in a regulated environment. It follows one real deviation from report through AI-assisted drafting to a final, human-approved CAPA.

## Prerequisites

- Login as `quality.director@pharmacountry.vn` (password `Demo@1234`) to see the reviewer's-eye view, or an Administrator account to see everything.
- **Honest disclosure, stated plainly up front:** the steps that *ask* the AI for a draft and that *execute* an approve/reject decision are, today, backend function calls — not Desk buttons. This guide describes the real business process and what a human reviewer actually verifies and decides; where a step is currently backend-only, it's called out explicitly.

## Roles involved

| Role | Responsibility |
|---|---|
| QA Manager | Reports the original deviation. |
| AI QMS Copilot (a system) | Produces a draft suggestion from real, tool-sourced data — never invents facts, never finalizes anything itself. |
| **Quality Director** | Reviews the draft and makes the binding approve/reject decision. |

## The process, step by step

### 1. A deviation is reported

A real **QMS Deviation** exists: *"Cold storage temperature excursion — Warehouse C"* — a cold storage unit recorded a temperature excursion above its validated range during a compressor fault. It's marked **Major** severity, reported by the QA Manager, and under investigation. (This is a separate, independent deviation from the platform's main "Warehouse B" flagship deviation used in other examples — deliberately, so this scenario doesn't quietly interfere with unrelated demo data.)

### 2. Someone asks the AI Copilot to draft a CAPA

*(Today: a backend function call, narrated here as a real step because it produces real, inspectable results.)* The Copilot is asked to draft a Corrective and Preventive Action for this deviation. Behind the scenes:
- It calls a real, registered tool that fetches the deviation's actual data (severity, description, investigation notes, root cause) — the same real record you could open yourself.
- It hands that real data to an AI model (in this build, a clearly-labeled mock model — every such call is logged with which provider and model were used, so nobody could mistake it for an untracked or hidden step) to produce a draft.
- The AI also fills in a few deterministic, rule-based suggestions alongside the AI text — for example, a suggested due date based on the deviation's severity (a Major severity here maps to a 14-day suggested due date), and a suggested action-plan owner drawn from who originally reported the deviation. These are business-rule pre-fills, not the AI "guessing" — worth knowing so you don't mistake a sensible default for an AI judgment call.

### 3. The suggestion is persisted as a Draft — never automatically final

The result is saved as an **AI Draft** record. Its status starts as **Draft**, and it is explicitly flagged as requiring human approval. The record keeps two things structurally separate:
- **`data_facts`** — the real, tool-sourced data the AI was given, untouched.
- **`ai_suggestion`** — the AI's own generated text and suggested fields, clearly marked as a suggestion.

This separation is deliberate and enforced by the data structure itself, not just a formatting convention — so a reviewer opening this record later can never mistake AI-generated wording for verified fact.

### 4. The Quality Director reviews the draft

Quality Director opens the AI Draft and reads both the real data and the AI's suggested action plan side by side. The suggested action plan text itself even opens with a reminder that it is an AI-suggested draft requiring review — a small but deliberate detail meant to stop anyone downstream from mistaking it for a finished, authoritative document if it were ever seen out of context.

### 5. The decision: approve, or reject

*(Today: a backend function call, executed on the Quality Director's explicit instruction.)*

**If approved:** this is the only action in the entire system that can turn this AI Draft into a real **QMS CAPA** record. The approval and the CAPA's creation happen as one atomic step — there is no separate path that could create the CAPA without this specific approval. The resulting CAPA carries the suggested (or Quality-Director-overridden) subject, type, owner, due date, and action plan. The AI Draft itself updates to status **Approved**, permanently recording who approved it and when, and the underlying AI activity log is updated to show the suggestion was accepted and which real record it became.

**If rejected instead:** the AI Draft's status becomes **Rejected**, and — this is the point of the whole exercise — **no CAPA is created at all**. Nothing is left behind pretending to be an official record. A second, independent test of this exact scenario (rejecting a different draft for the same deviation) confirms the CAPA count genuinely does not change when a draft is rejected.

Two further safeguards apply regardless of outcome:
- **No self-approval.** The system will not allow a draft to be saved directly as "Approved" without a named human reviewer attached — attempting this is blocked outright.
- **No re-deciding.** Once a draft has been Approved or Rejected, that decision is final; the system blocks any attempt to change it afterward.

### 6. The real CAPA exists — and is inspectable

Once approved, the **QMS CAPA** record can be opened directly. Its creation timestamp is strictly after the approval action — proof, if you want it, that the record genuinely did not exist before the human decision was made.

## What this demonstrates, in plain terms

The AI never gets the final word. It gathers real data, produces a clearly-labeled draft, and stops. A named human — here, the Quality Director — is the only one who can turn that draft into something the organization treats as an official quality record, and even a rejection is handled honestly (nothing is quietly created anyway).

## Reports

- **AI Draft** list, filtered by `use_case` and `status`, to see everything pending review versus already decided across all five AI Copilot use cases (not just CAPA drafting).
- The AI activity/job log, showing every call's provider, model, and the real tools it used — a full audit trail of what the AI was actually given and asked to do.
- **QMS CAPA** list, to see CAPAs that originated from an approved AI draft alongside ones raised manually through the standard quality process.

## Common errors across the process

| Situation | What it means |
|---|---|
| A draft cannot be saved as Approved without a reviewer | Deliberate self-approval guard. |
| A decided draft can't be re-decided | Deliberate finality guard, protecting the audit trail. |
| The non-CAPA approval path refuses a `draft_capa` draft (and vice versa) | CAPA creation and simple suggestion endorsement are two different, non-interchangeable actions on purpose — the system keeps them separate so CAPA creation always goes through its own atomic, auditable path. |

## FAQ

**Why does a Major-severity deviation get a 14-day suggested due date specifically?** That mapping (Critical → 7 days, Major → 14 days, Minor → 30 days) is a fixed business rule applied consistently, not something the AI model decides case by case — so due-date suggestions are predictable and explainable, even before you consider the AI-written narrative around them.

**Could two different reviewers approve the same draft twice?** No — once a draft is Approved (or Rejected), the finality guard prevents it from being decided again by anyone.

**Is this pattern specific to CAPAs?** No — all five AI Copilot use cases (summarizing a deviation, finding similar deviations, suggesting investigation questions, drafting a CAPA, summarizing an audit finding) go through the same Draft-then-human-decision pattern. CAPA drafting is simply the one use case whose approval also mints a brand-new business record; the other four simply mark the suggestion itself as endorsed.
