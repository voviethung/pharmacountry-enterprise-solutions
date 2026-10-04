"""Golden Demo #21 (Cosmetics Manufacturing, master plan DEMO 03, "PHASE 6" item 2) — DocTypes
for IP-COSMETICS (already reserved in setup.py's _INDUSTRY_PACKS from DP-303). Unlike every
other manufacturing golden demo so far, this has a genuine TWO-STAGE production flow — a Bulk
batch, QC-released, then consumed as an ingredient by a Packed batch — modeled with two Items
and two BOMs rather than a new doctype, which is why `block_fg_release_without_qa` fires TWICE
in this single demo (once at Bulk release, once at final Packed release) with zero hook
changes: it already matches on any warehouse whose name contains "released", not a hardcoded
"FG Released". C01 (formula revision) and C03 (artwork version) are pure reuse, same as every
prior manufacturing golden demo. Only 3 genuinely new DocTypes, for concepts no prior golden
demo has needed: `Cosmetics Stability Sample` (C04 — periodic shelf-life testing schedule),
`Cosmetics Complaint` (C05 — customer complaint traced back to a batch), and `Cosmetics Rework
Record` (C06 — an explicit audit-trail record alongside the real stock-ledger genealogy a
rework Stock Entry already produces).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_cosmetics_doctypes.run
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
			"name": "Cosmetics Stability Sample",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch_no", "fieldtype": "Data", "label": "Batch No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "condition", "fieldtype": "Select", "label": "Storage Condition", "options": "Room Temperature\nAccelerated 40C\nRefrigerated", "reqd": 1, "in_list_view": 1},
				{"fieldname": "time_point_months", "fieldtype": "Int", "label": "Time Point (months)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "scheduled_date", "fieldtype": "Date", "label": "Scheduled Date", "reqd": 1, "in_list_view": 1},
				{"fieldname": "test_date", "fieldtype": "Date", "label": "Test Date"},
				{"fieldname": "result_summary", "fieldtype": "Small Text", "label": "Result Summary"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Scheduled\nTested\nOverdue", "read_only": 1, "default": "Scheduled", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "scheduled_date",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cosmetics Complaint",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "batch_no", "fieldtype": "Data", "label": "Batch No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "complaint_date", "fieldtype": "Date", "label": "Complaint Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nInvestigating\nClosed", "default": "Open", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "complaint_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cosmetics Rework Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "original_batch", "fieldtype": "Data", "label": "Original Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "new_batch", "fieldtype": "Data", "label": "New Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "rework_date", "fieldtype": "Date", "label": "Rework Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "reason", "fieldtype": "Small Text", "label": "Reason"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "rework_date",
			"sort_order": "DESC",
		}
	)
