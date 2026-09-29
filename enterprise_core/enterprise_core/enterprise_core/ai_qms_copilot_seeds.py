"""Phase 6A — AI-DEMO-02 (QMS Copilot) seed data + validations. Registers the 3 new `AI Tool`
rows this demo adds to the SAME registry AI-DEMO-01 built (`get_deviation_detail`,
`find_similar_deviations`, `get_audit_finding_summary_data`), the `qms_copilot_synthesis`
Prompt Template/AI Action, two additional `QMS Deviation` records needed to give
`find_similar_deviations()` a genuine positive match AND a genuine negative control (Golden
Demo #2/#3's existing seeded deviations don't share enough vocabulary with each other to prove
similarity actually works), and validation functions proving: all 5 use cases run end-to-end,
the similarity search finds a real match and correctly excludes an unrelated deviation, and —
the defining acceptance criterion for this demo — the mandatory human-approval workflow: a
draft cannot become a real CAPA without an explicit, attributable approval step, an
unapproved/rejected draft is clearly distinguishable from an approved one, and the DocType-level
guard rails (no self-approval, no re-deciding a finalized draft) actually fire.
"""

import frappe

from enterprise_core.enterprise_core.ai_qms_copilot import (
	USE_CASE_TOOL_MAP,
	approve_ai_suggestion,
	approve_capa_draft,
	reject_capa_draft,
	run_qms_copilot,
)
from enterprise_core.enterprise_core.ai_drafts import create_ai_draft
from enterprise_core.enterprise_core.qms_seeds import seed_deviation_capa_flow, seed_qms_audit

# Reuses the exact same real, distinct demo users Golden Demo #3's own CAPA owner/closer
# segregation (Q02) already established — quality.director is the one who REVIEWS/APPROVES AI
# output here, never the AI itself and never the seed script's own Administrator session.
_REVIEWER = "quality.director@pharmacountry.vn"
_REPORTER = "qa.manager@pharmacountry.vn"

_SIMILAR_DEVIATION_SUBJECT = "Cold storage temperature excursion — Warehouse C"
_UNRELATED_DEVIATION_SUBJECT = "Packaging label misprint — Batch 552199A"


# ---------------------------------------------------------------------------
# AI Tool registry additions (3 tools, appended to AI-DEMO-01's registry)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"get_deviation_detail",
		"Deviation Detail",
		"Full detail for one QMS Deviation plus any linked QMS CAPA (Golden Demo #2/#3 QMS).",
		"enterprise_core.enterprise_core.ai_tools.get_deviation_detail",
		"QMS Deviation",
	),
	(
		"find_similar_deviations",
		"Find Similar Deviations",
		"Non-vector, field/keyword-based similarity search across QMS Deviation (severity + subject/description/root_cause keyword overlap).",
		"enterprise_core.enterprise_core.ai_tools.find_similar_deviations",
		"QMS Deviation",
	),
	(
		"get_audit_finding_summary_data",
		"Audit Finding Summary Data",
		"Full detail for one QMS Audit plus all of its QMS Audit Finding child rows.",
		"enterprise_core.enterprise_core.ai_tools.get_audit_finding_summary_data",
		"QMS Audit",
	),
]


def _ensure_ai_tools():
	created = []
	for tool_code, label, description, path, permission_doctype in _AI_TOOLS:
		if frappe.db.exists("AI Tool", tool_code):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Tool",
				"tool_code": tool_code,
				"label": label,
				"description": description,
				"python_function_path": path,
				"required_permission_doctype": permission_doctype,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append(tool_code)
	return created


def _ensure_prompt_template():
	if frappe.db.exists("Prompt Template", {"template_code": "qms_copilot_synthesis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "qms_copilot_synthesis",
			"version": 1,
			"system_instruction": (
				"You are a Quality Management System copilot assisting with one of 5 approved use cases "
				"(summarize a deviation, find similar deviations, suggest investigation questions, draft a "
				"CAPA, summarize an audit finding). You are given REAL, tool-sourced structured QMS data as "
				"context — never invent facts, never fetch additional data yourself, never run or suggest "
				"SQL. Your output is ALWAYS a draft/suggestion for a qualified human reviewer — it is never "
				"final, never auto-approved, and never itself a substitute for the underlying data facts, "
				"which are returned and logged separately."
			),
			"input_schema": frappe.as_json({"use_case": "string", "source_reference": "string", "<tool_code>": "object (tool-specific structured data)"}),
			"output_schema": frappe.as_json({"draft": "string — a suggestion requiring human approval, never auto-final"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", "qms_copilot_synthesis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "qms_copilot_synthesis",
			"description": "AI-DEMO-02 QMS Copilot — synthesizes a draft/suggestion over real QMS tool output for one of 5 approved use cases. Output always requires human approval (never auto-final).",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "qms_copilot_synthesis", "version": 1}, "name"),
			"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS),
			"human_review_required": 1,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Extra demo Deviations — needed so find_similar_deviations() has a genuine positive match
# (Golden Demo #2/#3's own existing seeded deviations don't share enough vocabulary to prove
# similarity works) and a genuine negative control (an unrelated deviation that should NOT be
# flagged similar).
# ---------------------------------------------------------------------------

def _ensure_similar_deviation():
	existing = frappe.db.get_value("QMS Deviation", {"subject": _SIMILAR_DEVIATION_SUBJECT}, "name")
	if existing:
		return existing, False
	dev = frappe.get_doc(
		{
			"doctype": "QMS Deviation",
			"subject": _SIMILAR_DEVIATION_SUBJECT,
			"description": "Cold storage unit C-05 recorded a temperature excursion above the validated range during a compressor fault.",
			"severity": "Major",
			"status": "Under Investigation",
			"reported_by": _REPORTER,
			"investigation_notes": "Maintenance log shows a compressor fault similar to the Warehouse B excursion.",
			"root_cause": "Compressor thermostat drift beyond calibration tolerance — same failure mode as Warehouse B.",
		}
	)
	dev.insert(ignore_permissions=True)
	return dev.name, True


def _ensure_unrelated_deviation():
	existing = frappe.db.get_value("QMS Deviation", {"subject": _UNRELATED_DEVIATION_SUBJECT}, "name")
	if existing:
		return existing, False
	dev = frappe.get_doc(
		{
			"doctype": "QMS Deviation",
			"subject": _UNRELATED_DEVIATION_SUBJECT,
			"description": "Secondary packaging line printed the wrong lot number on outer cartons for one shift.",
			"severity": "Minor",
			"status": "Under Investigation",
			"reported_by": _REPORTER,
			"investigation_notes": "Print head alignment drifted after a routine changeover.",
			"root_cause": "Printhead alignment fault following a component changeover on the labeling line.",
		}
	)
	dev.insert(ignore_permissions=True)
	return dev.name, True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_qms_copilot():
	"""Phase 6A / AI-DEMO-02 — registers the 3 new AI Tools, the qms_copilot_synthesis Prompt
	Template + AI Action (reusing the existing, unmodified CE-13 AI foundation router/policy/
	logging), and the extra similarity-proof Deviation data. Depends on Golden Demo #2/#3's own
	QMS seeds (`seed_deviation_capa_flow`, `seed_qms_audit`) already having run — called
	defensively here (idempotent) rather than assumed."""
	base_flow = seed_deviation_capa_flow()
	audit_flow = seed_qms_audit()
	tools_created = _ensure_ai_tools()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	similar_name, similar_created = _ensure_similar_deviation()
	unrelated_name, unrelated_created = _ensure_unrelated_deviation()
	return (
		f"seed_ai_qms_copilot: base QMS flow: '{base_flow}' '{audit_flow}' "
		f"AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"Similar-deviation control {'created' if similar_created else 'already existed'} ({similar_name}). "
		f"Unrelated-deviation control {'created' if unrelated_created else 'already existed'} ({unrelated_name})."
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _base_deviation_name():
	name = frappe.db.get_value("QMS Deviation", {"subject": "Cold storage temperature excursion — Warehouse B"}, "name")
	if not name:
		frappe.throw("AI-DEMO-02 validation setup FAILED: base Deviation (Warehouse B) not found — run seed_deviation_capa_flow() first.")
	return name


def _capa_draft_deviation_name():
	"""draft_capa's own base deviation is deliberately the AI-DEMO-02-owned 'Warehouse C'
	similarity-control record, NOT the shared Warehouse B flagship deviation. Golden Demo #2/#3's
	OWN `qms_seeds._ensure_capa_for_deviation()` does an un-ordered
	`frappe.db.get_value("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": ...})`
	lookup against Warehouse B assuming AT MOST ONE CAPA exists for it — a real bug found during
	this build: repeatedly approving draft_capa AI Drafts against Warehouse B created several
	extra CAPAs sharing that same (source_type, source_reference) key, which made THAT unrelated,
	pre-existing lookup nondeterministically pick up one of the fresh AI-approved CAPAs instead of
	the golden demo's own flagship CAPA and silently close it. Every AI Draft/QMS CAPA this demo's
	own validations create is append-only (same precedent as AI Job Log), so repeated runs must
	target a deviation nothing else assumes uniqueness over — Warehouse C, owned exclusively by
	this demo, is that record."""
	name = frappe.db.get_value("QMS Deviation", {"subject": _SIMILAR_DEVIATION_SUBJECT}, "name")
	if not name:
		frappe.throw("AI-DEMO-02 validation setup FAILED: Warehouse C similarity-control Deviation not found — run seed_ai_qms_copilot() first.")
	return name


def _base_audit_name():
	name = frappe.db.get_value("QMS Audit", {"subject": "Internal GMP Audit — Q3 2026"}, "name")
	if not name:
		frappe.throw("AI-DEMO-02 validation setup FAILED: base Audit not found — run seed_qms_audit() first.")
	return name


def _test_all_use_cases_answer():
	"""Every one of the 5 example use cases runs end-to-end: real tool data, mock AI
	interpretation, AND a persisted AI Draft that starts life as 'Draft' (never auto-approved)."""
	deviation = _base_deviation_name()
	audit = _base_audit_name()
	source_ref_by_use_case = {
		"summarize_deviation": deviation,
		"find_similar_deviation": deviation,
		"suggest_investigation_questions": deviation,
		"draft_capa": _capa_draft_deviation_name(),  # NOT the shared Warehouse B deviation — see _capa_draft_deviation_name() docstring.
		"summarize_audit_finding": audit,
	}
	results = {}
	for use_case, expected_tools in USE_CASE_TOOL_MAP.items():
		source_reference = source_ref_by_use_case[use_case]
		resp = run_qms_copilot(use_case, source_reference, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if not resp.get("data_facts") or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': data_facts missing tool output.")
		suggestion = resp.get("ai_suggestion") or {}
		if not suggestion.get("text"):
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': no ai_suggestion.text returned.")
		if suggestion.get("requires_human_approval") is not True:
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': ai_suggestion.requires_human_approval is not True.")
		if suggestion.get("approval_status") != "Draft":
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': new AI Draft approval_status={suggestion.get('approval_status')!r}, expected 'Draft' (must never auto-approve).")
		draft_name = suggestion.get("draft")
		if not draft_name or not frappe.db.exists("AI Draft", draft_name):
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': no AI Draft record was persisted.")
		if frappe.db.get_value("AI Draft", draft_name, "status") != "Draft":
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': persisted AI Draft {draft_name} is not in 'Draft' status.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-02 smoke test FAILED for '{use_case}': no AI Job Log entry written.")
		results[use_case] = resp
	return results


def _test_similarity_finds_real_match():
	"""The similarity search over real Deviation data finds the genuinely similar Warehouse C
	deviation, states a real similarity basis (shared keywords / severity match — not a
	black-box score), and correctly does NOT surface the unrelated packaging-label deviation."""
	deviation = _base_deviation_name()
	resp = run_qms_copilot("find_similar_deviation", deviation, user="Administrator")
	candidates = resp["data_facts"]["find_similar_deviations"]["candidates"]
	similar_name = frappe.db.get_value("QMS Deviation", {"subject": _SIMILAR_DEVIATION_SUBJECT}, "name")
	unrelated_name = frappe.db.get_value("QMS Deviation", {"subject": _UNRELATED_DEVIATION_SUBJECT}, "name")
	candidate_names = {c["deviation"] for c in candidates}
	if similar_name not in candidate_names:
		frappe.throw(f"AI-DEMO-02 similarity test FAILED: genuinely similar Deviation {similar_name} was NOT found as a candidate. Got: {candidate_names}")
	if unrelated_name in candidate_names:
		frappe.throw(f"AI-DEMO-02 similarity test FAILED: unrelated Deviation {unrelated_name} was incorrectly flagged as similar.")
	matched = next(c for c in candidates if c["deviation"] == similar_name)
	if not matched["shared_keywords"]:
		frappe.throw(f"AI-DEMO-02 similarity test FAILED: matched candidate {similar_name} has no stated shared_keywords (basis not explainable).")
	if not matched["same_severity"]:
		frappe.throw(f"AI-DEMO-02 similarity test FAILED: matched candidate {similar_name} expected same_severity=True (both Major).")
	return f"similarity CONFIRMED: {similar_name} matched via {matched['shared_keywords']}, {unrelated_name} correctly excluded."


def _test_mandatory_capa_approval():
	"""THE defining acceptance-criteria proof for this demo:
	  (a) a draft_capa AI Draft cannot become a real QMS CAPA without an explicit approve_capa_draft() call.
	  (b) an unapproved (freshly-created) / rejected draft is clearly distinguishable (status) from an approved one, and NO CAPA exists for the rejected one.
	  (c) the approval is attributable to a specific real human user (quality.director), never the AI / never left blank.
	  (d) DocType-level guard rails fire: cannot self-approve (flip status without reviewed_by via a raw save), cannot re-decide an already-decided draft.
	"""
	deviation = _capa_draft_deviation_name()  # NOT the shared Warehouse B deviation — see _capa_draft_deviation_name() docstring.

	# (a) fresh draft_capa is Draft, no CAPA minted yet. Uses a before/after COUNT for this
	# specific deviation rather than "does a CAPA with the suggested subject exist" — this
	# validation function is re-run repeatedly (AI Draft/QMS CAPA are append-only, like AI Job
	# Log), so a subject-existence check would false-positive-fail from a PRIOR run's already-
	# approved CAPA with the same deterministic subject. A count captured immediately before
	# THIS approval call is robust to that.
	capa_count_before_approval = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation})
	resp = run_qms_copilot("draft_capa", deviation, user="Administrator")
	draft_name = resp["ai_suggestion"]["draft"]
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.status != "Draft":
		frappe.throw(f"AI-DEMO-02 approval test FAILED: freshly-created draft_capa {draft_name} status={draft.status!r}, expected 'Draft'.")
	if draft.resulting_reference:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: freshly-created draft {draft_name} already has resulting_reference={draft.resulting_reference!r} — should be empty until approved.")
	capa_count_before_this_draft_decided = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation})
	if capa_count_before_this_draft_decided != capa_count_before_approval:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: creating draft {draft_name} itself changed the QMS CAPA count ({capa_count_before_approval} -> {capa_count_before_this_draft_decided}) — a draft must never create a record on its own.")

	# approve -> real CAPA minted, attributable to a real human reviewer.
	capa_name = approve_capa_draft(draft_name, reviewed_by=_REVIEWER, review_notes="Reviewed against the Warehouse B/C cold-chain pattern — approved as-is.")
	if not frappe.db.exists("QMS CAPA", capa_name):
		frappe.throw(f"AI-DEMO-02 approval test FAILED: approve_capa_draft() reported CAPA {capa_name} but it does not exist.")
	capa_count_after_approval = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation})
	if capa_count_after_approval != capa_count_before_approval + 1:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: approving draft {draft_name} should create EXACTLY one new CAPA ({capa_count_before_approval} -> expected {capa_count_before_approval + 1}, got {capa_count_after_approval}).")
	draft.reload()
	if draft.status != "Approved":
		frappe.throw(f"AI-DEMO-02 approval test FAILED: draft {draft_name} status={draft.status!r} after approval, expected 'Approved'.")
	if draft.resulting_reference != capa_name:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: draft {draft_name} resulting_reference={draft.resulting_reference!r}, expected {capa_name!r}.")
	if draft.reviewed_by != _REVIEWER:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: draft {draft_name} reviewed_by={draft.reviewed_by!r}, expected {_REVIEWER!r} (a specific real human, not the AI).")
	if not draft.reviewed_on:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: draft {draft_name} has no reviewed_on timestamp.")
	log = frappe.db.get_value("AI Job Log", draft.generated_by_job_log, ["accepted", "final_record_reference"], as_dict=True)
	if not log or not log.accepted or log.final_record_reference != capa_name:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: AI Job Log {draft.generated_by_job_log} not updated with accepted=1/final_record_reference={capa_name!r}. Got: {log}")

	# (b) a SECOND draft_capa, rejected -> clearly distinguishable, NO CAPA created.
	resp2 = run_qms_copilot("draft_capa", deviation, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	capa_count_before_reject = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation})
	reject_capa_draft(draft2_name, reviewed_by=_REVIEWER, review_notes="Duplicate of an already-approved CAPA for this deviation — rejected.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	if draft2.status != "Rejected":
		frappe.throw(f"AI-DEMO-02 approval test FAILED: draft2 {draft2_name} status={draft2.status!r}, expected 'Rejected'.")
	if draft2.resulting_reference:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: rejected draft {draft2_name} has resulting_reference={draft2.resulting_reference!r} — a rejected draft must NEVER produce a real record.")
	capa_count_after_reject = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation})
	if capa_count_after_reject != capa_count_before_reject:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: rejecting draft {draft2_name} changed the QMS CAPA count ({capa_count_before_reject} -> {capa_count_after_reject}) — a rejected draft created a record.")
	if draft.status == draft2.status:
		frappe.throw("AI-DEMO-02 approval test FAILED: approved and rejected drafts report the SAME status — not distinguishable.")

	# (d) guard rail: cannot self-approve (flip status without reviewed_by) via a raw save.
	guard_draft = create_ai_draft(
		copilot_code="qms_copilot",
		use_case="draft_capa",
		source_doctype="QMS Deviation",
		source_reference=deviation,
		content="[AI-DEMO-02 negative test draft — should never reach Approved without reviewed_by.]",
	)
	guard_draft.status = "Approved"  # deliberately no reviewed_by set
	blocked = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: AI Draft {guard_draft.name} was saved as Approved WITHOUT reviewed_by — self-approval guard did not fire.")

	# (d) guard rail: cannot re-decide an already-decided draft.
	blocked_redecision = False
	try:
		reject_capa_draft(draft_name, reviewed_by=_REVIEWER, review_notes="Attempting to re-decide an already-Approved draft.")
	except frappe.ValidationError:
		blocked_redecision = True
	if not blocked_redecision:
		frappe.throw(f"AI-DEMO-02 approval test FAILED: an already-Approved draft {draft_name} was re-decided to Rejected — finality guard did not fire.")

	return (
		f"mandatory-approval CONFIRMED: draft {draft_name} approved by {_REVIEWER} -> real CAPA {capa_name} minted "
		f"only after approval; draft {draft2_name} rejected -> no CAPA created (count stayed {capa_count_before_reject}); "
		f"self-approval guard and re-decision guard both fired as expected."
	)


def _test_non_capa_approval_no_new_record():
	"""The other 4 use cases: approval endorses the draft text but does NOT mint any new
	record — proves the CAPA-specific 'convert to real record' behavior is NOT the default for
	every use case, it's specific to draft_capa."""
	deviation = _base_deviation_name()
	resp = run_qms_copilot("summarize_deviation", deviation, user="Administrator")
	draft_name = resp["ai_suggestion"]["draft"]
	approve_ai_suggestion(draft_name, reviewed_by=_REVIEWER, review_notes="Accurate summary, endorsed.")
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.status != "Approved":
		frappe.throw(f"AI-DEMO-02 non-CAPA approval test FAILED: draft {draft_name} status={draft.status!r}, expected 'Approved'.")
	if draft.resulting_reference:
		frappe.throw(f"AI-DEMO-02 non-CAPA approval test FAILED: draft {draft_name} unexpectedly has resulting_reference={draft.resulting_reference!r} — summarize_deviation approval must not mint a new record.")
	if draft.reviewed_by != _REVIEWER:
		frappe.throw(f"AI-DEMO-02 non-CAPA approval test FAILED: draft {draft_name} reviewed_by={draft.reviewed_by!r}, expected {_REVIEWER!r}.")
	return f"non-CAPA approval CONFIRMED: draft {draft_name} approved by {_REVIEWER}, no new record minted."


def seed_ai_qms_copilot_validations():
	"""Runs all 4 validations end-to-end: 5-use-case smoke test, real similarity match +
	negative control, the mandatory CAPA-approval proof (the defining acceptance criterion),
	and the non-CAPA approval-without-new-record proof."""
	smoke = _test_all_use_cases_answer()
	similarity = _test_similarity_finds_real_match()
	capa_approval = _test_mandatory_capa_approval()
	non_capa_approval = _test_non_capa_approval_no_new_record()
	return (
		f"seed_ai_qms_copilot_validations: all {len(smoke)} use cases ran end-to-end, always starting as 'Draft'. "
		f"{similarity} {capa_approval} {non_capa_approval}"
	)
