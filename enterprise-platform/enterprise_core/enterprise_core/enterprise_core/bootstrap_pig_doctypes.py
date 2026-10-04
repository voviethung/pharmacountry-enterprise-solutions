"""Golden Demo #11 (Pig Farm Management, master plan DEMO 22, "PHASE 4" item 3) — DocTypes for
IP-LIVESTOCK-PIG (already reserved in setup.py's _INDUSTRY_PACKS from DP-303). Same from-scratch
domain-specific DocType set pattern as Golden Demo #8 (Shrimp Farm) — no ERPNext
manufacturing/quality overlap for the breeding/growing side, but the terminal Sale Lot links to
a real ERPNext Customer (like Vet Distribution) for genuine PF08 trace-to-customer.

Sow and Boar (master plan's own entity list) are merged into one "Pig Breeding Animal" doctype
with a `sex` Select field rather than two near-identical doctypes. "Weaning" is folded into Pig
Grower Batch's own fields rather than a separate doctype, since it's a lifecycle event/state
change on the batch, not a distinct record type with its own children — same simplification
logic as Shrimp Farm not having a separate "restocking" doctype.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_pig_doctypes.run
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
			"name": "Pig Farm",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:farm_name",
			"fields": [
				{"fieldname": "farm_name", "fieldtype": "Data", "label": "Farm Name", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "location", "fieldtype": "Data", "label": "Location", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "farm_name",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Pen",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:pen_code",
			"fields": [
				{"fieldname": "pen_code", "fieldtype": "Data", "label": "Pen Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Pig Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "pen_type", "fieldtype": "Select", "label": "Pen Type", "options": "Breeding\nFarrowing\nNursery\nGrower\nFinisher", "reqd": 1, "in_list_view": 1},
				{"fieldname": "capacity", "fieldtype": "Int", "label": "Capacity"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Empty\nOccupied", "default": "Empty", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "pen_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Breeding Animal",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:tag_id",
			"fields": [
				{"fieldname": "tag_id", "fieldtype": "Data", "label": "Tag ID", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "sex", "fieldtype": "Select", "label": "Sex", "options": "Sow\nBoar", "reqd": 1, "in_list_view": 1},
				{"fieldname": "breed", "fieldtype": "Data", "label": "Breed", "in_list_view": 1},
				{"fieldname": "birth_date", "fieldtype": "Date", "label": "Birth Date"},
				{"fieldname": "pen", "fieldtype": "Link", "label": "Pen", "options": "Pig Pen"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nCulled\nSold", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "tag_id",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Breeding Service",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "sow", "fieldtype": "Link", "label": "Sow", "options": "Pig Breeding Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "boar", "fieldtype": "Link", "label": "Boar", "options": "Pig Breeding Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "service_date", "fieldtype": "Date", "label": "Service Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "expected_farrow_date", "fieldtype": "Date", "label": "Expected Farrow Date", "read_only": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Served\nConfirmed Pregnant\nFarrowed\nFailed", "default": "Served", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "service_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Farrowing",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "breeding_service", "fieldtype": "Link", "label": "Breeding Service", "options": "Pig Breeding Service", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farrowing_date", "fieldtype": "Date", "label": "Farrowing Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "born_alive", "fieldtype": "Int", "label": "Born Alive", "reqd": 1, "in_list_view": 1},
				{"fieldname": "born_dead", "fieldtype": "Int", "label": "Born Dead"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "farrowing_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Grower Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:batch_code",
			"fields": [
				{"fieldname": "batch_code", "fieldtype": "Data", "label": "Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farrowing", "fieldtype": "Link", "label": "Farrowing", "options": "Pig Farrowing", "reqd": 1, "in_list_view": 1},
				{"fieldname": "pen", "fieldtype": "Link", "label": "Pen", "options": "Pig Pen", "reqd": 1, "in_list_view": 1},
				{"fieldname": "stage", "fieldtype": "Select", "label": "Stage", "options": "Nursery\nGrower\nFinisher\nSold", "default": "Nursery", "in_list_view": 1},
				{"fieldname": "weaning_date", "fieldtype": "Date", "label": "Weaning Date"},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count (Weaned)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nSold", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "weaning_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Feed Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "feed_date", "fieldtype": "Date", "label": "Feed Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "feed_product", "fieldtype": "Data", "label": "Feed Product", "reqd": 1},
				{"fieldname": "qty_kg", "fieldtype": "Float", "label": "Quantity (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "cost", "fieldtype": "Currency", "label": "Cost"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "feed_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Vaccination",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "vaccine_name", "fieldtype": "Data", "label": "Vaccine Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "due_date", "fieldtype": "Date", "label": "Due Date", "reqd": 1, "in_list_view": 1},
				{"fieldname": "administered_date", "fieldtype": "Date", "label": "Administered Date"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Due\nAdministered\nOverdue", "read_only": 1, "default": "Due", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "due_date",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Medicine Treatment",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "treatment_date", "fieldtype": "Date", "label": "Treatment Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "medicine_name", "fieldtype": "Data", "label": "Medicine Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "diagnosis", "fieldtype": "Small Text", "label": "Diagnosis"},
				{"fieldname": "withdrawal_days", "fieldtype": "Int", "label": "Withdrawal Days", "reqd": 1},
				{"fieldname": "withdrawal_end_date", "fieldtype": "Date", "label": "Withdrawal End Date", "read_only": 1, "in_list_view": 1},
				{"fieldname": "cost", "fieldtype": "Currency", "label": "Cost"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "treatment_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Weight Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_weight_kg", "fieldtype": "Float", "label": "Average Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_count", "fieldtype": "Int", "label": "Sample Count"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "record_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Mortality Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "mortality_count", "fieldtype": "Int", "label": "Mortality Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "cause", "fieldtype": "Data", "label": "Cause"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "record_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Pig Sale Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "batch", "fieldtype": "Link", "label": "Batch", "options": "Pig Grower Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "sale_date", "fieldtype": "Date", "label": "Sale Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "head_count", "fieldtype": "Int", "label": "Head Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "total_weight_kg", "fieldtype": "Float", "label": "Total Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_price", "fieldtype": "Currency", "label": "Sale Price", "reqd": 1},
				{"fieldname": "other_cost", "fieldtype": "Currency", "label": "Other Cost (labor/utilities)"},
				{"fieldname": "total_feed_cost", "fieldtype": "Currency", "label": "Total Feed Cost", "read_only": 1},
				{"fieldname": "total_medicine_cost", "fieldtype": "Currency", "label": "Total Medicine Cost", "read_only": 1},
				{"fieldname": "total_cost", "fieldtype": "Currency", "label": "Total Cost", "read_only": 1},
				{"fieldname": "cost_per_kg", "fieldtype": "Currency", "label": "Cost per kg", "read_only": 1},
				{"fieldname": "profit", "fieldtype": "Currency", "label": "Profit", "read_only": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "sale_date",
			"sort_order": "DESC",
		}
	)
