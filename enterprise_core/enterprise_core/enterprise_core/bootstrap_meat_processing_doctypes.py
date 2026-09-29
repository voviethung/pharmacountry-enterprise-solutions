"""Golden Demo #28 — Meat / Animal Product Processing (master plan DEMO 31, "PHASE 6" item 9,
the last Phase 6 item) — DocTypes for IP-MEAT-PROCESSING (already reserved in setup.py's
_INDUSTRY_PACKS from DP-303). Structurally the closest kin in the whole codebase to Golden Demo
#19's Seafood Processing & Export (IP-SEAFOOD-PROCESSING) — same architectural choice: this does
NOT use ERPNext's Item/Stock/Warehouse/Company machinery (no new Company, same as every prior
"farm-shaped" golden demo this session), it's a parallel domain-specific pipeline of its own
DocTypes, because lots here are received/processed/packed by live weight and carton count, not
discrete stock-tracked Items.

Real cross-demo reuse story, mirroring Seafood's own Dynamic-Link-to-an-existing-harvest
precedent: `Meat Incoming Lot.source_reference` is a Dynamic Link (same "source_type"/
"source_reference" pattern as Seafood Harvest Lot / native ERPNext Quality Inspection) that can
point at an EXISTING `Pig Sale Lot` (Golden Demo #11/Pig Farm) or `Cattle Sale Lot` (Golden Demo
#12/Cattle) record. The demo instance concretely uses the real `Pig Sale Lot` already sold to
"Dong Nai Meat Processing Co." (a Customer record Golden Demo #11 planted in anticipation of
this exact demo) for one incoming lot, plus a second, deliberately self-contained
"Direct Farm Intake" lot (no Dynamic Link target — realistic, since not every supplier a meat
plant buys from is itself a completed golden demo) — giving `Meat Processing Batch` a genuine
TWO-source genealogy to prove MP03 non-trivially (Seafood's SP03 was 1:1).

Slaughter is intentionally NOT a separate DocType — MP01-MP07 has no dedicated "slaughter" test
letter, so the live-weight -> carcass-weight transition is modeled as fields on `Meat Processing
Batch` itself (mirrors how Seafood folds "processing" straight onto its own Processing Batch
without a separate grading-to-processing hop). MP04 (QC hold/release) is a genuinely NEW,
EXPLICIT enforcement gate this session's kin (Seafood) never needed a lettered test for: `Meat
Processing Batch.qc_status` starts "On Hold", and `Meat Packing Lot`'s own `validate` hook
BLOCKS insert unless the referenced batch's qc_status is "Released" — modeled directly after
Premix's Weighing Verification Pending/Verified gate and 3PL's quarantine-release gate, both
already established patterns in this session for "a real hold enforced at insert time, not just
a status label."

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_meat_processing_doctypes.run
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
			"name": "Meat Plant",
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
			"name": "Meat Incoming Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:lot_code",
			"fields": [
				{"fieldname": "lot_code", "fieldtype": "Data", "label": "Lot Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "plant", "fieldtype": "Link", "label": "Plant", "options": "Meat Plant", "reqd": 1, "in_list_view": 1},
				{"fieldname": "species", "fieldtype": "Data", "label": "Species", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "source_type",
					"fieldtype": "Select",
					"label": "Source Type",
					"options": "Pig Sale Lot\nCattle Sale Lot\nDirect Farm Intake",
					"reqd": 1,
					"in_list_view": 1,
				},
				{"fieldname": "source_reference", "fieldtype": "Dynamic Link", "label": "Source Reference", "options": "source_type"},
				{"fieldname": "source_farm_name", "fieldtype": "Data", "label": "Source Farm / Cooperative (if direct)"},
				{"fieldname": "receiving_date", "fieldtype": "Date", "label": "Receiving Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "animal_count", "fieldtype": "Int", "label": "Animal Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "live_weight_kg", "fieldtype": "Float", "label": "Live Weight (kg)", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "inspection_status",
					"fieldtype": "Select",
					"label": "Ante-mortem Inspection Status",
					"options": "Pending\nPassed\nFailed",
					"default": "Pending",
					"in_list_view": 1,
				},
				{"fieldname": "inspected_by", "fieldtype": "Data", "label": "Inspected By"},
				{"fieldname": "inspected_on", "fieldtype": "Date", "label": "Inspected On"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "receiving_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Meat Processing Batch Source",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				{"fieldname": "incoming_lot", "fieldtype": "Link", "label": "Incoming Lot", "options": "Meat Incoming Lot", "reqd": 1, "in_list_view": 1},
				{"fieldname": "live_weight_kg", "fieldtype": "Float", "label": "Live Weight Consumed (kg)", "reqd": 1, "in_list_view": 1},
			],
			"permissions": [],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Meat Processing Batch",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:batch_code",
			"fields": [
				{"fieldname": "batch_code", "fieldtype": "Data", "label": "Batch Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "plant", "fieldtype": "Link", "label": "Plant", "options": "Meat Plant", "reqd": 1, "in_list_view": 1},
				{"fieldname": "process_date", "fieldtype": "Date", "label": "Process Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "process_type",
					"fieldtype": "Select",
					"label": "Process Type",
					"options": "Whole Carcass\nPrimal Cuts\nDeboned\nGround/Minced",
					"reqd": 1,
					"in_list_view": 1,
				},
				{"fieldname": "sources", "fieldtype": "Table", "label": "Incoming Lot Sources (MP03 genealogy)", "options": "Meat Processing Batch Source", "reqd": 1},
				{"fieldname": "total_live_weight_kg", "fieldtype": "Float", "label": "Total Live Weight (kg)", "read_only": 1, "in_list_view": 1},
				{"fieldname": "carcass_weight_kg", "fieldtype": "Float", "label": "Carcass Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "carcass_yield_percent", "fieldtype": "Float", "label": "Carcass Yield (%)", "read_only": 1, "in_list_view": 1},
				{"fieldname": "output_cut_weight_kg", "fieldtype": "Float", "label": "Output Cut Weight (kg)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "cut_yield_percent", "fieldtype": "Float", "label": "Cut Yield (%)", "read_only": 1, "in_list_view": 1},
				{
					"fieldname": "qc_status",
					"fieldtype": "Select",
					"label": "QC Status",
					"options": "On Hold\nReleased\nRejected",
					"default": "On Hold",
					"in_list_view": 1,
				},
				{"fieldname": "qc_released_by", "fieldtype": "Data", "label": "QC Released By", "read_only": 1},
				{"fieldname": "qc_released_on", "fieldtype": "Datetime", "label": "QC Released On", "read_only": 1},
				{"fieldname": "qc_notes", "fieldtype": "Small Text", "label": "QC Notes"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "process_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Meat Packing Lot",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:packing_lot_code",
			"fields": [
				{"fieldname": "packing_lot_code", "fieldtype": "Data", "label": "Packing Lot Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "processing_batch", "fieldtype": "Link", "label": "Processing Batch", "options": "Meat Processing Batch", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "pack_date", "fieldtype": "Date", "label": "Pack Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "carton_count", "fieldtype": "Int", "label": "Carton Count", "reqd": 1, "in_list_view": 1},
				{"fieldname": "net_weight_per_carton_kg", "fieldtype": "Float", "label": "Net Weight per Carton (kg)", "reqd": 1},
				{"fieldname": "total_packed_weight_kg", "fieldtype": "Float", "label": "Total Packed Weight (kg)", "read_only": 1, "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Available\nDistributed", "default": "Available", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "pack_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Meat Cold Storage Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "packing_lot", "fieldtype": "Link", "label": "Packing Lot", "options": "Meat Packing Lot", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "storage_date", "fieldtype": "Date", "label": "Storage Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "storage_temp_c", "fieldtype": "Float", "label": "Storage Temperature (C)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "warehouse_location", "fieldtype": "Data", "label": "Warehouse Location"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "In Storage\nDistributed", "default": "In Storage", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "storage_date",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Meat Distribution",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "packing_lot", "fieldtype": "Link", "label": "Packing Lot", "options": "Meat Packing Lot", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "distribution_date", "fieldtype": "Date", "label": "Distribution Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "destination", "fieldtype": "Data", "label": "Destination", "reqd": 1, "in_list_view": 1},
				{"fieldname": "carton_count", "fieldtype": "Int", "label": "Carton Count", "reqd": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "distribution_date",
			"sort_order": "DESC",
		}
	)
