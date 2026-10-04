"""Golden Demo #9 — Veterinary Pharmaceutical Manufacturing (master plan DEMO 14), IP-VETERINARY.
Reuses Golden Demo #1's exact manufacturing/QC/release pattern for a new Company — including
`block_fg_release_without_qa` (VPM04) completely unmodified.
"""

import frappe

_COMPANY_NAME = "Demo Vet Pharma Co."
_COMPANY_ABBR = "DVP"
_RM_QUARANTINE = f"RM Quarantine - {_COMPANY_ABBR}"
_RM_APPROVED = f"RM Approved - {_COMPANY_ABBR}"
_FG_QUARANTINE = f"FG Quarantine - {_COMPANY_ABBR}"
_FG_RELEASED = f"FG Released - {_COMPANY_ABBR}"
_FG_ITEM = "OXYTET-200-INJ"
_BATCH_QTY = 500  # liters


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(
		ignore_permissions=True
	)
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(
				ignore_permissions=True
			)


def _ensure_warehouses():
	for wh in (_RM_QUARANTINE, _RM_APPROVED, _FG_QUARANTINE, _FG_RELEASED):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


_RAW_MATERIALS = [("OXYTET-API", "Oxytetracycline HCl API", "Kg"), ("WFI", "Water for Injection", "Litre"), ("PVP-EXCIP", "PVP Excipient", "Kg")]


def _ensure_items():
	for item_code, item_name, uom in _RAW_MATERIALS:
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
				"has_batch_no": 1,
				"has_expiry_date": 1,
				"create_new_batch": 1,
				"shelf_life_in_days": 730,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Item", _FG_ITEM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": _FG_ITEM,
				"item_name": "Oxytetracycline 200mg/mL Injectable Solution",
				"item_group": "Finished Goods",
				"stock_uom": "Litre",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"has_expiry_date": 1,
				"create_new_batch": 1,
				"shelf_life_in_days": 730,
				"target_species": "Cattle, Swine, Poultry",
				"indication": "Bacterial infections — respiratory disease, foot rot, bacterial enteritis.",
				"withdrawal_period_days": 28,
			}
		).insert(ignore_permissions=True)


_FORMULA_V1 = [("OXYTET-API", 100.0), ("WFI", 380.0), ("PVP-EXCIP", 20.0)]  # sums to 500L


def _ensure_bom():
	if frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		return False
	bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Litre", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for item_code, qty in _FORMULA_V1:
		bom.append("items", {"item_code": item_code, "qty": qty})
	bom.insert(ignore_permissions=True)
	bom.submit()
	return True


def seed_vet_mfg_master_data():
	"""DP-560 — Company/Items/Formula. VPM01 (species/indication master) is proven by the
	FG Item's own target_species/indication/withdrawal_period_days fields, not a separate
	master table — verified directly in api.verify_vet_mfg_golden_demo()."""
	company_created = _ensure_company()
	_ensure_item_groups()
	_ensure_warehouses()
	_ensure_items()
	bom_created = _ensure_bom()
	return f"seed_vet_mfg_master_data: Company {'created' if company_created else 'already existed'}. Formula {'created' if bom_created else 'already existed'}."


def _ensure_rm_stock_and_approval():
	transferred = False
	for item_code, qty in [("OXYTET-API", 150), ("WFI", 500), ("PVP-EXCIP", 30)]:
		approved_balance = (
			frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0", (_RM_APPROVED, item_code))[0][0]
			or 0
		)
		if approved_balance >= qty:
			continue
		receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		receipt.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _RM_QUARANTINE, "use_serial_batch_fields": 1, "basic_rate": 50000})
		receipt.insert(ignore_permissions=True)
		receipt.submit()
		receipt.reload()
		bundle = frappe.db.get_value("Stock Entry Detail", {"parent": receipt.name, "item_code": item_code}, "serial_and_batch_bundle")
		batch_no = frappe.db.get_value("Serial and Batch Entry", {"parent": bundle}, "batch_no") if bundle else None

		transfer = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		row = {"item_code": item_code, "qty": qty, "s_warehouse": _RM_QUARANTINE, "t_warehouse": _RM_APPROVED}
		if batch_no:
			row["batch_no"] = batch_no
			row["use_serial_batch_fields"] = 1
		transfer.append("items", row)
		transfer.insert(ignore_permissions=True)
		transfer.submit()
		transferred = True
	return transferred


def _ensure_work_order():
	existing = frappe.db.exists("Work Order", {"production_item": _FG_ITEM, "docstatus": 1})
	if existing:
		return existing, False
	bom_no = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1})
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": _FG_ITEM,
			"bom_no": bom_no,
			"qty": _BATCH_QTY,
			"company": _COMPANY_NAME,
			"source_warehouse": _RM_APPROVED,
			"fg_warehouse": _FG_QUARANTINE,
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


def _ensure_qc_and_release():
	batch = frappe.db.get_value("Batch", {"item": _FG_ITEM, "batch_qty": [">", 0]}, "name")
	if not batch:
		return None, False, False
	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}):
		se_name = frappe.db.get_value("Stock Entry", {"purpose": "Manufacture", "work_order": frappe.db.get_value("Work Order", {"production_item": _FG_ITEM}, "name")}, "name")
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

	already_released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent=sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(_FG_RELEASED, batch),
	)
	release_created = False
	if not already_released:
		# VPM04 — reuses block_fg_release_without_qa (Golden Demo #1) COMPLETELY unmodified.
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": _FG_ITEM, "qty": _BATCH_QTY, "s_warehouse": _FG_QUARANTINE, "t_warehouse": _FG_RELEASED, "batch_no": batch, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True
	return batch, qc_created, release_created


def seed_vet_mfg_production():
	"""DP-561 — VPM03 (batch/expiry, native has_batch_no+shelf_life) + VPM04 (QC release,
	reused hook)."""
	if not frappe.db.exists("BOM", {"item": _FG_ITEM, "is_active": 1}):
		return "seed_vet_mfg_production: SKIPPED — run seed_vet_mfg_master_data first."
	rm_transferred = _ensure_rm_stock_and_approval()
	wo_name, wo_created = _ensure_work_order()
	manufacture_created = _ensure_manufacture(wo_name)
	batch, qc_created, release_created = _ensure_qc_and_release()
	return (
		f"seed_vet_mfg_production: RM {'transferred' if rm_transferred else 'already approved'}. "
		f"Work Order {'created' if wo_created else 'already existed'} ({wo_name}). "
		f"Manufacture {'created' if manufacture_created else 'already existed'}. Batch {batch}. "
		f"QC {'created' if qc_created else 'already existed'}. Release {'created' if release_created else 'already existed'}."
	)


def seed_vet_mfg_formula_revision():
	"""DP-562 — VPM02, formula revision. Unlike Golden Demo #1's DP-504/Feed's F01 revisions
	(which cancelled the old BOM outright), here the earlier batch is a legitimate historical
	production run, not a bug being corrected — cancelling its BOM is rightly blocked by
	ERPNext ("linked with Work Order"). The correct move is to leave the old BOM Active (a
	valid historical record) and just flip is_default so future Work Orders pick the new one."""
	old_bom = frappe.db.get_value("BOM", {"item": _FG_ITEM}, order_by="creation asc")
	if not old_bom:
		return "seed_vet_mfg_formula_revision: SKIPPED — run seed_vet_mfg_master_data first."
	if frappe.db.count("BOM", {"item": _FG_ITEM}) >= 2:
		return "seed_vet_mfg_formula_revision: already revised (2+ BOM versions exist)."
	if frappe.db.get_value("BOM", old_bom, "is_default"):
		frappe.db.set_value("BOM", old_bom, "is_default", 0)
	new_bom = frappe.get_doc({"doctype": "BOM", "item": _FG_ITEM, "quantity": _BATCH_QTY, "uom": "Litre", "company": _COMPANY_NAME, "is_active": 1, "is_default": 1})
	for item_code, qty in [("OXYTET-API", 100.0), ("WFI", 370.0), ("PVP-EXCIP", 30.0)]:  # excipient ratio revised
		new_bom.append("items", {"item_code": item_code, "qty": qty})
	new_bom.insert(ignore_permissions=True)
	new_bom.submit()
	return f"seed_vet_mfg_formula_revision: VPM02 CONFIRMED — {old_bom} kept Active (valid history) but no longer default, new version {new_bom.name} is now default."


def seed_vet_mfg_recall():
	"""DP-563 — VPM06, recall. Reuses Golden Demo #3's QMS Recall doctype as-is."""
	batch = frappe.db.get_value("Batch", {"item": _FG_ITEM, "batch_qty": [">", 0]}, "name")
	if not batch:
		return "seed_vet_mfg_recall: SKIPPED — run seed_vet_mfg_production first."
	marker = f"Illustrative recall — {_FG_ITEM} batch {batch} (demo)"
	if frappe.db.exists("QMS Recall", {"subject": marker}):
		return "seed_vet_mfg_recall: already existed."
	frappe.get_doc(
		{
			"doctype": "QMS Recall",
			"subject": marker,
			"batch_reference": batch,
			"reason": "Illustrative recall record for the Vet Manufacturing demo — not a real product issue.",
			"status": "Completed",
			"customers_notified": 1,
		}
	).insert(ignore_permissions=True)
	return f"seed_vet_mfg_recall: VPM06 CONFIRMED — QMS Recall created for batch {batch}."


def _ensure_label_document():
	marker = f"LABEL-{_FG_ITEM}"
	if frappe.db.exists("DMS Document", marker):
		return False
	frappe.get_doc({"doctype": "DMS Document", "document_code": marker, "title": f"Product Label — {_FG_ITEM}", "doc_type": "Label", "status": "Draft", "requires_training": 0}).insert(
		ignore_permissions=True
	)
	v1 = frappe.get_doc(
		{"doctype": "DMS Document Version", "document": marker, "version_no": 1, "status": "Draft", "content_summary": "Withdrawal period: 28 days. Species: Cattle, Swine, Poultry."}
	)
	v1.insert(ignore_permissions=True)
	v1.status = "Approved"
	v1.approved_by = "quality.director@pharmacountry.vn"
	v1.save(ignore_permissions=True)
	v1.status = "Effective"
	v1.effective_date = frappe.utils.nowdate()
	v1.save(ignore_permissions=True)
	return True


def seed_vet_mfg_label():
	"""DP-564 — VPM07, label version. Reuses Golden Demo #4's whole DMS Document/Version
	lifecycle (D01/D02/D04/D06 already enforced there) instead of a parallel concept."""
	if not frappe.db.exists("Item", _FG_ITEM):
		return "seed_vet_mfg_label: SKIPPED — run seed_vet_mfg_master_data first."
	created = _ensure_label_document()
	return f"seed_vet_mfg_label: label document {'created and reached Effective' if created else 'already existed'}."
