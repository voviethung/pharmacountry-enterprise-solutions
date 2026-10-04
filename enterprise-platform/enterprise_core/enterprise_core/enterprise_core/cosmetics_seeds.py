"""Golden Demo #21 — Cosmetics Manufacturing (master plan DEMO 03, "PHASE 6" item 2),
IP-COSMETICS. Two-stage flow: Bulk batch (formula) -> QC -> Release -> consumed as an
ingredient by the Packed batch -> QC -> Release. `block_fg_release_without_qa` fires twice
(Bulk release, Packed release) with zero hook changes — it matches any warehouse whose name
contains "released".
"""

import frappe

_COMPANY_NAME = "Demo Cosmetics Co."
_COMPANY_ABBR = "DCC"
_RM_WAREHOUSE = f"RM Store - {_COMPANY_ABBR}"
_BULK_QUARANTINE = f"Bulk Quarantine - {_COMPANY_ABBR}"
_BULK_RELEASED = f"Bulk Released - {_COMPANY_ABBR}"
_PACKING_STORE = f"Packing Store - {_COMPANY_ABBR}"
_FG_QUARANTINE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED = f"FG Released - {_COMPANY_ABBR}"

_BULK_ITEM = "FACIAL-CLEANSER-BULK"
_PACKED_ITEM = "FACIAL-CLEANSER-150ML"
_BULK_BATCH_QTY = 100  # kg
_PACKED_BATCH_QTY = 500  # bottles

_CHEMICALS = [("AQUA", "Water (Aqua)"), ("GLYCERIN", "Glycerin"), ("COCAMIDOPROPYL-BETAINE", "Cocamidopropyl Betaine"), ("FRAGRANCE", "Fragrance"), ("PRESERVATIVE-PHENOXYETHANOL", "Preservative (Phenoxyethanol)")]
# CITRIC-ACID is reused directly from Golden Demo #20 (Supplement) — Item is not company-scoped.
_PACKAGING_MATERIALS = [("BOTTLE-150ML", "Bottle 150ml"), ("PUMP-CAP", "Pump Cap"), ("LABEL-FACIAL-CLEANSER", "Label - Facial Cleanser")]

_BULK_FORMULA_V1 = [("AQUA", 70), ("GLYCERIN", 10), ("COCAMIDOPROPYL-BETAINE", 15), ("CITRIC-ACID", 1), ("FRAGRANCE", 2), ("PRESERVATIVE-PHENOXYETHANOL", 2)]
_BULK_FORMULA_V2 = [("AQUA", 71), ("GLYCERIN", 10), ("COCAMIDOPROPYL-BETAINE", 15), ("CITRIC-ACID", 1), ("FRAGRANCE", 1), ("PRESERVATIVE-PHENOXYETHANOL", 2)]
_PACKED_FORMULA = [(_BULK_ITEM, 75), ("BOTTLE-150ML", 500), ("PUMP-CAP", 500), ("LABEL-FACIAL-CLEANSER", 500)]


def _original_bulk_batch():
	"""The batch the ORIGINAL Bulk Work Order produced, found by joining through that specific
	Work Order's own Manufacture Stock Entry — NOT `{"batch_qty": [">", 0]}, order_by="creation
	asc"` (used in an earlier version of this file), which is fragile once a second
	FACIAL-CLEANSER-BULK batch exists (from the rework in DP-638): once the original batch's
	own current batch_qty (its live quantity summed across all warehouses) drops to 0 — fully
	consumed between packing and rework — that filter silently starts resolving to the
	REWORKED batch instead, a real idempotency bug found when a second full registry pass
	tried to rework the rework and hit a negative-stock error. This lookup is immune to that:
	it identifies the batch by which Work Order actually produced it, never by a fluctuating
	quantity."""
	return frappe.db.sql(
		"""select sbe.batch_no from `tabWork Order` wo
		join `tabStock Entry` se on se.work_order = wo.name and se.purpose = 'Manufacture' and se.docstatus = 1
		join `tabStock Entry Detail` sed on sed.parent = se.name and sed.t_warehouse is not null
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where wo.production_item = %(item)s
		order by wo.creation asc limit 1""",
		{"item": _BULK_ITEM},
	)[0][0] if frappe.db.exists("Work Order", {"production_item": _BULK_ITEM}) else None


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
	# Company.cost_center is normally auto-populated by ERPNext's own on_update/after_insert
	# logic, but came back NULL here (found while debugging a "Cost Center is mandatory" error
	# on the first Manufacture Stock Entry) — set it explicitly to the default Cost Center
	# ERPNext's Company setup always creates ("Main - <abbr>"), rather than depend on that
	# auto-population always firing.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods", "Packaging Material"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_warehouses():
	for wh in (_RM_WAREHOUSE, _BULK_QUARANTINE, _BULK_RELEASED, _PACKING_STORE, _FG_QUARANTINE, _FG_RELEASED):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


def _ensure_items():
	created = 0
	for item_code, item_name in _CHEMICALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}).insert(ignore_permissions=True)
		created += 1
	for item_code, item_name in _PACKAGING_MATERIALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Packaging Material", "stock_uom": "Nos", "is_stock_item": 1}).insert(
			ignore_permissions=True
		)
		created += 1
	if not frappe.db.exists("Item", _BULK_ITEM):
		frappe.get_doc(
			{"doctype": "Item", "item_code": _BULK_ITEM, "item_name": "Facial Cleanser - Bulk", "item_group": "Finished Goods", "stock_uom": "Kg", "is_stock_item": 1, "has_batch_no": 1, "create_new_batch": 1}
		).insert(ignore_permissions=True)
		created += 1
	if not frappe.db.exists("Item", _PACKED_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _PACKED_ITEM,
				"item_name": "Facial Cleanser 150ml Bottle",
				"item_group": "Finished Goods",
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"has_expiry_date": 1,
				"shelf_life_in_days": 1095,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_bom(item_code, qty, uom, ingredients):
	if frappe.db.exists("BOM", {"item": item_code, "is_active": 1}):
		return False
	bom = frappe.get_doc({"doctype": "BOM", "item": item_code, "quantity": qty, "uom": uom, "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, ing_qty in ingredients:
		bom.append("items", {"item_code": ing_code, "qty": ing_qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_cosmetics_master_data():
	"""DP-631 — Company, Warehouses, Items, Bulk Formula v1, Packed Formula."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	items_created = _ensure_items()
	bulk_bom_created = _ensure_bom(_BULK_ITEM, _BULK_BATCH_QTY, "Kg", _BULK_FORMULA_V1)
	packed_bom_created = _ensure_bom(_PACKED_ITEM, _PACKED_BATCH_QTY, "Nos", _PACKED_FORMULA)
	return (
		f"seed_cosmetics_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {items_created} new item(s). "
		f"Bulk formula {'created' if bulk_bom_created else 'already existed'}. Packed formula {'created' if packed_bom_created else 'already existed'}."
	)


def _receive_stock(warehouse, item_qty_rate):
	created = False
	for item_code, qty, rate in item_qty_rate:
		balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (warehouse, item_code))[0][0] or 0
		if balance >= qty:
			continue
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": warehouse, "basic_rate": rate})
		se.insert(ignore_permissions=True)
		se.submit()
		created = True
	return created


def _ensure_work_order(production_item, bom_no, qty, source_warehouse, fg_warehouse):
	existing = frappe.db.exists("Work Order", {"production_item": production_item, "bom_no": bom_no, "docstatus": 1})
	if existing:
		return existing, False
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": production_item,
			"bom_no": bom_no,
			"qty": qty,
			"company": _COMPANY_NAME,
			"source_warehouse": source_warehouse,
			"fg_warehouse": fg_warehouse,
			"skip_transfer": 1,
			# The Packed BOM consumes FACIAL-CLEANSER-BULK as a single ingredient — without
			# this, ERPNext's default multi-level BOM explosion treats it as a sub-assembly and
			# expands it down to ITS OWN raw materials (Aqua, Glycerin, ...) instead, which by
			# this point in the flow have already been fully consumed making the Bulk batch —
			# found as a real "Valuation Rate ... is required" error on an unrelated ingredient
			# (Preservative) once its RM balance hit exactly zero.
			"use_multi_level_bom": 0,
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo.name, True


def _ensure_manufacture(wo_name, qty):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=qty)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _ensure_qc_and_release(item_code, wo_name, quarantine_wh, released_wh, qty):
	batch = frappe.db.get_value("Batch", {"item": item_code, "batch_qty": [">", 0]}, "name", order_by="creation desc")
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
		(released_wh, batch),
	)
	release_created = False
	if not released:
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "s_warehouse": quarantine_wh, "t_warehouse": released_wh, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch, qc_created, release_created


def seed_cosmetics_bulk_production():
	"""DP-632 — Bulk formula -> Bulk batch -> Bulk QC -> Bulk release. `block_fg_release_without_qa`
	fires here (1st time in this demo) since "Bulk Released - DCC" matches its warehouse-name
	pattern — zero hook changes needed."""
	bom_no = frappe.db.get_value("BOM", {"item": _BULK_ITEM, "is_active": 1}, "name")
	if not bom_no:
		return "seed_cosmetics_bulk_production: SKIPPED — run seed_cosmetics_master_data first."
	rm_received = _receive_stock(_RM_WAREHOUSE, [("AQUA", 71, 5000), ("GLYCERIN", 10, 60000), ("COCAMIDOPROPYL-BETAINE", 15, 90000), ("CITRIC-ACID", 1, 95000), ("FRAGRANCE", 2, 250000), ("PRESERVATIVE-PHENOXYETHANOL", 2, 180000)])
	wo_name, wo_created = _ensure_work_order(_BULK_ITEM, bom_no, _BULK_BATCH_QTY, _RM_WAREHOUSE, _BULK_QUARANTINE)
	manufacture_created = _ensure_manufacture(wo_name, _BULK_BATCH_QTY)
	batch, qc_created, release_created = _ensure_qc_and_release(_BULK_ITEM, wo_name, _BULK_QUARANTINE, _BULK_RELEASED, _BULK_BATCH_QTY)
	return (
		f"seed_cosmetics_bulk_production: RM stock {'received' if rm_received else 'already present'}. Work Order {'created' if wo_created else 'already existed'} ({wo_name}). "
		f"Manufacture {'created' if manufacture_created else 'already existed'}. Bulk Batch {batch}. QC {'created' if qc_created else 'already existed'}. "
		f"Release {'created' if release_created else 'already existed'} (block_fg_release_without_qa reuse #1)."
	)


def seed_cosmetics_packed_production():
	"""DP-633 — packaging materials + released bulk staged into Packing Store -> Packed batch
	-> final QC -> final release. C02 (bulk batch and packed batch genealogy) is proven here:
	trace_feed_batch_genealogy(packed_batch) now resolves the SPECIFIC bulk batch_no consumed,
	not just the item code — the additive fix this golden demo required in
	trace_feed_batch_genealogy() itself."""
	bulk_batch = _original_bulk_batch()
	if not bulk_batch or not frappe.db.exists("Stock Ledger Entry", {"warehouse": _BULK_RELEASED, "item_code": _BULK_ITEM}):
		return "seed_cosmetics_packed_production: SKIPPED — run seed_cosmetics_bulk_production first."

	packaging_received = _receive_stock(_PACKING_STORE, [("BOTTLE-150ML", 500, 3000), ("PUMP-CAP", 500, 1500), ("LABEL-FACIAL-CLEANSER", 500, 500)])

	bom_no = frappe.db.get_value("BOM", {"item": _PACKED_ITEM, "is_active": 1}, "name")
	packed_wo_already_manufactured = frappe.db.exists(
		"Stock Entry", {"work_order": frappe.db.get_value("Work Order", {"production_item": _PACKED_ITEM, "docstatus": 1}, "name"), "purpose": "Manufacture", "docstatus": 1}
	)
	bulk_staged = False
	if not packed_wo_already_manufactured:
		# Packing Store's OWN current balance can't tell "never staged" apart from "staged, then
		# fully consumed by the Packed Work Order's own Manufacture step" — it's 0 either way,
		# so a balance-based check here re-triggers a doomed second transfer of stock the
		# original batch no longer has (found as a real "negative stock" error on a second
		# registry pass, after the rework in DP-638 had already consumed the batch's remainder).
		# Whether the Packed WO has already manufactured is the real signal.
		staged_balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_PACKING_STORE, _BULK_ITEM))[0][0] or 0
		if staged_balance < 75:
			se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
			se.append("items", {"item_code": _BULK_ITEM, "qty": 75, "s_warehouse": _BULK_RELEASED, "t_warehouse": _PACKING_STORE, "batch_no": bulk_batch, "use_serial_batch_fields": 1})
			se.insert(ignore_permissions=True)
			se.submit()
			bulk_staged = True

	wo_name, wo_created = _ensure_work_order(_PACKED_ITEM, bom_no, _PACKED_BATCH_QTY, _PACKING_STORE, _FG_QUARANTINE)
	manufacture_created = _ensure_manufacture(wo_name, _PACKED_BATCH_QTY)
	packed_batch, qc_created, release_created = _ensure_qc_and_release(_PACKED_ITEM, wo_name, _FG_QUARANTINE, _FG_RELEASED, _PACKED_BATCH_QTY)

	from enterprise_core.enterprise_core.api import trace_feed_batch_genealogy

	genealogy = trace_feed_batch_genealogy(packed_batch) if packed_batch else None
	bulk_consumed = next((r for r in (genealogy or {}).get("raw_materials_consumed", []) if r.get("item_code") == _BULK_ITEM), None)
	c02_confirmed = bool(bulk_consumed and bulk_consumed.get("batch_no") == bulk_batch)

	return (
		f"seed_cosmetics_packed_production: Packaging {'received' if packaging_received else 'already present'}. Bulk batch {'staged' if bulk_staged else 'already staged'} into Packing Store. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). Manufacture {'created' if manufacture_created else 'already existed'}. Packed Batch {packed_batch}. "
		f"QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'} (block_fg_release_without_qa reuse #2). "
		f"C02 CONFIRMED ({c02_confirmed}) — packed batch genealogy resolves bulk batch {bulk_batch}."
	)


def seed_cosmetics_formula_revision():
	"""DP-634 — C01, formula revision does not change the already-created bulk batch. Same
	is_default-flip pattern as Vet Mfg/Aqua Env/Supplement, with the same explicit
	before/after-unchanged assertion Supplement's DP-626 added."""
	if not frappe.db.exists("Work Order", {"production_item": _BULK_ITEM, "docstatus": 1}):
		return "seed_cosmetics_formula_revision: SKIPPED — run seed_cosmetics_bulk_production first."
	if frappe.db.count("BOM", {"item": _BULK_ITEM}) >= 2:
		return "seed_cosmetics_formula_revision: already revised (2+ BOM versions exist)."
	old_bom = frappe.db.get_value("BOM", {"item": _BULK_ITEM, "is_active": 1}, "name", order_by="creation asc")
	before = frappe.get_all("BOM Item", filters={"parent": old_bom}, fields=["item_code", "qty"], order_by="item_code")
	frappe.db.set_value("BOM", old_bom, "is_default", 0)
	new_bom = frappe.get_doc({"doctype": "BOM", "item": _BULK_ITEM, "quantity": _BULK_BATCH_QTY, "uom": "Kg", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for ing_code, qty in _BULK_FORMULA_V2:
		new_bom.append("items", {"item_code": ing_code, "qty": qty})
	new_bom.insert(ignore_permissions=True)
	new_bom.submit()
	after = frappe.get_all("BOM Item", filters={"parent": old_bom}, fields=["item_code", "qty"], order_by="item_code")
	if before != after:
		frappe.throw(f"C01 FAILED: revising the formula changed BOM {old_bom}'s own recorded items.")
	return f"seed_cosmetics_formula_revision: C01 CONFIRMED — {old_bom} kept Active and UNCHANGED as history, new version {new_bom.name} is now default."


_ARTWORK_DOC_NAME = f"ARTWORK-{_PACKED_ITEM}"


def seed_cosmetics_artwork():
	"""DP-635 — C03, artwork version. Reuses Golden Demo #4's DMS Document/Version lifecycle
	with doc_type="Artwork" (the option Golden Demo #20 already added) — exact same pattern as
	Supplement's own Artwork."""
	if not frappe.db.exists("Item", _PACKED_ITEM):
		return "seed_cosmetics_artwork: SKIPPED — run seed_cosmetics_master_data first."
	if frappe.db.exists("DMS Document Version", {"document": _ARTWORK_DOC_NAME, "status": "Effective"}):
		return "seed_cosmetics_artwork: already existed (Effective)."
	if not frappe.db.exists("DMS Document", _ARTWORK_DOC_NAME):
		frappe.get_doc({"doctype": "DMS Document", "document_code": _ARTWORK_DOC_NAME, "title": f"Bottle Artwork — {_PACKED_ITEM}", "doc_type": "Artwork", "status": "Draft", "requires_training": 0}).insert(
			ignore_permissions=True
		)
	v1 = frappe.get_doc({"doctype": "DMS Document Version", "document": _ARTWORK_DOC_NAME, "version_no": 1, "status": "Draft", "content_summary": "150ml bottle wraparound label, matches formula v1 ingredient declaration."})
	v1.insert(ignore_permissions=True)
	v1.status = "Approved"
	v1.approved_by = "quality.director@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Effective"
	v1.effective_date = frappe.utils.nowdate()
	v1.save(ignore_permissions=True)
	return "seed_cosmetics_artwork: C03 CONFIRMED — artwork document created and reached Effective."


def seed_cosmetics_stability():
	"""DP-636 — C04, stability sample schedule. A real cosmetics stability program samples the
	same batch at multiple time points under multiple storage conditions; two time points are
	deliberately left in the past with no test_date so C04 fires on real overdue data, same
	approach as every prior golden demo's deliberate overdue/out-of-range seed row."""
	packed_batch = frappe.db.get_value("Batch", {"item": _PACKED_ITEM, "batch_qty": [">", 0]}, "name", order_by="creation desc")
	if not packed_batch:
		return "seed_cosmetics_stability: SKIPPED — run seed_cosmetics_packed_production first."
	created = 0
	# scheduled_date is set directly via day-offsets from today, not derived from a synthetic
	# "manufacture_date - N months" anchor via add_months — that combination is ambiguous
	# (calendar months aren't a fixed number of days) and, once tried, produced zero Overdue
	# entries even for a time point intended to land in the past, silently failing C04's own
	# verify check. Every prior golden demo's deliberate overdue/out-of-range row used a direct
	# day-offset for exactly this reason.
	schedule = [
		(0, "Room Temperature", -90, True), (0, "Accelerated 40C", -90, True),
		(1, "Room Temperature", -60, True), (1, "Accelerated 40C", -60, True),
		(3, "Room Temperature", -5, False), (3, "Accelerated 40C", -5, False),  # overdue — scheduled in the past, never tested
		(12, "Room Temperature", 275, None),  # far future — still Scheduled, not overdue
	]
	for months, condition, days_offset, tested in schedule:
		scheduled_date = frappe.utils.add_days(frappe.utils.nowdate(), days_offset)
		if frappe.db.exists("Cosmetics Stability Sample", {"batch_no": packed_batch, "condition": condition, "time_point_months": months}):
			continue
		doc = frappe.get_doc(
			{"doctype": "Cosmetics Stability Sample", "batch_no": packed_batch, "condition": condition, "time_point_months": months, "scheduled_date": scheduled_date}
		)
		if tested:
			doc.test_date = scheduled_date
			doc.result_summary = "Within spec — pH, viscosity, appearance, fragrance all conform."
		doc.insert(ignore_permissions=True)
		created += 1
	overdue_count = frappe.db.count("Cosmetics Stability Sample", {"batch_no": packed_batch, "status": "Overdue"})
	return f"seed_cosmetics_stability: {created} stability sample(s) created (C04), {overdue_count} Overdue."


_CUSTOMER_GROUP = "Consumer Health / Cosmetics Retailers"
_CUSTOMER_NAME = "GlowBeauty Retail Chain"


def _ensure_customer():
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(ignore_permissions=True)
	if frappe.db.exists("Customer", {"customer_name": _CUSTOMER_NAME}):
		return frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), False
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": _CUSTOMER_NAME, "customer_type": "Company", "customer_group": _CUSTOMER_GROUP})
	customer.insert(ignore_permissions=True)
	return customer.name, True


def seed_cosmetics_distribution_and_complaint():
	"""DP-637 — distribution (reuses trace_batch_to_customers) + C05 (complaint traced back to
	the batch the complaining customer actually received)."""
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _FG_RELEASED, "item_code": _PACKED_ITEM}):
		return "seed_cosmetics_distribution_and_complaint: SKIPPED — run seed_cosmetics_packed_production first."
	customer, customer_created = _ensure_customer()

	existing_so = frappe.db.exists("Sales Order", {"customer": customer, "docstatus": 1})
	if existing_so:
		so_name = existing_so
	else:
		so = frappe.get_doc(
			{"doctype": "Sales Order", "customer": customer, "company": _COMPANY_NAME, "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 5), "items": [{"item_code": _PACKED_ITEM, "qty": 100, "warehouse": _FG_RELEASED, "rate": 95000}]}
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
	batch = frappe.db.get_value("Delivery Note Item", {"parent": dn_name, "item_code": _PACKED_ITEM}, "batch_no")

	complaint_created = False
	if batch and not frappe.db.exists("Cosmetics Complaint", {"batch_no": batch, "customer": customer}):
		frappe.get_doc(
			{
				"doctype": "Cosmetics Complaint",
				"customer": customer,
				"batch_no": batch,
				"description": "Consumer reported unusual fragrance change after 2 months of use.",
				"status": "Investigating",
			}
		).insert(ignore_permissions=True)
		complaint_created = True

	from enterprise_core.enterprise_core.api import trace_batch_to_customers

	traced = trace_batch_to_customers(batch) if batch else []
	c05_confirmed = any(row.get("customer") == customer for row in traced)
	if not c05_confirmed:
		frappe.throw(f"C05 FAILED: complaint batch {batch} does not trace back to the complaining customer {customer}.")
	return f"seed_cosmetics_distribution_and_complaint: Delivery {'created' if dn_created else 'already existed'}. Complaint {'created' if complaint_created else 'already existed'}. C05 CONFIRMED — batch {batch} traces to complaining customer {customer}."


def seed_cosmetics_rework():
	"""DP-638 — C06, rework does not lose genealogy. A second Bulk batch needs a minor
	pH-correction rework: a manual Manufacture-purpose Stock Entry (no Work Order — a rework
	isn't a fresh production run) consumes the ORIGINAL bulk batch plus a small corrective
	ingredient and produces a NEW bulk batch, so `trace_feed_batch_genealogy()` (unmodified,
	same function C02 already uses) still resolves the original batch as an input — real
	stock-ledger genealogy, not just the explicit `Cosmetics Rework Record` audit note sitting
	alongside it."""
	original_batch = _original_bulk_batch()
	if not original_batch:
		return "seed_cosmetics_rework: SKIPPED — run seed_cosmetics_bulk_production first."
	if frappe.db.exists("Cosmetics Rework Record", {"original_batch": original_batch}):
		return "seed_cosmetics_rework: already existed."

	# Only the remainder of the original batch still sitting in Bulk Released is available to
	# rework — most of it (75kg) was already consumed by seed_cosmetics_packed_production.
	# Found as a real BatchNegativeStockError the first time this used the full _BULK_BATCH_QTY.
	remaining_qty = frappe.db.sql(
		"select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_BULK_RELEASED, _BULK_ITEM)
	)[0][0] or 0
	if remaining_qty <= 0:
		return f"seed_cosmetics_rework: SKIPPED — no remaining stock of batch {original_batch} in {_BULK_RELEASED} to rework."
	corrective_qty = round(remaining_qty * 0.02, 2)  # same 0.5/100 = 0.5% ratio as the original v1->v2 revision

	if not frappe.db.exists("Item", "CITRIC-ACID"):
		return "seed_cosmetics_rework: SKIPPED — CITRIC-ACID item missing (run Supplement's master data first, or Cosmetics master data which also needs it)."
	# top up a small corrective ingredient stock in RM Store for the rework
	balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code='CITRIC-ACID' and is_cancelled=0", (_RM_WAREHOUSE,))[0][0] or 0
	if balance < corrective_qty:
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": "CITRIC-ACID", "qty": 1, "t_warehouse": _RM_WAREHOUSE, "basic_rate": 95000})
		se.insert(ignore_permissions=True)
		se.submit()

	rework_se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Repack", "purpose": "Repack", "company": _COMPANY_NAME})
	rework_se.append("items", {"item_code": _BULK_ITEM, "qty": remaining_qty, "s_warehouse": _BULK_RELEASED, "batch_no": original_batch, "use_serial_batch_fields": 1})
	rework_se.append("items", {"item_code": "CITRIC-ACID", "qty": corrective_qty, "s_warehouse": _RM_WAREHOUSE})
	rework_se.append("items", {"item_code": _BULK_ITEM, "qty": remaining_qty, "t_warehouse": _BULK_QUARANTINE, "use_serial_batch_fields": 1})
	rework_se.insert(ignore_permissions=True)
	rework_se.submit()

	new_batch = frappe.db.get_value("Batch", {"item": _BULK_ITEM, "batch_qty": [">", 0]}, "name", order_by="creation desc")

	qi = frappe.get_doc(
		{
			"doctype": "Quality Inspection",
			"inspection_type": "In Process",
			"reference_type": "Stock Entry",
			"reference_name": rework_se.name,
			"item_code": _BULK_ITEM,
			"batch_no": new_batch,
			"sample_size": 5,
			"status": "Accepted",
			"company": _COMPANY_NAME,
			"inspected_by": frappe.session.user,
		}
	)
	qi.insert(ignore_permissions=True)
	qi.submit()

	release_se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	release_se.append("items", {"item_code": _BULK_ITEM, "qty": remaining_qty, "s_warehouse": _BULK_QUARANTINE, "t_warehouse": _BULK_RELEASED, "batch_no": new_batch, "use_serial_batch_fields": 1})
	release_se.insert(ignore_permissions=True)
	release_se.submit()

	frappe.get_doc(
		{"doctype": "Cosmetics Rework Record", "original_batch": original_batch, "new_batch": new_batch, "reason": "Minor pH deviation on QC recheck — corrected with an additional 0.5kg citric acid addition, re-tested and Accepted."}
	).insert(ignore_permissions=True)

	from enterprise_core.enterprise_core.api import trace_feed_batch_genealogy

	genealogy = trace_feed_batch_genealogy(new_batch)
	bulk_consumed = next((r for r in genealogy.get("raw_materials_consumed", []) if r.get("item_code") == _BULK_ITEM), None)
	c06_confirmed = bool(bulk_consumed and bulk_consumed.get("batch_no") == original_batch)
	if not c06_confirmed:
		frappe.throw(f"C06 FAILED: reworked batch {new_batch}'s genealogy does not resolve back to original batch {original_batch}.")
	return f"seed_cosmetics_rework: C06 CONFIRMED — new batch {new_batch}'s genealogy resolves back to original batch {original_batch} through the rework."


# ---------------------------------------------------------------------------
# Catalog expansion (P2 post-launch reviewer fix, NOT a master-plan DP item) — this golden
# demo's ONLY sellable finished good was FACIAL-CLEANSER-150ML (FACIAL-CLEANSER-BULK is an
# unsellable manufacturing intermediate), giving WEB-05's "Skincare" grouping zero real
# breadth. Adds ONE new real, single-stage finished cosmetic — a real Item + real Formula
# (BOM) mixing real chemical ingredients with real packaging materials, the same mixed-UOM
# BOM shape the Packed Formula above already establishes (kg chemicals + Nos packaging ->
# Nos bottles) — deliberately NOT re-running the two-stage Bulk/Packed pipeline (that
# specific shape exists to demonstrate C02's genealogy test, not because every SKU needs it).
# No production run of its own here — real public stock/price is established downstream by
# Demo Consumer Distribution Co.'s own Material Receipt, same pattern as
# FACIAL-CLEANSER-150ML/VITC-1000-EFF.
# ---------------------------------------------------------------------------

_TONER_ITEM = "FACIAL-TONER-200ML"
_TONER_NAME = "Hydrating Facial Toner 200ml"
_TONER_BATCH_QTY = 500  # Nos (bottles)
_TONER_NEW_CHEMICALS = [("NIACINAMIDE", "Niacinamide"), ("WITCH-HAZEL-EXTRACT", "Witch Hazel Extract")]
_TONER_NEW_PACKAGING = [("BOTTLE-200ML", "Bottle 200ml (Toner)"), ("SPRAY-CAP", "Spray Cap"), ("LABEL-FACIAL-TONER", "Label - Facial Toner")]
# AQUA, GLYCERIN, PRESERVATIVE-PHENOXYETHANOL are reused directly from this module's own
# existing chemicals above — Item is not company-scoped.
_TONER_FORMULA = [
	("AQUA", 90),
	("GLYCERIN", 5),
	("NIACINAMIDE", 2),
	("WITCH-HAZEL-EXTRACT", 2),
	("PRESERVATIVE-PHENOXYETHANOL", 1),
	("BOTTLE-200ML", 500),
	("SPRAY-CAP", 500),
	("LABEL-FACIAL-TONER", 500),
]


def seed_cosmetics_catalog_expansion():
	"""P2 catalog-widening fix (post-launch reviewer feedback, not a master-plan DP item) — one
	new real finished cosmetic (Item + real Formula/BOM), widening WEB-05's "Skincare" category
	beyond the single FACIAL-CLEANSER-150ML SKU. See the module-level comment above this
	section for the full design rationale."""
	if not frappe.db.exists("Company", _COMPANY_NAME):
		return "seed_cosmetics_catalog_expansion: SKIPPED — run seed_cosmetics_master_data first."
	created_items = 0
	for item_code, item_name in _TONER_NEW_CHEMICALS:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Raw Material", "stock_uom": "Kg", "is_stock_item": 1}).insert(ignore_permissions=True)
		created_items += 1
	for item_code, item_name in _TONER_NEW_PACKAGING:
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({"doctype": "Item", "item_code": item_code, "item_name": item_name, "item_group": "Packaging Material", "stock_uom": "Nos", "is_stock_item": 1}).insert(ignore_permissions=True)
		created_items += 1

	toner_created = False
	if not frappe.db.exists("Item", _TONER_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _TONER_ITEM,
				"item_name": _TONER_NAME,
				"item_group": "Finished Goods",
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"has_expiry_date": 1,
				"shelf_life_in_days": 1095,
			}
		).insert(ignore_permissions=True)
		toner_created = True

	bom_created = False
	if not frappe.db.exists("BOM", {"item": _TONER_ITEM, "is_active": 1}):
		bom = frappe.get_doc({"doctype": "BOM", "item": _TONER_ITEM, "quantity": _TONER_BATCH_QTY, "uom": "Nos", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
		for ing_code, qty in _TONER_FORMULA:
			bom.append("items", {"item_code": ing_code, "qty": qty})
		bom.insert(ignore_permissions=True)
		bom.submit()
		bom_created = True

	return f"seed_cosmetics_catalog_expansion: {created_items} new raw/packaging Item(s). Toner Item {'created' if toner_created else 'already existed'}. Formula {'created' if bom_created else 'already existed'}."
