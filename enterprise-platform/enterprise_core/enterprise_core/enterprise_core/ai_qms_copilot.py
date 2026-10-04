"""Phase 6A — AI-DEMO-02: QMS Copilot (master plan §19E, lines ~3183-3192).

Same mandatory architecture shape as AI-DEMO-01 (`ai_executive_assistant.py`):

    User -> QMS Copilot -> AI Action -> approved tools/reports -> structured business data
    -> AI synthesis

`run_qms_copilot(use_case, source_reference, user, **params)` mirrors `ask_enterprise()`'s
orchestration almost exactly: a FIXED `use_case -> AI Tool(s)` mapping (still no free-text NLP,
still no arbitrary SQL), tools called AS the real user (permission-enforced), real tool output
handed to the existing, unmodified `ai_core.run_ai_action()` for the mocked synthesis step.

What's NEW here, and the whole reason this demo exists on top of AI-DEMO-01: **every** one of
the 5 use cases produces a persisted `AI Draft` row (see `ai_drafts.py`) that starts life as a
`Draft` and can ONLY move to `Approved`/`Rejected` via an explicit, attributable human review —
never auto-finalized, per master plan principle #24 ("AI output ở regulated workflow mặc định
là suggestion/draft, không auto-final approval"). The response's own `ai_suggestion` field is
kept structurally separate from `data_facts` for the same "fact vs. interpretation" reason
AI-DEMO-01 established, PLUS it carries `requires_human_approval` / `approval_status` / `draft`
so a caller can never mistake a fresh AI Draft for an already-endorsed one.

Why ALL 5 use cases require approval, not just `draft_capa` (a real design decision, documented
here rather than made silently): the master plan text for this demo says "Human approval bắt
buộc" (mandatory) at the COPILOT level, not scoped to only the CAPA-drafting use case. A pure
"summarize deviation" or "summarize audit finding" AI output is just as capable of being
mistaken for authoritative human-authored content once it's displayed next to (or attached to)
the real record — an unreviewed AI summary sitting on a Deviation record reads exactly like a
QA-authored note to anyone who opens it later. Treating summaries as ephemeral/unreviewed
"just display it" output would be the more convenient reading, but the LESS defensible one
given the master plan's own blanket wording — so every use case gets the same `AI Draft`
workflow. The one real structural distinction that DOES matter: only `draft_capa`'s approval
mints a brand new business record (a real `QMS CAPA`) — the other 4 use cases' approval simply
marks the draft text itself as human-endorsed, with no new record created. That split is
enforced in code (`approve_capa_draft()` vs. `approve_ai_suggestion()` below), not just by
convention.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action
from enterprise_core.enterprise_core.ai_drafts import create_ai_draft, decide_ai_draft

_QMS_COPILOT_ACTION_CODE = "qms_copilot_synthesis"
_COPILOT_CODE = "qms_copilot"

# Fixed use_case -> AI Tool(s) mapping — see ai_executive_assistant.QUESTION_TOOL_MAP for the
# identical precedent this mirrors.
USE_CASE_TOOL_MAP = {
	"summarize_deviation": ["get_deviation_detail"],
	"find_similar_deviation": ["find_similar_deviations"],
	"suggest_investigation_questions": ["get_deviation_detail"],
	"draft_capa": ["get_deviation_detail"],
	"summarize_audit_finding": ["get_audit_finding_summary_data"],
}

# use_case -> (tool kwarg name to pass source_reference as, the record's own DocType)
_USE_CASE_META = {
	"summarize_deviation": ("deviation", "QMS Deviation"),
	"find_similar_deviation": ("deviation", "QMS Deviation"),
	"suggest_investigation_questions": ("deviation", "QMS Deviation"),
	"draft_capa": ("deviation", "QMS Deviation"),
	"summarize_audit_finding": ("audit", "QMS Audit"),
}

# Severity -> suggested CAPA due-date offset (days). Deterministic business-rule PRE-FILL, not
# the "AI" part of this demo — the hard mock constraint applies only to the ONE synthesis call
# (_call_provider_adapter(), untouched, still MOCK). This mirrors a real copilot pattern: rule-
# based structured pre-fill + a (here, mocked) LLM narrative, never the mock text alone trying
# to double as structured due-date/owner data.
_SEVERITY_DUE_DAYS = {"Critical": 7, "Major": 14, "Minor": 30}


def _suggest_capa_fields(deviation_data):
	severity = deviation_data.get("severity") or "Major"
	due_days = _SEVERITY_DUE_DAYS.get(severity, 14)
	root_cause = deviation_data.get("root_cause") or deviation_data.get("investigation_notes") or "root cause to be confirmed during investigation"
	return {
		"subject": f"CAPA for {deviation_data.get('subject')}",
		"capa_type": "Both" if severity == "Critical" else "Corrective",
		"due_date": str(frappe.utils.add_days(frappe.utils.nowdate(), due_days)),
		"owner_user": deviation_data.get("reported_by"),
		"action_plan": (
			f"[AI-suggested draft — requires QA review before this becomes an approved CAPA action plan.] "
			f"Address root cause: {root_cause}"
		),
	}


def run_qms_copilot(use_case: str, source_reference: str, user: str | None = None, **params) -> dict:
	"""The QMS Copilot entry point. Resolves use_case -> registered AI Tool(s) from the SAME
	`AI Tool` registry AI-DEMO-01 built (not a parallel one), executes each tool's real Python
	function AS `user`, hands real tool output to `run_ai_action()` for mock synthesis, THEN
	persists the result as a new, pending `AI Draft` row — every use case, always Draft on
	creation, never auto-approved."""
	user = user or frappe.session.user
	if use_case not in USE_CASE_TOOL_MAP:
		frappe.throw(f"QMS Copilot: unknown use_case '{use_case}'. Known: {sorted(USE_CASE_TOOL_MAP)}.")

	param_key, source_doctype = _USE_CASE_META[use_case]
	call_params = {param_key: source_reference, **params}

	tool_codes = USE_CASE_TOOL_MAP[use_case]
	tools_called, data_facts, sources, tool_notes = [], {}, [], {}
	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"QMS Copilot: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"QMS Copilot: AI Tool '{tool_code}' is disabled by the Tool Registry.")
		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **call_params)
		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		_QMS_COPILOT_ACTION_CODE,
		context={"use_case": use_case, "source_reference": source_reference, **data_facts},
		user=user,
		tool_calls=tool_codes,
		retrieved_sources=sources,
	)

	suggested_fields = None
	if use_case == "draft_capa":
		suggested_fields = _suggest_capa_fields(data_facts.get("get_deviation_detail", {}))
	elif use_case == "find_similar_deviation":
		candidates = data_facts.get("find_similar_deviations", {}).get("candidates", [])
		suggested_fields = {
			"similar_deviations": [c["deviation"] for c in candidates],
			"similarity_basis": "keyword overlap (subject/description/root_cause) + same-severity bonus — non-vector, field-based",
		}

	draft = create_ai_draft(
		copilot_code=_COPILOT_CODE,
		use_case=use_case,
		source_doctype=source_doctype,
		source_reference=source_reference,
		content=ai_result["output"],
		suggested_fields=suggested_fields,
		generated_by_job_log=ai_result["job_log"],
	)

	return {
		"use_case": use_case,
		"source_reference": source_reference,
		# Data fact: the REAL, tool-sourced structured output — never touched by the (mock) model.
		"data_facts": data_facts,
		"tool_notes": tool_notes,
		# AI suggestion: kept structurally separate from data_facts, and explicitly flagged as
		# requiring human approval — never presented as if it were already-authoritative fact.
		"ai_suggestion": {
			"text": ai_result["output"],
			"suggested_fields": suggested_fields,
			"requires_human_approval": True,
			"approval_status": draft.status,
			"draft": draft.name,
		},
		"sources": sources,
		"tools_called": tools_called,
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}


def approve_capa_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None, capa_overrides: dict | None = None) -> str:
	"""THE mandatory-approval proof for 'draft CAPA': approval and QMS CAPA creation happen
	atomically in ONE function — there is no other code path in this module that creates a QMS
	CAPA from an AI Draft. Requires the draft to still be 'Draft' (fresh) and an explicit
	`reviewed_by` (a real human user — `ai_drafts.ai_draft_validate()` enforces this a second
	time, structurally, at the DocType level, so this isn't the only gate)."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case != "draft_capa":
		frappe.throw(f"AI Draft {draft_name} is not a draft_capa suggestion (use_case={draft.use_case}) — approve_capa_draft() only applies to CAPA drafts.")
	if draft.status != "Draft":
		frappe.throw(f"AI Draft {draft_name} is already '{draft.status}' — cannot approve/convert to CAPA again.")
	if not reviewed_by:
		frappe.throw("approve_capa_draft requires an explicit reviewed_by (a real human user) — AI output cannot self-approve.")

	fields = frappe.parse_json(draft.suggested_fields or "{}")
	if capa_overrides:
		fields.update(capa_overrides)

	capa = frappe.get_doc(
		{
			"doctype": "QMS CAPA",
			"subject": fields.get("subject") or f"AI-suggested CAPA for {draft.source_reference}",
			"capa_type": fields.get("capa_type") or "Corrective",
			"source_type": draft.source_doctype,
			"source_reference": draft.source_reference,
			"owner_user": fields.get("owner_user") or reviewed_by,
			"due_date": fields.get("due_date") or frappe.utils.add_days(frappe.utils.nowdate(), 14),
			"status": "Open",
			"action_plan": fields.get("action_plan") or draft.content,
		}
	)
	capa.insert(ignore_permissions=True)

	draft.status = "Approved"
	draft.reviewed_by = reviewed_by
	draft.reviewed_on = frappe.utils.now_datetime()
	if review_notes:
		draft.review_notes = review_notes
	draft.resulting_doctype = "QMS CAPA"
	draft.resulting_reference = capa.name
	draft.save(ignore_permissions=True)

	if draft.generated_by_job_log and frappe.db.exists("AI Job Log", draft.generated_by_job_log):
		frappe.db.set_value("AI Job Log", draft.generated_by_job_log, {"accepted": 1, "final_record_reference": capa.name})

	return capa.name


def reject_capa_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	"""Rejects a draft_capa AI Draft WITHOUT creating any QMS CAPA — proves an unapproved
	suggestion never silently becomes a real record."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case != "draft_capa":
		frappe.throw(f"AI Draft {draft_name} is not a draft_capa suggestion (use_case={draft.use_case}).")
	decide_ai_draft(draft_name, "Rejected", reviewed_by, review_notes=review_notes)
	return draft_name


def approve_ai_suggestion(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	"""Approval for the 4 non-CAPA use cases — marks the draft Approved (human-endorsed as
	accurate) WITHOUT minting any new master record. Deliberately refuses a draft_capa row so
	CAPA creation always goes through the atomic `approve_capa_draft()` above."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case == "draft_capa":
		frappe.throw(f"AI Draft {draft_name} is a draft_capa suggestion — use approve_capa_draft() so approval and CAPA creation happen atomically.")
	decide_ai_draft(draft_name, "Approved", reviewed_by, review_notes=review_notes)
	return draft_name


def reject_ai_suggestion(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.use_case == "draft_capa":
		frappe.throw(f"AI Draft {draft_name} is a draft_capa suggestion — use reject_capa_draft().")
	decide_ai_draft(draft_name, "Rejected", reviewed_by, review_notes=review_notes)
	return draft_name
