"""Golden Demo #10 (Veterinary Distribution, master plan DEMO 16, "PHASE 4" item 2) — like
DEMO 14, this needs almost no new DocTypes. ERPNext natively covers Territory (VD01, with its
own `territory_manager` + `targets` child table for VD05 sales targets), Sales Partner (VD02,
the "Dealer" concept, with `commission_rate`), Customer.credit_limit (VD04, same mechanism
Golden Demo #2's PD04 proved), and batch/expiry (VD03, same has_batch_no pattern). VD06
(Recall) reuses Golden Demo #3's QMS Recall. Only VD07 (Technical visit linked to customer)
is genuinely new.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_vet_dist_doctypes.run
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
			"name": "Vet Technical Visit",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer", "reqd": 1, "in_list_view": 1},
				{"fieldname": "visit_date", "fieldtype": "Date", "label": "Visit Date", "default": "Today", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sales_person", "fieldtype": "Link", "label": "Sales Person", "options": "Sales Person", "in_list_view": 1},
				{"fieldname": "products_discussed", "fieldtype": "Small Text", "label": "Products Discussed"},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
				{"fieldname": "follow_up_date", "fieldtype": "Date", "label": "Follow-up Date"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "visit_date",
			"sort_order": "DESC",
		}
	)
