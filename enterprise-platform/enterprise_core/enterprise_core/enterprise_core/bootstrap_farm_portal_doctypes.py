"""WEB-07 — Farm Customer / Technical Service Portal (Phase 7, master plan §8 line ~2575-2576).

Reuses Golden Demo #10 (Veterinary Distribution)'s own real `Vet Technical Visit` DocType
(created by `bootstrap_vet_dist_doctypes.py` for VD07 "Technical visit linked customer") almost
verbatim — deliberately NOT a new "Farm Visit"-style DocType. That DocType is already exactly the
real business record this portal needs ("a field rep's technical visit to a customer"); the ONLY
gap is that it has no structured way to record a *product recommendation* made during a visit
(today `products_discussed`/`notes` are free text). Two small, additive schema changes close that
gap without touching the DocType's own JSON (so this works identically on `test.demo.local`,
which has `developer_mode`, and `pharmacountry.vn`, which does not):

1. A `Custom Field` (`recommended_item`, Link -> Item, optional) on `Vet Technical Visit` — lets a
   visit optionally name a REAL recommended product (here, always Golden Demo #9's real
   `OXYTET-200-INJ`, which already carries real `target_species`/`indication`/
   `withdrawal_period_days` custom fields the portal's `get_my_recommendations()` reads directly).
   `Custom Field` rows are plain DB rows, independent of the base DocType's JSON/developer_mode —
   the same mechanism already used platform-wide (e.g. `bootstrap_vet_mfg_doctypes.py`'s own
   `target_species`/`indication`/`withdrawal_period_days` fields on `Item`).

2. A `Custom DocPerm` granting the native `Sales User` role READ-ONLY (not write/create/delete)
   access to `Vet Technical Visit`, which today only grants `System Manager` any access at all. This
   is what lets the native `Customer`-scoped `User Permission` cascade (same mechanism WEB-03/04/10
   already rely on for Sales Order/Sales Invoice/Supplier Quotation) actually restrict WHICH
   `Vet Technical Visit` rows a farm portal user's `frappe.get_list()` call returns — without this,
   `Sales User` has no base read permission on this doctype at all and the farm portal could not
   read its own technical visits through the same enforced-permission pattern platform's other
   portals use. `Custom DocPerm` is the exact same additive, DB-only mechanism Frappe's own "Role
   Permission Manager" UI produces — it never edits the base DocType's own `permissions` list, so it
   is equally safe/available on both sites regardless of `developer_mode`. Read-only, because a farm
   customer must never be able to create/edit/delete their own technical visit record (that stays a
   field-rep/back-office action). This does not broaden any OTHER doctype's visibility, and does not
   change what any EXISTING `Sales User`-role user can see beyond this one, narrow (read-only)
   doctype — any user without a `Customer`-scoped `User Permission` already sees company-wide data on
   every other cascaded doctype in this platform (Sales Order, Sales Invoice, Delivery Note,
   Purchase Order, ...); this is the identical trust model, not a new or broader one.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_farm_portal_doctypes.run
"""

import frappe

_DOCTYPE = "Vet Technical Visit"


def _add_recommended_item_field():
	fieldname = f"{_DOCTYPE}-recommended_item"
	if frappe.db.exists("Custom Field", fieldname):
		print(f"Custom Field '{fieldname}' already exists, skipping.")
		return False
	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": _DOCTYPE,
			"fieldname": "recommended_item",
			"label": "Recommended Item",
			"fieldtype": "Link",
			"options": "Item",
			"insert_after": "notes",
			"description": "Optional real product recommendation made during this visit (WEB-07 Farm Portal).",
		}
	).insert(ignore_permissions=True)
	print(f"Added Custom Field 'recommended_item' to {_DOCTYPE}.")
	return True


def _add_sales_user_read_permission():
	if frappe.db.exists("Custom DocPerm", {"parent": _DOCTYPE, "role": "Sales User"}):
		print(f"Custom DocPerm for 'Sales User' on {_DOCTYPE} already exists, skipping.")
		return False
	frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": _DOCTYPE,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": "Sales User",
			"permlevel": 0,
			"read": 1,
			"write": 0,
			"create": 0,
			"delete": 0,
			"report": 1,
			"select": 1,
			"share": 0,
			"email": 0,
			"print": 0,
			"export": 0,
		}
	).insert(ignore_permissions=True)
	print(f"Added Custom DocPerm: 'Sales User' read-only on {_DOCTYPE}.")
	return True


def run():
	if not frappe.db.exists("DocType", _DOCTYPE):
		print(f"SKIPPED — DocType '{_DOCTYPE}' doesn't exist yet. Run Golden Demo #10's "
			"bootstrap_vet_dist_doctypes.run first.")
		return
	_add_recommended_item_field()
	_add_sales_user_read_permission()
	frappe.clear_cache(doctype=_DOCTYPE)
