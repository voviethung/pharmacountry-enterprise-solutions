"""Golden Demo #7 (Compound Feed Manufacturing, master plan DEMO 18) business rules —
F03/F07. Registered on Stock Entry.validate ALONGSIDE Golden Demo #1's pharma hooks
(validations.py) — this fires for ANY company's Manufacture Stock Entry with a Work Order
(generically useful, not feed-specific in principle), so the full pharma registry chain was
re-run after adding this to confirm no regression (see project_status.md DP-548).
"""

import frappe
from frappe import _

_WEIGHING_TOLERANCE_PERCENT = 3.0


def block_weighing_tolerance_exceeded(doc, method):
	"""F03 — weighing tolerance. Actual consumption per raw material must stay within
	±_WEIGHING_TOLERANCE_PERCENT of what the BOM (scaled to the Work Order qty) declares."""
	if doc.purpose != "Manufacture" or not doc.work_order:
		return
	bom_no, wo_qty = frappe.db.get_value("Work Order", doc.work_order, ["bom_no", "qty"])
	if not bom_no:
		return
	bom = frappe.get_doc("BOM", bom_no)
	expected = {row.item_code: row.qty * (wo_qty / bom.quantity) for row in bom.items}
	for row in doc.items:
		if not row.s_warehouse or row.item_code not in expected:
			continue
		expected_qty = expected[row.item_code]
		if expected_qty == 0:
			continue
		deviation_percent = abs(row.qty - expected_qty) / expected_qty * 100
		if deviation_percent > _WEIGHING_TOLERANCE_PERCENT:
			frappe.throw(
				_(
					"Weighing tolerance exceeded for {0}: consumed {1}, expected {2} (±{3}%), deviation {4:.1f}%."
				).format(row.item_code, row.qty, round(expected_qty, 3), _WEIGHING_TOLERANCE_PERCENT, deviation_percent),
				title=_("F03: Weighing Tolerance Exceeded"),
			)


def block_line_not_cleaned_after_allergen(doc, method):
	"""F07 — cross-contamination/sequencing flag. A Work Order for a non-allergen Formula
	can't start on a line (fg_warehouse) whose most recent prior Work Order used an
	allergen-containing Formula, unless a Feed Line Cleaning Log exists after that prior run."""
	if doc.doctype != "Work Order" or not doc.bom_no:
		return
	current_has_allergen = frappe.db.get_value("Item", doc.production_item, "contains_allergen")
	if current_has_allergen:
		return  # only non-allergen runs need to check what came before

	prior = frappe.db.sql(
		"""
		select wo.name, wo.creation, i.contains_allergen
		from `tabWork Order` wo
		join `tabItem` i on i.name = wo.production_item
		where wo.fg_warehouse = %(warehouse)s and wo.docstatus = 1 and wo.name != %(name)s
		order by wo.creation desc limit 1
		""",
		{"warehouse": doc.fg_warehouse, "name": doc.name or ""},
		as_dict=True,
	)
	if not prior or not prior[0].contains_allergen:
		return

	cleaned = frappe.db.exists("Feed Line Cleaning Log", {"warehouse": doc.fg_warehouse, "cleaned_date": [">", prior[0].creation]})
	if not cleaned:
		frappe.throw(
			_(
				"Cannot start Work Order for {0} on line {1} — the previous run ({2}) used an allergen-containing "
				"formula and no Line Cleaning Log has been recorded since. Cross-contamination risk."
			).format(doc.production_item, doc.fg_warehouse, prior[0].name),
			title=_("F07: Line Not Cleaned After Allergen Run"),
		)
