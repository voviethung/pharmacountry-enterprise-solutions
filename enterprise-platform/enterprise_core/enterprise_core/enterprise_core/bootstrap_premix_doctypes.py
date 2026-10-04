"""Golden Demo #26 (Premix / Feed Additive Manufacturing, master plan DEMO 19, "PHASE 6" item
7) — DocTypes for IP-PREMIX (already reserved in setup.py's _INDUSTRY_PACKS from DP-303,
category "Animal Feed", no re-add needed). Downstream/kin of Golden Demo #7 (Compound Feed
Manufacturing) — this demo makes the PREMIX-VM-style vitamin/mineral concentrate that a feed
mill's own formula (e.g. Feed's PIG-STARTER) buys as an ingredient, so it's precision (mg-scale
micro-dosing) manufacturing rather than Feed's bulk-ratio manufacturing.

Minimal new schema, following this session's established bias:
- 4 Custom Fields: `Item.is_micro_ingredient` / `Item.requires_second_check` (PM01/PM02 gates),
  `BOM Item.sequence_no` (PM03 mixing order), `BOM.premix_approval_status` (PM04 gate, same
  shape as Medical Device's MD02 `BOM.design_change_record` but a plain Select instead of a
  Link to a separate approval-record DocType — the approval concept doesn't need its own
  document here, just a status flag, so no extra DocType was added for it).
- 1 new DocType: `Premix Weighing Verification` (PM02's four-eyes GMP record — who weighed a
  critical ingredient and who independently verified it, a real audit record, not just a
  boolean flag, since this is what a GMP premix double-check actually produces).
- PM06 (COA/potency) needs ZERO new schema at all — native ERPNext `Quality Inspection
  Reading` (numeric, min_value/max_value, reading_1) already auto-computes Accepted/Rejected
  from a tolerance band (confirmed by reading quality_inspection.py's own
  `min_max_criteria_passed()` before relying on it) — exactly PM06's "measured potency within
  tolerance of target," so only a `Quality Inspection Parameter` master row (plain data, no
  schema) is needed, created directly in premix_seeds.py.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_premix_doctypes.run
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
	# Custom Fields first, DocTypes after — same order-of-operations lesson as Medical Device's
	# bootstrap (DP-646 sync note): on a site without developer_mode (pharmacountry.vn), the
	# DocType `.insert()` calls below throw and abort the rest of run(), so pure-DB-write
	# Custom Fields need to land first. All 4 Custom Fields here are independent of the new
	# `Premix Weighing Verification` DocType (none Links to it), so unlike Medical Device's
	# `BOM.design_change_record`, none of them needs the two-step (migrate, then re-run
	# bootstrap) sequence — all 4 can be created in a single pass on either site.
	_add_custom_field("Item", "is_micro_ingredient", {"label": "Micro Ingredient (Premix)", "fieldtype": "Check", "default": "0", "insert_after": "is_stock_item"})
	_add_custom_field("Item", "requires_second_check", {"label": "Requires Second-Person Check (Premix)", "fieldtype": "Check", "default": "0", "insert_after": "is_micro_ingredient"})
	_add_custom_field("BOM Item", "sequence_no", {"label": "Mixing Sequence No (Premix)", "fieldtype": "Int", "insert_after": "qty"})
	_add_custom_field("BOM", "premix_approval_status", {"label": "Formula Approval Status (Premix)", "fieldtype": "Select", "options": "\nDraft\nApproved\nRejected", "insert_after": "is_default"})

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Premix Weighing Verification",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "work_order", "fieldtype": "Link", "label": "Work Order", "options": "Work Order", "reqd": 1, "in_list_view": 1},
				{"fieldname": "item_code", "fieldtype": "Link", "label": "Item", "options": "Item", "reqd": 1, "in_list_view": 1},
				{"fieldname": "target_qty", "fieldtype": "Float", "label": "Target Qty (from Formula)"},
				{"fieldname": "weighed_qty", "fieldtype": "Float", "label": "Weighed Qty", "reqd": 1, "in_list_view": 1},
				{"fieldname": "weighed_by", "fieldtype": "Data", "label": "Weighed By", "reqd": 1},
				{"fieldname": "verified_by", "fieldtype": "Data", "label": "Verified By (second person)"},
				{"fieldname": "verified_on", "fieldtype": "Datetime", "label": "Verified On"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Pending\nVerified", "default": "Pending", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "creation",
			"sort_order": "DESC",
		}
	)
