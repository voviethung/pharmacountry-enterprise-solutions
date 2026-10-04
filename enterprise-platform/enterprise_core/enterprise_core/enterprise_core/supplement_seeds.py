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


# ---------------------------------------------------------------------------
# Catalog expansion (P2 post-launch reviewer fix, NOT a master-plan DP item) —
# widening WEB-01 (catalog.pharmacountry.vn) / WEB-05 (shop.pharmacountry.vn) /
# WEB-02 (brand.pharmacountry.vn) beyond the single VITC-1000-EFF flagship, which a
# reviewer correctly flagged as making the public sites look too thin to be a real
# business. Adds 5 new REAL supplement products, each a real Item with a real
# Formula (BOM) on file — never a cosmetic-only label. Two of them
# (VITD3-1000-SG, ZINC-50-TAB) are additionally taken through the FULL real
# production -> QC -> LIMS COA pipeline (identical depth to VITC-1000-EFF's own
# DP-625/DP-628) to become WEB-02 brand-site flagship SKUs #2/#3 (reviewer's own
# suggested 3-5 SKU range). The other 3 (MULTIVIT-COMP-TAB, OMEGA3-1000-SG,
# PROBIOTIC-10B-CAP) get a real Item + real Formula but no production run of
# their own here — their real public stock/price is established downstream by
# Demo Consumer Distribution Co.'s own Material Receipt
# (consumer_dist_seeds.py's seed_consumer_dist_catalog_expansion()), the exact
# same "distributor receives a finished good it didn't itself manufacture"
# pattern the golden demo already established for VITC-1000-EFF/
# FACIAL-CLEANSER-150ML — not a shortcut invented for this fix.
# ---------------------------------------------------------------------------

_NEW_RAW_MATERIALS = [
	("VIT-D3-CONCENTRATE", "Cholecalciferol (Vitamin D3) Concentrate"),
	("SOYBEAN-OIL", "Soybean Oil"),
	("GELATIN", "Gelatin (Softgel Shell)"),
	("ZINC-GLUCONATE", "Zinc Gluconate"),
	("MCC", "Microcrystalline Cellulose"),
	("MAG-STEARATE", "Magnesium Stearate"),
	("VIT-B-COMPLEX", "Vitamin B-Complex Blend"),
	("FISH-OIL-CONCENTRATE", "Fish Oil Concentrate (Omega-3)"),
	("VIT-E-TOCOPHEROL", "Vitamin E (Mixed Tocopherols)"),
	("PROBIOTIC-BLEND", "Probiotic Blend (Lactobacillus/Bifidobacterium)"),
	("MALTODEXTRIN", "Maltodextrin"),
	("VEG-CAPSULE-SHELL", "Vegetable Capsule Shell (HPMC)"),
]

# GLYCERIN and ASCORBIC-ACID are reused directly from this same module's existing raw
# materials/Cosmetics' GLYCERIN — Item is not company-scoped.
_NEW_PRODUCTS = {
	"VITD3-1000-SG": {
		"name": "Vitamin D3 1000 IU Softgel",
		"shelf_life": 1095,
		"batch_qty": 500,
		"formula": [("VIT-D3-CONCENTRATE", 5), ("SOYBEAN-OIL", 450), ("GELATIN", 40), ("GLYCERIN", 5)],
		"flagship": True,
	},
	"ZINC-50-TAB": {
		"name": "Zinc Gluconate 50mg Tablet",
		"shelf_life": 1095,
		"batch_qty": 300,
		"formula": [("ZINC-GLUCONATE", 30), ("MCC", 250), ("MAG-STEARATE", 20)],
		"flagship": True,
	},
	"MULTIVIT-COMP-TAB": {
		"name": "Multivitamin Complex Tablet",
		"shelf_life": 1095,
		"batch_qty": 400,
		"formula": [("ASCORBIC-ACID", 60), ("VIT-D3-CONCENTRATE", 2), ("ZINC-GLUCONATE", 15), ("VIT-B-COMPLEX", 23), ("MCC", 300)],
		"flagship": False,
	},
	"OMEGA3-1000-SG": {
		"name": "Omega-3 Fish Oil 1000mg Softgel",
		"shelf_life": 1095,
		"batch_qty": 500,
		"formula": [("FISH-OIL-CONCENTRATE", 420), ("GELATIN", 60), ("GLYCERIN", 15), ("VIT-E-TOCOPHEROL", 5)],
		"flagship": False,
	},
	"PROBIOTIC-10B-CAP": {
		"name": "Probiotic 10 Billion CFU Capsule",
		"shelf_life": 730,
		"batch_qty": 250,
		"formula": [("PROBIOTIC-BLEND", 10), ("MALTODEXTRIN", 220), ("VEG-CAPSULE-SHELL", 20)],
		"flagship": False,
	},
}

_FLAGSHIP_LIMS = {
	"VITD3-1000-SG": {
		"spec_code": "SPEC-VITD3-1000-SG",
		"method_code": "MTD-HPLC-VITD3",
		"method_name": "HPLC Assay — Vitamin D3 Content",
		"parameter": "Vitamin D3 Content",
		"unit": "IU/softgel",
		"min_value": 950.0,
		"max_value": 1050.0,
		"result_value": 1005.0,
	},
	"ZINC-50-TAB": {
		"spec_code": "SPEC-ZINC-50-TAB",
		"method_code": "MTD-TITRATION-ZINC",
		"method_name": "Complexometric Titration — Zinc Content",
		"parameter": "Zinc Content",
		"unit": "mg/tablet",
		"min_value": 47.5,
		"max_value": 52.5,
		"result_value": 50.2,
	},
}


def _ensure_new_raw_materials():
	created = 0
	for item_code, item_name in _NEW_RAW_MATERIALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_new_products():
	items_created = 0
	boms_created = 0
	for item_code, spec in _NEW_PRODUCTS.items():
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": spec["name"],
					"item_group": "Finished Goods",
					"stock_uom": "Kg",
					"is_stock_item": 1,
					"has_batch_no": 1,
					"create_new_batch": 1,
					"has_expiry_date": 1,
					"shelf_life_in_days": spec["shelf_life"],
				}
			).insert(ignore_permissions=True)
			items_created += 1
		if not frappe.db.exists("BOM", {"item": item_code, "is_active": 1}):
			bom = frappe.get_doc({"doctype": "BOM", "item": item_code, "quantity": spec["batch_qty"], "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
			for ing_code, qty in spec["formula"]:
				bom.append("items", {"item_code": ing_code, "qty": qty})
			bom.insert(ignore_permissions=True)
			bom.submit()
			boms_created += 1
	return items_created, boms_created


def seed_supplement_catalog_expansion():
	"""P2 catalog-widening fix (post-launch reviewer feedback, not a master-plan DP item) — 5
	new real supplement products (Item + real Formula/BOM each), widening WEB-01/WEB-05's
	catalog beyond the single VITC-1000-EFF flagship it reused from this golden demo. See the
	module-level comment above this section for the full design rationale."""
	if not frappe.db.exists("Company", _COMPANY_NAME):
		return "seed_supplement_catalog_expansion: SKIPPED — run seed_supplement_master_data first."
	rm_created = _ensure_new_raw_materials()
	items_created, boms_created = _ensure_new_products()
	return f"seed_supplement_catalog_expansion: {rm_created} new raw material(s), {items_created} new product Item(s), {boms_created} new Formula/BOM(s) (of {len(_NEW_PRODUCTS)} total products)."


def _flagship_batch_from_work_order(item_code):
	"""The batch THIS company's own Work Order actually produced, found by joining through
	that Work Order's own Manufacture Stock Entry — NOT a bare `{"item": item_code, "batch_qty":
	[">", 0]}` lookup, which would be genuinely ambiguous once Demo Consumer Distribution Co.
	also receives its own, unrelated second batch of this same globally-reused Item into ITS
	OWN warehouse (seed_consumer_dist_catalog_expansion()) — the exact cross-demo regression
	class already found and fixed for VITC-1000-EFF/FACIAL-CLEANSER-150ML in Golden Demo #25
	(see verify_supplement_golden_demo()'s own comment for the full history). Same join shape
	as Cosmetics' `_original_bulk_batch()`."""
	row = frappe.db.sql(
		"""select sbe.batch_no from `tabWork Order` wo
		join `tabStock Entry` se on se.work_order = wo.name and se.purpose = 'Manufacture' and se.docstatus = 1
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.t_warehouse is not null
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where wo.production_item = %(item)s and wo.company = %(company)s
		order by wo.creation asc limit 1""",
		{"item": item_code, "company": _COMPANY_NAME},
	)
	return row[0][0] if row else None


def _ensure_flagship_rm_stock(formula):
	created = False
	for ing_code, qty in formula:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_WAREHOUSE, ing_code))[0][0] or 0
		if balance >= qty:
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": ing_code, "qty": qty, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 95000})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _ensure_line_clean_after_allergen(fg_warehouse):
	"""Golden Demo #7 (Feed Manufacturing)'s F07 hook (`block_line_not_cleaned_after_allergen`
	in feed_validations.py, registered globally on Work Order.validate — deliberately NOT
	scoped to Feed's own company, "generically useful, not feed-specific in principle" per its
	own module docstring) blocks ANY non-allergen Work Order on a line (fg_warehouse) whose
	most recent prior Work Order used an allergen-containing Formula, unless a real `Feed Line
	Cleaning Log` post-dates that run. Demo Supplement Co.'s own FG Quarantine - DSC line
	already ran VITC-1000-EFF's allergen formula (Soy Lecithin) before these new non-allergen
	flagship Work Orders — found live as this hook correctly firing, not a bug — so it's
	satisfied here with a real cleaning log, the exact same fix feed_seeds.py's own F07 test
	uses, never worked around."""
	latest_allergen_wo = frappe.db.sql(
		"""select wo.creation from `tabWork Order` wo
		join `tabItem` i on i.name = wo.production_item
		where wo.fg_warehouse = %(warehouse)s and wo.docstatus = 1 and i.contains_allergen = 1
		order by wo.creation desc limit 1""",
		{"warehouse": fg_warehouse},
	)
	if not latest_allergen_wo:
		return False
	already_cleaned = frappe.db.exists("Feed Line Cleaning Log", {"warehouse": fg_warehouse, "cleaned_date": [">", latest_allergen_wo[0][0]]})
	if already_cleaned:
		return False
	frappe.get_doc(
		{
			"doctype": "Feed Line Cleaning Log",
			"warehouse": fg_warehouse,
			"cleaned_date": frappe.utils.now_datetime(),
			"cleaned_by": "Warehouse Officer (demo)",
			"notes": "Full wet clean after an allergen-containing (Soy Lecithin) VITC-1000-EFF run on this line — verified allergen-free before starting a new non-allergen product's Work Order.",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_flagship_work_order(item_code, bom_no, batch_qty):
	existing = frappe.db.exists("Work Order", {"production_item": item_code, "company": _COMPANY_NAME, "docstatus": 1})
	if existing:
		return existing, False
	_ensure_line_clean_after_allergen(_FG_QUARANTINE_WAREHOUSE)
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": item_code,
			"bom_no": bom_no,
			"qty": batch_qty,
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


def _ensure_flagship_manufacture(wo_name, batch_qty):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=batch_qty)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _ensure_flagship_qc_and_release(item_code, wo_name, batch_qty):
	batch = _flagship_batch_from_work_order(item_code)
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
				"item_code": item_code,
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
		se.append("items", {"item_code": item_code, "qty": batch_qty, "s_warehouse": _FG_QUARANTINE_WAREHOUSE, "t_warehouse": _FG_RELEASED_WAREHOUSE, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qc_created, release_created


def _ensure_flagship_lims(item_code, batch):
	cfg = _FLAGSHIP_LIMS[item_code]
	item_name = _NEW_PRODUCTS[item_code]["name"]
	if not frappe.db.exists("LIMS Specification", {"item_name": item_name, "status": "Effective"}):
		frappe.get_doc(
			{
				"doctype": "LIMS Specification",
				"spec_code": cfg["spec_code"],
				"item_name": item_name,
				"version_no": 1,
				"status": "Effective",
				"parameters": [{"parameter_name": cfg["parameter"], "unit": cfg["unit"], "min_value": cfg["min_value"], "max_value": cfg["max_value"]}],
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("LIMS Test Method", {"method_code": cfg["method_code"], "status": "Effective"}):
		frappe.get_doc({"doctype": "LIMS Test Method", "method_code": cfg["method_code"], "method_name": cfg["method_name"], "instrument_type": "Titrator", "status": "Effective"}).insert(
			ignore_permissions=True
		)

	sample_name = frappe.db.get_value("LIMS Sample", {"batch_reference": batch, "item_name": item_name}, "name")
	if not sample_name:
		sample = frappe.get_doc({"doctype": "LIMS Sample", "item_name": item_name, "batch_reference": batch, "sample_type": "Finished Goods", "received_date": frappe.utils.nowdate(), "status": "Assigned"})
		sample.insert(ignore_permissions=True)
		sample_name = sample.name

	test_name = frappe.db.get_value("LIMS Test", {"sample": sample_name}, "name")
	if not test_name or frappe.db.get_value("LIMS Test", test_name, "status") != "Approved":
		spec = frappe.db.get_value("LIMS Specification", {"item_name": item_name, "status": "Effective"}, "name")
		method = frappe.db.get_value("LIMS Test Method", {"method_code": cfg["method_code"], "status": "Effective"}, "name")
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
					"results": [{"parameter_name": cfg["parameter"], "result_value": cfg["result_value"], "unit": cfg["unit"]}],
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
	return coa_name


def seed_supplement_flagship_production():
	"""P2 catalog-widening fix — full production -> QC -> LIMS COA pipeline (identical depth to
	VITC-1000-EFF's own DP-625/DP-628) for the 2 new WEB-02 brand-site flagship SKUs
	(VITD3-1000-SG, ZINC-50-TAB), bringing WEB-02 to 3 real flagship SKUs total (within the
	reviewer's own suggested 3-5 range). Run seed_supplement_catalog_expansion() first."""
	results = []
	for item_code, spec in _NEW_PRODUCTS.items():
		if not spec.get("flagship"):
			continue
		bom_no = frappe.db.get_value("BOM", {"item": item_code, "is_active": 1}, "name")
		if not bom_no:
			results.append(f"{item_code}: SKIPPED (run seed_supplement_catalog_expansion first)")
			continue
		_ensure_flagship_rm_stock(spec["formula"])
		wo_name, wo_created = _ensure_flagship_work_order(item_code, bom_no, spec["batch_qty"])
		_ensure_flagship_manufacture(wo_name, spec["batch_qty"])
		batch, qc_created, release_created = _ensure_flagship_qc_and_release(item_code, wo_name, spec["batch_qty"])
		coa_name = _ensure_flagship_lims(item_code, batch) if batch else None
		results.append(f"{item_code}: batch={batch}, WO {'created' if wo_created else 'existed'}, QC {'created' if qc_created else 'existed'}, release {'created' if release_created else 'existed'}, COA={coa_name}")
	return "seed_supplement_flagship_production: " + " | ".join(results)
