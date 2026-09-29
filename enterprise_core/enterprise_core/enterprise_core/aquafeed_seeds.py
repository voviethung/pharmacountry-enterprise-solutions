"""Golden Demo #15 — Aquafeed Manufacturing (master plan DEMO 26, "PHASE 5" item 1), IP-AQUAFEED.
Reuses ERPNext's manufacturing module (BOM=Formula, Stock Entry, Work Order, Quality
Inspection) exactly as Golden Demo #1/#7/#9 did, including the SAME generic
`block_fg_release_without_qa` hook (AF06) with zero changes, and Golden Demo #7's
`trace_feed_batch_genealogy()` (AF05) unmodified too — it's a generic Serial-and-Batch-Bundle
walk, not Feed-specific. Raw materials already created by Feed Manufacturing (FISH-MEAL, SBM,
PREMIX-VM) are reused directly rather than re-created — Item is not company-scoped in ERPNext,
only Warehouse/stock balances are.
"""

import frappe

_COMPANY_NAME = "Demo Aquafeed Co."
_COMPANY_ABBR = "DAF"
_RM_WAREHOUSE = f"RM Silo - {_COMPANY_ABBR}"
_FG_QUARANTINE_WAREHOUSE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED_WAREHOUSE = f"FG Released - {_COMPANY_ABBR}"
_BATCH_QTY = 1000

_SHRIMP_SPECIES = "Shrimp (Litopenaeus vannamei)"
_PL_ITEM = ("SHRIMP-FEED-PL", "Shrimp Feed - Post-Larvae", "Post-Larvae", 0.6, "Sinking")
_GROWER_ITEM = ("SHRIMP-FEED-GROWER", "Shrimp Feed - Grower", "Grower", 2.2, "Sinking")

_FORMULA_PL = [("FISH-MEAL", 450), ("SBM", 250), ("FISH-OIL", 100), ("WHEAT-FLOUR", 150), ("PREMIX-VM", 50)]
_FORMULA_GROWER = [("FISH-MEAL", 300), ("SBM", 350), ("FISH-OIL", 60), ("WHEAT-FLOUR", 250), ("PREMIX-VM", 40)]


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_warehouses():
	for wh in (_RM_WAREHOUSE, _FG_QUARANTINE_WAREHOUSE, _FG_RELEASED_WAREHOUSE):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


def _ensure_raw_materials():
	created = 0
	for item_code, item_name in [("FISH-OIL", "Fish Oil"), ("WHEAT-FLOUR", "Wheat Flour (Binder)")]:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}).insert(
			ignore_permissions=True
		)
		created += 1
	return created


def _ensure_finished_items():
	created = 0
	for item_code, item_name, life_stage, pellet_size, buoyancy in (_PL_ITEM, _GROWER_ITEM):
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_name,
				"item_group": "Finished Goods",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"target_species": _SHRIMP_SPECIES,
				"life_stage": life_stage,
				"pellet_size_mm": pellet_size,
				"buoyancy": buoyancy,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_formula(item_code, ingredients):
	if frappe.db.exists("BOM", {"item": item_code, "is_active": 1}):
		return False
	bom = frappe.get_doc({"doctype": "BOM", "item": item_code, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, qty in ingredients:
		bom.append("items", {"item_code": ing_code, "qty": qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_aquafeed_master_data():
	"""DP-597 — Company, Warehouses ("Silos"), Items (species/life_stage/pellet_size/buoyancy —
	AF01/AF02), and 2 Formulas for the same species at 2 different life stages (AF01: "formula
	by species/stage")."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	rm_created = _ensure_raw_materials()
	fg_created = _ensure_finished_items()
	pl_bom_created = _ensure_formula(_PL_ITEM[0], _FORMULA_PL)
	grower_bom_created = _ensure_formula(_GROWER_ITEM[0], _FORMULA_GROWER)
	return (
		f"seed_aquafeed_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). "
		f"{rm_created} new raw material(s), {fg_created} new finished item(s). "
		f"Post-Larvae formula {'created' if pl_bom_created else 'already existed'}. Grower formula {'created' if grower_bom_created else 'already existed'} (AF01)."
	)


def _ensure_rm_stock():
	created = False
	for item_code, qty in [("FISH-MEAL", 300), ("SBM", 350), ("FISH-OIL", 60), ("WHEAT-FLOUR", 250), ("PREMIX-VM", 40)]:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_WAREHOUSE, item_code))[0][0] or 0
		if balance >= qty:
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 22000})
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


def _ensure_extrusion_log(wo_name):
	if frappe.db.exists("Aquafeed Extrusion Log", {"work_order": wo_name}):
		return False
	frappe.get_doc(
		{"doctype": "Aquafeed Extrusion Log", "work_order": wo_name, "barrel_temperature_c": 95.0, "moisture_percent": 11.5, "oil_coating_percent": 2.5, "measured_pellet_size_mm": 2.15}
	).insert(ignore_permissions=True)
	return True


def _ensure_qc_and_release(production_item, wo_name):
	batch = frappe.db.get_value("Batch", {"item": production_item, "batch_qty": [">", 0]}, "name")
	if not batch:
		return None, False, False
	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}):
		se_name = frappe.db.get_value("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture"}, "name")
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
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": production_item, "qty": _BATCH_QTY, "s_warehouse": _FG_QUARANTINE_WAREHOUSE, "t_warehouse": _FG_RELEASED_WAREHOUSE, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qc_created, release_created


def seed_aquafeed_production():
	"""DP-598 — the master plan's own flow (extrusion -> drying -> oil coating -> QC ->
	release) for Shrimp Feed - Grower. AF03 (extrusion process record), AF04 (batch QC, native
	Quality Inspection), AF05 (lot trace, reuses Golden Demo #7's trace_feed_batch_genealogy()
	unmodified), AF06 (release gate, reuses block_fg_release_without_qa unmodified — 4th reuse
	after Pharma/Feed/Vet Mfg), AF07 (yield)."""
	bom_no = frappe.db.get_value("BOM", {"item": _GROWER_ITEM[0], "is_active": 1}, "name")
	if not bom_no:
		return "seed_aquafeed_production: SKIPPED — run seed_aquafeed_master_data first."
	rm_received = _ensure_rm_stock()
	wo_name, wo_created = _ensure_work_order(_GROWER_ITEM[0], bom_no)
	manufacture_created = _ensure_manufacture(wo_name)
	extrusion_created = _ensure_extrusion_log(wo_name)
	batch, qc_created, release_created = _ensure_qc_and_release(_GROWER_ITEM[0], wo_name)
	produced_qty = frappe.db.get_value("Work Order", wo_name, "produced_qty")
	yield_percent = round((produced_qty / _BATCH_QTY) * 100, 1) if produced_qty else 0

	from enterprise_core.enterprise_core.api import trace_feed_batch_genealogy

	genealogy = trace_feed_batch_genealogy(batch) if batch else None
	trace_ok = bool(genealogy and genealogy.get("raw_materials_consumed"))

	return (
		f"seed_aquafeed_production: RM stock {'received' if rm_received else 'already present'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). Manufacture {'created' if manufacture_created else 'already existed'}. "
		f"Extrusion Log {'created' if extrusion_created else 'already existed'} (AF03). Batch {batch}. "
		f"QC {'created' if qc_created else 'already existed'} (AF04). Release {'created' if release_created else 'already existed'} (AF06). "
		f"AF07 yield: {yield_percent}%. AF05 lot trace resolves: {trace_ok}."
	)
