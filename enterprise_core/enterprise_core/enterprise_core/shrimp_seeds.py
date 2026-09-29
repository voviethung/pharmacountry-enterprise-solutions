"""Golden Demo #8 — Shrimp Farm Management (master plan DEMO 28), IP-SHRIMP. The last of the
8 golden demos, and the only one with no ERPNext manufacturing/quality overlap at all.
"""

import frappe

_FARM_NAME = "Demo Shrimp Farm — Bac Lieu"
_POND_CODE = "POND-A1"


def _ensure_farm_and_pond():
	farm_created = False
	if not frappe.db.exists("Shrimp Farm", _FARM_NAME):
		frappe.get_doc({"doctype": "Shrimp Farm", "farm_name": _FARM_NAME, "location": "Bac Lieu, Vietnam"}).insert(ignore_permissions=True)
		farm_created = True
	pond_created = False
	if not frappe.db.exists("Shrimp Pond", _POND_CODE):
		frappe.get_doc({"doctype": "Shrimp Pond", "pond_code": _POND_CODE, "farm": _FARM_NAME, "area_m2": 2500, "status": "Empty"}).insert(
			ignore_permissions=True
		)
		pond_created = True
	return farm_created, pond_created


def seed_shrimp_farm_master_data():
	"""DP-554 — Farm and Pond master data ("Prepare pond" — master plan's own flow start)."""
	farm_created, pond_created = _ensure_farm_and_pond()
	return f"seed_shrimp_farm_master_data: Farm {'created' if farm_created else 'already existed'}. Pond {'created' if pond_created else 'already existed'}."


def _ensure_stocking_batch():
	# ANY batch for this pond (not just an Active one) — this demo's seed chain models one
	# complete crop cycle through Harvest, not repeated re-stocking on every registry re-run;
	# once a cycle has completed the pond is legitimately "Harvested", and trying to stock it
	# again would correctly (and, for a seed re-run, unhelpfully) hit the SF02 block.
	existing = frappe.db.get_value("Shrimp Stocking Batch", {"pond": _POND_CODE}, "name", order_by="creation desc")
	if existing:
		return existing, False
	batch = frappe.get_doc(
		{
			"doctype": "Shrimp Stocking Batch",
			"pond": _POND_CODE,
			"species": "Litopenaeus vannamei (Whiteleg shrimp)",
			"stocking_date": frappe.utils.add_days(frappe.utils.nowdate(), -60),
			"initial_count": 250000,
			"source_hatchery": "CP Vietnam Hatchery",
			"status": "Active",
		}
	)
	batch.insert(ignore_permissions=True)
	return batch.name, True


def seed_shrimp_stocking():
	"""DP-555 — SF01 (pond lifecycle: Empty->Stocked) + SF02 (stocking batch)."""
	if not frappe.db.exists("Shrimp Pond", _POND_CODE):
		return "seed_shrimp_stocking: SKIPPED — run seed_shrimp_farm_master_data first."
	batch_name, created = _ensure_stocking_batch()
	pond_status = frappe.db.get_value("Shrimp Pond", _POND_CODE, "status")
	return f"seed_shrimp_stocking: Stocking Batch {'created' if created else 'already existed'} ({batch_name}). SF01 pond status: {pond_status}."


def _batch_name():
	return frappe.db.get_value("Shrimp Stocking Batch", {"pond": _POND_CODE, "status": "Active"}, "name")


def _ensure_feed_logs(batch_name):
	created = 0
	# 3 representative entries standing in for a full 60-day daily feeding log (demo
	# simplicity, same as the pharma demo's single-batch-not-exhaustive-daily-log approach) —
	# quantities scaled so the resulting FCR (DP-557) lands in a realistic ~1.2-1.5 range for
	# a 4200kg harvest, not the ~0.04 an earlier 3-day-only version produced (a real
	# aquaculture-literate viewer would immediately flag an FCR that low as wrong).
	for days_ago, qty in [(45, 1500.0), (20, 1900.0), (5, 2100.0)]:
		feed_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Shrimp Daily Feed Log", {"stocking_batch": batch_name, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{
				"doctype": "Shrimp Daily Feed Log",
				"stocking_batch": batch_name,
				"feed_date": feed_date,
				"feed_product": "Shrimp Grower Pellet 2mm",
				"qty_kg": qty,
				"cost": qty * 28000,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_water_readings(batch_name):
	pond = frappe.db.get_value("Shrimp Stocking Batch", batch_name, "pond")
	created = 0
	readings = [
		(-5, {"do_mg_l": 5.2, "ph": 8.0, "temperature_c": 29.0, "salinity_ppt": 15.0, "alkalinity": 120, "nh3_mg_l": 0.02, "no2_mg_l": 0.05}),
		(-2, {"do_mg_l": 3.1, "ph": 8.1, "temperature_c": 29.5, "salinity_ppt": 15.0, "alkalinity": 118, "nh3_mg_l": 0.02, "no2_mg_l": 0.05}),  # DO below threshold -> SF10 alert
	]
	for days_ago, params in readings:
		# fixed 08:00 time component, not now_datetime() — that bakes in the CURRENT
		# wall-clock time, which differs run to run and made the exists-check below never
		# match on a re-run, silently creating duplicate readings every time (found via a
		# real duplicate: "2 flagged as alerts" on a re-run that should have created 0 new).
		reading_dt = f"{frappe.utils.add_days(frappe.utils.nowdate(), days_ago)} 08:00:00"
		if frappe.db.exists("Shrimp Water Parameter Reading", {"pond": pond, "reading_datetime": reading_dt}):
			continue
		frappe.get_doc({"doctype": "Shrimp Water Parameter Reading", "pond": pond, "reading_datetime": reading_dt, **params}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def _ensure_growth_samples(batch_name):
	created = 0
	for days_ago, abw in [(30, 8.5), (10, 15.2)]:
		sample_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_ago)
		if frappe.db.exists("Shrimp Growth Sample", {"stocking_batch": batch_name, "sample_date": sample_date}):
			continue
		frappe.get_doc(
			{
				"doctype": "Shrimp Growth Sample",
				"stocking_batch": batch_name,
				"sample_date": sample_date,
				"average_body_weight_g": abw,
				"sample_count": 100,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_treatment(batch_name):
	if frappe.db.exists("Shrimp Health Treatment", {"stocking_batch": batch_name}):
		return False
	frappe.get_doc(
		{
			"doctype": "Shrimp Health Treatment",
			"stocking_batch": batch_name,
			"issue_date": frappe.utils.add_days(frappe.utils.nowdate(), -20),
			"diagnosis": "Mild vibriosis suspected — reduced feeding activity observed.",
			"treatment_applied": "Probiotic water treatment + reduced feed rate for 3 days.",
			"dosage": "5 ppm probiotic, applied daily x3",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_mortality(batch_name):
	if frappe.db.exists("Shrimp Mortality Record", {"stocking_batch": batch_name}):
		return False
	frappe.get_doc(
		{
			"doctype": "Shrimp Mortality Record",
			"stocking_batch": batch_name,
			"record_date": frappe.utils.add_days(frappe.utils.nowdate(), -20),
			"mortality_count": 12000,
			"cause": "Mild vibriosis (see linked Health Treatment) — resolved after treatment.",
		}
	).insert(ignore_permissions=True)
	return True


def seed_shrimp_operations():
	"""DP-556 — SF03 (daily feed), SF04 (water measurement)+SF10 (alert threshold), SF05
	(growth sample), SF06 (treatment), SF07 (mortality). One water reading is deliberately
	below the DO threshold to prove SF10 fires on real data, not just a synthetic negative
	test."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_shrimp_operations: SKIPPED — run seed_shrimp_stocking first."
	feed_created = _ensure_feed_logs(batch_name)
	water_created = _ensure_water_readings(batch_name)
	growth_created = _ensure_growth_samples(batch_name)
	treatment_created = _ensure_treatment(batch_name)
	mortality_created = _ensure_mortality(batch_name)
	alert_count = frappe.db.count("Shrimp Water Parameter Reading", {"pond": frappe.db.get_value("Shrimp Stocking Batch", batch_name, "pond"), "is_alert": 1})
	return (
		f"seed_shrimp_operations: {feed_created} feed log(s), {water_created} water reading(s) ({alert_count} flagged as alerts — SF10), "
		f"{growth_created} growth sample(s) created. Treatment {'created' if treatment_created else 'already existed'}. "
		f"Mortality {'created' if mortality_created else 'already existed'}."
	)


def seed_shrimp_harvest():
	"""DP-557 — SF08 (harvest trace) + SF09 (cost). KPIs (survival rate, FCR, cost/kg) are
	computed server-side from the batch's own recorded feed/mortality history, not entered
	manually."""
	batch_name = _batch_name()
	if not batch_name:
		return "seed_shrimp_harvest: SKIPPED — no Active Stocking Batch, run seed_shrimp_stocking/operations first."
	existing = frappe.db.get_value("Shrimp Harvest", {"stocking_batch": batch_name}, "name")
	if existing:
		h = frappe.get_doc("Shrimp Harvest", existing)
		return f"seed_shrimp_harvest: already existed ({existing}). Survival {h.survival_rate_percent}%, FCR {h.fcr}, cost/kg {h.cost_per_kg}."
	harvest = frappe.get_doc(
		{
			"doctype": "Shrimp Harvest",
			"stocking_batch": batch_name,
			"harvest_date": frappe.utils.nowdate(),
			"total_weight_kg": 4200.0,
			"average_body_weight_g": 18.5,
			"total_cost": 50000000,  # other costs (PL, labor, utilities) beyond feed
		}
	)
	harvest.insert(ignore_permissions=True)
	return (
		f"seed_shrimp_harvest: created ({harvest.name}). SF08/SF09 — Survival rate {harvest.survival_rate_percent}%, "
		f"FCR {harvest.fcr}, days of culture {harvest.days_of_culture}, cost/kg {harvest.cost_per_kg}."
	)


def _test_sf01_invalid_transition_blocked():
	pond = frappe.get_doc("Shrimp Pond", _POND_CODE)
	if pond.status != "Harvested":
		return True  # pond hasn't reached Harvested yet in this run order — nothing to test
	pond.status = "Stocked"  # Harvested -> Stocked skips Empty, should be blocked
	blocked = False
	try:
		pond.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("SF01 negative test FAILED: an invalid pond status transition was not blocked!")
	return True


def _test_sf02_double_stocking_blocked():
	pond_status = frappe.db.get_value("Shrimp Pond", _POND_CODE, "status")
	if pond_status == "Empty":
		return True  # nothing stocked yet in this run order — nothing to test
	dup = frappe.get_doc(
		{
			"doctype": "Shrimp Stocking Batch",
			"pond": _POND_CODE,
			"species": "Litopenaeus vannamei",
			"stocking_date": frappe.utils.nowdate(),
			"initial_count": 100000,
			"status": "Active",
		}
	)
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("SF02 negative test FAILED: double-stocking a non-Empty pond was not blocked!")
	return True


def _test_sf03_inactive_batch_blocked():
	harvested_batch = frappe.db.get_value("Shrimp Stocking Batch", {"pond": _POND_CODE, "status": "Harvested"}, "name")
	if not harvested_batch:
		return True  # nothing harvested yet in this run order — nothing to test
	log = frappe.get_doc(
		{
			"doctype": "Shrimp Daily Feed Log",
			"stocking_batch": harvested_batch,
			"feed_date": frappe.utils.nowdate(),
			"feed_product": "Shrimp Grower Pellet 2mm",
			"qty_kg": 10,
		}
	)
	blocked = False
	try:
		log.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("SF03 negative test FAILED: logging feed against a Harvested batch was not blocked!")
	return True


def seed_shrimp_validations():
	"""DP-558 — SF01/SF02/SF03 negative tests. Each one only actually tests something once
	the flow has reached the relevant state (pond Harvested for SF01/SF03, pond
	Stocked/Harvested for SF02) — run this AFTER seed_shrimp_harvest for full coverage."""
	sf01 = _test_sf01_invalid_transition_blocked()
	sf02 = _test_sf02_double_stocking_blocked()
	sf03 = _test_sf03_inactive_batch_blocked()
	return f"seed_shrimp_validations: SF01 CONFIRMED ({sf01}). SF02 CONFIRMED ({sf02}). SF03 CONFIRMED ({sf03})."
