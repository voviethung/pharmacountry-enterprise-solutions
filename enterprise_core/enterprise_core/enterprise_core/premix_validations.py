"""Golden Demo #26 (Premix / Feed Additive Manufacturing, master plan DEMO 19) business rules —
PM01/PM02/PM03/PM04. Every hook here is additively scoped (only fires when a Premix-specific
Custom Field is actually populated/truthy), so none of them changes behavior for the 25 prior
golden demos' own Stock Entries/BOMs — confirmed by the full regression sweep this demo's own
DP entry records.
"""

import frappe
from frappe import _

_MICRO_TOLERANCE_PERCENT = 1.0  # tighter than Golden Demo #7's blanket 3% (F03) — micro-dosed
# vitamin/mineral ingredients need much tighter precision than bulk feed ingredients. Both hooks
# run on every Manufacture Stock Entry; this one is the binding constraint for micro items,
# F03's 3% stays the binding constraint for everything else (carrier, mineral mix).


def block_micro_weigh_tolerance_exceeded(doc, method):
	"""PM01 — micro-weigh tolerance. A micro-dosed ingredient (Item.is_micro_ingredient=1)
	consumed outside ±_MICRO_TOLERANCE_PERCENT of what the BOM (scaled to the Work Order qty)
	declares is blocked."""
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
		if not frappe.db.get_value("Item", row.item_code, "is_micro_ingredient"):
			continue
		expected_qty = expected[row.item_code]
		if not expected_qty:
			continue
		deviation_percent = abs(row.qty - expected_qty) / expected_qty * 100
		if deviation_percent > _MICRO_TOLERANCE_PERCENT:
			frappe.throw(
				_(
					"PM01: micro-weigh tolerance exceeded for {0}: weighed {1}, expected {2} (±{3}%), deviation {4:.1f}%."
				).format(row.item_code, row.qty, round(expected_qty, 4), _MICRO_TOLERANCE_PERCENT, deviation_percent),
				title=_("PM01: Micro-Weigh Tolerance Exceeded"),
			)


def block_manufacture_without_second_check(doc, method):
	"""PM02 — critical ingredient double-check (four-eyes control). Any ingredient flagged
	Item.requires_second_check=1 consumed by a Manufacture Stock Entry needs a Verified
	`Premix Weighing Verification` record for this exact Work Order + item, with a real second
	person (`verified_by` different from `weighed_by`) — not just a boolean sign-off."""
	if doc.purpose != "Manufacture" or not doc.work_order:
		return
	for row in doc.items:
		if not row.s_warehouse:
			continue
		if not frappe.db.get_value("Item", row.item_code, "requires_second_check"):
			continue
		verification = frappe.db.get_value(
			"Premix Weighing Verification",
			{"work_order": doc.work_order, "item_code": row.item_code},
			["status", "weighed_by", "verified_by"],
			as_dict=True,
			order_by="creation desc",
		)
		if not verification or verification.status != "Verified":
			frappe.throw(
				_(
					"PM02: critical ingredient {0} requires a second-person weighing verification before it can be "
					"consumed by Work Order {1} — no Verified Premix Weighing Verification record found."
				).format(row.item_code, doc.work_order),
				title=_("PM02: Critical Ingredient Double-Check Required"),
			)
		if not verification.verified_by or verification.verified_by == verification.weighed_by:
			frappe.throw(
				_(
					"PM02: the weighing verification for critical ingredient {0} must be signed off by a DIFFERENT "
					"person than whoever weighed it (four-eyes control) — weighed_by and verified_by are the same/missing."
				).format(row.item_code),
				title=_("PM02: Four-Eyes Control Violation"),
			)


def block_sequence_violation(doc, method):
	"""PM03 — sequence rule. Ingredients must be consumed by a Manufacture Stock Entry in the
	order the Formula (BOM Item.sequence_no) declares — e.g. carrier first, minerals next,
	vitamins last. Only fires when the BOM actually declares a sequence (sequence_no populated
	on at least one row) — a BOM with no sequence data (every other golden demo's BOM) is left
	completely alone."""
	if doc.purpose != "Manufacture" or not doc.work_order:
		return
	bom_no = frappe.db.get_value("Work Order", doc.work_order, "bom_no")
	if not bom_no:
		return
	seq_map = {r.item_code: r.sequence_no for r in frappe.get_all("BOM Item", filters={"parent": bom_no}, fields=["item_code", "sequence_no"])}
	if not any(seq_map.values()):
		return

	consumption_rows = sorted((row for row in doc.items if row.s_warehouse and seq_map.get(row.item_code)), key=lambda r: r.idx)
	last_seq = 0
	last_item = None
	for row in consumption_rows:
		seq = seq_map[row.item_code]
		if seq < last_seq:
			frappe.throw(
				_(
					"PM03: ingredient {0} (mixing sequence {1}) was added after {2} (sequence {3}) — out of order. "
					"Ingredients must be added to the mixer in ascending sequence order."
				).format(row.item_code, seq, last_item, last_seq),
				title=_("PM03: Sequence Violation"),
			)
		last_seq = seq
		last_item = row.item_code


def block_bom_default_without_approval(doc, method):
	"""PM04 — formula revision. A BOM can only become the active default Formula through an
	Approved status — same shape as Medical Device's MD02 (BOM.design_change_record gate) but
	a plain Select on the BOM itself rather than a Link to a separate approval-record DocType.
	Only fires when `premix_approval_status` is actually set — every other golden demo's BOM
	leaves this field empty and is untouched."""
	if not doc.is_default or not doc.get("premix_approval_status"):
		return
	if doc.premix_approval_status != "Approved":
		frappe.throw(
			_("PM04: BOM {0} cannot become the default Formula — premix_approval_status is '{1}', must be 'Approved'.").format(doc.name, doc.premix_approval_status),
			title=_("PM04: Formula Not Approved"),
		)
