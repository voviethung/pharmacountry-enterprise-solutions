"""Phase 6A — AI-DEMO-09 (Livestock Farm Assistant) + AI-DEMO-10 (Shrimp/Aquaculture Assistant)
(master plan §19E, lines ~3250-3268). The master plan's own curated Phase 6A summary list treats
"Farm/Aquaculture Insight" as ONE combined item even though its detailed spec numbers it as two
sub-items — built together here, as instructed, under two entry points in this one module.

Same mandatory architecture shape as every prior Phase 6A item:

    User -> {Livestock,Aquaculture} Insight -> AI Action -> approved tools/reports -> structured
    business data -> AI synthesis

**Design decision, documented here rather than made silently: both verticals follow AI-DEMO-05
(Manufacturing Insight)'s NO-DRAFT shape, exactly as the task instruction directs.** All 8 use
cases across both verticals (FCR deterioration explanation, mortality anomaly, barn/flock
requiring attention, feed-cost analysis; pond instability analysis, feed/FCR trend, water trend
analysis, anomaly explanation) are READ-ONLY analytical QUESTIONS answered from real structured
data and handed back to the user who asked — nothing here is minted into, or displayed alongside,
another record for a later reader to mistake as human-authored (the same reasoning
`ai_manufacturing_insight.py`'s own module docstring already gives at length for why THAT demo is
NO-DRAFT; it applies identically here — analytically this pair is closest to Manufacturing
Insight of all 4 prior Phase 6A items, not to QMS/DMS Copilot's draft/approval shape).

**"Automation handles hard thresholds. AI handles interpretation."** — see `ai_tools.py`'s own
"AI-DEMO-09 + AI-DEMO-10" section docstring for the full, per-vertical proof of how this was
applied (Shrimp Farm's real, pre-existing SF10 water-reading automation is read/interpreted, never
duplicated; Pig Farm has no equivalent threshold automation at all, so the livestock tools use a
farm's-own-relative-history comparison instead of inventing a new hard threshold anywhere).

Two entry points, not one combined function, because the two verticals have genuinely different
question sets and default data scopes (isolated Pig pens vs. isolated Shrimp ponds) — forcing them
through one function with a `vertical` parameter would only add an extra dispatch layer with no
real benefit, the same "two cleaner functions read better" judgment call the task instructions
explicitly allow.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action

_LIVESTOCK_INSIGHT_ACTION_CODE = "livestock_farm_insight_synthesis"
_AQUACULTURE_INSIGHT_ACTION_CODE = "aquaculture_insight_synthesis"

# Fixed question_code -> AI Tool mapping — see ai_manufacturing_insight.QUESTION_TOOL_MAP for the
# identical precedent this mirrors. Still no free-text NLP, still no arbitrary tool/SQL execution.
LIVESTOCK_QUESTION_TOOL_MAP = {
	"fcr_deterioration": ["explain_fcr_deterioration"],
	"mortality_anomaly": ["analyze_mortality_anomaly"],
	"barn_requiring_attention": ["identify_barn_requiring_attention"],
	"feed_cost_analysis": ["analyze_feed_cost"],
}

AQUACULTURE_QUESTION_TOOL_MAP = {
	"pond_instability": ["analyze_pond_instability"],
	"feed_fcr_trend": ["analyze_feed_fcr_trend"],
	"water_trend": ["analyze_water_trend"],
	"pond_anomaly_explanation": ["explain_pond_anomaly"],
}


def _run_insight(question_tool_map, action_code, question_code, user, params):
	user = user or frappe.session.user
	if question_code not in question_tool_map:
		frappe.throw(f"Farm/Aquaculture Insight: unknown question_code '{question_code}'. Known: {sorted(question_tool_map)}.")

	tool_codes = question_tool_map[question_code]
	tools_called, data_facts, sources, tool_notes = [], {}, [], {}
	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"Farm/Aquaculture Insight: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"Farm/Aquaculture Insight: AI Tool '{tool_code}' is disabled by the Tool Registry.")
		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **params)
		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		action_code,
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
		# fact/interpretation separation every prior Phase 6A item established. No ai_suggestion/
		# draft field: see module docstring for why this pair is NO-DRAFT.
		"ai_interpretation": ai_result["output"],
		"sources": sources,
		"tools_called": tools_called,
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}


def ask_livestock_insight(question_code: str, user: str | None = None, **params) -> dict:
	"""AI-DEMO-09 — Livestock Farm Assistant entry point. Resolves question_code -> registered AI
	Tool (from the SAME `AI Tool` registry every prior Phase 6A item built, not a parallel one),
	executes it AS `user`, hands its real output into the existing, unmodified
	`ai_core.run_ai_action()` for mocked synthesis. Defaults to the isolated `PEN-AI9-C1/C2/C3`
	Pig Grower Batch cohorts (`ai_tools._LIVESTOCK_AI9_PENS`) unless the caller passes an explicit
	`farm_pens` kwarg — see `ai_tools.py`'s own section docstring for why the flagship Golden Demo
	#11 batch is excluded by default (its feed-log data isn't FCR-realistic, sized for a different
	test's purpose)."""
	return _run_insight(LIVESTOCK_QUESTION_TOOL_MAP, _LIVESTOCK_INSIGHT_ACTION_CODE, question_code, user, params)


def ask_aquaculture_insight(question_code: str, user: str | None = None, **params) -> dict:
	"""AI-DEMO-10 — Shrimp/Aquaculture Assistant entry point. Structurally identical to
	`ask_livestock_insight()`. Defaults to the isolated `POND-AI10-1/2/3` Shrimp Stocking Batch/
	Harvest/Water-Reading cycles (`ai_tools._AQUACULTURE_AI10_PONDS`) unless the caller passes an
	explicit `ponds` kwarg — Golden Demo #8's own flagship `POND-A1` is a single crop cycle with
	nothing to trend against, so it is excluded by default (never touched by this demo's own seed
	data either)."""
	return _run_insight(AQUACULTURE_QUESTION_TOOL_MAP, _AQUACULTURE_INSIGHT_ACTION_CODE, question_code, user, params)
