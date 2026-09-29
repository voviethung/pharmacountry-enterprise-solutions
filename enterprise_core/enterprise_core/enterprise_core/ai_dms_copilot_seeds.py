"""Phase 6A — AI-DEMO-03 (DMS Copilot) seed data + validations. Registers the 4 new `AI Tool`
rows this demo adds to the SAME registry AI-DEMO-01/02 built (`compare_document_revisions`,
`suggest_impacted_documents`, `suggest_training_impact`, `search_effective_documents`), the
`dms_copilot_synthesis` Prompt Template/AI Action, 4 additional `DMS Document` records needed
to give `suggest_impacted_documents()` a genuine same-department+same-type match, a
same-department-only match, a same-type-only match, AND a genuine negative control (Golden
Demo #4's own seed data has exactly ONE document — SOP-WH-02 — so there is nothing to relate it
to without this), plus marking 2 of Golden Demo #4's OWN already-auto-created `DMS Training
Assignment` rows as completed (so `suggest_training_impact()` has a genuine non-empty
"needs retraining" answer instead of a trivially-empty one). Validations prove: all 5 use cases
run end-to-end, the revision comparison finds a real field-level diff, the impacted-documents
proxy correctly includes/excludes candidates by its stated basis, the training-impact tool
surfaces the real completed-training users, the Q&A search correctly excludes an Obsolete
version that matches the SAME keywords as an Effective one (the defining acceptance criterion
for this demo, directly mirroring the master plan's own RAG "Obsolete doc not used as current"
requirement), and — mirroring AI-DEMO-02's own mandatory-approval proof — that approval/
rejection are attributable to a real human reviewer, mint no new record for any of the 5 use
cases, and the DocType-level guard rails (no self-approval, no re-deciding a finalized draft)
actually fire.
"""

import frappe

from enterprise_core.enterprise_core.ai_dms_copilot import (
	USE_CASE_TOOL_MAP,
	approve_dms_draft,
	reject_dms_draft,
	run_dms_copilot,
)
from enterprise_core.enterprise_core.ai_drafts import create_ai_draft
from enterprise_core.enterprise_core.dms_seeds import (
	seed_dms_document_lifecycle,
	seed_dms_revision,
	seed_dms_validations,
)

_BASE_DOCUMENT = "SOP-WH-02"
_REVIEWER = "quality.director@pharmacountry.vn"

# Users this demo marks as having COMPLETED training on SOP-WH-02's current Effective version
# (v2) — real, pre-existing `DMS Training Assignment` rows (auto-created by
# `dms_validations.dms_document_version_on_update()` for every @pharmacountry.vn user when v2
# went Effective), just flipped `completed=1` here so `suggest_training_impact()` has a
# genuinely non-empty "needs retraining" answer to surface, rather than fabricating new rows.
_TRAINED_USERS = ["warehouse.officer@pharmacountry.vn", "qa.manager@pharmacountry.vn"]

# (document_code, title, doc_type, department) — 4 new documents, none of which existed in
# Golden Demo #4's own seed data (confirmed by reading dms_seeds.py first: it seeds exactly one
# document, SOP-WH-02). Deliberately span all 4 relationship-basis combinations relative to
# SOP-WH-02 (doc_type="SOP", department="Warehouse"):
_IMPACT_DOCS = [
	("SOP-WH-05", "Warehouse Receiving Inspection", "SOP", "Warehouse"),  # same dept + same type
	("FORM-WH-01", "Warehouse Temperature Log Form", "Form", "Warehouse"),  # same dept only
	("SOP-QA-01", "QA Batch Release Review", "SOP", "Quality Assurance"),  # same type only
	("POLICY-HR-01", "Employee Onboarding Policy", "Policy", "Human Resources"),  # negative control — shares neither
]


# ---------------------------------------------------------------------------
# AI Tool registry additions (4 tools, appended to AI-DEMO-01/02's registry)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"compare_document_revisions",
		"Compare Document Revisions",
		"Real field-level diff between two DMS Document Version records of the same DMS Document (Golden Demo #4 DMS).",
		"enterprise_core.enterprise_core.ai_tools.compare_document_revisions",
		"DMS Document Version",
	),
	(
		"suggest_impacted_documents",
		"Suggest Impacted Documents",
		"Real relationship-based lookup (same department and/or same document type) over DMS Document — no black-box score, states its basis.",
		"enterprise_core.enterprise_core.ai_tools.suggest_impacted_documents",
		"DMS Document",
	),
	(
		"suggest_training_impact",
		"Suggest Training Impact",
		"Real query over DMS Training Assignment for a document's current Effective version — who already completed training and would need retraining.",
		"enterprise_core.enterprise_core.ai_tools.suggest_training_impact",
		"DMS Training Assignment",
	),
	(
		"search_effective_documents",
		"Search Effective Documents",
		"Non-vector keyword search restricted to Effective DMS Document Version records only — Obsolete/Draft matches are computed but never returned as usable sources.",
		"enterprise_core.enterprise_core.ai_tools.search_effective_documents",
		"DMS Document Version",
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
	if frappe.db.exists("Prompt Template", {"template_code": "dms_copilot_synthesis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "dms_copilot_synthesis",
			"version": 1,
			"system_instruction": (
				"You are a Document Management System copilot assisting with one of 5 approved use cases "
				"(compare SOP revisions, create a change summary, suggest impacted documents, suggest "
				"training impact, answer a question over EFFECTIVE controlled documents only). You are "
				"given REAL, tool-sourced structured DMS data as context — never invent facts, never fetch "
				"additional data yourself, never run or suggest SQL, and never treat an Obsolete or Draft "
				"document as a current source. Your output is ALWAYS a draft/suggestion for a qualified "
				"human reviewer — it is never final, never auto-approved, and never itself a substitute for "
				"the underlying data facts, which are returned and logged separately."
			),
			"input_schema": frappe.as_json({"use_case": "string", "source_reference": "string", "<tool_code>": "object (tool-specific structured data)"}),
			"output_schema": frappe.as_json({"draft": "string — a suggestion requiring human approval, never auto-final"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", "dms_copilot_synthesis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "dms_copilot_synthesis",
			"description": "AI-DEMO-03 DMS Copilot — synthesizes a draft/suggestion over real DMS tool output for one of 5 approved use cases. Output always requires human approval (never auto-final).",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "dms_copilot_synthesis", "version": 1}, "name"),
			"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS),
			"human_review_required": 1,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Extra demo Documents — needed so suggest_impacted_documents() has real matches across all 4
# relationship-basis combinations plus a genuine negative control.
# ---------------------------------------------------------------------------

def _ensure_impact_docs():
	created = []
	for document_code, title, doc_type, department in _IMPACT_DOCS:
		if frappe.db.exists("DMS Document", document_code):
			continue
		frappe.get_doc(
			{
				"doctype": "DMS Document",
				"document_code": document_code,
				"title": title,
				"doc_type": doc_type,
				"department": department,
				"status": "Effective",
				"requires_training": 0,
			}
		).insert(ignore_permissions=True)
		created.append(document_code)
	return created


def _ensure_training_completed():
	"""Flips completed=1 on 2 of SOP-WH-02's already-auto-created Training Assignment rows for
	its current Effective version — a direct field update on EXISTING rows (never creates a new
	row), safe to call every re-run."""
	current_version = frappe.db.get_value("DMS Document", _BASE_DOCUMENT, "current_version")
	if not current_version:
		return []
	updated = []
	for user in _TRAINED_USERS:
		assignment = frappe.db.get_value("DMS Training Assignment", {"document_version": current_version, "user": user}, ["name", "completed"], as_dict=True)
		if not assignment:
			continue  # dms_seeds hasn't run yet for this user — seed_ai_dms_copilot() calls it defensively before this
		if not assignment.completed:
			frappe.db.set_value("DMS Training Assignment", assignment.name, {"completed": 1, "completed_date": frappe.utils.nowdate()})
			updated.append(user)
	return updated


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_dms_copilot():
	"""Phase 6A / AI-DEMO-03 — registers the 4 new AI Tools, the dms_copilot_synthesis Prompt
	Template + AI Action (reusing the existing, unmodified CE-13 AI foundation router/policy/
	logging), the extra relationship-proof Documents, and marks 2 real training assignments
	completed. Depends on Golden Demo #4's own DMS seeds (`seed_dms_document_lifecycle`,
	`seed_dms_revision`, `seed_dms_validations`) already having run — called defensively here
	(idempotent) rather than assumed, exactly like AI-DEMO-02 does for its own QMS base seeds."""
	lifecycle = seed_dms_document_lifecycle()
	revision = seed_dms_revision()
	dms_validations_result = seed_dms_validations()
	tools_created = _ensure_ai_tools()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	impact_docs_created = _ensure_impact_docs()
	training_marked = _ensure_training_completed()
	return (
		f"seed_ai_dms_copilot: base DMS flow: '{lifecycle}' '{revision}' '{dms_validations_result}' "
		f"AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"Impact-proof documents created: {impact_docs_created or 'none (already existed)'}. "
		f"Training marked completed for: {training_marked or 'none (already completed or version not yet Effective)'}."
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _current_version_name():
	name = frappe.db.get_value("DMS Document", _BASE_DOCUMENT, "current_version")
	if not name:
		frappe.throw(f"AI-DEMO-03 validation setup FAILED: {_BASE_DOCUMENT} has no current_version — run seed_ai_dms_copilot() first.")
	return name


def _test_all_use_cases_answer():
	"""Every one of the 5 use cases runs end-to-end: real tool data, mock AI interpretation,
	AND a persisted AI Draft that starts life as 'Draft' (never auto-approved)."""
	source_ref_by_use_case = {
		"compare_sop_revisions": _BASE_DOCUMENT,
		"create_change_summary": _BASE_DOCUMENT,
		"suggest_impacted_documents": _BASE_DOCUMENT,
		"suggest_training_impact": _BASE_DOCUMENT,
		"qa_effective_documents": "cold storage logs",
	}
	results = {}
	for use_case, expected_tools in USE_CASE_TOOL_MAP.items():
		source_reference = source_ref_by_use_case[use_case]
		resp = run_dms_copilot(use_case, source_reference, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if not resp.get("data_facts") or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': data_facts missing tool output.")
		suggestion = resp.get("ai_suggestion") or {}
		if not suggestion.get("text"):
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': no ai_suggestion.text returned.")
		if suggestion.get("requires_human_approval") is not True:
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': ai_suggestion.requires_human_approval is not True.")
		if suggestion.get("approval_status") != "Draft":
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': new AI Draft approval_status={suggestion.get('approval_status')!r}, expected 'Draft' (must never auto-approve).")
		draft_name = suggestion.get("draft")
		if not draft_name or not frappe.db.exists("AI Draft", draft_name):
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': no AI Draft record was persisted.")
		if frappe.db.get_value("AI Draft", draft_name, "status") != "Draft":
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': persisted AI Draft {draft_name} is not in 'Draft' status.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-03 smoke test FAILED for '{use_case}': no AI Job Log entry written.")
		results[use_case] = resp
	return results


def _test_compare_finds_real_diff():
	"""compare_document_revisions() over SOP-WH-02's real v1 (Obsolete) -> v2 (Effective)
	revision finds a genuine field-level diff, including the content_summary and status fields
	that Golden Demo #4's own seed data actually changed between them."""
	resp = run_dms_copilot("compare_sop_revisions", _BASE_DOCUMENT, user="Administrator")
	cmp_data = resp["data_facts"]["compare_document_revisions"]
	if cmp_data["version_a"]["version_no"] != 1 or cmp_data["version_b"]["version_no"] != 2:
		frappe.throw(f"AI-DEMO-03 compare test FAILED: expected version_a=1/version_b=2, got {cmp_data['version_a']} / {cmp_data['version_b']}.")
	changed_fields = {c["field"] for c in cmp_data["fields_changed"]}
	if "content_summary" not in changed_fields:
		frappe.throw(f"AI-DEMO-03 compare test FAILED: content_summary not detected as changed between v1 and v2. Got: {changed_fields}")
	if "status" not in changed_fields:
		frappe.throw(f"AI-DEMO-03 compare test FAILED: status not detected as changed between v1 and v2. Got: {changed_fields}")
	return f"compare CONFIRMED: v1->v2 diff found {cmp_data['change_count']} changed field(s): {sorted(changed_fields)}."


def _test_impacted_documents_relationship():
	"""suggest_impacted_documents() over SOP-WH-02 (doc_type=SOP, department=Warehouse) finds
	the same-dept+same-type match, the same-dept-only match, and the same-type-only match, each
	with the correct stated basis — and correctly EXCLUDES the negative-control document that
	shares neither."""
	resp = run_dms_copilot("suggest_impacted_documents", _BASE_DOCUMENT, user="Administrator")
	candidates = {c["document"]: c for c in resp["data_facts"]["suggest_impacted_documents"]["impacted_documents"]}
	if "SOP-WH-05" not in candidates or sorted(candidates["SOP-WH-05"]["relationship_basis"]) != ["same department", "same document type"]:
		frappe.throw(f"AI-DEMO-03 impacted-documents test FAILED: SOP-WH-05 (dept+type match) basis wrong or missing. Got: {candidates.get('SOP-WH-05')}")
	if "FORM-WH-01" not in candidates or candidates["FORM-WH-01"]["relationship_basis"] != ["same department"]:
		frappe.throw(f"AI-DEMO-03 impacted-documents test FAILED: FORM-WH-01 (dept-only match) basis wrong or missing. Got: {candidates.get('FORM-WH-01')}")
	if "SOP-QA-01" not in candidates or candidates["SOP-QA-01"]["relationship_basis"] != ["same document type"]:
		frappe.throw(f"AI-DEMO-03 impacted-documents test FAILED: SOP-QA-01 (type-only match) basis wrong or missing. Got: {candidates.get('SOP-QA-01')}")
	if "POLICY-HR-01" in candidates:
		frappe.throw(f"AI-DEMO-03 impacted-documents test FAILED: negative-control POLICY-HR-01 was incorrectly flagged as impacted. Got: {candidates.get('POLICY-HR-01')}")
	return f"impacted-documents CONFIRMED: {sorted(candidates)} correctly related to {_BASE_DOCUMENT}; POLICY-HR-01 correctly excluded."


def _test_training_impact_real_data():
	"""suggest_training_impact() over SOP-WH-02's current Effective version surfaces the real,
	pre-existing (not fabricated) Training Assignment data — both trained users this demo marked
	completed are reported as needing retraining."""
	resp = run_dms_copilot("suggest_training_impact", _BASE_DOCUMENT, user="Administrator")
	impact = resp["data_facts"]["suggest_training_impact"]
	needing = {u["user"] for u in impact["users_needing_retraining"]}
	missing = set(_TRAINED_USERS) - needing
	if missing:
		frappe.throw(f"AI-DEMO-03 training-impact test FAILED: expected {_TRAINED_USERS} in users_needing_retraining, missing {missing}. Got: {needing}")
	if impact.get("current_version") != _current_version_name():
		frappe.throw(f"AI-DEMO-03 training-impact test FAILED: current_version={impact.get('current_version')!r}, expected {_current_version_name()!r}.")
	return f"training-impact CONFIRMED: {sorted(needing)} correctly surfaced as needing retraining for {_BASE_DOCUMENT}'s current version."


def _test_qa_effective_documents_excludes_obsolete():
	"""THE defining acceptance-criteria proof for this demo, directly mirroring the master
	plan's own RAG 'Obsolete doc not used as current' requirement: searching for keywords that
	appear in BOTH SOP-WH-02's Obsolete v1 content ('Review cold storage logs weekly.') AND its
	Effective v2 content ('...cold storage logs daily...') returns ONLY v2 as a usable source —
	v1 is still found (proving the search itself works and isn't just silently missing it) but
	is reported exclusively in obsolete_or_draft_matches_excluded, never in results."""
	resp = run_dms_copilot("qa_effective_documents", "cold storage logs", user="Administrator")
	qa = resp["data_facts"]["search_effective_documents"]
	v1_name = frappe.db.get_value("DMS Document Version", {"document": _BASE_DOCUMENT, "version_no": 1}, "name")
	v2_name = frappe.db.get_value("DMS Document Version", {"document": _BASE_DOCUMENT, "version_no": 2}, "name")
	result_versions = {r["version"] for r in qa["results"]}
	excluded_versions = {r["version"] for r in qa["obsolete_or_draft_matches_excluded"]}
	if v2_name not in result_versions:
		frappe.throw(f"AI-DEMO-03 Q&A test FAILED: Effective v2 ({v2_name}) not found in results. Got results: {result_versions}")
	if v1_name in result_versions:
		frappe.throw(f"AI-DEMO-03 Q&A test FAILED: Obsolete v1 ({v1_name}) was incorrectly returned as a usable Q&A source. Got results: {result_versions}")
	if v1_name not in excluded_versions:
		frappe.throw(f"AI-DEMO-03 Q&A test FAILED: Obsolete v1 ({v1_name}) should appear in obsolete_or_draft_matches_excluded (proving it matched but was correctly excluded), got: {excluded_versions}")
	return f"Q&A-effective-only CONFIRMED: query 'cold storage logs' matched BOTH v1 (Obsolete) and v2 (Effective); only v2 ({v2_name}) returned as a source, v1 ({v1_name}) correctly excluded."


def _test_approval_and_guard_rails():
	"""Mirrors AI-DEMO-02's mandatory-approval proof, adapted for DMS Copilot's structural
	distinction: NONE of its 5 use cases mint a new record on approval (checked directly), but
	approval/rejection are still attributable to a real human reviewer and the same DocType-
	level guard rails (no self-approval, no re-deciding a finalized draft) still fire."""
	resp = run_dms_copilot("compare_sop_revisions", _BASE_DOCUMENT, user="Administrator")
	draft_name = resp["ai_suggestion"]["draft"]
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.status != "Draft":
		frappe.throw(f"AI-DEMO-03 approval test FAILED: freshly-created draft {draft_name} status={draft.status!r}, expected 'Draft'.")
	if draft.resulting_reference:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: freshly-created draft {draft_name} already has resulting_reference={draft.resulting_reference!r} — should always be empty for DMS Copilot.")

	approve_dms_draft(draft_name, reviewed_by=_REVIEWER, review_notes="Reviewed against the real v1/v2 diff — approved as-is.")
	draft.reload()
	if draft.status != "Approved":
		frappe.throw(f"AI-DEMO-03 approval test FAILED: draft {draft_name} status={draft.status!r} after approval, expected 'Approved'.")
	if draft.resulting_reference:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: approved draft {draft_name} unexpectedly has resulting_reference={draft.resulting_reference!r} — DMS Copilot approval must NEVER mint a new record.")
	if draft.reviewed_by != _REVIEWER:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: draft {draft_name} reviewed_by={draft.reviewed_by!r}, expected {_REVIEWER!r} (a specific real human, not the AI).")
	if not draft.reviewed_on:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: draft {draft_name} has no reviewed_on timestamp.")

	# A second draft, rejected -> clearly distinguishable, still no record minted.
	resp2 = run_dms_copilot("compare_sop_revisions", _BASE_DOCUMENT, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	reject_dms_draft(draft2_name, reviewed_by=_REVIEWER, review_notes="Duplicate review — rejected.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	if draft2.status != "Rejected":
		frappe.throw(f"AI-DEMO-03 approval test FAILED: draft2 {draft2_name} status={draft2.status!r}, expected 'Rejected'.")
	if draft2.resulting_reference:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: rejected draft {draft2_name} unexpectedly has resulting_reference={draft2.resulting_reference!r}.")
	if draft.status == draft2.status:
		frappe.throw("AI-DEMO-03 approval test FAILED: approved and rejected drafts report the SAME status — not distinguishable.")

	# copilot_code guard: cannot approve/reject a foreign (e.g. qms_copilot) draft through this module.
	foreign_draft = create_ai_draft(
		copilot_code="qms_copilot",
		use_case="summarize_deviation",
		source_doctype="QMS Deviation",
		source_reference=None,
		content="[AI-DEMO-03 negative test — a foreign-copilot draft that must be refused by approve_dms_draft().]",
	)
	foreign_blocked = False
	try:
		approve_dms_draft(foreign_draft.name, reviewed_by=_REVIEWER)
	except frappe.ValidationError:
		foreign_blocked = True
	if not foreign_blocked:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: approve_dms_draft() approved a FOREIGN copilot's draft {foreign_draft.name} — copilot_code guard did not fire.")

	# DocType-level guard rail: cannot self-approve (flip status without reviewed_by) via a raw save.
	guard_draft = create_ai_draft(
		copilot_code="dms_copilot",
		use_case="compare_sop_revisions",
		source_doctype="DMS Document",
		source_reference=_BASE_DOCUMENT,
		content="[AI-DEMO-03 negative test draft — should never reach Approved without reviewed_by.]",
	)
	guard_draft.status = "Approved"  # deliberately no reviewed_by set
	self_approval_blocked = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		self_approval_blocked = True
	if not self_approval_blocked:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: AI Draft {guard_draft.name} was saved as Approved WITHOUT reviewed_by — self-approval guard did not fire.")

	# DocType-level guard rail: cannot re-decide an already-decided draft.
	redecision_blocked = False
	try:
		reject_dms_draft(draft_name, reviewed_by=_REVIEWER, review_notes="Attempting to re-decide an already-Approved draft.")
	except frappe.ValidationError:
		redecision_blocked = True
	if not redecision_blocked:
		frappe.throw(f"AI-DEMO-03 approval test FAILED: an already-Approved draft {draft_name} was re-decided to Rejected — finality guard did not fire.")

	return (
		f"approval CONFIRMED: draft {draft_name} approved by {_REVIEWER} with NO new record minted; "
		f"draft {draft2_name} rejected -> also no record; foreign-copilot guard, self-approval guard, "
		f"and re-decision guard all fired as expected."
	)


def seed_ai_dms_copilot_validations():
	"""Runs all 6 validations end-to-end: 5-use-case smoke test, the real revision-diff proof,
	the impacted-documents relationship proof, the training-impact real-data proof, THE
	effective-vs-obsolete Q&A exclusion proof, and the approval/guard-rail proof (adapted for
	DMS Copilot's own no-new-record structural distinction)."""
	smoke = _test_all_use_cases_answer()
	compare = _test_compare_finds_real_diff()
	impacted = _test_impacted_documents_relationship()
	training = _test_training_impact_real_data()
	qa = _test_qa_effective_documents_excludes_obsolete()
	approval = _test_approval_and_guard_rails()
	return (
		f"seed_ai_dms_copilot_validations: all {len(smoke)} use cases ran end-to-end, always starting as 'Draft'. "
		f"{compare} {impacted} {training} {qa} {approval}"
	)
