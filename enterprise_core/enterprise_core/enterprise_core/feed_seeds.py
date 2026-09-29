"""Golden Demo #7 — Compound Feed Manufacturing (master plan DEMO 18), a NEW industry
vertical (unlike Golden Demo #3-6, which were standalone cross-industry products reusing
Demo Pharma Co) — its own Company, own master data. Reuses ERPNext's manufacturing module
(BOM=Formula, Stock Entry, Work Order, Quality Inspection) exactly as Golden Demo #1 did,
including the SAME generic `block_fg_release_without_qa` hook (F06 QC release) with zero
changes — it's warehouse-name-pattern-based, not pharma-specific.
"""

import frappe

_COMPANY_NAME = "Demo Feed Mill Co."
_COMPANY_ABBR = "DFM"
_RM_WAREHOUSE = f"RM Silo - {_COMPANY_ABBR}"
_FG_QUARANTINE_WAREHOUSE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED_WAREHOUSE = f"FG Released - {_COMPANY_ABBR}"

_RAW_MATERIALS = [("CORN", "Corn", "Kg", 0), ("SBM", "Soybean Meal", "Kg", 0), ("FISH-MEAL", "Fish Meal", "Kg", 1), ("PREMIX-VM", "Premix Vitamin-Mineral", "Kg", 0)]
_PIG_STARTER = ("PIG-STARTER", "Pig Starter Feed", "Kg", 1)  # formula includes Fish Meal (allergen)
_PIG_GROWER = ("PIG-GROWER", "Pig Grower Feed", "Kg", 0)  # formula has no fish meal — deliberately non-allergen for F07
_BATCH_QTY = 1000


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": _COMPANY_NAME,
			"abbr": _COMPANY_ABBR,
			"default_currency": "VND",
			"country": "Vietnam",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(
				ignore_permissions=True
			)


def _ensure_warehouses():
	for wh in (_RM_WAREHOUSE, _FG_QUARANTINE_WAREHOUSE, _FG_RELEASED_WAREHOUSE):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(
				ignore_permissions=True
			)


def _ensure_items():
	for item_code, item_name, uom, allergen in _RAW_MATERIALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_name,
				"item_group": "Raw Material",
				"stock_uom": uom,
				"is_stock_item": 1,
				"contains_allergen": allergen,
			}
		).insert(ignore_permissions=True)
	for item_code, item_name, uom, allergen in (_PIG_STARTER, _PIG_GROWER):
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_name,
				"item_group": "Finished Goods",
				"stock_uom": uom,
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"contains_allergen": allergen,
			}
		).insert(ignore_permissions=True)


_FORMULA_V1 = [("CORN", 600), ("SBM", 300), ("FISH-MEAL", 80), ("PREMIX-VM", 20)]
_FORMULA_GROWER = [("CORN", 650), ("SBM", 330), ("PREMIX-VM", 20)]  # no fish meal — non-allergen


def _ensure_formula(item_code, ingredients):
	if frappe.db.exists("BOM", {"item": item_code, "is_active": 1}):
		return False
	bom = frappe.get_doc(
		{"doctype": "BOM", "item": item_code, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1}
	)
	for ing_code, qty in ingredients:
		bom.append("items", {"item_code": ing_code, "qty": qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_feed_master_data():
	"""DP-548 — Company, Item Groups, Warehouses ("Silos"), Items, and Formula (BOM) for
	Pig Starter Feed. Master plan §7 DEMO 18 Entities: Ingredient=Item, Formula=BOM,
	Silo=Warehouse."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	_ensure_items()
	starter_created = _ensure_formula("PIG-STARTER", _FORMULA_V1)
	grower_created = _ensure_formula("PIG-GROWER", _FORMULA_GROWER)
	return (
		f"seed_feed_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). "
		f"Formula (Pig Starter) {'created' if starter_created else 'already existed'}. "
		f"Formula (Pig Grower, non-allergen) {'created' if grower_created else 'already existed'}."
	)


def seed_feed_formula_revision():
	"""DP-549 — F01, formula revision. Cancels BOM v1 for Pig Starter and creates v2 with a
	reduced fish-meal ratio (80kg -> 60kg, offset by more soybean meal), same pattern as
	Golden Demo #1's DP-504 BOM-fix incident (cancel old, create new, old keeps its name)."""
	old_bom = frappe.db.get_value("BOM", {"item": "PIG-STARTER", "is_active": 1}, "name")
	if not old_bom:
		return "seed_feed_formula_revision: SKIPPED — run seed_feed_master_data first."
	if frappe.db.count("BOM", {"item": "PIG-STARTER"}) >= 2:
		return "seed_feed_formula_revision: already revised (2+ BOM versions exist)."
	frappe.get_doc("BOM", old_bom).cancel()
	new_bom = frappe.get_doc(
		{"doctype": "BOM", "item": "PIG-STARTER", "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1}
	)
	for ing_code, qty in [("CORN", 600), ("SBM", 320), ("FISH-MEAL", 60), ("PREMIX-VM", 20)]:
		new_bom.append("items", {"item_code": ing_code, "qty": qty})
	new_bom.insert(ignore_permissions=True)
	new_bom.submit()
	return f"seed_feed_formula_revision: F01 CONFIRMED — {old_bom} cancelled, new version {new_bom.name} active."


def seed_feed_substitution():
	"""DP-550 — F02, ingredient substitution approval. A pending request to swap Fish Meal
	for Meat and Bone Meal, approved by a demo user."""
	current_bom = frappe.db.get_value("BOM", {"item": "PIG-STARTER", "is_active": 1}, "name")
	if not current_bom:
		return "seed_feed_substitution: SKIPPED — run seed_feed_master_data first."
	if frappe.db.exists("Feed Ingredient Substitution", {"formula_bom": current_bom}):
		return "seed_feed_substitution: already existed."
	if not frappe.db.exists("Item", "MBM"):
		frappe.get_doc(
			{"doctype": "Item", "item_code": "MBM", "item_name": "Meat and Bone Meal", "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}
		).insert(ignore_permissions=True)
	sub = frappe.get_doc(
		{
			"doctype": "Feed Ingredient Substitution",
			"formula_bom": current_bom,
			"original_item": "FISH-MEAL",
			"substitute_item": "MBM",
			"reason": "Fish meal price volatility — evaluating a lower-cost protein source of equivalent nutrition.",
			"status": "Pending",
		}
	)
	sub.insert(ignore_permissions=True)
	sub.status = "Approved"
	sub.approved_by = "production.manager@pharmacountry.vn"
	sub.save(ignore_permissions=True)
	return f"seed_feed_substitution: F02 CONFIRMED — substitution request {sub.name} Approved."


def _ensure_rm_stock():
	created = False
	for item_code, qty in [("CORN", 700), ("SBM", 400), ("FISH-MEAL", 80), ("PREMIX-VM", 30)]:
		balance = (
			frappe.db.sql(
				"select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0",
				(_RM_WAREHOUSE, item_code),
			)[0][0]
			or 0
		)
		if balance >= qty:
			continue
		se = frappe.get_doc(
			{"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME}
		)
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 15000})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _ensure_work_order(production_item, bom_no):
	existing = frappe.db.exists("Work Order", {"production_item": production_item, "docstatus": 1})
	if existing:
		return existing, False
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": production_item,
			"bom_no": bom_no,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _RM_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"skip_transfer": 1,
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo.name, True


def _ensure_manufacture(wo_name):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=_BATCH_QTY)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _ensure_qc_and_release(production_item):
	batch = frappe.db.get_value("Batch", {"item": production_item, "batch_qty": [">", 0]}, "name")
	if not batch:
		return None, False, False
	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}):
		se_name = frappe.db.get_value("Stock Entry", {"work_order": frappe.db.get_value("Work Order", {"production_item": production_item}, "name"), "purpose": "Manufacture"}, "name")
		qi = frappe.get_doc(
			{
				"doctype": "Quality Inspection",
				"inspection_type": "In Process",
				"reference_type": "Stock Entry",
				"reference_name": se_name,
				"item_code": production_item,
				"batch_no": batch,
				"sample_size": 5,
				"status": "Accepted",
				"company": _COMPANY_NAME,
				"inspected_by": frappe.session.user,
			}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		qc_created = True

	released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(_FG_RELEASED_WAREHOUSE, batch),
	)
	release_created = False
	if not released:
		se = frappe.get_doc(
			{"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME}
		)
		se.append(
			"items",
			{
				"item_code": production_item,
				"qty": _BATCH_QTY,
				"s_warehouse": _FG_QUARANTINE_WAREHOUSE,
				"t_warehouse": _FG_RELEASED_WAREHOUSE,
				"batch_no": batch,
				"use_serial_batch_fields": 1,
			},
		)
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qc_created, release_created


def seed_feed_manufacturing():
	"""DP-551 — the master plan's own flow (weighing -> mixing -> QC -> warehouse) for Pig
	Starter Feed, using the REVISED formula (F01). F03 (weighing tolerance) is enforced
	structurally by `block_weighing_tolerance_exceeded` on every Manufacture Stock Entry —
	this run passes because ERPNext's own make_stock_entry() computes exact BOM-ratio
	consumption (0% deviation). F06 (QC release) reuses Golden Demo #1's generic
	`block_fg_release_without_qa` hook unmodified."""
	bom_no = frappe.db.get_value("BOM", {"item": "PIG-STARTER", "is_active": 1}, "name")
	if not bom_no:
		return "seed_feed_manufacturing: SKIPPED — run seed_feed_master_data first."
	rm_received = _ensure_rm_stock()
	wo_name, wo_created = _ensure_work_order("PIG-STARTER", bom_no)
	manufacture_created = _ensure_manufacture(wo_name)
	batch, qc_created, release_created = _ensure_qc_and_release("PIG-STARTER")
	produced_qty = frappe.db.get_value("Work Order", wo_name, "produced_qty")
	yield_percent = round((produced_qty / _BATCH_QTY) * 100, 1) if produced_qty else 0
	return (
		f"seed_feed_manufacturing: RM stock {'received' if rm_received else 'already present'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). "
		f"Manufacture {'created' if manufacture_created else 'already existed'}. Batch {batch}. "
		f"QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'}. "
		f"F05 yield: {yield_percent}%."
	)


def _ensure_grower_rm_stock():
	created = False
	for item_code, qty in [("CORN", 700), ("SBM", 400)]:
		balance = (
			frappe.db.sql(
				"select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0",
				(_RM_WAREHOUSE, item_code),
			)[0][0]
			or 0
		)
		if balance >= qty:
			continue
		se = frappe.get_doc(
			{"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME}
		)
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 15000})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _test_f07_sequencing_blocked_then_cleaned():
	"""F07 negative-then-positive test. Pig Grower Feed (non-allergen) can't start on the
	same line right after Pig Starter Feed (contains fish meal, allergen) without a Line
	Cleaning Log recorded since — blocked first, then succeeds once cleaned."""
	grower_bom = frappe.db.get_value("BOM", {"item": "PIG-GROWER", "is_active": 1}, "name")
	if not grower_bom:
		frappe.throw("_test_f07_sequencing_blocked_then_cleaned: Pig Grower BOM not found — run seed_feed_master_data first.")
	if frappe.db.exists("Work Order", {"production_item": "PIG-GROWER", "docstatus": 1}):
		return True

	_ensure_grower_rm_stock()
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": "PIG-GROWER",
			"bom_no": grower_bom,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _RM_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"skip_transfer": 1,
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	blocked = False
	try:
		wo.insert(ignore_permissions=True)
		wo.submit()
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("F07 negative test FAILED: a non-allergen Work Order right after an allergen run was not blocked!")

	# clean the line, then the same attempt must succeed
	frappe.get_doc(
		{
			"doctype": "Feed Line Cleaning Log",
			"warehouse": _FG_QUARANTINE_WAREHOUSE,
			"cleaned_by": "Warehouse Officer (demo)",
			"notes": "Full wet clean after Pig Starter (allergen) run — verified allergen-free per F07.",
		}
	).insert(ignore_permissions=True)

	wo2 = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": "PIG-GROWER",
			"bom_no": grower_bom,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _RM_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"skip_transfer": 1,
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo2.insert(ignore_permissions=True)
	wo2.submit()
	return True


def seed_feed_sequencing():
	"""DP-552 — F07, cross-contamination/sequencing flag."""
	if not frappe.db.exists("Work Order", {"production_item": "PIG-STARTER", "docstatus": 1}):
		return "seed_feed_sequencing: SKIPPED — run seed_feed_manufacturing first (need a completed allergen run on the line)."
	f07 = _test_f07_sequencing_blocked_then_cleaned()
	return f"seed_feed_sequencing: F07 CONFIRMED ({f07})."
