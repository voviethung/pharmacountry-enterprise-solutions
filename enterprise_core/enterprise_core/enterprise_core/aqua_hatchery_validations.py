"""Golden Demo #18 (Aquaculture Hatchery / Seed Management, master plan DEMO 30) business
rules — AH02/AH03/AH04/AH06.
"""

import frappe
from frappe import _


def aqua_spawning_batch_validate(doc, method):
	"""AH01/AH02 — dam must be Female, sire (if given) must be Male, same sex-check shape as
	Pig/Cattle Farm's breeding-service validation."""
	dam_sex = frappe.db.get_value("Aqua Broodstock", doc.dam, "sex")
	if dam_sex != "Female":
		frappe.throw(_("{0} is not Female.").format(doc.dam), title=_("AH02: Invalid Dam"))
	if doc.sire:
		sire_sex = frappe.db.get_value("Aqua Broodstock", doc.sire, "sex")
		if sire_sex != "Male":
			frappe.throw(_("{0} is not Male.").format(doc.sire), title=_("AH02: Invalid Sire"))


def aqua_larval_batch_validate(doc, method):
	"""AH03 — larval survival rate is always server-computed from the spawning batch's own
	recorded egg_count, never trusted from manual entry. Can only close out a Spawned batch."""
	spawning = frappe.get_doc("Aqua Spawning Batch", doc.spawning_batch)
	if spawning.status != "Spawned":
		frappe.throw(
			_("Cannot record Larval Batch for Spawning Batch {0} — status is '{1}', must be Spawned.").format(doc.spawning_batch, spawning.status),
			title=_("AH03: Spawning Batch Not Active"),
		)
	doc.survival_rate_percent = round((doc.larvae_count / spawning.egg_count) * 100, 2) if spawning.egg_count else 0


def aqua_larval_batch_on_update(doc, method):
	frappe.db.set_value("Aqua Spawning Batch", doc.spawning_batch, "status", "Hatched")


def _block_if_nursery_not_active(doc, method):
	"""AH05 — health records can only be logged against an Active Nursery Batch."""
	status = frappe.db.get_value("Aqua Nursery Batch", doc.nursery_batch, "status")
	if status != "Active":
		frappe.throw(
			_("Cannot log {0} against Nursery Batch {1} — status is '{2}', must be Active.").format(doc.doctype, doc.nursery_batch, status),
			title=_("AH04: Nursery Batch Not Active"),
		)


def aqua_seed_batch_validate(doc, method):
	"""AH04 — graded counts can never exceed the nursery batch's own recorded initial_count.
	Can only grade an Active Nursery Batch."""
	nursery = frappe.get_doc("Aqua Nursery Batch", doc.nursery_batch)
	if nursery.status != "Active":
		frappe.throw(
			_("Cannot grade Nursery Batch {0} — status is '{1}', must be Active.").format(doc.nursery_batch, nursery.status),
			title=_("AH04: Nursery Batch Not Active"),
		)
	graded = (doc.grade_a_count or 0) + (doc.grade_b_count or 0) + (doc.reject_count or 0)
	if nursery.initial_count and graded > nursery.initial_count:
		frappe.throw(
			_("Graded total ({0}) exceeds Nursery Batch {1}'s initial_count ({2}).").format(graded, doc.nursery_batch, nursery.initial_count),
			title=_("AH04: Graded Total Exceeds Batch Size"),
		)


def aqua_seed_batch_on_update(doc, method):
	frappe.db.set_value("Aqua Nursery Batch", doc.nursery_batch, "status", "Graded")


def aqua_seed_dispatch_validate(doc, method):
	"""AH06 — a Seed Batch already Dispatched cannot be dispatched twice."""
	status = frappe.db.get_value("Aqua Seed Batch", doc.seed_batch, "status")
	if status != "Available":
		frappe.throw(
			_("Cannot dispatch Seed Batch {0} — status is '{1}', must be Available.").format(doc.seed_batch, status),
			title=_("AH06: Seed Batch Not Available"),
		)


def aqua_seed_dispatch_on_update(doc, method):
	frappe.db.set_value("Aqua Seed Batch", doc.seed_batch, "status", "Dispatched")
