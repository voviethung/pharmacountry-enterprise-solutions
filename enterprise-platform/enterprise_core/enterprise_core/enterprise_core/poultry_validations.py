"""Golden Demo #12 (Poultry Farm Management, master plan DEMO 23) business rules —
PO01/PO02/PO04/PO06.
"""

import frappe
from frappe import _


def poultry_flock_validate(doc, method):
	"""PO01 — a House can't take a second Flock while occupied (same lifecycle guard shape as
	Shrimp Farm's SF02 / Pig Farm's PF01 pen rule)."""
	if not doc.is_new():
		return
	house_status = frappe.db.get_value("Poultry House", doc.house, "status")
	if house_status != "Empty":
		frappe.throw(
			_("Cannot place Flock in House {0} — status is '{1}', must be Empty.").format(doc.house, house_status),
			title=_("PO01: House Not Available"),
		)


def poultry_flock_on_update(doc, method):
	if doc.status == "Active":
		frappe.db.set_value("Poultry House", doc.house, "status", "Occupied")


def _block_if_flock_not_active(doc, method):
	"""PO02/PO03/PO04/PO05 — mortality, feed, vaccination and weight records can only be
	logged against an Active Flock."""
	flock_status = frappe.db.get_value("Poultry Flock", doc.flock, "status")
	if flock_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Flock {1} — status is '{2}', must be Active.").format(doc.doctype, doc.flock, flock_status),
			title=_("PO01: Flock Not Active"),
		)


def poultry_vaccination_validate(doc, method):
	"""PO04 — vaccination due/overdue status is always server-computed, never manually set."""
	_block_if_flock_not_active(doc, method)
	if doc.administered_date:
		doc.status = "Administered"
	elif doc.due_date and frappe.utils.getdate(doc.due_date) < frappe.utils.getdate(frappe.utils.nowdate()):
		doc.status = "Overdue"
	else:
		doc.status = "Due"


def poultry_egg_production_validate(doc, method):
	"""PO06 — egg production can only be logged for a Layer flock, not a Broiler."""
	_block_if_flock_not_active(doc, method)
	flock_type = frappe.db.get_value("Poultry Flock", doc.flock, "flock_type")
	if flock_type != "Layer":
		frappe.throw(
			_("Cannot log egg production for Flock {0} — flock_type is '{1}', must be Layer.").format(doc.flock, flock_type),
			title=_("PO06: Not a Layer Flock"),
		)


def poultry_sale_lot_validate(doc, method):
	"""PO07 — a Flock still Sold cannot be sold twice; cost allocation (feed + other),
	cost/kg, profit and livability are always server-recomputed from the flock's own recorded
	history, same "server always recomputes" principle as Shrimp Harvest / Pig Sale Lot."""
	flock = frappe.get_doc("Poultry Flock", doc.flock)
	if flock.status != "Active":
		frappe.throw(
			_("Cannot sell Flock {0} — status is '{1}', must be Active.").format(doc.flock, flock.status),
			title=_("PO01: Flock Not Active"),
		)

	total_feed_cost = frappe.db.sql("select sum(cost) from `tabPoultry Feed Log` where flock=%s", (doc.flock,))[0][0] or 0
	doc.total_feed_cost = total_feed_cost
	doc.total_cost = total_feed_cost + (doc.other_cost or 0)
	doc.cost_per_kg = round(doc.total_cost / doc.total_weight_kg, 2) if doc.total_weight_kg else 0
	doc.profit = (doc.sale_price or 0) - doc.total_cost

	total_mortality = frappe.db.sql("select sum(mortality_count) from `tabPoultry Mortality Record` where flock=%s", (doc.flock,))[0][0] or 0
	final_count = max(flock.initial_count - total_mortality, 0)
	doc.livability_percent = round((final_count / flock.initial_count) * 100, 2) if flock.initial_count else 0


def poultry_sale_lot_on_update(doc, method):
	frappe.db.set_value("Poultry Flock", doc.flock, "status", "Sold")
	house = frappe.db.get_value("Poultry Flock", doc.flock, "house")
	if house:
		frappe.db.set_value("Poultry House", house, "status", "Empty")
