"""Golden Demo #14 (Hatchery / Breeding Management, master plan DEMO 25) business rules —
H02/H03/H04/H05/H06.
"""

import frappe
from frappe import _

_INCUBATION_DAYS = 21  # average chicken egg incubation period — illustrative, same status as
# every prior farm demo's placeholder gestation/cycle-length constants.


def hatchery_incubation_validate(doc, method):
	"""H02 — an Incubator can't take a second batch while occupied (same occupancy-guard shape
	as Shrimp Pond/Pig Pen/Poultry House)."""
	if doc.is_new():
		incubator_status = frappe.db.get_value("Hatchery Incubator", doc.incubator, "status")
		if incubator_status != "Empty":
			frappe.throw(
				_("Cannot assign Egg Batch to Incubator {0} — status is '{1}', must be Empty.").format(doc.incubator, incubator_status),
				title=_("H02: Incubator Not Available"),
			)
	if not doc.expected_hatch_date:
		doc.expected_hatch_date = frappe.utils.add_days(doc.start_date, _INCUBATION_DAYS)


def hatchery_incubation_on_update(doc, method):
	if doc.status == "Incubating":
		frappe.db.set_value("Hatchery Incubator", doc.incubator, "status", "Occupied")
		frappe.db.set_value("Hatchery Egg Batch", doc.egg_batch, "status", "Incubating")


def hatchery_hatch_result_validate(doc, method):
	"""H03 — hatch rate is always server-computed from the egg batch's own recorded egg_count,
	never trusted from manual entry (same "server always recomputes" principle as every prior
	harvest/sale doctype in this platform). Can only close out an Incubating Incubation."""
	incubation = frappe.get_doc("Hatchery Incubation", doc.incubation)
	if incubation.status != "Incubating":
		frappe.throw(
			_("Cannot record Hatch Result for Incubation {0} — status is '{1}', must be Incubating.").format(doc.incubation, incubation.status),
			title=_("H03: Incubation Not Active"),
		)
	egg_count = frappe.db.get_value("Hatchery Egg Batch", incubation.egg_batch, "egg_count")
	accounted = (doc.hatched_count or 0) + (doc.infertile_count or 0) + (doc.dead_in_shell_count or 0)
	if egg_count and accounted > egg_count:
		frappe.throw(
			_("Hatched + infertile + dead-in-shell ({0}) exceeds the egg batch's own egg_count ({1}).").format(accounted, egg_count),
			title=_("H03: Hatch Counts Exceed Egg Batch"),
		)
	doc.hatch_rate_percent = round((doc.hatched_count / egg_count) * 100, 2) if egg_count else 0


def hatchery_hatch_result_on_update(doc, method):
	incubation = frappe.get_doc("Hatchery Incubation", doc.incubation)
	frappe.db.set_value("Hatchery Incubation", incubation.name, "status", "Hatched")
	frappe.db.set_value("Hatchery Egg Batch", incubation.egg_batch, "status", "Hatched")
	frappe.db.set_value("Hatchery Incubator", incubation.incubator, "status", "Empty")


def hatchery_chick_grading_validate(doc, method):
	"""H04 — graded counts can never exceed the chick batch's own recorded initial_count."""
	initial_count = frappe.db.get_value("Hatchery Chick Batch", doc.chick_batch, "initial_count")
	graded = (doc.grade_a_count or 0) + (doc.grade_b_count or 0) + (doc.reject_count or 0)
	if initial_count and graded > initial_count:
		frappe.throw(
			_("Graded total ({0}) exceeds Chick Batch {1}'s initial_count ({2}).").format(graded, doc.chick_batch, initial_count),
			title=_("H04: Graded Total Exceeds Batch Size"),
		)


def _block_if_chick_batch_not_active(doc, method):
	"""H05 — vaccination can only be logged against an Active Chick Batch."""
	batch_status = frappe.db.get_value("Hatchery Chick Batch", doc.chick_batch, "status")
	if batch_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Chick Batch {1} — status is '{2}', must be Active.").format(doc.doctype, doc.chick_batch, batch_status),
			title=_("H-lifecycle: Chick Batch Not Active"),
		)


def hatchery_vaccination_validate(doc, method):
	"""H05 — vaccination due/overdue status is always server-computed, never manually set."""
	_block_if_chick_batch_not_active(doc, method)
	if doc.administered_date:
		doc.status = "Administered"
	elif doc.due_date and frappe.utils.getdate(doc.due_date) < frappe.utils.getdate(frappe.utils.nowdate()):
		doc.status = "Overdue"
	else:
		doc.status = "Due"


def hatchery_dispatch_validate(doc, method):
	"""H06 — a Chick Batch already Dispatched cannot be dispatched twice."""
	batch_status = frappe.db.get_value("Hatchery Chick Batch", doc.chick_batch, "status")
	if batch_status != "Active":
		frappe.throw(
			_("Cannot dispatch Chick Batch {0} — status is '{1}', must be Active.").format(doc.chick_batch, batch_status),
			title=_("H06: Chick Batch Not Active"),
		)


def hatchery_dispatch_on_update(doc, method):
	frappe.db.set_value("Hatchery Chick Batch", doc.chick_batch, "status", "Dispatched")
