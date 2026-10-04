"""Golden Demo #14 (Hatchery / Breeding Management, master plan DEMO 25, "PHASE 4" item 6, the
last Phase 4 item) — DocTypes for IP-HATCHERY (already reserved in setup.py's _INDUSTRY_PACKS
from DP-303). The deepest pipeline of any farm golden demo so far: Parent Stock -> Egg Batch ->
Incubation (assigned to an Incubator, same Empty/Occupied occupancy-guard pattern as Shrimp
Pond/Pig Pen/Poultry House) -> Hatch Result -> Chick Batch -> Chick Grading -> Vaccination ->
Dispatch. No mortality-tracking doctype, unlike every other farm golden demo — the master
plan's own H01-H06 test list has no mortality test for Hatchery, so — same "build what's
tested" scoping discipline as every prior golden demo — it's left out. Likewise no cost
allocation on Dispatch (H06 tests customer *trace*, not cost, unlike Pig/Poultry/Cattle's
explicit PF07/PO07/CT07 cost tests).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_hatchery_doctypes.run
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
			"name": "Hatchery Farm",
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
			"name": "Hatchery Parent Stock",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:parent_flock_code",
			"fields": [
				{"fieldname": "parent_flock_code", "fieldtype": "Data", "label": "Parent Flock Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Hatchery Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "breed", "fieldtype": "Data", "label": "Breed", "in_list_view": 1},
				{"fieldname": "placement_date", "fieldtype": "Date", "label": "Placement Date", "default": "Today"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nRetired", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "parent_flock_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Egg Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:batch_code",
			"fields": [
				{"fieldname": "batch_code", "fieldtype": "Data", "label": "Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "parent_stock", "fieldtype": "Link", "label": "Parent Stock", "options": "Hatchery Parent Stock", "reqd": 1, "in_list_view": 1},
				{"fieldname": "collection_date", "fieldtype": "Date", "label": "Collection Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "egg_count", "fieldtype": "Int", "label": "Egg Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Collected\nIncubating\nHatched", "default": "Collected", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "collection_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Incubator",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:incubator_code",
			"fields": [
				{"fieldname": "incubator_code", "fieldtype": "Data", "label": "Incubator Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Hatchery Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "capacity", "fieldtype": "Int", "label": "Capacity (eggs)"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Empty\nOccupied", "default": "Empty", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "incubator_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Incubation",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "egg_batch", "fieldtype": "Link", "label": "Egg Batch", "options": "Hatchery Egg Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "incubator", "fieldtype": "Link", "label": "Incubator", "options": "Hatchery Incubator", "reqd": 1, "in_list_view": 1},
				{"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "expected_hatch_date", "fieldtype": "Date", "label": "Expected Hatch Date", "read_only": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Incubating\nHatched\nFailed", "default": "Incubating", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "start_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Hatch Result",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "incubation", "fieldtype": "Link", "label": "Incubation", "options": "Hatchery Incubation", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "hatch_date", "fieldtype": "Date", "label": "Hatch Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "hatched_count", "fieldtype": "Int", "label": "Hatched Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "infertile_count", "fieldtype": "Int", "label": "Infertile Count"},
				{"fieldname": "dead_in_shell_count", "fieldtype": "Int", "label": "Dead-in-Shell Count"},
				{"fieldname": "hatch_rate_percent", "fieldtype": "Float", "label": "Hatch Rate (%)", "read_only": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "hatch_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Chick Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:chick_batch_code",
			"fields": [
				{"fieldname": "chick_batch_code", "fieldtype": "Data", "label": "Chick Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "hatch_result", "fieldtype": "Link", "label": "Hatch Result", "options": "Hatchery Hatch Result", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "hatch_date", "fieldtype": "Date", "label": "Hatch Date", "reqd": 1, "in_list_view": 1},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nDispatched", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "hatch_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Chick Grading",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "chick_batch", "fieldtype": "Link", "label": "Chick Batch", "options": "Hatchery Chick Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "grading_date", "fieldtype": "Date", "label": "Grading Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "grade_a_count", "fieldtype": "Int", "label": "Grade A Count", "in_list_view": 1},
				{"fieldname": "grade_b_count", "fieldtype": "Int", "label": "Grade B Count", "in_list_view": 1},
				{"fieldname": "reject_count", "fieldtype": "Int", "label": "Reject Count"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "grading_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Hatchery Vaccination",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "chick_batch", "fieldtype": "Link", "label": "Chick Batch", "options": "Hatchery Chick Batch", "reqd": 1, "in_list_view": 1},
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
			"name": "Hatchery Dispatch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "chick_batch", "fieldtype": "Link", "label": "Chick Batch", "options": "Hatchery Chick Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "dispatch_date", "fieldtype": "Date", "label": "Dispatch Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "head_count", "fieldtype": "Int", "label": "Head Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_price", "fieldtype": "Currency", "label": "Sale Price"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "dispatch_date",
			"sort_order": "DESC",
		}
	)
