"""Golden Demo #9 (Veterinary Pharmaceutical Manufacturing, master plan DEMO 14, "PHASE 4"
item 1) — "Tương tự pharma manufacturing nhưng terminology/product master phù hợp thú y" per
the master plan itself. Unlike DEMO 10-13 (QMS/DMS/LIMS/EAM), this needs almost NO new
DocTypes: the whole manufacturing flow (Company/Item/BOM/Work Order/Quality Inspection/QA
release) reuses Golden Demo #1's exact machinery — including `block_fg_release_without_qa`
completely unmodified (VPM04), the same way Golden Demo #7's Feed Manufacturing did. Only 2
genuinely vet-specific additions:

- 3 Custom Fields on Item (target_species, indication, withdrawal_period_days) — VPM01.
- "Label" added to DMS Document.doc_type's options — VPM07 reuses Golden Demo #4's whole
  versioned-document lifecycle (D01/D02/D04/D06 already enforced there) for label version
  control, instead of building a parallel label-versioning concept from scratch.

VPM06 (Recall) reuses Golden Demo #3's QMS Recall doctype as-is — one shared recall concept
across the platform, not a vet-specific parallel one.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_vet_mfg_doctypes.run
"""

import frappe


def run():
	if not frappe.db.exists("Custom Field", "Item-target_species"):
		frappe.get_doc(
			{"doctype": "Custom Field", "dt": "Item", "fieldname": "target_species", "label": "Target Species (Vet)", "fieldtype": "Data", "insert_after": "item_group"}
		).insert()
		print("Added Custom Field 'target_species' to Item.")
	else:
		print("Custom Field 'Item-target_species' already exists, skipping.")

	if not frappe.db.exists("Custom Field", "Item-indication"):
		frappe.get_doc(
			{"doctype": "Custom Field", "dt": "Item", "fieldname": "indication", "label": "Indication (Vet)", "fieldtype": "Small Text", "insert_after": "target_species"}
		).insert()
		print("Added Custom Field 'indication' to Item.")
	else:
		print("Custom Field 'Item-indication' already exists, skipping.")

	if not frappe.db.exists("Custom Field", "Item-withdrawal_period_days"):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"fieldname": "withdrawal_period_days",
				"label": "Withdrawal Period (days)",
				"fieldtype": "Int",
				"insert_after": "indication",
				"description": "Days after last dose before the animal/animal product may enter the food supply.",
			}
		).insert()
		print("Added Custom Field 'withdrawal_period_days' to Item.")
	else:
		print("Custom Field 'Item-withdrawal_period_days' already exists, skipping.")

	doc_type_field = frappe.db.get_value("DocField", {"parent": "DMS Document", "fieldname": "doc_type"}, "options")
	if doc_type_field and "Label" not in doc_type_field.split("\n"):
		frappe.db.set_value("DocField", {"parent": "DMS Document", "fieldname": "doc_type"}, "options", doc_type_field + "\nLabel")
		frappe.clear_cache(doctype="DMS Document")
		print("Added 'Label' option to DMS Document.doc_type.")
	else:
		print("DMS Document.doc_type already has 'Label' option, skipping.")
