"""Golden Demo #19 (Seafood Processing & Export, master plan DEMO 32, "PHASE 5" item 5, the
last Phase 5 item) — DocTypes for IP-SEAFOOD-PROCESSING (already reserved in setup.py's
_INDUSTRY_PACKS from DP-303). Unlike the manufacturing golden demos, this does NOT use
ERPNext's Item/Stock/Warehouse machinery — it's a parallel domain-specific pipeline (same
architectural choice as Shrimp/Fish/Pig/Poultry/Cattle/Hatchery Farm), because processing lots
here are graded/processed/packed by weight and carton count, not discrete stock-tracked Items.
The real reuse story is upstream: `Seafood Harvest Lot.source_reference` is a Dynamic Link
(same "reference_type"/"reference_name" pattern as native ERPNext Quality Inspection) pointing
at an EXISTING `Shrimp Harvest` or `Fish Harvest` record from Golden Demo #8/#17 — this is the
first golden demo whose "master data" step doesn't create a new farm/pond at all, it plugs
straight into a previously-completed golden demo's own harvest record. SP08 (recall) reuses
Golden Demo #3's `QMS Recall` doctype as-is, the 6th distinct golden demo to do so.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_seafood_doctypes.run
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
			"name": "Seafood Plant",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:plant_name",
			"fields": [
				{"fieldname": "plant_name", "fieldtype": "Data", "label": "Plant Name", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "location", "fieldtype": "Data", "label": "Location", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "plant_name",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Harvest Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:lot_code",
			"fields": [
				{"fieldname": "lot_code", "fieldtype": "Data", "label": "Lot Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "plant", "fieldtype": "Link", "label": "Plant", "options": "Seafood Plant", "reqd": 1, "in_list_view": 1},
				{"fieldname": "source_type", "fieldtype": "Select", "label": "Source Type", "options": "Shrimp Harvest\nFish Harvest", "reqd": 1, "in_list_view": 1},
				{"fieldname": "source_reference", "fieldtype": "Dynamic Link", "label": "Source Reference", "options": "source_type", "reqd": 1, "in_list_view": 1},
				{"fieldname": "species", "fieldtype": "Data", "label": "Species", "reqd": 1},
				{"fieldname": "receiving_date", "fieldtype": "Date", "label": "Receiving Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "received_weight_kg", "fieldtype": "Float", "label": "Received Weight (kg)", "reqd": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "receiving_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Grading",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "harvest_lot", "fieldtype": "Link", "label": "Harvest Lot", "options": "Seafood Harvest Lot", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "grading_date", "fieldtype": "Date", "label": "Grading Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "grade_a_kg", "fieldtype": "Float", "label": "Grade A (kg)", "in_list_view": 1},
				{"fieldname": "grade_b_kg", "fieldtype": "Float", "label": "Grade B (kg)", "in_list_view": 1},
				{"fieldname": "reject_kg", "fieldtype": "Float", "label": "Reject (kg)"},
				{"fieldname": "yield_percent", "fieldtype": "Float", "label": "Yield (%)", "read_only": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "grading_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Processing Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:batch_code",
			"fields": [
				{"fieldname": "batch_code", "fieldtype": "Data", "label": "Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "grading", "fieldtype": "Link", "label": "Grading", "options": "Seafood Grading", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "process_date", "fieldtype": "Date", "label": "Process Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "process_type", "fieldtype": "Select", "label": "Process Type", "options": "Whole\nHeadless\nPeeled\nButterfly", "reqd": 1, "in_list_view": 1},
				{"fieldname": "output_weight_kg", "fieldtype": "Float", "label": "Output Weight (kg)", "reqd": 1, "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "process_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Packing Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:packing_lot_code",
			"fields": [
				{"fieldname": "packing_lot_code", "fieldtype": "Data", "label": "Packing Lot Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "processing_batch", "fieldtype": "Link", "label": "Processing Batch", "options": "Seafood Processing Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "pack_date", "fieldtype": "Date", "label": "Pack Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "carton_count", "fieldtype": "Int", "label": "Carton Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "net_weight_per_carton_kg", "fieldtype": "Float", "label": "Net Weight per Carton (kg)", "reqd": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Available\nShipped", "default": "Available", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "pack_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Cold Storage Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "packing_lot", "fieldtype": "Link", "label": "Packing Lot", "options": "Seafood Packing Lot", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "storage_date", "fieldtype": "Date", "label": "Storage Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "storage_temp_c", "fieldtype": "Float", "label": "Storage Temperature (C)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "warehouse_location", "fieldtype": "Data", "label": "Warehouse Location"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "In Storage\nShipped", "default": "In Storage", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "storage_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seafood Shipment",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "packing_lot", "fieldtype": "Link", "label": "Packing Lot", "options": "Seafood Packing Lot", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "shipment_date", "fieldtype": "Date", "label": "Shipment Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "destination_country", "fieldtype": "Data", "label": "Destination Country", "reqd": 1, "in_list_view": 1},
				{"fieldname": "carton_count", "fieldtype": "Int", "label": "Carton Count", "reqd": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "shipment_date",
			"sort_order": "DESC",
		}
	)
