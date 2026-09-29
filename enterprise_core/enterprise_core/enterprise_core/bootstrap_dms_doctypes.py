"""Golden Demo #4 (DMS & Training standalone, master plan DEMO 11) — DocTypes for CE-07.
Same ORM-based creation pattern as bootstrap_doctypes.py/bootstrap_qms_doctypes.py. Run with
developer_mode=1:

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_dms_doctypes.run

Lessons carried over from Golden Demo #3 (QMS): create referenced DocTypes before the ones
that Link to them; `track_changes: 1` set from the start (Q08-equivalent D06 "Revision keeps
history" needs it); no Dynamic Link fields here so the QMS source_type naming bug doesn't
recur, but DMS Document Version's `document` Link still needs DMS Document created first.
"""

import frappe


def _create_if_missing(doctype_dict):
	name = doctype_dict["name"]
	if frappe.db.exists("DocType", name):
		print(f"DocType '{name}' already exists, skipping.")
		return
	doc = frappe.get_doc(doctype_dict)
	doc.insert()
	print(f"Created DocType '{name}'.")


def _add_field_if_missing(doctype_name, field_dict):
	doc = frappe.get_doc("DocType", doctype_name)
	if any(f.fieldname == field_dict["fieldname"] for f in doc.fields):
		print(f"Field '{field_dict['fieldname']}' already exists on '{doctype_name}', skipping.")
		return
	doc.append("fields", field_dict)
	doc.save()
	print(f"Added field '{field_dict['fieldname']}' to '{doctype_name}'.")


def run():
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "DMS Document",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:document_code",
			"fields": [
				{"fieldname": "document_code", "fieldtype": "Data", "label": "Document Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "title", "fieldtype": "Data", "label": "Title", "reqd": 1, "in_list_view": 1},
				{"fieldname": "doc_type", "fieldtype": "Select", "label": "Document Type", "options": "SOP\nSpecification\nForm\nTemplate\nPolicy", "reqd": 1, "in_list_view": 1},
				{"fieldname": "department", "fieldtype": "Data", "label": "Department"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nUnder Review\nApproved\nEffective\nUnder Periodic Review\nObsolete", "default": "Draft", "in_list_view": 1},
				{"fieldname": "next_review_date", "fieldtype": "Date", "label": "Next Periodic Review Date"},
				{"fieldname": "requires_training", "fieldtype": "Check", "label": "Requires Training on Effective", "default": "1"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "document_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "DMS Document Version",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "document", "fieldtype": "Link", "label": "Document", "options": "DMS Document", "reqd": 1, "in_list_view": 1},
				{"fieldname": "version_no", "fieldtype": "Int", "label": "Version No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nUnder Review\nApproved\nEffective\nObsolete", "default": "Draft", "in_list_view": 1},
				{"fieldname": "content_summary", "fieldtype": "Text", "label": "Content Summary"},
				{"fieldname": "reviewed_by", "fieldtype": "Link", "label": "Reviewed By", "options": "User"},
				{"fieldname": "approved_by", "fieldtype": "Link", "label": "Approved By", "options": "User"},
				{"fieldname": "effective_date", "fieldtype": "Date", "label": "Effective Date"},
				{"fieldname": "obsolete_date", "fieldtype": "Date", "label": "Obsolete Date"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "version_no",
			"sort_order": "DESC",
		}
	)

	_add_field_if_missing(
		"DMS Document",
		{"fieldname": "current_version", "fieldtype": "Link", "label": "Current Effective Version", "options": "DMS Document Version", "read_only": 1, "insert_after": "status"},
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "DMS Training Assignment",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "document_version", "fieldtype": "Link", "label": "Document Version", "options": "DMS Document Version", "reqd": 1, "in_list_view": 1},
				{"fieldname": "user", "fieldtype": "Link", "label": "User", "options": "User", "reqd": 1, "in_list_view": 1},
				{"fieldname": "assigned_date", "fieldtype": "Date", "label": "Assigned Date", "default": "Today"},
				{"fieldname": "completed", "fieldtype": "Check", "label": "Completed"},
				{"fieldname": "completed_date", "fieldtype": "Date", "label": "Completed Date"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "assigned_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "DMS Controlled Print Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "document_version", "fieldtype": "Link", "label": "Document Version", "options": "DMS Document Version", "reqd": 1, "in_list_view": 1},
				{"fieldname": "printed_by", "fieldtype": "Link", "label": "Printed By", "options": "User", "reqd": 1, "in_list_view": 1},
				{"fieldname": "printed_date", "fieldtype": "Datetime", "label": "Printed Date", "default": "now", "in_list_view": 1},
				{"fieldname": "copy_number", "fieldtype": "Data", "label": "Copy Number"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "printed_date",
			"sort_order": "DESC",
		}
	)
