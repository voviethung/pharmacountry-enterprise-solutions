# Administrator Guide — Enterprise Platform

## Purpose

This guide is for whoever administers or configures this platform: setting up a new industry vertical, managing demo data, provisioning users and roles, configuring the AI layer, and finding/extending the guided sales-demo scenarios. It covers platform-wide administrative concerns rather than any one business transaction type — for how a specific business process works day to day, see the scenario-specific guides linked from the [README](README.md).

## Prerequisites

- A **System Manager** login. None of the demo business-role accounts described elsewhere in this guide set have System Manager access — that's deliberate (see Roles & Permissions below), so administrative tasks genuinely require a separate, real administrator account.
- Familiarity with the Frappe Desk UI (list views, doctype forms) and, for some tasks, the ability to run `bench execute` against the site (typically via your deployment's Docker Compose setup).

## 1. Industry Packs & Editions

The platform supports multiple industries (pharmaceutical manufacturing, cosmetics, livestock/pig farming, and others) from one shared codebase, controlled by two mechanisms:

- **Industry Pack** (a DocType) — one record per industry vertical (e.g. `IP-PHARMA`, `IP-COSMETICS`, `IP-LIVESTOCK-PIG`, `IP-QMS`, `IP-VETERINARY`). Each Industry Pack holds:
  - `pack_code`, `pack_name`, `industry_category`, `description`
  - `default_edition` — which edition of the platform this pack activates
  - `terminology_overrides` — industry-specific relabeling of generic terms
  - `roles` — the Role Templates this pack expects (see Roles & Permissions below)
  - `workspaces` — which Desk workspaces this pack surfaces
  - `seeds` — an ordered list of Seed Templates (see Seeding & Reset below) that populate this pack's demo data
- **Enterprise Core Settings** (a single, site-wide settings record) — its `active_edition` field controls which edition is currently active on a given site.

To see which packs exist, open the **Industry Pack** list. To see what a pack will do when seeded, open the pack record and review its `seeds` child table in sequence order.

## 2. Seeding & Reset

### Seeding a pack's demo data

Every Industry Pack's demo data is populated by calling:

```
enterprise_core.enterprise_core.api.run_industry_pack_seeds("<pack_code>")
```

This dispatches every **Seed Template** attached to the pack, in order, calling each one's own Python seed function. Two properties matter for you as an administrator:
- **It's idempotent.** Every seed function checks whether its data already exists before creating anything — so running the same pack's seeds again does not create duplicates, and safely re-creates anything that was deleted or altered in the meantime.
- **Errors don't cascade.** If one seed function in the sequence fails, the runner records that failure and continues with the rest — so one broken step doesn't block everything else in the pack from being visible in the result.

### Resetting demo data — two different tools for two different jobs

Don't confuse these:

1. **Whole-site reset** (`scripts/reset-site.sh` / the site's snapshot-and-restore tooling) — a destructive, full-site rebuild. This is the right tool for restoring a site to a known clean state between major demo sessions, but it should never be run while a live guided sales demo is in progress on that site.
2. **Per-scenario "Reset Scenario" button** (inside Guided Demo Mode — see section 5 below) — a much narrower, non-destructive action. Because every guided demo scenario only *navigates* already-real, already-submitted records (no step in a scenario walkthrough itself mutates data), "reset" for a scenario can only honestly mean *re-running that scenario's underlying Industry Pack seed function* to re-assert its canonical data — exactly the same idempotent seeding described above. It does not undo genuine transactional history (a cancelled document stays cancelled), and it is only ever wired to a function that has been read and confirmed safe to re-run. Where no safe reset function exists for a scenario, the button honestly says so (with an explanation) instead of pretending to do something.

## 3. Roles & Permissions

### Demo user accounts and Role Templates

For a fully-built-out vertical (currently: Pharmaceutical manufacturing), demo user accounts follow this pattern:
- One user per business role, at `<role>@pharmacountry.vn` (e.g. `qc.manager@pharmacountry.vn`), sharing one demo-only password (`Demo@1234` — never a real credential, never reused in a production deployment).
- Each Industry Pack's **Role Template** records map to a real, native Frappe **Role** via the Role Template's `frappe_role` field. This mapping is what actually gives each demo user their permissions — a Role Template is not itself a permission object, it's a labeled pointer to the real underlying Frappe Role.
- **Deliberately, none of these demo users has System Manager.** Logging in as each one genuinely demonstrates that role's real permission boundary rather than administrator-level access — this has been directly verified (checking role assignments, not just assuming the setup is correct).

**A known, disclosed platform limitation:** the underlying system's native Quality module has only one role — **Quality Manager** — covering the entire quality workflow. It does not distinguish QC Analyst / QC Manager / QA Manager / Quality Director as separate permission levels; all four of those business titles currently map to the same native Quality Manager role. If you need to enforce finer-grained separation between them (for example, so a QC Analyst genuinely cannot approve a QC Manager's release), use Frappe's **Role Permission Manager** to create and assign more granular custom roles — this is real, supported configuration work, just not something this platform has pre-built yet.

To add demo users for a vertical that doesn't have them yet (Cosmetics and Pig Farm currently don't — see the [README](README.md) for the full disclosure), follow the same pattern: create or confirm each Role Template's `frappe_role` mapping, then create one User per role at a consistent email pattern, assign the mapped Role, and deliberately withhold System Manager.

### Portal customer scoping — the User Permission pattern

Every customer-facing self-service portal on this platform (the 3PL client portal, the dealer portal, the supplier portal, and the farm customer portal used in the Farm Portal Technical Visit scenario) uses the **same** underlying scoping mechanism, reused verbatim rather than re-invented each time:

1. A real Frappe **User Permission** record links a portal user to the specific **Customer** (or equivalent party) record they represent — `allow="Customer"`, `for_value=<the specific customer>`, `apply_to_all_doctypes=1`.
2. Every backend function serving that portal resolves "who is this for" from the *logged-in session* (`frappe.session.user` → the linked Customer), **never** from any value the client's own request claims — so there's no parameter a browser could tamper with to see someone else's data.
3. On top of the native User Permission cascade (which already narrows what a `frappe.get_list()` call returns), every portal API additionally re-checks, in plain Python, that every returned row's own customer field actually matches the resolved customer — a deliberate belt-and-suspenders layer, so even a permission-configuration mistake couldn't silently leak a row.

If you're building a new customer-facing portal, replicate this exact three-layer pattern (User Permission + explicit list filter + post-fetch re-assertion) rather than inventing a new scoping approach — it has been independently, empirically tested (logging in as two different real customers and confirming neither can see or fetch the other's records, including by guessing at record names) across every portal that currently uses it.

## 4. AI Provider / Model / Policy Layer

AI features on this platform (like the QMS Copilot used in the AI QMS Copilot scenario) are built on a shared foundation, configured through a small set of DocTypes:

| DocType | What it configures |
|---|---|
| **AI Provider** | A connection to an AI vendor — its base URL, an enabled flag, and a securely-resolved credential (never stored in plain text on the record itself). |
| **AI Model** | One specific model available through a provider, with its declared `capabilities` (e.g. "reasoning"), a `priority` for selection ordering, and its own enabled flag. |
| **AI Action** | One specific use case's configuration — which Prompt Template to use, which AI Tools it's allowed to call, its `required_capabilities`, `fallback_policy`, `human_review_required` flag, a `max_cost_usd` ceiling, and a `retention_policy` for how long its logs are kept. |
| **Prompt Template** | The versioned system instruction and input/output schema for one AI Action. |
| **AI Tool** | A registered, callable Python function (by its exact dotted path) that an AI Action is allowed to invoke — each tool declares which DocType permission it requires, so a tool call is always run *as the real requesting user*, never with elevated access. |
| **AI Draft** | The persisted output of an AI Action that requires human review — see below. |
| **AI Job Log** | An audit record of every AI call: which provider/model answered, which tools were invoked, whether the output was ultimately accepted, and what real record (if any) resulted. |

**Model selection (the router)** filters `AI Model` records by: the model being enabled, its provider being enabled, and its declared capabilities matching what the requested AI Action needs — then prefers a configured preferred provider before falling back to the next eligible model by priority. To add a new provider or model, create the corresponding **AI Provider**/**AI Model** records and enable them; to change which model an action prefers, adjust the AI Action's `preferred_provider`/`required_capabilities` rather than hand-picking a model directly.

**The human-in-the-loop pattern.** Any AI Action with `human_review_required` set produces an **AI Draft**, not a finished record — see the AI QMS Copilot scenario's guides for the fullest worked example. The platform-wide rule this enforces: an AI Draft can never silently become an official business record. It requires an explicit, named human reviewer to approve it, that approval is permanently attributed, and a rejected draft creates nothing at all. This is enforced in code, not left to convention — attempting to bypass it (e.g. flipping a draft's status directly without a named reviewer) is blocked.

## 5. Guided Demo Mode — where to find and run guided scenarios

**Guided Demo Mode** is a real Frappe Desk feature (not a separate app) for walking a salesperson or new user through a specific, pre-built scenario, step by step, with direct links to the real records involved.

- Find it under the **Guided Demo Scenario** list in Desk. **Note:** today, only the **System Manager** role has access to this list — a business-role demo user cannot open it directly. If you want a non-administrator to run a guided demo themselves, you'll need to grant them read access to this DocType, or have an administrator drive the walkthrough on a shared screen.
- Opening a scenario and clicking **Start Demo** opens a dialog showing the objective, the primary login role, every step (with a direct "Open record →" link where the step points at a real document), and a closing "what this demonstrates" summary.
- **Reset Scenario** (inside the same dialog) either re-runs the scenario's underlying seed data (safe, idempotent — see Seeding & Reset above) or, if no safe reset function has been wired up for that scenario, shows an honest explanation of why not, rather than doing nothing silently.

**The 5 scenarios that currently exist**, each built from one real golden demo's real data:

| Scenario code | Built from |
|---|---|
| `PHARMA-BATCH-RELEASE` | Pharmaceutical Batch Release golden demo |
| `COSMETICS-STABILITY-COMPLAINT` | Cosmetics Manufacturing golden demo |
| `PIG-FARM-BREEDING-TO-SALE` | Pig Farm Management golden demo |
| `AI-QMS-COPILOT-CAPA-APPROVAL` | AI QMS Copilot AI demo |
| `FARM-PORTAL-TECHNICAL-VISIT` | Farm Customer / Technical Service Portal (Phase 7) |

**This is a deliberately small, honestly-disclosed set** — the platform has roughly 28 golden demos in total (plus several more customer-facing portal sites), and only these 5 have a Guided Demo Scenario record today. The `Guided Demo Scenario`/`Guided Demo Scenario Step` DocTypes and the Start Demo UI are fully generic — adding a 6th, 7th, etc. scenario for another golden demo is a matter of writing one more seed function in the same shape as the existing 5 (see `guided_demo_seeds.py` for the pattern), not further platform engineering. Whether to build out more is a business decision for whoever owns the platform roadmap, not something to assume is already covered.

## Reports

- **Industry Pack** list — what verticals exist and what each one seeds.
- **Guided Demo Scenario** list — what guided walkthroughs exist (System Manager access required today).
- **AI Job Log** — a full audit trail of every AI call made on the platform, across every AI-powered feature.
- **User** list, filtered by role, to review who has access to what.

## Common errors

| Situation | What it means |
|---|---|
| Re-running a pack's seed function appears to do nothing new | Expected — idempotent seed functions skip anything that already exists. Check the returned message text, which reports "already existed" vs. "created" for each step. |
| A demo user can't perform an action you expected their role to allow | Check which native Frappe Role their Role Template actually maps to — for the Quality module specifically, remember the collapsed-role limitation described above. |
| A portal user can see a "not found" error for a record you know exists | If it belongs to a different customer, this is correct, deliberate behavior (see Roles & Permissions above) — not a bug to fix. |
| The "Reset Scenario" button says reset isn't available | Correct, honest behavior for a scenario with no safe idempotent reset function wired up yet — not a broken button. |

## FAQ

**Can I add a demo login for a vertical that doesn't have one yet (e.g. Cosmetics, Pig Farm)?** Yes — follow the same Role Template → native Role → demo User pattern used for the Pharmaceutical vertical, described above. This is genuinely straightforward administrative configuration, not a code change.

**Where do I find the master plan or the full build history behind this platform?** The master plan document and `documents/project_status.md` (the platform's own running build log) are the authoritative technical references — this guide and the scenario guides it links to are written for day-to-day platform administration and end-user operation, not as a substitute for those.

**Is this documentation set the complete user-facing documentation for the whole platform?** No — see the [README](README.md) for an explicit, honest breakdown of what's covered (5 scenarios plus this platform-wide administrator guide) and what isn't yet (the remaining ~23 golden demos and other portal sites).
