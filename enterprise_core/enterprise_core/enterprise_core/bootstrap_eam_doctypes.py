"""Golden Demo #6 (EAM/CMMS/Calibration/Validation standalone, master plan DEMO 13) —
DocTypes for CE-09. Heavily reuses ERPNext's native Assets module (Asset, Asset Maintenance,
Asset Repair — the latter already covers "breakdown creates work order" E03 and "spare part
issue" E04 via its own `stock_items` child table, so those aren't rebuilt here). Only 2 new
DocTypes for the genuinely missing concepts: calibration due-date tracking (E02) and
IQ/OQ/PQ qualification (E05/E06).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_eam_doctypes.run
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


def run():
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "EAM Calibration Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "asset", "fieldtype": "Link", "label": "Asset", "options": "Asset", "reqd": 1, "in_list_view": 1},
				{"fieldname": "calibration_date", "fieldtype": "Date", "label": "Calibration Date", "default": "Today", "reqd": 1},
				{"fieldname": "due_date", "fieldtype": "Date", "label": "Next Calibration Due", "reqd": 1, "in_list_view": 1},
				{"fieldname": "performed_by", "fieldtype": "Data", "label": "Performed By"},
				{"fieldname": "result", "fieldtype": "Select", "label": "Result", "options": "Pass\nFail", "reqd": 1, "in_list_view": 1},
				{"fieldname": "certificate_no", "fieldtype": "Data", "label": "Certificate No"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Maintenance Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "due_date",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "EAM Qualification",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "asset", "fieldtype": "Link", "label": "Asset", "options": "Asset", "reqd": 1, "in_list_view": 1},
				{"fieldname": "qualification_type", "fieldtype": "Select", "label": "Qualification Type", "options": "IQ\nOQ\nPQ\nRequalification", "reqd": 1, "in_list_view": 1},
				{"fieldname": "performed_date", "fieldtype": "Date", "label": "Performed Date", "default": "Today", "reqd": 1},
				{"fieldname": "performed_by", "fieldtype": "Data", "label": "Performed By"},
				{"fieldname": "result", "fieldtype": "Select", "label": "Result", "options": "\nPass\nFail", "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nQualified\nNot Qualified", "default": "Draft", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Maintenance Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "performed_date",
			"sort_order": "DESC",
		}
	)
