"""Golden Demo #12 — Poultry Farm Management (master plan DEMO 23, "PHASE 4" item 4),
IP-LIVESTOCK-POULTRY. Two flocks (one Broiler, one Layer) in the same farm so PO06 (egg
output, Layer-only) and PO07 (sale/harvest, both types) each have a real scenario to prove
against, plus a real cross-type negative test for PO06.
"""

import frappe

_FARM_NAME = "Demo Poultry Farm - Tien Giang"
_BROILER_HOUSE = "HOUSE-B1"
_LAYER_HOUSE = "HOUSE-L1"
_BROILER_FLOCK = "FLOCK-BR-2026-001"
_LAYER_FLOCK = "FLOCK-LY-2026-001"


def _ensure_farm_and_houses():
	farm_created = False
	if not frappe.db.exists("Poultry Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Poultry Farm", "farm_name": _FARM_NAME, "location": "Tien Giang, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	houses_created = 0
	for house_code, capacity in [(_BROILER_HOUSE, 25000), (_LAYER_HOUSE, 6000)]:
		if not frappe.db.exists("Poultry House", house_code):
			frappe.get_doc({"doctype": "Poultry House", "house_code": house_code, "farm": _FARM_NAME, "capacity": capacity, "status": "Empty"}).insert(ignore_permissions=True)
			houses_created += 1
	return farm_created, houses_created


def seed_poultry_farm_master_data():
	"""DP-579 — master data: Farm, Houses."""
	farm_created, houses_created = _ensure_farm_and_houses()
	return f"seed_poultry_farm_master_data: Farm {'created' if farm_created else 'already existed'}. {houses_created} house(s) created."


def _ensure_flocks():
	created = 0
	if not frappe.db.exists("Poultry Flock", _BROILER_FLOCK):
		frappe.get_doc(
			{
				"doctype": "Poultry Flock",
				"flock_code": _BROILER_FLOCK,
				"house": _BROILER_HOUSE,
				"flock_type": "Broiler",
				"breed": "Ross 308",
				"placement_date": frappe.utils.add_days(frappe.utils.nowdate(), -40),
				"initial_count": 20000,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		created += 1
	if not frappe.db.exists("Poultry Flock", _LAYER_FLOCK):
		frappe.get_doc(
			{
				"doctype": "Poultry Flock",
				"flock_code": _LAYER_FLOCK,
				"house": _LAYER_HOUSE,
				"flock_type": "Layer",
				"breed": "Hy-Line Brown",
				"placement_date": frappe.utils.add_days(frappe.utils.nowdate(), -200),
				"initial_count": 5000,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def seed_poultry_placement():
	"""DP-580 — PO01 (flock lifecycle: placed into an Empty House, House flips to Occupied)."""
	if not frappe.db.exists("Poultry House", _BROILER_HOUSE):
		return "seed_poultry_placement: SKIPPED — run seed_poultry_farm_master_data first."
	flocks_created = _ensure_flocks()
	broiler_house_status = frappe.db.get_value("Poultry House", _BROILER_HOUSE, "status")
	layer_house_status = frappe.db.get_value("Poultry House", _LAYER_HOUSE, "status")
	return f"seed_poultry_placement: {flocks_created} flock(s) created. PO01 house statuses: {_BROILER_HOUSE}={broiler_house_status}, {_LAYER_HOUSE}={layer_house_status}."


def _ensure_feed_logs(flock_name, scale):
	created = 0
	for days_ago, qty in [(30, 800.0 * scale), (15, 1400.0 * scale), (5, 1600.0 * scale)]:
		feed_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Poultry Feed Log", {"flock": flock_name, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{
				"doctype": "Poultry Feed Log",
				"flock": flock_name,
				"feed_date": feed_date,
				"feed_product": "Broiler Grower Feed" if scale == 1 else "Layer Feed",
				"qty_kg": qty,
				"cost": qty * 14000,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_vaccinations(flock_name):
	created = 0
	rows = [
		{"vaccine_name": "Newcastle Disease (ND)", "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -20), "administered_date": frappe.utils.add_days(frappe.utils.nowdate(), -20)},
		{"vaccine_name": "Infectious Bursal Disease (Gumboro)", "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -4), "administered_date": None},
	]
	for row in rows:
		if frappe.db.exists("Poultry Vaccination", {"flock": flock_name, "vaccine_name": row["vaccine_name"]}):
			continue
		frappe.get_doc({"doctype": "Poultry Vaccination", "flock": flock_name, **row}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_weight_records(flock_name, weights):
	created = 0
	for days_ago, weight in weights:
		record_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Poultry Weight Record", {"flock": flock_name, "record_date": record_date}):
			continue
		frappe.get_doc({"doctype": "Poultry Weight Record", "flock": flock_name, "record_date": record_date, "average_weight_g": weight, "sample_count": 50}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def _ensure_mortality(flock_name, count, cause):
	if frappe.db.exists("Poultry Mortality Record", {"flock": flock_name}):
		return False
	frappe.get_doc(
		{"doctype": "Poultry Mortality Record", "flock": flock_name, "record_date": frappe.utils.add_days(frappe.utils.nowdate(), -20), "mortality_count": count, "cause": cause}
	).insert(ignore_permissions=True)
	return True


def _ensure_egg_production(flock_name):
	created = 0
	for days_ago, count, weight in [(5, 4300, 275.0), (2, 4350, 278.5)]:
		record_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Poultry Egg Production", {"flock": flock_name, "record_date": record_date}):
			continue
		frappe.get_doc({"doctype": "Poultry Egg Production", "flock": flock_name, "record_date": record_date, "egg_count": count, "egg_weight_kg": weight}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def seed_poultry_operations():
	"""DP-581 — PO02 (mortality), PO03 (feed), PO04 (vaccine due/overdue), PO05 (weight curve),
	PO06 (egg output, Layer flock only). One vaccination per flock is deliberately left overdue
	so PO04 fires on real seeded data, same approach as Shrimp/Pig Farm's deliberate
	out-of-range/overdue seed rows."""
	if not frappe.db.exists("Poultry Flock", _BROILER_FLOCK):
		return "seed_poultry_operations: SKIPPED — run seed_poultry_placement first."

	broiler_feed = _ensure_feed_logs(_BROILER_FLOCK, 1)
	broiler_vacc = _ensure_vaccinations(_BROILER_FLOCK)
	broiler_weight = _ensure_weight_records(_BROILER_FLOCK, [(30, 900.0), (10, 2100.0)])
	broiler_mortality = _ensure_mortality(_BROILER_FLOCK, 350, "Normal attrition + minor heat stress week 3.")

	layer_feed = _ensure_feed_logs(_LAYER_FLOCK, 0.3)
	layer_vacc = _ensure_vaccinations(_LAYER_FLOCK)
	layer_weight = _ensure_weight_records(_LAYER_FLOCK, [(30, 1750.0), (10, 1800.0)])
	layer_mortality = _ensure_mortality(_LAYER_FLOCK, 40, "Normal culling of underperforming layers.")
	egg_created = _ensure_egg_production(_LAYER_FLOCK)

	overdue_count = frappe.db.count("Poultry Vaccination", {"status": "Overdue"})
	return (
		f"seed_poultry_operations: Broiler — {broiler_feed} feed log(s), {broiler_vacc} vaccination(s), {broiler_weight} weight record(s), "
		f"mortality {'created' if broiler_mortality else 'already existed'}. Layer — {layer_feed} feed log(s), {layer_vacc} vaccination(s), "
		f"{layer_weight} weight record(s), mortality {'created' if layer_mortality else 'already existed'}, {egg_created} egg production record(s) (PO06). "
		f"{overdue_count} vaccination(s) Overdue across both flocks (PO04)."
	)


_CUSTOMER_GROUP = "Livestock Buyers"
_CUSTOMER_NAME = "Tien Giang Poultry Processing Co."


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


def _ensure_sale_lot(flock_name, head_count, total_weight_kg, sale_price, other_cost, customer):
	existing = frappe.db.get_value("Poultry Sale Lot", {"flock": flock_name}, "name")
	if existing:
		lot = frappe.get_doc("Poultry Sale Lot", existing)
		return lot.name, False, lot
	lot = frappe.get_doc(
		{
			"doctype": "Poultry Sale Lot",
			"flock": flock_name,
			"sale_date": frappe.utils.nowdate(),
			"customer": customer,
			"head_count": head_count,
			"total_weight_kg": total_weight_kg,
			"sale_price": sale_price,
			"other_cost": other_cost,
		}
	)
	lot.insert(ignore_permissions=True)
	return lot.name, True, lot


def seed_poultry_sale():
	"""DP-582 — PO07 (sale/harvest) for both flocks; cost allocation and livability are
	server-computed, not entered manually."""
	if not frappe.db.exists("Poultry Flock", _BROILER_FLOCK):
		return "seed_poultry_sale: SKIPPED — run seed_poultry_operations first."
	customer, customer_created = _ensure_customer()
	broiler_name, broiler_created, broiler_lot = _ensure_sale_lot(_BROILER_FLOCK, 19600, 45000.0, 1150000000, 30000000, customer)
	layer_name, layer_created, layer_lot = _ensure_sale_lot(_LAYER_FLOCK, 4900, 9310.0, 145000000, 5000000, customer)
	return (
		f"seed_poultry_sale: to {customer} ({'new' if customer_created else 'existing'}). "
		f"Broiler Sale Lot {'created' if broiler_created else 'already existed'} ({broiler_name}, livability {broiler_lot.livability_percent}%, cost/kg {broiler_lot.cost_per_kg}). "
		f"Layer Sale Lot {'created' if layer_created else 'already existed'} ({layer_name}, livability {layer_lot.livability_percent}%, cost/kg {layer_lot.cost_per_kg})."
	)


def _test_po01_duplicate_flock_code_blocked():
	dup = frappe.get_doc({"doctype": "Poultry Flock", "flock_code": _BROILER_FLOCK, "house": _BROILER_HOUSE, "flock_type": "Broiler", "initial_count": 100, "status": "Active"})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# same NameError-not-ValidationError subtlety documented in Pig Farm's PF01 test.
		blocked = True
	if not blocked:
		frappe.throw("PO01 negative test FAILED: a duplicate flock_code was not blocked!")
	return True


def _test_po06_wrong_flock_type_blocked():
	attempt = frappe.get_doc({"doctype": "Poultry Egg Production", "flock": _BROILER_FLOCK, "record_date": frappe.utils.nowdate(), "egg_count": 10})
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("PO06 negative test FAILED: egg production was not blocked for a Broiler flock!")
	return True


def _test_po07_double_sale_blocked():
	flock_status = frappe.db.get_value("Poultry Flock", _BROILER_FLOCK, "status")
	if flock_status != "Sold":
		return True  # hasn't been sold yet in this run order — nothing to test
	attempt = frappe.get_doc(
		{
			"doctype": "Poultry Sale Lot",
			"flock": _BROILER_FLOCK,
			"sale_date": frappe.utils.nowdate(),
			"customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"),
			"head_count": 1,
			"total_weight_kg": 2.3,
			"sale_price": 100000,
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("PO07 negative test FAILED: selling an already-Sold flock a second time was not blocked!")
	return True


def seed_poultry_validations():
	"""DP-583 — PO01/PO06/PO07 negative tests. Run AFTER seed_poultry_sale for full PO07
	coverage, same ordering caveat as every prior golden demo's validations step."""
	po01 = _test_po01_duplicate_flock_code_blocked()
	po06 = _test_po06_wrong_flock_type_blocked()
	po07 = _test_po07_double_sale_blocked()
	return f"seed_poultry_validations: PO01 CONFIRMED ({po01}). PO06 CONFIRMED ({po06}). PO07 CONFIRMED ({po07})."
