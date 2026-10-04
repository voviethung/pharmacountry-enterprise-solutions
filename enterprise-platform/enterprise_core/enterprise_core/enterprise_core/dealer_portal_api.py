"""WEB-03 — B2B Customer / Dealer Portal (Phase 7, master plan §8 lines ~2563-2564: "WEB-03 B2B
Customer / Dealer Portal — Catalog, price, stock, order, invoice, debt, return."). Backs the
standalone Next.js app in `nextjs-demo/web-03-dealer-portal/`.

THIS IS A FUNDAMENTALLY DIFFERENT SECURITY MODEL FROM `public_api.py` (WEB-01/WEB-02/Hub) — read
that module's docstring first if you haven't: those 3 sites are GUEST-ONLY (`allow_guest=True`,
zero authentication, hand-picked hardcoded scope). THIS module has the opposite job: a real dealer
logs in with a real password, and every function below must resolve "which dealer" from that real,
authenticated identity — NEVER from a client-supplied parameter. Nothing here is `allow_guest=True`.

AUTHENTICATION DESIGN (decided here, applies to the whole module):
  Frappe's own native session-cookie login (`POST /api/method/login` with `usr`/`pwd`), NOT a
  hand-rolled login function, NOT a per-dealer API key/secret. Reasoning:
    - API key/secret per dealer was rejected: it's the right mechanism for machine-to-machine
      integration, but wrong for "a customer logs in with a password" — there's no realistic UX
      for a human typing an API secret into a login form, and this master plan explicitly asks for
      a *customer* portal, not a B2B integration endpoint.
    - Frappe's native `/api/method/login` is real, already handles password hashing/lockout/2FA
      hooks/`User.enabled` checks correctly, and returns a real `sid` session cookie — reusing it
      is strictly safer than re-implementing password verification in this module.
  The CRITICAL design decision is where that `sid` lives afterward: it is NEVER sent to the
  browser. The Next.js app's own login Route Handler calls Frappe's login endpoint SERVER-SIDE
  (reusing WEB-01/02/Hub's own Node `http`-module Host-header workaround — see
  `nextjs-demo/web-03-dealer-portal/lib/frappeAuth.ts`), keeps the real Frappe `sid` in an
  in-memory, server-only session store, and issues the BROWSER a separate, opaque, random
  Next.js-owned session token as an `httpOnly` cookie. The browser's JS can never read that cookie
  (httpOnly) and never sees the real Frappe `sid` at all, even in a network trace — only the
  Next.js server ever presents the real `sid` to Frappe, from server-side Route Handlers/Server
  Components. This is strictly safer than proxying the raw Frappe cookie to the browser (which
  this task's own instructions flagged as the risk to avoid) at the cost of session state living
  only in the Next.js process's memory (acceptable for this demo; documented in that app's README
  as a real, disclosed limitation — not silently glossed over).

DEALER IDENTITY RESOLUTION — the single most important invariant in this whole module:
  `_get_my_customer()` below is the ONLY way any function here learns "which dealer is this."
  It reads `frappe.session.user` (set by the Frappe framework itself from the validated `sid`
  cookie presented with THIS request — not from any request body/query parameter this module
  reads) and looks up the real `Customer` that a `User Permission` (created by
  `dealer_portal_seeds.py`, `allow="Customer"`, `apply_to_all_doctypes=1` — same mechanism as
  Golden Demo #24/3PL's proven Warehouse-scoped precedent) links to that user. NO function in this
  module ever accepts a `customer`/`dealer_id`/`dealer` parameter from the caller and trusts it —
  grep this file: there is no such parameter anywhere. Every list/read query below is filtered by
  the customer resolved from `_get_my_customer()`, AND (defense in depth, not relying on a single
  layer) native ERPNext/Frappe permission enforcement (the `User Permission` cascades automatically
  to Sales Order/Sales Invoice/Delivery Note through `frappe.get_list()`, the SAME permission-aware
  entry point 3PL's own precedent proved works this way — `frappe.get_all()`/raw SQL are
  deliberately never used here for cross-dealer-sensitive reads), AND an explicit
  post-fetch assertion in Python that every returned row's own `customer` field actually equals the
  resolved dealer (so even a permission-configuration mistake could never silently leak a row).

  `_get_my_customer()` itself uses `frappe.db.get_value()` (not `get_list()`) for exactly one
  reason, explicitly documented here (mirroring `public_api.py`'s own "why get_all() here"
  discipline): the query's ONLY filter is `frappe.session.user` — the framework-authenticated
  identity of the CURRENT request, not a value any caller could ever substitute — so there is no
  ambient-permission surface being bypassed; it is structurally equivalent to a user reading their
  own `frappe.get_doc("User", frappe.session.user)`.

  Item catalog/stock reads are NOT customer-scoped (there is one shared Item master and one shared
  Distribution Center warehouse across all dealers, matching Golden Demo #25's own real design) —
  only PRICING and TRANSACTIONAL data (orders/invoices/debt/returns) are dealer-scoped.

WHY THESE ENDPOINTS RUN AS THE REAL LOGGED-IN USER, NEVER `ignore_permissions=True`:
  Every write here (`place_order`, `request_return`) calls `.insert()`/`.submit()` with NO
  `ignore_permissions` argument — they run genuinely permission-checked as `frappe.session.user`
  (the real dealer), so ERPNext's own native validation (credit limit block via
  `Customer.check_credit_limit()`, the exact mechanism Golden Demo #25's own CD04 test already
  proved) fires for real, not a bypassed imitation of it.
"""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Consumer Distribution Co."
_DC_WAREHOUSE = "Distribution Center - DCD"
_PUBLIC_PRICE_LIST = "Standard Selling"


def _get_my_customer():
	"""The ONLY function in this module that resolves "which dealer is this" — see module
	docstring. Throws AuthenticationError for a guest, PermissionError for a real-but-unlinked
	Frappe user (e.g. Administrator, or any user who isn't a provisioned dealer-portal account)."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Please log in to access the dealer portal."), frappe.AuthenticationError)
	customer = frappe.db.get_value("User Permission", {"user": user, "allow": "Customer"}, "for_value")
	if not customer:
		frappe.throw(_("This account is not linked to a dealer account."), frappe.PermissionError)
	return customer


def _safe_item_codes():
	"""Same real, data-driven filter as public_api.py's own `_safe_item_codes()` (Item with real
	Stock Ledger Entry movement for this company AND a real selling Item Price on the public
	Standard Selling list) — deliberately NOT imported from public_api.py to keep the guest-only
	and authenticated modules independent of one another (a change to one can never silently
	affect the other's security boundary)."""
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


def _item_price(item_code, price_list):
	"""Dealer's own negotiated price on THEIR price list, falling back to the public Standard
	Selling rate only if the dealer's own list has no override for this item — never the other way
	around, and never any OTHER dealer's price list."""
	price = frappe.db.get_value(
		"Item Price", {"item_code": item_code, "selling": 1, "price_list": price_list}, "price_list_rate"
	)
	if price is None and price_list != _PUBLIC_PRICE_LIST:
		price = frappe.db.get_value(
			"Item Price", {"item_code": item_code, "selling": 1, "price_list": _PUBLIC_PRICE_LIST}, "price_list_rate"
		)
	return price


@frappe.whitelist()
def get_my_profile():
	"""Confirms a login resolved to a real dealer, and hands the frontend a real Frappe CSRF token
	for the state-changing (`place_order`/`request_return`) POST calls below — Frappe's own
	session-cookie CSRF protection requires this even though the raw `sid` never reaches a browser
	in this app's design (see module docstring); fetched here, once, right after login, rather
	than adding a second dedicated endpoint."""
	customer = _get_my_customer()
	c = frappe.db.get_value(
		"Customer", customer, ["customer_name", "territory", "default_price_list", "customer_group"], as_dict=True
	)
	return {
		"user": frappe.session.user,
		"customer": customer,
		"customer_name": c.customer_name,
		"territory": c.territory,
		"price_list": c.default_price_list or _PUBLIC_PRICE_LIST,
		"csrf_token": frappe.sessions.get_csrf_token(),
	}


@frappe.whitelist(methods=["GET"])
def get_catalog_with_my_pricing():
	"""Real product catalog (same safe-item-code filter as the public site) priced with THIS
	dealer's own negotiated price list — never the generic public price WEB-01 shows, never
	another dealer's price."""
	customer = _get_my_customer()
	price_list = frappe.db.get_value("Customer", customer, "default_price_list") or _PUBLIC_PRICE_LIST
	items = []
	for item_code in _safe_item_codes():
		item = frappe.db.get_value("Item", item_code, ["item_code", "item_name", "stock_uom", "sales_uom"], as_dict=True)
		if not item:
			continue
		items.append(
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				# `sales_uom` (e.g. "Tube") over `stock_uom` for display — same fix as
				# public_api.py's `_serialize_item()`, see its comment for the real bug this
				# addresses (VITC-1000-EFF showing "/ Kg" next to a per-tube price).
				"uom": item.sales_uom or item.stock_uom,
				"my_price": _item_price(item_code, price_list),
				"price_list": price_list,
				"currency": "VND",
			}
		)
	return items


@frappe.whitelist(methods=["GET"])
def get_stock_availability(item_code: str = ""):
	"""Real-time on-hand qty at the shared Distribution Center warehouse — not dealer-scoped (one
	shared warehouse serves every dealer, matching Golden Demo #25's own real design), but still
	requires a logged-in dealer session (not `allow_guest`), and restricted to the same safe
	item-code set the catalog exposes."""
	_get_my_customer()  # requires a real logged-in dealer; return value unused (stock isn't dealer-scoped)
	safe_codes = _safe_item_codes()
	if item_code:
		if item_code not in safe_codes:
			frappe.throw(_("Item not found."), frappe.DoesNotExistError)
		codes = [item_code]
	else:
		codes = safe_codes
	result = []
	for code in codes:
		qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": _DC_WAREHOUSE}, "actual_qty") or 0
		result.append({"item_code": code, "warehouse": _DC_WAREHOUSE, "available_qty": qty})
	return result


@frappe.whitelist(methods=["GET"])
def get_my_orders():
	"""This dealer's own Sales Orders only. Filtered explicitly by the resolved customer AND
	re-asserted in Python against every returned row's own `customer` field (belt-and-suspenders on
	top of the native User Permission cascade — see module docstring)."""
	customer = _get_my_customer()
	rows = frappe.get_list(
		"Sales Order",
		filters={"customer": customer},
		fields=["name", "customer", "transaction_date", "delivery_date", "grand_total", "status", "docstatus", "po_no"],
		order_by="transaction_date desc, creation desc",
	)
	leaked = [r for r in rows if r.customer != customer]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_order_detail(sales_order: str = ""):
	"""One Sales Order's detail — but ONLY if it genuinely belongs to the logged-in dealer. This is
	the exact function the cross-dealer negative test (dealer A authenticated, requesting dealer
	B's real order name) must fail against. Returns a plain 404-shaped error either way (order
	doesn't exist vs. belongs to someone else) — never a distinguishable "found but not yours"
	response that would itself leak the order's existence to another dealer."""
	customer = _get_my_customer()
	if not sales_order or not frappe.db.exists("Sales Order", sales_order):
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)
	actual_customer = frappe.db.get_value("Sales Order", sales_order, "customer")
	if actual_customer != customer:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Sales Order", sales_order)
	if not doc.has_permission("read"):
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)
	return {
		"name": doc.name,
		"customer": doc.customer,
		"transaction_date": doc.transaction_date,
		"delivery_date": doc.delivery_date,
		"status": doc.status,
		"grand_total": doc.grand_total,
		"po_no": doc.po_no,
		"items": [
			{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "rate": r.rate, "amount": r.amount}
			for r in doc.items
		],
	}


@frappe.whitelist(methods=["POST"])
def place_order(items):
	"""Creates a REAL Sales Order for the logged-in dealer, running genuinely permission-checked
	(no `ignore_permissions`) so native ERPNext validation — including the credit-limit block —
	fires for real. `customer` is ALWAYS the session-resolved dealer; nothing in `items` can ever
	name a different customer (the payload only carries item_code/qty, there is no customer field
	to spoof in the first place)."""
	customer = _get_my_customer()
	if isinstance(items, str):
		items = frappe.parse_json(items)
	if not items:
		frappe.throw(_("At least one item is required."))
	safe_codes = set(_safe_item_codes())
	for row in items:
		if row.get("item_code") not in safe_codes:
			frappe.throw(_("Item {0} is not available for order.").format(row.get("item_code")))
		if not row.get("qty") or float(row["qty"]) <= 0:
			frappe.throw(_("Quantity must be greater than zero."))

	customer_doc = frappe.db.get_value("Customer", customer, ["territory", "default_price_list"], as_dict=True)
	price_list = customer_doc.default_price_list or _PUBLIC_PRICE_LIST
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": customer,
			"company": _COMPANY_NAME,
			"territory": customer_doc.territory,
			"selling_price_list": price_list,
			"delivery_date": add_days(nowdate(), 7),
			"items": [
				{
					"item_code": row["item_code"],
					"qty": float(row["qty"]),
					"rate": _item_price(row["item_code"], price_list),
					"warehouse": _DC_WAREHOUSE,
				}
				for row in items
			],
		}
	)
	so.insert()  # NOT ignore_permissions — real permission check + real credit-limit validation
	so.submit()
	return {"name": so.name, "grand_total": so.grand_total, "status": so.status}


@frappe.whitelist(methods=["GET"])
def get_my_invoices():
	"""This dealer's own Sales Invoices only — same explicit-filter + post-fetch-assert pattern as
	`get_my_orders()`."""
	customer = _get_my_customer()
	rows = frappe.get_list(
		"Sales Invoice",
		filters={"customer": customer},
		fields=["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "docstatus"],
		order_by="posting_date desc, creation desc",
	)
	leaked = [r for r in rows if r.customer != customer]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_debt():
	"""This dealer's own real outstanding receivable balance (native `get_balance_on`, the same
	GL-based aggregate ERPNext's own UI uses) plus their real credit limit/headroom. `customer` is
	always the session-resolved dealer — this computed aggregate is never parameterizable."""
	from erpnext.accounts.utils import get_balance_on

	customer = _get_my_customer()
	outstanding = get_balance_on(party_type="Customer", party=customer, company=_COMPANY_NAME) or 0
	credit_limit = frappe.db.get_value(
		"Customer Credit Limit", {"parent": customer, "company": _COMPANY_NAME}, "credit_limit"
	)
	return {
		"customer": customer,
		"outstanding_balance": outstanding,
		"credit_limit": credit_limit,
		"available_credit": (credit_limit - outstanding) if credit_limit is not None else None,
	}


@frappe.whitelist(methods=["GET"])
def get_my_returns():
	"""This dealer's own return Delivery Notes only — same explicit-filter + post-fetch-assert
	pattern as `get_my_orders()`."""
	customer = _get_my_customer()
	rows = frappe.get_list(
		"Delivery Note",
		filters={"customer": customer, "is_return": 1},
		fields=["name", "customer", "posting_date", "grand_total", "docstatus", "return_against"],
		order_by="posting_date desc, creation desc",
	)
	leaked = [r for r in rows if r.customer != customer]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_deliveries_eligible_for_return():
	"""This dealer's own non-return, submitted Delivery Notes — the list a dealer picks FROM when
	filing a new return request. Same explicit-filter + post-fetch-assert pattern."""
	customer = _get_my_customer()
	rows = frappe.get_list(
		"Delivery Note",
		filters={"customer": customer, "is_return": 0, "docstatus": 1},
		fields=["name", "customer", "posting_date", "grand_total"],
		order_by="posting_date desc, creation desc",
	)
	leaked = [r for r in rows if r.customer != customer]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["POST"])
def request_return(delivery_note: str = "", qty=None):
	"""Files a real return against ONE of the dealer's own real Delivery Notes — re-checked against
	the session-resolved customer (never trusting the client-supplied `delivery_note` name alone),
	using ERPNext's native `make_return_doc()` (same mechanism Golden Demo #25's own CD05 return
	uses). Runs genuinely permission-checked (no `ignore_permissions`)."""
	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	customer = _get_my_customer()
	if not delivery_note or not frappe.db.exists("Delivery Note", delivery_note):
		frappe.throw(_("Delivery not found."), frappe.DoesNotExistError)
	actual_customer = frappe.db.get_value("Delivery Note", delivery_note, "customer")
	if actual_customer != customer:
		frappe.throw(_("Delivery not found."), frappe.DoesNotExistError)

	dn_return = make_return_doc("Delivery Note", delivery_note)
	if qty:
		for row in dn_return.items:
			row.qty = -abs(float(qty))
	dn_return.insert()
	dn_return.submit()
	return {"name": dn_return.name, "grand_total": dn_return.grand_total}


# ============================================================================
# Empirical permission proof — called from enterprise_core.enterprise_core.api's
# verify_dealer_portal_demo(), part of the platform's standard verify_* regression sweep. This is
# the single most important test in this whole module (see the master task's own framing): it
# logs in as each real dealer user (frappe.set_user, the same technique 3PL's own
# verify_3pl_golden_demo() re-derives its W01 access-control check with) and empirically proves —
# not merely asserts — that dealer A cannot see dealer B's orders/invoices/debt, and that
# requesting the OTHER dealer's real order id while authenticated as the first genuinely fails.
# ============================================================================

def verify_dealer_portal_access_control():
	"""Real, empirical two-user permission proof for the WEB-03 dealer portal. Always restores
	`frappe.session.user` in a `finally` block, even on failure, so a broken assertion here can
	never leave a later call running as a restricted dealer user (same discipline as 3PL's own
	`seed_3pl_access_control_test()`)."""
	from enterprise_core.enterprise_core.dealer_portal_seeds import _ALPHA_USER, _BETA_USER, _DEALER_ALPHA, _DEALER_BETA

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	original_user = frappe.session.user
	try:
		frappe.set_user(_ALPHA_USER)
		alpha_orders = get_my_orders()
		alpha_invoices = get_my_invoices()
		alpha_debt = get_my_debt()
		check(
			"Alpha sees only its own Sales Orders (customer field on every row == Alpha)",
			all(o.customer == _DEALER_ALPHA for o in alpha_orders) and len(alpha_orders) > 0,
			[o.name for o in alpha_orders],
		)
		check(
			"Alpha sees only its own Sales Invoices",
			all(i.customer == _DEALER_ALPHA for i in alpha_invoices),
			[i.name for i in alpha_invoices],
		)
		check("Alpha's debt view resolves to Alpha's own customer", alpha_debt["customer"] == _DEALER_ALPHA, alpha_debt)

		frappe.set_user(_BETA_USER)
		beta_orders = get_my_orders()
		beta_invoices = get_my_invoices()
		beta_debt = get_my_debt()
		check(
			"Beta sees only its own Sales Orders (customer field on every row == Beta)",
			all(o.customer == _DEALER_BETA for o in beta_orders) and len(beta_orders) > 0,
			[o.name for o in beta_orders],
		)
		check(
			"Beta sees only its own Sales Invoices",
			all(i.customer == _DEALER_BETA for i in beta_invoices),
			[i.name for i in beta_invoices],
		)
		check("Beta's debt view resolves to Beta's own customer", beta_debt["customer"] == _DEALER_BETA, beta_debt)

		# Cross-dealer negative test: Beta is still the logged-in user here — try to fetch one of
		# ALPHA's real order names directly.
		alpha_order_name = alpha_orders[0].name if alpha_orders else None
		cross_access_blocked = False
		try:
			get_my_order_detail(alpha_order_name)
		except frappe.DoesNotExistError:
			cross_access_blocked = True
		except Exception:
			cross_access_blocked = False
		check(
			"Beta requesting Alpha's real order id (while authenticated as Beta) is genuinely rejected",
			cross_access_blocked and alpha_order_name is not None,
			alpha_order_name,
		)

		# And the reverse direction, for completeness.
		frappe.set_user(_ALPHA_USER)
		beta_order_name = beta_orders[0].name if beta_orders else None
		reverse_blocked = False
		try:
			get_my_order_detail(beta_order_name)
		except frappe.DoesNotExistError:
			reverse_blocked = True
		except Exception:
			reverse_blocked = False
		check(
			"Alpha requesting Beta's real order id (while authenticated as Alpha) is genuinely rejected",
			reverse_blocked and beta_order_name is not None,
			beta_order_name,
		)

		# Unauthenticated access must also be genuinely rejected, not silently scoped to nothing.
		frappe.set_user("Guest")
		guest_blocked = False
		try:
			get_my_orders()
		except frappe.AuthenticationError:
			guest_blocked = True
		except Exception:
			guest_blocked = False
		check("A Guest (unauthenticated) request to get_my_orders() is rejected", guest_blocked, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
