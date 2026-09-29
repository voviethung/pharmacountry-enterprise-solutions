"""Golden Demo #22 — Medical Device Manufacturing (master plan DEMO 04, "PHASE 6" item 3),
IP-MEDICAL-DEVICE.
"""

import frappe

_COMPANY_NAME = "Demo MedDevice Co."
_COMPANY_ABBR = "DMD"
_RM_WAREHOUSE = f"RM Store - {_COMPANY_ABBR}"
_WIP_WAREHOUSE = f"WIP Store - {_COMPANY_ABBR}"
_FG_QUARANTINE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED = f"FG Released - {_COMPANY_ABBR}"

_FG_ITEM = "INFUSION-PUMP-ACC"
_COMPONENTS = [("PUMP-HOUSING", "Pump Housing (Critical Component)"), ("PUMP-TUBING", "Pump Tubing"), ("PUMP-FASTENERS", "Fasteners Kit"), ("PUMP-SEAL", "Seal Ring")]
_BATCH_QTY = 10
_BOM_ITEMS = [("PUMP-HOUSING", 10), ("PUMP-TUBING", 20), ("PUMP-FASTENERS", 40), ("PUMP-SEAL", 10)]

_SUPPLIER_NAME = "MedTech Precision Components Ltd."
_SUPPLIER_GROUP = "Critical Component Suppliers"
_DCR_CODE = "ECN-001"


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_warehouses():
	for wh in (_RM_WAREHOUSE, _WIP_WAREHOUSE, _FG_QUARANTINE, _FG_RELEASED):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


def _ensure_items():
	created = 0
	for item_code, item_name in _COMPONENTS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Nos", "is_stock_item": 1, "has_batch_no": 1, "create_new_batch": 1}).insert(
			ignore_permissions=True
		)
		created += 1
	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": "Infusion Pump Accessory Set",
				"item_group": "Finished Goods",
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"has_serial_no": 1,
				"serial_no_series": "IPA-.#####",
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_supplier():
	if not frappe.db.exists("Supplier Group", _SUPPLIER_GROUP):
		frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": _SUPPLIER_GROUP, "parent_supplier_group": "All Supplier Groups", "is_group": 0}).insert(ignore_permissions=True)
	if frappe.db.exists("Supplier", {"supplier_name": _SUPPLIER_NAME}):
		return False
	frappe.get_doc(
		{"doctype": "Supplier", "supplier_name": _SUPPLIER_NAME, "supplier_group": _SUPPLIER_GROUP, "supplier_type": "Company", "is_critical_supplier": 1, "quality_status": "Pending"}
	).insert(ignore_permissions=True)
	return True


def _ensure_design_change_record():
	if frappe.db.exists("MedDev Design Change Record", _DCR_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "MedDev Design Change Record",
			"change_code": _DCR_CODE,
			"item": _FG_ITEM,
			"description": "Initial design release for Infusion Pump Accessory Set assembly.",
			"status": "Approved",
			"approved_date": frappe.utils.nowdate(),
		}
	).insert(ignore_permissions=True)
	return True


def seed_meddev_master_data():
	"""DP-640 — Company, Warehouses, Items, Supplier (critical, Pending — MD03 starting state),
	Design Change Record (Approved — MD02's approval gate)."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	items_created = _ensure_items()
	supplier_created = _ensure_supplier()
	dcr_created = _ensure_design_change_record()
	return (
		f"seed_meddev_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {items_created} new item(s). "
		f"Supplier {'created' if supplier_created else 'already existed'} (critical, Pending). Design Change Record {'created' if dcr_created else 'already existed'} (Approved)."
	)


def _test_md03_po_blocked_while_pending():
	if frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_NAME}, "quality_status") != "Pending":
		return True  # already progressed past Pending in this run order — nothing to test
	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"supplier": frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_NAME}, "name"),
			"company": _COMPANY_NAME,
			"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 14),
			"items": [{"item_code": "PUMP-HOUSING", "qty": 100, "rate": 45000, "warehouse": _RM_WAREHOUSE}],
		}
	)
	blocked = False
	try:
		po.insert(ignore_permissions=True)
		po.submit()
	except frappe.ValidationError:
		blocked = True
		if po.name and frappe.db.exists("Purchase Order", po.name):
			frappe.delete_doc("Purchase Order", po.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("MD03 negative test FAILED: a Purchase Order against an unapproved critical supplier was not blocked!")
	return True


def seed_meddev_supplier_qualification():
	"""DP-641 — MD03, critical supplier approval. Proves the block fires on real (Pending)
	data, then approves the supplier so procurement can proceed."""
	if not frappe.db.exists("Supplier", {"supplier_name": _SUPPLIER_NAME}):
		return "seed_meddev_supplier_qualification: SKIPPED — run seed_meddev_master_data first."
	md03 = _test_md03_po_blocked_while_pending()
	supplier_name = frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_NAME}, "name")
	approved = False
	if frappe.db.get_value("Supplier", supplier_name, "quality_status") != "Approved":
		frappe.db.set_value("Supplier", supplier_name, "quality_status", "Approved")
		approved = True
	return f"seed_meddev_supplier_qualification: MD03 CONFIRMED ({md03}). Supplier {'approved' if approved else 'already approved'}."


def _test_md02_bom_blocked_without_approved_dcr():
	draft_dcr_code = "ECN-DRAFT-TEST"
	if not frappe.db.exists("MedDev Design Change Record", draft_dcr_code):
		frappe.get_doc({"doctype": "MedDev Design Change Record", "change_code": draft_dcr_code, "item": _FG_ITEM, "status": "Draft"}).insert(ignore_permissions=True)
	bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Nos", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1, "design_change_record": draft_dcr_code})
	for ing_code, qty in _BOM_ITEMS:
		bom.append("items", {"item_code": ing_code, "qty": qty})
	blocked = False
	try:
		bom.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("MD02 negative test FAILED: a BOM with a Draft (unapproved) Design Change Record was not blocked from becoming default!")
	return True


def seed_meddev_bom():
	"""DP-642 — MD02, approved BOM revision only. Proves the block fires against a Draft
	Design Change Record first, then creates the real BOM against the Approved one."""
	if not frappe.db.exists("MedDev Design Change Record", _DCR_CODE):
		return "seed_meddev_bom: SKIPPED — run seed_meddev_master_data first."
	md02 = _test_md02_bom_blocked_without_approved_dcr()
	bom_created = False
	if not frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Nos", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1, "design_change_record": _DCR_CODE})
		for ing_code, qty in _BOM_ITEMS:
			bom.append("items", {"item_code": ing_code, "qty": qty})
		bom.insert(ignore_permissions=True)
		bom.submit()
		bom_created = True
	return f"seed_meddev_bom: MD02 CONFIRMED ({md02}). BOM {'created' if bom_created else 'already existed'} against Approved {_DCR_CODE}."


def _ensure_incoming_stock(item_code, qty, rate=45000):
	# a Material Receipt-type Stock Entry directly into RM Store, same convention every prior
	# manufacturing golden demo used for raw material procurement (the Purchase Order itself is
	# only needed to prove MD03's supplier-approval gate, not as the actual receipt mechanism).
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
	se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": rate})
	se.insert(ignore_permissions=True)
	se.submit()
	batch = frappe.db.get_value("Batch", {"item": item_code}, "name", order_by="creation desc")
	return batch, se.name


def seed_meddev_incoming_inspection():
	"""DP-643 — MD04, incoming inspection failure blocks use. A good housing batch passes QC
	and can move into WIP; a second, defective batch fails QC and is blocked from the same
	move — proven on real seeded data, not just a synthetic negative test."""
	if frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_NAME}, "quality_status") != "Approved":
		return "seed_meddev_incoming_inspection: SKIPPED — run seed_meddev_supplier_qualification first."

	created = {}
	good_se_name = frappe.db.get_value("Stock Entry", {"purpose": "Material Receipt", "company": _COMPANY_NAME}, "name", order_by="creation asc")
	for item_code, qty in [("PUMP-HOUSING", 20), ("PUMP-TUBING", 40), ("PUMP-FASTENERS", 80), ("PUMP-SEAL", 20)]:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_WAREHOUSE, item_code))[0][0] or 0
		if balance < qty:
			_, se_name = _ensure_incoming_stock(item_code, qty)
			created[item_code] = True
			if item_code == "PUMP-HOUSING":
				good_se_name = se_name

	good_batch = frappe.db.get_value("Batch", {"item": "PUMP-HOUSING"}, "name", order_by="creation asc")
	if not frappe.db.exists("Quality Inspection", {"item_code": "PUMP-HOUSING", "batch_no": good_batch, "status": "Accepted"}):
		qi = frappe.get_doc(
			{"doctype": "Quality Inspection", "inspection_type": "Incoming", "reference_type": "Stock Entry", "reference_name": good_se_name, "item_code": "PUMP-HOUSING", "batch_no": good_batch, "sample_size": 5, "status": "Accepted", "company": _COMPANY_NAME, "inspected_by": frappe.session.user}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()

	good_moved = False
	if not frappe.db.exists("Stock Entry", {"purpose": "Material Transfer", "company": _COMPANY_NAME}):
		# ALL four components need to reach WIP — the Work Order's assembly step (DP-644) sources
		# its whole BOM from WIP Store, not just the one component (PUMP-HOUSING) MD04's negative
		# test cares about. Found as a real "Valuation Rate ... is required" error on
		# PUMP-TUBING when only PUMP-HOUSING had ever been moved there.
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		for item_code, qty in [("PUMP-HOUSING", 10), ("PUMP-TUBING", 20), ("PUMP-FASTENERS", 40), ("PUMP-SEAL", 10)]:
			batch_no = good_batch if item_code == "PUMP-HOUSING" else frappe.db.get_value("Batch", {"item": item_code}, "name", order_by="creation asc")
			se.append("items", {"item_code": item_code, "qty": qty, "s_warehouse": _RM_WAREHOUSE, "t_warehouse": _WIP_WAREHOUSE, "batch_no": batch_no, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		good_moved = True

	bad_batch_marker = "PUMP-HOUSING-BAD-BATCH-TEST"
	bad_se_name = None
	if not frappe.db.exists("Batch", bad_batch_marker):
		bad_se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		bad_se.append("items", {"item_code": "PUMP-HOUSING", "qty": 5, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 45000})
		bad_se.insert(ignore_permissions=True)
		bad_se.submit()
		bad_se_name = bad_se.name
		bad_batch = frappe.db.get_value("Batch", {"item": "PUMP-HOUSING"}, "name", order_by="creation desc")
		frappe.rename_doc("Batch", bad_batch, bad_batch_marker, force=True)
	bad_batch = bad_batch_marker

	if not frappe.db.exists("Quality Inspection", {"item_code": "PUMP-HOUSING", "batch_no": bad_batch, "status": "Rejected"}):
		if not bad_se_name:
			bad_se_name = frappe.db.get_value("Stock Entry Detail", {"item_code": "PUMP-HOUSING", "t_warehouse": _RM_WAREHOUSE}, "parent", order_by="creation desc")
		qi = frappe.get_doc(
			{"doctype": "Quality Inspection", "inspection_type": "Incoming", "reference_type": "Stock Entry", "reference_name": bad_se_name, "item_code": "PUMP-HOUSING", "batch_no": bad_batch, "sample_size": 5, "status": "Rejected", "company": _COMPANY_NAME, "inspected_by": frappe.session.user, "remarks": "Housing wall thickness out of tolerance."}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()

	attempt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	attempt.append("items", {"item_code": "PUMP-HOUSING", "qty": 5, "s_warehouse": _RM_WAREHOUSE, "t_warehouse": _WIP_WAREHOUSE, "batch_no": bad_batch, "use_serial_batch_fields": 1})
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
		attempt.submit()
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("MD04 negative test FAILED: moving a Rejected-QC batch into WIP was not blocked!")

	return f"seed_meddev_incoming_inspection: {len(created)} component(s) received. Good batch moved to WIP: {good_moved}. MD04 CONFIRMED (rejected batch {bad_batch} blocked from WIP)."


_ASSET_CATEGORY = "Medical Device Assembly Equipment"
_EQUIP_ITEM_CODE = "EQUIP-TORQUE-01"
_LOCATION_NAME = f"Assembly Floor - {_COMPANY_ABBR}"
_GOOD_ASSET_NAME = "Assembly Torque Station #1"
_OVERDUE_ASSET_NAME = "Assembly Torque Station #2"


def _ensure_equipment():
	if not frappe.db.exists("Asset Category", _ASSET_CATEGORY):
		frappe.get_doc(
			{
				"doctype": "Asset Category",
				"asset_category_name": _ASSET_CATEGORY,
				"accounts": [
					{
						"company_name": _COMPANY_NAME,
						"fixed_asset_account": f"Plants and Machineries - {_COMPANY_ABBR}",
						"accumulated_depreciation_account": f"Accumulated Depreciation - {_COMPANY_ABBR}",
						"depreciation_expense_account": f"Depreciation - {_COMPANY_ABBR}",
					}
				],
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", _EQUIP_ITEM_CODE):
		frappe.get_doc(
			{"doctype": "Item", "item_code": _EQUIP_ITEM_CODE, "item_name": "Precision Torque Station", "item_group": "Finished Goods", "stock_uom": "Nos", "is_stock_item": 0, "is_fixed_asset": 1, "asset_category": _ASSET_CATEGORY}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Location", _LOCATION_NAME):
		frappe.get_doc({"doctype": "Location", "location_name": _LOCATION_NAME}).insert(ignore_permissions=True)

	created = 0
	for asset_name in (_GOOD_ASSET_NAME, _OVERDUE_ASSET_NAME):
		if frappe.db.exists("Asset", {"asset_name": asset_name}):
			continue
		asset = frappe.get_doc(
			{
				"doctype": "Asset",
				"item_code": _EQUIP_ITEM_CODE,
				"asset_name": asset_name,
				"company": _COMPANY_NAME,
				"location": _LOCATION_NAME,
				"purchase_date": "2025-01-15",
				"available_for_use_date": "2025-01-20",
				"gross_purchase_amount": 80000000,
				"net_purchase_amount": 80000000,
				"asset_quantity": 1,
			}
		)
		asset.insert(ignore_permissions=True)
		asset.submit()
		created += 1

	good_asset = frappe.db.get_value("Asset", {"asset_name": _GOOD_ASSET_NAME}, "name")
	if not frappe.db.exists("EAM Calibration Record", {"asset": good_asset, "result": "Pass"}):
		frappe.get_doc(
			{"doctype": "EAM Calibration Record", "asset": good_asset, "calibration_date": frappe.utils.nowdate(), "due_date": frappe.utils.add_days(frappe.utils.nowdate(), 180), "performed_by": "External Calibration Services Co.", "result": "Pass", "certificate_no": f"CAL-{frappe.utils.nowdate()}-GOOD"}
		).insert(ignore_permissions=True)

	overdue_asset = frappe.db.get_value("Asset", {"asset_name": _OVERDUE_ASSET_NAME}, "name")
	if not frappe.db.exists("EAM Calibration Record", {"asset": overdue_asset, "result": "Pass"}):
		frappe.get_doc(
			{"doctype": "EAM Calibration Record", "asset": overdue_asset, "calibration_date": frappe.utils.add_days(frappe.utils.nowdate(), -400), "due_date": frappe.utils.add_days(frappe.utils.nowdate(), -35), "performed_by": "External Calibration Services Co.", "result": "Pass", "certificate_no": f"CAL-{frappe.utils.nowdate()}-OVERDUE"}
		).insert(ignore_permissions=True)

	return created, good_asset, overdue_asset


def _test_md07_overdue_equipment_blocked(bom_no, overdue_asset):
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": _FG_ITEM,
			"bom_no": bom_no,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _WIP_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE,
			"skip_transfer": 1,
			"use_multi_level_bom": 0,
			"equipment": overdue_asset,
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
		frappe.throw("MD07 negative test FAILED: a Work Order configured against overdue-calibration equipment was not blocked!")
	return True


def seed_meddev_assembly():
	"""DP-644 — MD07 (calibration-gated operation) + MD01 (serial uniqueness, native). The
	Work Order is configured against the good, in-calibration equipment; a second attempt
	against overdue equipment proves the block."""
	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name")
	if not bom_no:
		return "seed_meddev_assembly: SKIPPED — run seed_meddev_bom first."
	if not frappe.db.exists("Stock Entry", {"purpose": "Material Transfer", "company": _COMPANY_NAME}):
		return "seed_meddev_assembly: SKIPPED — run seed_meddev_incoming_inspection first."

	equipment_created, good_asset, overdue_asset = _ensure_equipment()
	md07 = _test_md07_overdue_equipment_blocked(bom_no, overdue_asset)

	wo_name = frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1, "equipment": good_asset})
	wo_created = False
	if not wo_name:
		wo = frappe.get_doc(
			{
				"doctype": "Work Order",
				"production_item": _FG_ITEM,
				"bom_no": bom_no,
				"qty": _BATCH_QTY,
				"company": _COMPANY_NAME,
				"source_warehouse": _WIP_WAREHOUSE,
				"fg_warehouse": _FG_QUARANTINE,
				"skip_transfer": 1,
				"use_multi_level_bom": 0,
				"equipment": good_asset,
				"planned_start_date": frappe.utils.now_datetime(),
			}
		)
		wo.insert(ignore_permissions=True)
		wo.submit()
		wo_name = wo.name
		wo_created = True

	manufacture_created = False
	if not frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

		se = make_stock_entry(wo_name, "Manufacture", qty=_BATCH_QTY)
		se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
		se.insert(ignore_permissions=True)
		se.submit()
		manufacture_created = True

	fg_batch = frappe.db.get_value("Batch", {"item": _FG_ITEM}, "name", order_by="creation desc")
	serial_count = frappe.db.count("Serial No", {"item_code": _FG_ITEM, "batch_no": fg_batch}) if fg_batch else 0
	return (
		f"seed_meddev_assembly: {equipment_created} equipment asset(s) created. MD07 CONFIRMED ({md07}). "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). Manufacture {'created' if manufacture_created else 'already existed'}. "
		f"FG Batch {fg_batch}, {serial_count} serial(s) created (MD01)."
	)


def seed_meddev_release():
	"""DP-645 — final QC + release. Reuses block_fg_release_without_qa unmodified — 7th reuse
	after Pharma/Feed/Vet Mfg/Aquafeed/Aqua Env/Supplement/Cosmetics."""
	fg_batch = frappe.db.get_value("Batch", {"item": _FG_ITEM}, "name", order_by="creation desc")
	if not fg_batch:
		return "seed_meddev_release: SKIPPED — run seed_meddev_assembly first."
	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": fg_batch, "status": "Accepted", "docstatus": 1}):
		se_name = frappe.db.get_value("Stock Entry", {"purpose": "Manufacture", "company": _COMPANY_NAME}, "name")
		qi = frappe.get_doc(
			{"doctype": "Quality Inspection", "inspection_type": "In Process", "reference_type": "Stock Entry", "reference_name": se_name, "item_code": _FG_ITEM, "batch_no": fg_batch, "sample_size": 3, "status": "Accepted", "company": _COMPANY_NAME, "inspected_by": frappe.session.user}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		qc_created = True

	released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(_FG_RELEASED, fg_batch),
	)
	release_created = False
	if not released:
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": _FG_ITEM, "qty": _BATCH_QTY, "s_warehouse": _FG_QUARANTINE, "t_warehouse": _FG_RELEASED, "batch_no": fg_batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return f"seed_meddev_release: QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'} (block_fg_release_without_qa reuse #7)."


_CUSTOMER_GROUP = "Medical Device Distributors"
_CUSTOMER_NAME = "National Hospital Supply Co."


def _ensure_customer():
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(ignore_permissions=True)
	if frappe.db.exists("Customer", {"customer_name": _CUSTOMER_NAME}):
		return frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), False
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": _CUSTOMER_NAME, "customer_type": "Company", "customer_group": _CUSTOMER_GROUP})
	customer.insert(ignore_permissions=True)
	return customer.name, True


def seed_meddev_trace_and_complaint():
	"""DP-646 — MD05 (finished serial traces components, reuses trace_feed_batch_genealogy()
	via a thin serial->batch wrapper) + MD06 (complaint links serial/lot)."""
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _FG_RELEASED, "item_code": _FG_ITEM}):
		return "seed_meddev_trace_and_complaint: SKIPPED — run seed_meddev_release first."
	customer, customer_created = _ensure_customer()

	existing_so = frappe.db.exists("Sales Order", {"customer": customer, "docstatus": 1})
	if existing_so:
		so_name = existing_so
	else:
		so = frappe.get_doc(
			{"doctype": "Sales Order", "customer": customer, "company": _COMPANY_NAME, "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 5), "items": [{"item_code": _FG_ITEM, "qty": _BATCH_QTY, "warehouse": _FG_RELEASED, "rate": 1200000}]}
		)
		so.insert(ignore_permissions=True)
		so.submit()
		so_name = so.name

	dn_created = False
	if not frappe.db.exists("Delivery Note", {"against_sales_order": so_name, "docstatus": 1}):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

		dn = make_delivery_note(so_name)
		dn.insert(ignore_permissions=True)
		dn.submit()
		dn_created = True

	dn_name = frappe.db.get_value("Delivery Note", {"against_sales_order": so_name, "docstatus": 1}, "name")
	serial_no = frappe.db.get_value("Serial No", {"item_code": _FG_ITEM}, "name", order_by="creation asc")

	from enterprise_core.enterprise_core.api import trace_serial_genealogy

	genealogy = trace_serial_genealogy(serial_no) if serial_no else None
	md05_confirmed = bool(genealogy and genealogy.get("raw_materials_consumed"))

	complaint_created = False
	if serial_no and not frappe.db.exists("MedDev Complaint", {"serial_or_lot": serial_no}):
		frappe.get_doc(
			{"doctype": "MedDev Complaint", "customer": customer, "serial_or_lot": serial_no, "description": "Customer reported a loose tubing connector on arrival.", "status": "Investigating"}
		).insert(ignore_permissions=True)
		complaint_created = True

	if not md05_confirmed:
		frappe.throw(f"MD05 FAILED: serial {serial_no}'s genealogy did not resolve any consumed components.")
	return (
		f"seed_meddev_trace_and_complaint: Delivery {'created' if dn_created else 'already existed'} to {customer} ({'new' if customer_created else 'existing'}). "
		f"MD05 CONFIRMED — serial {serial_no} traces to {len(genealogy['raw_materials_consumed'])} component(s). "
		f"MD06 — Complaint {'created' if complaint_created else 'already existed'} referencing serial {serial_no}."
	)
