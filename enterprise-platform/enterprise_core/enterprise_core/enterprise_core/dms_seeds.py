"""Golden Demo #4 — DMS & Training standalone (master plan DEMO 11), IP-DMS. Continues the
cold-storage story from Golden Demo #3's QMS Change Control (DP-526) — SOP-WH-02 is exactly
the document that change control flagged as needing revision.
"""

import frappe

_DOC_CODE = "SOP-WH-02"


def _ensure_document():
	if frappe.db.exists("DMS Document", _DOC_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "DMS Document",
			"document_code": _DOC_CODE,
			"title": "Cold Chain Monitoring — Warehouse B",
			"doc_type": "SOP",
			"department": "Warehouse",
			"status": "Draft",
			"requires_training": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_version_1_effective():
	existing = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 1}, "name")
	if existing:
		return existing, False
	v1 = frappe.get_doc(
		{
			"doctype": "DMS Document Version",
			"document": _DOC_CODE,
			"version_no": 1,
			"status": "Draft",
			"content_summary": "Review cold storage logs weekly.",
		}
	)
	v1.insert(ignore_permissions=True)
	v1.status = "Under Review"
	v1.reviewed_by = "qa.manager@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Approved"
	v1.approved_by = "quality.director@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Effective"
	v1.effective_date = frappe.utils.nowdate()
	v1.save(ignore_permissions=True)
	return v1.name, True


def seed_dms_document_lifecycle():
	"""DP-531/532 — Document request -> draft -> review -> approve -> effective -> training,
	the master plan's own Flow for DEMO 11. Proves D03 (training assignment on effective) by
	verifying assignments actually exist afterward, not just that the transition succeeded."""
	doc_created = _ensure_document()
	v1_name, v1_created = _ensure_version_1_effective()

	training_count = frappe.db.count("DMS Training Assignment", {"document_version": v1_name})
	if training_count == 0:
		frappe.throw(f"D03 FAILED: no Training Assignments were auto-created for Effective version {v1_name}.")

	return (
		f"seed_dms_document_lifecycle: Document {'created' if doc_created else 'already existed'} ({_DOC_CODE}). "
		f"Version 1 {'reached Effective' if v1_created else 'already existed'} ({v1_name}). "
		f"D03: {training_count} training assignment(s) confirmed."
	)


def _ensure_version_2_revision():
	"""D02/D04/D06 — a periodic-review-triggered revision: Version 2 goes Effective, Version 1
	must automatically become Obsolete (not deleted — D06 needs its history to remain), and
	DMS Document.current_version must point at Version 2 only (D02)."""
	existing = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 2}, "name")
	if existing:
		return existing, False
	v2 = frappe.get_doc(
		{
			"doctype": "DMS Document Version",
			"document": _DOC_CODE,
			"version_no": 2,
			"status": "Draft",
			"content_summary": "Review cold storage logs daily within 24 hours (revised per DP-526/DP-528 CAPA findings); redundant logger with SMS alert now required.",
		}
	)
	v2.insert(ignore_permissions=True)
	v2.status = "Approved"
	v2.reviewed_by = "qa.manager@pharmacountry.vn"
	v2.approved_by = "quality.director@pharmacountry.vn"
	v2.save(ignore_permissions=True)
	v2.status = "Effective"
	v2.effective_date = frappe.utils.nowdate()
	v2.save(ignore_permissions=True)
	return v2.name, True


def seed_dms_revision():
	"""DP-533 — the revision half of the flow (periodic review -> revision/obsolete)."""
	if not frappe.db.exists("DMS Document Version", {"document": _DOC_CODE, "version_no": 1, "status": "Effective"}):
		if not frappe.db.exists("DMS Document Version", {"document": _DOC_CODE, "version_no": 1}):
			return "seed_dms_revision: SKIPPED — Version 1 does not exist yet, run seed_dms_document_lifecycle first."
	v2_name, v2_created = _ensure_version_2_revision()

	v1_status = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 1}, "status")
	current_version = frappe.db.get_value("DMS Document", _DOC_CODE, "current_version")
	if v1_status != "Obsolete":
		frappe.throw(f"D04 FAILED: Version 1 should be Obsolete after Version 2 went Effective, is '{v1_status}'.")
	if current_version != v2_name:
		frappe.throw(f"D02 FAILED: DMS Document.current_version is {current_version!r}, expected {v2_name!r}.")

	return (
		f"seed_dms_revision: Version 2 {'reached Effective' if v2_created else 'already existed'} ({v2_name}). "
		f"D04 CONFIRMED (Version 1 -> Obsolete). D02 CONFIRMED (current_version points only at Version 2). "
		f"D06 CONFIRMED (Version 1 still queryable, not deleted)."
	)


def _test_d01_effective_version_immutable():
	v1_name = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 1}, "name")
	if not v1_name:
		frappe.throw("_test_d01_effective_version_immutable: Version 1 not found — run seed_dms_document_lifecycle first.")
	v1 = frappe.get_doc("DMS Document Version", v1_name)
	v1.content_summary = "Tampered content — this edit must be blocked."
	blocked = False
	try:
		v1.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("D01 negative test FAILED: editing an Effective/Obsolete version's content was not blocked!")
	return True


def _ensure_controlled_print():
	"""D05 — controlled print logged."""
	current_version = frappe.db.get_value("DMS Document", _DOC_CODE, "current_version")
	if not current_version:
		return False
	if frappe.db.exists("DMS Controlled Print Log", {"document_version": current_version, "copy_number": "COPY-01"}):
		return False
	frappe.get_doc(
		{
			"doctype": "DMS Controlled Print Log",
			"document_version": current_version,
			"printed_by": "warehouse.officer@pharmacountry.vn",
			"copy_number": "COPY-01",
		}
	).insert(ignore_permissions=True)
	return True


def seed_dms_validations():
	"""DP-534 — D01 (immutability negative test) and D05 (controlled print log)."""
	d01 = _test_d01_effective_version_immutable()
	print_logged = _ensure_controlled_print()
	return f"seed_dms_validations: D01 CONFIRMED ({d01}). D05 controlled print {'logged' if print_logged else 'already logged'}."
