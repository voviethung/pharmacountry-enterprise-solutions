"""Phase 6A — shared `AI Draft` mechanism (master plan §19E / principle #24, line ~3690:
"AI output ở regulated workflow mặc định là suggestion/draft, không auto-final approval" — AI
output in a regulated workflow defaults to suggestion/draft, never auto-final-approval).

Deliberately GENERIC and copilot-agnostic — AI-DEMO-02 (QMS Copilot) is the first consumer
(`ai_qms_copilot.py`), but nothing here mentions QMS. A future DMS Copilot (AI-DEMO-03) or any
other Phase 6A item that needs "AI produced a draft, a real human must review it before it
counts" reuses this SAME `AI Draft` DocType and these SAME two functions rather than building
its own parallel draft/approval table — the whole point of building this now instead of
QMS-specific schema.

Two structural guarantees, enforced in `ai_draft_validate()` (wired via `hooks.py` doc_events on
"AI Draft", not just left to caller discipline — the exact style already used for QMS's own
Q01/Q02/Q04 in `qms_validations.py`):
  1. A draft cannot leave 'Draft' status without `reviewed_by` on record — i.e. it is
     structurally impossible for the AI's own output to self-approve; some real User docname
     must be attached, and Frappe's Link field already guarantees that name resolves to a real
     User record, never a placeholder string.
  2. Once a draft has been decided (Approved/Rejected), that decision cannot be silently
     re-flipped by a later save — matches CAPA's own closed-status finality expectations
     elsewhere in this codebase.

`decide_ai_draft()` is the one generic helper for the 4 "reviewed, no new record minted" use
cases (a copilot's summarize/interpret-only drafts). A copilot that needs approval to ALSO
create a new business record (like QMS Copilot's draft_capa -> real QMS CAPA) does NOT use this
helper directly — it does its own atomic decide+create (see
`ai_qms_copilot.approve_capa_draft()`) so the new record and the draft's Approved status are
never left half-done relative to each other.
"""

import frappe


def ai_draft_validate(doc, method=None):
	if doc.status != "Draft" and not doc.reviewed_by:
		frappe.throw(
			f"AI Draft {doc.name or '(new)'} cannot leave 'Draft' status without reviewed_by — every "
			f"AI-generated draft/suggestion requires an explicit human reviewer on record before it "
			f"becomes Approved or Rejected (master plan principle #24: AI output in a regulated "
			f"workflow defaults to suggestion/draft, never auto-final-approval)."
		)
	if doc.status != "Draft" and not doc.reviewed_on:
		doc.reviewed_on = frappe.utils.now_datetime()
	if not doc.is_new():
		previous_status = frappe.db.get_value("AI Draft", doc.name, "status")
		if previous_status in ("Approved", "Rejected") and doc.status != previous_status:
			frappe.throw(f"AI Draft {doc.name} was already decided ({previous_status}) — a draft decision cannot be changed once made.")


def create_ai_draft(*, copilot_code, use_case, source_doctype, source_reference, content, title=None, suggested_fields=None, generated_by_job_log=None):
	"""Persists a new pending ('Draft') AI Draft row. Called by a copilot's orchestration
	module right after the mock synthesis step — see `ai_qms_copilot.run_qms_copilot()`. Every
	call creates a NEW row (append-only, like AI Job Log) — repeated copilot calls for the same
	source record are expected and are not an idempotency bug, exactly like AI Job Log already
	accumulates one row per `run_ai_action()` call."""
	draft = frappe.get_doc(
		{
			"doctype": "AI Draft",
			"copilot_code": copilot_code,
			"use_case": use_case,
			"title": title or f"{use_case} — {source_reference}",
			"source_doctype": source_doctype,
			"source_reference": source_reference,
			"content": content,
			"suggested_fields": frappe.as_json(suggested_fields) if suggested_fields else None,
			"status": "Draft",
			"generated_by_job_log": generated_by_job_log,
		}
	)
	draft.insert(ignore_permissions=True)
	return draft


def decide_ai_draft(draft_name, decision, reviewed_by, review_notes=None):
	"""Generic approve/reject for a draft that does NOT mint a new business record on approval
	(e.g. a reviewed summary/interpretation that's simply endorsed as accurate). `draft_capa`
	specifically does NOT go through this — see module docstring."""
	if decision not in ("Approved", "Rejected"):
		frappe.throw(f"decide_ai_draft: decision must be 'Approved' or 'Rejected', got {decision!r}.")
	if not reviewed_by:
		frappe.throw("decide_ai_draft requires an explicit reviewed_by (a real human user) — AI output cannot self-approve.")

	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.status != "Draft":
		frappe.throw(f"AI Draft {draft_name} is already '{draft.status}' — cannot decide again.")

	draft.status = decision
	draft.reviewed_by = reviewed_by
	draft.reviewed_on = frappe.utils.now_datetime()
	if review_notes:
		draft.review_notes = review_notes
	draft.save(ignore_permissions=True)
	return draft
