"""Golden Demo #13 (Cattle / Dairy Farm Management, master plan DEMO 24, "PHASE 4" item 5) —
DocTypes for IP-LIVESTOCK-CATTLE (already reserved in setup.py's _INDUSTRY_PACKS from DP-303).

Architecturally different from Shrimp/Pig/Poultry Farm: dairy cattle are long-lived individual
assets with pedigree and repeated lactation cycles, not a batch of identical units moving
through one growth cycle — so there is no Pond/Pen/House occupancy state machine here (no CT0x
test needs one), and every operational record (milking, treatment, feed, sale) is keyed
directly off an individual `Cattle Animal`, not a batch. Pedigree (CT01) is a self-referential
Link (sire/dam point back to Cattle Animal), same technique as a BOM's own recursive structure
elsewhere in ERPNext. "Body condition" (in the master plan's entity list) has no dedicated CT0x
test, so — same "build what's tested" scoping discipline as every prior golden demo — it's left
out.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_cattle_doctypes.run
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
			"name": "Cattle Farm",
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
			"name": "Cattle Animal",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:tag_id",
			"fields": [
				{"fieldname": "tag_id", "fieldtype": "Data", "label": "Tag ID", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Cattle Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sex", "fieldtype": "Select", "label": "Sex", "options": "Male\nFemale", "reqd": 1, "in_list_view": 1},
				{"fieldname": "breed", "fieldtype": "Data", "label": "Breed", "in_list_view": 1},
				{"fieldname": "birth_date", "fieldtype": "Date", "label": "Birth Date"},
				{"fieldname": "sire", "fieldtype": "Link", "label": "Sire", "options": "Cattle Animal"},
				{"fieldname": "dam", "fieldtype": "Link", "label": "Dam", "options": "Cattle Animal"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nSold\nCulled", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "tag_id",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cattle Breeding Service",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "dam", "fieldtype": "Link", "label": "Dam", "options": "Cattle Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sire", "fieldtype": "Link", "label": "Sire", "options": "Cattle Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "service_date", "fieldtype": "Date", "label": "Service Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "expected_calving_date", "fieldtype": "Date", "label": "Expected Calving Date", "read_only": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Served\nConfirmed Pregnant\nCalved\nFailed", "default": "Served", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "service_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cattle Calving",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "breeding_service", "fieldtype": "Link", "label": "Breeding Service", "options": "Cattle Breeding Service", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "calving_date", "fieldtype": "Date", "label": "Calving Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "calf_count", "fieldtype": "Int", "label": "Calf Count", "default": 1, "reqd": 1},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "calving_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cattle Milking Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "animal", "fieldtype": "Link", "label": "Animal", "options": "Cattle Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "milk_yield_liters", "fieldtype": "Float", "label": "Milk Yield (L)", "reqd": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "record_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cattle Health Treatment",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "animal", "fieldtype": "Link", "label": "Animal", "options": "Cattle Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "treatment_date", "fieldtype": "Date", "label": "Treatment Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "diagnosis", "fieldtype": "Small Text", "label": "Diagnosis"},
				{"fieldname": "treatment_applied", "fieldtype": "Small Text", "label": "Treatment Applied"},
				{"fieldname": "dosage", "fieldtype": "Data", "label": "Dosage"},
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
			"name": "Cattle Feed Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "animal", "fieldtype": "Link", "label": "Animal", "options": "Cattle Animal", "reqd": 1, "in_list_view": 1},
				{"fieldname": "feed_date", "fieldtype": "Date", "label": "Feed Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "ration_name", "fieldtype": "Data", "label": "Ration Name", "reqd": 1},
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
			"name": "Cattle Sale Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "animal", "fieldtype": "Link", "label": "Animal", "options": "Cattle Animal", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "sale_date", "fieldtype": "Date", "label": "Sale Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_type", "fieldtype": "Select", "label": "Sale Type", "options": "Sold\nCulled", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "weight_kg", "fieldtype": "Float", "label": "Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_price", "fieldtype": "Currency", "label": "Sale Price", "reqd": 1},
				{"fieldname": "other_cost", "fieldtype": "Currency", "label": "Other Cost (labor/utilities)"},
				{"fieldname": "total_feed_cost", "fieldtype": "Currency", "label": "Total Feed Cost", "read_only": 1},
				{"fieldname": "total_health_cost", "fieldtype": "Currency", "label": "Total Health Cost", "read_only": 1},
				{"fieldname": "total_cost", "fieldtype": "Currency", "label": "Total Cost (per animal)", "read_only": 1},
				{"fieldname": "cost_per_kg", "fieldtype": "Currency", "label": "Cost per kg", "read_only": 1},
				{"fieldname": "profit", "fieldtype": "Currency", "label": "Profit", "read_only": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "sale_date",
			"sort_order": "DESC",
		}
	)
