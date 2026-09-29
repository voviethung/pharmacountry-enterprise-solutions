"""Golden Demo #22 (Medical Device Manufacturing, master plan DEMO 04) business rules —
MD02/MD03/MD04/MD07.
"""

import frappe
from frappe import _


def meddev_bom_validate(doc, method):
	"""MD02 — a BOM can only become the active default through an Approved Design Change
	Record. Reversal of the earlier is_default-flip demos' concern: those proved a REVISION
	doesn't corrupt history; this proves a revision can't even take effect without documented
	change control.

	Scoped to Medical Device's own company — a real cross-demo bug found by Golden Demo #26
	(Premix)'s own registry run: this hook originally fired on ANY is_default BOM platform-wide
	(no company/item scoping at all), unconditionally requiring `design_change_record` to be
	set. That was latent and undetected since Golden Demo #22 because no manufacturing demo
	created a NEW BOM afterward until Premix — every BOM-owning demo before it (Feed, Vet Mfg,
	Aqua Env, Supplement, Cosmetics) had already finished creating its BOMs before this hook
	even existed. Fixed the same way this session scopes every other cross-cutting hook
	(warehouse-name patterns, item flags): only Medical Device's own company is affected, so
	every other demo's BOM (this field is empty for all of them) is left alone, same as before
	this fix for MedDev itself."""
	if not doc.is_default or doc.company != "Demo MedDevice Co.":
		return
	if not doc.design_change_record:
		frappe.throw(_("Cannot make BOM {0} the default — no Design Change Record linked.").format(doc.name), title=_("MD02: Design Change Record Required"))
	status = frappe.db.get_value("MedDev Design Change Record", doc.design_change_record, "status")
	if status != "Approved":
		frappe.throw(
			_("Cannot make BOM {0} the default — linked Design Change Record {1} is '{2}', must be Approved.").format(doc.name, doc.design_change_record, status),
			title=_("MD02: Design Change Record Not Approved"),
		)


def meddev_block_critical_supplier_not_approved(doc, method):
	"""MD03 — a critical supplier must be Approved before a Purchase Order can be raised
	against them."""
	is_critical, quality_status = frappe.db.get_value("Supplier", doc.supplier, ["is_critical_supplier", "quality_status"]) or (0, None)
	if is_critical and quality_status != "Approved":
		frappe.throw(
			_("Cannot raise a Purchase Order against critical Supplier {0} — quality_status is '{1}', must be Approved.").format(doc.supplier, quality_status),
			title=_("MD03: Critical Supplier Not Approved"),
		)


def meddev_block_rejected_material_use(doc, method):
	"""MD04 — incoming material with a Rejected Quality Inspection can't be transferred into
	assembly (any warehouse whose name contains "wip"), same warehouse-name-pattern matching
	shape as block_fg_release_without_qa, inverted: blocks on REJECTED existing rather than
	ACCEPTED missing."""
	if doc.purpose != "Material Transfer":
		return
	for row in doc.items:
		if not row.t_warehouse or "wip" not in row.t_warehouse.lower():
			continue
		if not row.batch_no:
			continue
		rejected = frappe.db.exists("Quality Inspection", {"item_code": row.item_code, "batch_no": row.batch_no, "status": "Rejected", "docstatus": 1})
		if rejected:
			frappe.throw(
				_("Cannot move batch {0} of item {1} into WIP warehouse {2} — a Rejected Quality Inspection exists for this batch.").format(row.batch_no, row.item_code, row.t_warehouse),
				title=_("MD04: Rejected Material Blocked"),
			)


def meddev_block_overdue_equipment_operation(doc, method):
	"""MD07 — a Work Order configured against equipment whose calibration is overdue is
	blocked, same "most recently PERFORMED Pass calibration, not due_date alone" ordering logic
	as Golden Demo #6's E06 qualification check (reused, not reinvented)."""
	if not doc.get("equipment"):
		return
	latest_due = frappe.db.get_value(
		"EAM Calibration Record", {"asset": doc.equipment, "result": "Pass"}, "due_date", order_by="calibration_date desc, creation desc"
	)
	if not latest_due:
		frappe.throw(_("Cannot configure Work Order against Equipment {0} — no passing calibration record exists.").format(doc.equipment), title=_("MD07: Calibration Required"))
	if frappe.utils.getdate(latest_due) < frappe.utils.getdate():
		frappe.throw(
			_("Cannot configure Work Order against Equipment {0} — its calibration was due {1} and is overdue.").format(doc.equipment, latest_due),
			title=_("MD07: Calibration Overdue"),
		)
