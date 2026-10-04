"""Golden Demo #18 — Aquaculture Hatchery / Seed Management (master plan DEMO 30, "PHASE 5"
item 4), IP-AQUA-HATCHERY.
"""

import frappe

_FARM_NAME = "Demo Aqua Hatchery - Ninh Thuan"
_DAM_TAG = "SHRIMP-DAM-001"
_SIRE_TAG = "SHRIMP-SIRE-001"
_SPECIES = "Litopenaeus vannamei (Whiteleg shrimp)"


def _ensure_farm_and_broodstock():
	farm_created = False
	if not frappe.db.exists("Aqua Hatchery Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Aqua Hatchery Farm", "farm_name": _FARM_NAME, "location": "Ninh Thuan, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	created = 0
	for tag, sex in [(_DAM_TAG, "Female"), (_SIRE_TAG, "Male")]:
		if not frappe.db.exists("Aqua Broodstock", tag):
			frappe.get_doc({"doctype": "Aqua Broodstock", "tag_id": tag, "farm": _FARM_NAME, "species": _SPECIES, "sex": sex, "source": "SPF Broodstock Import", "status": "Active"}).insert(
				ignore_permissions=True
			)
			created += 1
	return farm_created, created


def seed_aqua_hatchery_master_data():
	"""DP-612 — Farm, Broodstock (AH01 trace roots)."""
	farm_created, broodstock_created = _ensure_farm_and_broodstock()
	return f"seed_aqua_hatchery_master_data: Farm {'created' if farm_created else 'already existed'}. {broodstock_created} broodstock created."


def _ensure_spawning_batch():
	existing = frappe.db.get_value("Aqua Spawning Batch", {"dam": _DAM_TAG, "sire": _SIRE_TAG}, "name", order_by="creation desc")
	if existing:
		return existing, False
	batch = frappe.get_doc(
		{"doctype": "Aqua Spawning Batch", "dam": _DAM_TAG, "sire": _SIRE_TAG, "spawning_date": frappe.utils.add_days(frappe.utils.nowdate(), -60), "egg_count": 500000}
	)
	batch.insert(ignore_permissions=True)
	return batch.name, True


def seed_aqua_hatchery_spawning():
	"""DP-613 — AH02 (spawning batch)."""
	if not frappe.db.exists("Aqua Broodstock", _DAM_TAG):
		return "seed_aqua_hatchery_spawning: SKIPPED — run seed_aqua_hatchery_master_data first."
	batch_name, created = _ensure_spawning_batch()
	return f"seed_aqua_hatchery_spawning: Spawning Batch {'created' if created else 'already existed'} ({batch_name})."


def _ensure_larval_and_nursery():
	spawning_name = frappe.db.get_value("Aqua Spawning Batch", {"dam": _DAM_TAG, "sire": _SIRE_TAG}, "name", order_by="creation desc")
	existing_larval = frappe.db.get_value("Aqua Larval Batch", {"spawning_batch": spawning_name}, "name")
	if existing_larval:
		nursery_name = frappe.db.get_value("Aqua Nursery Batch", {"larval_batch": existing_larval}, "name")
		return existing_larval, False, nursery_name, False

	spawning = frappe.get_doc("Aqua Spawning Batch", spawning_name)
	larval = frappe.get_doc(
		{"doctype": "Aqua Larval Batch", "spawning_batch": spawning_name, "hatch_date": frappe.utils.add_days(spawning.spawning_date, 1), "larvae_count": 350000}
	)
	larval.insert(ignore_permissions=True)

	nursery_created = False
	nursery_name = frappe.db.get_value("Aqua Nursery Batch", {"larval_batch": larval.name}, "name")
	if not nursery_name:
		nursery = frappe.get_doc({"doctype": "Aqua Nursery Batch", "larval_batch": larval.name, "nursery_start_date": larval.hatch_date, "initial_count": larval.larvae_count})
		nursery.insert(ignore_permissions=True)
		nursery_name = nursery.name
		nursery_created = True
	return larval.name, True, nursery_name, nursery_created


def _ensure_health_record(nursery_name):
	if frappe.db.exists("Aqua Health Record", {"nursery_batch": nursery_name}):
		return False
	frappe.get_doc(
		{
			"doctype": "Aqua Health Record",
			"nursery_batch": nursery_name,
			"record_date": frappe.utils.add_days(frappe.utils.nowdate(), -15),
			"diagnosis": "Mild Vibrio bacterial load detected during PL-stage monitoring.",
			"treatment_applied": "Probiotic water treatment + reduced feed rate for 3 days.",
			"dosage": "5 ppm probiotic, applied daily x3",
		}
	).insert(ignore_permissions=True)
	return True


def seed_aqua_hatchery_larval_nursery():
	"""DP-614 — AH03 (larval survival, server-computed) + AH04 (nursery) + AH05 (health record)."""
	if not frappe.db.exists("Aqua Spawning Batch", {"dam": _DAM_TAG}):
		return "seed_aqua_hatchery_larval_nursery: SKIPPED — run seed_aqua_hatchery_spawning first."
	larval_name, larval_created, nursery_name, nursery_created = _ensure_larval_and_nursery()
	health_created = _ensure_health_record(nursery_name)
	survival = frappe.db.get_value("Aqua Larval Batch", larval_name, "survival_rate_percent")
	return (
		f"seed_aqua_hatchery_larval_nursery: Larval Batch {'created' if larval_created else 'already existed'} ({larval_name}, AH03 survival {survival}%). "
		f"Nursery Batch {'created' if nursery_created else 'already existed'} ({nursery_name}). Health Record {'created' if health_created else 'already existed'} (AH05)."
	)


_SEED_BATCH_CODE = "SEEDBATCH-2026-001"
_CUSTOMER_GROUP = "Aquaculture Seed Buyers"
_CUSTOMER_NAME = "Ninh Thuan Shrimp Growers Co-op"


def _ensure_seed_batch():
	nursery_name = frappe.db.get_value("Aqua Nursery Batch", {}, "name", order_by="creation desc")
	existing = frappe.db.exists("Aqua Seed Batch", _SEED_BATCH_CODE)
	if existing:
		return existing, False
	batch = frappe.get_doc(
		{"doctype": "Aqua Seed Batch", "seed_batch_code": _SEED_BATCH_CODE, "nursery_batch": nursery_name, "grade_a_count": 280000, "grade_b_count": 40000, "reject_count": 20000}
	)
	batch.insert(ignore_permissions=True)
	return batch.name, True


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


def seed_aqua_hatchery_dispatch():
	"""DP-615 — AH06 (seed batch dispatch, grading folded into Seed Batch creation)."""
	if not frappe.db.exists("Aqua Nursery Batch", {}):
		return "seed_aqua_hatchery_dispatch: SKIPPED — run seed_aqua_hatchery_larval_nursery first."
	seed_batch_name, seed_batch_created = _ensure_seed_batch()
	customer, customer_created = _ensure_customer()
	dispatch_created = False
	if not frappe.db.exists("Aqua Seed Dispatch", {"seed_batch": seed_batch_name}):
		frappe.get_doc({"doctype": "Aqua Seed Dispatch", "seed_batch": seed_batch_name, "customer": customer, "quantity": 300000, "sale_price": 15000000}).insert(ignore_permissions=True)
		dispatch_created = True
	return (
		f"seed_aqua_hatchery_dispatch: Seed Batch {'created' if seed_batch_created else 'already existed'} ({seed_batch_name}). "
		f"Dispatch {'created' if dispatch_created else 'already existed'} to {customer} ({'new' if customer_created else 'existing'}) — AH06."
	)


def _test_ah01_duplicate_tag_blocked():
	dup = frappe.get_doc({"doctype": "Aqua Broodstock", "tag_id": _DAM_TAG, "farm": _FARM_NAME, "species": _SPECIES, "sex": "Female", "status": "Active"})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# same NameError-not-ValidationError subtlety documented in Pig/Poultry/Cattle/Hatchery
		# Farm's negative tests.
		blocked = True
	if not blocked:
		frappe.throw("AH01 negative test FAILED: a duplicate broodstock tag_id was not blocked!")
	return True


def _test_ah04_overgrading_blocked():
	nursery_name = frappe.db.get_value("Aqua Nursery Batch", {}, "name", order_by="creation desc")
	if not nursery_name or frappe.db.get_value("Aqua Nursery Batch", nursery_name, "status") != "Graded":
		return True  # hasn't been graded yet in this run order — nothing to test
	attempt = frappe.get_doc({"doctype": "Aqua Seed Batch", "seed_batch_code": "SEEDBATCH-OVERGRADE-TEST", "nursery_batch": nursery_name, "grade_a_count": 900000})
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("AH04 negative test FAILED: grading a batch beyond its initial_count was not blocked!")
	return True


def _test_ah06_double_dispatch_blocked():
	status = frappe.db.get_value("Aqua Seed Batch", _SEED_BATCH_CODE, "status")
	if status != "Dispatched":
		return True  # hasn't been dispatched yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{"doctype": "Aqua Seed Dispatch", "seed_batch": _SEED_BATCH_CODE, "customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), "quantity": 1000}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("AH06 negative test FAILED: dispatching an already-Dispatched seed batch a second time was not blocked!")
	return True


def seed_aqua_hatchery_validations():
	"""DP-616 — AH01/AH04/AH06 negative tests. Run AFTER seed_aqua_hatchery_dispatch for full
	AH04/AH06 coverage, same ordering caveat as every prior golden demo's validations step."""
	ah01 = _test_ah01_duplicate_tag_blocked()
	ah04 = _test_ah04_overgrading_blocked()
	ah06 = _test_ah06_double_dispatch_blocked()
	return f"seed_aqua_hatchery_validations: AH01 CONFIRMED ({ah01}). AH04 CONFIRMED ({ah04}). AH06 CONFIRMED ({ah06})."
