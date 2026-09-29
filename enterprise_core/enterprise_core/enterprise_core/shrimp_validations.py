"""Golden Demo #8 (Shrimp Farm Management, master plan DEMO 28) business rules —
SF01/SF02/SF03/SF08/SF10.
"""

import frappe
from frappe import _

# Reasonable intensive whiteleg shrimp culture ranges — illustrative thresholds, not a real
# aquaculture spec, same status as the pharma demo's placeholder shelf-life value.
_WATER_THRESHOLDS = {
	"do_mg_l": (4.0, 10.0),
	"ph": (7.5, 8.5),
	"temperature_c": (26.0, 32.0),
	"salinity_ppt": (10.0, 25.0),
	"nh3_mg_l": (0.0, 0.1),
	"no2_mg_l": (0.0, 0.2),
}


def shrimp_pond_validate(doc, method):
	"""SF01 — pond crop lifecycle: status can only move Empty -> Stocked -> Harvested -> Empty
	in that order, never skipping or reversing (e.g. can't harvest an Empty pond)."""
	if doc.is_new():
		return
	before_status = frappe.db.get_value("Shrimp Pond", doc.name, "status")
	valid_transitions = {"Empty": {"Stocked"}, "Stocked": {"Harvested"}, "Harvested": {"Empty"}}
	if before_status != doc.status and doc.status not in valid_transitions.get(before_status, set()):
		frappe.throw(
			_("Invalid pond status transition for {0}: {1} -> {2}.").format(doc.name, before_status, doc.status),
			title=_("SF01: Invalid Pond Lifecycle Transition"),
		)


def shrimp_stocking_batch_validate(doc, method):
	"""SF02 — a Pond can't be stocked twice (must be Empty to accept a new Stocking Batch)."""
	if not doc.is_new():
		return
	pond_status = frappe.db.get_value("Shrimp Pond", doc.pond, "status")
	if pond_status != "Empty":
		frappe.throw(
			_("Cannot stock Pond {0} — status is '{1}', must be Empty.").format(doc.pond, pond_status),
			title=_("SF02: Pond Not Available"),
		)


def shrimp_stocking_batch_on_update(doc, method):
	if doc.status == "Active":
		frappe.db.set_value("Shrimp Pond", doc.pond, "status", "Stocked")


def _block_if_batch_not_active(doc, method):
	"""SF03 — daily feed (and, by the same rule, growth samples/treatments/mortality) can
	only be logged against an Active Stocking Batch."""
	batch_status = frappe.db.get_value("Shrimp Stocking Batch", doc.stocking_batch, "status")
	if batch_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Stocking Batch {1} — status is '{2}', must be Active.").format(
				doc.doctype, doc.stocking_batch, batch_status
			),
			title=_("SF03: Stocking Batch Not Active"),
		)


def shrimp_water_reading_validate(doc, method):
	"""SF10 — alert threshold. Any parameter outside _WATER_THRESHOLDS flags the reading."""
	messages = []
	for field, (low, high) in _WATER_THRESHOLDS.items():
		value = doc.get(field)
		if value is not None and not (low <= value <= high):
			messages.append(f"{field}={value} (expected {low}-{high})")
	doc.is_alert = 1 if messages else 0
	doc.alert_message = "; ".join(messages) if messages else ""


def shrimp_harvest_validate(doc, method):
	"""SF08/SF09 — harvest can only close out an Active Stocking Batch, and computes the KPIs
	(survival rate, FCR, days of culture, cost/kg) from the batch's own recorded history
	rather than trusting manually-entered values — same "server always recomputes" principle
	as Golden Demo #5's L04."""
	batch = frappe.get_doc("Shrimp Stocking Batch", doc.stocking_batch)
	if batch.status != "Active":
		frappe.throw(
			_("Cannot harvest Stocking Batch {0} — status is '{1}', must be Active.").format(doc.stocking_batch, batch.status),
			title=_("SF08: Stocking Batch Not Active"),
		)

	total_mortality = frappe.db.sql(
		"select sum(mortality_count) from `tabShrimp Mortality Record` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	final_count = max(batch.initial_count - total_mortality, 0)
	doc.survival_rate_percent = round((final_count / batch.initial_count) * 100, 2) if batch.initial_count else 0

	total_feed_kg = frappe.db.sql(
		"select sum(qty_kg) from `tabShrimp Daily Feed Log` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	doc.fcr = round(total_feed_kg / doc.total_weight_kg, 2) if doc.total_weight_kg else 0

	doc.days_of_culture = (frappe.utils.getdate(doc.harvest_date) - frappe.utils.getdate(batch.stocking_date)).days

	total_feed_cost = frappe.db.sql(
		"select sum(cost) from `tabShrimp Daily Feed Log` where stocking_batch=%s", (doc.stocking_batch,)
	)[0][0] or 0
	total_cost = (doc.total_cost or 0) + total_feed_cost
	doc.cost_per_kg = round(total_cost / doc.total_weight_kg, 2) if doc.total_weight_kg else 0


def shrimp_harvest_on_update(doc, method):
	frappe.db.set_value("Shrimp Stocking Batch", doc.stocking_batch, "status", "Harvested")
	frappe.db.set_value("Shrimp Pond", frappe.db.get_value("Shrimp Stocking Batch", doc.stocking_batch, "pond"), "status", "Harvested")
