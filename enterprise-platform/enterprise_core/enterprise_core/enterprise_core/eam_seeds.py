"""Golden Demo #6 — EAM/CMMS/Calibration/Validation standalone (master plan DEMO 13),
IP-EAM. Reuses the DP-509 Asset ("Tablet Compression Machine #1") rather than creating a
second demo equipment record — one asset carries its full lifecycle (maintenance, repair,
calibration, qualification) across this whole platform, not siloed per golden demo.
"""

import frappe

_ASSET_NAME = "Tablet Compression Machine #1"
_SPARE_PART_CODE = "SPARE-BELT-01"
_SPARE_WAREHOUSE = "Stores - DPC"


def _asset_docname():
	return frappe.db.get_value("Asset", {"asset_name": _ASSET_NAME}, "name")


def _ensure_calibration(result="Pass", due_in_days=180):
	asset = _asset_docname()
	if not asset:
		return None, False
	marker_due = frappe.utils.add_days(frappe.utils.nowdate(), due_in_days)
	existing = frappe.db.get_value("EAM Calibration Record", {"asset": asset, "due_date": marker_due}, "name")
	if existing:
		return existing, False
	cal = frappe.get_doc(
		{
			"doctype": "EAM Calibration Record",
			"asset": asset,
			"calibration_date": frappe.utils.nowdate(),
			"due_date": marker_due,
			"performed_by": "External Calibration Services Co.",
			"result": result,
			"certificate_no": f"CAL-{frappe.utils.nowdate()}",
		}
	)
	cal.insert(ignore_permissions=True)
	return cal.name, True


def seed_eam_calibration():
	"""DP-543 — E02, calibration tracking baseline. A Pass calibration due 180 days out."""
	asset = _asset_docname()
	if not asset:
		return "seed_eam_calibration: SKIPPED — Asset 'Tablet Compression Machine #1' not found, run Golden Demo #1's seed_eam_flow first."
	cal_name, created = _ensure_calibration()
	return f"seed_eam_calibration: Calibration record {'created' if created else 'already existed'} ({cal_name})."


def _ensure_qualification():
	asset = _asset_docname()
	marker = "OQ"
	existing = frappe.db.get_value("EAM Qualification", {"asset": asset, "qualification_type": marker, "status": "Qualified"}, "name")
	if existing:
		return existing, False
	q = frappe.get_doc(
		{
			"doctype": "EAM Qualification",
			"asset": asset,
			"qualification_type": marker,
			"performed_date": frappe.utils.nowdate(),
			"performed_by": "maintenance@pharmacountry.vn",
			"result": "Pass",
			"status": "Draft",
		}
	)
	q.insert(ignore_permissions=True)
	q.status = "Qualified"
	q.save(ignore_permissions=True)
	return q.name, True


def seed_eam_qualification():
	"""DP-544 — E05/E06 happy path: Operational Qualification succeeds because a valid
	(non-overdue) calibration exists."""
	if not frappe.db.exists("EAM Calibration Record", {"asset": _asset_docname(), "result": "Pass"}):
		return "seed_eam_qualification: SKIPPED — run seed_eam_calibration first."
	q_name, created = _ensure_qualification()
	return f"seed_eam_qualification: OQ {'reached Qualified' if created else 'already existed'} ({q_name})."


def _ensure_spare_part_item():
	if frappe.db.exists("Item", _SPARE_PART_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": _SPARE_PART_CODE,
			"item_name": "Compression Machine Drive Belt",
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_spare_part_stock():
	balance = (
		frappe.db.sql(
			"select sum(actual_qty) from `tabStock Ledger Entry` where warehouse=%s and item_code=%s and is_cancelled=0",
			(_SPARE_WAREHOUSE, _SPARE_PART_CODE),
		)[0][0]
		or 0
	)
	if balance > 0:
		return False
	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": "Demo Pharma Co",
		}
	)
	se.append("items", {"item_code": _SPARE_PART_CODE, "qty": 5, "t_warehouse": _SPARE_WAREHOUSE, "basic_rate": 250000})
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _ensure_breakdown_repair():
	asset = _asset_docname()
	marker = "Drive belt failure during production run"
	existing = frappe.db.get_value("Asset Repair", {"asset": asset, "description": marker}, "name")
	if existing:
		return existing, False
	repair = frappe.get_doc(
		{
			"doctype": "Asset Repair",
			"asset": asset,
			"failure_date": frappe.utils.now_datetime(),
			"description": marker,
			"actions_performed": "Replaced worn drive belt; verified machine cycles correctly at rated speed.",
			"repair_status": "Pending",
			"company": "Demo Pharma Co",
			"stock_items": [
				{"item_code": _SPARE_PART_CODE, "warehouse": _SPARE_WAREHOUSE, "consumed_quantity": 1, "valuation_rate": 250000},
			],
		}
	)
	repair.insert(ignore_permissions=True)
	repair.completion_date = frappe.utils.now_datetime()
	repair.repair_status = "Completed"
	repair.save(ignore_permissions=True)
	return repair.name, True


def seed_eam_breakdown_repair():
	"""DP-545 — E03 (breakdown creates work order) and E04 (spare part issue), both native
	ERPNext Asset Repair — no custom code needed for either. Asset Repair *is* the work order
	here; its `stock_items` child table *is* the spare-part consumption record."""
	asset = _asset_docname()
	if not asset:
		return "seed_eam_breakdown_repair: SKIPPED — Asset not found."
	item_created = _ensure_spare_part_item()
	stock_created = _ensure_spare_part_stock()
	repair_name, repair_created = _ensure_breakdown_repair()
	return (
		f"seed_eam_breakdown_repair: Spare part item {'created' if item_created else 'already existed'}. "
		f"Stock {'received' if stock_created else 'already present'}. "
		f"Asset Repair {'completed' if repair_created else 'already existed'} ({repair_name})."
	)


def _test_e06_overdue_calibration_blocks_qualification():
	"""E06 negative test: an overdue calibration must block a *new* qualification attempt.
	Uses a synthetic due date in the past on a fresh EAM Qualification (PQ, distinct from the
	OQ happy path) so it doesn't collide with the already-Qualified OQ record."""
	asset = _asset_docname()
	overdue_cal_name, _created = _ensure_calibration(result="Pass", due_in_days=-30)
	marker = "PQ"
	if frappe.db.exists("EAM Qualification", {"asset": asset, "qualification_type": marker}):
		return True
	q = frappe.get_doc(
		{
			"doctype": "EAM Qualification",
			"asset": asset,
			"qualification_type": marker,
			"performed_date": frappe.utils.nowdate(),
			"performed_by": "maintenance@pharmacountry.vn",
			"result": "Pass",
			"status": "Draft",
		}
	)
	q.insert(ignore_permissions=True)
	q.status = "Qualified"
	blocked = False
	try:
		q.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("E06 negative test FAILED: qualifying an asset with overdue calibration was not blocked!")
	return True


def seed_eam_validations():
	"""DP-546 — E06 negative test. Note: this deliberately makes the asset's *latest*
	calibration record overdue (due_in_days=-30), which also means seed_eam_calibration's
	original Pass-180-days record is no longer the latest — realistic (calibration due dates
	only move forward in reality), and doesn't retroactively break DP-544's already-Qualified
	OQ record (past qualifications aren't re-validated retroactively, only new ones)."""
	if not _asset_docname():
		return "seed_eam_validations: SKIPPED — Asset not found."
	e06 = _test_e06_overdue_calibration_blocks_qualification()
	return f"seed_eam_validations: E06 CONFIRMED ({e06})."
