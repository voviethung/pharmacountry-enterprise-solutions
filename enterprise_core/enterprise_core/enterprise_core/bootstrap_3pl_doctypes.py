"""Golden Demo #24 (Pharma 3PL / GSP / Cold Chain, master plan DEMO 08, "PHASE 6" item 5) —
DocTypes/Custom Fields for IP-3PL-COLDCHAIN (a new pack — a 3PL warehouse-operator vertical
wasn't in DP-303's original 19-pack list, registered directly in setup.py the same way
IP-PHARMACY was for Golden Demo #23).

Only ONE genuinely new DocType: `Cold Chain Temperature Reading` (W02 — a cold-chain temperature log
that IS the excursion event itself, flagged via `is_excursion`/`status`, rather than a second
"event" doctype spawned by a hook — the reading record already fully captures "an event was
created" once flagged, so a separate event doctype would just be a redundant shadow of the same
row). Everything else this demo needs is either fully native ERPNext (Warehouse already ships
with `is_rejected_warehouse` and a `customer` Link field — used here to model "stock ownership
by client" literally, not just by naming convention; Delivery Note already ships with
`transporter`/`driver_name`/`vehicle_no`/`lr_no`/`lr_date` for Transport; `Sales Order
Item.delivery_date` for the SLA commitment) or a handful of Custom Fields:
`Warehouse.min_temp_c`/`max_temp_c` (the configured cold-chain range W02 compares each reading
against) and `Delivery Note.sla_committed_date`/`sla_met` (a plain informational SLA flag, no
enforcement hook — the spec gives SLA no lettered test, so this stays minimal by design).
Quarantine (W04) and FEFO (W03) need zero new schema at all: quarantine is the same
warehouse-name-substring gate idiom as `block_fg_release_without_qa`/
`meddev_block_rejected_material_use` (see threepl_validations.py), and FEFO is a plain
`Batch.expiry_date asc` query.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_3pl_doctypes.run
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
	# Custom Fields first, DocTypes after — the exact ordering lesson from bootstrap_meddev_doctypes.py's
	# own docstring: on a site without developer_mode, DocType-creation calls can throw and abort the
	# rest of run(), so the pure-DB-write Custom Fields must land first regardless.
	_add_custom_field("Warehouse", "min_temp_c", {"label": "Min Temp C (3PL Cold Chain)", "fieldtype": "Float", "insert_after": "warehouse_type"})
	_add_custom_field("Warehouse", "max_temp_c", {"label": "Max Temp C (3PL Cold Chain)", "fieldtype": "Float", "insert_after": "min_temp_c"})
	_add_custom_field("Delivery Note", "sla_committed_date", {"label": "SLA Committed Date (3PL)", "fieldtype": "Date", "insert_after": "lr_date"})
	_add_custom_field("Delivery Note", "sla_met", {"label": "SLA Met (3PL)", "fieldtype": "Check", "read_only": 1, "insert_after": "sla_committed_date"})

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Cold Chain Temperature Reading",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "warehouse", "fieldtype": "Link", "label": "Warehouse", "options": "Warehouse", "reqd": 1, "in_list_view": 1},
				{"fieldname": "reading_datetime", "fieldtype": "Datetime", "label": "Reading Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
				{"fieldname": "temperature_c", "fieldtype": "Float", "label": "Temperature (C)", "reqd": 1, "in_list_view": 1},
				{"fieldname": "is_excursion", "fieldtype": "Check", "label": "Is Excursion", "read_only": 1, "default": "0", "in_list_view": 1},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Normal\nExcursion", "read_only": 1, "default": "Normal", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "reading_datetime",
			"sort_order": "DESC",
		}
	)
