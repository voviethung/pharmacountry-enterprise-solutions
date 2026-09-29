"""Golden Demo #4 (DMS & Training standalone, master plan DEMO 11) business rules — D01-D04.
"""

import frappe
from frappe import _


def dms_document_version_validate(doc, method):
	"""D01 — version immutable after Effective: once a version has ever been Effective, its
	content_summary can no longer change (status transitions onward to Obsolete are still
	allowed — that's not a content edit)."""
	if doc.is_new():
		return
	before = frappe.db.get_value("DMS Document Version", doc.name, ["status", "content_summary"], as_dict=True)
	if before and before.status in ("Effective", "Obsolete") and doc.content_summary != before.content_summary:
		frappe.throw(
			_("Cannot edit the content of Document Version {0} — it has already been Effective. Create a new version instead.").format(doc.name),
			title=_("D01: Version Immutable"),
		)


def dms_document_version_on_update(doc, method):
	"""D02 — only the effective version is 'current'. D04 — the previous Effective version
	is archived (flipped to Obsolete, not deleted) when a new one becomes Effective. D03 —
	training assignments are created for the demo users when a version goes Effective."""
	if doc.status != "Effective":
		return

	previous = frappe.db.get_value(
		"DMS Document Version", {"document": doc.document, "status": "Effective", "name": ["!=", doc.name]}, "name"
	)
	if previous:
		prev_doc = frappe.get_doc("DMS Document Version", previous)
		prev_doc.status = "Obsolete"
		prev_doc.obsolete_date = frappe.utils.nowdate()
		prev_doc.save(ignore_permissions=True)

	frappe.db.set_value("DMS Document", doc.document, {"current_version": doc.name, "status": "Effective"})

	requires_training = frappe.db.get_value("DMS Document", doc.document, "requires_training")
	if requires_training:
		for user in frappe.get_all("User", filters={"name": ["like", "%@pharmacountry.vn"]}, pluck="name"):
			if not frappe.db.exists("DMS Training Assignment", {"document_version": doc.name, "user": user}):
				frappe.get_doc(
					{
						"doctype": "DMS Training Assignment",
						"document_version": doc.name,
						"user": user,
						"assigned_date": frappe.utils.nowdate(),
					}
				).insert(ignore_permissions=True)
