"""Phase 6A — AI-DEMO-05 (Manufacturing Insight) seed data + validations. Registers the 4 new
`AI Tool` rows this demo adds to the SAME registry AI-DEMO-01/02/03 built (`explain_production_
delay`, `analyze_yield_anomalies`, `check_batch_record_completeness`, `summarize_downtime`), the
`manufacturing_insight_synthesis` Prompt Template/AI Action, and a small set of REAL additional
Work Order / Batch / Premix Weighing Verification data under Golden Demo #26 (Premix)'s own
"Demo Premix Co." company — needed because the flagship `PREMIX-BROILER-2PCT` batch is a SINGLE
batch with essentially zero planned-vs-actual timing variance and 100% yield, giving these 4
analytical tools nothing genuine to compare against.

**Why an ISOLATED, AI-DEMO-05-owned FG item (`PREMIX-BROILER-2PCT-AI5`), not more Work Orders
for the flagship `PREMIX-BROILER-2PCT` item itself** — this is a direct application of this
session's own AI-DEMO-02 "Warehouse C isolation" lesson, re-derived by actually reading the code
first rather than assumed: `premix_seeds.py`'s own `_ensure_work_order()` does
`frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1})` (an "at most
one" existence check with no explicit ordering) and `_finished_batch()`/`api.py`'s
`verify_premix_golden_demo()` do `frappe.db.get_value("Batch", {"item": _FG_ITEM}, "name",
order_by="creation desc")` (picks the MOST RECENTLY CREATED batch). Adding more submitted Work
Orders / batches for the REAL `PREMIX-BROILER-2PCT` item would make `verify_premix_golden_demo()`
non-deterministically (or, for the batch lookup, DETERMINISTICALLY WRONGLY — always picking up
whichever of THIS demo's new batches was created last) pick up an AI-DEMO-05 batch instead of the
golden demo's own real, fully-QC'd/released flagship one — silently corrupting an existing,
already-passing golden demo's verification exactly the way an unscoped write once threatened to
for QMS Copilot's own CAPA lookup. A brand-new item sidesteps this completely: every one of those
lookups filters on the EXACT literal `"PREMIX-BROILER-2PCT"` string, which a differently-named
item can never match, so `PREMIX-BROILER-2PCT-AI5`'s Work Orders/batches are invisible to every
one of Premix's own existing checks by construction, not by convention. The new item reuses the
SAME company, SAME warehouses, SAME 6-ingredient recipe/ratios/mixing sequence, and the SAME
already-flagged critical/micro ingredients (`SELENIUM-PREMIX` etc. — Item-level flags, not
item-specific, so PM01/PM02/PM03 fire on it exactly as they do on the real flagship item) — this
is still real Premix GMP business logic being exercised for real, just on an AI-DEMO-05-owned
parallel production line, exactly mirroring how AI-DEMO-02 introduced its own isolated
"Warehouse C" deviation without pretending it was original golden-demo data.

This module deliberately does NOT call any of `premix_seeds.py`'s Work-Order-related functions
(`seed_premix_weighing_verification`, `seed_premix_sequencing`, `seed_premix_micro_tolerance`,
`seed_premix_manufacturing`) even defensively — re-invoking them AFTER this module's own extra
Work Orders exist would be exactly the risk described above (Premix's own `_ensure_work_order()`
could pick up one of THIS demo's Work Orders instead of the flagship one). It only calls
`seed_premix_master_data()` defensively (Company/Items/Formula — no Work-Order ambiguity there)
and otherwise self-skips with a clear message if the flagship batch/Work Order isn't already
present, exactly the existing `SKIPPED — run seed_X first` idiom every other seed module uses.

**4 scenarios, each isolating ONE tool's positive test case from the others** (same "isolate the
cause" discipline `premix_seeds.py`'s own PM01/PM02/PM03 negative tests use):
  - `WO-A-ONTIME`      — on-time, 100% yield. The "everything normal" baseline/negative control.
  - `WO-B-DELAYED`     — planned to finish 5 days ago, actually finishes today (~5 days late);
                          100% yield (isolates the delay tool from the yield tool). Its critical
                          ingredient's four-eyes verification (`Premix Weighing Verification`,
                          PM02) is deliberately signed off (`verified_on`) only 1 day before
                          completion — a REAL, directly-recorded contributing factor
                          `explain_production_delay()` can correlate against.
  - `WO-C-YIELD-ANOMALY`      — on-time (isolates the yield tool from the delay tool); FG output
                          declared at 430kg against a 500kg Work Order (86% yield, full BOM-scale
                          raw-material consumption still occurs — a real mass-balance yield-loss
                          scenario, not a fabricated number) — beyond `analyze_yield_anomalies()`'s
                          default 5% threshold, the positive test case.
  - `WO-D-YIELD-NORMAL-VARIANCE` — on-time; FG output declared at 480kg (96% yield, 4% deviation)
                          — WITHIN the default 5% threshold, proving the tool can tell ordinary
                          variance apart from a genuine anomaly, not just detect "any shortfall".

Plus one standalone, deliberately-incomplete `Batch` (no Work Order, no Quality Inspection at
all) as `check_batch_record_completeness()`'s positive test case — see that tool's own docstring
in `ai_tools.py` for why a standalone Batch (not a 5th Work Order scenario) is the right fixture
for THIS use case specifically.
"""

import frappe

from enterprise_core.enterprise_core.ai_manufacturing_insight import QUESTION_TOOL_MAP, ask_manufacturing_insight
from enterprise_core.enterprise_core.premix_seeds import seed_premix_master_data

_COMPANY_NAME = "Demo Premix Co."
_RM_WAREHOUSE = "RM Store - DPX"
_FG_QUARANTINE = "FG Quarantine - DPX"

# AI-DEMO-05-owned FG item — see module docstring for why this is NOT the real flagship
# PREMIX-BROILER-2PCT item.
_FG_ITEM = "PREMIX-BROILER-2PCT-AI5"
_BATCH_QTY = 500  # kg — same batch size as the real flagship Premix batch

# Same recipe as premix_seeds.py's own _FORMULA_V1 (carrier first, minerals next, vitamins last,
# real GMP mixing-order rationale — see that module's own comment): (item_code, qty at 500kg
# batch, mixing sequence_no). Reuses the SAME raw-material Items Golden Demo #26 already created
# (RICE-HULL/MINERAL-MIX/SELENIUM-PREMIX/VIT-D3/VIT-A-ACETATE/VIT-E) — their is_micro_ingredient/
# requires_second_check flags are Item-level, not tied to which FG item consumes them.
_FORMULA_V1 = [
	("RICE-HULL", 469, 1),
	("MINERAL-MIX", 15, 2),
	("SELENIUM-PREMIX", 0.05, 3),
	("VIT-D3", 3, 4),
	("VIT-A-ACETATE", 5, 5),
	("VIT-E", 7.95, 6),
]
_CRITICAL_ITEM = "SELENIUM-PREMIX"
_CRITICAL_TARGET_QTY = 0.05

# Extra RM stock this module tops up — 4 additional full-scale (500kg-equivalent) manufacture
# runs' worth of raw material, on top of whatever premix_seeds.py's own _ensure_rm_stock()
# already received (which itself has almost no buffer — barely enough for ONE batch). A
# distinguishing exact-qty marker (4x the per-batch formula qty) is the existence guard, mirroring
# premix_seeds.py's own "guard on Stock Entry Detail existence, not balance" idiom (Lesson 3),
# scoped to a qty value ONLY this module's own top-up would ever create.
_RM_TOPUP_MULTIPLIER = 4
_RM_TOPUP_RATES = {
	"RICE-HULL": 3000,
	"MINERAL-MIX": 45000,
	"SELENIUM-PREMIX": 850000,
	"VIT-D3": 620000,
	"VIT-A-ACETATE": 540000,
	"VIT-E": 410000,
}

# (marker, planned_start_offset_days, planned_end_offset_days, produced_qty, verified_on_offset_days)
_SCENARIOS = [
	("WO-A-ONTIME", -1 / 12, 0, _BATCH_QTY, 0),  # ~2h before "now" -> "now"; 100% yield; on time
	("WO-B-DELAYED", -6, -5, _BATCH_QTY, -1),  # planned to finish 5 days ago; 100% yield; four-eyes
	# verification only signed off 1 day before completion (4 days after planned_end_date) — the
	# real, directly-recorded contributing factor explain_production_delay() correlates against.
	("WO-C-YIELD-ANOMALY", -1 / 12, 0, 430, 0),  # on-time; 86% yield — beyond the 5% threshold.
	("WO-D-YIELD-NORMAL-VARIANCE", -1 / 12, 0, 480, 0),  # on-time; 96% yield — within the 5% threshold.
]

_INCOMPLETE_BATCH_ID = "PREMIX-BROILER-2PCT-AI5-INCOMPLETE-TEST"


# ---------------------------------------------------------------------------
# AI Tool registry additions (4 tools, appended to AI-DEMO-01/02/03's registry)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"explain_production_delay",
		"Explain Production Delay",
		"Real Work Order planned_end_date vs actual_end_date comparison, correlated against real Premix Weighing Verification (PM02) timing (Golden Demo #26 Premix).",
		"enterprise_core.enterprise_core.ai_tools.explain_production_delay",
		"Work Order",
	),
	(
		"analyze_yield_anomalies",
		"Analyze Yield Anomalies",
		"Real Work Order qty vs produced_qty yield comparison across multiple batches of the same item, flagged against a stated threshold (Golden Demo #26 Premix).",
		"enterprise_core.enterprise_core.ai_tools.analyze_yield_anomalies",
		"Work Order",
	),
	(
		"check_batch_record_completeness",
		"Check Batch Record Completeness",
		"Real per-batch audit: Quality Inspection, manufacturing traceability, and Premix Weighing Verification (PM02) presence for each required critical ingredient.",
		"enterprise_core.enterprise_core.ai_tools.check_batch_record_completeness",
		"Batch",
	),
	(
		"summarize_downtime",
		"Summarize Downtime",
		"Real Work Order planned_end_date vs actual_end_date gap AGGREGATE across a period — an explicitly-labeled derived proxy, not a native 'downtime' field.",
		"enterprise_core.enterprise_core.ai_tools.summarize_downtime",
		"Work Order",
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


def _ensure_prompt_template():
	if frappe.db.exists("Prompt Template", {"template_code": "manufacturing_insight_synthesis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "manufacturing_insight_synthesis",
			"version": 1,
			"system_instruction": (
				"You are a manufacturing operations insight assistant answering one of 4 approved analytical questions "
				"(explain a production delay, analyze yield anomalies, review batch-record completeness, summarize "
				"downtime). You are given REAL, tool-sourced structured manufacturing data as context — never invent "
				"facts, never fetch additional data yourself, never run or suggest SQL. Produce a concise interpretation "
				"grounded ONLY in the provided data, clearly distinguishing directly-recorded facts from any derived/ "
				"computed proxy the data explicitly flags as such. Your output is an interpretation, not a substitute "
				"for the underlying data facts, which are returned and logged separately. You never decide or authorize "
				"anything — a flagged anomaly, delay, or incomplete batch is always for a human to act on."
			),
			"input_schema": frappe.as_json({"question_code": "string", "<tool_code>": "object (tool-specific structured data)"}),
			"output_schema": frappe.as_json({"interpretation": "string"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", "manufacturing_insight_synthesis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "manufacturing_insight_synthesis",
			"description": "AI-DEMO-05 Manufacturing Insight — synthesizes an interpretation over real manufacturing tool output for one of 4 approved analytical questions. Read-only: never drafts, never mints or authorizes any record.",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "manufacturing_insight_synthesis", "version": 1}, "name"),
			"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS),
			"human_review_required": 0,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# AI-DEMO-05-owned Item + Formula (BOM) — isolated from the real flagship PREMIX-BROILER-2PCT.
# ---------------------------------------------------------------------------

def _ensure_ai5_item_and_bom():
	created = []
	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": "Broiler Vitamin-Mineral Premix (2%) — AI-DEMO-05 Insight Line",
				"item_group": "Finished Goods",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
			}
		).insert(ignore_permissions=True)
		created.append(_FG_ITEM)

	if not frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": _FG_ITEM,
				"quantity": _BATCH_QTY,
				"uom": "Kg",
				"company": _COMPANY_NAME,
				"is_active": 1,
				"is_default": 1,
				"premix_approval_status": "Approved",
			}
		)
		for item_code, qty, seq in _FORMULA_V1:
			bom.append("items", {"item_code": item_code, "qty": qty, "sequence_no": seq})
		bom.insert(ignore_permissions=True)
		bom.submit()
		created.append(f"BOM for {_FG_ITEM}")
	return created


def _ensure_extra_rm_stock():
	created = []
	for item_code, qty, seq in _FORMULA_V1:
		topup_qty = round(qty * _RM_TOPUP_MULTIPLIER, 4)
		if frappe.db.exists("Stock Entry Detail", {"item_code": item_code, "t_warehouse": _RM_WAREHOUSE, "qty": topup_qty}):
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": topup_qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": _RM_TOPUP_RATES[item_code]})
		se.insert(ignore_permissions=True)
		se.submit()
		created.append(item_code)
	return created


def _rename_finished_batch(wo_name, marker_batch_name):
	"""Resolves the batch a Work Order's Manufacture Stock Entry produced (same raw-SQL join
	idiom premix_seeds.py's own `_finished_batch()` already uses — a SEED-file convenience, not
	an AI-tool query, so the `frappe.get_list()`-only constraint that applies to `ai_tools.py`
	doesn't apply here) and renames it to a stable, memorable, idempotency-friendly marker —
	exactly the same technique `meddev_seeds.py`'s own `bad_batch_marker` already established."""
	rows = frappe.db.sql(
		"""select sbe.batch_no from `tabStock Entry` se
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.t_warehouse is not null and sed.is_finished_item = 1
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where se.work_order = %(wo)s and se.purpose = 'Manufacture' and se.docstatus = 1
		order by se.creation desc limit 1""",
		{"wo": wo_name},
	)
	batch_no = rows[0][0] if rows else None
	if batch_no and batch_no != marker_batch_name and not frappe.db.exists("Batch", marker_batch_name):
		frappe.rename_doc("Batch", batch_no, marker_batch_name, force=True)
	return marker_batch_name


def _ensure_qc_for_batch(marker_batch_name, se_name):
	"""Real Quality Inspection (Accepted) for a Work-Order-produced batch — idempotent and
	called UNCONDITIONALLY every run (decoupled from `_ensure_extra_work_order()`'s own
	Batch-existence guard, so it still runs even for a batch created by a PRIOR run). Every real
	Work-Order-produced batch in this dataset is fully documented; ONLY the standalone
	`_ensure_incomplete_batch()` fixture is deliberately missing this, so
	`check_batch_record_completeness()` has a real negative control (these 4) to contrast
	against its one positive/incomplete test case."""
	if frappe.db.exists("Quality Inspection", {"batch_no": marker_batch_name, "status": "Accepted", "docstatus": 1}):
		return False
	qi = frappe.get_doc(
		{
			"doctype": "Quality Inspection",
			"inspection_type": "In Process",
			"reference_type": "Stock Entry",
			"reference_name": se_name,
			"item_code": _FG_ITEM,
			"batch_no": marker_batch_name,
			"sample_size": 5,
			"status": "Accepted",
			"company": _COMPANY_NAME,
			"inspected_by": frappe.session.user,
		}
	)
	qi.insert(ignore_permissions=True)
	qi.submit()
	return True


def _manufacture_se_for_batch(marker_batch_name):
	"""Resolves the (already-submitted) Manufacture Stock Entry that produced `marker_batch_name`
	— used to backfill QC for a batch created by a PRIOR run of this module (before
	`_ensure_qc_for_batch()` existed, or simply on every idempotent re-run)."""
	row = frappe.db.sql(
		"""select se.name from `tabStock Entry` se
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.is_finished_item = 1
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where sbe.batch_no = %(batch)s and se.purpose = 'Manufacture' and se.docstatus = 1 limit 1""",
		{"batch": marker_batch_name},
	)
	return row[0][0] if row else None


def _ensure_extra_work_order(marker, planned_start_offset, planned_end_offset, produced_qty, verified_on_offset):
	"""Creates ONE of the 4 real, varied Work Order scenarios described in the module docstring
	— fully idempotent, guarded on the STABLE marker Batch name (never on a timestamp, since
	`planned_start_date`/`planned_end_date` are deliberately relative-to-"now"-at-first-seed-time
	and would otherwise drift on every re-run)."""
	marker_batch_name = f"{_FG_ITEM}-AIDEMO05-{marker}"
	if frappe.db.exists("Batch", marker_batch_name):
		_ensure_qc_for_batch(marker_batch_name, _manufacture_se_for_batch(marker_batch_name))
		return False, marker_batch_name

	now = frappe.utils.now_datetime()
	planned_start = frappe.utils.add_to_date(now, days=planned_start_offset)
	planned_end = frappe.utils.add_to_date(now, days=planned_end_offset)
	verified_on = frappe.utils.add_to_date(now, days=verified_on_offset)

	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name")
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": _FG_ITEM,
			"bom_no": bom_no,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _RM_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE,
			"skip_transfer": 1,
			"use_multi_level_bom": 0,
			"planned_start_date": planned_start,
			"planned_end_date": planned_end,
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()

	v = frappe.get_doc(
		{
			"doctype": "Premix Weighing Verification",
			"work_order": wo.name,
			"item_code": _CRITICAL_ITEM,
			"target_qty": _CRITICAL_TARGET_QTY,
			"weighed_qty": _CRITICAL_TARGET_QTY,
			"weighed_by": "Operator - Nguyen Van A (demo)",
			"status": "Pending",
		}
	)
	v.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Premix Weighing Verification",
		v.name,
		{"verified_by": "QA Supervisor - Tran Thi B (demo)", "verified_on": verified_on, "status": "Verified"},
	)

	if produced_qty >= _BATCH_QTY:
		# Full-yield scenario — reuses ERPNext's own native mapper, same as
		# premix_seeds.py's own _ensure_manufacture().
		from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

		se = make_stock_entry(wo.name, "Manufacture", qty=_BATCH_QTY)
		se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
		se.insert(ignore_permissions=True)
		se.submit()
	else:
		# Yield-loss scenario — manual build (mirrors premix_seeds.py's own PM01/PM03 negative-
		# test Stock Entry construction, but this one is meant to SUCCEED): full BOM-scale raw
		# material consumption (satisfies PM01's ±1% tolerance and PM03's ascending sequence
		# order), FG output declared BELOW the Work Order's planned qty — a real mass-balance
		# yield-loss scenario (material lost to spillage/dust during mixing), not a fabricated
		# number pretending to be something else.
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Manufacture",
				"purpose": "Manufacture",
				"company": _COMPANY_NAME,
				"work_order": wo.name,
				"bom_no": bom_no,
				# Real ERPNext gotcha found while building this: Stock Entry.validate() has
				# `if not self.from_bom: self.fg_completed_qty = 0.0` — a MANUALLY built
				# Manufacture entry (from_bom defaults falsy) silently gets fg_completed_qty
				# zeroed out during its own first validate() (which is why insert() succeeds —
				# the mandatory check runs BEFORE that reset — but a later submit() re-validates
				# against the now-zeroed value and throws "For Quantity is mandatory"). Setting
				# from_bom=1 here (exactly like the native make_stock_entry() mapper always
				# does) is what the WO-A/B branch above gets for free from that mapper.
				"from_bom": 1,
				"fg_completed_qty": produced_qty,
			}
		)
		for item_code, qty, seq in _FORMULA_V1:
			se.append("items", {"item_code": item_code, "qty": qty, "s_warehouse": _RM_WAREHOUSE})
		se.append("items", {"item_code": _FG_ITEM, "qty": produced_qty, "t_warehouse": _FG_QUARANTINE, "is_finished_item": 1, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()

	_rename_finished_batch(wo.name, marker_batch_name)
	_ensure_qc_for_batch(marker_batch_name, se.name)
	return True, wo.name


def _ensure_incomplete_batch():
	"""The deliberately-incomplete standalone Batch — `check_batch_record_completeness()`'s
	positive test case. No Work Order, no Quality Inspection, no Premix Weighing Verification —
	a real, if synthetic, 'batch known to the system but its documentation was never completed'
	scenario (e.g. a data-migration artifact or a batch record entered by hand), deliberately
	NOT routed through any real manufacture flow (which would legitimately trigger PM01-04 and
	could never actually produce an incomplete real batch of this item — Golden Demo #26's own
	validations are airtight by design)."""
	if frappe.db.exists("Batch", _INCOMPLETE_BATCH_ID):
		return False
	frappe.get_doc(
		{
			"doctype": "Batch",
			"item": _FG_ITEM,
			"batch_id": _INCOMPLETE_BATCH_ID,
			"manufacturing_date": frappe.utils.nowdate(),
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_manufacturing_insight():
	"""Phase 6A / AI-DEMO-05 — registers the 4 new AI Tools, the
	manufacturing_insight_synthesis Prompt Template + AI Action (reusing the existing,
	unmodified CE-13 AI foundation router/policy/logging), the isolated AI-DEMO-05-owned
	Item+Formula, the 4 real Work Order scenarios, and the deliberately-incomplete standalone
	Batch. Idempotent: safe to re-run any number of times. Self-skips (never calls
	premix_seeds.py's own Work-Order-related functions — see module docstring) if Golden Demo
	#26's own flagship Work Order/batch isn't already present."""
	master_data_result = seed_premix_master_data()
	if not frappe.db.exists("Work Order", {"production_item": "PREMIX-BROILER-2PCT", "docstatus": 1}):
		return f"seed_ai_manufacturing_insight: SKIPPED — Golden Demo #26 (Premix)'s own flagship Work Order not found. '{master_data_result}' Run Premix's full seed chain (through seed_premix_manufacturing) first."

	tools_created = _ensure_ai_tools()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	item_bom_created = _ensure_ai5_item_and_bom()
	rm_topped_up = _ensure_extra_rm_stock()

	scenarios_created = []
	for marker, start_off, end_off, produced_qty, verified_off in _SCENARIOS:
		created, ref = _ensure_extra_work_order(marker, start_off, end_off, produced_qty, verified_off)
		if created:
			scenarios_created.append(f"{marker}:{ref}")

	incomplete_batch_created = _ensure_incomplete_batch()

	return (
		f"seed_ai_manufacturing_insight: AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"AI-DEMO-05 Item/BOM: {item_bom_created or 'already existed'}. "
		f"RM top-up received for: {rm_topped_up or 'none (already topped up)'}. "
		f"Work Order scenarios created: {scenarios_created or 'none (already existed)'}. "
		f"Incomplete-batch fixture {'created' if incomplete_batch_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _test_all_questions_answer():
	"""Every one of the 4 example questions answers with the data_facts/ai_interpretation/
	sources/tools_called shape populated, as Administrator — and, unlike AI-DEMO-02/03, WITHOUT
	an ai_suggestion/draft field (proving the documented no-draft design decision actually holds
	in the response shape, not just in the docstring)."""
	results = {}
	for question_code, expected_tools in QUESTION_TOOL_MAP.items():
		resp = ask_manufacturing_insight(question_code, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "data_facts" not in resp or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': data_facts missing tool output.")
		if not resp.get("ai_interpretation"):
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': no ai_interpretation returned.")
		if "ai_suggestion" in resp:
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': response unexpectedly contains an ai_suggestion/draft field — this demo is documented as NO-DRAFT.")
		if not resp.get("provider") or not resp.get("model"):
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': provider/model not logged in response.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': no AI Job Log entry written.")
		logged_tools = frappe.db.get_value("AI Job Log", resp["job_log"], "tool_calls")
		if not logged_tools or frappe.parse_json(logged_tools) != expected_tools:
			frappe.throw(f"AI-DEMO-05 smoke test FAILED for '{question_code}': AI Job Log.tool_calls={logged_tools!r}, expected {expected_tools}.")
		results[question_code] = resp
	return results


def _test_production_delay_real_correlation(resp):
	"""explain_production_delay() flags WO-B-DELAYED as late and correlates it against its OWN
	real Premix Weighing Verification's verified_on timing; WO-A-ONTIME is correctly reported as
	on-time, not delayed — proving the tool distinguishes the two, not just flags everything."""
	facts = resp["data_facts"]["explain_production_delay"]
	delayed_wos = {d["work_order"] for d in facts["delayed"]}
	on_time_wos = {d["work_order"] for d in facts["on_time"]}
	wo_b_batch = f"{_FG_ITEM}-AIDEMO05-WO-B-DELAYED"
	wo_a_batch = f"{_FG_ITEM}-AIDEMO05-WO-A-ONTIME"
	# Resolve each scenario's real Work Order name via its stable marker batch.
	wo_b_name = _work_order_for_batch(wo_b_batch)
	wo_a_name = _work_order_for_batch(wo_a_batch)
	if not wo_b_name or wo_b_name not in delayed_wos:
		frappe.throw(f"AI-DEMO-05 delay test FAILED: WO-B-DELAYED ({wo_b_name}) not found in 'delayed'. Got: {sorted(delayed_wos)}")
	if not wo_a_name or wo_a_name not in on_time_wos:
		frappe.throw(f"AI-DEMO-05 delay test FAILED: WO-A-ONTIME ({wo_a_name}) not found in 'on_time'. Got: {sorted(on_time_wos)}")
	entry_b = next(d for d in facts["delayed"] if d["work_order"] == wo_b_name)
	if entry_b["delay_hours"] < 24:
		frappe.throw(f"AI-DEMO-05 delay test FAILED: WO-B-DELAYED's own delay_hours={entry_b['delay_hours']} is not a genuine multi-day delay.")
	factors_text = " ".join(entry_b["contributing_factors"])
	if "Premix Weighing Verification" not in factors_text or "AFTER" not in factors_text:
		frappe.throw(f"AI-DEMO-05 delay test FAILED: WO-B-DELAYED's contributing_factors did not cite the real verification-timing correlation. Got: {entry_b['contributing_factors']}")
	return f"production-delay CONFIRMED: {wo_b_name} correctly flagged delayed ({entry_b['delay_hours']}h) with a real verification-timing correlation; {wo_a_name} correctly reported on-time."


def _work_order_for_batch(marker_batch_name):
	if not frappe.db.exists("Batch", marker_batch_name):
		return None
	row = frappe.db.sql(
		"""select se.work_order from `tabStock Entry` se
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.is_finished_item = 1
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where sbe.batch_no = %(batch)s and se.purpose = 'Manufacture' and se.docstatus = 1 limit 1""",
		{"batch": marker_batch_name},
	)
	return row[0][0] if row else None


def _test_yield_anomaly_threshold_discrimination(resp):
	"""analyze_yield_anomalies() flags WO-C-YIELD-ANOMALY (86% yield, 14% deviation) as anomalous
	but does NOT flag WO-D-YIELD-NORMAL-VARIANCE (96% yield, 4% deviation) against the default 5%
	threshold — proving genuine threshold discrimination, not a blanket 'anything under 100% is
	an anomaly' rule."""
	facts = resp["data_facts"]["analyze_yield_anomalies"]
	by_batch = {b["batch_no"]: b for b in facts["batches"]}
	anomaly_batch = f"{_FG_ITEM}-AIDEMO05-WO-C-YIELD-ANOMALY"
	normal_batch = f"{_FG_ITEM}-AIDEMO05-WO-D-YIELD-NORMAL-VARIANCE"
	if anomaly_batch not in by_batch or not by_batch[anomaly_batch]["anomaly"]:
		frappe.throw(f"AI-DEMO-05 yield test FAILED: {anomaly_batch} not flagged as an anomaly. Got: {by_batch.get(anomaly_batch)}")
	if normal_batch not in by_batch or by_batch[normal_batch]["anomaly"]:
		frappe.throw(f"AI-DEMO-05 yield test FAILED: {normal_batch} incorrectly flagged as an anomaly (should be within threshold). Got: {by_batch.get(normal_batch)}")
	return f"yield-anomaly CONFIRMED: {anomaly_batch} ({by_batch[anomaly_batch]['yield_percent']}%) flagged anomalous; {normal_batch} ({by_batch[normal_batch]['yield_percent']}%) correctly within threshold."


def _test_batch_completeness_positive_negative(resp):
	"""check_batch_record_completeness() reports the deliberately-incomplete fixture batch as
	INCOMPLETE with real, specific missing-record reasons, and reports at least one real
	Work-Order-produced batch (e.g. WO-A-ONTIME's) as COMPLETE."""
	facts = resp["data_facts"]["check_batch_record_completeness"]
	by_batch = {r["batch_no"]: r for r in facts["results"]}
	if _INCOMPLETE_BATCH_ID not in by_batch or by_batch[_INCOMPLETE_BATCH_ID]["complete"]:
		frappe.throw(f"AI-DEMO-05 completeness test FAILED: {_INCOMPLETE_BATCH_ID} not reported incomplete. Got: {by_batch.get(_INCOMPLETE_BATCH_ID)}")
	if not by_batch[_INCOMPLETE_BATCH_ID]["missing"]:
		frappe.throw(f"AI-DEMO-05 completeness test FAILED: {_INCOMPLETE_BATCH_ID} reported incomplete but with no stated 'missing' reasons.")
	complete_batches = [b for b, r in by_batch.items() if r["complete"] and b != _INCOMPLETE_BATCH_ID]
	if not complete_batches:
		frappe.throw(f"AI-DEMO-05 completeness test FAILED: no genuinely COMPLETE batch found for contrast. Got: {by_batch}")
	return f"batch-completeness CONFIRMED: {_INCOMPLETE_BATCH_ID} correctly INCOMPLETE ({by_batch[_INCOMPLETE_BATCH_ID]['missing']}); {sorted(complete_batches)} correctly COMPLETE."


def _test_downtime_derived_proxy_labeled(resp):
	"""summarize_downtime() aggregates a genuine multi-day derived delay (from WO-B-DELAYED) and
	explicitly labels the number as a derived proxy, never as a native 'downtime' fact."""
	facts = resp["data_facts"]["summarize_downtime"]
	if "methodology_note" not in facts or "derived proxy" not in facts["methodology_note"]:
		frappe.throw(f"AI-DEMO-05 downtime test FAILED: methodology_note missing or doesn't explicitly say 'derived proxy'. Got: {facts.get('methodology_note')}")
	if facts["total_derived_delay_hours"] < 24:
		frappe.throw(f"AI-DEMO-05 downtime test FAILED: total_derived_delay_hours={facts['total_derived_delay_hours']} does not reflect WO-B-DELAYED's real multi-day gap.")
	return f"downtime-summary CONFIRMED: total_derived_delay_hours={facts['total_derived_delay_hours']}, explicitly labeled a derived proxy."


def seed_ai_manufacturing_insight_validations():
	"""Runs all validations end-to-end: 4-question smoke test (including the no-draft shape
	proof), the real delay-correlation proof, the yield-anomaly threshold-discrimination proof,
	the batch-completeness positive/negative proof, and the downtime derived-proxy labeling
	proof."""
	smoke = _test_all_questions_answer()
	delay = _test_production_delay_real_correlation(smoke["production_delay"])
	yield_test = _test_yield_anomaly_threshold_discrimination(smoke["yield_anomaly"])
	completeness = _test_batch_completeness_positive_negative(smoke["batch_completeness"])
	downtime = _test_downtime_derived_proxy_labeled(smoke["downtime_summary"])
	return f"seed_ai_manufacturing_insight_validations: all {len(smoke)} example questions answered, no ai_suggestion/draft field present (NO-DRAFT design confirmed). {delay} {yield_test} {completeness} {downtime}"
