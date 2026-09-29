"""Golden Demo #11 — Pig Farm Management (master plan DEMO 22, "PHASE 4" item 3), IP-LIVESTOCK-PIG.
"""

import frappe

_FARM_NAME = "Demo Pig Farm - Dong Nai"
_BREEDING_PEN = "PEN-B1"
_GROWER_PEN = "PEN-G1"
_SOW_TAG = "SOW-001"
_BOAR_TAG = "BOAR-001"


def _ensure_farm_pens_and_breeding_stock():
	farm_created = False
	if not frappe.db.exists("Pig Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Pig Farm", "farm_name": _FARM_NAME, "location": "Dong Nai, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True

	pens_created = 0
	for pen_code, pen_type, capacity in [(_BREEDING_PEN, "Breeding", 10), (_GROWER_PEN, "Nursery", 50)]:
		if not frappe.db.exists("Pig Pen", pen_code):
			frappe.get_doc({"doctype": "Pig Pen", "pen_code": pen_code, "farm": _FARM_NAME, "pen_type": pen_type, "capacity": capacity, "status": "Empty"}).insert(
				ignore_permissions=True
			)
			pens_created += 1

	animals_created = 0
	for tag, sex, breed in [(_SOW_TAG, "Sow", "Yorkshire"), (_BOAR_TAG, "Boar", "Duroc")]:
		if not frappe.db.exists("Pig Breeding Animal", tag):
			frappe.get_doc(
				{
					"doctype": "Pig Breeding Animal",
					"tag_id": tag,
					"sex": sex,
					"breed": breed,
					"birth_date": frappe.utils.add_days(frappe.utils.nowdate(), -400),
					"pen": _BREEDING_PEN,
					"status": "Active",
				}
			).insert(ignore_permissions=True)
			animals_created += 1

	return farm_created, pens_created, animals_created


def seed_pig_farm_master_data():
	"""DP-573 — master data: Farm, Pens, Sow/Boar (merged Pig Breeding Animal, PF01 uniqueness
	via each doctype's own unique autoname field)."""
	farm_created, pens_created, animals_created = _ensure_farm_pens_and_breeding_stock()
	return f"seed_pig_farm_master_data: Farm {'created' if farm_created else 'already existed'}. {pens_created} pen(s) created. {animals_created} breeding animal(s) created."


def _ensure_breeding_service():
	existing = frappe.db.get_value("Pig Breeding Service", {"sow": _SOW_TAG, "boar": _BOAR_TAG}, "name", order_by="creation desc")
	if existing:
		return existing, False
	service = frappe.get_doc(
		{
			"doctype": "Pig Breeding Service",
			"sow": _SOW_TAG,
			"boar": _BOAR_TAG,
			"service_date": frappe.utils.add_days(frappe.utils.nowdate(), -140),
		}
	)
	service.insert(ignore_permissions=True)
	return service.name, True


def _ensure_confirmed_pregnant(service_name):
	service = frappe.get_doc("Pig Breeding Service", service_name)
	if service.status == "Served":
		service.status = "Confirmed Pregnant"
		service.save(ignore_permissions=True)
		return True
	return False


def _ensure_farrowing(service_name):
	existing = frappe.db.get_value("Pig Farrowing", {"breeding_service": service_name}, "name")
	if existing:
		return existing, False
	service = frappe.get_doc("Pig Breeding Service", service_name)
	farrowing = frappe.get_doc(
		{
			"doctype": "Pig Farrowing",
			"breeding_service": service_name,
			"farrowing_date": service.expected_farrow_date,
			"born_alive": 12,
			"born_dead": 1,
		}
	)
	farrowing.insert(ignore_permissions=True)
	return farrowing.name, True


def _ensure_grower_batch(farrowing_name):
	existing = frappe.db.get_value("Pig Grower Batch", {"farrowing": farrowing_name}, "name")
	if existing:
		return existing, False
	farrowing = frappe.get_doc("Pig Farrowing", farrowing_name)
	batch = frappe.get_doc(
		{
			"doctype": "Pig Grower Batch",
			"batch_code": "BATCH-2026-001",
			"farrowing": farrowing_name,
			"pen": _GROWER_PEN,
			"stage": "Nursery",
			"weaning_date": frappe.utils.add_days(farrowing.farrowing_date, 21),
			"initial_count": farrowing.born_alive - 1,  # one pre-weaning loss, tracked separately by a Mortality Record
			"status": "Active",
		}
	)
	batch.insert(ignore_permissions=True)
	return batch.name, True


def seed_pig_breeding_flow():
	"""DP-574 — PF02 (breeding lifecycle: Served -> Confirmed Pregnant -> Farrowed) end to end,
	producing the Grower Batch that PF03/04/05/06/07/08 all operate on."""
	if not frappe.db.exists("Pig Breeding Animal", _SOW_TAG):
		return "seed_pig_breeding_flow: SKIPPED — run seed_pig_farm_master_data first."
	service_name, service_created = _ensure_breeding_service()
	confirmed = _ensure_confirmed_pregnant(service_name)
	farrowing_name, farrowing_created = _ensure_farrowing(service_name)
	batch_name, batch_created = _ensure_grower_batch(farrowing_name)
	service_status = frappe.db.get_value("Pig Breeding Service", service_name, "status")
	return (
		f"seed_pig_breeding_flow: Service {'created' if service_created else 'already existed'} ({service_name}, status={service_status}). "
		f"Confirmed-pregnant transition {'applied' if confirmed else 'already done'}. "
		f"Farrowing {'created' if farrowing_created else 'already existed'} ({farrowing_name}). "
		f"Grower Batch {'created' if batch_created else 'already existed'} ({batch_name})."
	)


def _batch_name():
	return frappe.db.get_value("Pig Grower Batch", {"pen": _GROWER_PEN, "status": "Active"}, "name")


def _ensure_feed_logs(batch_name):
	created = 0
	for days_ago, qty in [(35, 40.0), (20, 90.0), (7, 130.0)]:
		feed_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Pig Feed Log", {"batch": batch_name, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{
				"doctype": "Pig Feed Log",
				"batch": batch_name,
				"feed_date": feed_date,
				"feed_product": "Pig Grower Pellet",
				"qty_kg": qty,
				"cost": qty * 15000,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_vaccinations(batch_name):
	created = 0
	# One administered on schedule, one deliberately overdue (due in the past, never
	# administered) — proves PF04 fires on real data, not just a synthetic negative test, same
	# approach as Shrimp Farm's SF10 deliberately-out-of-range water reading.
	rows = [
		{"vaccine_name": "Classical Swine Fever", "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -25), "administered_date": frappe.utils.add_days(frappe.utils.nowdate(), -25)},
		{"vaccine_name": "Foot-and-Mouth Disease", "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -3), "administered_date": None},
	]
	for row in rows:
		if frappe.db.exists("Pig Vaccination", {"batch": batch_name, "vaccine_name": row["vaccine_name"]}):
			continue
		frappe.get_doc({"doctype": "Pig Vaccination", "batch": batch_name, **row}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_medicine_treatment(batch_name):
	if frappe.db.exists("Pig Medicine Treatment", {"batch": batch_name}):
		return False
	frappe.get_doc(
		{
			"doctype": "Pig Medicine Treatment",
			"batch": batch_name,
			"treatment_date": frappe.utils.add_days(frappe.utils.nowdate(), -15),
			"medicine_name": "Amoxicillin 15% LA",
			"diagnosis": "Mild respiratory infection observed in a subset of the batch.",
			"withdrawal_days": 10,
			"cost": 850000,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_weight_records(batch_name):
	created = 0
	for days_ago, weight in [(30, 7.5), (10, 22.0)]:
		record_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Pig Weight Record", {"batch": batch_name, "record_date": record_date}):
			continue
		frappe.get_doc({"doctype": "Pig Weight Record", "batch": batch_name, "record_date": record_date, "average_weight_kg": weight, "sample_count": 11}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def _ensure_mortality(batch_name):
	if frappe.db.exists("Pig Mortality Record", {"batch": batch_name}):
		return False
	frappe.get_doc(
		{
			"doctype": "Pig Mortality Record",
			"batch": batch_name,
			"record_date": frappe.utils.add_days(frappe.utils.nowdate(), -18),
			"mortality_count": 1,
			"cause": "Scours (diarrhea) shortly after weaning — resolved after treatment.",
		}
	).insert(ignore_permissions=True)
	return True


def seed_pig_operations():
	"""DP-575 — PF03 (feed), PF04 (vaccination due/overdue), PF05 (medicine + withdrawal),
	PF06 (mortality)."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_pig_operations: SKIPPED — run seed_pig_breeding_flow first."
	feed_created = _ensure_feed_logs(batch_name)
	vacc_created = _ensure_vaccinations(batch_name)
	treatment_created = _ensure_medicine_treatment(batch_name)
	weight_created = _ensure_weight_records(batch_name)
	mortality_created = _ensure_mortality(batch_name)
	overdue_count = frappe.db.count("Pig Vaccination", {"batch": batch_name, "status": "Overdue"})
	return (
		f"seed_pig_operations: {feed_created} feed log(s), {vacc_created} vaccination(s) ({overdue_count} Overdue — PF04), "
		f"weight record(s): {weight_created}. Medicine treatment {'created' if treatment_created else 'already existed'} (PF05). "
		f"Mortality {'created' if mortality_created else 'already existed'} (PF06)."
	)


_CUSTOMER_GROUP = "Livestock Buyers"
_CUSTOMER_NAME = "Dong Nai Meat Processing Co."


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


def seed_pig_sale():
	"""DP-576 — PF07 (cost allocation) + PF08 (trace to sale lot). Sale date is deliberately
	placed AFTER the medicine's withdrawal_end_date (treatment -15d + 10d withdrawal = -5d, sale
	at today) so the PF05 block is provably satisfied, not just provably enforceable."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_pig_sale: SKIPPED — run seed_pig_operations first."
	customer, customer_created = _ensure_customer()
	existing = frappe.db.get_value("Pig Sale Lot", {"batch": batch_name}, "name")
	if existing:
		lot = frappe.get_doc("Pig Sale Lot", existing)
		return f"seed_pig_sale: already existed ({existing}). Cost/kg {lot.cost_per_kg}, profit {lot.profit}."
	lot = frappe.get_doc(
		{
			"doctype": "Pig Sale Lot",
			"batch": batch_name,
			"sale_date": frappe.utils.nowdate(),
			"customer": customer,
			"head_count": 10,
			"total_weight_kg": 950.0,
			"sale_price": 66500000,
			"other_cost": 2000000,
		}
	)
	lot.insert(ignore_permissions=True)
	return (
		f"seed_pig_sale: created ({lot.name}) to {customer} ({'new' if customer_created else 'existing'}). "
		f"PF07 — total cost {lot.total_cost}, cost/kg {lot.cost_per_kg}, profit {lot.profit}."
	)


def _test_pf01_duplicate_tag_blocked():
	dup = frappe.get_doc({"doctype": "Pig Breeding Animal", "tag_id": _SOW_TAG, "sex": "Sow", "status": "Active"})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# DuplicateEntryError is a frappe.exceptions.NameError, NOT a ValidationError — unlike
		# every other negative test in this platform (which blocks via a `validate` hook
		# throwing ValidationError), this one is a raw name-collision on the autoname'd `name`
		# field itself, caught by Frappe's own insert() before validate ever runs.
		blocked = True
	if not blocked:
		frappe.throw("PF01 negative test FAILED: a duplicate animal tag_id was not blocked!")
	return True


def _test_pf02_invalid_transition_blocked():
	service_name = frappe.db.get_value("Pig Breeding Service", {"sow": _SOW_TAG, "boar": _BOAR_TAG}, "name", order_by="creation desc")
	if not service_name:
		return True  # nothing seeded yet in this run order — nothing to test
	service = frappe.get_doc("Pig Breeding Service", service_name)
	if service.status != "Farrowed":
		return True  # hasn't reached the terminal state yet — nothing to test
	service.status = "Served"  # Farrowed -> Served skips backwards, should be blocked
	blocked = False
	try:
		service.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("PF02 negative test FAILED: an invalid breeding lifecycle transition was not blocked!")
	return True


def _test_pf05_withdrawal_sale_blocked():
	batch_name = frappe.db.get_value("Pig Grower Batch", {"pen": _GROWER_PEN}, "name", order_by="creation desc")
	if not batch_name or frappe.db.get_value("Pig Grower Batch", batch_name, "status") != "Sold":
		return True  # batch hasn't been sold yet in this run order — nothing to test
	treatment_date = frappe.db.get_value("Pig Medicine Treatment", {"batch": batch_name}, "treatment_date")
	if not treatment_date:
		return True
	attempt = frappe.get_doc(
		{
			"doctype": "Pig Sale Lot",
			"batch": batch_name,
			"sale_date": frappe.utils.add_days(treatment_date, 1),  # 1 day into a 10-day withdrawal
			"customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"),
			"head_count": 1,
			"total_weight_kg": 90.0,
			"sale_price": 6000000,
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
		attempt.delete(ignore_permissions=True)  # would only run if the block failed
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("PF05 negative test FAILED: selling within the medicine withdrawal period was not blocked!")
	return True


def seed_pig_validations():
	"""DP-577 — PF01/PF02/PF05 negative tests. Same "only actually tests something once the
	flow has reached the relevant state" caveat as Shrimp Farm's seed_shrimp_validations — run
	this AFTER seed_pig_sale for full coverage."""
	pf01 = _test_pf01_duplicate_tag_blocked()
	pf02 = _test_pf02_invalid_transition_blocked()
	pf05 = _test_pf05_withdrawal_sale_blocked()
	return f"seed_pig_validations: PF01 CONFIRMED ({pf01}). PF02 CONFIRMED ({pf02}). PF05 CONFIRMED ({pf05})."
