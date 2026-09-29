"""Golden Demo #7 (Compound Feed Manufacturing, master plan DEMO 18) — the first of the
remaining 2 golden demos that's a real NEW INDUSTRY VERTICAL, not a standalone
cross-industry product like QMS/DMS/LIMS/EAM. Most of the flow (raw material -> formula ->
weighing/mixing -> QC -> warehouse) reuses ERPNext's own manufacturing module (BOM=Formula,
Stock Entry=weighing/mixing, Quality Inspection=QC) exactly as Golden Demo #1 did — including
reusing `block_fg_release_without_qa` (validations.py) as-is, since it's generic on
warehouse-name pattern, not pharma-specific. Only 2 new DocTypes for genuinely
feed-industry-specific concepts: F02 (ingredient substitution approval) and F07
(cross-contamination/line-sequencing).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_feed_doctypes.run
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
	if not frappe.db.exists("Custom Field", "Item-contains_allergen"):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"fieldname": "contains_allergen",
				"label": "Contains Allergen (Feed)",
				"fieldtype": "Check",
				"insert_after": "item_group",
			}
		).insert()
		print("Added Custom Field 'contains_allergen' to Item.")
	else:
		print("Custom Field 'Item-contains_allergen' already exists, skipping.")

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Feed Ingredient Substitution",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "formula_bom", "fieldtype": "Link", "label": "Formula (BOM)", "options": "BOM", "reqd": 1, "in_list_view": 1},
				{"fieldname": "original_item", "fieldtype": "Link", "label": "Original Ingredient", "options": "Item", "reqd": 1, "in_list_view": 1},
				{"fieldname": "substitute_item", "fieldtype": "Link", "label": "Substitute Ingredient", "options": "Item", "reqd": 1, "in_list_view": 1},
				{"fieldname": "reason", "fieldtype": "Small Text", "label": "Reason"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Pending\nApproved\nRejected", "default": "Pending", "in_list_view": 1},
				{"fieldname": "approved_by", "fieldtype": "Link", "label": "Approved By", "options": "User"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Manufacturing Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Feed Line Cleaning Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "warehouse", "fieldtype": "Link", "label": "Line / Warehouse", "options": "Warehouse", "reqd": 1, "in_list_view": 1},
				{"fieldname": "cleaned_date", "fieldtype": "Datetime", "label": "Cleaned Date", "default": "now", "reqd": 1, "in_list_view": 1},
				{"fieldname": "cleaned_by", "fieldtype": "Data", "label": "Cleaned By"},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1},
				{"role": "Manufacturing Manager", "read": 1, "write": 1, "create": 1, "report": 1, "select": 1},
			],
			"sort_field": "cleaned_date",
			"sort_order": "DESC",
		}
	)
