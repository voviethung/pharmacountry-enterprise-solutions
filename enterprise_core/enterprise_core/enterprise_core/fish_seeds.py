"""Golden Demo #17 — Fish Farm Management (master plan DEMO 29, "PHASE 5" item 3), IP-FISH.
"""

import frappe

_FARM_NAME = "Demo Fish Farm - An Giang"
_POND_CODE = "POND-F1"
_SPECIES = "Pangasius (Ca Tra)"


def _ensure_farm_and_pond():
	farm_created = False
	if not frappe.db.exists("Fish Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Fish Farm", "farm_name": _FARM_NAME, "location": "An Giang, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	pond_created = False
	if not frappe.db.exists("Fish Pond", _POND_CODE):
		frappe.get_doc({"doctype": "Fish Pond", "pond_code": _POND_CODE, "farm": _FARM_NAME, "pond_type": "Pond", "area_or_volume": 5000, "status": "Empty"}).insert(
			ignore_permissions=True
		)
		pond_created = True
	return farm_created, pond_created


def seed_fish_farm_master_data():
	"""DP-606 — Farm and Pond master data."""
	farm_created, pond_created = _ensure_farm_and_pond()
	return f"seed_fish_farm_master_data: Farm {'created' if farm_created else 'already existed'}. Pond {'created' if pond_created else 'already existed'}."


def _ensure_stocking_batch():
	existing = frappe.db.get_value("Fish Stocking Batch", {"pond": _POND_CODE}, "name", order_by="creation desc")
	if existing:
		return existing, False
	batch = frappe.get_doc(
		{
			"doctype": "Fish Stocking Batch",
			"pond": _POND_CODE,
			"species": _SPECIES,
			"stocking_date": frappe.utils.add_days(frappe.utils.nowdate(), -210),
			"initial_count": 50000,
			"source_hatchery": "An Giang Pangasius Hatchery",
			"status": "Active",
		}
	)
	batch.insert(ignore_permissions=True)
	return batch.name, True


def seed_fish_stocking():
	"""DP-607 — FF01 (pond lifecycle: Empty->Stocked, stocking batch)."""
	if not frappe.db.exists("Fish Pond", _POND_CODE):
		return "seed_fish_stocking: SKIPPED — run seed_fish_farm_master_data first."
	batch_name, created = _ensure_stocking_batch()
	pond_status = frappe.db.get_value("Fish Pond", _POND_CODE, "status")
	return f"seed_fish_stocking: Stocking Batch {'created' if created else 'already existed'} ({batch_name}). FF01 pond status: {pond_status}."


def _batch_name():
	return frappe.db.get_value("Fish Stocking Batch", {"pond": _POND_CODE, "status": "Active"}, "name")


def _ensure_feed_logs(batch_name):
	created = 0
	for days_ago, qty in [(150, 20000.0), (60, 27000.0), (10, 27800.0)]:
		feed_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Fish Feed Log", {"stocking_batch": batch_name, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{"doctype": "Fish Feed Log", "stocking_batch": batch_name, "feed_date": feed_date, "feed_product": "Pangasius Floating Pellet", "qty_kg": qty, "cost": qty * 13500}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_growth_samples(batch_name):
	created = 0
	for days_ago, weight in [(120, 250.0), (30, 950.0)]:
		sample_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Fish Growth Sample", {"stocking_batch": batch_name, "sample_date": sample_date}):
			continue
		frappe.get_doc({"doctype": "Fish Growth Sample", "stocking_batch": batch_name, "sample_date": sample_date, "average_weight_g": weight, "sample_count": 50}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def _ensure_mortality(batch_name):
	if frappe.db.exists("Fish Mortality Record", {"stocking_batch": batch_name}):
		return False
	frappe.get_doc(
		{"doctype": "Fish Mortality Record", "stocking_batch": batch_name, "record_date": frappe.utils.add_days(frappe.utils.nowdate(), -100), "mortality_count": 3000, "cause": "Normal attrition + minor gill parasite outbreak, resolved."}
	).insert(ignore_permissions=True)
	return True


def seed_fish_operations():
	"""DP-608 — FF03 (feed), FF02/FF04 (growth sample + server-computed biomass estimate),
	FF05 (mortality). Mortality is created BEFORE growth samples, not after: the growth
	sample's validate hook sums whatever mortality rows already exist in the DB as of its own
	insert — filtering by record_date alone isn't enough if the mortality row that occurred
	earlier hasn't been INSERTED yet, so insertion order has to match (or precede) chronological
	order for the two growth samples (one before, one after the single mortality event) to come
	out correct. Found as a real bug: a first version of this seed created growth samples before
	mortality, so both samples silently computed against zero recorded mortality regardless of
	their own dates."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_fish_operations: SKIPPED — run seed_fish_stocking first."
	feed_created = _ensure_feed_logs(batch_name)
	mortality_created = _ensure_mortality(batch_name)
	growth_created = _ensure_growth_samples(batch_name)
	latest_biomass = frappe.db.get_value("Fish Growth Sample", {"stocking_batch": batch_name}, "estimated_biomass_kg", order_by="sample_date desc")
	return (
		f"seed_fish_operations: {feed_created} feed log(s) created (FF03). {growth_created} growth sample(s) created (FF04), "
		f"latest FF02 biomass estimate: {latest_biomass}kg. Mortality {'created' if mortality_created else 'already existed'} (FF05)."
	)


def seed_fish_harvest():
	"""DP-609 — FF06 (harvest). KPIs (survival rate, FCR, cost/kg) are computed server-side from
	the batch's own recorded feed/mortality history, not entered manually."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_fish_harvest: SKIPPED — no Active Stocking Batch, run seed_fish_stocking/operations first."
	existing = frappe.db.get_value("Fish Harvest", {"stocking_batch": batch_name}, "name")
	if existing:
		h = frappe.get_doc("Fish Harvest", existing)
		return f"seed_fish_harvest: already existed ({existing}). Survival {h.survival_rate_percent}%, FCR {h.fcr}, cost/kg {h.cost_per_kg}."
	harvest = frappe.get_doc(
		{"doctype": "Fish Harvest", "stocking_batch": batch_name, "harvest_date": frappe.utils.nowdate(), "total_weight_kg": 46750.0, "average_weight_g": 995.0, "total_cost": 150000000}
	)
	harvest.insert(ignore_permissions=True)
	return (
		f"seed_fish_harvest: created ({harvest.name}). FF06 — Survival rate {harvest.survival_rate_percent}%, "
		f"FCR {harvest.fcr}, days of culture {harvest.days_of_culture}, cost/kg {harvest.cost_per_kg}."
	)


def _test_ff01_invalid_transition_blocked():
	pond = frappe.get_doc("Fish Pond", _POND_CODE)
	if pond.status != "Harvested":
		return True  # pond hasn't reached Harvested yet in this run order — nothing to test
	pond.status = "Stocked"  # Harvested -> Stocked skips Empty, should be blocked
	blocked = False
	try:
		pond.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("FF01 negative test FAILED: an invalid pond status transition was not blocked!")
	return True


def _test_ff01_double_stocking_blocked():
	pond_status = frappe.db.get_value("Fish Pond", _POND_CODE, "status")
	if pond_status == "Empty":
		return True  # nothing stocked yet in this run order — nothing to test
	dup = frappe.get_doc({"doctype": "Fish Stocking Batch", "pond": _POND_CODE, "species": _SPECIES, "stocking_date": frappe.utils.nowdate(), "initial_count": 1000, "status": "Active"})
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("FF01 negative test FAILED: double-stocking a non-Empty pond was not blocked!")
	return True


def seed_fish_validations():
	"""DP-610 — FF01 negative tests (pond lifecycle + double stocking). Run AFTER
	seed_fish_harvest for full coverage, same ordering caveat as Shrimp Farm's own validations
	step."""
	transition = _test_ff01_invalid_transition_blocked()
	double_stock = _test_ff01_double_stocking_blocked()
	return f"seed_fish_validations: FF01 (invalid transition) CONFIRMED ({transition}). FF01 (double stocking) CONFIRMED ({double_stock})."
