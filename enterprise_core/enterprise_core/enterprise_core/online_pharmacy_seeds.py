"""WEB-06 — Online Pharmacy (Phase 7, master plan §8 lines ~2572-2573: "WEB-06 Online Pharmacy —
Frontend riêng, tích hợp pharmacy ERP."). Seed/infra module for the ONE-TIME, idempotent setup this
guest-writable storefront needs before `online_pharmacy_api.py` can accept a real order: an isolated
POS Profile, an isolated top-up stock batch, an isolated guest Customer, and an open POS Opening
Entry. Backs the standalone Next.js app in `nextjs-demo/web-06-online-pharmacy/`.

WHY A SEPARATE SEEDS MODULE — NOT INLINE IN `online_pharmacy_api.py` (same split as WEB-03/WEB-04's
own `dealer_portal_seeds.py`/`supplier_portal_seeds.py`, unlike WEB-05 which needed none):
  WEB-05's guest checkout only ever had to create a `Customer` + `Address` + `Sales Order` inline,
  per request — `Customer.insert(ignore_permissions=True)` alone was safe there (no nested
  permission-check surprise). WEB-06 reuses Golden Demo #23 (Pharmacy Chain)'s real POS Invoice
  mechanism instead (see `online_pharmacy_api.py`'s own docstring for why a POS Invoice, not a Sales
  Order, is the only way to genuinely re-prove the native expiry-block mechanism), and a POS Invoice
  has real INFRASTRUCTURE prerequisites a guest request must never be trusted to create for itself:
  a POS Profile and an open POS Opening Entry. Those are one-time, admin-run setup steps — run via
  `bench execute` (as this file's own functions, never `allow_guest`), exactly like every golden
  demo's own `*_seeds.py` — not something `place_pharmacy_order` creates on the fly under guest
  elevation.

WHY A DEDICATED "Online Pharmacy Store A POS" POS PROFILE — NOT GOLDEN DEMO #23's OWN "Pharmacy
Store A POS":
  A REAL bug class this session has hit repeatedly (Pharmacy's own DP-650 inter-store-transfer bug,
  3PL's DP-663 reconciliation bug) is an idempotency/lookup guard that resolves the WRONG document
  because it isn't scoped tightly enough. Golden Demo #23's own `verify_pharmacy_golden_demo()` (RX05
  check) does exactly this: `frappe.db.get_value("POS Invoice", {"pos_profile": "Pharmacy Store A
  POS", "is_return": 0, "docstatus": 1}, "name")` with NO ordering — it resolves to WHICHEVER
  matching POS Invoice happens to sort first. If WEB-06's online orders posted through that SAME POS
  Profile, this query could non-deterministically resolve to one of WEB-06's own online orders
  instead of Golden Demo #23's own original seeded sale, and RX05's own "a return exists against
  THIS sale" check would then fail — a real, avoidable cross-demo corruption of exactly the kind this
  session has been warned about repeatedly. Fix: WEB-06 posts through its OWN POS Profile,
  "Online Pharmacy Store A POS" — same real Company, same real Store A warehouse (the online
  storefront's real per-store stock and the in-store POS's real per-store stock are the SAME real
  `Bin.actual_qty` at the same real warehouse; only the POS Profile/document trail is separated) —
  so no query scoped to "Pharmacy Store A POS" can ever match a WEB-06 order, and no query scoped to
  "Online Pharmacy Store A POS" can ever match a Golden-Demo-#23 in-store sale.

WHY AN ISOLATED TOP-UP STOCK BATCH, NOT JUST GOLDEN DEMO #23's OWN 120 REAL UNITS AT STORE A:
  Store A's real, live stock (`Bin.actual_qty` = 130, of which 120 sits in Golden Demo #23's own
  real, non-expired batch `60FE50C` (expiry 2028-09-27) and 10 sits in the deliberately-expired RX03
  test batch — confirmed live via direct query before writing this module) is real, presentable per-
  store stock, and WEB-06's catalog is honestly built to READ it directly. But `place_pharmacy_order`
  creates a REAL, STOCK-DEDUCTING POS Invoice on every call, and this build's own verification
  workflow places many real test orders (and is required to re-run its own access-control proof
  multiple times to check for idempotency corruption) — repeatedly depleting Golden Demo #23's own
  120-unit flagship batch down towards zero would be exactly the "mutate Golden Demo #23's own
  flagship stock" mistake this build was explicitly warned against. Fix: `_ensure_online_fulfillment_
  stock()` receives an ADDITIONAL 1,000 real units into the SAME real Store A warehouse, under a NEW,
  separately-named batch (`WEB06-ONLINE-STOCK`) with a real expiry date of 2027-06-30 — chosen
  DELIBERATELY EARLIER than the golden demo's own batch's 2028-09-27 expiry (but still safely in the
  future) so that native FEFO batch-picking (`online_pharmacy_api._pick_batches_fefo()`, earliest-
  expiry-first, the same FEFO discipline every batch-tracked golden demo in this platform already
  uses) always drains THIS isolated batch before ever touching Golden Demo #23's own 120 units. This
  is still 100% real ERPNext stock at the real storefront's real warehouse (the catalog's displayed
  "in stock" figure is deliberately the honest SUM of both batches, not just the top-up) — it is
  isolated for WRITE-side idempotency safety, not hidden from the READ-side honesty this build was
  also asked to preserve.

  REAL BUG PROACTIVELY AVOIDED, NOT REDISCOVERED (documented in Golden Demo #24 (3PL)'s own DP-659
  entry in project_status.md): `Stock Entry Detail.expiry_date` is a real field, but ERPNext's own
  auto-batch-creation path (`Item.create_new_batch=1`, `serial_and_batch_bundle.py`'s `create_batch()`
  -> `make_batch()`) never reads it — it only ever computes `manufacturing_date + shelf_life_in_days`.
  Applying that lesson here directly: after submitting the top-up Stock Entry, this module reads back
  the REAL auto-created batch name and sets `Batch.expiry_date` directly via `frappe.db.set_value()`,
  exactly like DP-659's own fix — never trusting the row-level `expiry_date` kwarg to have taken
  effect.

ISOLATED GUEST CUSTOMER — "Pharmacy Online Guest (WEB-06 Online Orders)", same naming/isolation
  discipline as WEB-05's "Web Store Guest (WEB-05 Online Orders)": one shared Customer record reused
  across every guest checkout, never Golden Demo #23's own "Pharmacy Walk-in Customer" (that
  Customer's own real POS Invoices are what RX03/RX05's checks are scoped around).
"""

import frappe

_COMPANY_NAME = "Demo Pharmacy Chain Co."
_COMPANY_ABBR = "DPH"
_STORE_WAREHOUSE = f"Store A - {_COMPANY_ABBR}"
_ITEM = "PARA-500-TAB"

_ONLINE_POS_PROFILE = "Online Pharmacy Store A POS"
_ONLINE_GUEST_CUSTOMER = "Pharmacy Online Guest (WEB-06 Online Orders)"

# Deliberately earlier than Golden Demo #23's own real batch's 2028-09-27 expiry (see module
# docstring) so native FEFO always drains this isolated top-up batch first.
_TOPUP_BATCH_NAME = "WEB06-ONLINE-STOCK"
_TOPUP_BATCH_EXPIRY = "2027-06-30"
_TOPUP_QTY = 1000
_TOPUP_RATE = 800  # same basic_rate Golden Demo #23's own _ensure_central_stock() used
_TOPUP_MARKER = "WEB-06 Online Pharmacy fulfillment stock top-up"

# A dedicated, never-logged-into technical "cashier" identity for the online POS Opening Entry's own
# `user` field. REAL bug found+fixed while building this: ERPNext's own `POS Opening Entry.check_
# user_already_assigned()` throws "Cashier is currently assigned to another POS" if the SAME user is
# already the `user` on any OTHER open POS Opening Entry, filtered by user alone (confirmed by reading
# `pos_opening_entry.py` directly) — `frappe.session.user` (Administrator, when this seed runs via
# `bench execute`) is already the cashier on Golden Demo #23's own "Pharmacy Store A POS" opening
# entry, so reusing it here was rejected outright. Fixed with its own dedicated User, same "service
# account, not ambient privilege" discipline as every other isolation choice in this module — never
# given a real password/portal login, only ever referenced by name in this one field.
_ONLINE_POS_CASHIER_USER = "online.pharmacy.pos@pharmacountry.vn"


def _ensure_online_pos_profile():
	"""Isolated POS Profile for the online storefront — same real Company/warehouse/price list as
	Golden Demo #23's own "Pharmacy Store A POS", but a SEPARATE document trail (see module
	docstring for why sharing the golden demo's own profile is unsafe)."""
	if frappe.db.exists("POS Profile", _ONLINE_POS_PROFILE):
		return False
	frappe.get_doc(
		{
			"doctype": "POS Profile",
			"name": _ONLINE_POS_PROFILE,
			"company": _COMPANY_NAME,
			"warehouse": _STORE_WAREHOUSE,
			"currency": "VND",
			"selling_price_list": "Standard Selling",
			"write_off_account": f"Write Off - {_COMPANY_ABBR}",
			"write_off_cost_center": f"Main - {_COMPANY_ABBR}",
			"write_off_limit": 1,
			"payments": [{"mode_of_payment": "Cash", "default": 1}],
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_online_guest_customer():
	"""The ONE shared Customer every WEB-06 guest checkout is created against — see module
	docstring. Created once, idempotently, exactly like WEB-05's own `_ensure_web_guest_customer()`."""
	if frappe.db.exists("Customer", {"customer_name": _ONLINE_GUEST_CUSTOMER}):
		return False
	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": _ONLINE_GUEST_CUSTOMER,
			"customer_type": "Individual",
			"default_price_list": "Standard Selling",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_online_fulfillment_stock():
	"""Isolated 1,000-unit top-up batch at the SAME real Store A warehouse — see module docstring
	for why this exists (protecting Golden Demo #23's own 120-unit flagship batch from repeated
	verification-time depletion) and for the DP-659 auto-batch-expiry bug this proactively avoids."""
	if frappe.db.exists("Batch", _TOPUP_BATCH_NAME):
		return False
	if frappe.db.exists("Stock Entry", {"remarks": _TOPUP_MARKER, "docstatus": 1}):
		return False

	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": _COMPANY_NAME,
			"remarks": _TOPUP_MARKER,
		}
	)
	se.append(
		"items",
		{"item_code": _ITEM, "qty": _TOPUP_QTY, "t_warehouse": _STORE_WAREHOUSE, "basic_rate": _TOPUP_RATE, "expiry_date": _TOPUP_BATCH_EXPIRY},
	)
	se.insert(ignore_permissions=True)
	se.submit()
	# `se.items[0].serial_and_batch_bundle` is NOT populated on the in-memory object immediately
	# after `submit()` — confirmed empirically (a real bug hit while building this: the field read
	# back as the bundle name from BEFORE submission's own batch-creation step, giving a bundle with
	# no rows yet). A `reload()` is required to see the real, final linkage.
	se.reload()

	# The row-level expiry_date kwarg above is silently ignored by ERPNext's own auto-batch-creation
	# path (DP-659's own finding, applied here proactively) — the REAL batch's expiry must be set
	# directly, after the fact, once the real batch_no is known.
	new_batch = frappe.db.get_value(
		"Serial and Batch Entry", {"parent": se.items[0].serial_and_batch_bundle}, "batch_no"
	)
	if not new_batch:
		frappe.throw("WEB-06 setup FAILED: top-up Stock Entry did not create a real batch.")
	frappe.db.set_value("Batch", new_batch, "expiry_date", _TOPUP_BATCH_EXPIRY)
	if new_batch != _TOPUP_BATCH_NAME:
		frappe.rename_doc("Batch", new_batch, _TOPUP_BATCH_NAME, force=True)
	return True


def _ensure_online_pos_cashier_user():
	"""See `_ONLINE_POS_CASHIER_USER`'s own definition comment for why this dedicated, never-
	logged-into User exists — a real "Cashier is currently assigned to another POS" conflict with
	Golden Demo #23's own Administrator-owned POS session was found and fixed this way."""
	if frappe.db.exists("User", _ONLINE_POS_CASHIER_USER):
		return False
	frappe.get_doc(
		{
			"doctype": "User",
			"email": _ONLINE_POS_CASHIER_USER,
			"first_name": "WEB-06 Online Pharmacy",
			"send_welcome_email": 0,
			"enabled": 1,
			"user_type": "System User",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_online_pos_opening():
	"""An open POS Opening Entry for the isolated online POS Profile — required by POS Invoice's
	own server-side `validate_pos_opening_entry()` (filters only by pos_profile + status=Open, not
	by user — confirmed by reading `sales_invoice.py` directly before writing this) before any real
	sale can be recorded against it. Uses the dedicated `_ONLINE_POS_CASHIER_USER`, not `frappe.
	session.user` — see that constant's own comment for the real conflict this avoids.

	Real, previously-latent bug found (and fixed here) by the mandatory full regression sweep
	re-run on a LATER calendar day than this entry was first opened: ERPNext's own
	`validate_pos_opening_entry()` additionally requires `period_start_date` to equal
	`frappe.utils.today()` exactly — an Open entry from a PRIOR day is still `status="Open"`
	(ERPNext never auto-closes it) but is rejected by that same-day check on the very next real
	sale, with "POS Opening Entry ... is outdated. Please close the POS and create a new POS
	Opening Entry." The old guard here only checked `status == "Open"`, never staleness — exactly
	the same idempotency-guard class of bug this session's lessons warn about elsewhere (a guard
	that was correct once but stops being a correct proxy for "no action needed" as real time
	passes). Fixed by also checking the entry is genuinely from TODAY, and closing (not deleting —
	it's real submitted history) a stale one before opening a fresh one."""
	existing = frappe.db.get_value("POS Opening Entry", {"pos_profile": _ONLINE_POS_PROFILE, "status": "Open"}, ["name", "period_start_date"], as_dict=True)
	if existing:
		if frappe.utils.get_date_str(existing.period_start_date) == frappe.utils.today():
			return False
		frappe.get_doc("POS Opening Entry", existing.name).db_set("status", "Closed")
	entry = frappe.get_doc(
		{
			"doctype": "POS Opening Entry",
			"period_start_date": frappe.utils.now_datetime(),
			"posting_date": frappe.utils.nowdate(),
			"company": _COMPANY_NAME,
			"pos_profile": _ONLINE_POS_PROFILE,
			"user": _ONLINE_POS_CASHIER_USER,
			"balance_details": [{"mode_of_payment": "Cash", "opening_amount": 500000}],
		}
	)
	entry.insert(ignore_permissions=True)
	entry.submit()
	return True


def seed_online_pharmacy_setup():
	"""WEB-06 one-time infra setup — run via `bench execute` (Administrator), never guest-reachable.
	Idempotent: safe to re-run on every deploy/regression sweep. Order matters: the POS Profile must
	exist before the POS Opening Entry can reference it."""
	if not frappe.db.exists("Warehouse", _STORE_WAREHOUSE):
		return "seed_online_pharmacy_setup: SKIPPED — Golden Demo #23 (seed_pharmacy_master_data) has not run yet."
	profile_created = _ensure_online_pos_profile()
	customer_created = _ensure_online_guest_customer()
	stock_topped_up = _ensure_online_fulfillment_stock()
	cashier_created = _ensure_online_pos_cashier_user()
	opening_created = _ensure_online_pos_opening()
	return (
		f"seed_online_pharmacy_setup: POS Profile {'created' if profile_created else 'already existed'}. "
		f"Guest Customer {'created' if customer_created else 'already existed'}. "
		f"Fulfillment top-up stock {'received (' + str(_TOPUP_QTY) + ' units, batch ' + _TOPUP_BATCH_NAME + ')' if stock_topped_up else 'already present'}. "
		f"Cashier service user {'created' if cashier_created else 'already existed'}. "
		f"POS Opening Entry {'opened' if opening_created else 'already open'}."
	)
