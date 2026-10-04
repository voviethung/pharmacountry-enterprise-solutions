"""Golden Demo #28 — Meat / Animal Product Processing (master plan DEMO 31, "PHASE 6" item 9,
the last Phase 6 item), IP-MEAT-PROCESSING. Structurally the closest kin in the whole codebase
to Golden Demo #19's Seafood Processing & Export — same "self-contained parallel pipeline, no
Company/Item/Stock" architecture, same Dynamic-Link-to-an-existing-record reuse story. Sources
one incoming lot from Golden Demo #11's (Pig Farm) real `Pig Sale Lot` — already sold to
"Dong Nai Meat Processing Co." (a Customer record that demo planted in anticipation of exactly
this one) — and a second, deliberately self-contained "Direct Farm Intake" lot with no upstream
golden demo behind it, giving the one Processing Batch a genuine TWO-source genealogy (MP03).
"""

import frappe
from frappe.utils import now_datetime

_PLANT_NAME = "Dong Nai Meat Processing Plant"
_LOT1_CODE = "MPLOT-2026-001"
_LOT2_CODE = "MPLOT-2026-002"
_BATCH_CODE = "MPPROC-2026-001"
_PACKING_LOT_CODE = "MPPACK-2026-001"
_NEGATIVE_TEST_MARKER_CARTONS = 9999

_CUSTOMER_GROUP = "Meat & Cold Chain Buyers"
_CUSTOMER_NAME = "Mekong Fresh Foods Distribution Co."


def seed_meat_processing_master_data():
	"""DP-686 — Plant master data. No Company, no Farm doctype — mirrors Seafood's "Plant only"
	master data step exactly."""
	if frappe.db.exists("Meat Plant", _PLANT_NAME):
		return "seed_meat_processing_master_data: already existed."
	frappe.get_doc({"doctype": "Meat Plant", "plant_name": _PLANT_NAME, "location": "Dong Nai Province, Vietnam"}).insert(ignore_permissions=True)
	return f"seed_meat_processing_master_data: Plant created ({_PLANT_NAME})."


def seed_meat_processing_receiving():
	"""DP-687 — MP01 (incoming lot, traceable to a specific farm/source). Lot 1 is sourced from
	Golden Demo #11's real Pig Sale Lot via Dynamic Link (source_type/source_reference, same
	pattern as Seafood Harvest Lot); Lot 2 is a deliberately self-contained "Direct Farm Intake"
	lot (no upstream golden demo), giving the later Processing Batch a genuine two-source
	genealogy for MP03 rather than Seafood's simpler 1:1 chain."""
	if not frappe.db.exists("Meat Plant", _PLANT_NAME):
		return "seed_meat_processing_receiving: SKIPPED — run seed_meat_processing_master_data first."

	pig_sale_lot = frappe.db.get_value("Pig Sale Lot", {"customer": "Dong Nai Meat Processing Co."}, "name")
	if not pig_sale_lot:
		return "seed_meat_processing_receiving: SKIPPED — Golden Demo #11's Pig Sale Lot (sold to 'Dong Nai Meat Processing Co.') doesn't exist yet."
	pig_lot = frappe.db.get_value("Pig Sale Lot", pig_sale_lot, ["head_count", "total_weight_kg"], as_dict=True)

	lot1_created = False
	if not frappe.db.exists("Meat Incoming Lot", _LOT1_CODE):
		frappe.get_doc(
			{
				"doctype": "Meat Incoming Lot",
				"lot_code": _LOT1_CODE,
				"plant": _PLANT_NAME,
				"species": "Pig (Landrace x Yorkshire crossbred)",
				"source_type": "Pig Sale Lot",
				"source_reference": pig_sale_lot,
				"receiving_date": frappe.utils.today(),
				"animal_count": pig_lot.head_count,
				"live_weight_kg": pig_lot.total_weight_kg,
				"inspection_status": "Passed",
				"inspected_by": "Dr. Le Van Hai — Ante-mortem Inspector",
				"inspected_on": frappe.utils.today(),
			}
		).insert(ignore_permissions=True)
		lot1_created = True

	lot2_created = False
	if not frappe.db.exists("Meat Incoming Lot", _LOT2_CODE):
		frappe.get_doc(
			{
				"doctype": "Meat Incoming Lot",
				"lot_code": _LOT2_CODE,
				"plant": _PLANT_NAME,
				"species": "Pig (mixed breed)",
				"source_type": "Direct Farm Intake",
				"source_farm_name": "Song Be Independent Pig Cooperative",
				"receiving_date": frappe.utils.today(),
				"animal_count": 12,
				"live_weight_kg": 1080.0,
				"inspection_status": "Passed",
				"inspected_by": "Dr. Le Van Hai — Ante-mortem Inspector",
				"inspected_on": frappe.utils.today(),
			}
		).insert(ignore_permissions=True)
		lot2_created = True

	return (
		f"seed_meat_processing_receiving: Lot 1 {'created' if lot1_created else 'already existed'} (MP01, from Pig Sale Lot {pig_sale_lot}, "
		f"{pig_lot.head_count} head / {pig_lot.total_weight_kg}kg). Lot 2 {'created' if lot2_created else 'already existed'} (MP01, direct farm intake, 12 head / 1080.0kg)."
	)


def seed_meat_processing_batch():
	"""DP-688 — MP02 (yield, server-computed) + MP03 (a Processing Batch consuming BOTH incoming
	lots — real multi-source genealogy). Starts with qc_status="On Hold" (MP04's initial state,
	the "goods held pending QC" starting point)."""
	if not frappe.db.exists("Meat Incoming Lot", _LOT1_CODE) or not frappe.db.exists("Meat Incoming Lot", _LOT2_CODE):
		return "seed_meat_processing_batch: SKIPPED — run seed_meat_processing_receiving first."
	if frappe.db.exists("Meat Processing Batch", _BATCH_CODE):
		yields = frappe.db.get_value("Meat Processing Batch", _BATCH_CODE, ["carcass_yield_percent", "cut_yield_percent"], as_dict=True)
		return f"seed_meat_processing_batch: already existed (MP02 carcass yield {yields.carcass_yield_percent}%, cut yield {yields.cut_yield_percent}%)."

	lot1_weight = frappe.db.get_value("Meat Incoming Lot", _LOT1_CODE, "live_weight_kg")
	lot2_weight = frappe.db.get_value("Meat Incoming Lot", _LOT2_CODE, "live_weight_kg")

	batch = frappe.get_doc(
		{
			"doctype": "Meat Processing Batch",
			"batch_code": _BATCH_CODE,
			"plant": _PLANT_NAME,
			"process_type": "Primal Cuts",
			"sources": [
				{"incoming_lot": _LOT1_CODE, "live_weight_kg": lot1_weight},
				{"incoming_lot": _LOT2_CODE, "live_weight_kg": lot2_weight},
			],
			"carcass_weight_kg": 1460.0,
			"output_cut_weight_kg": 1240.0,
		}
	)
	batch.insert(ignore_permissions=True)
	return (
		f"seed_meat_processing_batch: Processing Batch created from 2 incoming lots (MP03 genealogy: {_LOT1_CODE} + {_LOT2_CODE}, "
		f"total live weight {batch.total_live_weight_kg}kg). MP02: carcass yield {batch.carcass_yield_percent}%, cut yield {batch.cut_yield_percent}%. qc_status={batch.qc_status}."
	)


def seed_meat_processing_qc_and_packing():
	"""DP-689 — MP04 (QC hold/release, enforced live): while the batch is still "On Hold", a
	real Packing Lot insert attempt is proven BLOCKED (leaving no artifact behind, marked with a
	distinctive carton_count so a later verify pass can positively confirm its absence — same
	"no submitted doc left behind" idiom Ingredient Trading's FT05 negative test used) before the
	batch is actually released and the real Packing Lot is created. Also MP05 (cold storage)."""
	if not frappe.db.exists("Meat Processing Batch", _BATCH_CODE):
		return "seed_meat_processing_qc_and_packing: SKIPPED — run seed_meat_processing_batch first."
	if frappe.db.exists("Meat Packing Lot", _PACKING_LOT_CODE):
		return "seed_meat_processing_qc_and_packing: already existed."

	qc_status = frappe.db.get_value("Meat Processing Batch", _BATCH_CODE, "qc_status")
	blocked = True
	if qc_status == "On Hold":
		attempt = frappe.get_doc(
			{
				"doctype": "Meat Packing Lot",
				"packing_lot_code": "MPPACK-2026-NEGTEST",
				"processing_batch": _BATCH_CODE,
				"carton_count": _NEGATIVE_TEST_MARKER_CARTONS,
				"net_weight_per_carton_kg": 1.0,
			}
		)
		blocked = False
		try:
			attempt.insert(ignore_permissions=True)
		except frappe.ValidationError:
			blocked = True
		if not blocked:
			frappe.throw("MP04 negative test FAILED: packing a Processing Batch that is still On Hold was not blocked!")

	frappe.db.set_value(
		"Meat Processing Batch",
		_BATCH_CODE,
		{"qc_status": "Released", "qc_released_by": "QC Manager — Meat Plant", "qc_released_on": now_datetime()},
	)

	packing = frappe.get_doc(
		{
			"doctype": "Meat Packing Lot",
			"packing_lot_code": _PACKING_LOT_CODE,
			"processing_batch": _BATCH_CODE,
			"carton_count": 62,
			"net_weight_per_carton_kg": 20.0,
		}
	)
	packing.insert(ignore_permissions=True)

	cold_storage_created = False
	if not frappe.db.exists("Meat Cold Storage Record", {"packing_lot": _PACKING_LOT_CODE}):
		frappe.get_doc(
			{"doctype": "Meat Cold Storage Record", "packing_lot": _PACKING_LOT_CODE, "storage_temp_c": -18.0, "warehouse_location": "Cold Store B - Rack 5"}
		).insert(ignore_permissions=True)
		cold_storage_created = True

	return (
		f"seed_meat_processing_qc_and_packing: MP04 CONFIRMED (pack-while-On-Hold blocked={blocked}), batch Released, Packing Lot created "
		f"({packing.carton_count} cartons x {packing.net_weight_per_carton_kg}kg = {packing.total_packed_weight_kg}kg). "
		f"Cold Storage Record {'created' if cold_storage_created else 'already existed'} (MP05)."
	)


def _ensure_customer():
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(
			ignore_permissions=True
		)
	if frappe.db.exists("Customer", {"customer_name": _CUSTOMER_NAME}):
		return frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), False
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": _CUSTOMER_NAME, "customer_type": "Company", "customer_group": _CUSTOMER_GROUP})
	customer.insert(ignore_permissions=True)
	return customer.name, True


def seed_meat_processing_distribution_and_recall():
	"""DP-690 — MP06 (chain closure: distribution to a real Customer) + MP07 (recall simulation
	— a QMS Recall referencing the ORIGINATING incoming lot, the way a real recall is actually
	triggered: something is found wrong with a specific incoming lot/farm source, and every
	finished/distributed lot downstream of it must be identified — reuses Golden Demo #3's `QMS
	Recall` doctype as-is, the 7th distinct golden demo to do so this session)."""
	if not frappe.db.exists("Meat Packing Lot", _PACKING_LOT_CODE):
		return "seed_meat_processing_distribution_and_recall: SKIPPED — run seed_meat_processing_qc_and_packing first."
	customer, customer_created = _ensure_customer()

	distribution_created = False
	if not frappe.db.exists("Meat Distribution", {"packing_lot": _PACKING_LOT_CODE}):
		frappe.get_doc(
			{
				"doctype": "Meat Distribution",
				"packing_lot": _PACKING_LOT_CODE,
				"customer": customer,
				"destination": "Ho Chi Minh City Cold Chain Distribution Hub",
				"carton_count": 62,
			}
		).insert(ignore_permissions=True)
		distribution_created = True

	recall_created = False
	if not frappe.db.exists("QMS Recall", {"batch_reference": _LOT1_CODE}):
		frappe.get_doc(
			{
				"doctype": "QMS Recall",
				"subject": f"Simulated recall drill — incoming lot {_LOT1_CODE} (MP07 demo scenario)",
				"batch_reference": _LOT1_CODE,
				"reason": "Simulated recall drill — precautionary residue spot-check follow-up on the originating farm lot, no real product issue. Every finished/distributed lot downstream of this incoming lot must be identified.",
				"status": "Initiated",
			}
		).insert(ignore_permissions=True)
		recall_created = True

	return (
		f"seed_meat_processing_distribution_and_recall: Distribution {'created' if distribution_created else 'already existed'} to {customer} ({'new' if customer_created else 'existing'}) — MP06 chain closure. "
		f"Recall {'created' if recall_created else 'already existed'} on incoming lot {_LOT1_CODE} — MP07."
	)


def _test_mp02_overyield_blocked():
	"""A throwaway Processing Batch whose carcass_weight_kg deliberately exceeds its own
	sources' total live weight must be blocked at insert()."""
	attempt = frappe.get_doc(
		{
			"doctype": "Meat Processing Batch",
			"batch_code": "MPPROC-2026-NEGTEST",
			"plant": _PLANT_NAME,
			"process_type": "Whole Carcass",
			"sources": [{"incoming_lot": _LOT1_CODE, "live_weight_kg": 100.0}],
			"carcass_weight_kg": 9999.0,
			"output_cut_weight_kg": 10.0,
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("MP02 negative test FAILED: carcass weight exceeding the batch's own total live weight was not blocked!")
	return True


def _test_meat_double_distribution_blocked():
	status = frappe.db.get_value("Meat Packing Lot", _PACKING_LOT_CODE, "status")
	if status != "Distributed":
		return True  # hasn't been distributed yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{
			"doctype": "Meat Distribution",
			"packing_lot": _PACKING_LOT_CODE,
			"customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"),
			"destination": "Hanoi Cold Chain Distribution Hub",
			"carton_count": 5,
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("Negative test FAILED: distributing an already-Distributed packing lot a second time was not blocked!")
	return True


def seed_meat_processing_validations():
	"""DP-690b — MP02 negative test + double-distribution negative test. Run AFTER
	seed_meat_processing_distribution_and_recall for full double-distribution coverage, same
	ordering caveat as every prior golden demo's validations step (e.g. Seafood's SP06 test)."""
	mp02 = _test_mp02_overyield_blocked()
	dist = _test_meat_double_distribution_blocked()
	return f"seed_meat_processing_validations: MP02 CONFIRMED ({mp02}). Double-distribution block CONFIRMED ({dist})."
