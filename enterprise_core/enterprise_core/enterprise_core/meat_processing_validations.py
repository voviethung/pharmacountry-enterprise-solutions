"""Golden Demo #28 (Meat / Animal Product Processing, master plan DEMO 31) business rules —
MP02 (yield, server-computed, over-yield blocked at both the carcass AND cut stages) and MP04
(QC hold/release — a Packing Lot cannot be created against a Processing Batch that isn't
Released, the "goods held pending QC" gate the master plan explicitly calls out as its own
lettered test, unlike kin demo Seafood Processing). Also a light MP05/MP06 chain-closure hook on
Meat Distribution, mirroring Seafood's own shipment closure pattern exactly.
"""

import frappe
from frappe import _


def meat_processing_batch_validate(doc, method):
	"""MP02 — carcass yield % and cut yield % are always server-computed from the batch's own
	sources child table (never trusted from manual entry, same "server always recomputes"
	principle as every prior harvest/grading doctype in this platform). Carcass weight can never
	exceed the total live weight actually consumed, and cut weight can never exceed the carcass
	weight it was cut from — two independent over-yield gates, one per processing stage."""
	total_live = sum((row.live_weight_kg or 0) for row in (doc.sources or []))
	doc.total_live_weight_kg = total_live

	if total_live and (doc.carcass_weight_kg or 0) > total_live:
		frappe.throw(
			_("Carcass weight ({0}kg) exceeds the total live weight actually consumed from the batch's own sources ({1}kg).").format(doc.carcass_weight_kg, total_live),
			title=_("MP02: Carcass Weight Exceeds Live Weight"),
		)
	if (doc.output_cut_weight_kg or 0) > (doc.carcass_weight_kg or 0):
		frappe.throw(
			_("Output cut weight ({0}kg) exceeds the carcass weight it was cut from ({1}kg).").format(doc.output_cut_weight_kg, doc.carcass_weight_kg),
			title=_("MP02: Cut Weight Exceeds Carcass Weight"),
		)

	doc.carcass_yield_percent = round((doc.carcass_weight_kg / total_live) * 100, 2) if total_live else 0
	doc.cut_yield_percent = round((doc.output_cut_weight_kg / doc.carcass_weight_kg) * 100, 2) if doc.carcass_weight_kg else 0


def meat_packing_lot_validate(doc, method):
	"""MP04 — a real hold/release gate: a Processing Batch's output cannot be packed (and
	therefore cannot reach cold storage or distribution) until its own QC has explicitly
	Released it. Modeled directly after Premix's Weighing Verification Pending/Verified gate and
	3PL's quarantine-release gate — both already-established "blocked at insert() time, not just
	a status label" patterns in this session. Also server-computes total_packed_weight_kg (never
	trusted from manual entry, same "server always recomputes" principle as every other derived
	field in this platform)."""
	qc_status = frappe.db.get_value("Meat Processing Batch", doc.processing_batch, "qc_status")
	if qc_status != "Released":
		frappe.throw(
			_("Cannot pack Processing Batch {0} — QC status is '{1}', must be Released. Goods are held pending QC.").format(doc.processing_batch, qc_status),
			title=_("MP04: Processing Batch Not QC-Released"),
		)
	doc.total_packed_weight_kg = (doc.carton_count or 0) * (doc.net_weight_per_carton_kg or 0)


def meat_distribution_validate(doc, method):
	"""A Packing Lot already Distributed cannot be distributed twice — same lifecycle-closure
	shape as Seafood's SP06 double-shipment gate."""
	status = frappe.db.get_value("Meat Packing Lot", doc.packing_lot, "status")
	if status != "Available":
		frappe.throw(
			_("Cannot distribute Packing Lot {0} — status is '{1}', must be Available.").format(doc.packing_lot, status),
			title=_("Packing Lot Not Available"),
		)


def meat_distribution_on_update(doc, method):
	frappe.db.set_value("Meat Packing Lot", doc.packing_lot, "status", "Distributed")
	cold_storage = frappe.db.get_value("Meat Cold Storage Record", {"packing_lot": doc.packing_lot}, "name")
	if cold_storage:
		frappe.db.set_value("Meat Cold Storage Record", cold_storage, "status", "Distributed")
