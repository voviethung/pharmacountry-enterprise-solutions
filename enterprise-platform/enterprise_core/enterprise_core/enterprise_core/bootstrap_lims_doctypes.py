"""Golden Demo #5 (LIMS / QC Laboratory standalone, master plan DEMO 12) — DocTypes for
CE-08. Same ORM-based creation pattern as the other bootstrap_*_doctypes.py files. Run with
developer_mode=1:

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_lims_doctypes.run

L05 ("OOS trigger") deliberately creates a real QMS OOS OOT record (Golden Demo #3) rather
than a parallel LIMS-only OOS concept — one OOS/OOT module shared across the platform, not
two competing ones.
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
			"name": "LIMS Instrument",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:instrument_code",
			"fields": [
				{"fieldname": "instrument_code", "fieldtype": "Data", "label": "Instrument Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "instrument_name", "fieldtype": "Data", "label": "Instrument Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "calibration_due_date", "fieldtype": "Date", "label": "Calibration Due Date", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Calibrated\nOverdue\nOut of Service", "default": "Calibrated", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "calibration_due_date",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Specification Parameter",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "parameter_name", "fieldtype": "Data", "label": "Parameter", "reqd": 1, "in_list_view": 1},
				{"fieldname": "unit", "fieldtype": "Data", "label": "Unit", "in_list_view": 1},
				{"fieldname": "min_value", "fieldtype": "Float", "label": "Min Value", "in_list_view": 1},
				{"fieldname": "max_value", "fieldtype": "Float", "label": "Max Value", "in_list_view": 1},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Specification",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "spec_code", "fieldtype": "Data", "label": "Spec Code", "reqd": 1, "in_list_view": 1},
				{"fieldname": "item_name", "fieldtype": "Data", "label": "Item / Product", "reqd": 1, "in_list_view": 1},
				{"fieldname": "version_no", "fieldtype": "Int", "label": "Version No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nEffective\nObsolete", "default": "Draft", "in_list_view": 1},
				{"fieldname": "parameters", "fieldtype": "Table", "label": "Parameters", "options": "LIMS Specification Parameter"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Test Method",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "method_code", "fieldtype": "Data", "label": "Method Code", "reqd": 1, "in_list_view": 1},
				{"fieldname": "method_name", "fieldtype": "Data", "label": "Method Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "instrument_type", "fieldtype": "Data", "label": "Instrument Type"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nEffective\nObsolete", "default": "Draft", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Sample",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "item_name", "fieldtype": "Data", "label": "Item / Product", "reqd": 1, "in_list_view": 1},
				{"fieldname": "batch_reference", "fieldtype": "Data", "label": "Batch Reference", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_type", "fieldtype": "Select", "label": "Sample Type", "options": "Incoming\nIn-Process\nFinished Goods\nStability", "reqd": 1, "in_list_view": 1},
				{"fieldname": "received_date", "fieldtype": "Date", "label": "Received Date", "default": "Today", "reqd": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Received\nAssigned\nTesting\nReviewed\nApproved\nRejected", "default": "Received", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "received_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Test Result",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "parameter_name", "fieldtype": "Data", "label": "Parameter", "reqd": 1, "in_list_view": 1},
				{"fieldname": "result_value", "fieldtype": "Float", "label": "Result Value", "in_list_view": 1},
				{"fieldname": "unit", "fieldtype": "Data", "label": "Unit", "in_list_view": 1},
				{"fieldname": "pass_fail", "fieldtype": "Select", "label": "Pass/Fail", "options": "\nPass\nFail", "read_only": 1, "in_list_view": 1},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS Test",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "sample", "fieldtype": "Link", "label": "Sample", "options": "LIMS Sample", "reqd": 1, "in_list_view": 1},
				{"fieldname": "specification", "fieldtype": "Link", "label": "Specification", "options": "LIMS Specification", "reqd": 1, "in_list_view": 1},
				{"fieldname": "method", "fieldtype": "Link", "label": "Test Method", "options": "LIMS Test Method", "reqd": 1},
				{"fieldname": "instrument", "fieldtype": "Link", "label": "Instrument", "options": "LIMS Instrument"},
				{"fieldname": "analyst", "fieldtype": "Link", "label": "Analyst", "options": "User", "reqd": 1, "in_list_view": 1},
				{"fieldname": "reviewed_by", "fieldtype": "Link", "label": "Reviewed By", "options": "User"},
				{"fieldname": "approved_by", "fieldtype": "Link", "label": "Approved By", "options": "User"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Assigned\nIn Progress\nResult Entered\nReviewed\nApproved", "default": "Assigned", "in_list_view": 1},
				{"fieldname": "results", "fieldtype": "Table", "label": "Results", "options": "LIMS Test Result"},
				{"fieldname": "oos_triggered", "fieldtype": "Check", "label": "OOS Triggered", "read_only": 1},
				{"fieldname": "linked_oos", "fieldtype": "Link", "label": "Linked QMS OOS/OOT", "options": "QMS OOS OOT", "read_only": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "LIMS COA",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch_reference", "fieldtype": "Data", "label": "Batch Reference", "reqd": 1, "in_list_view": 1},
				{"fieldname": "test", "fieldtype": "Link", "label": "LIMS Test", "options": "LIMS Test", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nApproved", "default": "Draft", "in_list_view": 1},
				{"fieldname": "issued_date", "fieldtype": "Date", "label": "Issued Date"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)
