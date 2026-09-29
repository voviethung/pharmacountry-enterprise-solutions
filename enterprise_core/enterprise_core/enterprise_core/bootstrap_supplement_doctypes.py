"""Golden Demo #20 (Supplement / Nutraceutical Manufacturing, master plan DEMO 02, "PHASE 6"
item 1) — needs ZERO new DocTypes, the leanest bootstrap of any golden demo alongside Aqua
Environment's (Golden Demo #16). Every S0x test is satisfied by pure reuse: S01 (formula
revision) is the same BOM `is_default`-flip pattern as Vet Mfg/Aqua Env; S02 (allergen flag) is
the `contains_allergen` Custom Field Feed Manufacturing already added to Item; S03 (artwork
version) reuses Golden Demo #4's whole DMS Document/DMS Document Version lifecycle with
`doc_type="Artwork"` — the only genuinely new piece, one more option alongside "Label"; S04
(batch expiry) is native `Item.shelf_life_in_days`-driven `Batch.expiry_date`; S05 (COA from
approved results) reuses Golden Demo #5's full LIMS Sample -> Test -> Approved -> `LIMS COA`
chain unmodified; S06 (traceability) reuses `trace_feed_batch_genealogy()` and
`trace_batch_to_customers()` unmodified.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_supplement_doctypes.run
"""

import frappe


def run():
	doc_type_field = frappe.db.get_value("DocField", {"parent": "DMS Document", "fieldname": "doc_type"}, "options")
	if doc_type_field and "Artwork" not in doc_type_field.split("\n"):
		frappe.db.set_value("DocField", {"parent": "DMS Document", "fieldname": "doc_type"}, "options", doc_type_field + "\nArtwork")
		frappe.clear_cache(doctype="DMS Document")
		print("Added 'Artwork' option to DMS Document.doc_type.")
	else:
		print("DMS Document.doc_type already has 'Artwork' option, skipping.")
