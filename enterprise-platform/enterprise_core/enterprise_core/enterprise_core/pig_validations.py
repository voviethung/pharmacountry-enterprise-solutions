"""Golden Demo #11 (Pig Farm Management, master plan DEMO 22) business rules — PF01/PF02/PF04/PF05.
"""

import frappe
from frappe import _

_GESTATION_DAYS = 114  # average sow gestation length — illustrative, same status as the shrimp
# demo's placeholder water thresholds.


def pig_breeding_service_validate(doc, method):
	"""PF02 (part 1) — breeding lifecycle state machine: Served -> Confirmed Pregnant -> Farrowed,
	or Served/Confirmed Pregnant -> Failed. Never backwards, never skipping. Also computes the
	expected farrow date server-side rather than trusting manual entry."""
	sow_sex = frappe.db.get_value("Pig Breeding Animal", doc.sow, "sex")
	if sow_sex != "Sow":
		frappe.throw(_("{0} is not a Sow.").format(doc.sow), title=_("PF02: Invalid Sow"))
	boar_sex = frappe.db.get_value("Pig Breeding Animal", doc.boar, "sex")
	if boar_sex != "Boar":
		frappe.throw(_("{0} is not a Boar.").format(doc.boar), title=_("PF02: Invalid Boar"))

	if not doc.expected_farrow_date:
		doc.expected_farrow_date = frappe.utils.add_days(doc.service_date, _GESTATION_DAYS)

	if doc.is_new():
		return
	before_status = frappe.db.get_value("Pig Breeding Service", doc.name, "status")
	valid_transitions = {
		"Served": {"Confirmed Pregnant", "Failed"},
		"Confirmed Pregnant": {"Farrowed", "Failed"},
	}
	if before_status != doc.status and doc.status not in valid_transitions.get(before_status, set()):
		frappe.throw(
			_("Invalid breeding lifecycle transition for {0}: {1} -> {2}.").format(doc.name, before_status, doc.status),
			title=_("PF02: Invalid Breeding Lifecycle Transition"),
		)


def pig_farrowing_validate(doc, method):
	"""PF02 (part 2) — a litter can only be recorded against a Breeding Service that reached
	Confirmed Pregnant (not Served, not already Farrowed/Failed)."""
	service_status = frappe.db.get_value("Pig Breeding Service", doc.breeding_service, "status")
	if service_status != "Confirmed Pregnant":
		frappe.throw(
			_("Cannot record Farrowing for Breeding Service {0} — status is '{1}', must be Confirmed Pregnant.").format(
				doc.breeding_service, service_status
			),
			title=_("PF02: Breeding Service Not Confirmed Pregnant"),
		)


def pig_farrowing_on_update(doc, method):
	frappe.db.set_value("Pig Breeding Service", doc.breeding_service, "status", "Farrowed")


def pig_grower_batch_validate(doc, method):
	"""PF01 (pen half) — a Pen can't take a second Grower Batch while occupied (same lifecycle
	guard shape as Shrimp Farm's SF02 pond-stocking rule)."""
	if not doc.is_new():
		return
	pen_status = frappe.db.get_value("Pig Pen", doc.pen, "status")
	if pen_status != "Empty":
		frappe.throw(
			_("Cannot place Batch in Pen {0} — status is '{1}', must be Empty.").format(doc.pen, pen_status),
			title=_("PF01: Pen Not Available"),
		)


def pig_grower_batch_on_update(doc, method):
	if doc.status == "Active":
		frappe.db.set_value("Pig Pen", doc.pen, "status", "Occupied")


def _block_if_batch_not_active(doc, method):
	"""PF03/PF04/PF06 — feed logs, vaccinations, weight records and mortality can only be
	logged against an Active Grower Batch (same rule shape as Shrimp Farm's SF03)."""
	batch_status = frappe.db.get_value("Pig Grower Batch", doc.batch, "status")
	if batch_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Batch {1} — status is '{2}', must be Active.").format(doc.doctype, doc.batch, batch_status),
			title=_("PF03: Batch Not Active"),
		)


def pig_vaccination_validate(doc, method):
	"""PF04 — vaccination due/overdue status is always server-computed, never manually set."""
	_block_if_batch_not_active(doc, method)
	if doc.administered_date:
		doc.status = "Administered"
	elif doc.due_date and frappe.utils.getdate(doc.due_date) < frappe.utils.getdate(frappe.utils.nowdate()):
		doc.status = "Overdue"
	else:
		doc.status = "Due"


def pig_medicine_treatment_validate(doc, method):
	"""PF05 — withdrawal end date is always server-computed from treatment_date + withdrawal_days,
	never trusted from manual entry (same principle as Golden Demo #9's Vet Mfg withdrawal fields)."""
	_block_if_batch_not_active(doc, method)
	doc.withdrawal_end_date = frappe.utils.add_days(doc.treatment_date, doc.withdrawal_days)


def pig_sale_lot_validate(doc, method):
	"""PF05 (enforcement) + PF07 — a batch still inside an active medicine withdrawal period
	cannot be sold; cost allocation (feed + medicine + other) and profit are always
	server-recomputed from the batch's own recorded history, same "server always recomputes"
	principle as Golden Demo #8's shrimp_harvest_validate."""
	batch = frappe.get_doc("Pig Grower Batch", doc.batch)
	if batch.status != "Active":
		frappe.throw(
			_("Cannot sell Batch {0} — status is '{1}', must be Active.").format(doc.batch, batch.status),
			title=_("PF-lifecycle: Batch Not Active"),
		)

	latest_withdrawal_end = frappe.db.sql(
		"select max(withdrawal_end_date) from `tabPig Medicine Treatment` where batch=%s", (doc.batch,)
	)[0][0]
	if latest_withdrawal_end and frappe.utils.getdate(latest_withdrawal_end) >= frappe.utils.getdate(doc.sale_date):
		frappe.throw(
			_("Cannot sell Batch {0} on {1} — medicine withdrawal period active until {2}.").format(doc.batch, doc.sale_date, latest_withdrawal_end),
			title=_("PF05: Medicine Withdrawal Period Active"),
		)

	total_feed_cost = frappe.db.sql("select sum(cost) from `tabPig Feed Log` where batch=%s", (doc.batch,))[0][0] or 0
	total_medicine_cost = frappe.db.sql("select sum(cost) from `tabPig Medicine Treatment` where batch=%s", (doc.batch,))[0][0] or 0
	doc.total_feed_cost = total_feed_cost
	doc.total_medicine_cost = total_medicine_cost
	doc.total_cost = total_feed_cost + total_medicine_cost + (doc.other_cost or 0)
	doc.cost_per_kg = round(doc.total_cost / doc.total_weight_kg, 2) if doc.total_weight_kg else 0
	doc.profit = (doc.sale_price or 0) - doc.total_cost


def pig_sale_lot_on_update(doc, method):
	frappe.db.set_value("Pig Grower Batch", doc.batch, {"status": "Sold", "stage": "Sold"})
	pen = frappe.db.get_value("Pig Grower Batch", doc.batch, "pen")
	if pen:
		frappe.db.set_value("Pig Pen", pen, "status", "Empty")
