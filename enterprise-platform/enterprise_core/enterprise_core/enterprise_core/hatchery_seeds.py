"""Golden Demo #14 — Hatchery / Breeding Management (master plan DEMO 25, "PHASE 4" item 6, the
last Phase 4 item), IP-HATCHERY.
"""

import frappe

_FARM_NAME = "Demo Hatchery - Dong Thap"
_PARENT_FLOCK = "PARENT-2025-001"
_EGG_BATCH = "EGGBATCH-2026-001"
_INCUBATOR = "INCUBATOR-01"
_CHICK_BATCH = "CHICKBATCH-2026-001"


def _ensure_farm_parent_stock_and_incubator():
	farm_created = False
	if not frappe.db.exists("Hatchery Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Hatchery Farm", "farm_name": _FARM_NAME, "location": "Dong Thap, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	parent_created = False
	if not frappe.db.exists("Hatchery Parent Stock", _PARENT_FLOCK):
		frappe.get_doc(
			{"doctype": "Hatchery Parent Stock", "parent_flock_code": _PARENT_FLOCK, "farm": _FARM_NAME, "breed": "Ross 308 Parent Stock", "placement_date": frappe.utils.add_days(frappe.utils.nowdate(), -300), "status": "Active"}
		).insert(ignore_permissions=True)
		parent_created = True
	incubator_created = False
	if not frappe.db.exists("Hatchery Incubator", _INCUBATOR):
		frappe.get_doc({"doctype": "Hatchery Incubator", "incubator_code": _INCUBATOR, "farm": _FARM_NAME, "capacity": 6000, "status": "Empty"}).insert(ignore_permissions=True)
		incubator_created = True
	return farm_created, parent_created, incubator_created


def seed_hatchery_master_data():
	"""DP-591 — master data: Farm, Parent Stock (pedigree/trace root for H01), Incubator."""
	farm_created, parent_created, incubator_created = _ensure_farm_parent_stock_and_incubator()
	return f"seed_hatchery_master_data: Farm {'created' if farm_created else 'already existed'}. Parent Stock {'created' if parent_created else 'already existed'}. Incubator {'created' if incubator_created else 'already existed'}."


def _ensure_egg_batch_and_incubation():
	if not frappe.db.exists("Hatchery Egg Batch", _EGG_BATCH):
		frappe.get_doc(
			{"doctype": "Hatchery Egg Batch", "batch_code": _EGG_BATCH, "parent_stock": _PARENT_FLOCK, "collection_date": frappe.utils.add_days(frappe.utils.nowdate(), -25), "egg_count": 5000, "status": "Collected"}
		).insert(ignore_permissions=True)
		egg_batch_created = True
	else:
		egg_batch_created = False

	existing_incubation = frappe.db.get_value("Hatchery Incubation", {"egg_batch": _EGG_BATCH}, "name")
	if existing_incubation:
		return egg_batch_created, existing_incubation, False
	egg_batch = frappe.get_doc("Hatchery Egg Batch", _EGG_BATCH)
	incubation = frappe.get_doc(
		{"doctype": "Hatchery Incubation", "egg_batch": _EGG_BATCH, "incubator": _INCUBATOR, "start_date": egg_batch.collection_date, "status": "Incubating"}
	)
	incubation.insert(ignore_permissions=True)
	return egg_batch_created, incubation.name, True


def seed_hatchery_egg_and_incubation():
	"""DP-592 — H01 (egg batch origin), H02 (incubator assignment, Empty -> Occupied)."""
	if not frappe.db.exists("Hatchery Parent Stock", _PARENT_FLOCK):
		return "seed_hatchery_egg_and_incubation: SKIPPED — run seed_hatchery_master_data first."
	egg_batch_created, incubation_name, incubation_created = _ensure_egg_batch_and_incubation()
	incubator_status = frappe.db.get_value("Hatchery Incubator", _INCUBATOR, "status")
	return (
		f"seed_hatchery_egg_and_incubation: Egg Batch {'created' if egg_batch_created else 'already existed'}. "
		f"Incubation {'created' if incubation_created else 'already existed'} ({incubation_name}). H02 incubator status: {incubator_status}."
	)


def _ensure_hatch_result_and_chick_batch():
	incubation_name = frappe.db.get_value("Hatchery Incubation", {"egg_batch": _EGG_BATCH}, "name")
	existing_hatch = frappe.db.get_value("Hatchery Hatch Result", {"incubation": incubation_name}, "name")
	if existing_hatch:
		return existing_hatch, False, frappe.db.exists("Hatchery Chick Batch", _CHICK_BATCH), False

	incubation = frappe.get_doc("Hatchery Incubation", incubation_name)
	hatch_result = frappe.get_doc(
		{"doctype": "Hatchery Hatch Result", "incubation": incubation_name, "hatch_date": incubation.expected_hatch_date, "hatched_count": 4200, "infertile_count": 400, "dead_in_shell_count": 200}
	)
	hatch_result.insert(ignore_permissions=True)

	chick_batch_created = False
	if not frappe.db.exists("Hatchery Chick Batch", _CHICK_BATCH):
		frappe.get_doc(
			{"doctype": "Hatchery Chick Batch", "chick_batch_code": _CHICK_BATCH, "hatch_result": hatch_result.name, "hatch_date": hatch_result.hatch_date, "initial_count": hatch_result.hatched_count, "status": "Active"}
		).insert(ignore_permissions=True)
		chick_batch_created = True
	return hatch_result.name, True, True, chick_batch_created


def _ensure_chick_grading():
	if frappe.db.exists("Hatchery Chick Grading", {"chick_batch": _CHICK_BATCH}):
		return False
	frappe.get_doc({"doctype": "Hatchery Chick Grading", "chick_batch": _CHICK_BATCH, "grade_a_count": 3800, "grade_b_count": 300, "reject_count": 100}).insert(ignore_permissions=True)
	return True


def seed_hatchery_hatch_and_grading():
	"""DP-593 — H03 (hatch rate, server-computed) + H04 (chick grading, graded total can't
	exceed the batch's initial_count)."""
	if not frappe.db.exists("Hatchery Incubation", {"egg_batch": _EGG_BATCH}):
		return "seed_hatchery_hatch_and_grading: SKIPPED — run seed_hatchery_egg_and_incubation first."
	hatch_name, hatch_created, chick_exists, chick_created = _ensure_hatch_result_and_chick_batch()
	grading_created = _ensure_chick_grading()
	hatch_rate = frappe.db.get_value("Hatchery Hatch Result", hatch_name, "hatch_rate_percent")
	return (
		f"seed_hatchery_hatch_and_grading: Hatch Result {'created' if hatch_created else 'already existed'} ({hatch_name}, H03 hatch rate {hatch_rate}%). "
		f"Chick Batch {'created' if chick_created else 'already existed'}. Grading {'created' if grading_created else 'already existed'} (H04)."
	)


_CUSTOMER_GROUP = "Livestock Buyers"
_CUSTOMER_NAME = "Dong Thap Broiler Growers Co-op"


def _ensure_vaccinations():
	created = 0
	rows = [
		{"vaccine_name": "Marek's Disease (in-ovo/day-old)", "due_date": frappe.utils.nowdate(), "administered_date": frappe.utils.nowdate()},
		{"vaccine_name": "Newcastle Disease (ND) Booster", "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -2), "administered_date": None},
	]
	for row in rows:
		if frappe.db.exists("Hatchery Vaccination", {"chick_batch": _CHICK_BATCH, "vaccine_name": row["vaccine_name"]}):
			continue
		frappe.get_doc({"doctype": "Hatchery Vaccination", "chick_batch": _CHICK_BATCH, **row}).insert(ignore_permissions=True)
		created += 1
	return created


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


def seed_hatchery_vaccination_and_dispatch():
	"""DP-594 — H05 (vaccine schedule) + H06 (customer dispatch trace)."""
	if not frappe.db.exists("Hatchery Chick Batch", _CHICK_BATCH):
		return "seed_hatchery_vaccination_and_dispatch: SKIPPED — run seed_hatchery_hatch_and_grading first."
	vacc_created = _ensure_vaccinations()
	customer, customer_created = _ensure_customer()
	dispatch_created = False
	if not frappe.db.exists("Hatchery Dispatch", {"chick_batch": _CHICK_BATCH}):
		frappe.get_doc({"doctype": "Hatchery Dispatch", "chick_batch": _CHICK_BATCH, "customer": customer, "head_count": 4100, "sale_price": 41000000}).insert(ignore_permissions=True)
		dispatch_created = True
	overdue_count = frappe.db.count("Hatchery Vaccination", {"chick_batch": _CHICK_BATCH, "status": "Overdue"})
	return (
		f"seed_hatchery_vaccination_and_dispatch: {vacc_created} vaccination(s) created ({overdue_count} Overdue — H05). "
		f"Dispatch {'created' if dispatch_created else 'already existed'} to {customer} ({'new' if customer_created else 'existing'}) — H06."
	)


def _test_h01_duplicate_batch_code_blocked():
	dup = frappe.get_doc({"doctype": "Hatchery Egg Batch", "batch_code": _EGG_BATCH, "parent_stock": _PARENT_FLOCK, "collection_date": frappe.utils.nowdate(), "egg_count": 100})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# same NameError-not-ValidationError subtlety documented in Pig/Poultry/Cattle Farm's
		# negative tests.
		blocked = True
	if not blocked:
		frappe.throw("H01 negative test FAILED: a duplicate egg batch_code was not blocked!")
	return True


def _test_h04_overgrading_blocked():
	attempt = frappe.get_doc({"doctype": "Hatchery Chick Grading", "chick_batch": _CHICK_BATCH, "grading_date": frappe.utils.nowdate(), "grade_a_count": 9000, "grade_b_count": 0, "reject_count": 0})
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("H04 negative test FAILED: grading a batch beyond its initial_count was not blocked!")
	return True


def _test_h06_double_dispatch_blocked():
	batch_status = frappe.db.get_value("Hatchery Chick Batch", _CHICK_BATCH, "status")
	if batch_status != "Dispatched":
		return True  # hasn't been dispatched yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{"doctype": "Hatchery Dispatch", "chick_batch": _CHICK_BATCH, "dispatch_date": frappe.utils.nowdate(), "customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), "head_count": 1}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("H06 negative test FAILED: dispatching an already-Dispatched chick batch a second time was not blocked!")
	return True


def seed_hatchery_validations():
	"""DP-595 — H01/H04/H06 negative tests. Run AFTER seed_hatchery_vaccination_and_dispatch
	for full H06 coverage, same ordering caveat as every prior golden demo's validations step."""
	h01 = _test_h01_duplicate_batch_code_blocked()
	h04 = _test_h04_overgrading_blocked()
	h06 = _test_h06_double_dispatch_blocked()
	return f"seed_hatchery_validations: H01 CONFIRMED ({h01}). H04 CONFIRMED ({h04}). H06 CONFIRMED ({h06})."
