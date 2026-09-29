"""Phase 6A — AI-DEMO-03: DMS Copilot (master plan §19E, lines ~3194-3201).

Same mandatory architecture shape as AI-DEMO-01/02:

    User -> DMS Copilot -> AI Action -> approved tools/reports -> structured business data
    -> AI synthesis

`run_dms_copilot(use_case, source_reference, user, **params)` mirrors `run_qms_copilot()`'s
orchestration almost exactly — a FIXED `use_case -> AI Tool(s)` mapping (still no free-text
NLP, still no arbitrary SQL/tool execution), tools called AS the real user (permission-
enforced), real tool output handed to the existing, unmodified `ai_core.run_ai_action()` for
mock synthesis, and every use case persists a new `AI Draft` row (the SAME shared, generic
DocType AI-DEMO-02 built specifically so a future copilot like this one could reuse it) that
starts life as `Draft` and can only leave that status via an explicit, attributable human
review — master plan principle #24 (line ~3690, "AI output ở regulated workflow mặc định là
suggestion/draft, không auto-final approval").

**Why ALL 5 use cases require approval, none exempted** (documented here, not decided
silently — the master plan gives no explicit "Human approval bắt buộc" sentence for THIS demo
the way it did for QMS Copilot, so this posture is this build's own interpretive choice):
document control (DMS) is exactly the same regulated, GMP-adjacent territory QMS Copilot
already established the posture for, and principle #24's own wording is general ("AI output
in a regulated workflow"), not scoped to any one copilot. The most tempting exception to carve
out would be `suggest_impacted_documents` — it reads like a plain data-fact listing, not an
authored draft — but that is exactly the "more convenient but less defensible" reading
AI-DEMO-02's own docstring already rejected for its analogous case (`summarize_deviation`):
an unreviewed AI-generated "these documents are impacted" list, sitting next to a real change-
control record, reads exactly like a QA-authored impact assessment to anyone who opens it
later, and a relationship PROXY (same department/doc_type, not a verified cross-reference) can
absolutely be wrong in ways that matter in a regulated document-control process. So this build
keeps the SAME blanket posture QMS Copilot used, for the same reason, applied consistently
rather than case-by-case. The one thing that IS different from QMS Copilot, and is a genuine
structural distinction: NONE of DMS Copilot's 5 use cases mint a new business record on
approval — a document-revision comparison, a change summary, an impacted-documents list, a
training-impact assessment, and a Q&A answer are all "interpret real data, humans decide what
to do next" outputs, unlike QMS's `draft_capa` (which produces an actual new `QMS CAPA`
record). So every use case here goes through the generic `approve_ai_suggestion()`/
`reject_ai_suggestion()` shape (renamed `approve_dms_draft()`/`reject_dms_draft()` below, with
an added copilot_code guard) — there is no DMS-Copilot equivalent of `approve_capa_draft()`.

**Q&A over effective documents is NOT anchored to one authored record.** The other 4 use
cases take a real `DMS Document` code as `source_reference` (AI Draft's `source_doctype`/
`source_reference` point at it, exactly like QMS Copilot's use cases point at a `QMS
Deviation`/`QMS Audit`). `qa_effective_documents` instead takes a free-text search query — it
answers a question over the whole Effective-document corpus, not one authored record — so its
AI Draft is persisted with `source_doctype`/`source_reference` left empty (both fields are
optional on `AI Draft`, not `reqd`) rather than pointing at an arbitrary single document; the
query text and the synthesized answer live in the draft's `title`/`content`, and the actual
retrieved sources are captured in `sources`/AI Job Log's `retrieved_sources` exactly like every
other use case already does.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action
from enterprise_core.enterprise_core.ai_drafts import create_ai_draft, decide_ai_draft

_DMS_COPILOT_ACTION_CODE = "dms_copilot_synthesis"
_COPILOT_CODE = "dms_copilot"

# Fixed use_case -> AI Tool(s) mapping — see ai_qms_copilot.USE_CASE_TOOL_MAP for the identical
# precedent this mirrors.
USE_CASE_TOOL_MAP = {
	"compare_sop_revisions": ["compare_document_revisions"],
	"create_change_summary": ["compare_document_revisions"],
	"suggest_impacted_documents": ["suggest_impacted_documents"],
	"suggest_training_impact": ["suggest_training_impact"],
	"qa_effective_documents": ["search_effective_documents"],
}

# use_case -> (tool kwarg name to pass source_reference as, the record's own DocType or None
# when the use case is not anchored to a single authored record — see module docstring).
_USE_CASE_META = {
	"compare_sop_revisions": ("document", "DMS Document"),
	"create_change_summary": ("document", "DMS Document"),
	"suggest_impacted_documents": ("document", "DMS Document"),
	"suggest_training_impact": ("document", "DMS Document"),
	"qa_effective_documents": ("query", None),
}


def run_dms_copilot(use_case: str, source_reference: str, user: str | None = None, **params) -> dict:
	"""The DMS Copilot entry point. Resolves use_case -> registered AI Tool(s) from the SAME
	`AI Tool` registry AI-DEMO-01/02 built (not a parallel one), executes each tool's real
	Python function AS `user`, hands real tool output to `run_ai_action()` for mock synthesis,
	THEN persists the result as a new, pending `AI Draft` row — every use case, always Draft on
	creation, never auto-approved. For `qa_effective_documents`, `source_reference` is the
	free-text search query, not a DocType record name — see module docstring."""
	user = user or frappe.session.user
	if use_case not in USE_CASE_TOOL_MAP:
		frappe.throw(f"DMS Copilot: unknown use_case '{use_case}'. Known: {sorted(USE_CASE_TOOL_MAP)}.")

	param_key, source_doctype = _USE_CASE_META[use_case]
	call_params = {param_key: source_reference, **params}

	tool_codes = USE_CASE_TOOL_MAP[use_case]
	tools_called, data_facts, sources, tool_notes = [], {}, [], {}
	for tool_code in tool_codes:
		if not frappe.db.exists("AI Tool", tool_code):
			frappe.throw(f"DMS Copilot: AI Tool '{tool_code}' is not registered.")
		tool = frappe.get_doc("AI Tool", tool_code)
		if not tool.enabled:
			frappe.throw(f"DMS Copilot: AI Tool '{tool_code}' is disabled by the Tool Registry.")
		fn = frappe.get_attr(tool.python_function_path)
		result = fn(user=user, **call_params)
		tools_called.append(tool_code)
		data_facts[tool_code] = result["data"]
		sources.extend(result.get("sources") or [])
		if result.get("notes"):
			tool_notes[tool_code] = result["notes"]

	ai_result = run_ai_action(
		_DMS_COPILOT_ACTION_CODE,
		context={"use_case": use_case, "source_reference": source_reference, **data_facts},
		user=user,
		tool_calls=tool_codes,
		retrieved_sources=sources,
	)

	suggested_fields = None
	if use_case in ("compare_sop_revisions", "create_change_summary"):
		cmp_data = data_facts.get("compare_document_revisions", {})
		suggested_fields = {
			"version_a": cmp_data.get("version_a"),
			"version_b": cmp_data.get("version_b"),
			"fields_changed": cmp_data.get("fields_changed"),
			"change_count": cmp_data.get("change_count"),
		}
	elif use_case == "suggest_impacted_documents":
		impacted = data_facts.get("suggest_impacted_documents", {}).get("impacted_documents", [])
		suggested_fields = {
			"impacted_documents": [i["document"] for i in impacted],
			"relationship_basis": "same department and/or same document type — non-vector, field-based proxy (no explicit cross-reference field exists in this schema)",
		}
	elif use_case == "suggest_training_impact":
		impact = data_facts.get("suggest_training_impact", {})
		suggested_fields = {
			"users_needing_retraining": [u["user"] for u in impact.get("users_needing_retraining", [])],
			"current_version": impact.get("current_version"),
		}
	elif use_case == "qa_effective_documents":
		qa = data_facts.get("search_effective_documents", {})
		suggested_fields = {
			"matched_effective_sources": [r["version"] for r in qa.get("results", [])],
			"obsolete_or_draft_matches_correctly_excluded": [r["version"] for r in qa.get("obsolete_or_draft_matches_excluded", [])],
		}

	draft = create_ai_draft(
		copilot_code=_COPILOT_CODE,
		use_case=use_case,
		source_doctype=source_doctype,
		source_reference=source_reference if source_doctype else None,
		content=ai_result["output"],
		title=f"{use_case} — {source_reference}",
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


def approve_dms_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	"""Generic approval for ANY of DMS Copilot's 5 use cases — endorses the draft text as
	human-reviewed WITHOUT minting any new record (none of the 5 use cases produce one — see
	module docstring). The copilot_code guard prevents accidentally approving a draft that
	belongs to a different copilot (e.g. `qms_copilot`) through this function."""
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.copilot_code != _COPILOT_CODE:
		frappe.throw(f"AI Draft {draft_name} does not belong to dms_copilot (copilot_code={draft.copilot_code!r}).")
	decide_ai_draft(draft_name, "Approved", reviewed_by, review_notes=review_notes)
	return draft_name


def reject_dms_draft(draft_name: str, reviewed_by: str, review_notes: str | None = None) -> str:
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.copilot_code != _COPILOT_CODE:
		frappe.throw(f"AI Draft {draft_name} does not belong to dms_copilot (copilot_code={draft.copilot_code!r}).")
	decide_ai_draft(draft_name, "Rejected", reviewed_by, review_notes=review_notes)
	return draft_name
