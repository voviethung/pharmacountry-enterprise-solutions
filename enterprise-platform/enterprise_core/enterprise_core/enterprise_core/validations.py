"""DP-503 (Warehouse flow) — the one real custom business rule this phase needs: master plan
§7 DEMO 01 test P01, "Không thể xuất nguyên liệu Quarantine vào production." Generalized
fresh (not copied) from the concept observed in ERP ENLIE's own stock_entry.py validation
during the productization audit (Decision 1: copy the CONCEPT, not the code, when actually
needed) — matched to a generic "any warehouse whose name contains Quarantine" rule rather
than any ENLIE-specific warehouse naming.
"""

import frappe
from frappe import _

_MANUFACTURE_PURPOSES = {"Manufacture", "Material Issue", "Material Transfer for Manufacture"}


def block_quarantine_issue_to_production(doc, method):
	if doc.purpose not in _MANUFACTURE_PURPOSES:
		return
	for row in doc.items:
		if not row.s_warehouse:
			continue
		if "quarantine" in row.s_warehouse.lower():
			frappe.throw(
				_(
					"Cannot issue item {0} from Quarantine warehouse {1} for production. "
					"Material must be QC-approved and moved to an Approved warehouse first."
				).format(row.item_code, row.s_warehouse),
				title=_("Quarantine Hold"),
			)


def block_fg_release_without_qa(doc, method):
	"""DP-506 — master plan §7 DEMO 01 test P06, "FG chưa QA release không được chuyển sang
	Released warehouse." Generalized the same way as block_quarantine_issue_to_production:
	fires on any warehouse whose name contains "released", requiring an Accepted Quality
	Inspection for that exact item+batch before the transfer is allowed."""
	if doc.purpose != "Material Transfer":
		return
	for row in doc.items:
		if not row.t_warehouse or "released" not in row.t_warehouse.lower():
			continue
		if not row.batch_no:
			continue
		has_accepted_qc = frappe.db.exists(
			"Quality Inspection",
			{"item_code": row.item_code, "batch_no": row.batch_no, "status": "Accepted", "docstatus": 1},
		)
		if not has_accepted_qc:
			frappe.throw(
				_(
					"Cannot move batch {0} of item {1} into Released warehouse {2}. "
					"No Accepted Quality Inspection found for this batch — QA release requires QC approval first."
				).format(row.batch_no, row.item_code, row.t_warehouse),
				title=_("QA Release Blocked"),
			)


def block_recalled_batch_delivery(doc, method):
	"""DP-516 — master plan §7 DEMO 05 test PD03, "Recalled batch blocks delivery." ERPNext's
	native Batch.disabled flag isn't enforced anywhere in stock transactions on its own — it
	only hides the batch from UI batch pickers — so this hook repurposes it explicitly as
	"recalled" for this demo and gives it real enforcement teeth at delivery time."""
	for row in doc.items:
		if not row.batch_no:
			continue
		if frappe.db.get_value("Batch", row.batch_no, "disabled"):
			frappe.throw(
				_(
					"Cannot deliver batch {0} of item {1} — this batch has been recalled."
				).format(row.batch_no, row.item_code),
				title=_("Batch Recalled"),
			)
