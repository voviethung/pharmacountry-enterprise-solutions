"""Golden Demo #15 (Aquafeed Manufacturing, master plan DEMO 26, "PHASE 5" item 1) — like
Feed Manufacturing (Golden Demo #7) and Vet Manufacturing (Golden Demo #9), this needs almost
no new DocTypes: the whole manufacturing flow (Company/Item/BOM/Work Order/Quality
Inspection/QA release) reuses Golden Demo #1's exact machinery, including
`block_fg_release_without_qa` completely unmodified (AF06 — the 4th reuse of that hook after
Pharma/Feed/Vet Mfg) and AF05's lot trace reuses `trace_feed_batch_genealogy()` unmodified too
(it's a generic Serial-and-Batch-Bundle walk, not Feed-specific).

Only genuinely new pieces:
- 3 Custom Fields on Item (life_stage, pellet_size_mm, buoyancy) — AF01/AF02. `target_species`
  (already added by Golden Demo #9's bootstrap, labelled "(Vet)" there but a plain Data field
  usable by any Item) is reused as-is for AF01's species dimension rather than adding a second,
  redundant species field.
- `Aquafeed Extrusion Log` — AF03, a plain process-record doctype with no validate hook (same
  status as Shrimp Farm's Growth Sample — record-keeping only, no negative test needed).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_aquafeed_doctypes.run
"""

import frappe


def run():
	if not frappe.db.exists("Custom Field", "Item-life_stage"):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"fieldname": "life_stage",
				"label": "Life Stage (Aquafeed)",
				"fieldtype": "Select",
				"options": "\nPost-Larvae\nJuvenile\nGrower\nFinisher\nBroodstock",
				"insert_after": "target_species",
			}
		).insert()
		print("Added Custom Field 'life_stage' to Item.")
	else:
		print("Custom Field 'Item-life_stage' already exists, skipping.")

	if not frappe.db.exists("Custom Field", "Item-pellet_size_mm"):
		frappe.get_doc(
			{"doctype": "Custom Field", "dt": "Item", "fieldname": "pellet_size_mm", "label": "Pellet Size (mm)", "fieldtype": "Float", "insert_after": "life_stage"}
		).insert()
		print("Added Custom Field 'pellet_size_mm' to Item.")
	else:
		print("Custom Field 'Item-pellet_size_mm' already exists, skipping.")

	if not frappe.db.exists("Custom Field", "Item-buoyancy"):
		frappe.get_doc(
			{"doctype": "Custom Field", "dt": "Item", "fieldname": "buoyancy", "label": "Buoyancy", "fieldtype": "Select", "options": "\nFloating\nSinking", "insert_after": "pellet_size_mm"}
		).insert()
		print("Added Custom Field 'buoyancy' to Item.")
	else:
		print("Custom Field 'Item-buoyancy' already exists, skipping.")

	if not frappe.db.exists("DocType", "Aquafeed Extrusion Log"):
		frappe.get_doc(
			{
				"doctype": "DocType",
				"name": "Aquafeed Extrusion Log",
				"module": "Enterprise Core",
				"custom": 0,
				"track_changes": 1,
				"autoname": "hash",
				"fields": [
					{"fieldname": "work_order", "fieldtype": "Link", "label": "Work Order", "options": "Work Order", "reqd": 1, "unique": 1, "in_list_view": 1},
					{"fieldname": "extrusion_date", "fieldtype": "Date", "label": "Extrusion Date", "default": "Today", "reqd": 1, "in_list_view": 1},
					{"fieldname": "barrel_temperature_c", "fieldtype": "Float", "label": "Barrel Temperature (C)", "reqd": 1, "in_list_view": 1},
					{"fieldname": "moisture_percent", "fieldtype": "Float", "label": "Moisture (%)"},
					{"fieldname": "oil_coating_percent", "fieldtype": "Float", "label": "Oil Coating (%)"},
					{"fieldname": "measured_pellet_size_mm", "fieldtype": "Float", "label": "Measured Pellet Size (mm)", "reqd": 1, "in_list_view": 1},
				],
				"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
				"sort_field": "extrusion_date",
				"sort_order": "DESC",
			}
		).insert()
		print("Created DocType 'Aquafeed Extrusion Log'.")
	else:
		print("DocType 'Aquafeed Extrusion Log' already exists, skipping.")
