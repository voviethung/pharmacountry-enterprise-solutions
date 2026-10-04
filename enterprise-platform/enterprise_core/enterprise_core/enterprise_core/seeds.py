"""DP-306 registry + DP-501 (Golden Pharma Demo) real implementations.

seed_demo_company and seed_pharma_master_data are real now — the rest stay stubs until
their own DP-5xx task (demo users -> DP-400 Demo Factory; end-to-end scenario -> once
CE-05/06/08 exist). Idempotent: every function checks for its own output before creating
anything, matching the DP-307 pattern established in enterprise_core/setup.py.
"""

import frappe

_DEMO_COMPANY_NAME = "Demo Pharma Co"
_DEMO_COMPANY_ABBR = "DPC"

_ROOT_ITEM_GROUP = "All Item Groups"

# (item_group_name, ) — matches master plan DEMO 01's 3-way split, generic (not ENLIE's
# literal NGUYÊN LIỆU/BAO BÌ/THÀNH PHẨM/VẬT TƯ/HÓA CHẤT/VĂN PHÒNG PHẨM 7-way split flagged
# as ENLIE-specific in the audit, F-4) — this is the platform's own minimal generic default.
_ITEM_GROUPS = ["Raw Material", "Packaging Material", "Finished Goods"]

# (item_code, item_name, item_group, stock_uom) — master plan §7 DEMO 01 "Master data bắt buộc".
_RAW_MATERIALS = [
	("PARA-API", "Paracetamol API", "Raw Material", "Kg"),
	("MCC", "Microcrystalline Cellulose (MCC)", "Raw Material", "Kg"),
	("PVP-K30", "PVP K30", "Raw Material", "Kg"),
	("MG-STEARATE", "Magnesium Stearate", "Raw Material", "Kg"),
]
_PACKAGING_MATERIALS = [
	("PVC-ALU", "PVC/Alu Blister Foil", "Packaging Material", "Nos"),
	("CARTON-PRINTED", "Printed Carton", "Packaging Material", "Nos"),
]
_FINISHED_GOODS = [
	("PARA-500-TAB", "Paracetamol 500 mg Tablet", "Finished Goods", "Nos"),
]

# (warehouse_name,) — master plan §7 DEMO 01: RM Quarantine/Approved/Rejected, FG Quarantine/Released.
_WAREHOUSES = [
	"RM Quarantine",
	"RM Approved",
	"RM Rejected",
	"FG Quarantine",
	"FG Released",
]

# BOM for Paracetamol 500mg Tablet: (item_code, qty)
# BOM.quantity=1000 means every item qty below is the TOTAL needed for a 1000-unit batch,
# not a per-tablet ratio. PVC-ALU/CARTON-PRINTED were originally 1 each (one blister/carton
# per tablet, an intuitive but wrong per-unit reading) which made ERPNext compute consumption
# as (1/1000) x work order qty = ~0 instead of 1000 each. Found via direct stock-ledger
# verification after seed_manufacturing_flow() reported success (DP-504 incident).
_PARA_500_BOM_ITEMS = [
	("PARA-API", 0.5),
	("MCC", 0.3),
	("PVP-K30", 0.1),
	("MG-STEARATE", 0.02),
	("PVC-ALU", 1000),
	("CARTON-PRINTED", 1000),
]


def seed_demo_company():
	"""DP-501 — creates the demo Company via ERPNext's own setup-wizard machinery (Fiscal
	Year, Company, Standard Chart of Accounts, default Price Lists, Global Defaults) instead
	of hand-rolling equivalents. `setup_complete()` is not itself safely re-runnable, so this
	is guarded by a plain existence check rather than calling it more than once."""
	if frappe.db.exists("Company", {"company_name": _DEMO_COMPANY_NAME}):
		return f"seed_demo_company: '{_DEMO_COMPANY_NAME}' already exists, skipped."

	from erpnext.setup.setup_wizard.setup_wizard import setup_complete

	current_year = frappe.utils.nowdate()[:4]
	args = frappe._dict(
		{
			"country": "Vietnam",
			"language": "english",
			"timezone": "Asia/Ho_Chi_Minh",
			"currency": "VND",
			"full_name": "Administrator",
			"email": "admin@example.com",
			"company_name": _DEMO_COMPANY_NAME,
			"company_abbr": _DEMO_COMPANY_ABBR,
			"fy_start_date": f"{current_year}-01-01",
			"fy_end_date": f"{current_year}-12-31",
			"chart_of_accounts": "Standard",
			"domain": "Manufacturing",
			"bank_account": "",
		}
	)
	setup_complete(args)
	return (
		f"seed_demo_company: created Company '{_DEMO_COMPANY_NAME}' ({_DEMO_COMPANY_ABBR}) "
		f"with Fiscal Year {current_year}, Standard Chart of Accounts, VND currency."
	)


def _ensure_root_item_group():
	if not frappe.db.exists("Item Group", _ROOT_ITEM_GROUP):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": _ROOT_ITEM_GROUP,
				"is_group": 1,
				"parent_item_group": "",
			}
		).insert(ignore_permissions=True)


def _ensure_item_groups():
	_ensure_root_item_group()
	for name in _ITEM_GROUPS:
		if frappe.db.exists("Item Group", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": name,
				"is_group": 0,
				"parent_item_group": _ROOT_ITEM_GROUP,
			}
		).insert(ignore_permissions=True)


def _ensure_warehouses(company_abbr):
	all_warehouses = f"All Warehouses - {company_abbr}"
	for name in _WAREHOUSES:
		full_name = f"{name} - {company_abbr}"
		if frappe.db.exists("Warehouse", full_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": name,
				"company": _DEMO_COMPANY_NAME,
				"parent_warehouse": all_warehouses,
			}
		).insert(ignore_permissions=True)


def _ensure_items(item_list, has_batch_and_expiry=False):
	for item_code, item_name, item_group, stock_uom in item_list:
		if frappe.db.exists("Item", item_code):
			continue
		doc = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name,
			"item_group": item_group,
			"stock_uom": stock_uom,
			"is_stock_item": 1,
			"has_batch_no": 1 if has_batch_and_expiry else 0,
			"has_expiry_date": 1 if has_batch_and_expiry else 0,
			"create_new_batch": 1 if has_batch_and_expiry else 0,
		}
		if has_batch_and_expiry:
			# ERPNext requires a positive shelf life whenever has_expiry_date is set.
			# 730 days (2 years) is a generic placeholder, not a real specification —
			# real expiry rules belong to CE-08 (LIMS)/CE-15 (RA) once those exist.
			doc["shelf_life_in_days"] = 730
		frappe.get_doc(doc).insert(ignore_permissions=True)


def _ensure_bom():
	if frappe.db.exists("BOM", {"item": "PARA-500-TAB", "is_active": 1}):
		return False
	bom = frappe.get_doc(
		{
			"doctype": "BOM",
			"item": "PARA-500-TAB",
			"quantity": 1000,
			"uom": "Nos",
			"company": _DEMO_COMPANY_NAME,
			"is_active": 1,
			"is_default": 1,
		}
	)
	for item_code, qty in _PARA_500_BOM_ITEMS:
		bom.append("items", {"item_code": item_code, "qty": qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def _ensure_batch_tracking_enabled():
	"""v16's newer Serial and Batch Bundle stock model is OFF by default — creating a Purchase
	Receipt/Stock Entry against a has_batch_no item fails until this is turned on. Found via
	the actual error message when seed_purchase_flow first ran, not from documentation."""
	settings = frappe.get_single("Stock Settings")
	changed = False
	if not settings.enable_serial_and_batch_no_for_item:
		settings.enable_serial_and_batch_no_for_item = 1
		changed = True
	if not settings.use_serial_batch_fields:
		settings.use_serial_batch_fields = 1
		changed = True
	if changed:
		settings.save(ignore_permissions=True)


def seed_pharma_master_data():
	"""DP-501 — Item Group tree, Warehouses, Items and BOM for master plan §7 DEMO 01.
	Requires the demo Company to exist first (run seed_demo_company before this one —
	enforced by `sequence` on the Industry Pack Seed rows, not by this function itself)."""
	if not frappe.db.exists("Company", {"company_name": _DEMO_COMPANY_NAME}):
		return "seed_pharma_master_data: SKIPPED — demo Company does not exist yet, run seed_demo_company first."

	_ensure_batch_tracking_enabled()
	_ensure_item_groups()
	_ensure_warehouses(_DEMO_COMPANY_ABBR)
	_ensure_items(_RAW_MATERIALS, has_batch_and_expiry=True)
	_ensure_items(_PACKAGING_MATERIALS, has_batch_and_expiry=False)
	_ensure_items(_FINISHED_GOODS, has_batch_and_expiry=True)
	bom_created = _ensure_bom()

	return (
		f"seed_pharma_master_data: ensured {len(_ITEM_GROUPS)} item groups, "
		f"{len(_WAREHOUSES)} warehouses, {len(_RAW_MATERIALS) + len(_PACKAGING_MATERIALS) + len(_FINISHED_GOODS)} items. "
		f"BOM for PARA-500-TAB {'created' if bom_created else 'already existed'}."
	)


_SUPPLIER_GROUP = "Raw Material Suppliers"
_SUPPLIER_NAME = "ABC Pharma Chemicals Co."

# Purchase quantities sized to fully cover one 1000-unit BOM batch of PARA-500-TAB.
_PURCHASE_ITEMS = [
	("PARA-API", 500, "Kg"),
	("MCC", 300, "Kg"),
	("PVP-K30", 100, "Kg"),
	("MG-STEARATE", 20, "Kg"),
	("PVC-ALU", 1000, "Nos"),
	("CARTON-PRINTED", 1000, "Nos"),
]

_RM_QUARANTINE_WAREHOUSE = f"RM Quarantine - {_DEMO_COMPANY_ABBR}"


def _ensure_supplier():
	if not frappe.db.exists("Supplier Group", _SUPPLIER_GROUP):
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": _SUPPLIER_GROUP,
				"is_group": 0,
				"parent_supplier_group": "All Supplier Groups",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Supplier", _SUPPLIER_NAME):
		frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": _SUPPLIER_NAME,
				"supplier_group": _SUPPLIER_GROUP,
				"supplier_type": "Company",
				"country": "Vietnam",
			}
		).insert(ignore_permissions=True)


def _ensure_purchase_order():
	existing = frappe.db.exists("Purchase Order", {"supplier": _SUPPLIER_NAME, "docstatus": 1})
	if existing:
		return existing, False
	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"supplier": _SUPPLIER_NAME,
			"company": _DEMO_COMPANY_NAME,
			"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
		}
	)
	for item_code, qty, uom in _PURCHASE_ITEMS:
		po.append(
			"items",
			{
				"item_code": item_code,
				"qty": qty,
				"uom": uom,
				"warehouse": _RM_QUARANTINE_WAREHOUSE,
				"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
			},
		)
	po.insert(ignore_permissions=True)
	po.submit()
	return po.name, True


def _ensure_purchase_receipt(po_name):
	if frappe.db.exists("Purchase Receipt", {"supplier": _SUPPLIER_NAME, "docstatus": 1}):
		return False
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	pr = make_purchase_receipt(po_name)
	pr.insert(ignore_permissions=True)
	pr.submit()
	return True


def seed_purchase_flow():
	"""DP-502 — Supplier -> Purchase Order -> Purchase Receipt, all raw/packaging materials
	received into RM Quarantine (not RM Approved) — matches master plan §7 DEMO 01 test P01
	("Không thể xuất nguyên liệu Quarantine vào production"): the actual quarantine-blocks-
	production GATE is a separate, later concern (DP-503/504 — no custom validation exists
	yet), this task only proves material correctly lands in Quarantine on receipt, with a
	real Batch per has_batch_no item (Frappe's Serial and Batch Bundle mechanism, not a bare
	batch_no field — that's the modern v15+/v16 stock transaction model)."""
	if not frappe.db.exists("Company", {"company_name": _DEMO_COMPANY_NAME}):
		return "seed_purchase_flow: SKIPPED — demo Company does not exist yet, run seed_demo_company first."
	if not frappe.db.exists("Item", "PARA-API"):
		return "seed_purchase_flow: SKIPPED — master data does not exist yet, run seed_pharma_master_data first."

	_ensure_supplier()
	po_name, po_created = _ensure_purchase_order()
	pr_created = _ensure_purchase_receipt(po_name)

	return (
		f"seed_purchase_flow: Supplier '{_SUPPLIER_NAME}' ensured. "
		f"Purchase Order {'created' if po_created else 'already existed'} ({po_name}). "
		f"Purchase Receipt {'created' if pr_created else 'already existed'}, "
		f"materials received into '{_RM_QUARANTINE_WAREHOUSE}'."
	)


_RM_APPROVED_WAREHOUSE = f"RM Approved - {_DEMO_COMPANY_ABBR}"

# Approve ALL 6 BOM items (4 raw materials + 2 packaging) — DP-504 (Manufacturing) needs
# every BOM component available in Approved to actually build PARA-500-TAB. An earlier
# version of this only approved 3 of 4 raw materials to leave one deliberately in Quarantine
# for the negative test below — that broke DP-504 (MG-STEARATE, part of the BOM, had no
# valuation rate in Approved since it was never transferred there). The negative test below
# doesn't need a withheld item: the quarantine-block hook fires on warehouse name alone,
# before any stock-sufficiency check, so it works even against an item with zero balance
# in Quarantine — proven by construction, not by leaving something artificially unapproved.
_ITEMS_TO_APPROVE = ["PARA-API", "MCC", "PVP-K30", "MG-STEARATE", "PVC-ALU", "CARTON-PRINTED"]
_BATCH_TRACKED_ITEMS = {"PARA-API", "MCC", "PVP-K30", "MG-STEARATE"}


def _ensure_qc_release_transfer():
	# Per-item check, not "does any transfer exist" — that looser check let a site stay stuck
	# on a stale partial transfer (e.g. pharmacountry.vn still had only the pre-DP-503-fix
	# 3-item version) and never pick up the missing items on re-run. Only transfers what's
	# actually missing from RM Approved, so this is safe to re-run against a partially-synced
	# site as well as a fresh one.
	missing = [
		(item_code, purchase_qty, uom)
		for item_code, purchase_qty, uom in _PURCHASE_ITEMS
		if not frappe.db.exists(
			"Stock Ledger Entry", {"warehouse": _RM_APPROVED_WAREHOUSE, "item_code": item_code, "is_cancelled": 0}
		)
	]
	if not missing:
		return False

	missing_batch_tracked = [item_code for item_code, _qty, _uom in missing if item_code in _BATCH_TRACKED_ITEMS]
	batches = {
		row.item: row.name
		for row in frappe.get_all("Batch", filters={"item": ["in", missing_batch_tracked]}, fields=["name", "item"])
	}
	if len(batches) != len(missing_batch_tracked):
		frappe.throw("_ensure_qc_release_transfer: missing batches for one or more items — run seed_purchase_flow first.")

	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Transfer",
			"purpose": "Material Transfer",
			"company": _DEMO_COMPANY_NAME,
		}
	)
	for item_code, purchase_qty, _uom in missing:
		row = {
			"item_code": item_code,
			"qty": purchase_qty,
			"s_warehouse": _RM_QUARANTINE_WAREHOUSE,
			"t_warehouse": _RM_APPROVED_WAREHOUSE,
			"use_serial_batch_fields": 1,
		}
		if item_code in _BATCH_TRACKED_ITEMS:
			row["batch_no"] = batches[item_code]
		se.append("items", row)
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def seed_warehouse_flow():
	"""DP-503 — moves all 6 QC-passed BOM items from RM Quarantine to RM Approved via a
	submitted Material Transfer Stock Entry (simulating "QC sampling passed, released for
	use" — CE-08/LIMS itself doesn't exist yet, this just gets the warehouse state right for
	DP-504 Manufacturing). Also the real proof point for the quarantine-issue-blocked
	validation registered in hooks.py: attempts a Material Issue straight from Quarantine
	and confirms it's rejected — master plan §7 DEMO 01 test P01."""
	if not frappe.db.exists("Purchase Receipt", {"supplier": _SUPPLIER_NAME, "docstatus": 1}):
		return "seed_warehouse_flow: SKIPPED — no received stock yet, run seed_purchase_flow first."

	transfer_created = _ensure_qc_release_transfer()

	# Negative test: confirms the hook actually blocks a Quarantine issue, don't just trust
	# that it's wired. Uses PARA-API even though its Quarantine balance is now 0 after the
	# transfer above — the hook checks warehouse identity in validate(), before any
	# stock-sufficiency check runs, so this proves the rule itself, not incidentally-present
	# stock.
	#
	# BUG FOUND 2026-09-28: this used to call frappe.db.rollback() in the except branch to
	# "undo the bad test entry" — but rollback() undoes the ENTIRE uncommitted transaction,
	# not just this one insert, which silently erased the legitimate QC release transfer
	# created a few lines above in the SAME bench-execute call. Fixed by deleting only the
	# specific leftover draft document instead of rolling back anything.
	blocked_correctly = False
	bad_se_name = None
	try:
		bad_se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"purpose": "Material Issue",
				"company": _DEMO_COMPANY_NAME,
				"items": [
					{
						"item_code": "PARA-API",
						"qty": 1,
						"s_warehouse": _RM_QUARANTINE_WAREHOUSE,
						"use_serial_batch_fields": 1,
					}
				],
			}
		)
		bad_se.insert(ignore_permissions=True)
		bad_se_name = bad_se.name
		bad_se.submit()
		frappe.delete_doc("Stock Entry", bad_se.name, force=1)  # only reached if the block FAILED to fire
		bad_se_name = None
	except frappe.ValidationError:
		blocked_correctly = True
		if bad_se_name:
			# validate() threw before any stock ledger write, so this draft is inert —
			# just tidy it up, no transaction-level undo needed or wanted.
			frappe.delete_doc("Stock Entry", bad_se_name, force=1, ignore_permissions=True)

	return (
		f"seed_warehouse_flow: QC release transfer {'created' if transfer_created else 'already existed'} "
		f"for all {len(_ITEMS_TO_APPROVE)} BOM items (Quarantine -> Approved). "
		f"Quarantine-issue-blocked validation: {'CONFIRMED working' if blocked_correctly else 'DID NOT FIRE — investigate'}."
	)


_FG_QUARANTINE_WAREHOUSE = f"FG Quarantine - {_DEMO_COMPANY_ABBR}"
_FG_RELEASED_WAREHOUSE = f"FG Released - {_DEMO_COMPANY_ABBR}"
_WORK_ORDER_QTY = 1000


def _ensure_work_order():
	existing = frappe.db.exists("Work Order", {"production_item": "PARA-500-TAB", "docstatus": 1})
	if existing:
		return existing, False
	# looked up rather than hardcoded — a cancelled BOM keeps its old name, so a corrected
	# replacement BOM for the same item gets a different autoname (DP-504 incident)
	active_bom = frappe.db.get_value("BOM", {"item": "PARA-500-TAB", "is_active": 1})
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": "PARA-500-TAB",
			"bom_no": active_bom,
			"qty": _WORK_ORDER_QTY,
			"company": _DEMO_COMPANY_NAME,
			"source_warehouse": _RM_APPROVED_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"skip_transfer": 1,  # no WIP step — BOM has no operations/routing, single-step Manufacture entry
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo.name, True


def _ensure_manufacture_entry(wo_name):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=_WORK_ORDER_QTY)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def seed_manufacturing_flow():
	"""DP-504 — Work Order for PARA-500-TAB (qty 1000, per the BOM from DP-501), consuming
	raw materials from RM Approved (never Quarantine — the DP-503 hook would correctly
	reject that) and producing finished goods into FG Quarantine (still needs QC/QA release
	before FG Released — that gate is DP-506, not yet built)."""
	if not frappe.db.exists("BOM", {"item": "PARA-500-TAB", "is_active": 1}):
		return "seed_manufacturing_flow: SKIPPED — BOM does not exist yet, run seed_pharma_master_data first."
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _RM_APPROVED_WAREHOUSE, "is_cancelled": 0}):
		return "seed_manufacturing_flow: SKIPPED — no approved raw material stock yet, run seed_warehouse_flow first."

	wo_name, wo_created = _ensure_work_order()
	se_created = _ensure_manufacture_entry(wo_name)

	return (
		f"seed_manufacturing_flow: Work Order {'created' if wo_created else 'already existed'} ({wo_name}), "
		f"qty {_WORK_ORDER_QTY}. Manufacture Stock Entry {'created' if se_created else 'already existed'}, "
		f"raw materials consumed from '{_RM_APPROVED_WAREHOUSE}', finished goods received into '{_FG_QUARANTINE_WAREHOUSE}'."
	)


def _ensure_incoming_qc():
	"""DP-505 — one Accepted Quality Inspection per batch-tracked raw material, referencing
	the DP-502 Purchase Receipt and that item's specific batch. Uses ERPNext's native Quality
	Inspection doctype (inspection_type=Incoming) rather than a hand-rolled QC record, matching
	master plan §7 DEMO 01's "Sampling/QC" workflow step."""
	pr_name = frappe.db.get_value("Purchase Receipt", {"supplier": _SUPPLIER_NAME, "docstatus": 1}, "name")
	if not pr_name:
		return 0
	created = 0
	for item_code in _BATCH_TRACKED_ITEMS:
		if frappe.db.exists("Quality Inspection", {"reference_name": pr_name, "item_code": item_code}):
			continue
		# these items were created by DP-501's seed_pharma_master_data before this flag
		# existed — flip it directly rather than only setting it on future inserts.
		if not frappe.db.get_value("Item", item_code, "inspection_required_before_purchase"):
			frappe.db.set_value("Item", item_code, "inspection_required_before_purchase", 1)
		batch_no = frappe.db.get_value("Batch", {"item": item_code}, "name")
		qi = frappe.get_doc(
			{
				"doctype": "Quality Inspection",
				"inspection_type": "Incoming",
				"reference_type": "Purchase Receipt",
				"reference_name": pr_name,
				"item_code": item_code,
				"batch_no": batch_no,
				"sample_size": 1,
				"status": "Accepted",
				"company": _DEMO_COMPANY_NAME,
				"inspected_by": frappe.session.user,
			}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		created += 1
	return created


def _ensure_fg_qc():
	"""DP-505 — In-Process QC (IPC, master plan §7 DEMO 01 test P05) for the manufactured
	PARA-500-TAB batch, referencing the DP-504 Manufacture Stock Entry. This is the record
	DP-506 (QA release) will require before FG can move from Quarantine to Released — the
	two are deliberately separate: QC tests the batch, QA authorizes the release."""
	se_name = frappe.db.get_value(
		"Stock Entry", {"purpose": "Manufacture", "docstatus": 1, "work_order": ["is", "set"]}, "name"
	)
	if not se_name:
		return False
	if frappe.db.exists("Quality Inspection", {"reference_name": se_name, "item_code": "PARA-500-TAB"}):
		return False
	batch_no = frappe.db.get_value("Batch", {"item": "PARA-500-TAB", "batch_qty": [">", 0]}, "name")
	qi = frappe.get_doc(
		{
			"doctype": "Quality Inspection",
			"inspection_type": "In Process",
			"reference_type": "Stock Entry",
			"reference_name": se_name,
			"item_code": "PARA-500-TAB",
			"batch_no": batch_no,
			"sample_size": 10,
			"status": "Accepted",
			"company": _DEMO_COMPANY_NAME,
			"inspected_by": frappe.session.user,
		}
	)
	qi.insert(ignore_permissions=True)
	qi.submit()
	return True


def seed_qc_flow():
	"""DP-505 — QC records bridging DP-502 (incoming raw materials) and DP-504 (manufactured
	FG) to DP-506 (QA release, not yet built)."""
	if not frappe.db.exists("Stock Entry", {"purpose": "Manufacture", "docstatus": 1}):
		return "seed_qc_flow: SKIPPED — no manufactured batch yet, run seed_manufacturing_flow first."

	incoming_created = _ensure_incoming_qc()
	fg_created = _ensure_fg_qc()

	return (
		f"seed_qc_flow: Incoming QC — {incoming_created} Quality Inspection(s) created for raw materials "
		f"(or already existed). FG In-Process QC — {'created' if fg_created else 'already existed'} for "
		f"PARA-500-TAB."
	)


def _ensure_qa_release():
	if frappe.db.exists(
		"Stock Ledger Entry", {"warehouse": _FG_RELEASED_WAREHOUSE, "item_code": "PARA-500-TAB", "is_cancelled": 0}
	):
		return False
	# derived from the Accepted QC record itself, not a generic "any batch with qty>0" lookup
	# — that was ambiguous whenever a second (e.g. test) batch briefly existed alongside the
	# real one, and QA release should release exactly the batch QC actually approved anyway.
	batch_no = frappe.db.get_value(
		"Quality Inspection", {"item_code": "PARA-500-TAB", "status": "Accepted", "docstatus": 1}, "batch_no"
	)
	if not batch_no:
		frappe.throw("_ensure_qa_release: no Accepted Quality Inspection for PARA-500-TAB found — run seed_qc_flow first.")
	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Transfer",
			"purpose": "Material Transfer",
			"company": _DEMO_COMPANY_NAME,
		}
	)
	se.append(
		"items",
		{
			"item_code": "PARA-500-TAB",
			"qty": _WORK_ORDER_QTY,
			"s_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"t_warehouse": _FG_RELEASED_WAREHOUSE,
			"batch_no": batch_no,
			"use_serial_batch_fields": 1,
		},
	)
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _test_qa_release_requires_qc():
	"""Negative test for master plan §7 DEMO 01 test P06. Receives a tiny synthetic 1-unit
	PARA-500-TAB batch straight into FG Quarantine (no linked Quality Inspection), then
	attempts to release it to FG Released — must be blocked by block_fg_release_without_qa.
	Marker text in the receipt's remarks makes the synthetic batch identifiable and this
	function safely skippable/idempotent on re-run."""
	marker = "DP-506 negative test batch"
	if frappe.db.exists("Stock Entry", {"remarks": marker}):
		return True

	receipt = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": _DEMO_COMPANY_NAME,
			"remarks": marker,
		}
	)
	receipt.append(
		"items",
		{
			"item_code": "PARA-500-TAB",
			"qty": 1,
			"t_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"use_serial_batch_fields": 1,
			"basic_rate": 0,
		},
	)
	receipt.insert(ignore_permissions=True)
	receipt.submit()
	# v16's Serial and Batch Bundle mechanism doesn't populate `batch_no` on the in-memory
	# child row after an auto-created batch — it only lands in the DB via a linked "Serial
	# and Batch Bundle" doc, discoverable by re-querying the just-submitted row. Skipping this
	# and leaving batch_no unset on the release attempt below let ERPNext auto-pick ANY
	# available batch in the source warehouse for the transfer — including the real, already
	# QC-approved batch — which silently defeated this negative test (found by making the
	# test report its own actual batch_no/result instead of only pass/fail).
	bundle_name = frappe.db.get_value(
		"Stock Entry Detail", {"parent": receipt.name, "item_code": "PARA-500-TAB"}, "serial_and_batch_bundle"
	)
	test_batch_no = frappe.db.get_value("Serial and Batch Entry", {"parent": bundle_name}, "batch_no")

	release_attempt = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Transfer",
			"purpose": "Material Transfer",
			"company": _DEMO_COMPANY_NAME,
		}
	)
	release_attempt.append(
		"items",
		{
			"item_code": "PARA-500-TAB",
			"qty": 1,
			"s_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"t_warehouse": _FG_RELEASED_WAREHOUSE,
			"batch_no": test_batch_no,
			"use_serial_batch_fields": 1,
		}
	)
	blocked = False
	try:
		release_attempt.insert(ignore_permissions=True)
		release_attempt.submit()
	except frappe.ValidationError:
		blocked = True

	if not blocked:
		frappe.throw("DP-506 negative test FAILED: release without QC was not blocked by block_fg_release_without_qa!")
	return True


def seed_qa_release():
	"""DP-506 — QA release: moves the manufactured PARA-500-TAB batch from FG Quarantine to
	FG Released, gated by block_fg_release_without_qa (requires the DP-505 Accepted Quality
	Inspection for that batch). Also runs the P06 negative test proving the gate actually
	blocks an unapproved batch."""
	if not frappe.db.exists("Quality Inspection", {"item_code": "PARA-500-TAB", "status": "Accepted", "docstatus": 1}):
		return "seed_qa_release: SKIPPED — no Accepted Quality Inspection for PARA-500-TAB yet, run seed_qc_flow first."

	block_confirmed = _test_qa_release_requires_qc()
	release_created = _ensure_qa_release()

	return (
		f"seed_qa_release: QA-release-without-QC block CONFIRMED working. "
		f"FG batch {'released to' if release_created else 'already in'} '{_FG_RELEASED_WAREHOUSE}'."
	)


_QUALITY_PROCEDURE_NAME = "SOP - Paracetamol 500 mg Tablet Manufacturing"
_DEVIATION_SUBJECT = "Minor temperature excursion during IPC sampling — Batch 552242D"


def _ensure_quality_procedure():
	if frappe.db.exists("Quality Procedure", {"quality_procedure_name": _QUALITY_PROCEDURE_NAME}):
		return False
	frappe.get_doc(
		{
			"doctype": "Quality Procedure",
			"quality_procedure_name": _QUALITY_PROCEDURE_NAME,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_deviation_record():
	"""master plan §7 DEMO 01 build step 9 calls for "1 batch có deviation" among the demo
	batches — represented here as a Non Conformance (ERPNext's native QMS doctype) against
	the manufactured PARA-500-TAB batch, with corrective/preventive action text filled in and
	status Resolved (the deviation was investigated and closed, not left open)."""
	if frappe.db.exists("Non Conformance", {"subject": _DEVIATION_SUBJECT}):
		return False
	frappe.get_doc(
		{
			"doctype": "Non Conformance",
			"subject": _DEVIATION_SUBJECT,
			"procedure": _QUALITY_PROCEDURE_NAME,
			"status": "Resolved",
			"process_owner": frappe.session.user,
			"details": (
				"In-process control (IPC) sampling during compression recorded a brief excursion "
				"above the SOP's specified temperature range. Batch 552242D was placed on hold "
				"pending QA investigation."
			),
			"corrective_action": (
				"Compression room HVAC setpoint verified and recalibrated. Batch re-sampled at "
				"three additional timepoints — all results within specification. Hold released by QA."
			),
			"preventive_action": (
				"Added a room-temperature check to the IPC checklist and reduced the HVAC "
				"maintenance interval for the compression suite."
			),
		}
	).insert(ignore_permissions=True)
	return True


def seed_qms_integration():
	"""DP-507 — QMS integration (CE-06): links the pharma demo to ERPNext's native Quality
	Procedure/Non Conformance doctypes rather than a bespoke QMS build. A Quality Procedure
	(SOP) for PARA-500-TAB manufacturing, referenced by a Non Conformance representing the
	"1 batch có deviation" scenario the master plan's guided demo calls for."""
	procedure_created = _ensure_quality_procedure()
	deviation_created = _ensure_deviation_record()
	return (
		f"seed_qms_integration: Quality Procedure {'created' if procedure_created else 'already existed'}. "
		f"Deviation (Non Conformance) {'created' if deviation_created else 'already existed'}."
	)


def seed_dms_integration():
	"""DP-508 — stub. Unlike DP-507 (QMS), core ERPNext ships no dedicated Document
	Management System doctype (only generic File attachments) — a real DMS (versioned SOPs,
	obsolete-document blocking per master plan test P10) needs CE-07 built as its own module,
	which doesn't exist yet. Left as an honest stub rather than force-fitting File records into
	something they're not."""
	return "seed_dms_integration: stub — full DMS (versioned documents, obsolete-blocking per test P10) needs CE-07 built; no native ERPNext doctype covers it."


_EAM_LOCATION_NAME = "Production Floor - DPC"
_EAM_ASSET_CATEGORY = "Manufacturing Equipment"
_EAM_ITEM_CODE = "EQUIP-TC-01"
_EAM_ASSET_NAME = "Tablet Compression Machine #1"
_EAM_MAINTENANCE_TEAM = "Pharma Maintenance Team"
_EAM_MAINTENANCE_USER = "maintenance@pharmacountry.vn"


def _ensure_eam_maintenance_user():
	"""ERPNext's Asset Maintenance Task auto-assignment (assign_tasks() in
	erpnext/assets/doctype/asset_maintenance/asset_maintenance.py) resolves the assignee via
	`frappe.db.get_value("User", assign_to_member, "email")` and then uses THAT email as if it
	were the User's docname for the actual ToDo assignment — this only works for a normal user
	whose docname already equals their email. "Administrator" fails this (its docname and
	email field differ), so a real user is needed here rather than reusing Administrator."""
	if frappe.db.exists("User", _EAM_MAINTENANCE_USER):
		return False
	frappe.get_doc(
		{
			"doctype": "User",
			"email": _EAM_MAINTENANCE_USER,
			"first_name": "Maintenance",
			"last_name": "Officer",
			"send_welcome_email": 0,
			"roles": [{"role": "Maintenance Manager"}],
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_eam_location():
	if frappe.db.exists("Location", _EAM_LOCATION_NAME):
		return False
	frappe.get_doc({"doctype": "Location", "location_name": _EAM_LOCATION_NAME}).insert(ignore_permissions=True)
	return True


def _ensure_eam_asset_category():
	if frappe.db.exists("Asset Category", _EAM_ASSET_CATEGORY):
		return False
	frappe.get_doc(
		{
			"doctype": "Asset Category",
			"asset_category_name": _EAM_ASSET_CATEGORY,
			"accounts": [
				{
					"company_name": _DEMO_COMPANY_NAME,
					"fixed_asset_account": f"Plants and Machineries - {_DEMO_COMPANY_ABBR}",
					"accumulated_depreciation_account": f"Accumulated Depreciation - {_DEMO_COMPANY_ABBR}",
					"depreciation_expense_account": f"Depreciation - {_DEMO_COMPANY_ABBR}",
				}
			],
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_eam_equipment_item():
	if frappe.db.exists("Item", _EAM_ITEM_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": _EAM_ITEM_CODE,
			"item_name": "Tablet Compression Machine",
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_fixed_asset": 1,
			"asset_category": _EAM_ASSET_CATEGORY,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_eam_asset():
	if frappe.db.exists("Asset", {"asset_name": _EAM_ASSET_NAME}):
		return False
	asset = frappe.get_doc(
		{
			"doctype": "Asset",
			"item_code": _EAM_ITEM_CODE,
			"asset_name": _EAM_ASSET_NAME,
			"company": _DEMO_COMPANY_NAME,
			"location": _EAM_LOCATION_NAME,
			"purchase_date": "2024-01-15",
			"available_for_use_date": "2024-01-20",
			"gross_purchase_amount": 500000000,
			"net_purchase_amount": 500000000,
			"asset_quantity": 1,
		}
	)
	asset.insert(ignore_permissions=True)
	asset.submit()
	return True


def _ensure_eam_maintenance():
	asset_docname = frappe.db.get_value("Asset", {"asset_name": _EAM_ASSET_NAME}, "name")
	if not asset_docname:
		frappe.throw("_ensure_eam_maintenance: Asset not found — run _ensure_eam_asset first.")
	if frappe.db.exists("Asset Maintenance", {"asset_name": asset_docname}):
		return False
	if not frappe.db.exists("Asset Maintenance Team", _EAM_MAINTENANCE_TEAM):
		frappe.get_doc(
			{
				"doctype": "Asset Maintenance Team",
				"maintenance_team_name": _EAM_MAINTENANCE_TEAM,
				"company": _DEMO_COMPANY_NAME,
				"maintenance_team_members": [
					{"team_member": _EAM_MAINTENANCE_USER, "maintenance_role": "Maintenance Manager"}
				],
			}
		).insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Asset Maintenance",
			# despite the field name, this Link expects the Asset's docname, not its asset_name label
			"asset_name": asset_docname,
			"company": _DEMO_COMPANY_NAME,
			"maintenance_team": _EAM_MAINTENANCE_TEAM,
			"asset_maintenance_tasks": [
				{
					"maintenance_task": "Monthly calibration check",
					"periodicity": "Monthly",
					"start_date": frappe.utils.nowdate(),
					"maintenance_status": "Planned",
					"assign_to": _EAM_MAINTENANCE_USER,
				}
			],
		}
	).insert(ignore_permissions=True)
	return True


def seed_eam_flow():
	"""DP-509 — EAM/CMMS (CE-09): a manufacturing Equipment record (master plan §7 DEMO 01's
	"Equipment" master data requirement) using ERPNext's native Assets module, plus a
	maintenance schedule — a calibration task — matching CE-09's validation/calibration scope."""
	_ensure_eam_maintenance_user()
	_ensure_eam_location()
	_ensure_eam_asset_category()
	_ensure_eam_equipment_item()
	asset_created = _ensure_eam_asset()
	maintenance_created = _ensure_eam_maintenance()
	return (
		f"seed_eam_flow: Asset '{_EAM_ASSET_NAME}' {'created' if asset_created else 'already existed'}. "
		f"Maintenance schedule {'created' if maintenance_created else 'already existed'}."
	)


_DASHBOARD_NAME = "Pharma Golden Demo"
_NUMBER_CARDS = [
	# (card_name, doctype, filters, function, aggregate_field)
	("Accepted Quality Inspections", "Quality Inspection", [["Quality Inspection", "status", "=", "Accepted"]], "Count", None),
	("Resolved Deviations", "Non Conformance", [["Non Conformance", "status", "=", "Resolved"]], "Count", None),
	("Purchase Orders (Pharma)", "Purchase Order", [["Purchase Order", "supplier", "=", _SUPPLIER_NAME]], "Count", None),
]


def _ensure_number_cards():
	created = 0
	for card_name, doctype, filters, function, aggregate_field in _NUMBER_CARDS:
		if frappe.db.exists("Number Card", card_name):
			continue
		doc = {
			"doctype": "Number Card",
			"label": card_name,
			"document_type": doctype,
			"type": "Document Type",
			"function": function,
			"filters_json": frappe.as_json(filters),
			"is_public": 1,
		}
		if aggregate_field:
			doc["aggregate_function_based_on"] = aggregate_field
		frappe.get_doc(doc).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_dashboard_chart():
	chart_name = "Quality Inspections Count"
	if frappe.db.exists("Dashboard Chart", chart_name):
		return False
	frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": chart_name,
			"chart_type": "Count",
			"document_type": "Quality Inspection",
			"based_on": "creation",
			"type": "Bar",
			"timeseries": 1,
			"time_interval": "Monthly",
			"filters_json": "[]",
			"is_public": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_dashboard():
	if frappe.db.exists("Dashboard", _DASHBOARD_NAME):
		return False
	frappe.get_doc(
		{
			"doctype": "Dashboard",
			"dashboard_name": _DASHBOARD_NAME,
			"is_default": 0,
			"charts": [{"chart": "Quality Inspections Count"}],
			"cards": [{"card": card_name} for card_name, *_ in _NUMBER_CARDS],
		}
	).insert(ignore_permissions=True)
	return True


def seed_dashboard():
	"""DP-510 — a small operational dashboard (master plan §7 DEMO 01 build step 8, "Tạo
	dashboard") built from data this session's own seed functions actually created: Accepted
	QC count (DP-505), Resolved Deviations (DP-507), Purchase Orders for the demo Supplier
	(DP-502), plus a Quality Inspection count chart."""
	cards_created = _ensure_number_cards()
	chart_created = _ensure_dashboard_chart()
	dashboard_created = _ensure_dashboard()
	return (
		f"seed_dashboard: {cards_created} Number Card(s) created (or already existed). "
		f"Chart {'created' if chart_created else 'already existed'}. "
		f"Dashboard '{_DASHBOARD_NAME}' {'created' if dashboard_created else 'already existed'}."
	)


# ERPNext's native Quality module has one role ("Quality Manager") for its whole quality
# workflow — no Director/Manager/Analyst seniority split. QUALITY_DIRECTOR, QA_MANAGER,
# QC_MANAGER and ANALYST all map to it here; separating them for real would need Role
# Permission Manager fine-tuning, out of scope for this demo.
_ROLE_TEMPLATE_FRAPPE_ROLE = {
	"GENERAL_DIRECTOR": "Analytics",
	"QUALITY_DIRECTOR": "Quality Manager",
	"QA_MANAGER": "Quality Manager",
	"QC_MANAGER": "Quality Manager",
	"PRODUCTION_MANAGER": "Manufacturing Manager",
	"PLANNING_OFFICER": "Manufacturing User",
	"WAREHOUSE_OFFICER": "Stock User",
	"PROCUREMENT_OFFICER": "Purchase User",
	"MAINTENANCE": "Maintenance Manager",
	"ANALYST": "Quality Manager",
	"OPERATOR": "Manufacturing User",
}
_DEMO_USER_DOMAIN = "pharmacountry.vn"
_DEMO_USER_PASSWORD = "Demo@1234"


def _ensure_role_template_mappings():
	updated = 0
	for template_code, frappe_role in _ROLE_TEMPLATE_FRAPPE_ROLE.items():
		if not frappe.db.exists("Role Template", template_code):
			continue
		if frappe.db.get_value("Role Template", template_code, "frappe_role") == frappe_role:
			continue
		frappe.db.set_value("Role Template", template_code, "frappe_role", frappe_role)
		updated += 1
	return updated


def _ensure_demo_users():
	role_templates = frappe.get_all(
		"Role Template",
		filters={"name": ["in", list(_ROLE_TEMPLATE_FRAPPE_ROLE)]},
		fields=["name", "template_name", "frappe_role"],
	)
	created = 0
	for rt in role_templates:
		email = f"{rt.name.lower().replace('_', '.')}@{_DEMO_USER_DOMAIN}"
		if frappe.db.exists("User", email):
			continue
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": rt.template_name,
				"send_welcome_email": 0,
				"new_password": _DEMO_USER_PASSWORD,
				"roles": [{"role": rt.frappe_role}] if rt.frappe_role else [],
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def seed_demo_users():
	"""DP-405 (Demo Factory) — maps IP-PHARMA's 11 Role Templates to real Frappe Roles (best
	native fit — see _ROLE_TEMPLATE_FRAPPE_ROLE comment for the Quality-module limitation),
	then creates one demo User per role. Deliberately NOT given System Manager, so logging in
	as each actually demonstrates permission boundaries rather than superuser access. All demo
	users share one placeholder password (_DEMO_USER_PASSWORD) — a demo convenience, not a
	real credential."""
	mappings_updated = _ensure_role_template_mappings()
	users_created = _ensure_demo_users()
	return (
		f"seed_demo_users: {mappings_updated} Role Template->Frappe Role mapping(s) applied. "
		f"{users_created} demo User(s) created (or already existed)."
	)


def seed_demo_scenario():
	return "seed_demo_scenario: stub — would create an end-to-end batch scenario (PO -> receipt -> WO -> QC -> release) once CE-06/08 are built here."


# ============================================================================
# Golden Demo #2 — Pharmaceutical Import & Distribution (master plan DEMO 05,
# "PHASE 3 — First 8 Golden Demos" item 2). Reuses the SAME Demo Pharma Co / IP-PHARMA as
# Golden Demo #1 (Manufacturing) — DP-303's _INDUSTRY_PACKS has no separate distribution
# pack; the master plan groups pharma manufacturing and distribution demos under one
# industry pack, not two. Starts from the FG Released stock DP-506 already produced.
# ============================================================================

_DIST_CUSTOMER_NAME = "ABC Pharmacy Chain Co."
_DIST_CUSTOMER_GROUP = "Pharmacy Chains"
_DIST_SALES_QTY = 200
_DIST_ITEM_RATE = 1500


def _ensure_customer_group():
	if frappe.db.exists("Customer Group", _DIST_CUSTOMER_GROUP):
		return False
	frappe.get_doc(
		{
			"doctype": "Customer Group",
			"customer_group_name": _DIST_CUSTOMER_GROUP,
			"parent_customer_group": "All Customer Groups",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_customer():
	if frappe.db.exists("Customer", {"customer_name": _DIST_CUSTOMER_NAME}):
		return False
	_ensure_customer_group()
	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": _DIST_CUSTOMER_NAME,
			"customer_type": "Company",
			"customer_group": _DIST_CUSTOMER_GROUP,
			"territory": "All Territories",
		}
	).insert(ignore_permissions=True)
	return True


def seed_pharma_distribution_master_data():
	"""DP-513 — master plan §7 DEMO 05's target customer ("doanh nghiệp nhập khẩu, bán buôn
	thuốc") modeled as one wholesale Customer buying the PARA-500-TAB this company already
	manufactures and released (DP-506)."""
	customer_created = _ensure_customer()
	return f"seed_pharma_distribution_master_data: Customer {'created' if customer_created else 'already existed'}."


def _ensure_fefo_setting():
	"""PD01 — FEFO (First-Expired-First-Out) picking is a native ERPNext mechanism
	(Stock Settings.pick_serial_and_batch_based_on = "Expiry"), not custom code."""
	settings = frappe.get_single("Stock Settings")
	if settings.pick_serial_and_batch_based_on == "Expiry":
		return False
	settings.pick_serial_and_batch_based_on = "Expiry"
	settings.save(ignore_permissions=True)
	return True


def _ensure_sales_order():
	existing = frappe.db.exists("Sales Order", {"customer": _DIST_CUSTOMER_NAME, "docstatus": 1})
	if existing:
		return existing, False
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DIST_CUSTOMER_NAME,
			"company": _DEMO_COMPANY_NAME,
			"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
			"items": [
				{
					"item_code": "PARA-500-TAB",
					"qty": _DIST_SALES_QTY,
					"warehouse": _FG_RELEASED_WAREHOUSE,
					"rate": _DIST_ITEM_RATE,
				}
			],
		}
	)
	so.insert(ignore_permissions=True)
	so.submit()
	return so.name, True


def _ensure_delivery_note(so_name):
	if frappe.db.exists("Delivery Note", {"against_sales_order": so_name, "docstatus": 1}):
		return False
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dn = make_delivery_note(so_name)
	dn.insert(ignore_permissions=True)
	dn.submit()
	return True


def seed_distribution_sales_flow():
	"""DP-514 — Sales Order + Delivery Note for the wholesale Customer, sourced from FG
	Released stock, matching master plan §7 DEMO 05's workflow ("sales order → FEFO picking →
	delivery"). Uses ERPNext's own `make_delivery_note()` rather than hand-building the Stock
	Entry equivalent (same reuse pattern as DP-502's `make_purchase_receipt()`)."""
	if not frappe.db.exists("Customer", {"customer_name": _DIST_CUSTOMER_NAME}):
		return "seed_distribution_sales_flow: SKIPPED — Customer does not exist yet, run seed_pharma_distribution_master_data first."
	_ensure_fefo_setting()
	so_name, so_created = _ensure_sales_order()
	dn_created = _ensure_delivery_note(so_name)
	return (
		f"seed_distribution_sales_flow: Sales Order {'created' if so_created else 'already existed'} ({so_name}). "
		f"Delivery Note {'created' if dn_created else 'already existed'}."
	)


def _ensure_synthetic_batch(batch_id, expiry_date, disabled=0):
	if frappe.db.exists("Batch", batch_id):
		return batch_id
	frappe.get_doc(
		{
			"doctype": "Batch",
			"batch_id": batch_id,
			"item": "PARA-500-TAB",
			"expiry_date": expiry_date,
			"disabled": disabled,
		}
	).insert(ignore_permissions=True)
	return batch_id


def _receive_synthetic_batch_into_fg_released(batch_id):
	# NOT `Stock Ledger Entry.batch_no` — v16's Serial and Batch Bundle mechanism leaves that
	# column NULL and puts the real batch link on a linked "Serial and Batch Bundle" doc
	# instead (the same indirection that caused the DP-506 incident). `Batch.batch_qty` is a
	# simple, already-resolved running total that avoids the join entirely.
	if (frappe.db.get_value("Batch", batch_id, "batch_qty") or 0) > 0:
		return False
	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": _DEMO_COMPANY_NAME,
		}
	)
	se.append(
		"items",
		{
			"item_code": "PARA-500-TAB",
			"qty": 1,
			"t_warehouse": _FG_RELEASED_WAREHOUSE,
			"batch_no": batch_id,
			"use_serial_batch_fields": 1,
			"basic_rate": 0,
		},
	)
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _attempt_delivery_of_batch(batch_id):
	"""Returns True if the attempt was blocked (ValidationError), False if it went through."""
	dn = frappe.get_doc(
		{
			"doctype": "Delivery Note",
			"customer": _DIST_CUSTOMER_NAME,
			"company": _DEMO_COMPANY_NAME,
			"items": [
				{
					"item_code": "PARA-500-TAB",
					"qty": 1,
					"warehouse": _FG_RELEASED_WAREHOUSE,
					"batch_no": batch_id,
					"rate": _DIST_ITEM_RATE,
				}
			],
		}
	)
	try:
		dn.insert(ignore_permissions=True)
		dn.submit()
		return False
	except frappe.ValidationError:
		return True


def _test_expired_batch_block():
	"""PD02 negative test. ERPNext's own StockController.validate_serialized_batch() already
	blocks ANY stock transaction (receipt or delivery) referencing a Batch whose expiry_date
	has passed — found by trying to build a custom hook for this and discovering ERPNext beat
	it there (BatchExpiredError fired on the synthetic batch's own Material Receipt, not on
	delivery). No custom validation needed; this test instead proves the real-world scenario:
	a batch that was VALID when it entered stock, then expires while sitting in inventory,
	then someone tries to ship it later. Synthetic batch EXP-TEST-001 is received with a valid
	future expiry (so the receipt itself succeeds), then backdated directly via frappe.db.set_value
	(bypassing insert-time validation, since ordinary time passing is what backdates a real
	batch too) — the delivery attempt must then hit ERPNext's own native block."""
	marker = "EXP-TEST-001"
	if (frappe.db.get_value("Batch", marker, "batch_qty") or 0) > 0:
		return True
	_ensure_synthetic_batch(marker, "2030-01-01")
	_receive_synthetic_batch_into_fg_released(marker)
	frappe.db.set_value("Batch", marker, "expiry_date", "2020-01-01")
	blocked = _attempt_delivery_of_batch(marker)
	if not blocked:
		frappe.throw("PD02 negative test FAILED: expired batch delivery was not blocked!")
	return True


def _test_recalled_batch_block():
	"""PD03 negative test. Synthetic batch RCL-TEST-001, far-future expiry but disabled=1
	("recalled"), 1 unit received straight into FG Released, delivery attempt must be blocked."""
	marker = "RCL-TEST-001"
	if (frappe.db.get_value("Batch", marker, "batch_qty") or 0) > 0:
		return True
	_ensure_synthetic_batch(marker, "2030-01-01", disabled=1)
	_receive_synthetic_batch_into_fg_released(marker)
	blocked = _attempt_delivery_of_batch(marker)
	if not blocked:
		frappe.throw("PD03 negative test FAILED: recalled batch delivery was not blocked!")
	return True


_DIST_CREDIT_LIMIT = 500000  # VND — above the 300,000 existing order plus the PD01 FEFO
# test's normal 45,000 VND order (see seed_distribution_fefo_proof), but still low enough
# that PD04's own deliberately-oversized test order pushes the customer over it. A single
# fixed limit can't satisfy "low enough to block a small test order" and "high enough to
# allow a later normal order" at once (found via testing — an earlier 305,000 value blocked
# the FEFO proof's legitimate order too), so PD04's test order is sized to the limit instead.


def _ensure_credit_limit():
	existing_row = frappe.db.get_value(
		"Customer Credit Limit", {"parent": _DIST_CUSTOMER_NAME, "company": _DEMO_COMPANY_NAME}, ["name", "credit_limit"], as_dict=True
	)
	if existing_row:
		if existing_row.credit_limit == _DIST_CREDIT_LIMIT:
			return False
		frappe.db.set_value("Customer Credit Limit", existing_row.name, "credit_limit", _DIST_CREDIT_LIMIT)
		return True
	customer = frappe.get_doc("Customer", _DIST_CUSTOMER_NAME)
	customer.append("credit_limits", {"company": _DEMO_COMPANY_NAME, "credit_limit": _DIST_CREDIT_LIMIT})
	customer.save(ignore_permissions=True)
	return True


def _test_credit_limit_block():
	"""PD04 negative test. Native ERPNext credit limit check (Sales Order.check_credit_limit(),
	via erpnext.selling.doctype.customer.customer.check_credit_limit) — no custom code needed.
	Deliberately oversized (150 units, 225,000 VND) so that on top of the existing 300,000 VND
	order it clears the 500,000 VND limit, while staying clear of the smaller 45,000 VND order
	the PD01 FEFO proof needs to go through unblocked."""
	if frappe.db.exists("Sales Order", {"po_no": "PD04-CREDIT-TEST", "customer": _DIST_CUSTOMER_NAME}):
		return True
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DIST_CUSTOMER_NAME,
			"company": _DEMO_COMPANY_NAME,
			"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
			"po_no": "PD04-CREDIT-TEST",
			"items": [{"item_code": "PARA-500-TAB", "qty": 150, "warehouse": _FG_RELEASED_WAREHOUSE, "rate": _DIST_ITEM_RATE}],
		}
	)
	blocked = False
	try:
		so.insert(ignore_permissions=True)
		so.submit()
	except frappe.ValidationError:
		blocked = True
		# check_credit_limit() throws from inside submit()'s own flow, by which point
		# Frappe may already have flipped docstatus to 1 in this uncommitted transaction
		# even though the save didn't truly succeed — delete_doc() on an apparently
		# "submitted" record fails ("Submitted Record cannot be deleted"), so branch on
		# actual docstatus rather than assuming a blocked submit always leaves a plain draft.
		if so.name and frappe.db.exists("Sales Order", so.name):
			actual_docstatus = frappe.db.get_value("Sales Order", so.name, "docstatus")
			if actual_docstatus == 1:
				frappe.get_doc("Sales Order", so.name).cancel()
			else:
				frappe.delete_doc("Sales Order", so.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("PD04 negative test FAILED: over-credit-limit order was not blocked!")
	return True


def seed_distribution_validations():
	"""DP-515/DP-516/DP-517 — proves PD02 (expired batch cannot ship, native ERPNext behavior
	— see _test_expired_batch_block), PD03 (recalled batch blocks delivery, custom hook —
	block_recalled_batch_delivery) and PD04 (credit limit, native ERPNext behavior) actually
	fire, using throwaway synthetic data so the real batch/customer transactions aren't
	touched."""
	if not frappe.db.exists("Customer", {"customer_name": _DIST_CUSTOMER_NAME}):
		return "seed_distribution_validations: SKIPPED — Customer does not exist yet, run seed_pharma_distribution_master_data first."
	expired_blocked = _test_expired_batch_block()
	recalled_blocked = _test_recalled_batch_block()
	_ensure_credit_limit()
	credit_blocked = _test_credit_limit_block()
	return (
		f"seed_distribution_validations: PD02 expired-batch-block CONFIRMED ({expired_blocked}). "
		f"PD03 recalled-batch-block CONFIRMED ({recalled_blocked}). "
		f"PD04 credit-limit-block CONFIRMED ({credit_blocked})."
	)


def _ensure_customer_return():
	real_dn = frappe.db.get_value("Delivery Note", {"customer": _DIST_CUSTOMER_NAME, "is_return": 0, "docstatus": 1}, "name")
	if not real_dn:
		return False, None
	if frappe.db.exists("Delivery Note", {"return_against": real_dn, "docstatus": 1}):
		return False, real_dn
	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dn_return = make_return_doc("Delivery Note", real_dn)
	# 20 of the 200 delivered units come back — same batch, restored to FG Released
	dn_return.items[0].qty = -20
	dn_return.insert(ignore_permissions=True)
	dn_return.submit()
	return True, real_dn


def seed_distribution_return():
	"""DP-518 — PD05, "Customer return restores correct batch." Uses ERPNext's native return
	mechanism (make_return_doc — the same one behind the "Create > Return" UI button) rather
	than hand-building a reverse Stock Entry, so the returned batch is guaranteed to match the
	original delivery's batch, not just re-picked via FEFO."""
	if not frappe.db.exists("Delivery Note", {"customer": _DIST_CUSTOMER_NAME, "docstatus": 1}):
		return "seed_distribution_return: SKIPPED — no Delivery Note exists yet, run seed_distribution_sales_flow first."
	return_created, against_dn = _ensure_customer_return()
	return f"seed_distribution_return: Return against {against_dn} {'created' if return_created else 'already existed'}."


# ============================================================================
# PD01 (FEFO) follow-up — DP-520..522. A single real batch can't demonstrate FEFO ordering
# (there's no choice to make), so this produces a genuine second batch through the SAME real
# pipeline (purchase -> QC -> approve -> manufacture -> QC -> release), smaller-scale (qty 50
# vs Golden Demo #1's 1000), with an earlier expiry than the first batch, then proves a new
# delivery picks the earlier-expiring batch even though it's the newer/smaller one.
# ============================================================================

_BATCH2_QTY = 50
_BATCH2_PACKAGING_PO_MARKER = "PD01-BATCH2-PACKAGING"
_BATCH2_EXPIRY = "2027-06-01"  # earlier than Batch 1's ~2028-09-27 — the whole point of this test


def _ensure_batch2_packaging_supply():
	"""Golden Demo #1's manufacturing run (DP-504) fully consumed PVC-ALU/CARTON-PRINTED —
	the only 2 items exhausted, since raw materials were purchased with headroom. A second,
	smaller batch needs a fresh top-up purchase of just those 2, through Quarantine then
	Approved like any other receipt."""
	po_name = frappe.db.get_value("Purchase Order", {"title": _BATCH2_PACKAGING_PO_MARKER}, "name")
	if not po_name:
		po = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": _SUPPLIER_NAME,
				"company": _DEMO_COMPANY_NAME,
				"title": _BATCH2_PACKAGING_PO_MARKER,
				"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
				"items": [
					{
						"item_code": item_code,
						"qty": _BATCH2_QTY,
						"uom": "Nos",
						"warehouse": _RM_QUARANTINE_WAREHOUSE,
						"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
					}
					for item_code in ("PVC-ALU", "CARTON-PRINTED")
				],
			}
		)
		po.insert(ignore_permissions=True)
		po.submit()
		po_name = po.name

	if not frappe.db.exists("Purchase Receipt Item", {"purchase_order": po_name}):
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

		pr = make_purchase_receipt(po_name)
		pr.insert(ignore_permissions=True)
		pr.submit()

	transferred = False
	for item_code in ("PVC-ALU", "CARTON-PRINTED"):
		if frappe.db.get_value("Item", item_code, "item_code") is None:
			continue
		balance = (
			frappe.db.sql(
				"select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0",
				(_RM_APPROVED_WAREHOUSE, item_code),
			)[0][0]
			or 0
		)
		if balance >= _BATCH2_QTY:
			continue
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Transfer",
				"purpose": "Material Transfer",
				"company": _DEMO_COMPANY_NAME,
			}
		)
		se.append(
			"items",
			{
				"item_code": item_code,
				"qty": _BATCH2_QTY,
				"s_warehouse": _RM_QUARANTINE_WAREHOUSE,
				"t_warehouse": _RM_APPROVED_WAREHOUSE,
			},
		)
		se.insert(ignore_permissions=True)
		se.submit()
		transferred = True
	return transferred


def _ensure_batch2_work_order():
	existing = frappe.db.exists("Work Order", {"production_item": "PARA-500-TAB", "docstatus": 1, "qty": _BATCH2_QTY})
	if existing:
		return existing, False
	active_bom = frappe.db.get_value("BOM", {"item": "PARA-500-TAB", "is_active": 1})
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": "PARA-500-TAB",
			"bom_no": active_bom,
			"qty": _BATCH2_QTY,
			"company": _DEMO_COMPANY_NAME,
			"source_warehouse": _RM_APPROVED_WAREHOUSE,
			"fg_warehouse": _FG_QUARANTINE_WAREHOUSE,
			"skip_transfer": 1,
			"planned_start_date": frappe.utils.now_datetime(),
		}
	)
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo.name, True


def _ensure_batch2_manufacture(wo_name):
	if frappe.db.exists("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1}):
		return False
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = make_stock_entry(wo_name, "Manufacture", qty=_BATCH2_QTY)
	se = frappe.get_doc(se) if not isinstance(se, frappe.model.document.Document) else se
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _batch2_batch_name():
	return frappe.db.get_value("Batch", {"item": "PARA-500-TAB", "expiry_date": _BATCH2_EXPIRY}, "name")


def _ensure_batch2_qc_and_release():
	batch2 = _batch2_batch_name()
	if not batch2:
		wo_name = frappe.db.get_value("Work Order", {"production_item": "PARA-500-TAB", "qty": _BATCH2_QTY}, "name")
		se_name = frappe.db.get_value("Stock Entry", {"work_order": wo_name, "purpose": "Manufacture"}, "name")
		batch2 = frappe.db.get_value(
			"Serial and Batch Entry",
			{"parent": frappe.db.get_value("Stock Entry Detail", {"parent": se_name, "item_code": "PARA-500-TAB"}, "serial_and_batch_bundle")},
			"batch_no",
		)
		frappe.db.set_value("Batch", batch2, "expiry_date", _BATCH2_EXPIRY)

	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": batch2, "status": "Accepted", "docstatus": 1}):
		se_name = frappe.db.get_value("Serial and Batch Entry", {"batch_no": batch2}, "parent")
		reference_se = frappe.db.get_value("Stock Entry Detail", {"serial_and_batch_bundle": se_name}, "parent")
		qi = frappe.get_doc(
			{
				"doctype": "Quality Inspection",
				"inspection_type": "In Process",
				"reference_type": "Stock Entry",
				"reference_name": reference_se,
				"item_code": "PARA-500-TAB",
				"batch_no": batch2,
				"sample_size": 5,
				"status": "Accepted",
				"company": _DEMO_COMPANY_NAME,
				"inspected_by": frappe.session.user,
			}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		qc_created = True

	release_created = False
	# not `Stock Ledger Entry.batch_no` (NULL under the Serial and Batch Bundle mechanism —
	# same recurring indirection bug as DP-506/DP-515) — join through the bundle instead.
	already_released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle
		join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(_FG_RELEASED_WAREHOUSE, batch2),
	)
	if not already_released:
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Transfer",
				"purpose": "Material Transfer",
				"company": _DEMO_COMPANY_NAME,
			}
		)
		se.append(
			"items",
			{
				"item_code": "PARA-500-TAB",
				"qty": _BATCH2_QTY,
				"s_warehouse": _FG_QUARANTINE_WAREHOUSE,
				"t_warehouse": _FG_RELEASED_WAREHOUSE,
				"batch_no": batch2,
				"use_serial_batch_fields": 1,
			},
		)
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True

	return batch2, qc_created, release_created


def seed_manufacturing_batch_2():
	"""DP-520/521 — a second, smaller (qty 50) real batch of PARA-500-TAB through the full
	pipeline (top-up packaging purchase -> approve -> manufacture -> in-process QC -> QA
	release), with its expiry deliberately backdated to 2027-06-01 (earlier than Batch 1's
	~2028-09-27) — the only way to give PD01 (FEFO) an actual choice to make between batches."""
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _FG_RELEASED_WAREHOUSE, "item_code": "PARA-500-TAB", "is_cancelled": 0}):
		return "seed_manufacturing_batch_2: SKIPPED — Golden Demo #1's Batch 1 must exist first."
	# packaging supply only runs before the qty-50 Work Order exists — once manufacturing
	# consumes it, RM Approved correctly drops back toward 0, which is NOT "still needs
	# topping up" (found via a real idempotency bug: re-running attempted a second transfer
	# from an already-empty RM Quarantine and failed on insufficient stock).
	if not frappe.db.exists("Work Order", {"production_item": "PARA-500-TAB", "docstatus": 1, "qty": _BATCH2_QTY}):
		_ensure_batch2_packaging_supply()
	wo_name, wo_created = _ensure_batch2_work_order()
	manufacture_created = _ensure_batch2_manufacture(wo_name)
	batch2, qc_created, release_created = _ensure_batch2_qc_and_release()
	return (
		f"seed_manufacturing_batch_2: Work Order {'created' if wo_created else 'already existed'} ({wo_name}). "
		f"Manufacture {'created' if manufacture_created else 'already existed'}. Batch {batch2}, expiry {_BATCH2_EXPIRY}. "
		f"QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'}."
	)


def _test_fefo_picks_earlier_expiry():
	"""PD01 — with 2 batches now in FG Released (Batch 1 ~2028-09-27, Batch 2 2027-06-01), a
	new Sales Order + Delivery Note for a quantity Batch 2 alone can cover must be
	auto-picked from Batch 2, proving FEFO actually chose the earlier-expiring batch over the
	larger/older Batch 1 — not just "whichever batch happened to be received first"."""
	batch2 = _batch2_batch_name()
	if not batch2:
		frappe.throw("_test_fefo_picks_earlier_expiry: Batch 2 not found — run seed_manufacturing_batch_2 first.")
	marker = "PD01-FEFO-TEST"
	if frappe.db.exists("Sales Order", {"po_no": marker}):
		return True

	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DIST_CUSTOMER_NAME,
			"company": _DEMO_COMPANY_NAME,
			"po_no": marker,
			"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
			"items": [
				{
					"item_code": "PARA-500-TAB",
					"qty": 30,
					"warehouse": _FG_RELEASED_WAREHOUSE,
					"rate": _DIST_ITEM_RATE,
				}
			],
		}
	)
	so.insert(ignore_permissions=True)
	so.submit()

	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dn = make_delivery_note(so.name)
	dn.insert(ignore_permissions=True)
	dn.submit()

	bundle_name = frappe.db.get_value("Stock Entry Detail", {"parent": dn.name}, "serial_and_batch_bundle") or frappe.db.get_value(
		"Delivery Note Item", {"parent": dn.name}, "batch_no"
	)
	picked_batch = bundle_name
	if not picked_batch:
		picked_batch = frappe.db.get_value(
			"Serial and Batch Entry",
			{"parent": frappe.db.get_value("Delivery Note Item", {"parent": dn.name}, "serial_and_batch_bundle")},
			"batch_no",
		)
	if picked_batch != batch2:
		frappe.throw(
			f"PD01 FEFO test FAILED: expected delivery to pick Batch 2 ({batch2}, expiry {_BATCH2_EXPIRY}) "
			f"but it picked {picked_batch!r} instead."
		)
	return True


def seed_distribution_fefo_proof():
	"""DP-522 — proves PD01 with a genuine 2-batch choice (see seed_manufacturing_batch_2)."""
	if not _batch2_batch_name():
		return "seed_distribution_fefo_proof: SKIPPED — Batch 2 does not exist yet, run seed_manufacturing_batch_2 first."
	fefo_confirmed = _test_fefo_picks_earlier_expiry()
	return f"seed_distribution_fefo_proof: PD01 FEFO-picks-earlier-expiry CONFIRMED ({fefo_confirmed})."
