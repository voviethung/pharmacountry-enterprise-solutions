"""Golden Demo #24 (Pharma 3PL / GSP / Cold Chain, master plan DEMO 08, "PHASE 6" item 5) —
two hook functions, same warehouse-name-substring / computed-flag idioms already established by
validations.py and meddev_validations.py:

- `threepl_temperature_reading_validate` (W02): computes `is_excursion`/`status` on a `3PL
  Temperature Reading` from the reading's own Warehouse's configured `min_temp_c`/`max_temp_c`
  range. The reading document itself, once flagged, IS the excursion event — no second doctype.
- `block_quarantine_delivery` (W04): blocks a Delivery Note item sourced from any warehouse
  whose name contains "quarantine". `block_quarantine_issue_to_production` (validations.py)
  already gates Quarantine issue for MANUFACTURING purposes on Stock Entry, but a 3PL outbound
  shipment to a client's own customer goes out via Delivery Note directly, a document type that
  hook never touches — hence this new, narrowly-scoped sibling rather than widening the existing
  one's purpose set (which would risk changing behavior for the 7 other golden demos already
  relying on it).
"""

import frappe
from frappe import _


def threepl_temperature_reading_validate(doc, method):
	min_c, max_c = frappe.db.get_value("Warehouse", doc.warehouse, ["min_temp_c", "max_temp_c"]) or (None, None)
	if min_c is None and max_c is None:
		doc.is_excursion = 0
		doc.status = "Normal"
		return
	out_of_range = (min_c is not None and doc.temperature_c < min_c) or (max_c is not None and doc.temperature_c > max_c)
	doc.is_excursion = 1 if out_of_range else 0
	doc.status = "Excursion" if out_of_range else "Normal"


def block_quarantine_delivery(doc, method):
	"""W04 — master plan DEMO 08 test W04, "goods in quarantine cannot be picked/delivered until
	released." Same warehouse-name-substring gate idiom as block_fg_release_without_qa /
	meddev_block_rejected_material_use, applied to Delivery Note (not Stock Entry) since 3PL
	outbound shipments leave via Delivery Note directly."""
	for row in doc.items:
		if row.warehouse and "quarantine" in row.warehouse.lower():
			frappe.throw(
				_(
					"Cannot deliver item {0} from Quarantine warehouse {1} — goods must be QC-released "
					"before picking/delivery."
				).format(row.item_code, row.warehouse),
				title=_("W04: Quarantine Hold"),
			)
