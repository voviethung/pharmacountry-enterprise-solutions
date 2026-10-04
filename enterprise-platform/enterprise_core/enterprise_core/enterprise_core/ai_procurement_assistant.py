"""Phase 6A — AI-DEMO-06: Procurement Assistant (master plan §19E, lines ~3221-3229).

Same mandatory architecture shape as AI-DEMO-01/02/03/05:

    User -> Procurement Assistant -> AI Action -> approved tools/reports -> structured business
    data -> AI synthesis

**A deliberate HYBRID design, documented here rather than made silently — the first Phase 6A
item that is NEITHER all-draft (QMS/DMS Copilot) NOR all-no-draft (Manufacturing Insight).** The
master plan's own text for this demo gives 4 purely analytical use cases (extract supplier
quotation, normalize terms, compare quotations, summarize price/delivery/payment/quality history)
and ONE explicit, narrower hard constraint: "AI không tự approve supplier" (the AI must NEVER
itself approve/qualify a supplier). That sentence is structurally different from QMS Copilot's
blanket "Human approval bắt buộc" (every output needs review) — it names ONE specific
consequential DECISION (a supplier's qualification/approval status), not every piece of output.
Applying AI-DEMO-02's blanket-approval posture to all 5 use cases here would be defensible but
over-broad: an "extract supplier quotation" or "compare quotations" result is exactly
AI-DEMO-01/05's read-only analytical-question shape (nothing here is minted into, or displayed
alongside, another record as if human-authored) — there is no more reason to gate it behind an
`AI Draft` than there was for `explain_production_delay()`. So:
  - `extract_quotation` / `normalize_terms` / `compare_quotations` / `summarize_supplier_history`
    follow AI-DEMO-05 (Manufacturing Insight)'s NO-DRAFT shape exactly — `ask_procurement_
    assistant()` below is structurally identical to `ask_manufacturing_insight()`.
  - `recommend_supplier_qualification` (the supplier-qualification-recommendation use case) is
    the ONE case that reuses AI-DEMO-02's `AI Draft` mechanism — see
    `recommend_supplier_qualification()`/`approve_supplier_status_draft()` below, modeled directly
    on `ai_qms_copilot.run_qms_copilot()`'s `draft_capa` / `approve_capa_draft()` pair (the closest
    precedent: an AI Draft that, once approved by a real human, mints/changes a real consequential
    record — here a `Supplier.quality_status` change instead of a new `QMS CAPA`).

**The "AI cannot self-approve a supplier" structural proof, stated precisely**: nowhere in this
module — outside `approve_supplier_status_draft()` itself — does any function ever call
`frappe.db.set_value("Supplier", ..., "quality_status", ...)` or `Supplier.save()` on a quality_
status/is_critical_supplier change. `recommend_supplier_qualification()` (the orchestration entry
point a caller/"the AI" would use) only ever calls the read-only
`ai_tools.recommend_supplier_qualification_change()` tool (which itself has no write call — see
its own docstring) and `ai_drafts.create_ai_draft()` (which only ever writes a NEW `AI Draft` row,
never touches `Supplier`). The ONLY write to `Supplier.quality_status` in this entire module is
the single `frappe.db.set_value(...)` call inside `approve_supplier_status_draft()`, itself gated
by (a) requiring the draft to still be 'Draft' (fresh, unapplied), (b) requiring an explicit
`reviewed_by` that must resolve to a real `User` record (Frappe's own Link-field integrity — a
free-text label like "AI" or "System" is rejected, not just discouraged) — enforced BOTH here and
a second time, structurally, at the DocType level by `ai_drafts.ai_draft_validate()`'s existing
no-self-approval guard (reused unmodified, not duplicated). `verify_ai_procurement_assistant_
golden_demo()` proves this negatively, not just by inspection: it asserts `Supplier.quality_status`
is UNCHANGED immediately after `recommend_supplier_qualification()` runs (before any human
approval), attempts a raw self-approval (blocked), attempts approval with no `reviewed_by`
(blocked), attempts approval with a bogus non-existent user string (blocked by Frappe's Link
field, not by this module's own code), and finally does a source-level check that
`ai_tools.recommend_supplier_qualification_change()` and `recommend_supplier_qualification()`
contain zero occurrences of a Supplier-writing call, while `approve_supplier_status_draft()`
contains exactly one.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action
from enterprise_core.enterprise_core.ai_drafts import create_ai_draft, decide_ai_draft
from enterprise_core.enterprise_core.ai_tools import (
	compare_supplier_quotations,
	extract_supplier_quotation,
	normalize_supplier_quotations,
	recommend_supplier_qualification_change,
	summarize_supplier_history,
)

_PROCUREMENT_SYNTHESIS_ACTION_CODE = "procurement_assistant_synthesis"
_QUALIFICATION_ACTION_CODE = "procurement_supplier_qualification_synthesis"
_COPILOT_CODE = "procurement_assistant"
_QUALIFICATION_USE_CASE = "supplier_qualification_recommendation"

# The 4 analytical, NO-DRAFT use cases — mirrors ai_manufacturing_insight.QUESTION_TOOL_MAP's
# exact shape (fixed use_case -> AI Tool(s), still no free-text NLP, still no arbitrary tool/SQL
# execution).
ANALYTICAL_USE_CASE_TOOL_MAP = {
	"extract_quotation": ["extract_supplier_quotation"],
	"normalize_terms": ["normalize_supplier_quotations"],
	"compare_quotations": ["compare_supplier_quotations"],
	"summarize_supplier_history": ["summarize_supplier_history"],
}

# use_case -> (tool kwarg name source_reference is passed as). extract_quotation takes a Supplier
# Quotation name; normalize_terms/compare_quotations take an item_code (comparing across every
# quotation for that item — a genuine multi-supplier comparison, the actual point of these two use
# cases); summarize_supplier_history takes a Supplier name.
_ANALYTICAL_USE_CASE_PARAM_KEY = {
	"extract_quotation": "supplier_quotation",
	"normalize_terms": "item_code",
	"compare_quotations": "item_code",
	"summarize_supplier_history": "supplier",
}


def ask_procurement_assistant(use_case: str, source_reference: str | None = None, user: str | None = None, **params) -> dict:
	"""The 4-analytical-use-case entry point — structurally IDENTICAL to
	`ask_manufacturing_insight()` (NO-DRAFT: see module docstring for why). Resolves
	use_case -> registered AI Tool(s) from the SAME `AI Tool` registry every prior Phase 6A item
	built (not a parallel one), executes each tool's real Python function AS `user`, hands real
	tool output to the existing, unmodified `ai_core.run_ai_action()` for mock synthesis."""
	user = user or frappe.session.user
	if use_case not in ANALYTICAL_USE_CASE_TOOL_MAP:
		frappe.throw(f"Procurement Assistant: unknown analytical use_case '{use_case}'. Known: {sorted(ANALYTICAL_USE_CASE_TOOL_MAP)}. (Did you mean recommend_supplier_qualification()?)")

	param_key = _ANALYTICAL_USE_CASE_PARAM_KEY[use_case]
	call_params = {param_key: source_reference, **params} if source_reference is not None else dict(params)

	tool_codes = ANALYTICAL_USE_CASE_TOOL_MAP[use_case]
	tools_called, data_facts, sources, tool_notes = [], {}, [], {}
	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"Procurement Assistant: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"Procurement Assistant: AI Tool '{tool_code}' is disabled by the Tool Registry.")
		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **call_params)
		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		_PROCUREMENT_SYNTHESIS_ACTION_CODE,
		context={"use_case": use_case, "source_reference": source_reference, **data_facts},
		user=user,
		tool_calls=tool_codes,
		retrieved_sources=sources,
	)

	return {
		"use_case": use_case,
		"source_reference": source_reference,
		# Data fact: the REAL, tool-sourced structured output — never touched by the (mock) model.
		"data_facts": data_facts,
		"tool_notes": tool_notes,
		# AI interpretation, kept in its own field, same fact/interpretation separation every
		# prior Phase 6A item established. No ai_suggestion/draft field here — see module
		# docstring for why these 4 use cases are deliberately NO-DRAFT.
		"ai_interpretation": ai_result["output"],
		"sources": sources,
		"tools_called": tools_called,
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}


def recommend_supplier_qualification(supplier: str, user: str | None = None) -> dict:
	"""THE 5th, consequential use case. Calls the read-only `recommend_supplier_qualification_
	change()` tool (no write call anywhere in it — see its own docstring), hands its real facts to
	the existing, unmodified `run_ai_action()` for mock synthesis, THEN persists the result as a
	new, pending `AI Draft` row — exactly mirroring `run_qms_copilot()`'s `draft_capa` shape, the
	closest precedent (an AI Draft that, once approved, mints/changes a real record). This function
	itself never writes to `Supplier` — see module docstring for the full structural proof."""
	user = user or frappe.session.user
	if not frappe.db.exists("AI Tool", "recommend_supplier_qualification_change"):
		frappe.throw("Procurement Assistant: AI Tool 'recommend_supplier_qualification_change' is not registered.")
	tool = frappe.get_doc("AI Tool", "recommend_supplier_qualification_change")
	if not tool.enabled:
		frappe.throw("Procurement Assistant: AI Tool 'recommend_supplier_qualification_change' is disabled by the Tool Registry.")

	fn = frappe.get_attr(tool.python_function_path)
	result = fn(user=user, supplier=supplier)
	data_facts = {"recommend_supplier_qualification_change": result["data"]}
	sources = result.get("sources") or []

	ai_result = run_ai_action(
		_QUALIFICATION_ACTION_CODE,
		context={"use_case": _QUALIFICATION_USE_CASE, "source_reference": supplier, **data_facts},
		user=user,
		tool_calls=["recommend_supplier_qualification_change"],
		retrieved_sources=sources,
	)

	suggested_fields = {
		"recommended_status": result["data"].get("recommended_status"),
		"current_status": result["data"].get("current_status"),
		"change_recommended": result["data"].get("change_recommended"),
		"reasons": result["data"].get("reasons"),
	}

	draft = create_ai_draft(
		copilot_code=_COPILOT_CODE,
		use_case=_QUALIFICATION_USE_CASE,
		source_doctype="Supplier",
		source_reference=supplier,
		content=ai_result["output"],
		title=f"Supplier qualification recommendation — {supplier}",
		suggested_fields=suggested_fields,
		generated_by_job_log=ai_result["job_log"],
	)

	return {
		"use_case": _QUALIFICATION_USE_CASE,
		"source_reference": supplier,
		"data_facts": data_facts,
		# AI suggestion: kept structurally separate from data_facts, explicitly flagged as
		# requiring human approval — never presented as if it were an already-applied decision.
		"ai_suggestion": {
			"text": ai_result["output"],
			"suggested_fields": suggested_fields,
			"requires_human_approval": True,
			"approval_status": draft.status,
			"draft": draft.name,
		},
		"sources": sources,
		"tools_called": ["recommend_supplier_qualification_change"],
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}


def approve_supplier_status_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None, status_override: str | None = None) -> str:
	"""THE mandatory-approval proof for 'AI không tự approve supplier': approval and the real
	`Supplier.quality_status` change happen atomically in ONE function — modeled directly on
	`ai_qms_copilot.approve_capa_draft()`. This is the ONLY function anywhere in this codebase
	that ever writes `Supplier.quality_status`/`is_critical_supplier` as a consequence of an AI
	Draft. Requires the draft to still be 'Draft' (fresh, unapplied) and an explicit `reviewed_by`
	— a real human User docname; `ai_drafts.ai_draft_validate()` enforces the same non-self-
	approval guarantee a second time, structurally, at the DocType level, so this isn't the only
	gate. `status_override` lets a reviewer apply a DIFFERENT status than the one recommended
	(e.g. downgrade to 'Under Review' instead of the suggested 'Disqualified') — the human decision
	is never forced to match the AI's own suggestion verbatim."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case != _QUALIFICATION_USE_CASE:
		frappe.throw(f"AI Draft {draft_name} is not a {_QUALIFICATION_USE_CASE} suggestion (use_case={draft.use_case}) — approve_supplier_status_draft() only applies to supplier-qualification drafts.")
	if draft.status != "Draft":
		frappe.throw(f"AI Draft {draft_name} is already '{draft.status}' — cannot approve/apply again.")
	if not reviewed_by:
		frappe.throw("approve_supplier_status_draft requires an explicit reviewed_by (a real human user) — AI output cannot self-approve a supplier.")
	if not frappe.db.exists("User", reviewed_by):
		frappe.throw(f"approve_supplier_status_draft: reviewed_by {reviewed_by!r} is not a real User record.")

	fields = frappe.parse_json(draft.suggested_fields or "{}")
	new_status = status_override or fields.get("recommended_status")
	if not new_status:
		frappe.throw(f"AI Draft {draft_name} has no recommended_status in its suggested_fields and no status_override was given — nothing to apply.")

	supplier = draft.source_reference
	# The ONE and ONLY write to Supplier.quality_status anywhere in this module — see the module
	# docstring's structural proof.
	frappe.db.set_value("Supplier", supplier, "quality_status", new_status)

	draft.status = "Approved"
	draft.reviewed_by = reviewed_by
	draft.reviewed_on = frappe.utils.now_datetime()
	if review_notes:
		draft.review_notes = review_notes
	draft.resulting_doctype = "Supplier"
	draft.resulting_reference = supplier
	draft.save(ignore_permissions=True)

	if draft.generated_by_job_log and frappe.db.exists("AI Job Log", draft.generated_by_job_log):
		frappe.db.set_value("AI Job Log", draft.generated_by_job_log, {"accepted": 1, "final_record_reference": supplier})

	return supplier


def reject_supplier_status_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	"""Rejects a supplier-qualification-recommendation AI Draft WITHOUT touching the real
	Supplier record at all — proves an unapproved recommendation never silently changes a
	supplier's qualification status."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case != _QUALIFICATION_USE_CASE:
		frappe.throw(f"AI Draft {draft_name} is not a {_QUALIFICATION_USE_CASE} suggestion (use_case={draft.use_case}).")
	decide_ai_draft(draft_name, "Rejected", reviewed_by, review_notes=review_notes)
	return draft_name
