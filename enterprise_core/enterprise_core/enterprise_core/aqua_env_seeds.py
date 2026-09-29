"""Golden Demo #16 — Aquaculture Environmental Product Manufacturing (master plan DEMO 27,
"PHASE 5" item 2), IP-AQUA-ENVIRONMENT. The leanest golden demo yet: **zero new DocTypes,
zero new Custom Fields**. Every AE0x test is satisfied by pure reuse:
- AE01 (formula revision) — native BOM, same is_default-flip pattern as Vet Mfg's VPM02 (the
  batch already produced with v1 is legitimate history, not a bug being corrected).
- AE02 (batch/lot) — native Item.has_batch_no.
- AE03 (QC) — native Quality Inspection.
- AE04 (label version) — Golden Demo #4's whole DMS Document/DMS Document Version lifecycle
  with doc_type="Label" (the option Golden Demo #9 already added — no new bootstrap needed).
- AE05 (release) — `block_fg_release_without_qa`, unmodified (5th reuse, after
  Pharma/Feed/Vet Mfg/Aquafeed).
- AE06 (distribution trace) — Golden Demo #2's `trace_batch_to_customers()`, unmodified (2nd
  reuse, after Vet Distribution's VD06).
"""

import frappe

_COMPANY_NAME = "Demo Aqua Environment Co."
_COMPANY_ABBR = "DAE"
_RM_WAREHOUSE = f"RM Store - {_COMPANY_ABBR}"
_FG_QUARANTINE_WAREHOUSE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED_WAREHOUSE = f"FG Released - {_COMPANY_ABBR}"
_BATCH_QTY = 100

_FG_ITEM = "AQUA-PROBIOTIC-BS500"
_RAW_MATERIALS = [("BACILLUS-CULTURE", "Bacillus subtilis Culture"), ("CARRIER-MALTODEXTRIN", "Carrier - Maltodextrin"), ("MINERAL-MIX-AQUA", "Mineral Mix (Aquaculture)")]
_FORMULA_V1 = [("BACILLUS-CULTURE", 20), ("CARRIER-MALTODEXTRIN", 70), ("MINERAL-MIX-AQUA", 10)]
_FORMULA_V2 = [("BACILLUS-CULTURE", 25), ("CARRIER-MALTODEXTRIN", 65), ("MINERAL-MIX-AQUA", 10)]  # higher CFU concentration


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


def _ensure_items():
	created = 0
	for item_code, item_name in _RAW_MATERIALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}).insert(
			ignore_permissions=True
		)
		created += 1
	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": "Aqua Probiotic (Bacillus subtilis) 500g",
				"item_group": "Finished Goods",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_formula(ingredients):
	if frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		return False
	bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, qty in ingredients:
		bom.append("items", {"item_code": ing_code, "qty": qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_aqua_env_master_data():
	"""DP-600 — Company, Warehouses, Items, Formula v1."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	items_created = _ensure_items()
	formula_created = _ensure_formula(_FORMULA_V1)
	return f"seed_aqua_env_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {items_created} new item(s). Formula v1 {'created' if formula_created else 'already existed'}."


def _ensure_rm_stock():
	created = False
	for item_code, qty in [("BACILLUS-CULTURE", 25), ("CARRIER-MALTODEXTRIN", 70), ("MINERAL-MIX-AQUA", 10)]:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_WAREHOUSE, item_code))[0][0] or 0
		if balance >= qty:
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 180000})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _ensure_work_order(bom_no):
	existing = frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1})
	if existing:
		return existing, False
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": _FG_ITEM,
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


def _ensure_qc_and_release(wo_name):
	batch = frappe.db.get_value("Batch", {"item": _FG_ITEM, "batch_qty": [">", 0]}, "name")
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
				"item_code": _FG_ITEM,
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
		se.append("items", {"item_code": _FG_ITEM, "qty": _BATCH_QTY, "s_warehouse": _FG_QUARANTINE_WAREHOUSE, "t_warehouse": _FG_RELEASED_WAREHOUSE, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qc_created, release_created


def seed_aqua_env_production():
	"""DP-601 — AE02 (batch/lot), AE03 (QC), AE05 (release, reuses block_fg_release_without_qa
	unmodified — 5th reuse after Pharma/Feed/Vet Mfg/Aquafeed)."""
	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name")
	if not bom_no:
		return "seed_aqua_env_production: SKIPPED — run seed_aqua_env_master_data first."
	rm_received = _ensure_rm_stock()
	wo_name, wo_created = _ensure_work_order(bom_no)
	manufacture_created = _ensure_manufacture(wo_name)
	batch, qc_created, release_created = _ensure_qc_and_release(wo_name)
	return (
		f"seed_aqua_env_production: RM stock {'received' if rm_received else 'already present'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). Manufacture {'created' if manufacture_created else 'already existed'}. "
		f"Batch {batch} (AE02). QC {'created' if qc_created else 'already existed'} (AE03). Release {'created' if release_created else 'already existed'} (AE05)."
	)


def seed_aqua_env_formula_revision():
	"""DP-602 — AE01, formula revision. Same is_default-flip pattern as Vet Mfg's VPM02 (not
	the DP-504/F01 cancel pattern) — the v1 batch was already produced and released before this
	runs, so it's legitimate production history, not a bug being corrected; ERPNext would
	refuse to cancel a BOM still linked to a submitted Work Order anyway."""
	if not frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}):
		return "seed_aqua_env_formula_revision: SKIPPED — run seed_aqua_env_production first."
	if frappe.db.count("BOM", {"item": _FG_ITEM}) >= 2:
		return "seed_aqua_env_formula_revision: already revised (2+ BOM versions exist)."
	old_bom = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name", order_by="creation asc")
	frappe.db.set_value("BOM", old_bom, "is_default", 0)
	new_bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, qty in _FORMULA_V2:
		new_bom.append("items", {"item_code": ing_code, "qty": qty})
	new_bom.insert(ignore_permissions=True)
	new_bom.submit()
	return f"seed_aqua_env_formula_revision: AE01 CONFIRMED — {old_bom} kept Active as history (is_default=0), new version {new_bom.name} is now default."


_LABEL_DOC_NAME = f"LABEL-{_FG_ITEM}"


def _ensure_label_document():
	if frappe.db.exists("DMS Document Version", {"document": _LABEL_DOC_NAME, "status": "Effective"}):
		return False
	if not frappe.db.exists("DMS Document", _LABEL_DOC_NAME):
		frappe.get_doc(
			{"doctype": "DMS Document", "document_code": _LABEL_DOC_NAME, "title": f"Product Label — {_FG_ITEM}", "doc_type": "Label", "status": "Draft", "requires_training": 0}
		).insert(ignore_permissions=True)
	v1 = frappe.get_doc(
		{"doctype": "DMS Document Version", "document": _LABEL_DOC_NAME, "version_no": 1, "status": "Draft", "content_summary": "Probiotic water treatment — dosage 2g/m3 pond water, apply weekly. Store in a cool, dry place."}
	)
	v1.insert(ignore_permissions=True)
	v1.status = "Approved"
	v1.approved_by = "quality.director@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Effective"
	v1.effective_date = frappe.utils.nowdate()
	v1.save(ignore_permissions=True)
	return True


def seed_aqua_env_label():
	"""DP-603 — AE04, label version. Reuses Golden Demo #4's whole DMS Document/DMS Document
	Version lifecycle (doc_type="Label", the option Golden Demo #9 already added) — a "Label"
	document reaches Effective through the same D01/D02/D04/D06-enforced lifecycle, exact same
	pattern as Vet Mfg's seed_vet_mfg_label(), zero new validation logic."""
	if not frappe.db.exists("Item", _FG_ITEM):
		return "seed_aqua_env_label: SKIPPED — run seed_aqua_env_master_data first."
	created = _ensure_label_document()
	return f"seed_aqua_env_label: AE04 {'CONFIRMED — label document created and reached Effective' if created else 'already existed (Effective)'}."


_CUSTOMER_GROUP = "Aquaculture Input Dealers"
_CUSTOMER_NAME = "Mekong Aqua Supplies Co."


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


def seed_aqua_env_distribution():
	"""DP-604 — AE06, distribution trace. Reuses Golden Demo #2's trace_batch_to_customers()
	unmodified — 2nd reuse after Vet Distribution's VD06."""
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _FG_RELEASED_WAREHOUSE, "item_code": _FG_ITEM}):
		return "seed_aqua_env_distribution: SKIPPED — run seed_aqua_env_production first."
	customer, customer_created = _ensure_customer()

	existing_so = frappe.db.exists("Sales Order", {"customer": customer, "docstatus": 1})
	if existing_so:
		so_name = existing_so
	else:
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer,
				"company": _COMPANY_NAME,
				"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 5),
				"items": [{"item_code": _FG_ITEM, "qty": 20, "warehouse": _FG_RELEASED_WAREHOUSE, "rate": 350000}],
			}
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
	batch = frappe.db.get_value("Delivery Note Item", {"parent": dn_name, "item_code": _FG_ITEM}, "batch_no")
	from enterprise_core.enterprise_core.api import trace_batch_to_customers

	traced = trace_batch_to_customers(batch) if batch else []
	dealer_found = any(row.get("customer") == customer for row in traced)
	if not dealer_found:
		frappe.throw(f"AE06 FAILED: batch {batch}'s distribution did not trace to dealer {customer}.")
	return f"seed_aqua_env_distribution: AE06 CONFIRMED — batch {batch}'s distribution traces to dealer {customer} ({'new' if customer_created else 'existing'}). Delivery {'created' if dn_created else 'already existed'}."
