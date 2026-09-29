"""Golden Demo #3 (QMS standalone, master plan DEMO 10) — DocTypes for CE-06 QMS. Same
ORM-based creation pattern as bootstrap_doctypes.py (schema-correct files for this exact
Frappe version, idempotent). Run with developer_mode=1:

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_qms_doctypes.run

DEMO 10 is explicitly a standalone product ("có thể bán cho nhiều ngành regulated" — sellable
to many regulated industries), not tied to the Pharma golden demo — these are fresh DocTypes,
not a reuse of DP-507's Non Conformance/Quality Procedure (which are scoped to proving CE-06
works inside the Pharma manufacturing story, not to being their own sellable product).

QMS CAPA is the spine: Deviation, OOS/OOT and Audit Finding can all feed into it (master plan
tests Q06 "OOS can create CAPA/deviation", Q07 "Audit finding → CAPA") via a source_type +
dynamic source_reference, rather than three separate one-off link fields.
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
			"name": "QMS CAPA",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "capa_type", "fieldtype": "Select", "label": "CAPA Type", "options": "Corrective\nPreventive\nBoth", "reqd": 1},
				{"fieldname": "source_type", "fieldtype": "Select", "label": "Source Type", "options": "\nQMS Deviation\nQMS OOS OOT\nQMS Complaint\nQMS Audit\nQMS Change Control\nQMS Risk", "description": "Must be an exact DocType name — Dynamic Link validates source_reference against it literally."},
				{"fieldname": "source_reference", "fieldtype": "Dynamic Link", "label": "Source Reference", "options": "source_type"},
				{"fieldname": "owner_user", "fieldtype": "Link", "label": "CAPA Owner", "options": "User", "reqd": 1, "in_list_view": 1},
				{"fieldname": "due_date", "fieldtype": "Date", "label": "Due Date", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "status",
					"fieldtype": "Select",
					"label": "Status",
					"options": "Open\nIn Progress\nOverdue\nPending Effectiveness Check\nClosed",
					"default": "Open",
					"in_list_view": 1,
				},
				{"fieldname": "action_plan", "fieldtype": "Text", "label": "Action Plan"},
				{"fieldname": "effectiveness_check_date", "fieldtype": "Date", "label": "Effectiveness Check Date"},
				{"fieldname": "effectiveness_evidence", "fieldtype": "Text", "label": "Effectiveness Evidence"},
				{"fieldname": "closed_by", "fieldtype": "Link", "label": "Closed By", "options": "User"},
				{"fieldname": "closed_date", "fieldtype": "Date", "label": "Closed Date"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "due_date",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "QMS Deviation",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Text", "label": "Description"},
				{"fieldname": "severity", "fieldtype": "Select", "label": "Severity", "options": "Minor\nMajor\nCritical", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nUnder Investigation\nCAPA Initiated\nClosed", "default": "Open", "in_list_view": 1},
				{"fieldname": "reported_by", "fieldtype": "Link", "label": "Reported By", "options": "User", "reqd": 1},
				{"fieldname": "reported_date", "fieldtype": "Date", "label": "Reported Date", "default": "Today", "reqd": 1},
				{"fieldname": "investigation_notes", "fieldtype": "Text", "label": "Investigation Notes"},
				{"fieldname": "root_cause", "fieldtype": "Text", "label": "Root Cause"},
				{"fieldname": "linked_capa", "fieldtype": "Link", "label": "Linked CAPA", "options": "QMS CAPA"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "reported_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "QMS Change Control",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "change_type", "fieldtype": "Select", "label": "Change Type", "options": "Process\nEquipment\nDocument\nMaterial\nOther", "reqd": 1},
				{"fieldname": "reason", "fieldtype": "Text", "label": "Reason"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nUnder Review\nApproved\nImplemented\nClosed", "default": "Draft", "in_list_view": 1},
				{"fieldname": "impacts_documents", "fieldtype": "Check", "label": "Impacts Documents"},
				{"fieldname": "impacts_training", "fieldtype": "Check", "label": "Impacts Training"},
				{"fieldname": "impacts_equipment", "fieldtype": "Check", "label": "Impacts Equipment"},
				{"fieldname": "impact_notes", "fieldtype": "Small Text", "label": "Impact Notes"},
				{"fieldname": "approved_by", "fieldtype": "Link", "label": "Approved By", "options": "User"},
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
			"name": "QMS OOS OOT",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "result_type", "fieldtype": "Select", "label": "Result Type", "options": "OOS\nOOT", "reqd": 1, "in_list_view": 1},
				{"fieldname": "test_reference", "fieldtype": "Data", "label": "Test Reference"},
				{"fieldname": "result_value", "fieldtype": "Data", "label": "Result Value"},
				{"fieldname": "specification", "fieldtype": "Data", "label": "Specification"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nInvestigated\nCAPA Created\nClosed", "default": "Open", "in_list_view": 1},
				{"fieldname": "linked_capa", "fieldtype": "Link", "label": "Linked CAPA", "options": "QMS CAPA"},
				{"fieldname": "linked_deviation", "fieldtype": "Link", "label": "Linked Deviation", "options": "QMS Deviation"},
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
			"name": "QMS Complaint",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name", "reqd": 1},
				{"fieldname": "description", "fieldtype": "Text", "label": "Description"},
				{"fieldname": "severity", "fieldtype": "Select", "label": "Severity", "options": "Minor\nMajor\nCritical", "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nUnder Investigation\nCAPA Created\nClosed", "default": "Open", "in_list_view": 1},
				{"fieldname": "linked_capa", "fieldtype": "Link", "label": "Linked CAPA", "options": "QMS CAPA"},
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
			"name": "QMS Recall",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "batch_reference", "fieldtype": "Data", "label": "Batch Reference"},
				{"fieldname": "reason", "fieldtype": "Text", "label": "Reason"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Initiated\nIn Progress\nCompleted", "default": "Initiated", "in_list_view": 1},
				{"fieldname": "customers_notified", "fieldtype": "Check", "label": "Customers Notified"},
				{"fieldname": "linked_capa", "fieldtype": "Link", "label": "Linked CAPA", "options": "QMS CAPA"},
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
			"name": "QMS Risk",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "risk_category", "fieldtype": "Select", "label": "Risk Category", "options": "Process\nProduct\nSupplier\nEquipment\nOther", "in_list_view": 1},
				{"fieldname": "likelihood", "fieldtype": "Select", "label": "Likelihood", "options": "Low\nMedium\nHigh", "reqd": 1},
				{"fieldname": "impact", "fieldtype": "Select", "label": "Impact", "options": "Low\nMedium\nHigh", "reqd": 1},
				{"fieldname": "risk_score", "fieldtype": "Int", "label": "Risk Score", "read_only": 1},
				{"fieldname": "mitigation", "fieldtype": "Text", "label": "Mitigation"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nMitigated\nClosed", "default": "Open", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "risk_score",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "QMS Audit Finding",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "finding", "fieldtype": "Small Text", "label": "Finding", "reqd": 1, "in_list_view": 1},
				{"fieldname": "severity", "fieldtype": "Select", "label": "Severity", "options": "Minor\nMajor\nCritical", "in_list_view": 1},
				{"fieldname": "linked_capa", "fieldtype": "Link", "label": "Linked CAPA", "options": "QMS CAPA", "in_list_view": 1},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "QMS Audit",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1, "in_list_view": 1},
				{"fieldname": "audit_type", "fieldtype": "Select", "label": "Audit Type", "options": "Internal\nExternal\nSupplier", "reqd": 1, "in_list_view": 1},
				{"fieldname": "auditor", "fieldtype": "Data", "label": "Auditor"},
				{"fieldname": "audit_date", "fieldtype": "Date", "label": "Audit Date", "default": "Today", "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Planned\nIn Progress\nCompleted", "default": "Planned", "in_list_view": 1},
				{"fieldname": "findings", "fieldtype": "Table", "label": "Findings", "options": "QMS Audit Finding"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "audit_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "QMS Supplier Quality",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:supplier_name",
			"fields": [
				{"fieldname": "supplier_name", "fieldtype": "Data", "label": "Supplier Name", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "quality_score", "fieldtype": "Int", "label": "Quality Score (0-100)", "in_list_view": 1},
				{"fieldname": "last_audit_date", "fieldtype": "Date", "label": "Last Audit Date"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Approved\nUnder Review\nDisqualified", "default": "Approved", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Quality Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "supplier_name",
			"sort_order": "ASC",
		}
	)
