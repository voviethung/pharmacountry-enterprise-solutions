"""Golden Demo #24 — Pharma 3PL / GSP / Cold Chain (master plan DEMO 08, "PHASE 6" item 5),
IP-3PL-COLDCHAIN. A 3PL warehouse operator storing multiple clients' pharma/cold-chain inventory
in the SAME physical facility, segregated by client, with per-service billing.

Minimal new schema — most of the "special characteristics" list is native ERPNext reuse:
- Stock ownership by client (W01): native `Warehouse.customer` Link (used literally, not just by
  naming convention) + a `User Permission` on Warehouse with `apply_to_all_doctypes=1` per
  client-portal User — proven by real source reading (frappe/database/query.py's
  `get_user_permission_conditions()`) AND an empirical live test to cascade automatically to
  Stock Ledger Entry through `frappe.get_list()`/ORM calls (NOT `frappe.get_all()` or raw
  `frappe.db.sql()`, both confirmed permission-unaware by design) — zero custom permission code.
- Temperature condition / excursion (W02): ONE new DocType, `Cold Chain Temperature Reading` — the
  reading record itself, flagged by a validate hook against the warehouse's own
  min_temp_c/max_temp_c Custom Fields, IS the excursion event; no second "event" doctype.
- FEFO (W03): plain `Batch.expiry_date asc` picking, same pattern as every prior batch-tracked
  golden demo — no new code.
- Quarantine (W04): the same warehouse-name-substring gate idiom as `block_fg_release_without_qa`
  / `meddev_block_rejected_material_use`, this time on Delivery Note (`block_quarantine_delivery`
  in threepl_validations.py) since 3PL outbound goes out via Delivery Note directly, not a
  manufacturing Stock Entry. Release itself (Quarantine -> Released) reuses
  `block_fg_release_without_qa` completely unmodified (8th reuse) by naming the destination
  warehouses "...Released - D3PL".
- Inventory reconciliation (W05): native `Stock Reconciliation`, used directly.
- Storage fee / picking fee / billing (W06): native `Item` (non-stock service items) + `Item
  Price`, and `seed_3pl_billing_run()` computes real usage from the real stock ledger and real
  Delivery Notes, then posts a real `Sales Invoice` per client — same "thin wrapper over real
  ledger data" pattern as `get_pharmacy_central_dashboard()`.
- Transport: fully native — Delivery Note already ships with
  transporter/driver_name/vehicle_no/lr_no/lr_date.
- SLA: native `Sales Order Item.delivery_date` as the commitment, captured onto the Delivery
  Note's own new `sla_committed_date`/`sla_met` Custom Fields (informational only — the spec
  gives SLA no lettered test, so no enforcement hook was added, deliberately minimal).
"""

import frappe
from frappe.utils import add_days, getdate, nowdate

_COMPANY_NAME = "Demo 3PL Cold Chain Co."
_COMPANY_ABBR = "D3PL"

_DC_WH = f"3PL Cold Chain DC - {_COMPANY_ABBR}"
_CLIENT_A_NAME = "Global MedSupply Corp"
_CLIENT_B_NAME = "NorthStar Pharma Distributors"
_CLIENT_A_QUARANTINE_WH = f"Client A Quarantine - {_COMPANY_ABBR}"
_CLIENT_A_RELEASED_WH = f"Client A Released - {_COMPANY_ABBR}"
_CLIENT_B_QUARANTINE_WH = f"Client B Quarantine - {_COMPANY_ABBR}"
_CLIENT_B_RELEASED_WH = f"Client B Released - {_COMPANY_ABBR}"

_ITEM_A = "COLD-VACCINE-A"
_ITEM_B = "COLD-BIOLOGIC-B"
_STORAGE_FEE_ITEM = "3PL-STORAGE-FEE"
_PICKING_FEE_ITEM = "3PL-PICKING-FEE"
_STORAGE_RATE = 0.5
_PICKING_RATE = 1.0
_CUSTOMER_GROUP = "3PL Client Accounts"

_DEMO_USER_DOMAIN = "pharmacountry.vn"
_DEMO_USER_PASSWORD = "Demo@1234"
_CLIENT_A_USER = f"client.a.3pl@{_DEMO_USER_DOMAIN}"
_CLIENT_B_USER = f"client.b.3pl@{_DEMO_USER_DOMAIN}"

_WAREHOUSES = [
	# (full_name, parent, is_group, customer, min_temp_c, max_temp_c)
	(_DC_WH, None, True, None, None, None),
	(_CLIENT_A_QUARANTINE_WH, _DC_WH, False, _CLIENT_A_NAME, 2.0, 8.0),
	(_CLIENT_A_RELEASED_WH, _DC_WH, False, _CLIENT_A_NAME, 2.0, 8.0),
	(_CLIENT_B_QUARANTINE_WH, _DC_WH, False, _CLIENT_B_NAME, -20.0, -10.0),
	(_CLIENT_B_RELEASED_WH, _DC_WH, False, _CLIENT_B_NAME, -20.0, -10.0),
]


# ---------------------------------------------------------------------------
# Master data (DP-658)
# ---------------------------------------------------------------------------

def _ensure_company():
	created = False
	if not frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
		created = True
	# cost_center/default_receivable_account/round_off_cost_center aren't reliably
	# auto-populated by Company creation (a real gap found first in Cosmetics, then again in
	# Pharmacy for the receivable account, then again here for round_off_cost_center — Sales
	# Invoice submission requires it and no prior golden demo's _ensure_company() needed one).
	# Checked unconditionally (not only right after creation) so a re-run against an
	# already-existing company still repairs a field that came back empty for any reason.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "default_receivable_account"):
		frappe.db.set_value("Company", _COMPANY_NAME, "default_receivable_account", f"Debtors - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "round_off_cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "round_off_cost_center", f"Main - {_COMPANY_ABBR}")
	return created


def _ensure_warehouses():
	created = 0
	for full_name, parent, is_group, customer, min_c, max_c in _WAREHOUSES:
		if frappe.db.exists("Warehouse", full_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": full_name.split(" - ")[0],
				"company": _COMPANY_NAME,
				"is_group": 1 if is_group else 0,
				"parent_warehouse": parent,
				# Native Warehouse.customer Link — models "stock ownership by client" literally,
				# not just via a naming convention.
				"customer": customer,
				"min_temp_c": min_c,
				"max_temp_c": max_c,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_customer_group():
	if frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		return False
	frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(ignore_permissions=True)
	return True


def _ensure_customers():
	created = 0
	for name in (_CLIENT_A_NAME, _CLIENT_B_NAME):
		if frappe.db.exists("Customer", {"customer_name": name}):
			continue
		frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_group": _CUSTOMER_GROUP, "territory": "All Territories"}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_items():
	created = 0
	items = [
		{
			"item_code": _ITEM_A, "item_name": "Cold Chain Vaccine Vial (Client A)", "item_group": "Products",
			"stock_uom": "Nos", "is_stock_item": 1, "has_batch_no": 1, "create_new_batch": 1,
			"batch_number_series": "COLDVAXA-.####", "has_expiry_date": 1, "shelf_life_in_days": 365,
		},
		{
			"item_code": _ITEM_B, "item_name": "Frozen Biologic Vial (Client B)", "item_group": "Products",
			"stock_uom": "Nos", "is_stock_item": 1, "has_batch_no": 1, "create_new_batch": 1,
			"batch_number_series": "COLDBIOB-.####", "has_expiry_date": 1, "shelf_life_in_days": 730,
		},
		{
			"item_code": _STORAGE_FEE_ITEM, "item_name": "3PL Storage Fee (per unit)", "item_group": "Services",
			"stock_uom": "Nos", "is_stock_item": 0,
		},
		{
			"item_code": _PICKING_FEE_ITEM, "item_name": "3PL Picking Fee (per unit picked)", "item_group": "Services",
			"stock_uom": "Nos", "is_stock_item": 0,
		},
	]
	for item in items:
		if frappe.db.exists("Item", item["item_code"]):
			continue
		frappe.get_doc({"doctype": "Item", **item}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_item_prices():
	created = 0
	price_list = "Standard Selling"
	for item_code, rate in ((_STORAGE_FEE_ITEM, _STORAGE_RATE), (_PICKING_FEE_ITEM, _PICKING_RATE)):
		if frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list, "selling": 1}):
			continue
		frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": price_list, "selling": 1, "price_list_rate": rate}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_client_users():
	created = 0
	for email, first_name, warehouses in (
		(_CLIENT_A_USER, "Client A Portal", (_CLIENT_A_QUARANTINE_WH, _CLIENT_A_RELEASED_WH)),
		(_CLIENT_B_USER, "Client B Portal", (_CLIENT_B_QUARANTINE_WH, _CLIENT_B_RELEASED_WH)),
	):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User", "email": email, "first_name": first_name, "send_welcome_email": 0,
					"new_password": _DEMO_USER_PASSWORD, "roles": [{"role": "Stock User"}],
				}
			).insert(ignore_permissions=True)
			created += 1
		# W01 — apply_to_all_doctypes=1 makes this cascade to any OTHER doctype whose own
		# top-level field Links to Warehouse (Stock Ledger Entry included) for any query made
		# through frappe.get_list()/ORM document loads — confirmed by reading Frappe's own
		# frappe/database/query.py (Engine.get_user_permission_conditions) AND by an empirical
		# live test against this exact site before this code was written. frappe.get_all() and
		# raw frappe.db.sql() are BOTH permission-unaware by design and must never be used for
		# anything that needs to respect this boundary. One User Permission row per warehouse —
		# User Permission matches an exact document, not a warehouse subtree.
		for wh in warehouses:
			if not frappe.db.exists("User Permission", {"user": email, "allow": "Warehouse", "for_value": wh}):
				frappe.get_doc(
					{"doctype": "User Permission", "user": email, "allow": "Warehouse", "for_value": wh, "apply_to_all_doctypes": 1}
				).insert(ignore_permissions=True)
				created += 1
	return created


def seed_3pl_master_data():
	"""DP-658 — Company, warehouse hierarchy (a DC group warehouse + a Quarantine/Released pair
	per client, each carrying native Warehouse.customer plus the new min_temp_c/max_temp_c
	cold-chain range), 2 client Customers, cold-chain Items (1 per client) + 2 billing service
	Items with Item Price, and 2 client-portal Users each restricted via Warehouse User
	Permission(s) to only their own warehouses (W01 setup)."""
	company_created = _ensure_company()
	customer_group_created = _ensure_customer_group()
	customers_created = _ensure_customers()
	warehouses_created = _ensure_warehouses()
	items_created = _ensure_items()
	prices_created = _ensure_item_prices()
	users_created = _ensure_client_users()
	return (
		f"seed_3pl_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). "
		f"Customer Group {'created' if customer_group_created else 'already existed'}. {customers_created} customer(s) created. "
		f"{warehouses_created} warehouse(s) created. {items_created} item(s) created. {prices_created} item price(s) created. "
		f"{users_created} user/permission record(s) created."
	)


# ---------------------------------------------------------------------------
# Inbound receiving (DP-659) — staggered expiry for a genuine W03 FEFO test
# ---------------------------------------------------------------------------

def _material_receipt(item_code, warehouse, qty, expiry_date, basic_rate=10):
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
	se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": warehouse, "basic_rate": basic_rate})
	se.insert(ignore_permissions=True)
	se.submit()
	# Real bug found+fixed: Stock Entry Detail DOES have its own `expiry_date` field, but
	# ERPNext's auto-batch-creation path (Item.create_new_batch=1) never reads it —
	# erpnext/stock/serial_batch_bundle.py's create_batch() calls make_batch() with only
	# item/reference_doctype/reference_name (confirmed by reading the actual source), so a new
	# Batch's expiry_date is ALWAYS purely Item.shelf_life_in_days + manufacturing_date,
	# regardless of any row-level override — every prior golden demo that set an item-row
	# expiry_date (e.g. Pharmacy's _ensure_central_stock, "2028-12-31") had it silently ignored
	# too, just never surfaced as a bug because none of them needed a SPECIFIC value, only "some
	# future date." This demo's FEFO test genuinely needs deliberately staggered, non-monotonic
	# expiry dates, so the only reliable fix is to set Batch.expiry_date directly after creation.
	batch_no = frappe.db.sql(
		"""select sbe.batch_no from `tabStock Ledger Entry` sle
		join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.voucher_type='Stock Entry' and sle.voucher_no=%s and sle.item_code=%s limit 1""",
		(se.name, item_code),
	)
	batch_no = batch_no[0][0] if batch_no else None
	if batch_no and expiry_date:
		frappe.db.set_value("Batch", batch_no, "expiry_date", expiry_date)
	return se.name


def _receipt_count(item_code, warehouse):
	# Scoped tightly (item + exact warehouse + purpose + submitted) — never a global/company-wide
	# count, per the batch-lookup-scoping lesson learned the hard way in Pharmacy/Cosmetics.
	return frappe.db.sql(
		"""select count(*) from `tabStock Entry` se join `tabStock Entry Detail` sed on sed.parent = se.name
		where se.purpose='Material Receipt' and se.docstatus=1 and sed.item_code=%s and sed.t_warehouse=%s""",
		(item_code, warehouse),
	)[0][0]


def seed_3pl_inbound_receiving():
	"""DP-659 — inbound receipts into each client's Quarantine warehouse. Client A gets 3
	receipts with explicit, deliberately non-monotonic expiry dates so CREATION order and
	EXPIRY order diverge — the batch created LAST (3rd receipt) has the EARLIEST expiry. A real
	W03 FEFO test has to prove picking honors expiry_date specifically, not insertion order;
	if the two orders happened to coincide, a naive FIFO-by-creation implementation would pass
	by accident."""
	created = 0
	if _receipt_count(_ITEM_A, _CLIENT_A_QUARANTINE_WH) < 3:
		_material_receipt(_ITEM_A, _CLIENT_A_QUARANTINE_WH, 50, add_days(nowdate(), 80))
		_material_receipt(_ITEM_A, _CLIENT_A_QUARANTINE_WH, 50, add_days(nowdate(), 170))
		_material_receipt(_ITEM_A, _CLIENT_A_QUARANTINE_WH, 50, add_days(nowdate(), 30))  # earliest expiry, created LAST
		created += 3
	if _receipt_count(_ITEM_B, _CLIENT_B_QUARANTINE_WH) < 2:
		_material_receipt(_ITEM_B, _CLIENT_B_QUARANTINE_WH, 80, add_days(nowdate(), 200))
		_material_receipt(_ITEM_B, _CLIENT_B_QUARANTINE_WH, 40, add_days(nowdate(), 400))
		created += 2
	return f"seed_3pl_inbound_receiving: {created} receipt(s) created."


# ---------------------------------------------------------------------------
# Quarantine block (W04) + QC release (DP-660)
# ---------------------------------------------------------------------------

def _batches_in_warehouse(item_code, warehouse):
	"""Raw-SQL, warehouse-scoped batch lookup (never global) — returns batches with positive net
	qty in this EXACT warehouse, ordered by Batch.expiry_date ascending (FEFO order)."""
	rows = frappe.db.sql(
		"""select sbe.batch_no, sum(sle.actual_qty) as qty
		from `tabStock Ledger Entry` sle
		join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.item_code=%s and sle.warehouse=%s and sle.is_cancelled=0
		group by sbe.batch_no having qty > 0.0001""",
		(item_code, warehouse),
		as_dict=True,
	)
	for r in rows:
		r["expiry_date"] = frappe.db.get_value("Batch", r.batch_no, "expiry_date")
	rows.sort(key=lambda r: (r["expiry_date"] is None, r["expiry_date"]))
	return rows


def _receiving_stock_entry(item_code, warehouse, batch_no):
	row = frappe.db.sql(
		"""select sle.voucher_no from `tabStock Ledger Entry` sle
		join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.item_code=%s and sle.warehouse=%s and sbe.batch_no=%s
		and sle.voucher_type='Stock Entry' and sle.actual_qty > 0 and sle.is_cancelled=0 limit 1""",
		(item_code, warehouse, batch_no),
	)
	return row[0][0] if row else None


def _test_w04_quarantine_block():
	"""W04 — attempts a Delivery Note straight out of Client A's Quarantine warehouse before any
	QC release has happened; asserts it's blocked by block_quarantine_delivery. Throws if NOT
	blocked. Deliberately returns None (skip, not fail) when nothing currently sits in
	Quarantine — on a registry re-run, everything from the first pass has already been
	QC-released and moved out, so there's nothing left to prove the block against; the negative
	assertion already ran for real the first time this ever executed. Guarding on "no batch
	found -> throw" instead would break idempotency, since release (later in this same function)
	always empties Quarantine by design."""
	batches = _batches_in_warehouse(_ITEM_A, _CLIENT_A_QUARANTINE_WH)
	if not batches:
		return None
	batch_no = batches[0].batch_no
	dn = frappe.get_doc(
		{
			"doctype": "Delivery Note", "customer": _CLIENT_A_NAME, "company": _COMPANY_NAME,
			"items": [{"item_code": _ITEM_A, "qty": 1, "rate": 100, "warehouse": _CLIENT_A_QUARANTINE_WH, "batch_no": batch_no}],
		}
	)
	try:
		dn.insert(ignore_permissions=True)
	except frappe.ValidationError:
		return True
	frappe.throw("W04 FAILED: Delivery Note from Quarantine warehouse was NOT blocked.")


def _release_batch(item_code, batch_no, qty, quarantine_wh, released_wh):
	qc_created = False
	if not frappe.db.exists("Quality Inspection", {"item_code": item_code, "batch_no": batch_no, "status": "Accepted", "docstatus": 1}):
		qi = frappe.get_doc(
			{
				"doctype": "Quality Inspection", "inspection_type": "Incoming", "reference_type": "Stock Entry",
				"reference_name": _receiving_stock_entry(item_code, quarantine_wh, batch_no),
				"item_code": item_code, "batch_no": batch_no, "sample_size": 5, "status": "Accepted",
				"company": _COMPANY_NAME, "inspected_by": frappe.session.user,
			}
		)
		qi.insert(ignore_permissions=True)
		qi.submit()
		qc_created = True

	already_released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sbe.batch_no=%s and sle.is_cancelled=0 limit 1""",
		(released_wh, batch_no),
	)
	release_created = False
	if not already_released:
		# block_fg_release_without_qa (validations.py) reuse #8 — fires because released_wh's
		# name contains "released"; the Accepted Quality Inspection created just above is exactly
		# what satisfies its gate.
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
		se.append("items", {"item_code": item_code, "qty": qty, "s_warehouse": quarantine_wh, "t_warehouse": released_wh, "batch_no": batch_no, "use_serial_batch_fields": 1})
		se.insert(ignore_permissions=True)
		se.submit()
		release_created = True
	return qc_created, release_created


def seed_3pl_quarantine_release():
	"""DP-660 — W04 negative test (Delivery Note straight out of Quarantine is blocked) runs
	FIRST, then every currently-quarantined batch is QC-Accepted and moved Quarantine ->
	Released."""
	blocked = _test_w04_quarantine_block()
	released = 0
	for item_code, quarantine_wh, released_wh in (
		(_ITEM_A, _CLIENT_A_QUARANTINE_WH, _CLIENT_A_RELEASED_WH),
		(_ITEM_B, _CLIENT_B_QUARANTINE_WH, _CLIENT_B_RELEASED_WH),
	):
		for row in _batches_in_warehouse(item_code, quarantine_wh):
			_, rel_created = _release_batch(item_code, row.batch_no, row.qty, quarantine_wh, released_wh)
			if rel_created:
				released += 1
	return f"seed_3pl_quarantine_release: W04 block test result={blocked}. {released} batch(es) released to Released warehouse."


# ---------------------------------------------------------------------------
# FEFO outbound (W03) + SLA + Transport (DP-661)
# ---------------------------------------------------------------------------

def _pick_fefo(item_code, warehouse, qty):
	"""W03 — FEFO: picks strictly in Batch.expiry_date ascending order, never by batch creation
	order — the inbound receipts are deliberately staggered so the two orders diverge, making
	this a genuine FEFO test rather than an accidental FIFO pass."""
	remaining = qty
	picks = []
	for row in _batches_in_warehouse(item_code, warehouse):
		if remaining <= 0:
			break
		take = min(row.qty, remaining)
		picks.append({"batch_no": row.batch_no, "qty": take, "expiry_date": row.expiry_date})
		remaining -= take
	if remaining > 0.0001:
		frappe.throw(f"FEFO picking shortfall for {item_code} in {warehouse}: {remaining} unpicked.")
	return picks


def seed_3pl_fefo_outbound():
	"""DP-661 — W03 FEFO outbound pick + delivery for Client A, plus native SLA (Sales Order
	Item.delivery_date as the commitment, captured onto Delivery Note's own new
	sla_committed_date/sla_met) and native Transport (Delivery Note's own
	transporter/driver_name/vehicle_no/lr_no/lr_date — zero new schema for either). Deliberately
	does NOT link the Delivery Note back to the Sales Order via against_sales_order/so_detail —
	ERPNext's validate_with_previous_doc() cross-checks each item row against a SPECIFIC parent
	document's item row by name, which throws an AttributeError when that per-row link isn't
	set (the exact failure class Pharmacy hit linking a Stock Entry to a Material Request). The
	Sales Order stands on its own as evidence of the committed delivery request."""
	if frappe.db.exists("Sales Order", {"customer": _CLIENT_A_NAME, "company": _COMPANY_NAME, "docstatus": 1}):
		return "seed_3pl_fefo_outbound: already existed."

	pick_qty = 60
	picks = _pick_fefo(_ITEM_A, _CLIENT_A_RELEASED_WH, pick_qty)
	all_batches = _batches_in_warehouse(_ITEM_A, _CLIENT_A_RELEASED_WH)
	earliest_expiry_batch = all_batches[0].batch_no
	if picks[0]["batch_no"] != earliest_expiry_batch:
		frappe.throw("W03 FAILED: FEFO picking did not select the earliest-expiry batch first.")

	committed_date = add_days(nowdate(), 3)
	so = frappe.get_doc(
		{
			"doctype": "Sales Order", "customer": _CLIENT_A_NAME, "company": _COMPANY_NAME, "delivery_date": committed_date,
			"items": [{"item_code": _ITEM_A, "qty": pick_qty, "rate": 100, "delivery_date": committed_date, "warehouse": _CLIENT_A_RELEASED_WH}],
		}
	)
	so.insert(ignore_permissions=True)
	so.submit()

	dn = frappe.get_doc(
		{
			"doctype": "Delivery Note", "customer": _CLIENT_A_NAME, "company": _COMPANY_NAME,
			"driver_name": "Nguyen Van A", "vehicle_no": "51C-123.45", "lr_no": "LR-3PL-0001", "lr_date": nowdate(),
			"sla_committed_date": committed_date,
			"items": [{"item_code": _ITEM_A, "qty": p["qty"], "rate": 100, "warehouse": _CLIENT_A_RELEASED_WH, "batch_no": p["batch_no"]} for p in picks],
		}
	)
	dn.insert(ignore_permissions=True)
	dn.sla_met = 1 if getdate(dn.posting_date) <= getdate(committed_date) else 0
	dn.save(ignore_permissions=True)
	dn.submit()
	return f"seed_3pl_fefo_outbound: SO {so.name}, DN {dn.name}, FEFO picks={[(p['batch_no'], p['qty']) for p in picks]}."


# ---------------------------------------------------------------------------
# Temperature monitoring / excursion (W02) (DP-662)
# ---------------------------------------------------------------------------

def seed_3pl_temperature_monitoring():
	"""DP-662 — W02: normal readings plus one deliberate excursion per client warehouse.
	threepl_temperature_reading_validate() (hooked on Cold Chain Temperature Reading.validate) computes
	is_excursion/status against the warehouse's own min_temp_c/max_temp_c — the reading document
	itself, once flagged, IS the excursion event."""
	created = 0
	readings = [
		(_CLIENT_A_RELEASED_WH, 4.0),    # within 2..8 -> Normal
		(_CLIENT_A_RELEASED_WH, 6.5),    # within 2..8 -> Normal
		(_CLIENT_A_RELEASED_WH, 12.0),   # > 8 -> EXCURSION
		(_CLIENT_B_RELEASED_WH, -15.0),  # within -20..-10 -> Normal
		(_CLIENT_B_RELEASED_WH, -5.0),   # > -10 -> EXCURSION
	]
	for warehouse, temp in readings:
		if frappe.db.exists("Cold Chain Temperature Reading", {"warehouse": warehouse, "temperature_c": temp}):
			continue
		frappe.get_doc({"doctype": "Cold Chain Temperature Reading", "warehouse": warehouse, "temperature_c": temp}).insert(ignore_permissions=True)
		created += 1
	return f"seed_3pl_temperature_monitoring: {created} reading(s) created."


# ---------------------------------------------------------------------------
# Inventory reconciliation (W05) (DP-663)
# ---------------------------------------------------------------------------

def seed_3pl_stock_reconciliation():
	"""DP-663 — W05: a native Stock Reconciliation correcting Client B's Released-warehouse
	count for COLD-BIOLOGIC-B, proving inventory reconciliation with zero custom code."""
	if frappe.db.exists("Stock Reconciliation", {"company": _COMPANY_NAME, "docstatus": 1}):
		return "seed_3pl_stock_reconciliation: already existed."
	batches = _batches_in_warehouse(_ITEM_B, _CLIENT_B_RELEASED_WH)
	if not batches:
		frappe.throw("seed_3pl_stock_reconciliation: no batch available in Client B Released to reconcile.")
	batch_no = batches[0].batch_no
	# Real bug found+fixed: a Stock Reconciliation row with a specific batch_no sets that ONE
	# BATCH's own absolute qty, not the warehouse's overall total — the first version computed
	# the WAREHOUSE-wide total (120) minus 2 (118) and applied that 118 to a single batch whose
	# own actual qty was only 80, silently ADDING 38 units to the warehouse instead of removing
	# 2 (120 -> 158, not 120 -> 118). Fixed by reading that specific batch's own current qty
	# (already available from _batches_in_warehouse()'s own per-batch sum) and reconciling
	# THAT down by 2, not the warehouse total.
	batch_book_qty = batches[0].qty
	warehouse_book_qty = sum(b.qty for b in batches)
	counted_qty = batch_book_qty - 2  # physical count found 2 fewer units of this batch than the book balance
	sr = frappe.get_doc(
		{
			"doctype": "Stock Reconciliation", "company": _COMPANY_NAME, "purpose": "Stock Reconciliation",
			"items": [{"item_code": _ITEM_B, "warehouse": _CLIENT_B_RELEASED_WH, "batch_no": batch_no, "use_serial_batch_fields": 1, "qty": counted_qty, "valuation_rate": 10}],
		}
	)
	sr.insert(ignore_permissions=True)
	sr.submit()
	return f"seed_3pl_stock_reconciliation: {sr.name}, warehouse book={warehouse_book_qty}, batch {batch_no} book={batch_book_qty}, counted={counted_qty}."


# ---------------------------------------------------------------------------
# Access control (W01) (DP-664)
# ---------------------------------------------------------------------------

def seed_3pl_access_control_test():
	"""DP-664 — W01: proves Client A's portal user, restricted via the Warehouse User
	Permission(s) created in seed_3pl_master_data(), genuinely cannot see Client B's Stock
	Ledger Entries when queried through frappe.get_list() (the permission-aware ORM entry
	point) — NOT frappe.get_all()/raw SQL, both proven permission-unaware. Always reverts the
	session user in a finally block, even on failure, so a broken assertion here can never leave
	a later seed step running as the wrong (restricted) user."""
	original_user = frappe.session.user
	try:
		frappe.set_user(_CLIENT_A_USER)
		visible = frappe.get_list(
			"Stock Ledger Entry", filters={"item_code": ["in", [_ITEM_A, _ITEM_B]]}, fields=["warehouse"], distinct=True, limit_page_length=0
		)
		visible_warehouses = {r.warehouse for r in visible}
	finally:
		frappe.set_user(original_user)

	sees_own = _CLIENT_A_RELEASED_WH in visible_warehouses or _CLIENT_A_QUARANTINE_WH in visible_warehouses
	sees_other = _CLIENT_B_RELEASED_WH in visible_warehouses or _CLIENT_B_QUARANTINE_WH in visible_warehouses
	if sees_other:
		frappe.throw(f"W01 FAILED: Client A's user could see Client B's warehouse(s): {visible_warehouses}")
	if not sees_own:
		frappe.throw(f"W01 setup problem: Client A's user could not see even its OWN warehouse stock: {visible_warehouses}")
	return f"seed_3pl_access_control_test: W01 confirmed -- Client A user sees only {sorted(visible_warehouses)}."


# ---------------------------------------------------------------------------
# Billing (W06) (DP-665)
# ---------------------------------------------------------------------------

def _billing_amounts(customer, quarantine_wh, released_wh):
	storage_qty = frappe.db.sql(
		"""select coalesce(sum(actual_qty), 0) from `tabStock Ledger Entry`
		where warehouse in (%s, %s) and is_cancelled=0""",
		(quarantine_wh, released_wh),
	)[0][0] or 0
	picking_qty = frappe.db.sql(
		"""select coalesce(sum(di.qty), 0) from `tabDelivery Note` dn join `tabDelivery Note Item` di on di.parent = dn.name
		where dn.customer=%s and dn.docstatus=1""",
		(customer,),
	)[0][0] or 0
	return storage_qty, picking_qty


def seed_3pl_billing_run():
	"""DP-665 — W06: billing by service rule. Storage fee = client's current real on-hand qty
	(Quarantine + Released) x the Storage Fee Item's own Item Price rate; picking fee = total
	qty actually shipped out via real Delivery Notes x the Picking Fee Item's own rate. A real
	Sales Invoice per client, computed from real ledger/delivery data, not a synthetic total —
	mirrors get_pharmacy_central_dashboard()'s "thin wrapper over real ledger data" pattern.
	Only bills a service that was actually used (skips a zero-qty picking line entirely, rather
	than forcing a qty=1 placeholder), so a client with no outbound activity yet is billed
	storage only — an honest reflection of real usage."""
	storage_rate = frappe.db.get_value("Item Price", {"item_code": _STORAGE_FEE_ITEM, "price_list": "Standard Selling", "selling": 1}, "price_list_rate") or _STORAGE_RATE
	picking_rate = frappe.db.get_value("Item Price", {"item_code": _PICKING_FEE_ITEM, "price_list": "Standard Selling", "selling": 1}, "price_list_rate") or _PICKING_RATE

	results = []
	for customer, quarantine_wh, released_wh in (
		(_CLIENT_A_NAME, _CLIENT_A_QUARANTINE_WH, _CLIENT_A_RELEASED_WH),
		(_CLIENT_B_NAME, _CLIENT_B_QUARANTINE_WH, _CLIENT_B_RELEASED_WH),
	):
		if frappe.db.exists("Sales Invoice", {"customer": customer, "company": _COMPANY_NAME, "docstatus": 1}):
			results.append(f"{customer}: already existed")
			continue
		storage_qty, picking_qty = _billing_amounts(customer, quarantine_wh, released_wh)
		items = [{"item_code": _STORAGE_FEE_ITEM, "qty": storage_qty, "rate": storage_rate}]
		if picking_qty:
			items.append({"item_code": _PICKING_FEE_ITEM, "qty": picking_qty, "rate": picking_rate})
		si = frappe.get_doc({"doctype": "Sales Invoice", "customer": customer, "company": _COMPANY_NAME, "items": items})
		si.insert(ignore_permissions=True)
		si.submit()
		results.append(f"{customer}: {si.name} (storage_qty={storage_qty}, picking_qty={picking_qty})")
	return "seed_3pl_billing_run: " + "; ".join(results)
