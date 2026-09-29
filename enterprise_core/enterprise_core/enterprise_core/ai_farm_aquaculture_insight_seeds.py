"""Phase 6A — AI-DEMO-09 (Livestock Farm Assistant) + AI-DEMO-10 (Shrimp/Aquaculture Assistant)
seed data + validations. Registers the 8 new `AI Tool` rows this combined item adds to the SAME
registry every prior Phase 6A item built (`explain_fcr_deterioration`, `analyze_mortality_
anomaly`, `identify_barn_requiring_attention`, `analyze_feed_cost`, `analyze_pond_instability`,
`analyze_feed_fcr_trend`, `analyze_water_trend`, `explain_pond_anomaly`), 2 Prompt Template/AI
Action pairs (one per vertical — see `ai_farm_aquaculture_insight.py`'s own module docstring for
why two entry points, not one), and isolated real farm/pond data for both verticals — needed
because BOTH flagship golden demos are structurally unable to show a trend: Golden Demo #11 (Pig
Farm)'s single `BATCH-2026-001` has only one cohort to compare against itself, and its feed-log
data was sized only to prove PF03/PF07 exist, not to be FCR-realistic (an explicit, EMPTY
`Pig Farm`/`pig_validations.py` FCR/mortality threshold hook — confirmed by reading it in full —
means there is also no existing automation this demo's tools could instead be reading); Golden
Demo #8 (Shrimp Farm)'s single `POND-A1` crop cycle is, likewise, one data point with nothing to
trend against.

**Why ISOLATED, AI-DEMO-09/10-owned Pens/Ponds — reusing the flagship items' Pen/Pond CODES would
corrupt existing, already-passing verify functions, exactly this session's own established
lesson (see the isolation rationale AI-DEMO-02/05/06 each documented in their own seed modules,
applied here a fourth/fifth time), re-derived here by actually reading the source first:**
  - `pig_seeds.py`'s own `_batch_name()`/`_test_pf05_withdrawal_sale_blocked()` AND `api.py`'s
    `verify_pig_farm_golden_demo()` all resolve the Grower Batch by filtering on the literal pen
    code `"PEN-G1"` — a second batch ever placed in `PEN-G1` would silently corrupt those lookups.
    New cohorts here use brand-new pen codes (`PEN-AI9-C1/C2/C3`) that no existing lookup can ever
    match, by construction.
  - `shrimp_seeds.py`'s own `_ensure_stocking_batch()`/`_batch_name()` AND `api.py`'s
    `verify_shrimp_golden_demo()` all resolve by the literal pond code `"POND-A1"` — EXCEPT
    `verify_shrimp_golden_demo()`'s own final Harvest check, which has **no pond filter at all**
    (`frappe.db.get_value("Shrimp Harvest", {}, [...], order_by="creation desc")`) and asserts the
    most-recently-created Harvest's FCR falls in a realistic 0.8-2.0 range. New pond codes
    (`POND-AI10-1/2/3`) avoid the pond-keyed collisions, and every one of this module's own new
    Shrimp Harvest FCRs (1.20/1.50/1.90) was deliberately kept inside that SAME 0.8-2.0 range so
    that check keeps passing regardless of which Harvest ends up "most recently created" from here
    on — the exact fix this session's lessons call for, applied proactively instead of found live.
  - Pen/Pond occupancy in both golden demos is a SEQUENTIAL, not permanent, exclusivity lock
    (`pig_grower_batch_validate`/`shrimp_stocking_batch_validate` both only block a SECOND batch
    while the existing one is still occupying that exact code) — so brand-new codes sidestep this
    entirely, by construction, not by convention.

**3 real cohorts per vertical, each isolating a deliberate, deteriorating trend across
chronological "successive batches" (livestock) / "successive crop cycles" (aquaculture) — the
same "isolate the cause, prove genuine discrimination" discipline `ai_manufacturing_insight_
seeds.py`'s own WO-A/B/C/D scenarios established:**
  - Livestock (`PEN-AI9-C1/C2/C3`, oldest->newest): FCR 2.60 -> 3.00 -> 4.20, mortality
    count 1 -> 2 -> 5 (peer-average ratio ~3.3x on the newest cohort), cost/kg-gained rising
    partly from feed price (15,000 -> 15,500 -> 16,000 VND/kg) and partly from declining
    efficiency — the newest cohort ALSO carries a real, linked `Pig Medicine Treatment`
    (respiratory/enteric illness) as the genuine contributing factor `explain_fcr_deterioration()`
    correlates against.
  - Aquaculture (`POND-AI10-1/2/3`, oldest->newest): FCR 1.20 -> 1.50 -> 1.90 (all inside the
    0.8-2.0 sanity range — see isolation note above), survival 96% -> 92.5% -> 80%. Water-quality
    readings: Pond 1 is a stable 6-reading baseline (no SF10 alerts anywhere), Pond 2 drifts
    moderately (still no alerts — proving `analyze_pond_instability()`'s variance signal can
    surface a genuine trend BEFORE any hard threshold is crossed), Pond 3 is an 8-reading series
    that visibly worsens and crosses SF10's real thresholds 5 times near the end (dissolved
    oxygen, ammonia, then nitrite too) — automation (SF10) flags those 5 readings on its own, and
    a real, linked `Shrimp Health Treatment` documents the same period's illness.
"""

import frappe

_LIVESTOCK_ACTION_CODE = "livestock_farm_insight_synthesis"
_AQUACULTURE_ACTION_CODE = "aquaculture_insight_synthesis"

_AI_TOOLS = [
	(
		"explain_fcr_deterioration",
		"Explain FCR Deterioration",
		"Real Pig Grower Batch cohort-over-cohort FCR comparison (feed_kg / weight_gain_kg), flagged against the farm's own trailing average, correlated with any real linked Pig Medicine Treatment (Golden Demo #11 Pig Farm).",
		"enterprise_core.enterprise_core.ai_tools.explain_fcr_deterioration",
		"Pig Grower Batch",
	),
	(
		"analyze_mortality_anomaly",
		"Analyze Mortality Anomaly",
		"Real Pig Mortality Record rate comparison across cohorts, expressed as a ratio against the farm's own peer average — not a fixed absolute threshold (Golden Demo #11 Pig Farm).",
		"enterprise_core.enterprise_core.ai_tools.analyze_mortality_anomaly",
		"Pig Mortality Record",
	),
	(
		"identify_barn_requiring_attention",
		"Identify Barn/Flock Requiring Attention",
		"Real composite ranking across Pig Grower Batch cohorts using FCR, mortality rate, and cost/kg-gained, each expressed relative to the peer average (Golden Demo #11 Pig Farm).",
		"enterprise_core.enterprise_core.ai_tools.identify_barn_requiring_attention",
		"Pig Grower Batch",
	),
	(
		"analyze_feed_cost",
		"Analyze Feed Cost",
		"Real cost-per-kg-gained analysis decomposed into effective feed price and feed-conversion efficiency, from real Pig Feed Log data (Golden Demo #11 Pig Farm).",
		"enterprise_core.enterprise_core.ai_tools.analyze_feed_cost",
		"Pig Feed Log",
	),
	(
		"analyze_pond_instability",
		"Analyze Pond Instability",
		"Real variance/trend analysis across a Shrimp Pond's own Water Parameter Readings, reading (never recomputing) the existing SF10 automation's is_alert flags (Golden Demo #8 Shrimp Farm).",
		"enterprise_core.enterprise_core.ai_tools.analyze_pond_instability",
		"Shrimp Water Parameter Reading",
	),
	(
		"analyze_feed_fcr_trend",
		"Analyze Feed/FCR Trend",
		"Real Shrimp Harvest FCR trend across successive crop cycles, extending AI-DEMO-01's get_worst_fcr_pond() single-snapshot query into a trend-over-time analysis (Golden Demo #8 Shrimp Farm).",
		"enterprise_core.enterprise_core.ai_tools.analyze_feed_fcr_trend",
		"Shrimp Harvest",
	),
	(
		"analyze_water_trend",
		"Analyze Water Trend",
		"Real farm-level water-parameter trend (early vs. recent period) across ponds, plus a real count of SF10-automation-flagged alerts per period (Golden Demo #8 Shrimp Farm).",
		"enterprise_core.enterprise_core.ai_tools.analyze_water_trend",
		"Shrimp Water Parameter Reading",
	),
	(
		"explain_pond_anomaly",
		"Explain Pond Anomaly",
		"Synthesis-grounding tool: bundles one pond's real instability signal with any real linked Shrimp Health Treatment / Mortality Record (Golden Demo #8 Shrimp Farm).",
		"enterprise_core.enterprise_core.ai_tools.explain_pond_anomaly",
		"Shrimp Health Treatment",
	),
]


def _ensure_ai_tools():
	created = []
	for tool_code, label, description, path, permission_doctype in _AI_TOOLS:
		if frappe.db.exists("AI Tool", tool_code):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Tool",
				"tool_code": tool_code,
				"label": label,
				"description": description,
				"python_function_path": path,
				"required_permission_doctype": permission_doctype,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append(tool_code)
	return created


def _ensure_prompt_template_and_action(template_code, action_code, system_instruction, allowed_tools):
	template_created = False
	if not frappe.db.exists("Prompt Template", {"template_code": template_code, "version": 1}):
		frappe.get_doc(
			{
				"doctype": "Prompt Template",
				"template_code": template_code,
				"version": 1,
				"system_instruction": system_instruction,
				"input_schema": frappe.as_json({"question_code": "string", "<tool_code>": "object (tool-specific structured data)"}),
				"output_schema": frappe.as_json({"interpretation": "string"}),
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		template_created = True

	action_created = False
	if not frappe.db.exists("AI Action", action_code):
		frappe.get_doc(
			{
				"doctype": "AI Action",
				"action_code": action_code,
				"description": f"AI-DEMO-09/10 — {action_code}: synthesizes an interpretation over real farm/aquaculture tool output. Read-only: never drafts, never mints or authorizes any record.",
				"required_capabilities": "reasoning",
				"preferred_provider": "anthropic",
				"fallback_policy": "Next Eligible Model",
				"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": template_code, "version": 1}, "name"),
				"allowed_tools": ",".join(allowed_tools),
				"human_review_required": 0,
				"max_cost_usd": 0.05,
				"retention_policy": "Store Full",
			}
		).insert(ignore_permissions=True)
		action_created = True
	return template_created, action_created


# ---------------------------------------------------------------------------
# AI-DEMO-09 — isolated Pig Farm cohorts (see module docstring for the full isolation rationale).
# ---------------------------------------------------------------------------

_PIG_FARM_NAME = "Demo Pig Farm - Dong Nai"  # reuse Golden Demo #11's own Farm — only PEN CODES
# need to be new, see module docstring.
_PIG_BREED_PEN = "PEN-AI9-BREED"
_PIG_SOW_TAG = "SOW-AI9-001"
_PIG_BOAR_TAG = "BOAR-AI9-001"
_PIG_CUSTOMER_NAME = "Dong Nai Meat Processing Co."  # reused as-is from pig_seeds.py — no "at
# most one sale lot per customer" assumption exists anywhere for this to violate.

# (marker, pen, farrow_offset_days, sale_offset_days, w0_kg, w1_kg, feed_entries[(offset,qty)],
#  feed_rate_vnd_per_kg, mortality_offset, mortality_count, mortality_cause, treatment|None,
#  head_count, total_weight_kg, sale_price, other_cost)
_PIG_CYCLES = [
	{
		"marker": "C1",
		"pen": "PEN-AI9-C1",
		"farrow_offset": -265,
		"sale_offset": -180,
		"w0_offset": -250,
		"w0_kg": 9.0,
		"w1_offset": -190,
		"w1_kg": 90.0,
		"feed": [(-245, 600.0), (-220, 700.0), (-195, 783.0)],
		"feed_rate": 15000,
		"mortality_offset": -230,
		"mortality_count": 1,
		"mortality_cause": "Normal pre-market cull-rate loss.",
		"treatment": None,
		"head_count": 10,
		"total_weight_kg": 900.0,
		"sale_price": 61_200_000,
		"other_cost": 1_000_000,
	},
	{
		"marker": "C2",
		"pen": "PEN-AI9-C2",
		"farrow_offset": -175,
		"sale_offset": -90,
		"w0_offset": -160,
		"w0_kg": 9.0,
		"w1_offset": -100,
		"w1_kg": 85.0,
		"feed": [(-155, 550.0), (-130, 650.0), (-105, 800.0)],
		"feed_rate": 15500,
		"mortality_offset": -140,
		"mortality_count": 2,
		"mortality_cause": "Slightly elevated post-weaning losses, no clear cause identified.",
		"treatment": None,
		"head_count": 9,
		"total_weight_kg": 765.0,
		"sale_price": 52_020_000,
		"other_cost": 1_000_000,
	},
	{
		"marker": "C3",
		"pen": "PEN-AI9-C3",
		"farrow_offset": -95,
		"sale_offset": -3,
		"w0_offset": -73,
		"w0_kg": 9.0,
		"w1_offset": -13,
		"w1_kg": 78.0,
		"feed": [(-70, 550.0), (-45, 600.0), (-20, 400.0)],
		"feed_rate": 16000,
		"mortality_offset": -25,
		"mortality_count": 5,
		"mortality_cause": "Respiratory/enteric illness outbreak across the cohort — see linked Medicine Treatment.",
		"treatment": {
			"offset": -23,
			"medicine_name": "Amoxicillin 15% LA",
			"diagnosis": "Respiratory and enteric illness outbreak observed across the cohort — reduced feed efficiency and elevated mortality during this cycle.",
			"withdrawal_days": 10,
			"cost": 900_000,
		},
		"head_count": 6,
		"total_weight_kg": 468.0,
		"sale_price": 31_824_000,
		"other_cost": 1_000_000,
	},
]


def _d(offset):
	return frappe.utils.add_days(frappe.utils.nowdate(), offset)


def _ensure_pig_isolated_breeding_stock():
	created = []
	if not frappe.db.exists("Pig Pen", _PIG_BREED_PEN):
		frappe.get_doc({"doctype": "Pig Pen", "pen_code": _PIG_BREED_PEN, "farm": _PIG_FARM_NAME, "pen_type": "Breeding", "capacity": 10, "status": "Empty"}).insert(ignore_permissions=True)
		created.append(_PIG_BREED_PEN)
	for tag, sex, breed in [(_PIG_SOW_TAG, "Sow", "Landrace"), (_PIG_BOAR_TAG, "Boar", "Pietrain")]:
		if not frappe.db.exists("Pig Breeding Animal", tag):
			frappe.get_doc(
				{
					"doctype": "Pig Breeding Animal",
					"tag_id": tag,
					"sex": sex,
					"breed": breed,
					"birth_date": _d(-600),
					"pen": _PIG_BREED_PEN,
					"status": "Active",
				}
			).insert(ignore_permissions=True)
			created.append(tag)
	for pen in _PIG_CYCLES:
		if not frappe.db.exists("Pig Pen", pen["pen"]):
			frappe.get_doc({"doctype": "Pig Pen", "pen_code": pen["pen"], "farm": _PIG_FARM_NAME, "pen_type": "Nursery", "capacity": 50, "status": "Empty"}).insert(ignore_permissions=True)
			created.append(pen["pen"])
	return created


def _ensure_pig_customer():
	existing = frappe.db.get_value("Customer", {"customer_name": _PIG_CUSTOMER_NAME}, "name")
	if existing:
		return existing
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": _PIG_CUSTOMER_NAME, "customer_type": "Company", "customer_group": "Livestock Buyers"})
	customer.insert(ignore_permissions=True)
	return customer.name


def _ensure_pig_cycle(cycle, customer):
	batch_code = f"BATCH-AI9-{cycle['marker']}"
	if not frappe.db.exists("Pig Grower Batch", batch_code):
		farrow_date = _d(cycle["farrow_offset"])
		service = frappe.get_doc(
			{
				"doctype": "Pig Breeding Service",
				"sow": _PIG_SOW_TAG,
				"boar": _PIG_BOAR_TAG,
				"service_date": frappe.utils.add_days(farrow_date, -114),
				"expected_farrow_date": farrow_date,
				"status": "Confirmed Pregnant",
			}
		)
		service.insert(ignore_permissions=True)

		farrowing = frappe.get_doc(
			{
				"doctype": "Pig Farrowing",
				"breeding_service": service.name,
				"farrowing_date": farrow_date,
				"born_alive": 12,
				"born_dead": 1,
			}
		)
		farrowing.insert(ignore_permissions=True)  # on_update flips the Breeding Service to "Farrowed"

		batch = frappe.get_doc(
			{
				"doctype": "Pig Grower Batch",
				"batch_code": batch_code,
				"farrowing": farrowing.name,
				"pen": cycle["pen"],
				"stage": "Nursery",
				"weaning_date": frappe.utils.add_days(farrow_date, 21),
				"initial_count": 11,  # born_alive(12) - 1 pre-wean loss, same convention as the flagship
				"status": "Active",
			}
		)
		batch.insert(ignore_permissions=True)  # on_update occupies the pen

	for offset, qty in cycle["feed"]:
		feed_date = _d(offset)
		if frappe.db.exists("Pig Feed Log", {"batch": batch_code, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{"doctype": "Pig Feed Log", "batch": batch_code, "feed_date": feed_date, "feed_product": "Pig Grower Pellet", "qty_kg": qty, "cost": qty * cycle["feed_rate"]}
		).insert(ignore_permissions=True)

	for offset, weight in [(cycle["w0_offset"], cycle["w0_kg"]), (cycle["w1_offset"], cycle["w1_kg"])]:
		record_date = _d(offset)
		if frappe.db.exists("Pig Weight Record", {"batch": batch_code, "record_date": record_date}):
			continue
		frappe.get_doc({"doctype": "Pig Weight Record", "batch": batch_code, "record_date": record_date, "average_weight_kg": weight, "sample_count": cycle["head_count"] + cycle["mortality_count"]}).insert(
			ignore_permissions=True
		)

	if not frappe.db.exists("Pig Mortality Record", {"batch": batch_code}):
		frappe.get_doc(
			{
				"doctype": "Pig Mortality Record",
				"batch": batch_code,
				"record_date": _d(cycle["mortality_offset"]),
				"mortality_count": cycle["mortality_count"],
				"cause": cycle["mortality_cause"],
			}
		).insert(ignore_permissions=True)

	if cycle["treatment"] and not frappe.db.exists("Pig Medicine Treatment", {"batch": batch_code}):
		t = cycle["treatment"]
		frappe.get_doc(
			{
				"doctype": "Pig Medicine Treatment",
				"batch": batch_code,
				"treatment_date": _d(t["offset"]),
				"medicine_name": t["medicine_name"],
				"diagnosis": t["diagnosis"],
				"withdrawal_days": t["withdrawal_days"],
				"cost": t["cost"],
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Pig Sale Lot", {"batch": batch_code}):
		frappe.get_doc(
			{
				"doctype": "Pig Sale Lot",
				"batch": batch_code,
				"sale_date": _d(cycle["sale_offset"]),
				"customer": customer,
				"head_count": cycle["head_count"],
				"total_weight_kg": cycle["total_weight_kg"],
				"sale_price": cycle["sale_price"],
				"other_cost": cycle["other_cost"],
			}
		).insert(ignore_permissions=True)
		return True
	return False


def _seed_ai_livestock_insight():
	if not frappe.db.exists("Pig Grower Batch", "BATCH-2026-001"):
		return "livestock: SKIPPED — Golden Demo #11 (Pig Farm)'s own flagship Grower Batch not found. Run Pig Farm's full seed chain first."
	master_created = _ensure_pig_isolated_breeding_stock()
	customer = _ensure_pig_customer()
	cycles_created = [f"BATCH-AI9-{c['marker']}" for c in _PIG_CYCLES if _ensure_pig_cycle(c, customer)]
	return f"livestock: isolated master data created: {master_created or 'none (already existed)'}. Cycles newly created: {cycles_created or 'none (already existed)'}."


# ---------------------------------------------------------------------------
# AI-DEMO-10 — isolated Shrimp Farm ponds (see module docstring for the full isolation rationale).
# ---------------------------------------------------------------------------

_SHRIMP_FARM_NAME = "Demo Shrimp Farm — Bac Lieu"  # reuse Golden Demo #8's own Farm — only POND
# CODES need to be new, see module docstring.

_SHRIMP_CYCLES = [
	{
		"marker": "1",
		"pond": "POND-AI10-1",
		"stocking_offset": -260,
		"harvest_offset": -160,
		"initial_count": 150000,
		"mortality_offset": -210,
		"mortality_count": 6000,
		"mortality_cause": "Normal background mortality, no specific cause identified.",
		"abw_g": 18.0,
		"total_weight_kg": 2592.0,
		"feed": [(-245, 900.0), (-220, 1050.0), (-200, 1160.0)],
		"feed_rate": 28000,
		"growth": [(-230, 10.0), (-180, 15.5)],
		"other_cost": 25_000_000,
		"treatment": None,
		"water_offsets": [-250, -230, -210, -190, -170, -162],
		"water": {
			"do_mg_l": [5.2, 5.3, 5.1, 5.4, 5.0, 5.2],
			"ph": [7.9, 8.0, 8.0, 7.9, 8.1, 8.0],
			"temperature_c": [28.0, 28.2, 28.5, 28.3, 28.6, 28.4],
			"salinity_ppt": [15.0] * 6,
			"alkalinity": [120] * 6,
			"nh3_mg_l": [0.02, 0.02, 0.03, 0.02, 0.03, 0.02],
			"no2_mg_l": [0.04, 0.05, 0.04, 0.05, 0.04, 0.05],
		},
	},
	{
		"marker": "2",
		"pond": "POND-AI10-2",
		"stocking_offset": -170,
		"harvest_offset": -70,
		"initial_count": 150000,
		"mortality_offset": -120,
		"mortality_count": 11250,
		"mortality_cause": "Slightly elevated mortality — mild stress suspected, no treatment required.",
		"abw_g": 18.0,
		"total_weight_kg": 2497.5,
		"feed": [(-155, 1100.0), (-130, 1250.0), (-110, 1396.0)],
		"feed_rate": 28000,
		"growth": [(-140, 9.8), (-90, 14.8)],
		"other_cost": 25_000_000,
		"treatment": None,
		"water_offsets": [-160, -140, -120, -100, -80, -72],
		"water": {
			"do_mg_l": [5.0, 4.8, 4.6, 4.5, 4.3, 4.2],
			"ph": [7.9, 8.0, 8.1, 8.2, 8.1, 8.3],
			"temperature_c": [28.5, 29.0, 29.2, 29.5, 29.3, 29.6],
			"salinity_ppt": [15.0] * 6,
			"alkalinity": [118] * 6,
			"nh3_mg_l": [0.03, 0.04, 0.05, 0.06, 0.07, 0.08],
			"no2_mg_l": [0.05, 0.06, 0.07, 0.08, 0.09, 0.10],
		},
	},
	{
		"marker": "3",
		"pond": "POND-AI10-3",
		"stocking_offset": -90,
		"harvest_offset": -5,
		"initial_count": 150000,
		"mortality_offset": -25,
		"mortality_count": 30000,
		"mortality_cause": "Elevated mortality coinciding with declining water quality (rising ammonia, unstable dissolved oxygen) — see linked Health Treatment.",
		"abw_g": 17.0,
		"total_weight_kg": 2040.0,
		"feed": [(-80, 1450.0), (-55, 1550.0), (-30, 876.0)],
		"feed_rate": 28000,
		"growth": [(-60, 9.5), (-15, 13.2)],
		"other_cost": 25_000_000,
		"treatment": {
			"offset": -30,
			"diagnosis": "Vibriosis suspected amid deteriorating water quality (rising ammonia, dissolved-oxygen instability) — reduced feeding activity observed.",
			"treatment_applied": "Probiotic water treatment + emergency water exchange.",
			"dosage": "10 ppm probiotic, applied daily x5; 30% water exchange.",
		},
		"water_offsets": [-85, -70, -55, -40, -25, -15, -8, -6],
		"water": {
			"do_mg_l": [5.0, 4.7, 4.3, 3.9, 4.5, 3.6, 3.2, 3.8],
			"ph": [7.9, 8.0, 8.1, 8.0, 8.2, 8.1, 8.0, 7.9],
			"temperature_c": [28.5, 29.0, 29.5, 30.0, 30.5, 31.0, 31.2, 31.5],
			"salinity_ppt": [15.0] * 8,
			"alkalinity": [115] * 8,
			"nh3_mg_l": [0.03, 0.05, 0.07, 0.09, 0.11, 0.12, 0.14, 0.15],
			"no2_mg_l": [0.05, 0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.22],
		},
	},
]


def _ensure_shrimp_pond(pond_code):
	if frappe.db.exists("Shrimp Pond", pond_code):
		return False
	frappe.get_doc({"doctype": "Shrimp Pond", "pond_code": pond_code, "farm": _SHRIMP_FARM_NAME, "area_m2": 1800, "status": "Empty"}).insert(ignore_permissions=True)
	return True


def _ensure_shrimp_cycle(cycle):
	pond = cycle["pond"]
	created_pond = _ensure_shrimp_pond(pond)

	batch = frappe.db.get_value("Shrimp Stocking Batch", {"pond": pond}, "name")
	if not batch:
		doc = frappe.get_doc(
			{
				"doctype": "Shrimp Stocking Batch",
				"pond": pond,
				"species": "Litopenaeus vannamei (Whiteleg shrimp)",
				"stocking_date": _d(cycle["stocking_offset"]),
				"initial_count": cycle["initial_count"],
				"source_hatchery": "CP Vietnam Hatchery",
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)  # on_update marks the pond Stocked
		batch = doc.name

	for offset, qty in cycle["feed"]:
		feed_date = _d(offset)
		if frappe.db.exists("Shrimp Daily Feed Log", {"stocking_batch": batch, "feed_date": feed_date}):
			continue
		frappe.get_doc(
			{"doctype": "Shrimp Daily Feed Log", "stocking_batch": batch, "feed_date": feed_date, "feed_product": "Shrimp Grower Pellet 2mm", "qty_kg": qty, "cost": qty * cycle["feed_rate"]}
		).insert(ignore_permissions=True)

	for i, offset in enumerate(cycle["water_offsets"]):
		reading_dt = f"{_d(offset)} 08:00:00"
		if frappe.db.exists("Shrimp Water Parameter Reading", {"pond": pond, "reading_datetime": reading_dt}):
			continue
		params = {field: values[i] for field, values in cycle["water"].items()}
		frappe.get_doc({"doctype": "Shrimp Water Parameter Reading", "pond": pond, "reading_datetime": reading_dt, **params}).insert(ignore_permissions=True)

	for offset, abw in cycle["growth"]:
		sample_date = _d(offset)
		if frappe.db.exists("Shrimp Growth Sample", {"stocking_batch": batch, "sample_date": sample_date}):
			continue
		frappe.get_doc({"doctype": "Shrimp Growth Sample", "stocking_batch": batch, "sample_date": sample_date, "average_body_weight_g": abw, "sample_count": 100}).insert(ignore_permissions=True)

	if not frappe.db.exists("Shrimp Mortality Record", {"stocking_batch": batch}):
		frappe.get_doc(
			{
				"doctype": "Shrimp Mortality Record",
				"stocking_batch": batch,
				"record_date": _d(cycle["mortality_offset"]),
				"mortality_count": cycle["mortality_count"],
				"cause": cycle["mortality_cause"],
			}
		).insert(ignore_permissions=True)

	if cycle["treatment"] and not frappe.db.exists("Shrimp Health Treatment", {"stocking_batch": batch}):
		t = cycle["treatment"]
		frappe.get_doc(
			{
				"doctype": "Shrimp Health Treatment",
				"stocking_batch": batch,
				"issue_date": _d(t["offset"]),
				"diagnosis": t["diagnosis"],
				"treatment_applied": t["treatment_applied"],
				"dosage": t["dosage"],
			}
		).insert(ignore_permissions=True)

	harvest_created = False
	if not frappe.db.exists("Shrimp Harvest", {"stocking_batch": batch}):
		frappe.get_doc(
			{
				"doctype": "Shrimp Harvest",
				"stocking_batch": batch,
				"harvest_date": _d(cycle["harvest_offset"]),
				"total_weight_kg": cycle["total_weight_kg"],
				"average_body_weight_g": cycle["abw_g"],
				"total_cost": cycle["other_cost"],
			}
		).insert(ignore_permissions=True)  # on_update marks the batch + pond Harvested
		harvest_created = True

	return created_pond, harvest_created


def _seed_ai_aquaculture_insight():
	if not frappe.db.exists("Shrimp Pond", "POND-A1"):
		return "aquaculture: SKIPPED — Golden Demo #8 (Shrimp Farm)'s own flagship Pond not found. Run Shrimp Farm's full seed chain first."
	ponds_created, harvests_created = [], []
	for cycle in _SHRIMP_CYCLES:
		pond_created, harvest_created = _ensure_shrimp_cycle(cycle)
		if pond_created:
			ponds_created.append(cycle["pond"])
		if harvest_created:
			harvests_created.append(cycle["pond"])
	return f"aquaculture: ponds newly created: {ponds_created or 'none (already existed)'}. Harvests newly created: {harvests_created or 'none (already existed)'}."


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_LIVESTOCK_SYSTEM_INSTRUCTION = (
	"You are a livestock farm operations insight assistant answering one of 4 approved analytical questions "
	"(explain FCR deterioration, analyze mortality anomaly, identify the barn/flock requiring attention, "
	"analyze feed cost). You are given REAL, tool-sourced structured farm data as context — never invent "
	"facts, never fetch additional data yourself, never run or suggest SQL. Every comparison in the provided "
	"data is RELATIVE to the farm's own historical/peer average, never a fixed absolute threshold — hard "
	"thresholds are automation's job, not yours; your job is interpretation of real relative deviations and "
	"trends. Produce a concise interpretation grounded ONLY in the provided data. You never decide or "
	"authorize anything — a flagged deterioration, anomaly, or cost trend is always for a human to act on."
)

_AQUACULTURE_SYSTEM_INSTRUCTION = (
	"You are a shrimp/aquaculture pond insight assistant answering one of 4 approved analytical questions "
	"(pond instability analysis, feed/FCR trend, water trend analysis, anomaly explanation). You are given "
	"REAL, tool-sourced structured pond data as context — never invent facts, never fetch additional data "
	"yourself, never run or suggest SQL. Some of the provided data (is_alert / alert_message) was already "
	"flagged by the golden demo's own deterministic water-quality automation (SF10) — treat those as REAL, "
	"already-decided facts, never re-derive or contradict them; your job is to interpret trends and variance "
	"across ALL readings, including ones that never crossed that hard threshold. Produce a concise "
	"interpretation grounded ONLY in the provided data. You never decide or authorize anything."
)


def seed_ai_farm_aquaculture_insight():
	"""Phase 6A / AI-DEMO-09 (Livestock Farm Assistant) + AI-DEMO-10 (Shrimp/Aquaculture
	Assistant) — registers the 8 new AI Tools, the 2 Prompt Template/AI Action pairs (reusing the
	existing, unmodified CE-13 AI foundation router/policy/logging), and the isolated real cohort/
	pond data for both verticals. Idempotent: safe to re-run any number of times. Self-skips
	(never touches either flagship golden demo's own Pen/Pond/Batch — see module docstring) if
	that vertical's flagship data isn't already present."""
	tools_created = _ensure_ai_tools()
	livestock_template_created, livestock_action_created = _ensure_prompt_template_and_action(
		_LIVESTOCK_ACTION_CODE,
		_LIVESTOCK_ACTION_CODE,
		_LIVESTOCK_SYSTEM_INSTRUCTION,
		["explain_fcr_deterioration", "analyze_mortality_anomaly", "identify_barn_requiring_attention", "analyze_feed_cost"],
	)
	aquaculture_template_created, aquaculture_action_created = _ensure_prompt_template_and_action(
		_AQUACULTURE_ACTION_CODE,
		_AQUACULTURE_ACTION_CODE,
		_AQUACULTURE_SYSTEM_INSTRUCTION,
		["analyze_pond_instability", "analyze_feed_fcr_trend", "analyze_water_trend", "explain_pond_anomaly"],
	)
	livestock_result = _seed_ai_livestock_insight()
	aquaculture_result = _seed_ai_aquaculture_insight()

	return (
		f"seed_ai_farm_aquaculture_insight: AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Livestock Prompt Template {'created' if livestock_template_created else 'already existed'}, AI Action {'created' if livestock_action_created else 'already existed'}. "
		f"Aquaculture Prompt Template {'created' if aquaculture_template_created else 'already existed'}, AI Action {'created' if aquaculture_action_created else 'already existed'}. "
		f"{livestock_result} {aquaculture_result}"
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------


def _test_all_livestock_questions_answer():
	from enterprise_core.enterprise_core.ai_farm_aquaculture_insight import LIVESTOCK_QUESTION_TOOL_MAP, ask_livestock_insight

	results = {}
	for question_code, expected_tools in LIVESTOCK_QUESTION_TOOL_MAP.items():
		resp = ask_livestock_insight(question_code, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-09 smoke test FAILED for '{question_code}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "data_facts" not in resp or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-09 smoke test FAILED for '{question_code}': data_facts missing tool output.")
		if not resp.get("ai_interpretation"):
			frappe.throw(f"AI-DEMO-09 smoke test FAILED for '{question_code}': no ai_interpretation returned.")
		if "ai_suggestion" in resp:
			frappe.throw(f"AI-DEMO-09 smoke test FAILED for '{question_code}': response unexpectedly contains an ai_suggestion/draft field — this demo is documented as NO-DRAFT.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-09 smoke test FAILED for '{question_code}': no AI Job Log entry written.")
		results[question_code] = resp
	return results


def _test_all_aquaculture_questions_answer():
	from enterprise_core.enterprise_core.ai_farm_aquaculture_insight import AQUACULTURE_QUESTION_TOOL_MAP, ask_aquaculture_insight

	results = {}
	for question_code, expected_tools in AQUACULTURE_QUESTION_TOOL_MAP.items():
		params = {"pond": "POND-AI10-3"} if question_code == "pond_anomaly_explanation" else {}
		resp = ask_aquaculture_insight(question_code, user="Administrator", **params)
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-10 smoke test FAILED for '{question_code}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "data_facts" not in resp or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-10 smoke test FAILED for '{question_code}': data_facts missing tool output.")
		if not resp.get("ai_interpretation"):
			frappe.throw(f"AI-DEMO-10 smoke test FAILED for '{question_code}': no ai_interpretation returned.")
		if "ai_suggestion" in resp:
			frappe.throw(f"AI-DEMO-10 smoke test FAILED for '{question_code}': response unexpectedly contains an ai_suggestion/draft field — this demo is documented as NO-DRAFT.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-10 smoke test FAILED for '{question_code}': no AI Job Log entry written.")
		results[question_code] = resp
	return results


def _test_fcr_deterioration_discrimination(resp):
	facts = resp["data_facts"]["explain_fcr_deterioration"]
	by_pen = {c["pen"]: c for c in facts["cohorts_chronological"]}
	c1, c2, c3 = by_pen.get("PEN-AI9-C1"), by_pen.get("PEN-AI9-C2"), by_pen.get("PEN-AI9-C3")
	if not (c1 and c2 and c3):
		frappe.throw(f"AI-DEMO-09 FCR test FAILED: not all 3 cohorts present. Got: {sorted(by_pen)}")
	if c1["flagged_deteriorated"] or c2["flagged_deteriorated"]:
		frappe.throw(f"AI-DEMO-09 FCR test FAILED: an early/normal-variance cohort was incorrectly flagged. c1={c1}, c2={c2}")
	if not c3["flagged_deteriorated"]:
		frappe.throw(f"AI-DEMO-09 FCR test FAILED: the genuinely deteriorated cohort (C3) was NOT flagged. Got: {c3}")
	if not any("Medicine Treatment" in f for f in c3["contributing_factors"]):
		frappe.throw(f"AI-DEMO-09 FCR test FAILED: C3's contributing_factors did not cite the real linked Medicine Treatment. Got: {c3['contributing_factors']}")
	return f"FCR-deterioration CONFIRMED: C1 FCR={c1['fcr']}, C2 FCR={c2['fcr']} (neither flagged), C3 FCR={c3['fcr']} correctly flagged with a real linked Medicine Treatment cited."


def _test_mortality_anomaly_discrimination(resp):
	facts = resp["data_facts"]["analyze_mortality_anomaly"]
	by_pen = {c["pen"]: c for c in facts["cohorts"]}
	c3 = by_pen.get("PEN-AI9-C3")
	if not c3 or not c3["anomalous"]:
		frappe.throw(f"AI-DEMO-09 mortality test FAILED: PEN-AI9-C3 not flagged anomalous. Got: {c3}")
	if c3["ratio_vs_peer_average"] < 2.0:
		frappe.throw(f"AI-DEMO-09 mortality test FAILED: PEN-AI9-C3's ratio_vs_peer_average={c3['ratio_vs_peer_average']} is not a genuine multiple of the peer average.")
	c1 = by_pen.get("PEN-AI9-C1")
	if c1 and c1["anomalous"]:
		frappe.throw(f"AI-DEMO-09 mortality test FAILED: PEN-AI9-C1 (baseline) incorrectly flagged anomalous. Got: {c1}")
	return f"mortality-anomaly CONFIRMED: PEN-AI9-C3's mortality is {c3['ratio_vs_peer_average']}x the farm's own peer average (flagged); PEN-AI9-C1 correctly not flagged."


def _test_barn_ranking(resp):
	facts = resp["data_facts"]["identify_barn_requiring_attention"]
	ranked = facts["ranked_cohorts"]
	if len(ranked) < 3:
		frappe.throw(f"AI-DEMO-09 ranking test FAILED: expected 3 ranked cohorts, got {len(ranked)}.")
	if ranked[0]["pen"] != "PEN-AI9-C3":
		frappe.throw(f"AI-DEMO-09 ranking test FAILED: PEN-AI9-C3 should rank #1 (most requiring attention). Got order: {[r['pen'] for r in ranked]}")
	return f"barn-ranking CONFIRMED: {[r['pen'] for r in ranked]} — PEN-AI9-C3 correctly ranked #1 (attention_score={ranked[0]['attention_score']})."


def _test_feed_cost_decomposition(resp):
	facts = resp["data_facts"]["analyze_feed_cost"]
	cohorts = facts["cohorts_chronological"]
	if len(cohorts) < 3:
		frappe.throw(f"AI-DEMO-09 feed-cost test FAILED: expected 3 cohorts, got {len(cohorts)}.")
	if not (cohorts[0]["cost_per_kg_gained"] < cohorts[1]["cost_per_kg_gained"] < cohorts[2]["cost_per_kg_gained"]):
		frappe.throw(f"AI-DEMO-09 feed-cost test FAILED: cost_per_kg_gained is not monotonically increasing across cohorts. Got: {[c['cost_per_kg_gained'] for c in cohorts]}")
	if not facts.get("price_vs_efficiency_decomposition"):
		frappe.throw("AI-DEMO-09 feed-cost test FAILED: no price_vs_efficiency_decomposition narrative returned.")
	return f"feed-cost CONFIRMED: cost/kg-gained rises monotonically {[c['cost_per_kg_gained'] for c in cohorts]}, decomposed into price + efficiency drivers."


def seed_ai_livestock_insight_validations():
	smoke = _test_all_livestock_questions_answer()
	fcr = _test_fcr_deterioration_discrimination(smoke["fcr_deterioration"])
	mortality = _test_mortality_anomaly_discrimination(smoke["mortality_anomaly"])
	ranking = _test_barn_ranking(smoke["barn_requiring_attention"])
	cost = _test_feed_cost_decomposition(smoke["feed_cost_analysis"])
	return f"seed_ai_livestock_insight_validations: all {len(smoke)} questions answered, no ai_suggestion/draft field present (NO-DRAFT confirmed). {fcr} {mortality} {ranking} {cost}"


def _test_pond_instability_discrimination(resp):
	facts = resp["data_facts"]["analyze_pond_instability"]
	by_pond = {r["pond"]: r for r in facts["results"]}
	p1, p3 = by_pond.get("POND-AI10-1"), by_pond.get("POND-AI10-3")
	if not p1 or not p3:
		frappe.throw(f"AI-DEMO-10 instability test FAILED: not all ponds present. Got: {sorted(by_pond)}")
	if p1["alert_reading_count"] != 0:
		frappe.throw(f"AI-DEMO-10 instability test FAILED: baseline POND-AI10-1 should have 0 SF10 alerts. Got: {p1['alert_reading_count']}")
	if p3["alert_reading_count"] < 3:
		frappe.throw(f"AI-DEMO-10 instability test FAILED: POND-AI10-3 should have several real SF10 alerts. Got: {p3['alert_reading_count']}")
	if p3["per_parameter_variance"]["do_mg_l"]["trend_direction"] != "falling":
		frappe.throw(f"AI-DEMO-10 instability test FAILED: POND-AI10-3's dissolved-oxygen trend should be falling. Got: {p3['per_parameter_variance']['do_mg_l']}")
	return f"pond-instability CONFIRMED: POND-AI10-1 has 0 automation-flagged alerts (stable baseline); POND-AI10-3 has {p3['alert_reading_count']} real SF10 alerts and a falling DO trend."


def _test_feed_fcr_trend_discrimination(resp):
	facts = resp["data_facts"]["analyze_feed_fcr_trend"]
	trend = facts["trend_chronological"]
	if len(trend) < 3:
		frappe.throw(f"AI-DEMO-10 FCR-trend test FAILED: expected 3 harvests, got {len(trend)}.")
	fcrs = [t["fcr"] for t in trend]
	if not all(0.8 <= f <= 2.0 for f in fcrs):
		frappe.throw(f"AI-DEMO-10 FCR-trend test FAILED: an FCR fell outside the realistic 0.8-2.0 sanity range (would corrupt verify_shrimp_golden_demo()). Got: {fcrs}")
	if trend[-1]["fcr"] <= trend[0]["fcr"]:
		frappe.throw(f"AI-DEMO-10 FCR-trend test FAILED: FCR did not deteriorate across the trend. Got: {fcrs}")
	if not trend[-1]["flagged_deteriorated"]:
		frappe.throw(f"AI-DEMO-10 FCR-trend test FAILED: the most recent harvest should be flagged deteriorated. Got: {trend[-1]}")
	return f"feed-FCR-trend CONFIRMED: FCR trend {fcrs} (all within the realistic sanity range), most recent cycle correctly flagged deteriorated."


def _test_water_trend(resp):
	facts = resp["data_facts"]["analyze_water_trend"]
	do_trend = facts["per_parameter_trend"].get("do_mg_l")
	alerts = facts["automation_flagged_alerts"]
	if not do_trend or do_trend["trend_direction"] != "falling":
		frappe.throw(f"AI-DEMO-10 water-trend test FAILED: farm-level dissolved-oxygen trend should be falling. Got: {do_trend}")
	if not (alerts["recent_period"] > alerts["early_period"]):
		frappe.throw(f"AI-DEMO-10 water-trend test FAILED: recent-period automation-flagged alerts should exceed early-period. Got: {alerts}")
	return f"water-trend CONFIRMED: farm-level DO trend falling, automation-flagged alerts rose from {alerts['early_period']} (early) to {alerts['recent_period']} (recent)."


def _test_pond_anomaly_explanation(resp):
	facts = resp["data_facts"]["explain_pond_anomaly"]
	if facts.get("pond") != "POND-AI10-3":
		frappe.throw(f"AI-DEMO-10 anomaly-explanation test FAILED: expected POND-AI10-3. Got: {facts.get('pond')}")
	if not facts.get("linked_health_treatments"):
		frappe.throw("AI-DEMO-10 anomaly-explanation test FAILED: no real linked Shrimp Health Treatment found for POND-AI10-3.")
	if not facts.get("instability_signal") or facts["instability_signal"].get("alert_reading_count", 0) < 1:
		frappe.throw(f"AI-DEMO-10 anomaly-explanation test FAILED: instability_signal missing or has no automation-flagged alerts. Got: {facts.get('instability_signal')}")
	return "pond-anomaly-explanation CONFIRMED: grounded in a real instability signal AND a real linked Shrimp Health Treatment."


def seed_ai_aquaculture_insight_validations():
	smoke = _test_all_aquaculture_questions_answer()
	instability = _test_pond_instability_discrimination(smoke["pond_instability"])
	fcr_trend = _test_feed_fcr_trend_discrimination(smoke["feed_fcr_trend"])
	water_trend = _test_water_trend(smoke["water_trend"])
	anomaly = _test_pond_anomaly_explanation(smoke["pond_anomaly_explanation"])
	return f"seed_ai_aquaculture_insight_validations: all {len(smoke)} questions answered, no ai_suggestion/draft field present (NO-DRAFT confirmed). {instability} {fcr_trend} {water_trend} {anomaly}"


def seed_ai_farm_aquaculture_insight_validations():
	"""Runs both verticals' full validation suites end to end."""
	livestock = seed_ai_livestock_insight_validations()
	aquaculture = seed_ai_aquaculture_insight_validations()
	return f"{livestock} | {aquaculture}"
