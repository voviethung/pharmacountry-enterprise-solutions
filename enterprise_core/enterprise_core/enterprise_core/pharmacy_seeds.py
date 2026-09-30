"""Golden Demo #23 — Pharmacy Chain (master plan DEMO 09, "PHASE 6" item 4), IP-PHARMACY.
Zero new DocTypes — pure native ERPNext reuse: HQ/Central/Store are just Warehouses, POS is
native POS Invoice/POS Profile/POS Opening Entry, "Promotion" is a native Pricing Rule,
"Replenishment" is a native Material Request + Stock Entry, "Expired product blocked" is
native StockController behavior (proven with zero custom code already, by Golden Demo #2's
PD02), and "Central dashboard" is a plain aggregate query function, not a stored doctype.
Reuses Golden Demo #1's own "Paracetamol 500 mg Tablet" Item directly — Item isn't
company-scoped.
"""

import frappe

_COMPANY_NAME = "Demo Pharmacy Chain Co."
_COMPANY_ABBR = "DPH"
_CENTRAL_WH = f"Central Warehouse - {_COMPANY_ABBR}"
_STORE_A_WH = f"Store A - {_COMPANY_ABBR}"
_STORE_B_WH = f"Store B - {_COMPANY_ABBR}"
_ITEM = "PARA-500-TAB"  # item_code, not item_name — "Paracetamol 500 mg Tablet" is the display name
_POS_PROFILE = "Pharmacy Store A POS"
_CUSTOMER_NAME = "Pharmacy Walk-in Customer"


def _ensure_company():
	if frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		return False
	frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	# POS Invoice needs a receivable account to post against ("Credit To") — not auto-populated
	# by Company creation the way cost_center is, found as a real gap on the first POS sale.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "default_receivable_account"):
		frappe.db.set_value("Company", _COMPANY_NAME, "default_receivable_account", f"Debtors - {_COMPANY_ABBR}")
	return True


def _ensure_warehouses():
	created = 0
	for wh in (_CENTRAL_WH, _STORE_A_WH, _STORE_B_WH):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)
			created += 1
	return created


def _ensure_central_stock():
	# Guards on whether a receipt has ever happened, not on the CURRENT balance — same
	# fluctuating-balance idempotency issue fixed in _ensure_replenishment(): once
	# replenishment consumes some of this stock, a balance-based guard would silently top up
	# Central again on every subsequent re-run instead of recognizing the initial receipt
	# already happened.
	if frappe.db.exists("Stock Entry", {"purpose": "Material Receipt", "company": _COMPANY_NAME, "docstatus": 1}):
		return False
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
	se.append("items", {"item_code": _ITEM, "qty": 500, "t_warehouse": _CENTRAL_WH, "basic_rate": 800, "expiry_date": "2028-12-31"})
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def _ensure_mode_of_payment_account():
	mop = frappe.get_doc("Mode of Payment", "Cash")
	if any(row.company == _COMPANY_NAME for row in mop.accounts):
		return False
	mop.append("accounts", {"company": _COMPANY_NAME, "default_account": f"Cash - {_COMPANY_ABBR}"})
	mop.save(ignore_permissions=True)
	return True


def _ensure_pos_profile():
	if frappe.db.exists("POS Profile", _POS_PROFILE):
		return False
	frappe.get_doc(
		{
			"doctype": "POS Profile",
			"name": _POS_PROFILE,
			"company": _COMPANY_NAME,
			"warehouse": _STORE_A_WH,
			"currency": "VND",
			"selling_price_list": "Standard Selling",
			"write_off_account": f"Write Off - {_COMPANY_ABBR}",
			"write_off_cost_center": f"Main - {_COMPANY_ABBR}",
			"write_off_limit": 1,
			"payments": [{"mode_of_payment": "Cash", "default": 1}],
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_walkin_customer():
	if frappe.db.exists("Customer", {"customer_name": _CUSTOMER_NAME}):
		return False
	frappe.get_doc({"doctype": "Customer", "customer_name": _CUSTOMER_NAME, "customer_type": "Individual"}).insert(ignore_permissions=True)
	return True


def _ensure_pos_settings():
	"""This site's POS Settings.invoice_type defaults to "Sales Invoice" — which blocks
	creating any non-return `POS Invoice` outright ("Sales Invoice mode is activated in POS")
	— found as a real config gap once the first POS Invoice insert failed. Switching it to
	"POS Invoice" is safe: grepped the whole codebase first and confirmed no other golden demo
	touches POS at all, so there's nothing else this could conflict with."""
	if frappe.db.get_single_value("POS Settings", "invoice_type") == "POS Invoice":
		return False
	frappe.db.set_value("POS Settings", "POS Settings", "invoice_type", "POS Invoice")
	return True


def seed_pharmacy_master_data():
	"""DP-648 — Company, Warehouses (HQ/Central/2 Stores), central stock, POS Profile + Mode
	of Payment Account, walk-in Customer, POS Settings (invoice_type=POS Invoice)."""
	pos_settings_fixed = _ensure_pos_settings()
	company_created = _ensure_company()
	warehouses_created = _ensure_warehouses()
	stock_received = _ensure_central_stock()
	mop_created = _ensure_mode_of_payment_account()
	pos_profile_created = _ensure_pos_profile()
	customer_created = _ensure_walkin_customer()
	return (
		f"seed_pharmacy_master_data: POS Settings {'fixed (invoice_type=POS Invoice)' if pos_settings_fixed else 'already correct'}. "
		f"Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). {warehouses_created} warehouse(s) created. "
		f"Central stock {'received' if stock_received else 'already present'}. Mode of Payment Account {'created' if mop_created else 'already existed'}. "
		f"POS Profile {'created' if pos_profile_created else 'already existed'}. Customer {'created' if customer_created else 'already existed'}."
	)


def _central_batch():
	# Scoped to Central Warehouse via the stock ledger, not `{"item": _ITEM}` alone —
	# PARA-500-TAB is reused globally from Golden Demo #1, so an unscoped "oldest batch of this
	# item" lookup silently resolves to PHARMA MANUFACTURING'S OWN batch instead (same bug
	# class already found and fixed in Cosmetics' `_original_bulk_batch()`), causing a
	# nonsensical "negative stock in Central Warehouse - DPH" once this function tries to move
	# 150 units of a batch that was never actually received there.
	row = frappe.db.sql(
		"""select sbe.batch_no from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sle.item_code=%s and sle.is_cancelled=0 and sle.actual_qty > 0 order by sle.creation asc limit 1""",
		(_CENTRAL_WH, _ITEM),
	)
	return row[0][0] if row else None


def _ensure_replenishment():
	central_batch = _central_batch()
	# Guards on whether the replenishment TRANSACTION already exists, not on Store A's CURRENT
	# balance — a balance-based guard isn't stable once the inter-store transfer (DP-650) moves
	# some of that stock on to Store B afterward: Store A's balance drops back below the
	# threshold, and a balance check alone would silently re-trigger another replenishment on
	# every subsequent idempotent re-run instead of recognizing the original one already
	# happened. Found as a real non-idempotency bug — Central Warehouse's balance kept
	# shrinking release over release.
	existing_mr = frappe.db.exists("Material Request", {"material_request_type": "Material Transfer", "company": _COMPANY_NAME})
	if existing_mr:
		return False, existing_mr, False
	mr = frappe.get_doc(
		{
			"doctype": "Material Request",
			"material_request_type": "Material Transfer",
			"company": _COMPANY_NAME,
			"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 1),
			"items": [{"item_code": _ITEM, "qty": 150, "warehouse": _STORE_A_WH, "from_warehouse": _CENTRAL_WH, "schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 1)}],
		}
	)
	mr.insert(ignore_permissions=True)
	mr.submit()
	mr_name = mr.name

	# Deliberately NOT linking this Stock Entry back to the Material Request (no
	# `material_request`/`material_request_item` fields) — ERPNext's own
	# validate_with_material_request() cross-checks each Stock Entry item row against a
	# SPECIFIC Material Request Item row by name, not just the parent Material Request, and
	# throws an AttributeError on a None match when that per-row link isn't set. The Material
	# Request still stands as evidence a replenishment request was made; this Stock Entry
	# independently fulfills the physical movement.
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	se.append("items", {"item_code": _ITEM, "qty": 150, "s_warehouse": _CENTRAL_WH, "t_warehouse": _STORE_A_WH, "batch_no": central_batch, "use_serial_batch_fields": 1})
	se.insert(ignore_permissions=True)
	se.submit()
	return True, mr_name, True


def seed_pharmacy_replenishment():
	"""DP-649 — RX02, HQ replenishment. A Material Request (Material Transfer type) from Store
	A, fulfilled by a Stock Entry moving stock from Central to Store A."""
	if not frappe.db.exists("Warehouse", _STORE_A_WH):
		return "seed_pharmacy_replenishment: SKIPPED — run seed_pharmacy_master_data first."
	replenished, mr_name, mr_created = _ensure_replenishment()
	return f"seed_pharmacy_replenishment: RX02 {'CONFIRMED — replenished' if replenished else 'already replenished'} (Material Request {mr_name})."


def seed_pharmacy_inter_store_transfer():
	"""DP-650 — RX04, inter-store batch transfer. Store A -> Store B, same batch preserved."""
	# Excludes RX03-EXPIRED-TEST for the same reason DP-653's own batch lookup needed it — and
	# the idempotency guard checks specifically for a transfer INTO Store B, not just "any 2nd
	# Material Transfer for this company" (that generic count was satisfied by TWO Central ->
	# Store A replenishments instead — found as a real bug once Store B's stock verified as 0
	# despite this step reporting "already existed" on every re-run, having never once actually
	# moved anything to Store B).
	if frappe.db.exists("Stock Entry Detail", {"t_warehouse": _STORE_B_WH, "item_code": _ITEM}):
		return "seed_pharmacy_inter_store_transfer: already existed."
	batch_no = frappe.db.sql(
		"""select sbe.batch_no from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sle.item_code=%s and sle.is_cancelled=0 and sle.actual_qty > 0 and sbe.batch_no != 'RX03-EXPIRED-TEST' limit 1""",
		(_STORE_A_WH, _ITEM),
	)
	if not batch_no:
		return "seed_pharmacy_inter_store_transfer: SKIPPED — run seed_pharmacy_replenishment first."
	batch_no = batch_no[0][0]
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	se.append("items", {"item_code": _ITEM, "qty": 30, "s_warehouse": _STORE_A_WH, "t_warehouse": _STORE_B_WH, "batch_no": batch_no, "use_serial_batch_fields": 1})
	se.insert(ignore_permissions=True)
	se.submit()
	return f"seed_pharmacy_inter_store_transfer: RX04 CONFIRMED — batch {batch_no} transferred Store A -> Store B."


def seed_pharmacy_pos_session():
	"""DP-651 — opens today's POS session (POS Opening Entry) for Store A's POS Profile,
	required by POS Invoice's own server-side validate() before any sale can be recorded."""
	if not frappe.db.exists("POS Profile", _POS_PROFILE):
		return "seed_pharmacy_pos_session: SKIPPED — run seed_pharmacy_master_data first."
	if frappe.db.exists("POS Opening Entry", {"pos_profile": _POS_PROFILE, "status": "Open"}):
		return "seed_pharmacy_pos_session: already open."
	entry = frappe.get_doc(
		{
			"doctype": "POS Opening Entry",
			"period_start_date": frappe.utils.now_datetime(),
			"posting_date": frappe.utils.nowdate(),
			"company": _COMPANY_NAME,
			"pos_profile": _POS_PROFILE,
			"user": frappe.session.user,
			"balance_details": [{"mode_of_payment": "Cash", "opening_amount": 500000}],
		}
	)
	entry.insert(ignore_permissions=True)
	entry.submit()
	return f"seed_pharmacy_pos_session: opened ({entry.name})."


def _test_rx03_expired_batch_blocked():
	marker = "RX03-EXPIRED-TEST"
	if (frappe.db.get_value("Batch", marker, "batch_qty") or 0) <= 0:
		se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
		se.append("items", {"item_code": _ITEM, "qty": 10, "t_warehouse": _STORE_A_WH, "basic_rate": 800, "expiry_date": "2030-01-01"})
		se.insert(ignore_permissions=True)
		se.submit()
		new_batch = frappe.db.get_value("Batch", {"item": _ITEM}, "name", order_by="creation desc")
		frappe.rename_doc("Batch", new_batch, marker, force=True)
		frappe.db.set_value("Batch", marker, "expiry_date", "2020-01-01")

	attempt = frappe.get_doc(
		{
			"doctype": "POS Invoice",
			"customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"),
			"company": _COMPANY_NAME,
			"pos_profile": _POS_PROFILE,
			"is_pos": 1,
			"update_stock": 1,
			"items": [{"item_code": _ITEM, "qty": 1, "rate": 1500, "warehouse": _STORE_A_WH, "batch_no": marker}],
			"payments": [{"mode_of_payment": "Cash", "amount": 1500}],
		}
	)
	blocked = False
	try:
		attempt.insert(ignore_permissions=True)
		attempt.submit()
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("RX03 negative test FAILED: a POS sale of an expired batch was not blocked!")
	return True


def seed_pharmacy_expiry_block():
	"""DP-652 — RX03, expired product blocked. Native ERPNext StockController behavior (same
	zero-custom-code finding as Golden Demo #2's PD02) — proven here against a POS Invoice
	specifically, not just a Delivery Note."""
	if not frappe.db.exists("POS Opening Entry", {"pos_profile": _POS_PROFILE, "status": "Open"}):
		return "seed_pharmacy_expiry_block: SKIPPED — run seed_pharmacy_pos_session first."
	rx03 = _test_rx03_expired_batch_blocked()
	return f"seed_pharmacy_expiry_block: RX03 CONFIRMED ({rx03})."


def seed_pharmacy_pos_sale():
	"""DP-653 — a real POS sale, the prerequisite for RX05's return test."""
	if not frappe.db.exists("POS Opening Entry", {"pos_profile": _POS_PROFILE, "status": "Open"}):
		return "seed_pharmacy_pos_sale: SKIPPED — run seed_pharmacy_pos_session first."
	if frappe.db.exists("POS Invoice", {"pos_profile": _POS_PROFILE, "is_return": 0, "docstatus": 1}):
		return "seed_pharmacy_pos_sale: already existed."
	# Excludes RX03-EXPIRED-TEST explicitly — with no such exclusion (and no ORDER BY), this
	# query non-deterministically picked the deliberately-expired batch instead of the real
	# replenished stock once both had positive quantity in Store A, making this REAL sale fail
	# with the same "batch has already expired" error DP-652's negative test expects.
	batch_no = frappe.db.sql(
		"""select sbe.batch_no from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse=%s and sle.item_code=%s and sle.is_cancelled=0 and sle.actual_qty > 0 and sbe.batch_no != 'RX03-EXPIRED-TEST' limit 1""",
		(_STORE_A_WH, _ITEM),
	)
	batch_no = batch_no[0][0] if batch_no else None
	inv = frappe.get_doc(
		{
			"doctype": "POS Invoice",
			"customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"),
			"company": _COMPANY_NAME,
			"pos_profile": _POS_PROFILE,
			"is_pos": 1,
			"update_stock": 1,
			"items": [{"item_code": _ITEM, "qty": 10, "rate": 1500, "warehouse": _STORE_A_WH, "batch_no": batch_no}],
			"payments": [{"mode_of_payment": "Cash", "amount": 15000}],
		}
	)
	inv.insert(ignore_permissions=True)
	# Payment must cover the ACTUAL computed grand_total, not the un-discounted 15000 assumed
	# above — a live Pricing Rule (created by seed_pharmacy_promotion, which may have already
	# run in an earlier registry pass) can auto-discount this same item, and POS Invoice
	# rejects any payment that doesn't exactly cover whatever grand_total it actually computed.
	# Found as a real "Paid amount + Write Off Amount can not be greater than Grand Total" error.
	if inv.payments[0].amount != inv.grand_total:
		inv.payments[0].amount = inv.grand_total
		inv.paid_amount = inv.grand_total  # not auto-resynced from the payments row on a plain save()
		inv.save(ignore_permissions=True)
	inv.submit()
	return f"seed_pharmacy_pos_sale: created ({inv.name})."


def seed_pharmacy_pos_return():
	"""DP-654 — RX05, POS return. Uses ERPNext's native return mechanism (make_return_doc),
	same pattern as Golden Demo #2's PD05 customer return."""
	original = frappe.db.get_value("POS Invoice", {"pos_profile": _POS_PROFILE, "is_return": 0, "docstatus": 1}, "name")
	if not original:
		return "seed_pharmacy_pos_return: SKIPPED — run seed_pharmacy_pos_sale first."
	if frappe.db.exists("POS Invoice", {"return_against": original, "docstatus": 1}):
		return "seed_pharmacy_pos_return: already existed."
	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	original_grand_total = frappe.db.get_value("POS Invoice", original, "grand_total")
	ret = make_return_doc("POS Invoice", original)
	# make_return_doc negates items/totals but doesn't touch the POS-specific "payments" child
	# table, leaving it at the ORIGINAL (positive) invoice's amount — mismatched against the
	# return's own negative grand_total. And POS Invoice's payment-vs-total check runs during
	# validate(), which fires on insert() itself, not just submit() — so the fix has to happen
	# BEFORE insert, using the original invoice's own (already-known) grand_total negated,
	# not `ret.grand_total` read back afterward (that direct-throw-after-insert approach never
	# even ran: the mismatch error fired first, during insert's own validate() call). Found as
	# the same "Paid amount + Write Off Amount can not be greater than Grand Total" error
	# DP-653 hit, one step further down the flow.
	if ret.payments:
		ret.payments[0].amount = -original_grand_total
		ret.paid_amount = -original_grand_total  # not auto-resynced from the payments row
	ret.insert(ignore_permissions=True)
	ret.submit()
	return f"seed_pharmacy_pos_return: RX05 CONFIRMED — return {ret.name} created against {original}."


_PRICING_RULE_NAME = "Pharmacy Loyalty Week Promotion"


def seed_pharmacy_promotion():
	"""DP-655 — RX06, promotion. A native Pricing Rule discounting the item by 10%, then a
	Sales Order proving the discounted rate applies automatically."""
	if not frappe.db.exists("POS Profile", _POS_PROFILE):
		return "seed_pharmacy_promotion: SKIPPED — run seed_pharmacy_master_data first."
	rule_created = False
	if not frappe.db.exists("Pricing Rule", {"title": _PRICING_RULE_NAME}):
		frappe.get_doc(
			{
				"doctype": "Pricing Rule",
				"title": _PRICING_RULE_NAME,
				"apply_on": "Item Code",
				"items": [{"item_code": _ITEM}],
				"selling": 1,
				"company": _COMPANY_NAME,
				"currency": "VND",
				"rate_or_discount": "Discount Percentage",
				"discount_percentage": 10,
				"valid_from": frappe.utils.add_days(frappe.utils.nowdate(), -1),
				"valid_upto": frappe.utils.add_days(frappe.utils.nowdate(), 30),
			}
		).insert(ignore_permissions=True)
		rule_created = True

	so_name = frappe.db.exists("Sales Order", {"company": _COMPANY_NAME, "docstatus": 1})
	if not so_name:
		so = frappe.get_doc(
			{"doctype": "Sales Order", "customer": frappe.db.get_value("Customer", {"customer_name": _CUSTOMER_NAME}, "name"), "company": _COMPANY_NAME, "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 3), "items": [{"item_code": _ITEM, "qty": 20, "rate": 1500, "warehouse": _STORE_A_WH}]}
		)
		so.insert(ignore_permissions=True)
		discounted_rate = so.items[0].rate
		so.submit()
		so_name = so.name
	else:
		discounted_rate = frappe.db.get_value("Sales Order Item", {"parent": so_name}, "rate")

	rx06_confirmed = discounted_rate and discounted_rate < 1500
	if not rx06_confirmed:
		frappe.throw(f"RX06 FAILED: Pricing Rule discount did not apply — rate was {discounted_rate}, expected < 1500.")
	return f"seed_pharmacy_promotion: Pricing Rule {'created' if rule_created else 'already existed'}. RX06 CONFIRMED — discounted rate {discounted_rate} (from 1500)."


def seed_pharmacy_dashboard():
	"""DP-656 — RX07, central dashboard. Just confirms the aggregate query resolves real data
	across all stores — no seed action of its own."""
	from enterprise_core.enterprise_core.api import get_pharmacy_central_dashboard

	dashboard = get_pharmacy_central_dashboard()
	if not dashboard.get("stock_by_warehouse"):
		frappe.throw("RX07 FAILED: central dashboard returned no stock data.")
	return f"seed_pharmacy_dashboard: RX07 CONFIRMED — {len(dashboard['stock_by_warehouse'])} warehouse row(s), total sales {dashboard.get('total_sales_amount')}."


# ---------------------------------------------------------------------------
# Catalog expansion (P2 post-launch reviewer fix, NOT a master-plan DP item) — this golden
# demo sold exactly ONE OTC product (PARA-500-TAB, reused from Golden Demo #1), which a
# reviewer correctly flagged as making WEB-06 (pharmacy.pharmacountry.vn) look too thin to be
# a real pharmacy. Adds 7 new real OTC items (a genuine pharmacy retail range — pain relief,
# antihistamine, cough/cold, antacid, pediatric, rehydration, topical antifungal), each with
# real stock received directly into Store A (the SAME warehouse WEB-06's own `_safe_item_codes()`
# scopes to) and a real selling Item Price on the public "Standard Selling" price list (the
# SAME price list Store A's own POS Profile already sells from) — plus real Store A stock for
# 2 EXISTING real items from other golden demos (VITC-1000-EFF, MULTIVIT-COMP-TAB — a pharmacy
# plausibly stocks general vitamins too), reusing their ALREADY-real Item Price rather than
# creating a duplicate. Every batch gets a real, explicitly-set, comfortably non-expired
# expiry_date via `frappe.db.set_value()` AFTER Stock Entry submission — never just the row's
# own `expiry_date` field, which Golden Demo #24 (3PL) found ERPNext's own auto-batch-creation
# path silently ignores (confirmed live: this exact bug was latent in this file's own
# `_ensure_central_stock()`/`_test_rx03_expired_batch_blocked()` from the start, just never
# surfaced because neither needed a SPECIFIC value, only "some future date" — Item.shelf_life_in_days
# happened to cover for it). Deliberately isolated: never touches PARA-500-TAB, Store B, Central
# Warehouse, or the RX03-EXPIRED-TEST marker batch this golden demo's own RX03 test depends on.
# ---------------------------------------------------------------------------

_NEW_OTC_ITEMS = {
	# item_code: (item_name, shelf_life_days, receive_qty, receive_basic_rate, sell_price)
	"IBUPROFEN-400-TAB": ("Ibuprofen 400mg Tablet", 1095, 400, 1000, 2000),
	"LORATADINE-10-TAB": ("Loratadine 10mg Tablet (Antihistamine)", 1095, 300, 1200, 2500),
	"COUGH-SYRUP-100ML": ("Herbal Cough Syrup 100ml", 730, 150, 25000, 45000),
	"ANTACID-CHEW-TAB": ("Antacid Chewable Tablet", 1095, 500, 900, 1800),
	"PARACETAMOL-SYRUP-KIDS": ("Paracetamol Pediatric Syrup 120mg/5ml", 730, 120, 20000, 38000),
	"ORS-SACHET": ("Oral Rehydration Salts Sachet", 1095, 600, 2500, 5000),
	"ANTIFUNGAL-CREAM-15G": ("Antifungal Cream 15g Tube", 730, 100, 22000, 42000),
}

# Existing real Items from other golden demos this pharmacy plausibly also stocks — reuses
# their ALREADY-real Item Price on Standard Selling (set by supplement_seeds.py /
# consumer_dist_seeds.py's own catalog-expansion steps) rather than creating a duplicate row.
_REUSED_ITEMS_TO_STOCK = {
	"VITC-1000-EFF": (20, 150000),
	"MULTIVIT-COMP-TAB": (40, 140000),
}

_EXPIRY_BUFFER_DAYS = 60  # comfortably inside shelf_life_in_days, well clear of "today" either way


def _ensure_otc_item(item_code, item_name, shelf_life_days):
	if frappe.db.exists("Item", item_code):
		return False
	if not frappe.db.exists("Item Group", "Finished Goods"):
		frappe.get_doc({"doctype": "Item Group", "item_group_name": "Finished Goods", "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name,
			"item_group": "Finished Goods",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"has_batch_no": 1,
			"create_new_batch": 1,
			"has_expiry_date": 1,
			"shelf_life_in_days": shelf_life_days,
		}
	).insert(ignore_permissions=True)
	return True


def _receive_with_real_expiry(item_code, qty, basic_rate, shelf_life_days):
	"""Receives real stock into Store A and then EXPLICITLY sets the resulting Batch's
	expiry_date via frappe.db.set_value() — the Golden Demo #24 (3PL) lesson: a Stock Entry
	Detail row's own `expiry_date` field is silently ignored by ERPNext's auto-batch-creation
	path (`Item.create_new_batch=1`), which only ever computes
	manufacturing_date + shelf_life_in_days on its own. Setting it directly, after submission,
	once the real batch_no is known, guarantees a real, comfortably non-expired date rather
	than trusting that side effect to happen to land right."""
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
	se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _STORE_A_WH, "basic_rate": basic_rate})
	se.insert(ignore_permissions=True)
	se.submit()
	batch_no = frappe.db.get_value("Stock Entry Detail", {"parent": se.name, "item_code": item_code}, "batch_no")
	if not batch_no:
		bundle = frappe.db.get_value("Stock Entry Detail", {"parent": se.name, "item_code": item_code}, "serial_and_batch_bundle")
		batch_no = frappe.db.get_value("Serial and Batch Entry", {"parent": bundle}, "batch_no") if bundle else None
	if batch_no:
		expiry_date = frappe.utils.add_days(frappe.utils.nowdate(), max(shelf_life_days - _EXPIRY_BUFFER_DAYS, 30))
		frappe.db.set_value("Batch", batch_no, "expiry_date", expiry_date)
	return batch_no


def seed_pharmacy_catalog_expansion():
	"""P2 catalog-widening fix (post-launch reviewer feedback, not a master-plan DP item) — 7
	new real OTC Items + real Store A stock + real Item Price on Standard Selling, plus real
	Store A stock for 2 existing real items reused from other golden demos. Widens WEB-06's
	catalog from 1 product to 10, isolated from PARA-500-TAB/Store B/RX03-EXPIRED-TEST. See the
	module-level comment above this section for the full design rationale."""
	if not frappe.db.exists("Warehouse", _STORE_A_WH):
		return "seed_pharmacy_catalog_expansion: SKIPPED — run seed_pharmacy_master_data first."

	items_created = 0
	receipts_created = 0
	prices_created = 0
	for item_code, (item_name, shelf_life_days, qty, basic_rate, sell_price) in _NEW_OTC_ITEMS.items():
		if _ensure_otc_item(item_code, item_name, shelf_life_days):
			items_created += 1
		if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _STORE_A_WH, "item_code": item_code}):
			_receive_with_real_expiry(item_code, qty, basic_rate, shelf_life_days)
			receipts_created += 1
		existing_price = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": "Standard Selling", "selling": 1}, "name")
		if not existing_price:
			frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Selling", "selling": 1, "price_list_rate": sell_price, "currency": "VND"}).insert(ignore_permissions=True)
			prices_created += 1

	reused_receipts = 0
	for item_code, (qty, basic_rate) in _REUSED_ITEMS_TO_STOCK.items():
		if not frappe.db.exists("Item", item_code):
			continue  # SKIPPED — run that item's own catalog-expansion seed on this site first.
		if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _STORE_A_WH, "item_code": item_code}):
			shelf_life = frappe.db.get_value("Item", item_code, "shelf_life_in_days") or 730
			_receive_with_real_expiry(item_code, qty, basic_rate, shelf_life)
			reused_receipts += 1

	return (
		f"seed_pharmacy_catalog_expansion: {items_created} new OTC Item(s), {receipts_created} new Store A receipt(s), "
		f"{prices_created} new Item Price row(s), {reused_receipts} reused-item Store A receipt(s)."
	)
