"""Golden Demo #26 — Premix / Feed Additive Manufacturing (master plan DEMO 19, "PHASE 6" item
7), IP-PREMIX. Precision manufacturing, downstream/kin of Golden Demo #7 (Compound Feed
Manufacturing) — this Company makes the vitamin/mineral concentrate ("Premix") that a feed
mill's own Formula (e.g. Feed's PIG-STARTER, which already buys generic "Premix Vitamin-
Mineral" as an ingredient) actually needs a real GMP precision process to produce: a bulk
carrier (Rice Hull, ~94% of the batch by weight) diluting a handful of mg/g-scale
micro-ingredients (vitamins, a trace mineral) down to a dosable concentration, mixed in a
specific order, with one ingredient (Selenium) requiring a documented four-eyes check because
of its narrow safety margin.

Reuses Golden Demo #7's own manufacturing machinery unmodified: `block_fg_release_without_qa`
(QC release gate) and `block_weighing_tolerance_exceeded` (F03's blanket 3% tolerance, which
still applies here as the bulk-ingredient constraint — PM01's own ±1% is the ADDITIONAL,
tighter constraint for micro ingredients specifically) and `trace_feed_batch_genealogy()` (PM05,
called unmodified from `verify_premix_golden_demo()`, no seed-time wrapper needed).
"""

import frappe

_COMPANY_NAME = "Demo Premix Co."
_COMPANY_ABBR = "DPX"
_RM_WAREHOUSE = f"RM Store - {_COMPANY_ABBR}"
_FG_QUARANTINE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED = f"FG Released - {_COMPANY_ABBR}"

_FG_ITEM = "PREMIX-BROILER-2PCT"
_BATCH_QTY = 500  # kg — a real premix batch is much smaller than a bulk feed batch (Golden
# Demo #7's Pig Starter batch was 1000kg)

_CARRIER = ("RICE-HULL", "Rice Hull Carrier", "Kg")
_MINERAL_MIX = ("MINERAL-MIX", "Trace Mineral Mix", "Kg")
# (item_code, item_name, uom, requires_second_check) — all 4 are micro-dosed (Item.is_micro_ingredient=1).
_MICRO_ITEMS = [
	("SELENIUM-PREMIX", "Sodium Selenite (Selenium Premix)", "Kg", 1),  # narrow safety margin — PM02's critical ingredient
	("VIT-D3", "Vitamin D3 Premix", "Kg", 0),
	("VIT-A-ACETATE", "Vitamin A Acetate Premix", "Kg", 0),
	("VIT-E", "Vitamin E Premix", "Kg", 0),
]

# (item_code, qty at 500kg batch, mixing sequence_no) — carrier loads first, minerals next,
# vitamins last (real GMP practice: trace minerals can catalyze vitamin oxidation, so vitamins
# are added last to minimize contact time) — the master plan's "Sequencing" Đặc thù.
_FORMULA_V1 = [
	("RICE-HULL", 469, 1),
	("MINERAL-MIX", 15, 2),
	("SELENIUM-PREMIX", 0.05, 3),
	("VIT-D3", 3, 4),
	("VIT-A-ACETATE", 5, 5),
	("VIT-E", 7.95, 6),
]
# Received with a small buffer above the one real batch's own consumption on a couple of rows —
# not because the idempotency guard is balance-based (it isn't — see _ensure_rm_stock, guarded
# on Stock Entry Detail existence per this session's Lesson 3), but so PM01/PM03's own deliberate
# negative-test Stock Entries (which attempt a qty above/independent of the real batch's own
# consumption) have enough physical stock to reach the PM01/PM03 validation itself, rather than
# tripping an unrelated "insufficient stock" error first.
_RM_RECEIPT_PLAN = [
	("RICE-HULL", 469, 3000),
	("MINERAL-MIX", 15, 45000),
	("SELENIUM-PREMIX", 0.1, 850000),
	("VIT-D3", 4.0, 620000),
	("VIT-A-ACETATE", 5.0, 540000),
	("VIT-E", 7.95, 410000),
]

_CRITICAL_ITEM = "SELENIUM-PREMIX"
_CRITICAL_TARGET_QTY = 0.05

_QI_PARAMETER = "Premix Potency - Vitamin A (IU per kg)"


def _ensure_company():
	created = False
	if not frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
		created = True
	# Company.cost_center/round_off_cost_center are not reliably auto-populated by Company
	# creation (a real gap found repeatedly this session — Cosmetics/Pharmacy/3PL) — repaired
	# UNCONDITIONALLY (not only right after creation, per 3PL's DP-665 fix) so a re-run against
	# an already-existing company still repairs a gap from any cause.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "round_off_cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "round_off_cost_center", f"Main - {_COMPANY_ABBR}")
	return created


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_warehouses():
	for wh in (_RM_WAREHOUSE, _FG_QUARANTINE, _FG_RELEASED):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


def _ensure_items():
	created = 0
	code, name, uom = _CARRIER
	if not frappe.db.exists("Item", code):
		frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Raw Material", "stock_uom": uom, "is_stock_item": 1}).insert(ignore_permissions=True)
		created += 1
	code, name, uom = _MINERAL_MIX
	if not frappe.db.exists("Item", code):
		frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Raw Material", "stock_uom": uom, "is_stock_item": 1}).insert(ignore_permissions=True)
		created += 1
	for code, name, uom, requires_check in _MICRO_ITEMS:
		if frappe.db.exists("Item", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": "Raw Material",
				"stock_uom": uom,
				"is_stock_item": 1,
				"is_micro_ingredient": 1,
				"requires_second_check": 1 if requires_check else 0,
			}
		).insert(ignore_permissions=True)
		created += 1
	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": "Broiler Vitamin-Mineral Premix (2%)",
				"item_group": "Finished Goods",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _test_pm04_bom_blocked_without_approval():
	"""PM04 — formula revision. A BOM with premix_approval_status='Draft' cannot become the
	default Formula. Mirrors Medical Device's MD02 negative test shape: build the full doc,
	expect insert() itself to throw."""
	bom = frappe.get_doc(
		{"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1, "premix_approval_status": "Draft"}
	)
	for item_code, qty, seq in _FORMULA_V1:
		bom.append("items", {"item_code": item_code, "qty": qty, "sequence_no": seq})
	blocked = False
	try:
		bom.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		blocked = "PM04" in str(e)
		if not blocked:
			raise
	if not blocked:
		frappe.throw("PM04 negative test FAILED: a BOM with Draft premix_approval_status was not blocked from becoming default!")
	return True


def _ensure_formula():
	if frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		return False
	bom = frappe.get_doc(
		{"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1, "premix_approval_status": "Approved"}
	)
	for item_code, qty, seq in _FORMULA_V1:
		bom.append("items", {"item_code": item_code, "qty": qty, "sequence_no": seq})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_premix_master_data():
	"""Company, Item Groups, Warehouses, Items (carrier + trace mineral mix + 4 micro
	vitamins/minerals, one flagged critical + all 4 flagged micro), and the Formula (BOM) —
	PM04 CONFIRMED: a Draft-status BOM is proven blocked from becoming default before the real
	Approved one is created."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	items_created = _ensure_items()
	pm04 = _test_pm04_bom_blocked_without_approval()
	bom_created = _ensure_formula()
	return (
		f"seed_premix_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {items_created} new item(s). "
		f"PM04 CONFIRMED ({pm04}). Formula {'created' if bom_created else 'already existed'} (Approved, is_default)."
	)


def _ensure_rm_stock():
	"""Existence-guarded (not balance-guarded, per this session's Lesson 3 — a balance-based
	guard here would re-trigger once the real manufacture step consumes stock down)."""
	created = False
	for item_code, qty, rate in _RM_RECEIPT_PLAN:
		if frappe.db.exists("Stock Entry Detail", {"item_code": item_code, "t_warehouse": _RM_WAREHOUSE}):
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": rate})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _ensure_work_order():
	existing = frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1})
	if existing:
		return existing, False
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
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo.name, True


def _test_pm02_manufacture_blocked_without_verification(wo_name):
	"""PM02 — critical ingredient double-check. Without a Verified Premix Weighing Verification
	record for the critical ingredient, even the REAL manufacture attempt (via ERPNext's own
	make_stock_entry() mapper) is blocked at insert() time."""
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return True  # already manufactured in a prior run — nothing left to block
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	blocked = False
	try:
		se = make_stock_entry(wo_name, "Manufacture", qty=_BATCH_QTY)
		se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
		se.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		blocked = "PM02" in str(e)
		if not blocked:
			raise
	if not blocked:
		frappe.throw("PM02 negative test FAILED: manufacture proceeded without a Verified weighing check on the critical ingredient!")
	return True


def seed_premix_weighing_verification():
	"""PM02 — critical ingredient double-check (four-eyes control). A Premix Weighing
	Verification record is created Pending (one person weighs), proven to BLOCK manufacture
	while Pending, then Verified by a second, different person — after which the same
	manufacture attempt would succeed (proven for real in seed_premix_manufacturing)."""
	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name")
	if not bom_no:
		return "seed_premix_weighing_verification: SKIPPED — run seed_premix_master_data first."
	rm_received = _ensure_rm_stock()
	wo_name, wo_created = _ensure_work_order()

	verification_name = frappe.db.get_value("Premix Weighing Verification", {"work_order": wo_name, "item_code": _CRITICAL_ITEM}, "name")
	if not verification_name:
		v = frappe.get_doc(
			{
				"doctype": "Premix Weighing Verification",
				"work_order": wo_name,
				"item_code": _CRITICAL_ITEM,
				"target_qty": _CRITICAL_TARGET_QTY,
				"weighed_qty": _CRITICAL_TARGET_QTY,
				"weighed_by": "Operator - Nguyen Van A (demo)",
				"status": "Pending",
			}
		)
		v.insert(ignore_permissions=True)
		verification_name = v.name

	pm02 = _test_pm02_manufacture_blocked_without_verification(wo_name)

	verified = False
	if frappe.db.get_value("Premix Weighing Verification", verification_name, "status") != "Verified":
		frappe.db.set_value(
			"Premix Weighing Verification",
			verification_name,
			{"verified_by": "QA Supervisor - Tran Thi B (demo)", "verified_on": frappe.utils.now_datetime(), "status": "Verified"},
		)
		verified = True

	return (
		f"seed_premix_weighing_verification: RM stock {'received' if rm_received else 'already present'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). PM02 CONFIRMED ({pm02}). "
		f"Verification {verification_name} {'newly Verified (four-eyes: second person)' if verified else 'already Verified'}."
	)


def _test_pm03_sequence_violation_blocked(wo_name):
	"""PM03 — sequence rule. A minimal, deliberately out-of-order manual Stock Entry (a
	late-sequence vitamin appended before the carrier, sequence 1) is blocked — deliberately
	excludes the critical ingredient so this test isolates PM03 from PM02 (which is already
	resolved/Verified by the time this runs, but isolating cause is more rigorous either way)."""
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return True  # already manufactured in a prior run — nothing left to block
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Manufacture", "purpose": "Manufacture", "company": _COMPANY_NAME, "work_order": wo_name, "fg_completed_qty": 1})
	se.append("items", {"item_code": "VIT-D3", "qty": 3, "s_warehouse": _RM_WAREHOUSE})  # sequence 4
	se.append("items", {"item_code": "RICE-HULL", "qty": 469, "s_warehouse": _RM_WAREHOUSE})  # sequence 1 — added AFTER, violates order
	se.append("items", {"item_code": _FG_ITEM, "qty": 1, "t_warehouse": _FG_QUARANTINE, "is_finished_item": 1})  # native "at least 1 FG row" gate
	blocked = False
	try:
		se.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		blocked = "PM03" in str(e)
		if not blocked:
			raise
	if not blocked:
		frappe.throw("PM03 negative test FAILED: an out-of-order ingredient consumption was not blocked!")
	return True


def seed_premix_sequencing():
	"""PM03 — sequence rule. Requires the critical ingredient already Verified (PM02) so this
	test's own block is attributable to sequencing alone, not an incidental PM02 gate."""
	wo_name = frappe.db.get_value("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}, "name")
	if not wo_name:
		return "seed_premix_sequencing: SKIPPED — run seed_premix_weighing_verification first."
	if frappe.db.get_value("Premix Weighing Verification", {"work_order": wo_name, "item_code": _CRITICAL_ITEM}, "status") != "Verified":
		return "seed_premix_sequencing: SKIPPED — run seed_premix_weighing_verification first (critical ingredient must be Verified first, to isolate PM03 from PM02)."
	pm03 = _test_pm03_sequence_violation_blocked(wo_name)
	return f"seed_premix_sequencing: PM03 CONFIRMED ({pm03})."


def _test_pm01_micro_tolerance_blocked(wo_name):
	"""PM01 — micro-weigh tolerance. A minimal, single-row manual Stock Entry weighs VIT-D3
	(target 3kg at this batch size) at 3.06kg — a 2% deviation. Deliberately chosen BETWEEN
	PM01's own ±1% micro tolerance and Golden Demo #7's generic ±3% blanket tolerance (F03,
	which also fires on every Manufacture Stock Entry including this one): a 2% deviation
	passes F03 (under 3%) but must still be blocked by PM01 (over 1%) — proving PM01 is a
	genuinely TIGHTER, additional constraint for micro ingredients, not just a duplicate of
	F03. A larger deviation would get caught by F03 first and never prove PM01 fired at all.
	Single-row doc, so PM02/PM03 cannot fire (isolates PM01)."""
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return True  # already manufactured in a prior run — nothing left to block
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Manufacture", "purpose": "Manufacture", "company": _COMPANY_NAME, "work_order": wo_name, "fg_completed_qty": 1})
	se.append("items", {"item_code": "VIT-D3", "qty": 3.06, "s_warehouse": _RM_WAREHOUSE})
	se.append("items", {"item_code": _FG_ITEM, "qty": 1, "t_warehouse": _FG_QUARANTINE, "is_finished_item": 1})  # native "at least 1 FG row" gate
	blocked = False
	try:
		se.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		blocked = "PM01" in str(e)
		if not blocked:
			raise
	if not blocked:
		frappe.throw("PM01 negative test FAILED: an out-of-tolerance micro-ingredient weight was not blocked!")
	return True


def seed_premix_micro_tolerance():
	"""PM01 — micro-weigh tolerance."""
	wo_name = frappe.db.get_value("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}, "name")
	if not wo_name:
		return "seed_premix_micro_tolerance: SKIPPED — run seed_premix_weighing_verification first."
	pm01 = _test_pm01_micro_tolerance_blocked(wo_name)
	return f"seed_premix_micro_tolerance: PM01 CONFIRMED ({pm01})."


def _ensure_manufacture(wo_name):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=_BATCH_QTY)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _finished_batch():
	rows = frappe.db.sql(
		"""select sbe.batch_no from `tabWork Order` wo
		join `tabStock Entry` se on se.work_order = wo.name and se.purpose = 'Manufacture' and se.docstatus = 1
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.t_warehouse is not null
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where wo.production_item = %(item)s order by wo.creation asc limit 1""",
		{"item": _FG_ITEM},
	)
	return rows[0][0] if rows else None


def _ensure_qi_parameter():
	if frappe.db.exists("Quality Inspection Parameter", _QI_PARAMETER):
		return False
	frappe.get_doc(
		{"doctype": "Quality Inspection Parameter", "parameter": _QI_PARAMETER, "description": "Target 500,000 IU/kg Vitamin A activity in the finished premix; ±10% acceptance band."}
	).insert(ignore_permissions=True)
	return True


def _ensure_qc_and_release():
	batch = _finished_batch()
	if not batch:
		return None, False, False

	qi_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}):
		_ensure_qi_parameter()
		se_name = frappe.db.get_value("Stock Entry", {"work_order": frappe.db.get_value("Work Order", {"production_item": _FG_ITEM}, "name"), "purpose": "Manufacture"}, "name")
		qi = frappe.get_doc(
			{
				"doctype": "Quality Inspection",
				"inspection_type": "In Process",
				"reference_type": "Stock Entry",
				"reference_name": se_name,
				"item_code": _FG_ITEM,
				"batch_no": batch,
				"sample_size": 5,
				"company": _COMPANY_NAME,
				"inspected_by": frappe.session.user,
				# PM06 (COA) — native Quality Inspection Reading: numeric + min/max/reading_1 auto-
				# computes Accepted/Rejected (erpnext's own min_max_criteria_passed()), exactly
				# "measured potency within tolerance of target," zero new schema needed.
				"readings": [{"specification": _QI_PARAMETER, "numeric": 1, "min_value": 450000, "max_value": 550000, "reading_1": "512000"}],
			}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		qi_created = True

	released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(_FG_RELEASED, batch),
	)
	release_created = False
	if not released:
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": _FG_ITEM, "qty": _BATCH_QTY, "s_warehouse": _FG_QUARANTINE, "t_warehouse": _FG_RELEASED, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qi_created, release_created


def seed_premix_manufacturing():
	"""The real manufacture — PM01/PM02/PM03 are all now simultaneously satisfiable (exact
	BOM-ratio consumption via make_stock_entry(), critical ingredient Verified, and consumption
	order following the BOM's own insertion order, which was created in ascending sequence_no)
	— then PM06 (COA/potency) and release (`block_fg_release_without_qa` reuse), and PM07
	(yield reconciliation)."""
	wo_name = frappe.db.get_value("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}, "name")
	if not wo_name:
		return "seed_premix_manufacturing: SKIPPED — run seed_premix_weighing_verification first."
	if frappe.db.get_value("Premix Weighing Verification", {"work_order": wo_name, "item_code": _CRITICAL_ITEM}, "status") != "Verified":
		return "seed_premix_manufacturing: SKIPPED — run seed_premix_weighing_verification first (critical ingredient must be Verified before real manufacture, PM02)."

	manufacture_created = _ensure_manufacture(wo_name)
	batch, qi_created, release_created = _ensure_qc_and_release()

	wo = frappe.db.get_value("Work Order", wo_name, ["qty", "produced_qty"], as_dict=True)
	yield_percent = round((wo.produced_qty / wo.qty) * 100, 1) if wo and wo.produced_qty else 0

	return (
		f"seed_premix_manufacturing: Manufacture {'created' if manufacture_created else 'already existed'}. Batch {batch}. "
		f"QC/COA (PM06) {'created' if qi_created else 'already existed'} (Accepted, potency 512,000 IU/kg within 450k-550k band). "
		f"Release {'created' if release_created else 'already existed'} (block_fg_release_without_qa reuse). PM07 yield: {yield_percent}%."
	)
