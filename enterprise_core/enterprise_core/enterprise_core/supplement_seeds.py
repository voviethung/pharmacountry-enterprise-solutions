"""Golden Demo #20 — Supplement / Nutraceutical Manufacturing (master plan DEMO 02, "PHASE 6"
item 1), IP-SUPPLEMENT. Reuses ERPNext's manufacturing module (BOM=Formula, Stock Entry, Work
Order, Quality Inspection) exactly as Golden Demo #1/#7/#9/#15/#16 did, including the SAME
generic `block_fg_release_without_qa` hook (6th reuse) and the `contains_allergen` Custom Field
Feed Manufacturing already added to Item (S02) — no new Custom Field needed this time.
"""

import frappe

_COMPANY_NAME = "Demo Supplement Co."
_COMPANY_ABBR = "DSC"
_RM_WAREHOUSE = f"RM Store - {_COMPANY_ABBR}"
_FG_QUARANTINE_WAREHOUSE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED_WAREHOUSE = f"FG Released - {_COMPANY_ABBR}"
_BATCH_QTY = 1000

_FG_ITEM = "VITC-1000-EFF"
_FG_NAME = "Vitamin C 1000mg Effervescent Tablet"
_RAW_MATERIALS = [
	("ASCORBIC-ACID", "Ascorbic Acid (Vitamin C)"),
	("CITRIC-ACID", "Citric Acid"),
	("SODIUM-BICARB", "Sodium Bicarbonate"),
	("SORBITOL", "Sorbitol"),
	("SOY-LECITHIN", "Soy Lecithin"),  # allergen source — S02
	("ORANGE-FLAVOR", "Orange Flavor"),
]
_FORMULA_V1 = [("ASCORBIC-ACID", 400), ("CITRIC-ACID", 200), ("SODIUM-BICARB", 250), ("SORBITOL", 100), ("SOY-LECITHIN", 20), ("ORANGE-FLAVOR", 30)]
_FORMULA_V2 = [("ASCORBIC-ACID", 400), ("CITRIC-ACID", 200), ("SODIUM-BICARB", 250), ("SORBITOL", 110), ("SOY-LECITHIN", 10), ("ORANGE-FLAVOR", 30)]  # reduced soy lecithin


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
		frappe.get_doc(
			{"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1, "contains_allergen": 1 if item_code == "SOY-LECITHIN" else 0}
		).insert(ignore_permissions=True)
		created += 1
	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": _FG_NAME,
				"item_group": "Finished Goods",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"has_expiry_date": 1,
				"shelf_life_in_days": 730,
				"contains_allergen": 1,  # formula includes Soy Lecithin — S02
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


def seed_supplement_master_data():
	"""DP-624 — Company, Warehouses, Items (S02: contains_allergen correctly flagged from the
	formula's own Soy Lecithin ingredient, has_expiry_date + shelf_life_in_days for S04),
	Formula v1."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	items_created = _ensure_items()
	formula_created = _ensure_formula(_FORMULA_V1)
	return f"seed_supplement_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {items_created} new item(s). Formula v1 {'created' if formula_created else 'already existed'}."


def _ensure_rm_stock():
	created = False
	for item_code, qty in [("ASCORBIC-ACID", 400), ("CITRIC-ACID", 200), ("SODIUM-BICARB", 250), ("SORBITOL", 110), ("SOY-LECITHIN", 20), ("ORANGE-FLAVOR", 30)]:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_WAREHOUSE, item_code))[0][0] or 0
		if balance >= qty:
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 95000})
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


def seed_supplement_production():
	"""DP-625 — production + release (reuses block_fg_release_without_qa unmodified — 6th
	reuse after Pharma/Feed/Vet Mfg/Aquafeed/Aqua Env) + S04 (batch expiry computed from
	Item.shelf_life_in_days, native ERPNext behavior)."""
	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name")
	if not bom_no:
		return "seed_supplement_production: SKIPPED — run seed_supplement_master_data first."
	rm_received = _ensure_rm_stock()
	wo_name, wo_created = _ensure_work_order(bom_no)
	manufacture_created = _ensure_manufacture(wo_name)
	batch, qc_created, release_created = _ensure_qc_and_release(wo_name)
	expiry_date = frappe.db.get_value("Batch", batch, "expiry_date") if batch else None
	return (
		f"seed_supplement_production: RM stock {'received' if rm_received else 'already present'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). Manufacture {'created' if manufacture_created else 'already existed'}. "
		f"Batch {batch}, S04 expiry_date {expiry_date}. QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'}."
	)


def seed_supplement_formula_revision():
	"""DP-626 — S01, formula revision does not change the already-created batch. Same
	is_default-flip pattern as Vet Mfg's VPM02 / Aqua Env's AE01 — the v1 batch is legitimate
	production history by the time this runs."""
	if not frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}):
		return "seed_supplement_formula_revision: SKIPPED — run seed_supplement_production first."
	if frappe.db.count("BOM", {"item": _FG_ITEM}) >= 2:
		return "seed_supplement_formula_revision: already revised (2+ BOM versions exist)."
	old_bom = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, "name", order_by="creation asc")
	old_bom_items_before = frappe.get_all("BOM Item", filters={"parent": old_bom}, fields=["item_code", "qty"], order_by="item_code")
	frappe.db.set_value("BOM", old_bom, "is_default", 0)
	new_bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, qty in _FORMULA_V2:
		new_bom.append("items", {"item_code": ing_code, "qty": qty})
	new_bom.insert(ignore_permissions=True)
	new_bom.submit()
	old_bom_items_after = frappe.get_all("BOM Item", filters={"parent": old_bom}, fields=["item_code", "qty"], order_by="item_code")
	unchanged = old_bom_items_before == old_bom_items_after
	if not unchanged:
		frappe.throw(f"S01 FAILED: revising the formula changed BOM {old_bom}'s own recorded items — it should stay untouched as production history.")
	return f"seed_supplement_formula_revision: S01 CONFIRMED — {old_bom} kept Active and UNCHANGED as history, new version {new_bom.name} is now default."


_ARTWORK_DOC_NAME = f"ARTWORK-{_FG_ITEM}"


def _ensure_artwork_document():
	if frappe.db.exists("DMS Document Version", {"document": _ARTWORK_DOC_NAME, "status": "Effective"}):
		return False
	if not frappe.db.exists("DMS Document", _ARTWORK_DOC_NAME):
		frappe.get_doc(
			{"doctype": "DMS Document", "document_code": _ARTWORK_DOC_NAME, "title": f"Packaging Artwork — {_FG_ITEM}", "doc_type": "Artwork", "status": "Draft", "requires_training": 0}
		).insert(ignore_permissions=True)
	v1 = frappe.get_doc(
		{"doctype": "DMS Document Version", "document": _ARTWORK_DOC_NAME, "version_no": 1, "status": "Draft", "content_summary": "Front/back carton artwork, matches product formula v1 label claims."}
	)
	v1.insert(ignore_permissions=True)
	v1.status = "Approved"
	v1.approved_by = "quality.director@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Effective"
	v1.effective_date = frappe.utils.nowdate()
	v1.save(ignore_permissions=True)
	return True


def seed_supplement_artwork():
	"""DP-627 — S03, artwork version. Reuses Golden Demo #4's whole DMS Document/DMS Document
	Version lifecycle (doc_type="Artwork", the option this demo's own bootstrap added) — exact
	same pattern as Vet Mfg's Label / Aqua Env's Label."""
	if not frappe.db.exists("Item", _FG_ITEM):
		return "seed_supplement_artwork: SKIPPED — run seed_supplement_master_data first."
	created = _ensure_artwork_document()
	return f"seed_supplement_artwork: S03 {'CONFIRMED — artwork document created and reached Effective' if created else 'already existed (Effective)'}."


_LIMS_SPEC_CODE = "SPEC-VITC-1000-EFF"
_LIMS_METHOD_CODE = "MTD-TITRATION-VITC"
_LIMS_INSTRUMENT = "HPLC-01"  # reused from Golden Demo #5 — generic lab equipment, not pharma-specific
_ANALYST = "analyst@pharmacountry.vn"
_REVIEWER = "qc.manager@pharmacountry.vn"


def _ensure_lims_spec_and_method():
	spec_created = False
	if not frappe.db.exists("LIMS Specification", {"item_name": _FG_NAME, "status": "Effective"}):
		frappe.get_doc(
			{
				"doctype": "LIMS Specification",
				"spec_code": _LIMS_SPEC_CODE,
				"item_name": _FG_NAME,
				"version_no": 1,
				"status": "Effective",
				"parameters": [{"parameter_name": "Vitamin C Content", "unit": "mg/tablet", "min_value": 950.0, "max_value": 1050.0}],
			}
		).insert(ignore_permissions=True)
		spec_created = True
	method_created = False
	if not frappe.db.exists("LIMS Test Method", {"method_code": _LIMS_METHOD_CODE, "status": "Effective"}):
		frappe.get_doc({"doctype": "LIMS Test Method", "method_code": _LIMS_METHOD_CODE, "method_name": "Iodometric Titration — Vitamin C Content", "instrument_type": "Titrator", "status": "Effective"}).insert(
			ignore_permissions=True
		)
		method_created = True
	return spec_created, method_created


def seed_supplement_coa():
	"""DP-628 — S05, COA generated from approved results. Reuses Golden Demo #5's full LIMS
	Sample -> Test -> Approved -> LIMS COA chain unmodified, including the shared HPLC-01
	instrument and demo analyst/reviewer accounts."""
	batch = frappe.db.get_value("Batch", {"item": _FG_ITEM, "batch_qty": [">", 0]}, "name")
	if not batch:
		return "seed_supplement_coa: SKIPPED — run seed_supplement_production first."
	_ensure_lims_spec_and_method()

	sample_name = frappe.db.get_value("LIMS Sample", {"batch_reference": batch, "item_name": _FG_NAME}, "name")
	if not sample_name:
		sample = frappe.get_doc({"doctype": "LIMS Sample", "item_name": _FG_NAME, "batch_reference": batch, "sample_type": "Finished Goods", "received_date": frappe.utils.nowdate(), "status": "Assigned"})
		sample.insert(ignore_permissions=True)
		sample_name = sample.name

	test_name = frappe.db.get_value("LIMS Test", {"sample": sample_name}, "name")
	if not test_name or frappe.db.get_value("LIMS Test", test_name, "status") != "Approved":
		spec = frappe.db.get_value("LIMS Specification", {"item_name": _FG_NAME, "status": "Effective"}, "name")
		method = frappe.db.get_value("LIMS Test Method", {"method_code": _LIMS_METHOD_CODE, "status": "Effective"}, "name")
		if test_name:
			test = frappe.get_doc("LIMS Test", test_name)
		else:
			test = frappe.get_doc(
				{
					"doctype": "LIMS Test",
					"sample": sample_name,
					"specification": spec,
					"method": method,
					"instrument": _LIMS_INSTRUMENT,
					"analyst": _ANALYST,
					"status": "In Progress",
					"results": [{"parameter_name": "Vitamin C Content", "result_value": 1002.0, "unit": "mg/tablet"}],
				}
			)
			test.insert(ignore_permissions=True)
		test.status = "Result Entered"
		test.save(ignore_permissions=True)
		test.status = "Reviewed"
		test.reviewed_by = _REVIEWER
		test.save(ignore_permissions=True)
		test.status = "Approved"
		test.approved_by = _REVIEWER
		test.save(ignore_permissions=True)
		test_name = test.name

	coa_name = frappe.db.get_value("LIMS COA", {"test": test_name}, "name")
	if not coa_name:
		coa = frappe.get_doc({"doctype": "LIMS COA", "batch_reference": batch, "test": test_name, "status": "Draft"})
		coa.insert(ignore_permissions=True)
		coa.status = "Approved"
		coa.issued_date = frappe.utils.nowdate()
		coa.save(ignore_permissions=True)
		coa_name = coa.name

	return f"seed_supplement_coa: S05 CONFIRMED — COA {coa_name} generated from Approved LIMS Test {test_name} for batch {batch}."


_CUSTOMER_GROUP = "Pharmacy Chains"  # reused from Golden Demo #2 — same real-world buyer type for OTC supplements
_CUSTOMER_NAME = "VitaHealth Pharmacy Chain"


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


def seed_supplement_distribution():
	"""DP-629 — S06, traceability ingredient -> lots -> customers. Reuses
	trace_feed_batch_genealogy() (ingredient -> batch, unmodified) and
	trace_batch_to_customers() (batch -> customer, unmodified) — zero new query logic."""
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _FG_RELEASED_WAREHOUSE, "item_code": _FG_ITEM}):
		return "seed_supplement_distribution: SKIPPED — run seed_supplement_production first."
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
				"items": [{"item_code": _FG_ITEM, "qty": 50, "warehouse": _FG_RELEASED_WAREHOUSE, "rate": 280000}],
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

	from enterprise_core.enterprise_core.api import trace_batch_to_customers, trace_feed_batch_genealogy

	genealogy = trace_feed_batch_genealogy(batch) if batch else None
	customers = trace_batch_to_customers(batch) if batch else []
	dealer_found = any(row.get("customer") == customer for row in customers)
	ingredients_found = bool(genealogy and genealogy.get("raw_materials_consumed"))
	if not (dealer_found and ingredients_found):
		frappe.throw(f"S06 FAILED: batch {batch}'s traceability incomplete — ingredients resolved={ingredients_found}, customer traced={dealer_found}.")
	return f"seed_supplement_distribution: S06 CONFIRMED — batch {batch} traces from {len(genealogy['raw_materials_consumed'])} ingredient(s) to dealer {customer} ({'new' if customer_created else 'existing'}). Delivery {'created' if dn_created else 'already existed'}."
