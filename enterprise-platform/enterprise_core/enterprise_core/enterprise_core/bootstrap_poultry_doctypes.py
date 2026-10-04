"""Golden Demo #12 (Poultry Farm Management, master plan DEMO 23, "PHASE 4" item 4) — DocTypes
for IP-LIVESTOCK-POULTRY (already reserved in setup.py's _INDUSTRY_PACKS from DP-303). Same
from-scratch domain-specific DocType set pattern as Shrimp Farm / Pig Farm, but leaner than Pig
Farm — a poultry flock is placed as day-old chicks with no breeding-stage lifecycle, so "Flock"
and master plan's "Placement" are the same creation event, not two doctypes. "Water" (in the
master plan's entity list) has no dedicated PO0x test, so — same "build what's tested" scoping
discipline as every prior golden demo — it's left out. "Culling" is likewise not a separate
PO0x test and isn't built as its own doctype; deliberate removals show up as part of the Sale
Lot's head_count vs. flock initial_count reconciliation instead.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_poultry_doctypes.run
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
			"name": "Poultry Farm",
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
			"name": "Poultry House",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:house_code",
			"fields": [
				{"fieldname": "house_code", "fieldtype": "Data", "label": "House Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Poultry Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "capacity", "fieldtype": "Int", "label": "Capacity"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Empty\nOccupied", "default": "Empty", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "house_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Poultry Flock",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:flock_code",
			"fields": [
				{"fieldname": "flock_code", "fieldtype": "Data", "label": "Flock Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "house", "fieldtype": "Link", "label": "House", "options": "Poultry House", "reqd": 1, "in_list_view": 1},
				{"fieldname": "flock_type", "fieldtype": "Select", "label": "Flock Type", "options": "Broiler\nLayer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "breed", "fieldtype": "Data", "label": "Breed"},
				{"fieldname": "placement_date", "fieldtype": "Date", "label": "Placement Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count", "reqd": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nSold", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "placement_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Poultry Feed Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "in_list_view": 1},
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
			"name": "Poultry Vaccination",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "in_list_view": 1},
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
			"name": "Poultry Weight Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_weight_g", "fieldtype": "Float", "label": "Average Weight (g)", "reqd": 1, "in_list_view": 1},
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
			"name": "Poultry Mortality Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "in_list_view": 1},
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
			"name": "Poultry Egg Production",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "egg_count", "fieldtype": "Int", "label": "Egg Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "egg_weight_kg", "fieldtype": "Float", "label": "Total Egg Weight (kg)"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "record_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Poultry Sale Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "flock", "fieldtype": "Link", "label": "Flock", "options": "Poultry Flock", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "sale_date", "fieldtype": "Date", "label": "Sale Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "head_count", "fieldtype": "Int", "label": "Head Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "total_weight_kg", "fieldtype": "Float", "label": "Total Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_price", "fieldtype": "Currency", "label": "Sale Price", "reqd": 1},
				{"fieldname": "other_cost", "fieldtype": "Currency", "label": "Other Cost (labor/utilities)"},
				{"fieldname": "total_feed_cost", "fieldtype": "Currency", "label": "Total Feed Cost", "read_only": 1},
				{"fieldname": "total_cost", "fieldtype": "Currency", "label": "Total Cost", "read_only": 1},
				{"fieldname": "cost_per_kg", "fieldtype": "Currency", "label": "Cost per kg", "read_only": 1},
				{"fieldname": "profit", "fieldtype": "Currency", "label": "Profit", "read_only": 1},
				{"fieldname": "livability_percent", "fieldtype": "Float", "label": "Livability (%)", "read_only": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "sale_date",
			"sort_order": "DESC",
		}
	)
