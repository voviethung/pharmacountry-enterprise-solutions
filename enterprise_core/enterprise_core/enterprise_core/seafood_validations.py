"""Golden Demo #19 (Seafood Processing & Export, master plan DEMO 32) business rules —
SP02/SP06.
"""

import frappe
from frappe import _


def seafood_grading_validate(doc, method):
	"""SP02 — grade/yield is always server-computed from the harvest lot's own recorded
	received_weight_kg, never trusted from manual entry (same "server always recomputes"
	principle as every prior harvest/sale doctype in this platform). Graded weight can never
	exceed what was actually received."""
	harvest_lot = frappe.get_doc("Seafood Harvest Lot", doc.harvest_lot)
	graded = (doc.grade_a_kg or 0) + (doc.grade_b_kg or 0) + (doc.reject_kg or 0)
	if harvest_lot.received_weight_kg and graded > harvest_lot.received_weight_kg:
		frappe.throw(
			_("Graded weight ({0}kg) exceeds Harvest Lot {1}'s received_weight_kg ({2}kg).").format(graded, doc.harvest_lot, harvest_lot.received_weight_kg),
			title=_("SP02: Graded Weight Exceeds Received Weight"),
		)
	good_weight = (doc.grade_a_kg or 0) + (doc.grade_b_kg or 0)
	doc.yield_percent = round((good_weight / harvest_lot.received_weight_kg) * 100, 2) if harvest_lot.received_weight_kg else 0


def seafood_shipment_validate(doc, method):
	"""SP06 — a Packing Lot already Shipped cannot be shipped twice."""
	status = frappe.db.get_value("Seafood Packing Lot", doc.packing_lot, "status")
	if status != "Available":
		frappe.throw(
			_("Cannot ship Packing Lot {0} — status is '{1}', must be Available.").format(doc.packing_lot, status),
			title=_("SP06: Packing Lot Not Available"),
		)


def seafood_shipment_on_update(doc, method):
	frappe.db.set_value("Seafood Packing Lot", doc.packing_lot, "status", "Shipped")
	cold_storage = frappe.db.get_value("Seafood Cold Storage Record", {"packing_lot": doc.packing_lot}, "name")
	if cold_storage:
		frappe.db.set_value("Seafood Cold Storage Record", cold_storage, "status", "Shipped")
