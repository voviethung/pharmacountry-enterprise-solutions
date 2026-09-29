# Quick Start — AI QMS Copilot: Deviation to CAPA, With a Real Human Approval Gate

**Time needed:** 5–10 minutes
**What you'll see:** an AI assistant drafting a Corrective and Preventive Action (CAPA) plan from a real quality deviation — and the platform's hard rule that nothing the AI writes becomes an official record until a named person explicitly approves it.

## Purpose

This is the platform's flagship example of how AI is used in a regulated quality workflow: as a drafting assistant, never as a decision-maker. If you take away one thing from this quick start, it should be this: **an AI Draft can never turn itself into a real CAPA. Only an explicit, attributable human approval can.**

## Prerequisites

- A working login as `quality.director@pharmacountry.vn` (demo password `Demo@1234`), or an Administrator account.
- **An honest, important disclosure before you start:** as of today, *asking* the AI Copilot to draft a CAPA, and *deciding* (approving or rejecting) a draft, are performed as backend function calls — there isn't yet a Desk screen with an "Ask AI" or "Approve" button for this. Your system administrator or a technical colleague runs these calls on your behalf today. What you, as Quality Director, genuinely do yourself is **read the resulting AI Draft record** (a normal, readable form) and **your approval decision is what gets permanently recorded** as having happened — the trigger mechanism for that decision is just not a clickable button yet.

## The fastest path

1. Open the **QMS Deviation** titled *"Cold storage temperature excursion — Warehouse C"* — a real, independent deviation record (separate from the platform's main flagship Warehouse B deviation used elsewhere).
2. Someone (today: via a backend call) asks the AI Copilot to draft a CAPA for this deviation. Behind the scenes, this pulls the deviation's real data, and a mocked AI model — clearly labeled as such in every log — produces a suggested CAPA (subject, type, due date, and an action plan referencing the deviation's actual root cause).
3. Open the resulting **AI Draft** record. Notice two things kept deliberately separate: the real underlying data the AI was given, and the AI's own suggested text — never blended together, so you can always tell what's fact and what's AI interpretation. The record is clearly marked as requiring human approval, and its status is **Draft**.
4. Someone with the Quality Director login explicitly approves it (`quality.director@pharmacountry.vn` — today, via a backend call).
5. Open the resulting **QMS CAPA** record. It did not exist until that approval happened — check its creation time against the approval time if you want to confirm this yourself.

## Where to go next

- **[Role Guide — Quality Director](role-guide-quality-director.md)** — what the Quality Director's approval responsibility actually involves.
- **[Process Guide](process-guide.md)** — the full story, including what happens when a draft is rejected instead.

## Common errors / things worth knowing

| What you see | What it means |
|---|---|
| No "Ask AI" or "Approve Draft" button in the Desk UI | A genuine, disclosed gap — these actions exist and work correctly, but are triggered via backend calls today, not a form button. Ask your administrator to run them, or see the Administrator Guide. |
| An AI Draft record you try to hand-edit to "Approved" without a reviewer gets rejected by the system | Correct behavior — the system will not let a draft become Approved without a specific, named human reviewer attached. This is a deliberate safeguard against accidental or silent self-approval. |

## FAQ

**Could the AI just create the CAPA itself, skipping the draft stage?** No — there is no code path in this platform that lets an AI Draft become a real QMS CAPA without an explicit `approve` action naming a real human reviewer. This is checked in more than one place, not just assumed.

**What if the Quality Director rejects the draft?** No CAPA is created at all — rejecting is a real dead end, not a "create anyway" fallback. See the Process Guide for the full rejection path.

**Is this the same as an AI-generated report I can't trust?** No — this pattern is specifically designed so you never have to blindly trust AI text. The real, tool-sourced facts are always shown separately from the AI's suggested wording, and nothing becomes official without your sign-off.
