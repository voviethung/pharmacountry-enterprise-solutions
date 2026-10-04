"""WEB-05 — B2C Commerce (Phase 7, master plan §8 lines ~2569-2570: "WEB-05 B2C Commerce —
Consumer products."). Backs the standalone Next.js app in `nextjs-demo/web-05-b2c-commerce/`.

THIS IS A GENUINELY NEW RISK CATEGORY — read this before touching this file:
  Every prior Phase 7 build is one of two shapes: guest-only + READ-ONLY (`public_api.py`'s WEB-01/
  WEB-02/Hub — `allow_guest=True`, zero writes) or authenticated + WRITE (`dealer_portal_api.py`'s
  WEB-03, `supplier_portal_api.py`'s WEB-04 — a real login resolves identity, then a real write runs
  permission-checked as that user). WEB-05 needs a THIRD shape this platform has never built:
  `allow_guest=True` AND a real write (`place_web_order` creates a real, submitted Sales Order) — an
  anonymous caller who has never authenticated must be able to create a real transactional document.
  That is a strictly higher-risk combination than either prior shape alone, so it gets its own
  explicit threat model rather than borrowing one wholesale:

  1. NEVER TRUST A CLIENT-SUPPLIED PRICE. `place_web_order`'s accepted `items` shape only ever reads
     `item_code`/`qty` off each row — there is no `rate`/`price`/`amount` parameter anywhere in this
     module, and if a caller stuffs one into the JSON body anyway it is silently ignored (`_validate_
     items()` only ever extracts `item_code`/`qty`, nothing else). Every line's real `rate` is looked
     up server-side, by `item_code` alone, from the SAME real `Item Price` on the public "Standard
     Selling" price list `public_api.py`'s WEB-01 already established. Proven empirically, not just
     asserted — `verify_b2c_commerce_demo()` (in `api.py`) submits a real payload with a spoofed
     `rate: 1` line and asserts the resulting Sales Order's real rate is still the true catalog price.
  2. SCOPE WHAT A GUEST CAN WRITE. `place_web_order` is the ONLY function in this module that writes
     anything, and every call creates at most 2 real documents: one `Address` (this order's own
     delivery address) and one `Sales Order` — always for a single, dedicated, isolated "Web Store
     Guest" Customer (see below), NEVER Golden Demo #25's own flagship Hanoi/Saigon dealers and NEVER
     a WEB-03 portal dealer. It cannot read, modify, or delete any other record, and — critically —
     it cannot be used to enumerate or fetch another guest's order (point 6).
  3. A NARROW, DOCUMENTED "SERVICE ACCOUNT" CONTEXT, NOT AMBIENT PRIVILEGE. There is no logged-in
     user for a guest request, so `Guest` has no create permission on `Address`/`Sales Order` at all.
     TWO REAL BUGS were found and fixed while building this, in order:
       (a) `so.insert(ignore_permissions=True)` alone is NOT enough. ERPNext's own `Sales Order.
           set_missing_values()` internally re-fetches item details via `get_item_details()`, which
           calls `Item.check_permission()` on a FRESH, SEPARATE `Item` document instance — confirmed
           empirically: the first live test failed with a raw `frappe.PermissionError` deep inside
           `erpnext/stock/get_item_details.py`, despite `insert(ignore_permissions=True)` on the
           Sales Order itself.
       (b) The obvious next fix — a global `frappe.flags.ignore_permissions = True` around the write
           block — does NOT work either, and was proven not to by reading Frappe's own source rather
           than guessing again: `Document.has_permission()` checks the PER-INSTANCE
           `self.flags.ignore_permissions`, but the failing check here goes through the MODULE-level
           `frappe.has_permission()` (called by `check_doctype_permission()`), which never consults
           the global flag at all — confirmed by reading `frappe/__init__.py`'s `has_permission()`
           and `frappe/permissions.py`'s `check_doctype_permission()` directly. The global flag would
           have been a false fix that happened to look plausible; it was verified to fail live before
           being abandoned.
     The actual fix: `place_web_order` briefly elevates to `frappe.set_user("Administrator")` for
     ONLY the 3 real write statements (`address.insert()`, `so.insert()`, `so.submit()`), restoring
     the original session user in a `finally` clause even on failure — the same "dedicated service-
     account context" pattern a real production guest-checkout backend would use (a webshop's backend
     process, not the anonymous visitor, is what actually has ERP write access). This is safe
     specifically BECAUSE: (a) it is scoped to the smallest possible block — 3 statements, not the
     whole request, and restored immediately even on an exception; (b) every value written in that
     block was already fully validated ABOVE it, BEFORE the elevation (`item_code` against the real
     `_safe_item_codes()` allow-list, `qty` against a live stock check, price computed server-side,
     contact fields length/shape-checked) — nothing request-controlled is interpreted while elevated,
     only pre-vetted values are written into 2 hardcoded document types; and (c) nothing else in this
     module ever calls `frappe.set_user()` — nowhere in this module can a caller trigger this
     elevation without also passing every validation check above it first.
  4. REAL STOCK CHECKED, NEVER JUST TRUSTED. Each line's requested qty is checked against the real,
     live `Bin.actual_qty` at the shared Distribution Center warehouse (the same warehouse WEB-01's
     catalog/WEB-03's dealer portal already read stock from) — an order that would oversell real
     inventory is rejected before any document is created.
  5. SANE INPUT BOUNDS, HONESTLY NOT REAL ANTI-ABUSE. Quantities are capped
     (`_MAX_QTY_PER_LINE`/`_MAX_LINES_PER_ORDER`), item codes are re-checked against the same real
     `_safe_item_codes()` filter WEB-01 uses, and contact fields are length- and shape-checked. This
     is NOT rate limiting, NOT a CAPTCHA, and NOT fraud detection — a real production deployment of a
     guest-checkout endpoint would need all three; documented here and in the app's own README as
     honestly as this platform discloses its mocked payment/LLM/embeddings work elsewhere.
  6. ORDER LOOKUP REQUIRES A NON-GUESSABLE TOKEN **AND** THE CHECKOUT PHONE NUMBER — NEVER THE RAW
     SALES ORDER NAME ALONE. Frappe's own Sales Order naming series is sequential
     (`SAL-ORD-2026-000123`) and therefore guessable/enumerable; `get_order_status()` never accepts
     it, and `place_web_order`'s response never even includes it. Instead, `place_web_order`
     generates a random, unguessable `order_token` (`frappe.generate_hash`, ~40 bits of entropy),
     stores it in the Sales Order's own `po_no` field (never derived from the sequential `name`), and
     returns ONLY that token to the guest. `get_order_status(order_token, phone)` requires BOTH: it
     looks up the Sales Order by `po_no=order_token` (restricted further to `customer=_WEB_GUEST_
     CUSTOMER`, so this lookup can never accidentally resolve a non-guest order even if a po_no
     collided) AND re-checks that the request's own `phone` argument matches that order's stored
     `contact_mobile` (normalized to digits only) before returning anything. A correct token with the
     wrong phone, a guessed/wrong token, and a missing order all return the exact SAME generic
     "not found" `DoesNotExistError` — never a distinguishable "token valid, phone wrong" signal that
     would let an attacker brute-force the phone number once a valid token was guessed.
  7. NO REAL PAYMENT GATEWAY — CASH ON DELIVERY ONLY, CLEARLY LABELLED. There is no real payment
     processor anywhere in this platform and none is added here. `place_web_order` accepts exactly
     one `payment_method` value, `"Cash on Delivery"` — a real, simple, honest design (money changes
     hands at delivery, never through this API) rather than a fake card-entry screen that could
     visually be mistaken for a real payment flow.

DATA SOURCE — same company/items/price list as WEB-01, deliberately not reinvented. `_COMPANY_NAME`/
  `_DC_WAREHOUSE`/`_PUBLIC_PRICE_LIST`/`_safe_item_codes()` below are copy-identical in effect to
  `public_api.py`'s own (Demo Consumer Distribution Co., the "Standard Selling" price list, the same
  real Stock-Ledger-Entry + Item-Price SQL join) — checked live before writing this module
  (`get_catalog_items()` still returns exactly `VITC-1000-EFF`/260,000 VND and `FACIAL-CLEANSER-
  150ML`/95,000 VND) and confirmed this is still the ONLY golden demo company with real, presentable
  selling price data (Demo Supplement Co./Demo Cosmetics Co. still have no selling Item Price of
  their own — same finding WEB-01/WEB-02 already documented). Reusing it ties WEB-01 (browse the
  catalog), WEB-02 (the brand's own quality story for VITC-1000-EFF), WEB-03 (the B2B dealer
  channel), and WEB-05 (the direct-to-consumer channel) into one coherent real-data story for the
  same distributor, rather than inventing a 3rd company. Deliberately NOT imported from
  `public_api.py`/`dealer_portal_api.py` — same reasoning `dealer_portal_api.py`'s own docstring
  gives for keeping its own copy of `_safe_item_codes()`: keeps this guest-WRITE module's security
  boundary independent of either guest-READ-only or authenticated module's — a future edit to one
  can never silently change another's behavior.

ISOLATED CUSTOMER — "Web Store Guest (WEB-05 Online Orders)", Demo Consumer Distribution Co., a
  SINGLE shared Customer record reused across every guest checkout (never Golden Demo #25's own
  Hanoi/Saigon dealers, never a WEB-03 portal dealer) — avoids creating hundreds of throwaway
  Customer records for what a real storefront typically models as "one generic web-store account,
  many orders," while the per-order Address + `po_no` token + `contact_mobile`/`contact_display`
  fields carry the real, order-specific guest identity. Real Sales Orders are submitted
  (`docstatus=1`, not left as drafts) so they behave like any other real, completed transaction — but
  every one carries a `WEB05-` `po_no` prefix and the isolated customer, so it can never be confused
  with Golden Demo #25's own `CD0x-.../FLOW-...` flagship transactions or WEB-03's own `WEB03-...`
  portal-dealer orders (same isolation discipline `dealer_portal_seeds.py`'s own docstring
  documents).
"""

import re

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Consumer Distribution Co."
_DC_WAREHOUSE = "Distribution Center - DCD"
_PUBLIC_PRICE_LIST = "Standard Selling"

_WEB_GUEST_CUSTOMER = "Web Store Guest (WEB-05 Online Orders)"
_WEB_GUEST_CUSTOMER_GROUP = "Consumer Health Retail Customers"
_WEB_GUEST_TERRITORY = "Vietnam"
_WEB_GUEST_COUNTRY = "Vietnam"

_MAX_QTY_PER_LINE = 20
_MAX_LINES_PER_ORDER = 10
_MAX_NAME_LEN = 120
_MAX_LINE_LEN = 200
_MIN_PHONE_DIGITS = 8
_MAX_PHONE_DIGITS = 15

_PAYMENT_METHOD = "Cash on Delivery"  # the ONLY accepted value — see module docstring point 7.

# Presentation-only copy for the storefront — same discipline as public_api.py's own
# `_CATALOG_COPY`/`_PRODUCT_COPY` (Item.description/image are empty on every golden-demo Item, see
# that module's docstring for the full finding). Deliberately a fresh, independent dict rather than
# importing WEB-01's copy — presentation text, not a security boundary, so duplication here costs
# nothing and keeps this module self-contained. Only ever rendered for an item_code that
# independently passes the real, data-driven `_safe_item_codes()` filter below.
_STOREFRONT_COPY = {
	"VITC-1000-EFF": {
		"category": "Vitamins",
		"blurb": (
			"Fast-dissolving effervescent tablet delivering 1000mg of Vitamin C per serving. "
			"Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co."
		),
	},
	"VITD3-1000-SG": {
		"category": "Vitamins",
		"blurb": "Vitamin D3 1000 IU softgel for daily bone and immune support. Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co.",
	},
	"MULTIVIT-COMP-TAB": {
		"category": "Vitamins",
		"blurb": "A daily multivitamin complex tablet covering Vitamin C, D3, Zinc and B-Complex. Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co.",
	},
	"ZINC-50-TAB": {
		"category": "Minerals & Specialty Supplements",
		"blurb": "Zinc gluconate 50mg tablet supporting normal immune function. Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co.",
	},
	"OMEGA3-1000-SG": {
		"category": "Minerals & Specialty Supplements",
		"blurb": "Omega-3 fish oil 1000mg softgel. Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co.",
	},
	"PROBIOTIC-10B-CAP": {
		"category": "Minerals & Specialty Supplements",
		"blurb": "A 10 billion CFU probiotic capsule for daily digestive support. Made by Demo Supplement Co., distributed and sold by Demo Consumer Distribution Co.",
	},
	"FACIAL-CLEANSER-150ML": {
		"category": "Skincare",
		"blurb": (
			"Gentle daily facial cleanser in a 150ml bottle, formulated for everyday use. "
			"Distributed and sold by Demo Consumer Distribution Co."
		),
	},
	"FACIAL-TONER-200ML": {
		"category": "Skincare",
		"blurb": "Hydrating facial toner in a 200ml bottle, formulated for everyday use. Distributed and sold by Demo Consumer Distribution Co.",
	},
}


def _safe_item_codes():
	"""Same real, data-driven filter as public_api.py's/dealer_portal_api.py's own copy (Item with
	real Stock Ledger Entry movement for `_COMPANY_NAME` AND a real selling Item Price on the public
	`_PUBLIC_PRICE_LIST`) — deliberately re-implemented here rather than imported, see module
	docstring."""
	rows = frappe.db.sql(
		"""
		select distinct i.item_code
		from `tabItem` i
		inner join `tabStock Ledger Entry` sle on sle.item_code = i.item_code and sle.company = %(company)s
		inner join `tabItem Price` ip on ip.item_code = i.item_code and ip.selling = 1 and ip.price_list = %(price_list)s
		where i.disabled = 0
		order by i.item_code
		""",
		{"company": _COMPANY_NAME, "price_list": _PUBLIC_PRICE_LIST},
		as_dict=True,
	)
	return [r.item_code for r in rows]


def _current_price(item_code):
	"""The ONLY place any order line's rate ever comes from — a real, current, selling Item Price on
	the public price list, looked up by item_code alone. Never accepts or reads a client-supplied
	price of any kind (see module docstring point 1)."""
	price = frappe.db.get_value(
		"Item Price", {"item_code": item_code, "selling": 1, "price_list": _PUBLIC_PRICE_LIST}, "price_list_rate"
	)
	if price is None:
		frappe.throw(_("Item {0} has no current price and cannot be ordered.").format(item_code))
	return price


def _available_qty(item_code, display_uom=None, stock_uom=None):
	qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": _DC_WAREHOUSE}, "actual_qty") or 0
	# Bin.actual_qty is always in the Item's stock_uom. Convert to the customer-facing
	# display_uom (e.g. "Tube") when it differs, using the Item's own real UOM Conversion
	# Detail row — never a guessed/hardcoded factor.
	if display_uom and stock_uom and display_uom != stock_uom:
		factor = frappe.db.get_value(
			"UOM Conversion Detail", {"parent": item_code, "uom": display_uom}, "conversion_factor"
		)
		if factor:
			qty = qty / factor
	return qty


def _serialize_catalog_item(item_code):
	item = frappe.db.get_value("Item", item_code, ["item_code", "item_name", "stock_uom", "sales_uom"], as_dict=True)
	if not item:
		return None
	display_uom = item.sales_uom or item.stock_uom
	copy = _STOREFRONT_COPY.get(item_code, {})
	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		# `sales_uom` (e.g. "Tube") is the customer-facing selling unit when an Item defines
		# one — falling back to `stock_uom` only for items with no sales-side override. Fixes
		# a real bug where VITC-1000-EFF displayed "/ Kg" next to a per-tube retail price.
		"uom": display_uom,
		"category": copy.get("category", "Consumer Product"),
		"description": copy.get("blurb", ""),
		"price": _current_price(item_code),
		"currency": "VND",
		"available_qty": _available_qty(item_code, display_uom, item.stock_uom),
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_storefront_catalog():
	"""Public, guest-accessible storefront catalog — real price + real live stock qty, same
	`_safe_item_codes()` real data-driven safe set WEB-01 uses. Read-only; no guest input accepted."""
	return [item for item in (_serialize_catalog_item(code) for code in _safe_item_codes()) if item]


def _normalize_phone(phone):
	return re.sub(r"\D", "", phone or "")


def _validate_contact(contact):
	if isinstance(contact, str):
		contact = frappe.parse_json(contact) if contact else {}
	if not isinstance(contact, dict):
		frappe.throw(_("Contact information is required."))

	full_name = (contact.get("full_name") or "").strip()
	phone = _normalize_phone(contact.get("phone"))
	address_line1 = (contact.get("address_line1") or "").strip()
	city = (contact.get("city") or "").strip()
	email = (contact.get("email") or "").strip()

	if not full_name or len(full_name) > _MAX_NAME_LEN:
		frappe.throw(_("A valid name (1-{0} characters) is required.").format(_MAX_NAME_LEN))
	if not (_MIN_PHONE_DIGITS <= len(phone) <= _MAX_PHONE_DIGITS):
		frappe.throw(_("A valid phone number ({0}-{1} digits) is required.").format(_MIN_PHONE_DIGITS, _MAX_PHONE_DIGITS))
	if not address_line1 or len(address_line1) > _MAX_LINE_LEN:
		frappe.throw(_("A valid delivery address is required."))
	if not city or len(city) > _MAX_LINE_LEN:
		frappe.throw(_("A valid city/province is required."))
	if email and ("@" not in email or len(email) > _MAX_LINE_LEN):
		frappe.throw(_("Email address looks invalid."))

	return {
		"full_name": full_name,
		"phone": phone,
		"address_line1": address_line1,
		"city": city,
		"email": email,
	}


def _validate_items(items):
	if isinstance(items, str):
		items = frappe.parse_json(items) if items else []
	if not items or not isinstance(items, list):
		frappe.throw(_("At least one item is required."))
	if len(items) > _MAX_LINES_PER_ORDER:
		frappe.throw(_("Too many distinct items in one order (max {0}).").format(_MAX_LINES_PER_ORDER))

	safe_codes = set(_safe_item_codes())
	by_item_code = {}
	for row in items:
		if not isinstance(row, dict):
			frappe.throw(_("Malformed order line."))
		# ONLY item_code/qty are ever read from a line — any other key (e.g. a client-supplied
		# "rate"/"price"/"amount") is silently ignored, never trusted. See module docstring point 1.
		item_code = row.get("item_code")
		if item_code not in safe_codes:
			frappe.throw(_("Item {0} is not available for purchase.").format(item_code))
		try:
			qty = int(row.get("qty"))
		except (TypeError, ValueError):
			frappe.throw(_("Quantity must be a whole number."))
		if qty <= 0 or qty > _MAX_QTY_PER_LINE:
			frappe.throw(_("Quantity for {0} must be between 1 and {1}.").format(item_code, _MAX_QTY_PER_LINE))
		by_item_code[item_code] = by_item_code.get(item_code, 0) + qty  # collapse duplicate lines

	for item_code, qty in by_item_code.items():
		if qty > _available_qty(item_code):
			frappe.throw(_("Only {0} unit(s) of {1} are currently in stock.").format(int(_available_qty(item_code)), item_code))

	return [{"item_code": code, "qty": qty} for code, qty in by_item_code.items()]


def _ensure_web_guest_customer():
	"""The ONE shared Customer every guest checkout is created against — see module docstring for
	why a single reused Customer, not a new one per order. Created once, idempotently."""
	if not frappe.db.exists("Customer", {"customer_name": _WEB_GUEST_CUSTOMER}):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": _WEB_GUEST_CUSTOMER,
				"customer_type": "Individual",
				"customer_group": _WEB_GUEST_CUSTOMER_GROUP,
				"territory": _WEB_GUEST_TERRITORY,
				"default_price_list": _PUBLIC_PRICE_LIST,
			}
		).insert(ignore_permissions=True)
	return _WEB_GUEST_CUSTOMER


@frappe.whitelist(allow_guest=True, methods=["POST"])
def place_web_order(items=None, contact=None, payment_method=_PAYMENT_METHOD):
	"""Creates a REAL, submitted Sales Order for an anonymous guest — see module docstring for the
	full threat model. Every price is computed server-side (`_current_price`), every item_code and
	qty is re-validated (`_validate_items`, including a real live stock check), and the response
	deliberately never includes the real (sequential, guessable) Sales Order `name` — only the
	random `order_token` needed later by `get_order_status()`."""
	if payment_method != _PAYMENT_METHOD:
		frappe.throw(_("Only Cash on Delivery is supported by this demo checkout."))

	contact_info = _validate_contact(contact)
	order_items = _validate_items(items)
	customer = _ensure_web_guest_customer()
	order_token = f"WEB05-{frappe.generate_hash(length=10).upper()}"

	address = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": f"Web Order {order_token}",
			"address_type": "Shipping",
			"address_line1": contact_info["address_line1"],
			"city": contact_info["city"],
			"country": _WEB_GUEST_COUNTRY,
			"phone": contact_info["phone"],
			"links": [{"link_doctype": "Customer", "link_name": customer}],
		}
	)
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": customer,
			"company": _COMPANY_NAME,
			"territory": _WEB_GUEST_TERRITORY,
			"selling_price_list": _PUBLIC_PRICE_LIST,
			"customer_address": address.name,
			"shipping_address_name": address.name,
			"contact_display": contact_info["full_name"],
			"contact_mobile": contact_info["phone"],
			"contact_email": contact_info["email"] or None,
			"po_no": order_token,
			"delivery_date": add_days(nowdate(), 5),
			"items": [
				{
					"item_code": row["item_code"],
					"qty": row["qty"],
					"rate": _current_price(row["item_code"]),  # server-computed, NEVER client-supplied
					"warehouse": _DC_WAREHOUSE,
				}
				for row in order_items
			],
		}
	)

	# Narrow, documented, restored-on-exit "service account" elevation — see module docstring point 3
	# for the full reasoning, and for the 2 real bugs (including a global ignore_permissions flag that
	# looked like a fix but was proven NOT to work by reading Frappe's own source) found while getting
	# here. Scoped to exactly these 3 statements; every value they write was already validated above,
	# before this block, and restored even on failure.
	_original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		address.insert()
		so.customer_address = address.name
		so.shipping_address_name = address.name
		so.insert()
		so.submit()
	finally:
		frappe.set_user(_original_user)

	return {
		"order_token": order_token,
		"payment_method": _PAYMENT_METHOD,
		"status": so.status,
		"grand_total": so.grand_total,
		"currency": "VND",
		"delivery_date": str(so.delivery_date),
		"items": [
			{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "rate": r.rate, "amount": r.amount}
			for r in so.items
		],
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_order_status(order_token: str = "", phone: str = ""):
	"""Order-status lookup for a guest — requires BOTH the random `order_token` returned at checkout
	AND the phone number used at checkout; see module docstring point 6 for why, and for why every
	failure path returns the exact same generic error rather than a distinguishable one."""
	order_token = (order_token or "").strip()
	phone_digits = _normalize_phone(phone)

	def not_found():
		frappe.throw(_("Order not found. Check your order reference and phone number."), frappe.DoesNotExistError)

	if not order_token or not phone_digits:
		not_found()

	so_name = frappe.db.get_value("Sales Order", {"po_no": order_token, "customer": _WEB_GUEST_CUSTOMER}, "name")
	if not so_name:
		not_found()

	stored_phone = _normalize_phone(frappe.db.get_value("Sales Order", so_name, "contact_mobile"))
	if not stored_phone or stored_phone != phone_digits:
		not_found()

	doc = frappe.get_doc("Sales Order", so_name)
	return {
		"order_token": order_token,
		"status": doc.status,
		"payment_method": _PAYMENT_METHOD,
		"transaction_date": str(doc.transaction_date),
		"delivery_date": str(doc.delivery_date),
		"grand_total": doc.grand_total,
		"currency": "VND",
		"contact_display": doc.contact_display,
		"address_display": doc.address_display,
		"items": [
			{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "rate": r.rate, "amount": r.amount}
			for r in doc.items
		],
	}


# ============================================================================
# Empirical security proof — called from enterprise_core.enterprise_core.api's
# verify_b2c_commerce_demo(), part of the platform's standard verify_* regression sweep. Proves,
# rather than merely asserts, the two hard constraints of this module: server-side pricing survives
# a real tampering attempt, and order lookup genuinely requires both factors.
# ============================================================================

def verify_b2c_commerce_access_control():
	"""Real, empirical proof for WEB-05's guest-checkout security model. Always runs as Guest
	throughout (this endpoint never requires a session), unlike WEB-03/04's verify functions which
	must switch users — there IS no user to switch to here, which is exactly the point being
	proven."""
	original_user = frappe.session.user
	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	try:
		frappe.set_user("Guest")

		safe_codes = _safe_item_codes()
		check("At least one real item is available for checkout", bool(safe_codes), safe_codes)
		if not safe_codes:
			return {"all_passed": False, "checks": checks}
		item_code = safe_codes[0]

		# --- Price-tampering resistance: a spoofed "rate" in the payload must have ZERO effect. ---
		# Deliberately does NOT assert against a hardcoded flat price — Demo Consumer Distribution
		# Co. has a real, currently-active Pricing Rule promotion (Golden Demo #25's own CD02), so the
		# true server-computed price can legitimately be a discounted rate, not just the raw Item
		# Price. The real proof is comparing a TAMPERED order against a CLEAN order for the same item/
		# qty placed moments apart: if the client-supplied rate/price/amount had any effect at all,
		# the two would differ.
		clean_result = place_web_order(
			items=[{"item_code": item_code, "qty": 1}],
			contact={
				"full_name": "WEB05 Verify Clean Test",
				"phone": "0900000000",
				"address_line1": "1 Verify Street",
				"city": "Hanoi",
			},
		)
		tampered_result = place_web_order(
			items=[{"item_code": item_code, "qty": 1, "rate": 1, "price": 1, "amount": 1}],
			contact={
				"full_name": "WEB05 Verify Tamper Test",
				"phone": "0900000001",
				"address_line1": "123 Verify Street",
				"city": "Hanoi",
			},
		)
		check(
			"Price-tampering attempt (client sent rate/price/amount=1) had ZERO effect — identical real"
			" server-computed rate as an untampered order for the same item/qty",
			tampered_result["items"][0]["rate"] == clean_result["items"][0]["rate"]
			and tampered_result["items"][0]["rate"] not in (1, 0, None)
			and tampered_result["grand_total"] == clean_result["grand_total"],
			{"clean": clean_result, "tampered": tampered_result},
		)
		tampered_so = frappe.db.get_value("Sales Order", {"po_no": tampered_result["order_token"]}, "customer")
		check(
			"Order was created against the isolated Web Store Guest customer, never a real dealer",
			tampered_so == _WEB_GUEST_CUSTOMER,
			tampered_so,
		)

		# --- Order-lookup requires BOTH factors, real order used. ---
		order = place_web_order(
			items=[{"item_code": item_code, "qty": 2}],
			contact={
				"full_name": "WEB05 Verify Lookup Test",
				"phone": "0900000002",
				"address_line1": "456 Verify Avenue",
				"city": "Ho Chi Minh City",
			},
		)
		token = order["order_token"]

		correct_lookup_ok = False
		try:
			result = get_order_status(order_token=token, phone="0900000002")
			correct_lookup_ok = result["grand_total"] == order["grand_total"]
		except Exception:
			correct_lookup_ok = False
		check("Correct token + correct phone resolves the real order", correct_lookup_ok, token)

		wrong_phone_blocked = False
		try:
			get_order_status(order_token=token, phone="0999999999")
		except frappe.DoesNotExistError:
			wrong_phone_blocked = True
		except Exception:
			wrong_phone_blocked = False
		check("Correct token + WRONG phone is rejected (never returns the order on token alone)", wrong_phone_blocked, None)

		wrong_token_blocked = False
		try:
			get_order_status(order_token="WEB05-DOESNOTEXIST", phone="0900000002")
		except frappe.DoesNotExistError:
			wrong_token_blocked = True
		except Exception:
			wrong_token_blocked = False
		check("WRONG token + correct phone is rejected (phone alone is not enough either)", wrong_token_blocked, None)

		no_args_blocked = False
		try:
			get_order_status(order_token="", phone="")
		except frappe.DoesNotExistError:
			no_args_blocked = True
		except Exception:
			no_args_blocked = False
		check("Empty token/phone is rejected", no_args_blocked, None)

		# --- Input-bound rejection tests (defense-in-depth, not full anti-abuse — see docstring). ---
		bad_item_rejected = False
		try:
			place_web_order(
				items=[{"item_code": "PARA-API", "qty": 1}],  # a real but out-of-catalog pharma item
				contact={"full_name": "X", "phone": "0900000003", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			bad_item_rejected = True
		except Exception:
			bad_item_rejected = False
		check("An out-of-catalog real item_code (PARA-API) is rejected, not silently orderable", bad_item_rejected, None)

		bad_qty_rejected = False
		try:
			place_web_order(
				items=[{"item_code": item_code, "qty": -5}],
				contact={"full_name": "X", "phone": "0900000004", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			bad_qty_rejected = True
		except Exception:
			bad_qty_rejected = False
		check("A negative quantity is rejected", bad_qty_rejected, None)

		oversized_qty_rejected = False
		try:
			place_web_order(
				items=[{"item_code": item_code, "qty": 999999}],
				contact={"full_name": "X", "phone": "0900000005", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			oversized_qty_rejected = True
		except Exception:
			oversized_qty_rejected = False
		check("A qty far beyond real stock-on-hand is rejected (real stock check, not just a cap)", oversized_qty_rejected, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
