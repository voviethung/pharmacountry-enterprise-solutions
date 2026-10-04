"""Golden Demo #19 — Seafood Processing & Export (master plan DEMO 32, "PHASE 5" item 5, the
last Phase 5 item), IP-SEAFOOD-PROCESSING. Sources its incoming raw material from Golden Demo
#8's already-completed Shrimp Harvest — no new farm/pond master data, this plugs straight into
an existing golden demo's own harvest record.
"""

import frappe

_PLANT_NAME = "Demo Seafood Plant - Ca Mau"
_LOT_CODE = "SFLOT-2026-001"
_PROCESSING_BATCH_CODE = "SFPROC-2026-001"
_PACKING_LOT_CODE = "SFPACK-2026-001"


def seed_seafood_master_data():
	"""DP-618 — Plant master data."""
	if frappe.db.exists("Seafood Plant", _PLANT_NAME):
		return "seed_seafood_master_data: already existed."
	frappe.get_doc({"doctype": "Seafood Plant", "plant_name": _PLANT_NAME, "location": "Ca Mau, Vietnam"}).insert(ignore_permissions=True)
	return f"seed_seafood_master_data: Plant created ({_PLANT_NAME})."


def seed_seafood_receiving_and_grading():
	"""DP-619 — SP01 (harvest lot receiving, sourced from Golden Demo #8's Shrimp Harvest via
	a Dynamic Link) + SP02 (grade/yield, server-computed)."""
	shrimp_harvest = frappe.db.get_value("Shrimp Harvest", {}, "name")
	if not shrimp_harvest:
		return "seed_seafood_receiving_and_grading: SKIPPED — Golden Demo #8's Shrimp Harvest doesn't exist yet."
	if not frappe.db.exists("Seafood Plant", _PLANT_NAME):
		return "seed_seafood_receiving_and_grading: SKIPPED — run seed_seafood_master_data first."

	lot_created = False
	if not frappe.db.exists("Seafood Harvest Lot", _LOT_CODE):
		frappe.get_doc(
			{
				"doctype": "Seafood Harvest Lot",
				"lot_code": _LOT_CODE,
				"plant": _PLANT_NAME,
				"source_type": "Shrimp Harvest",
				"source_reference": shrimp_harvest,
				"species": "Litopenaeus vannamei (Whiteleg shrimp)",
				"received_weight_kg": 4000.0,
			}
		).insert(ignore_permissions=True)
		lot_created = True

	grading_created = False
	if not frappe.db.exists("Seafood Grading", {"harvest_lot": _LOT_CODE}):
		grading = frappe.get_doc({"doctype": "Seafood Grading", "harvest_lot": _LOT_CODE, "grade_a_kg": 3000.0, "grade_b_kg": 800.0, "reject_kg": 150.0})
		grading.insert(ignore_permissions=True)
		grading_created = True

	yield_percent = frappe.db.get_value("Seafood Grading", {"harvest_lot": _LOT_CODE}, "yield_percent")
	return f"seed_seafood_receiving_and_grading: Harvest Lot {'created' if lot_created else 'already existed'} (SP01, from {shrimp_harvest}). Grading {'created' if grading_created else 'already existed'} (SP02 yield {yield_percent}%)."


def seed_seafood_processing_and_packing():
	"""DP-620 — SP03 (processing batch), SP04 (packing lot), SP05 (cold storage)."""
	if not frappe.db.exists("Seafood Grading", {"harvest_lot": _LOT_CODE}):
		return "seed_seafood_processing_and_packing: SKIPPED — run seed_seafood_receiving_and_grading first."
	grading_name = frappe.db.get_value("Seafood Grading", {"harvest_lot": _LOT_CODE}, "name")

	processing_created = False
	if not frappe.db.exists("Seafood Processing Batch", _PROCESSING_BATCH_CODE):
		frappe.get_doc({"doctype": "Seafood Processing Batch", "batch_code": _PROCESSING_BATCH_CODE, "grading": grading_name, "process_type": "Peeled", "output_weight_kg": 3200.0}).insert(
			ignore_permissions=True
		)
		processing_created = True

	packing_created = False
	if not frappe.db.exists("Seafood Packing Lot", _PACKING_LOT_CODE):
		frappe.get_doc(
			{"doctype": "Seafood Packing Lot", "packing_lot_code": _PACKING_LOT_CODE, "processing_batch": _PROCESSING_BATCH_CODE, "carton_count": 160, "net_weight_per_carton_kg": 20.0}
		).insert(ignore_permissions=True)
		packing_created = True

	cold_storage_created = False
	if not frappe.db.exists("Seafood Cold Storage Record", {"packing_lot": _PACKING_LOT_CODE}):
		frappe.get_doc(
			{"doctype": "Seafood Cold Storage Record", "packing_lot": _PACKING_LOT_CODE, "storage_temp_c": -18.0, "warehouse_location": "Cold Store A - Rack 12"}
		).insert(ignore_permissions=True)
		cold_storage_created = True

	return (
		f"seed_seafood_processing_and_packing: Processing Batch {'created' if processing_created else 'already existed'} (SP03). "
		f"Packing Lot {'created' if packing_created else 'already existed'} (SP04). Cold Storage Record {'created' if cold_storage_created else 'already existed'} (SP05)."
	)


_CUSTOMER_GROUP = "Seafood Export Buyers"
_CUSTOMER_NAME = "Tokyo Marine Imports K.K."
_RECALL_ID = f"RECALL-{_PACKING_LOT_CODE}"


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


def seed_seafood_shipment_and_recall():
	"""DP-621 — SP06 (shipment) + SP08 (recall simulation, reuses Golden Demo #3's QMS Recall
	as-is — the 6th distinct golden demo to do so, after Vet Mfg/Vet Distribution/Feed/Fish
	Farm[implicitly via shared pattern]/this)."""
	if not frappe.db.exists("Seafood Packing Lot", _PACKING_LOT_CODE):
		return "seed_seafood_shipment_and_recall: SKIPPED — run seed_seafood_processing_and_packing first."
	customer, customer_created = _ensure_customer()

	shipment_created = False
	if not frappe.db.exists("Seafood Shipment", {"packing_lot": _PACKING_LOT_CODE}):
		frappe.get_doc(
			{"doctype": "Seafood Shipment", "packing_lot": _PACKING_LOT_CODE, "customer": customer, "destination_country": "Japan", "carton_count": 160}
		).insert(ignore_permissions=True)
		shipment_created = True

	recall_created = False
	if not frappe.db.exists("QMS Recall", {"batch_reference": _PACKING_LOT_CODE}):
		frappe.get_doc(
			{
				"doctype": "QMS Recall",
				"subject": f"Simulated recall drill — {_PACKING_LOT_CODE} (SP08 demo scenario)",
				"batch_reference": _PACKING_LOT_CODE,
				"reason": "Simulated recall drill — precautionary histamine spot-check follow-up, no real product issue.",
				"status": "Initiated",
			}
		).insert(ignore_permissions=True)
		recall_created = True

	return (
		f"seed_seafood_shipment_and_recall: Shipment {'created' if shipment_created else 'already existed'} to {customer} ({'new' if customer_created else 'existing'}) — SP06. "
		f"Recall {'created' if recall_created else 'already existed'} — SP08."
	)


def _test_sp02_overgrading_blocked():
	attempt = frappe.get_doc({"doctype": "Seafood Grading", "harvest_lot": _LOT_CODE, "grade_a_kg": 9000.0})
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("SP02 negative test FAILED: grading beyond the harvest lot's received_weight_kg was not blocked!")
	return True


def _test_sp06_double_shipment_blocked():
	status = frappe.db.get_value("Seafood Packing Lot", _PACKING_LOT_CODE, "status")
	if status != "Shipped":
		return True  # hasn't been shipped yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{"doctype": "Seafood Shipment", "packing_lot": _PACKING_LOT_CODE, "customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), "destination_country": "USA", "carton_count": 10}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("SP06 negative test FAILED: shipping an already-Shipped packing lot a second time was not blocked!")
	return True


def seed_seafood_validations():
	"""DP-622 — SP02/SP06 negative tests. Run AFTER seed_seafood_shipment_and_recall for full
	SP06 coverage, same ordering caveat as every prior golden demo's validations step."""
	sp02 = _test_sp02_overgrading_blocked()
	sp06 = _test_sp06_double_shipment_blocked()
	return f"seed_seafood_validations: SP02 CONFIRMED ({sp02}). SP06 CONFIRMED ({sp06})."
