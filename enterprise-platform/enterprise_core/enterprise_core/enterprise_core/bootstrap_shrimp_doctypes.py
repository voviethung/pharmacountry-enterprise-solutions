"""Golden Demo #8 (Shrimp Farm Management, master plan DEMO 28) — DocTypes for CE-11 (Farm).
The last of the 8 golden demos, and the only one with zero ERPNext manufacturing/quality
overlap — aquaculture is a genuinely different domain (Pond/Stocking Batch/Harvest, not
Item/BOM/Batch), so this is a from-scratch DocType set, same ORM-based creation pattern as
the other bootstrap_*_doctypes.py files.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_shrimp_doctypes.run
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
			"name": "Shrimp Farm",
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
			"name": "Shrimp Pond",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:pond_code",
			"fields": [
				{"fieldname": "pond_code", "fieldtype": "Data", "label": "Pond Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Shrimp Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "area_m2", "fieldtype": "Float", "label": "Area (m2)"},
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
			"name": "Shrimp Stocking Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "pond", "fieldtype": "Link", "label": "Pond", "options": "Shrimp Pond", "reqd": 1, "in_list_view": 1},
				{"fieldname": "species", "fieldtype": "Data", "label": "Species", "default": "Litopenaeus vannamei (Whiteleg shrimp)", "reqd": 1},
				{"fieldname": "stocking_date", "fieldtype": "Date", "label": "Stocking Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count (PL)", "reqd": 1},
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
			"name": "Shrimp Daily Feed Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Shrimp Stocking Batch", "reqd": 1, "in_list_view": 1},
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
			"name": "Shrimp Water Parameter Reading",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "pond", "fieldtype": "Link", "label": "Pond", "options": "Shrimp Pond", "reqd": 1, "in_list_view": 1},
				{"fieldname": "reading_datetime", "fieldtype": "Datetime", "label": "Reading Datetime", "default": "now", "reqd": 1, "in_list_view": 1},
				{"fieldname": "do_mg_l", "fieldtype": "Float", "label": "DO (mg/L)"},
				{"fieldname": "ph", "fieldtype": "Float", "label": "pH"},
				{"fieldname": "temperature_c", "fieldtype": "Float", "label": "Temperature (C)"},
				{"fieldname": "salinity_ppt", "fieldtype": "Float", "label": "Salinity (ppt)"},
				{"fieldname": "alkalinity", "fieldtype": "Float", "label": "Alkalinity (mg/L)"},
				{"fieldname": "nh3_mg_l", "fieldtype": "Float", "label": "NH3 (mg/L)"},
				{"fieldname": "no2_mg_l", "fieldtype": "Float", "label": "NO2 (mg/L)"},
				{"fieldname": "is_alert", "fieldtype": "Check", "label": "Alert (Out of Threshold)", "read_only": 1, "in_list_view": 1},
				{"fieldname": "alert_message", "fieldtype": "Small Text", "label": "Alert Message", "read_only": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "reading_datetime",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Shrimp Growth Sample",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Shrimp Stocking Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_date", "fieldtype": "Date", "label": "Sample Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_body_weight_g", "fieldtype": "Float", "label": "Average Body Weight (g)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sample_count", "fieldtype": "Int", "label": "Sample Count"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "sample_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Shrimp Health Treatment",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Shrimp Stocking Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "issue_date", "fieldtype": "Date", "label": "Issue Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "diagnosis", "fieldtype": "Small Text", "label": "Diagnosis"},
				{"fieldname": "treatment_applied", "fieldtype": "Small Text", "label": "Treatment Applied"},
				{"fieldname": "dosage", "fieldtype": "Data", "label": "Dosage"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "issue_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Shrimp Mortality Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Shrimp Stocking Batch", "reqd": 1, "in_list_view": 1},
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
			"name": "Shrimp Harvest",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "stocking_batch", "fieldtype": "Link", "label": "Stocking Batch", "options": "Shrimp Stocking Batch", "reqd": 1, "in_list_view": 1, "unique": 1},
				{"fieldname": "harvest_date", "fieldtype": "Date", "label": "Harvest Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "total_weight_kg", "fieldtype": "Float", "label": "Total Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "average_body_weight_g", "fieldtype": "Float", "label": "Average Body Weight (g)"},
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
