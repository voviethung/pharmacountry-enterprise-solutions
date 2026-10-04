"""Phase 6A — AI-DEMO-05: Manufacturing Insight (master plan §19E, lines ~3213-3219).

Same mandatory architecture shape as AI-DEMO-01/02/03:

    User -> Manufacturing Insight -> AI Action -> approved tools/reports -> structured business
    data -> AI synthesis

**Design decision, documented here rather than made silently: this demo follows AI-DEMO-01
(Executive Assistant)'s NO-DRAFT shape, not AI-DEMO-02/03 (QMS/DMS Copilot)'s `AI Draft`/
human-approval shape.**

The master plan's own text for THIS demo (line ~3213-3219, "Manufacturing Insight") carries no
"Human approval bắt buộc" sentence the way AI-DEMO-02's own master plan text explicitly does for
QMS Copilot. AI-DEMO-03 (DMS Copilot) faced the same absence of an explicit sentence and chose
to apply the draft/approval workflow ANYWAY, reading principle #24's "AI output in a regulated
workflow" wording broadly — that was the right call there because EVERY one of DMS Copilot's use
cases authors interpretive text (a comparison, a change summary, an impact assessment, a Q&A
answer) that gets attached to / presented alongside a real controlled-document record, where "an
unreviewed AI [output] sitting next to a real record reads exactly like a QA-authored note to
anyone who opens it later" (AI-DEMO-02's own words, restated in AI-DEMO-03's docstring).

Manufacturing Insight is structurally different, and its own name is the tell: "Insight," not
"Copilot." All 4 of its use cases (explain production delay, yield anomaly analysis, batch-
record completeness review, downtime summary) are READ-ONLY analytical QUESTIONS answered from
real structured data and handed back to the user who asked — exactly AI-DEMO-01's
`ask_enterprise()` shape (tool call -> real data -> mock synthesis -> response), not a Copilot
that drafts content into another record:
  - None of the 4 tools ever `.insert()`/`.save()`/`.submit()` anything (confirmed: no such call
    anywhere in `ai_tools.py`'s Manufacturing Insight section).
  - None of the 4 use cases produce an artifact that gets attached to, or displayed alongside, a
    Work Order / Batch / Quality Inspection record for a LATER reader to stumble on and mistake
    for human-authored documentation — the response goes back to the calling user, once, as an
    answer to their own question, the same way "which pond had the worst FCR this month?" does
    for AI-DEMO-01.
  - Even the two most compliance-adjacent-sounding use cases (yield anomaly analysis,
    batch-record completeness review) only FLAG/COMPUTE — they never decide or authorize
    anything, and never claim a flagged batch IS non-compliant, only that it deviates from a
    stated, real threshold or is missing a stated, real required record. A human still decides
    what to do about a flagged anomaly/delay/incomplete batch, exactly as a human still decides
    what to do about AI-DEMO-01's "batches on hold" or "overdue CAPAs" answers — those were never
    put behind an AI Draft either.

Master plan principle #24 ("AI output in a regulated workflow defaults to suggestion/draft,
never auto-final-approval") is about output that could BECOME final if nobody reviewed it —
there is no "final" here for a draft/approval gate to default away from: nothing is ever
persisted as a candidate business record by any of these 4 tools or by
`ask_manufacturing_insight()` itself. The full audit trail (AI Job Log: provider/model/
tool_calls/retrieved_sources, wired via the SAME `ai_core.run_ai_action()` every prior demo
uses, unmodified) still exists — this demo is fully logged, just never drafted.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action

_MANUFACTURING_INSIGHT_ACTION_CODE = "manufacturing_insight_synthesis"

# Fixed question_code -> AI Tool(s) mapping — see ai_executive_assistant.QUESTION_TOOL_MAP for
# the identical precedent this mirrors. Still no free-text NLP, still no arbitrary tool/SQL
# execution.
QUESTION_TOOL_MAP = {
	"production_delay": ["explain_production_delay"],
	"yield_anomaly": ["analyze_yield_anomalies"],
	"batch_completeness": ["check_batch_record_completeness"],
	"downtime_summary": ["summarize_downtime"],
}

# Default tool params per question_code — NOT free-text NLP parameter extraction, just fixed
# defaults scoping these 4 questions to the one company/item that actually has the genuinely
# varied Work Order/batch data seeded for it (`ai_manufacturing_insight_seeds.py`'s isolated
# `PREMIX-BROILER-2PCT-AI5` item under Golden Demo #26's own "Demo Premix Co." company — see
# that module's docstring for why this is a NEW, isolated item rather than reusing the flagship
# `PREMIX-BROILER-2PCT` one). An explicit kwarg passed by the caller always overrides these.
_QUESTION_DEFAULT_PARAMS = {
	"production_delay": {"company": "Demo Premix Co."},
	"yield_anomaly": {"item_code": "PREMIX-BROILER-2PCT-AI5", "company": "Demo Premix Co."},
	"batch_completeness": {"item_code": "PREMIX-BROILER-2PCT-AI5"},
	"downtime_summary": {"company": "Demo Premix Co."},
}


def ask_manufacturing_insight(question_code: str, user: str | None = None, **params) -> dict:
	"""The Manufacturing Insight entry point — mirrors `ask_enterprise()` almost exactly.
	Resolves question_code -> registered AI Tool(s) (looked up from the SAME `AI Tool` registry
	AI-DEMO-01/02/03 built, not a parallel one), executes each tool's real Python function AS
	`user` (permission-enforced via `frappe.get_list(user=...)` inside every tool), then calls
	the existing, unmodified `ai_core.run_ai_action()` for the mocked synthesis step. See module
	docstring for why this response has NO `ai_suggestion`/draft — it is structurally identical
	to `ask_enterprise()`'s response shape, not `run_qms_copilot()`'s."""
	user = user or frappe.session.user
	if question_code not in QUESTION_TOOL_MAP:
		frappe.throw(f"Manufacturing Insight: unknown question_code '{question_code}'. Known: {sorted(QUESTION_TOOL_MAP)}.")

	tool_codes = QUESTION_TOOL_MAP[question_code]
	call_params = {**_QUESTION_DEFAULT_PARAMS.get(question_code, {}), **params}

	tools_called, data_facts, sources, tool_notes = [], {}, [], {}
	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"Manufacturing Insight: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"Manufacturing Insight: AI Tool '{tool_code}' is disabled by the Tool Registry.")

		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **call_params)

		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		_MANUFACTURING_INSIGHT_ACTION_CODE,
		context={"question_code": question_code, **data_facts},
		user=user,
		tool_calls=tool_codes,
		retrieved_sources=sources,
	)

	return {
		"question_code": question_code,
		# Data fact: the REAL, tool-sourced structured output — never touched by the (mock) model.
		"data_facts": data_facts,
		"tool_notes": tool_notes,
		# AI interpretation: the model's own narrative text, kept in its OWN field — same
		# fact/interpretation separation AI-DEMO-01 established. No ai_suggestion/draft field:
		# see module docstring for why this demo never persists an AI Draft.
		"ai_interpretation": ai_result["output"],
		"sources": sources,
		"tools_called": tools_called,
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}
