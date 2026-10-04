"""Golden Demo #17 (Fish Farm Management, master plan DEMO 29, "PHASE 5" item 3) — DocTypes
for IP-FISH (already reserved in setup.py's _INDUSTRY_PACKS from DP-303). Near-identical
architecture to Golden Demo #8 (Shrimp Farm) — Pond/Stocking Batch/Feed/Growth/Mortality/
Harvest, same Empty->Stocked->Harvested pond lifecycle. Two deliberate differences from Shrimp
Farm's DocType set: no Water Parameter Reading and no Health Treatment doctype — the master
plan's own entity list mentions "health, treatment" but the FF0x test list (FF01-FF07) has no
water or health/treatment test, so — same "build what's tested" scoping discipline as every
prior golden demo — both are left out. FF02 (biomass estimate) is folded into `Fish Growth
Sample` as server-computed fields rather than a separate doctype — a biomass estimate is
naturally derived FROM a growth/weight sample in real aquaculture practice, not a parallel,
independently-entered concept.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_fish_doctypes.run
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
			"name": "Fish Farm",
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
			"name": "Fish Pond",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:pond_code",
			"fields": [
				{"fieldname": "pond_code", "fieldtype": "Data", "label": "Pond/Cage Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Fish Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "pond_type", "fieldtype": "Select", "label": "Type", "options": "Pond\nCage", "default": "Pond", "in_list_view": 1},
				{"fieldname": "area_or_volume", "fieldtype": "Float", "label": "Area (m2) / Volume (m3)"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Empty\nStocked\nHarvested", "default": "Empty", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "pond_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Fish Stocking Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "pond", "fieldtype": "Link", "label": "Pond/Cage", "options": "Fish Pond", "reqd": 1, "in_list_view": 1},
				{"fieldname": "species", "fieldtype": "Data", "label": "Species", "reqd": 1, "in_list_view": 1},
				{"fieldname": "stocking_date", "fieldtype": "Date", "label": "Stocking Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count", "reqd": 1},
				{"fieldname": "source_hatchery", "fieldtype": "Data", "label": "Source Hatchery"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nHarvested\nFailed", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "stocking_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Fish Feed Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Fish Stocking Batch", "reqd": 1, "in_list_view": 1},
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
			"name": "Fish Growth Sample",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Fish Stocking Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_date", "fieldtype": "Date", "label": "Sample Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_weight_g", "fieldtype": "Float", "label": "Average Weight (g)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_count", "fieldtype": "Int", "label": "Sample Count"},
				{"fieldname": "estimated_population", "fieldtype": "Int", "label": "Estimated Population", "read_only": 1, "in_list_view": 1},
				{"fieldname": "estimated_biomass_kg", "fieldtype": "Float", "label": "Estimated Biomass (kg)", "read_only": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "sample_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Fish Mortality Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Fish Stocking Batch", "reqd": 1, "in_list_view": 1},
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
			"name": "Fish Harvest",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Fish Stocking Batch", "reqd": 1, "in_list_view": 1, "unique": 1},
				{"fieldname": "harvest_date", "fieldtype": "Date", "label": "Harvest Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "total_weight_kg", "fieldtype": "Float", "label": "Total Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_weight_g", "fieldtype": "Float", "label": "Average Weight (g)"},
				{"fieldname": "total_cost", "fieldtype": "Currency", "label": "Total Cost"},
				{"fieldname": "survival_rate_percent", "fieldtype": "Float", "label": "Survival Rate (%)", "read_only": 1},
				{"fieldname": "fcr", "fieldtype": "Float", "label": "FCR (Feed Conversion Ratio)", "read_only": 1},
				{"fieldname": "days_of_culture", "fieldtype": "Int", "label": "Days of Culture", "read_only": 1},
				{"fieldname": "cost_per_kg", "fieldtype": "Currency", "label": "Cost per kg", "read_only": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "harvest_date",
			"sort_order": "DESC",
		}
	)
