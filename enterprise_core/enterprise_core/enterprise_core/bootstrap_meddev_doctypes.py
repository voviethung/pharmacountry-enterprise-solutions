"""Golden Demo #22 (Medical Device Manufacturing, master plan DEMO 04, "PHASE 6" item 3) —
DocTypes for IP-MEDICAL-DEVICE (already reserved in setup.py's _INDUSTRY_PACKS from DP-303).
Unlike every prior manufacturing golden demo, this uses BOTH batch AND serial tracking on the
finished item (`has_batch_no` + `has_serial_no` together, a real supported ERPNext combination)
— MD01 (serial uniqueness) is native Frappe primary-key uniqueness on Serial No, and MD05
(finished serial traces components) is a thin wrapper around Golden Demo #7's
`trace_feed_batch_genealogy()` (a serial belongs to exactly one batch, so tracing a serial's
components is really tracing its batch's components) — `block_fg_release_without_qa` keeps
working completely unmodified for the 7th time since it already keys off batch_no.

Only 2 new DocTypes: `MedDev Design Change Record` (MD02's approval gate for BOM revisions)
and `MedDev Complaint` (MD06). Everything else is Custom Fields on native doctypes:
`Supplier.quality_status`/`is_critical_supplier` (MD03), `BOM.design_change_record` (MD02),
`Work Order.equipment` (MD07, reusing Golden Demo #6's EAM Calibration Record for the actual
overdue check).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_meddev_doctypes.run
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


def _add_custom_field(dt, fieldname, field_dict):
	full_name = f"{dt}-{fieldname}"
	if frappe.db.exists("Custom Field", full_name):
		print(f"Custom Field '{full_name}' already exists, skipping.")
		return
	frappe.get_doc({"doctype": "Custom Field", "dt": dt, "fieldname": fieldname, **field_dict}).insert()
	print(f"Added Custom Field '{fieldname}' to {dt}.")


def run():
	# Custom Fields first, DocTypes after: on a site without developer_mode (e.g.
	# pharmacountry.vn), the DocType creation calls below throw and abort the rest of run() —
	# putting the pure-DB-write Custom Fields first means they still land even when the
	# DocType half needs `bench migrate` to pick up the JSON files instead. Found as a real gap
	# (the Custom Fields came back missing entirely on a first attempt) since this bootstrap
	# had DocTypes listed first, unlike Vet Mfg's bootstrap which already got this order right.
	_add_custom_field("Supplier", "quality_status", {"label": "Quality Status (MedDev)", "fieldtype": "Select", "options": "Pending\nApproved\nDisqualified", "default": "Pending", "insert_after": "supplier_group"})
	_add_custom_field("Supplier", "is_critical_supplier", {"label": "Critical Supplier (MedDev)", "fieldtype": "Check", "default": "0", "insert_after": "quality_status"})
	_add_custom_field("BOM", "design_change_record", {"label": "Design Change Record (MedDev)", "fieldtype": "Link", "options": "MedDev Design Change Record", "insert_after": "is_default"})
	_add_custom_field("Work Order", "equipment", {"label": "Equipment (MedDev)", "fieldtype": "Link", "options": "Asset", "insert_after": "production_item"})

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "MedDev Design Change Record",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:change_code",
			"fields": [
				{"fieldname": "change_code", "fieldtype": "Data", "label": "Change Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nApproved\nRejected", "default": "Draft", "in_list_view": 1},
				{"fieldname": "approved_date", "fieldtype": "Date", "label": "Approved Date"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "change_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "MedDev Complaint",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "serial_or_lot", "fieldtype": "Data", "label": "Serial/Lot No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "complaint_date", "fieldtype": "Date", "label": "Complaint Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nInvestigating\nClosed", "default": "Open", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "complaint_date",
			"sort_order": "DESC",
		}
	)
