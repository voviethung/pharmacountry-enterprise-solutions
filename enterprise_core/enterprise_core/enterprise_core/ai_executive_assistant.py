"""Phase 6A — AI-DEMO-01: Executive Assistant (master plan §19E, lines ~3154-3181).

Kiến trúc (mandatory shape):

    User -> Ask Enterprise -> AI Action -> approved tools/reports -> structured business data
    -> AI synthesis

`ask_enterprise()` is the ONE entry point ("Ask Enterprise") for this demo's 5 example
questions. It never lets the AI construct or run SQL — it resolves a small FIXED
question_code -> AI Tool registry mapping (this demo proves the architecture, not NLP intent
classification — master plan explicitly scopes AI-DEMO-01 to 5 known questions), calls the
REAL registered tool function(s) as the calling user (so results are genuinely
permission-scoped, not just labeled as if they were), then hands the REAL tool output to the
EXISTING, unmodified `ai_core.run_ai_action()` for the mock "AI synthesis" step.

The response is intentionally structured so a caller can tell data fact from AI
interpretation apart WITHOUT parsing prose:
    {
        "question_code": ...,
        "data_facts": {<tool_code>: <tool's real structured output>, ...},
        "ai_interpretation": "<the (mocked) model's own narrative text>",
        "sources": ["QMS CAPA:xyz", "Stock Ledger Entry:...", ...],
        "tools_called": ["get_overdue_capas", ...],
        "provider": ..., "model": ..., "fallback_used": ..., "job_log": ...,
    }
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action

_ASK_ENTERPRISE_ACTION_CODE = "ask_enterprise_synthesis"

# Fixed question_code -> AI Tool(s) mapping. Deliberately NOT free-text NLP — see module
# docstring. Each question maps to exactly one tool for this first iteration; nothing stops a
# later AI-DEMO item from mapping a question to multiple tools (the response shape already
# supports it: data_facts/sources/tools_called are all lists/dicts keyed by tool_code).
QUESTION_TOOL_MAP = {
	"overdue_capas": ["get_overdue_capas"],
	"batches_on_hold": ["get_batches_on_hold"],
	"near_expiry_inventory": ["get_near_expiry_inventory"],
	"worst_fcr_pond": ["get_worst_fcr_pond"],
	"revenue_trend": ["get_revenue_trend_explanation_data"],
}

# Default tool params per question_code — NOT free-text NLP parameter extraction, just a
# fixed default so "Doanh thu tháng này giảm vì sao?" is scoped to the one company that
# actually has the synthetic multi-month revenue-history data seeded for it (Golden Demo #25,
# Consumer Distribution — see ai_executive_assistant_seeds.seed_ai_demo_revenue_history()).
# Without this, get_revenue_trend_explanation_data() would aggregate Sales Invoices across
# EVERY golden demo's company, diluting the deliberate month-over-month decline story with
# unrelated demos' same-day seed invoices. An explicit `company=` kwarg passed by the caller
# always overrides this default.
_QUESTION_DEFAULT_PARAMS = {
	"revenue_trend": {"company": "Demo Consumer Distribution Co."},
}


def ask_enterprise(question_code: str, user: str | None = None, **params) -> dict:
	"""The 'Ask Enterprise' entry point. Resolves question_code -> registered AI Tool(s) (each
	tool row looked up from the `AI Tool` registry, not hardcoded here, so the registry stays
	the single source of truth for what's callable), executes each tool's real Python function
	AS `user` (permission-enforced), then calls the existing `run_ai_action()` for the mocked
	synthesis step — passing the real tool output through as `context` so the mock adapter's
	echoed `Context keys: [...]` genuinely reflects what real data was available to it."""
	user = user or frappe.session.user
	if question_code not in QUESTION_TOOL_MAP:
		frappe.throw(f"Ask Enterprise: unknown question_code '{question_code}'. Known: {sorted(QUESTION_TOOL_MAP)}.")

	tool_codes = QUESTION_TOOL_MAP[question_code]
	tools_called = []
	data_facts = {}
	sources = []
	tool_notes = {}

	call_params = {**_QUESTION_DEFAULT_PARAMS.get(question_code, {}), **params}

	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"Ask Enterprise: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"Ask Enterprise: AI Tool '{tool_code}' is disabled by the Tool Registry.")

		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **call_params)

		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		_ASK_ENTERPRISE_ACTION_CODE,
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
		# AI interpretation: the model's own narrative text, kept in its OWN field so a caller
		# can never accidentally treat interpretation as fact (or vice versa) by string-parsing.
		"ai_interpretation": ai_result["output"],
		"sources": sources,
		"tools_called": tools_called,
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}
