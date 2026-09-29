# Phase 2A — AI & Automation Foundation

Deliverable for master plan §21 "PHASE 2A — AI & Automation Foundation" (CE-13). Master plan
is explicit that full AI capability isn't required at this stage — only that "phải tạo
abstraction đúng ngay từ đầu" (the abstraction must be correct from the start). This document
describes what was built and, just as importantly, what was deliberately deferred.

## What business modules must do

Business code (QMS, LIMS, any future module) must call `enterprise_core.enterprise_core.
ai_core.run_ai_action(action_code, context)` and never import a provider SDK (openai,
anthropic, groq, ...) directly — matching master plan §13.2's explicit anti-pattern warning.

```python
from enterprise_core.enterprise_core.ai_core import run_ai_action

result = run_ai_action(
    "deviation_analysis",
    {"subject": deviation.subject, "severity": deviation.severity, "investigation_notes": deviation.investigation_notes},
)
# result = {"output": ..., "provider": ..., "model": ..., "fallback_used": bool}
```

## Registry DocTypes (CE-13 §13.3–§13.19)

| DocType | Purpose | Master plan ref |
|---|---|---|
| **AI Provider** | Provider connection config (type, base URL, secret *reference* — never a real key) | §13.3 |
| **AI Model** | Per-model capabilities, cost, latency/privacy class, routing priority | §13.4 |
| **Prompt Template** | Versioned system instruction + input/output schema | §13.15 |
| **AI Action** | The abstraction unit — required capabilities, preferred provider, fallback policy, linked Prompt Template, human-review flag | §13.5 |
| **AI Job Log** | Full audit trail of every `run_ai_action()` call — including blocked and failed attempts, not just successes | §13.12 |
| **Automation Rule** | Event/schedule/threshold/AI-assisted triggers | §13.16 |
| **AI Tenant Policy** | Single doctype — site-wide `AI Mode` (Disabled/External Providers/Customer API Key/Platform Managed/Private Endpoint/Hybrid) + allowed-provider list | §13.19 |

## What actually works end-to-end (verified, not just described)

- **Capability-based routing** (§13.6): `AI Action.required_capabilities` is matched against
  `AI Model.capabilities`; only enabled Models on enabled Providers, allowed by the site's
  `AI Tenant Policy`, are eligible.
- **Fallback on failure** (§13.7): if the preferred provider is unavailable, the router tries
  the next eligible model by priority. Proven with a real 2-provider chain (Anthropic
  priority 10 → Groq priority 20), not just described.
- **Policy enforcement** (§13.18/§13.19): `AI Mode = Disabled` blocks every action platform-
  wide, not just the preferred provider — proven by a live test that flips the policy,
  attempts a call, confirms it's blocked, and restores the policy.
- **Full audit logging** (§13.12): every call — success, fallback, or policy-blocked — writes
  an `AI Job Log` entry. Verified directly: the demo run leaves exactly one Success, one
  Fallback Used, and one Blocked by Policy entry.

Seed demo: `enterprise_core.enterprise_core.ai_seeds.seed_ai_foundation()` (registry data) and
`seed_ai_validations()` (the 3 live proofs above — safe to re-run; each test restores any
state it perturbs). Wired into `after_install`/`after_migrate` unconditionally (cross-cutting
platform infrastructure, not tied to a single Industry Pack).

The one demo Action seeded, `deviation_analysis`, is deliberately tied to Golden Demo #3's
real `QMS Deviation` doctype (an `Automation Rule` with `trigger_type=AI-Assisted` references
it) — this is the abstraction layer proven against something real, not a toy example.

## What was deliberately deferred (per master plan's own guidance)

- **Live provider HTTP calls.** `ai_core._call_provider_adapter()` is a clearly-labeled MOCK.
  No API keys exist in this demo environment, and master plan §13.18 forbids storing real
  keys in app config/client code regardless — a real adapter would dispatch on
  `AI Provider.provider_type` to the matching HTTP client using a secret resolved from an
  actual secrets store, not a literal value on the DocType.
- **RAG pipeline** (§13.9), **Tool Registry** (§13.10), **Human-in-the-loop UI** (§13.11
  beyond the `human_review_required` flag), **Usage/Cost dashboards** (§13.13), **AI
  Evaluation** (§13.14) — all explicitly listed in master plan §13 as real but not required
  before Golden Demos exist to consume them. `AI Action.human_review_required` and
  `max_cost_usd` fields exist in the registry (so nothing downstream needs a schema change
  later) but nothing enforces them yet beyond storing the value.
- **Automation Rule execution engine.** The DocType and one seeded example exist; there's no
  scheduler/event-listener wiring `Automation Rule` records to actually fire yet (the seeded
  rule documents *intent* — "this is what should happen" — matching how DP-306's Seed
  Template registry started as data before `run_industry_pack_seeds()` gave it a runner).

## Real bug found and fixed while building this

`run_ai_action()`'s fallback detection originally compared the used model's position in the
already-filtered eligible list (`i > 0`) — but a disabled preferred provider gets filtered
*out* before the loop starts, so the next candidate becomes index 0 and would never register
as a fallback. `fallback_used` now compares the provider actually used against
`AI Action.preferred_provider` directly, which is correct regardless of how many candidates
got filtered out beforehand. Found via the fallback test's own assertion failing on this exact
case — not a data bug, but the same "an idempotency/correctness check silently passes because
of how something upstream was filtered" pattern that has come up several times across the
golden demos.
