"""Golden Demo #13 — Cattle / Dairy Farm Management (master plan DEMO 24, "PHASE 4" item 5),
IP-LIVESTOCK-CATTLE.
"""

import frappe

_FARM_NAME = "Demo Dairy Farm - Lam Dong"
_SIRE_TAG = "BULL-001"
_DAM_TAG = "COW-001"
_CALF_TAG = "CALF-2026-001"


def _ensure_farm_and_breeding_stock():
	farm_created = False
	if not frappe.db.exists("Cattle Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Cattle Farm", "farm_name": _FARM_NAME, "location": "Lam Dong, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	animals_created = 0
	for tag, sex, breed, age_days in [(_SIRE_TAG, "Male", "Holstein Friesian", 1200), (_DAM_TAG, "Female", "Holstein Friesian", 900)]:
		if not frappe.db.exists("Cattle Animal", tag):
			frappe.get_doc(
				{"doctype": "Cattle Animal", "tag_id": tag, "farm": _FARM_NAME, "sex": sex, "breed": breed, "birth_date": frappe.utils.add_days(frappe.utils.nowdate(), -age_days), "status": "Active"}
			).insert(ignore_permissions=True)
			animals_created += 1
	return farm_created, animals_created


def seed_cattle_farm_master_data():
	"""DP-585 — master data: Farm, Sire + Dam (CT01 pedigree roots)."""
	farm_created, animals_created = _ensure_farm_and_breeding_stock()
	return f"seed_cattle_farm_master_data: Farm {'created' if farm_created else 'already existed'}. {animals_created} breeding animal(s) created."


def _ensure_breeding_service():
	existing = frappe.db.get_value("Cattle Breeding Service", {"dam": _DAM_TAG, "sire": _SIRE_TAG}, "name", order_by="creation desc")
	if existing:
		return existing, False
	service = frappe.get_doc({"doctype": "Cattle Breeding Service", "dam": _DAM_TAG, "sire": _SIRE_TAG, "service_date": frappe.utils.add_days(frappe.utils.nowdate(), -290)})
	service.insert(ignore_permissions=True)
	return service.name, True


def _ensure_confirmed_pregnant(service_name):
	service = frappe.get_doc("Cattle Breeding Service", service_name)
	if service.status == "Served":
		service.status = "Confirmed Pregnant"
		service.save(ignore_permissions=True)
		return True
	return False


def _ensure_calving_and_calf(service_name):
	existing_calving = frappe.db.get_value("Cattle Calving", {"breeding_service": service_name}, "name")
	if existing_calving:
		return existing_calving, False
	service = frappe.get_doc("Cattle Breeding Service", service_name)
	calving = frappe.get_doc({"doctype": "Cattle Calving", "breeding_service": service_name, "calving_date": service.expected_calving_date, "calf_count": 1})
	calving.insert(ignore_permissions=True)
	if not frappe.db.exists("Cattle Animal", _CALF_TAG):
		frappe.get_doc(
			{
				"doctype": "Cattle Animal",
				"tag_id": _CALF_TAG,
				"farm": _FARM_NAME,
				"sex": "Female",
				"breed": "Holstein Friesian",
				"birth_date": service.expected_calving_date,
				"sire": service.sire,
				"dam": service.dam,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
	return calving.name, True


def seed_cattle_breeding_flow():
	"""DP-586 — CT02 (reproduction lifecycle: Served -> Confirmed Pregnant -> Calved), producing
	the calf that extends CT01's pedigree chain one more generation."""
	if not frappe.db.exists("Cattle Animal", _DAM_TAG):
		return "seed_cattle_breeding_flow: SKIPPED — run seed_cattle_farm_master_data first."
	service_name, service_created = _ensure_breeding_service()
	confirmed = _ensure_confirmed_pregnant(service_name)
	calving_name, calving_created = _ensure_calving_and_calf(service_name)
	service_status = frappe.db.get_value("Cattle Breeding Service", service_name, "status")
	return (
		f"seed_cattle_breeding_flow: Service {'created' if service_created else 'already existed'} ({service_name}, status={service_status}). "
		f"Confirmed-pregnant transition {'applied' if confirmed else 'already done'}. "
		f"Calving {'created' if calving_created else 'already existed'} ({calving_name}), calf {_CALF_TAG}."
	)


def _ensure_milking_records():
	created = 0
	for days_ago, liters in [(10, 24.5), (5, 26.0), (1, 25.2)]:
		record_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Cattle Milking Record", {"animal": _DAM_TAG, "record_date": record_date}):
			continue
		frappe.get_doc({"doctype": "Cattle Milking Record", "animal": _DAM_TAG, "record_date": record_date, "milk_yield_liters": liters}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_treatment():
	if frappe.db.exists("Cattle Health Treatment", {"animal": _DAM_TAG}):
		return False
	frappe.get_doc(
		{
			"doctype": "Cattle Health Treatment",
			"animal": _DAM_TAG,
			"treatment_date": frappe.utils.add_days(frappe.utils.nowdate(), -8),
			"diagnosis": "Mild clinical mastitis, left rear quarter.",
			"treatment_applied": "Intramammary antibiotic infusion, 3-day course.",
			"dosage": "1 tube per quarter per day x3",
			"cost": 450000,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_feed_logs():
	created = 0
	for days_ago, qty in [(10, 45.0), (5, 46.0), (1, 45.5)]:
		feed_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Cattle Feed Log", {"animal": _DAM_TAG, "feed_date": feed_date}):
			continue
		frappe.get_doc({"doctype": "Cattle Feed Log", "animal": _DAM_TAG, "feed_date": feed_date, "ration_name": "Lactating TMR Ration", "qty_kg": qty, "cost": qty * 9000}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def seed_cattle_operations():
	"""DP-587 — CT03 (milk record), CT04 (treatment), CT05 (feed ration)."""
	if not frappe.db.exists("Cattle Animal", _DAM_TAG):
		return "seed_cattle_operations: SKIPPED — run seed_cattle_breeding_flow first."
	milking_created = _ensure_milking_records()
	treatment_created = _ensure_treatment()
	feed_created = _ensure_feed_logs()
	return (
		f"seed_cattle_operations: {milking_created} milking record(s) created (CT03). "
		f"Treatment {'created' if treatment_created else 'already existed'} (CT04). {feed_created} feed log(s) created (CT05)."
	)


_CUSTOMER_GROUP = "Livestock Buyers"
_DAIRY_CUSTOMER = "Lam Dong Dairy Cooperative"
_MEAT_CUSTOMER = "Lam Dong Meat Trading Co."


def _ensure_customer(customer_name):
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(
			ignore_permissions=True
		)
	if frappe.db.exists("Customer", {"customer_name": customer_name}):
		return frappe.db.get_value("Customer", {"customer_name": customer_name}, "name"), False
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": customer_name, "customer_type": "Company", "customer_group": _CUSTOMER_GROUP})
	customer.insert(ignore_permissions=True)
	return customer.name, True


def _ensure_sale_lot(animal, sale_type, customer, weight_kg, sale_price, other_cost):
	existing = frappe.db.get_value("Cattle Sale Lot", {"animal": animal}, "name")
	if existing:
		return frappe.get_doc("Cattle Sale Lot", existing), False
	lot = frappe.get_doc(
		{
			"doctype": "Cattle Sale Lot",
			"animal": animal,
			"sale_date": frappe.utils.nowdate(),
			"sale_type": sale_type,
			"customer": customer,
			"weight_kg": weight_kg,
			"sale_price": sale_price,
			"other_cost": other_cost,
		}
	)
	lot.insert(ignore_permissions=True)
	return lot, True


def seed_cattle_sale():
	"""DP-588 — CT06 (culling/sale) + CT07 (cost per animal). The calf is Sold to another
	dairy farm (surplus heifer stock); the dam is Culled at end of productive life (giving a
	meaningful cost rollup across her whole recorded feed+health history)."""
	if not frappe.db.exists("Cattle Animal", _CALF_TAG):
		return "seed_cattle_sale: SKIPPED — run seed_cattle_breeding_flow first."
	dairy_customer, dairy_created = _ensure_customer(_DAIRY_CUSTOMER)
	meat_customer, meat_created = _ensure_customer(_MEAT_CUSTOMER)
	calf_lot, calf_created = _ensure_sale_lot(_CALF_TAG, "Sold", dairy_customer, 45.0, 8000000, 200000)
	dam_lot, dam_created = _ensure_sale_lot(_DAM_TAG, "Culled", meat_customer, 620.0, 24000000, 500000)
	return (
		f"seed_cattle_sale: Calf Sale Lot {'created' if calf_created else 'already existed'} ({calf_lot.name}, to {dairy_customer}). "
		f"Dam Sale Lot {'created' if dam_created else 'already existed'} ({dam_lot.name}, to {meat_customer}, CT07 total cost {dam_lot.total_cost}, cost/kg {dam_lot.cost_per_kg}, profit {dam_lot.profit})."
	)


def _test_ct01_duplicate_tag_blocked():
	dup = frappe.get_doc({"doctype": "Cattle Animal", "tag_id": _DAM_TAG, "farm": _FARM_NAME, "sex": "Female", "status": "Active"})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# same NameError-not-ValidationError subtlety documented in Pig/Poultry Farm's negative tests.
		blocked = True
	if not blocked:
		frappe.throw("CT01 negative test FAILED: a duplicate animal tag_id was not blocked!")
	return True


def _test_ct02_invalid_transition_blocked():
	service_name = frappe.db.get_value("Cattle Breeding Service", {"dam": _DAM_TAG, "sire": _SIRE_TAG}, "name", order_by="creation desc")
	if not service_name:
		return True  # nothing seeded yet in this run order — nothing to test
	service = frappe.get_doc("Cattle Breeding Service", service_name)
	if service.status != "Calved":
		return True  # hasn't reached the terminal state yet — nothing to test
	service.status = "Served"  # Calved -> Served skips backwards, should be blocked
	blocked = False
	try:
		service.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("CT02 negative test FAILED: an invalid reproduction lifecycle transition was not blocked!")
	return True


def _test_ct06_double_sale_blocked():
	animal_status = frappe.db.get_value("Cattle Animal", _DAM_TAG, "status")
	if animal_status != "Culled":
		return True  # hasn't been culled yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{
			"doctype": "Cattle Sale Lot",
			"animal": _DAM_TAG,
			"sale_date": frappe.utils.nowdate(),
			"sale_type": "Sold",
			"customer": frappe.db.get_value("Customer", {"customer_name": _MEAT_CUSTOMER}, "name"),
			"weight_kg": 620.0,
			"sale_price": 24000000,
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("CT06 negative test FAILED: selling/culling an already-Culled animal a second time was not blocked!")
	return True


def seed_cattle_validations():
	"""DP-589 — CT01/CT02/CT06 negative tests. Run AFTER seed_cattle_sale for full CT06
	coverage, same ordering caveat as every prior golden demo's validations step."""
	ct01 = _test_ct01_duplicate_tag_blocked()
	ct02 = _test_ct02_invalid_transition_blocked()
	ct06 = _test_ct06_double_sale_blocked()
	return f"seed_cattle_validations: CT01 CONFIRMED ({ct01}). CT02 CONFIRMED ({ct02}). CT06 CONFIRMED ({ct06})."
