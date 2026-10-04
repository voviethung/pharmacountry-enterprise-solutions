"""Golden Demo #18 (Aquaculture Hatchery / Seed Management, master plan DEMO 30, "PHASE 5"
item 4) — DocTypes for IP-AQUA-HATCHERY (already reserved in setup.py's _INDUSTRY_PACKS from
DP-303). Same pipeline SHAPE as Golden Demo #14 (Hatchery/Breeding Management for poultry) —
Broodstock -> Spawning -> Larval Batch -> Nursery -> Grading -> Seed Batch -> Dispatch — but
leaner: no separate Incubator/Hatch-Result-vs-Batch split (a shrimp/fish "Larval Batch" IS the
hatch result, there's no separate incubation-equipment-assignment concept the way poultry eggs
need an Incubator), and grading is folded directly into Seed Batch creation instead of a
separate Grading doctype. No Nursery Feed Log and no Water doctype — the master plan's own
entity list mentions "feed, water" but the AH0x test list (AH01-AH06) has neither a feed nor a
water test, so — same "build what's tested" scoping discipline as every prior golden demo —
both are left out; AH04 ("Nursery") is satisfied by the Nursery Batch's own existence and
status lifecycle.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_aqua_hatchery_doctypes.run
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
			"name": "Aqua Hatchery Farm",
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
			"name": "Aqua Broodstock",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:tag_id",
			"fields": [
				{"fieldname": "tag_id", "fieldtype": "Data", "label": "Tag ID", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "farm", "fieldtype": "Link", "label": "Farm", "options": "Aqua Hatchery Farm", "reqd": 1, "in_list_view": 1},
				{"fieldname": "species", "fieldtype": "Data", "label": "Species", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sex", "fieldtype": "Select", "label": "Sex", "options": "Male\nFemale", "reqd": 1, "in_list_view": 1},
				{"fieldname": "source", "fieldtype": "Data", "label": "Source"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nRetired", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "tag_id",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Spawning Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "dam", "fieldtype": "Link", "label": "Dam (Female Broodstock)", "options": "Aqua Broodstock", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sire", "fieldtype": "Link", "label": "Sire (Male Broodstock)", "options": "Aqua Broodstock", "in_list_view": 1},
				{"fieldname": "spawning_date", "fieldtype": "Date", "label": "Spawning Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "egg_count", "fieldtype": "Int", "label": "Egg Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Spawned\nHatched\nFailed", "default": "Spawned", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "spawning_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Larval Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "spawning_batch", "fieldtype": "Link", "label": "Spawning Batch", "options": "Aqua Spawning Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "hatch_date", "fieldtype": "Date", "label": "Hatch Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "larvae_count", "fieldtype": "Int", "label": "Larvae Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "survival_rate_percent", "fieldtype": "Float", "label": "Survival Rate (%)", "read_only": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "hatch_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Nursery Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "larval_batch", "fieldtype": "Link", "label": "Larval Batch", "options": "Aqua Larval Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "nursery_start_date", "fieldtype": "Date", "label": "Nursery Start Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "initial_count", "fieldtype": "Int", "label": "Initial Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nGraded", "default": "Active", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "nursery_start_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Health Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "nursery_batch", "fieldtype": "Link", "label": "Nursery Batch", "options": "Aqua Nursery Batch", "reqd": 1, "in_list_view": 1},
				{"fieldname": "record_date", "fieldtype": "Date", "label": "Record Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "diagnosis", "fieldtype": "Small Text", "label": "Diagnosis"},
				{"fieldname": "treatment_applied", "fieldtype": "Small Text", "label": "Treatment Applied"},
				{"fieldname": "dosage", "fieldtype": "Data", "label": "Dosage"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "record_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Seed Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:seed_batch_code",
			"fields": [
				{"fieldname": "seed_batch_code", "fieldtype": "Data", "label": "Seed Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "nursery_batch", "fieldtype": "Link", "label": "Nursery Batch", "options": "Aqua Nursery Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "grading_date", "fieldtype": "Date", "label": "Grading Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "grade_a_count", "fieldtype": "Int", "label": "Grade A Count", "in_list_view": 1},
				{"fieldname": "grade_b_count", "fieldtype": "Int", "label": "Grade B Count", "in_list_view": 1},
				{"fieldname": "reject_count", "fieldtype": "Int", "label": "Reject Count"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Available\nDispatched", "default": "Available", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "grading_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Aqua Seed Dispatch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "seed_batch", "fieldtype": "Link", "label": "Seed Batch", "options": "Aqua Seed Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "dispatch_date", "fieldtype": "Date", "label": "Dispatch Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "quantity", "fieldtype": "Int", "label": "Quantity", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sale_price", "fieldtype": "Currency", "label": "Sale Price"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "dispatch_date",
			"sort_order": "DESC",
		}
	)
