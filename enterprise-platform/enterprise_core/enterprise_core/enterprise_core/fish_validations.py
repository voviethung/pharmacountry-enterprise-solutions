"""Golden Demo #17 (Fish Farm Management, master plan DEMO 29) business rules —
FF01/FF02/FF03/FF05/FF06.
"""

import frappe
from frappe import _


def fish_pond_validate(doc, method):
	"""FF01 — pond/cage crop lifecycle: status can only move Empty -> Stocked -> Harvested ->
	Empty in that order, never skipping or reversing (same shape as Shrimp Pond's SF01)."""
	if doc.is_new():
		return
	before_status = frappe.db.get_value("Fish Pond", doc.name, "status")
	valid_transitions = {"Empty": {"Stocked"}, "Stocked": {"Harvested"}, "Harvested": {"Empty"}}
	if before_status != doc.status and doc.status not in valid_transitions.get(before_status, set()):
		frappe.throw(
			_("Invalid pond/cage status transition for {0}: {1} -> {2}.").format(doc.name, before_status, doc.status),
			title=_("FF01: Invalid Pond Lifecycle Transition"),
		)


def fish_stocking_batch_validate(doc, method):
	"""FF01 — a Pond/Cage can't be stocked twice (must be Empty to accept a new Stocking Batch)."""
	if not doc.is_new():
		return
	pond_status = frappe.db.get_value("Fish Pond", doc.pond, "status")
	if pond_status != "Empty":
		frappe.throw(
			_("Cannot stock Pond/Cage {0} — status is '{1}', must be Empty.").format(doc.pond, pond_status),
			title=_("FF01: Pond Not Available"),
		)


def fish_stocking_batch_on_update(doc, method):
	if doc.status == "Active":
		frappe.db.set_value("Fish Pond", doc.pond, "status", "Stocked")


def _block_if_batch_not_active(doc, method):
	"""FF03/FF05 — feed logs and mortality can only be logged against an Active Stocking Batch."""
	batch_status = frappe.db.get_value("Fish Stocking Batch", doc.stocking_batch, "status")
	if batch_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Stocking Batch {1} — status is '{2}', must be Active.").format(doc.doctype, doc.stocking_batch, batch_status),
			title=_("FF01: Stocking Batch Not Active"),
		)


def fish_growth_sample_validate(doc, method):
	"""FF02/FF04 — biomass estimate is server-computed from the batch's own recorded mortality
	history, not entered manually: estimated_population = initial_count - mortality recorded
	ON OR BEFORE this sample's own date, estimated_biomass_kg = average_weight_g *
	estimated_population / 1000. Filtering by record_date (not just summing every mortality
	record for the batch) matters: without it, the result would depend on the ORDER records
	happen to be inserted in rather than their actual dates — a growth sample dated before a
	later-entered-but-earlier-occurring mortality event would incorrectly include it, and a
	re-run-safe seed registry can create records in any order."""
	_block_if_batch_not_active(doc, method)
	batch = frappe.get_doc("Fish Stocking Batch", doc.stocking_batch)
	total_mortality = frappe.db.sql(
		"select sum(mortality_count) from `tabFish Mortality Record` where stocking_batch=%s and record_date <= %s", (doc.stocking_batch, doc.sample_date)
	)[0][0] or 0
	doc.estimated_population = max(batch.initial_count - total_mortality, 0)
	doc.estimated_biomass_kg = round((doc.average_weight_g * doc.estimated_population) / 1000, 2)


def fish_harvest_validate(doc, method):
	"""FF06 — harvest can only close out an Active Stocking Batch, and computes the KPIs
	(survival rate, FCR, days of culture, cost/kg) from the batch's own recorded history rather
	than trusting manually-entered values — same "server always recomputes" principle as Shrimp
	Farm's SF08/SF09."""
	batch = frappe.get_doc("Fish Stocking Batch", doc.stocking_batch)
	if batch.status != "Active":
		frappe.throw(
			_("Cannot harvest Stocking Batch {0} — status is '{1}', must be Active.").format(doc.stocking_batch, batch.status),
			title=_("FF06: Stocking Batch Not Active"),
		)

	total_mortality = frappe.db.sql(
		"select sum(mortality_count) from `tabFish Mortality Record` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	final_count = max(batch.initial_count - total_mortality, 0)
	doc.survival_rate_percent = round((final_count / batch.initial_count) * 100, 2) if batch.initial_count else 0

	total_feed_kg = frappe.db.sql(
		"select sum(qty_kg) from `tabFish Feed Log` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	doc.fcr = round(total_feed_kg / doc.total_weight_kg, 2) if doc.total_weight_kg else 0

	doc.days_of_culture = (frappe.utils.getdate(doc.harvest_date) - frappe.utils.getdate(batch.stocking_date)).days

	total_feed_cost = frappe.db.sql(
		"select sum(cost) from `tabFish Feed Log` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	total_cost = (doc.total_cost or 0) + total_feed_cost
	doc.cost_per_kg = round(total_cost / doc.total_weight_kg, 2) if doc.total_weight_kg else 0


def fish_harvest_on_update(doc, method):
	frappe.db.set_value("Fish Stocking Batch", doc.stocking_batch, "status", "Harvested")
	frappe.db.set_value("Fish Pond", frappe.db.get_value("Fish Stocking Batch", doc.stocking_batch, "pond"), "status", "Harvested")
