"""WEB-07 — Farm Customer / Technical Service Portal (Phase 7, master plan §8 line ~2575-2576:
"WEB-07 Farm Customer / Technical Service Portal — Farm account, orders, technical visits,
treatment/feed recommendations, service history."). Backs the standalone Next.js app in
`nextjs-demo/web-07-farm-portal/`.

THIS IS A CLOSE STRUCTURAL TWIN OF `dealer_portal_api.py` (WEB-03) AND `supplier_portal_api.py`
(WEB-04) — read those modules' docstrings first if you haven't; the authentication design below is
reused VERBATIM, not re-derived. Like those modules (and unlike `public_api.py`'s guest-only
WEB-01/02/05/06 sites), a real farm customer logs in with a real password, and every function below
resolves "which farm" from that real, authenticated identity — NEVER from a client-supplied
parameter. Nothing here is `allow_guest=True`.

AUTHENTICATION DESIGN — IDENTICAL to WEB-03/04, reused verbatim, not redesigned:
  Frappe's own native session-cookie login (`POST /api/method/login`). The Next.js app's own login
  Route Handler calls Frappe's login endpoint SERVER-SIDE (the same Node `http`-module Host-header
  workaround from `nextjs-demo/web-03-dealer-portal/lib/frappeAuth.ts`, reused verbatim in
  `nextjs-demo/web-07-farm-portal/lib/frappeAuth.ts`), keeps the real Frappe `sid` in an in-memory,
  server-only session store (pinned onto `globalThis` — see that app's `lib/session.ts` for the
  exact Route-Handler-vs-Server-Component bundle-splitting bug WEB-03 already found and fixed,
  deliberately not rediscovered here), and issues the BROWSER a separate, opaque, random session
  token as an `httpOnly` cookie. The real Frappe `sid` never reaches the browser.

FARM IDENTITY RESOLUTION — the single most important invariant in this whole module:
  `_get_my_farm()` below is the ONLY way any function here learns "which farm is this." It reads
  `frappe.session.user` and looks up the real `Customer` that a `User Permission` (created by
  `farm_portal_seeds.py`, `allow="Customer"`, `apply_to_all_doctypes=1` — same mechanism as
  WEB-03/04's precedent) links to that user. NO function in this module ever accepts a
  `customer`/`farm_id`/`farm` parameter from the caller and trusts it as the scoping identity — grep
  this file: the only place a document name appears in a function signature is as a DOCUMENT
  REFERENCE to check ownership of (e.g. `get_my_order_detail(sales_order)` — the Sales Order name is
  client-supplied, exactly like WEB-03's own function of the same name, but its OWNER is always
  re-derived from the document itself and compared against the session-resolved farm, never trusted
  from the request).

THREE-LAYER DEFENSE — IDENTICAL SHAPE FOR EVERY DOCTYPE HERE, because (unlike WEB-04's `Request for
Quotation`) both `Sales Order` and `Vet Technical Visit` carry a top-level `customer` Link field:
  Layer 1 resolves the farm via `_get_my_farm()`. Layer 2 is an explicit `filters={"customer": farm}`
  on a permission-aware `frappe.get_list()` call — the native `User Permission` ALSO cascades here
  automatically for BOTH doctypes (confirmed for `Vet Technical Visit` specifically by first checking
  `frappe.get_meta("Vet Technical Visit").permissions`: only `System Manager` had any access at all
  until `bootstrap_farm_portal_doctypes.py` added a read-only `Sales User` `Custom DocPerm` — without
  that, `Sales User`-role farm portal accounts would have had NO base read permission on this doctype
  and the native cascade would have had nothing to narrow). Layer 3 is a post-fetch Python
  re-assertion that every returned row's own `customer` field actually equals the resolved farm — so
  even a permission-configuration mistake could never silently leak a row. `get_all()`/raw SQL are
  deliberately never used here for farm-sensitive reads — every list call below is `frappe.get_list()`
  running as the real, session-authenticated farm user.

WHY `place_order()` RUNS AS THE REAL LOGGED-IN USER, NEVER `ignore_permissions=True`:
  Exactly like WEB-03/04's own write endpoints: `.insert()`/`.submit()` run with NO
  `ignore_permissions` argument, so native ERPNext validation (the credit-limit block via
  `Customer.check_credit_limit()`, the exact mechanism Golden Demo #10's own VD04 and WEB-03's own
  credit test already proved) fires for real, not a bypassed imitation of it. The unit rate is a
  SERVER-SIDE constant (`_FARM_RATE`) — the request body only ever carries `qty`, never a `rate`, so
  there is nothing for a client to under-price.

WHAT'S REAL VS. WHAT'S A DELIBERATE, MINIMAL, DISCLOSED SIMPLIFICATION:
  Orders/farms/credit-limit enforcement/Sales Order->Delivery Note flow are all 100% real ERPNext
  mechanisms (see `farm_portal_seeds.py`'s own docstring for the full data-provenance discussion).
  There is exactly ONE real, sellable catalog item (`OXYTET-200-INJ`, Golden Demo #9/#10's own real
  finished good) — this portal is honestly scoped to that single real product rather than inventing
  a larger fictional feed/veterinary catalog that doesn't exist anywhere else in this platform.
  Technical visits/recommendations are real `Vet Technical Visit` records (see that module's own
  docstring for why this DocType, not a new one, and why only 4 total records were seeded).
"""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Vet Pharma Co."
_FG_ITEM = "OXYTET-200-INJ"
_FG_RELEASED = "FG Released - DVP"
_TERRITORY = "Mekong Delta Region"
_FARM_RATE = 220000  # server-side constant — never client-supplied, see module docstring


def _get_my_farm():
	"""The ONLY function in this module that resolves "which farm is this" — see module docstring.
	Throws AuthenticationError for a guest, PermissionError for a real-but-unlinked Frappe user
	(e.g. Administrator, or any user who isn't a provisioned farm-portal account)."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Please log in to access the farm portal."), frappe.AuthenticationError)
	customer = frappe.db.get_value("User Permission", {"user": user, "allow": "Customer"}, "for_value")
	if not customer:
		frappe.throw(_("This account is not linked to a farm account."), frappe.PermissionError)
	return customer


@frappe.whitelist()
def get_my_profile():
	"""Confirms a login resolved to a real farm account, and hands the frontend a real Frappe CSRF
	token for the state-changing (`place_order`) POST call below — same one-round-trip pattern as
	WEB-03/04's own `get_my_profile()`."""
	customer = _get_my_farm()
	c = frappe.db.get_value("Customer", customer, ["customer_name", "territory", "customer_group"], as_dict=True)
	return {
		"user": frappe.session.user,
		"customer": customer,
		"customer_name": c.customer_name,
		"territory": c.territory,
		"customer_group": c.customer_group,
		"csrf_token": frappe.sessions.get_csrf_token(),
	}


@frappe.whitelist(methods=["GET"])
def get_my_catalog():
	"""The one real, sellable product this portal offers — Golden Demo #9's real
	`OXYTET-200-INJ`, including its real veterinary custom fields (`target_species`, `indication`,
	`withdrawal_period_days`) so a farm can see what it's actually indicated for. Not farm-scoped
	(a single shared catalog, same design choice WEB-03 made for its own item master), but still
	requires a logged-in farm session (not `allow_guest`)."""
	_get_my_farm()  # requires a real logged-in farm; return value unused (catalog isn't farm-scoped)
	item = frappe.db.get_value(
		"Item",
		_FG_ITEM,
		["item_code", "item_name", "stock_uom", "target_species", "indication", "withdrawal_period_days"],
		as_dict=True,
	)
	if not item:
		return []
	return [{**item, "price": _FARM_RATE, "currency": "VND"}]


@frappe.whitelist(methods=["GET"])
def get_my_orders():
	"""This farm's own Sales Orders only. Filtered explicitly by the resolved customer AND
	re-asserted in Python against every returned row's own `customer` field (belt-and-suspenders on
	top of the native User Permission cascade — see module docstring)."""
	customer = _get_my_farm()
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
	"""One Sales Order's detail — but ONLY if it genuinely belongs to the logged-in farm. This is
	the exact function the cross-farm negative test (farm A authenticated, requesting farm B's real
	order name) must fail against. Returns a plain 404-shaped error either way (order doesn't exist
	vs. belongs to someone else) — never a distinguishable "found but not yours" response."""
	customer = _get_my_farm()
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
def place_order(qty):
	"""Creates a REAL Sales Order for the logged-in farm, running genuinely permission-checked (no
	`ignore_permissions`) so native ERPNext validation — including the credit-limit block — fires
	for real. `customer` is ALWAYS the session-resolved farm; the only real product
	(`OXYTET-200-INJ`) and its rate (`_FARM_RATE`) are both server-side constants — the request body
	only ever carries `qty`, so there is nothing here for a client to spoof."""
	customer = _get_my_farm()
	try:
		qty = float(qty)
	except (TypeError, ValueError):
		qty = 0
	if qty <= 0:
		frappe.throw(_("Quantity must be greater than zero."))

	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": customer,
			"company": _COMPANY_NAME,
			"territory": _TERRITORY,
			"delivery_date": add_days(nowdate(), 7),
			"items": [{"item_code": _FG_ITEM, "qty": qty, "rate": _FARM_RATE, "warehouse": _FG_RELEASED}],
		}
	)
	so.insert()  # NOT ignore_permissions — real permission check + real credit-limit validation
	so.submit()
	return {"name": so.name, "grand_total": so.grand_total, "status": so.status}


@frappe.whitelist(methods=["GET"])
def get_my_technical_visits():
	"""This farm's own real Technical Visit records only (Golden Demo #10's own `Vet Technical
	Visit` DocType — see `farm_portal_seeds.py`'s module docstring for why no new DocType was
	created). Same explicit-filter + post-fetch-assert pattern as `get_my_orders()`."""
	customer = _get_my_farm()
	rows = frappe.get_list(
		"Vet Technical Visit",
		filters={"customer": customer},
		fields=["name", "customer", "visit_date", "sales_person", "products_discussed", "notes", "follow_up_date", "recommended_item"],
		order_by="visit_date desc",
	)
	leaked = [r for r in rows if r.customer != customer]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_recommendations():
	"""This farm's own real treatment/feed recommendations — the subset of its own Technical
	Visits that named a real `recommended_item`, enriched with that item's real veterinary fields
	(`target_species`/`indication`/`withdrawal_period_days`). Not a separate fabricated record type
	— a recommendation IS a (visit, recommended_item) pair, which is what actually happened here
	(see `farm_portal_seeds.py`)."""
	visits = get_my_technical_visits()
	recs = [v for v in visits if v.get("recommended_item")]
	result = []
	for v in recs:
		item = frappe.db.get_value(
			"Item", v["recommended_item"], ["item_code", "item_name", "target_species", "indication", "withdrawal_period_days"], as_dict=True
		)
		result.append({**v, "item": item})
	return result


@frappe.whitelist(methods=["GET"])
def get_my_service_history():
	"""A unified, chronological timeline of this farm's own real orders AND real technical visits
	— a computed view assembled entirely from data already independently scoped to this farm by
	`get_my_orders()`/`get_my_technical_visits()` above, never a fabricated parallel record. Each
	entry names a real event type/date/reference."""
	events = []
	for o in get_my_orders():
		events.append(
			{
				"type": "Order",
				"date": o["transaction_date"],
				"reference_doctype": "Sales Order",
				"reference_name": o["name"],
				"summary": f"Order {o['name']} — {o['status']} — {o['grand_total']:,.0f} VND",
			}
		)
	for v in get_my_technical_visits():
		summary = f"Technical visit by {v['sales_person'] or 'field rep'}"
		if v.get("recommended_item"):
			summary += f" — recommended {v['recommended_item']}"
		events.append(
			{
				"type": "Technical Visit",
				"date": v["visit_date"],
				"reference_doctype": "Vet Technical Visit",
				"reference_name": v["name"],
				"summary": summary,
			}
		)
	return sorted(events, key=lambda e: str(e["date"] or ""), reverse=True)


# ============================================================================
# Empirical permission proof — called from enterprise_core.enterprise_core.api's
# verify_farm_portal_demo(), part of the platform's standard verify_* regression sweep. Same
# technique as verify_dealer_portal_access_control()/verify_supplier_portal_access_control(): logs
# in as each real farm user (frappe.set_user) and empirically proves — not merely asserts — that
# farm A cannot see farm B's orders/technical visits/recommendations/service history, and that
# requesting the OTHER farm's real document id while authenticated as the first genuinely fails.
# ============================================================================

def verify_farm_portal_access_control():
	"""Real, empirical two-user permission proof for the WEB-07 farm portal. Always restores
	`frappe.session.user` in a `finally` block, even on failure, so a broken assertion here can
	never leave a later call running as a restricted farm user."""
	from enterprise_core.enterprise_core.farm_portal_seeds import _ALPHA_USER, _BETA_USER, _FARM_ALPHA, _FARM_BETA

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	original_user = frappe.session.user
	try:
		frappe.set_user(_ALPHA_USER)
		alpha_orders = get_my_orders()
		alpha_visits = get_my_technical_visits()
		alpha_recs = get_my_recommendations()
		alpha_history = get_my_service_history()
		check(
			"Alpha sees only its own Sales Orders (customer field on every row == Alpha)",
			all(o["customer"] == _FARM_ALPHA for o in alpha_orders) and len(alpha_orders) > 0,
			[o["name"] for o in alpha_orders],
		)
		check(
			"Alpha sees only its own Technical Visits",
			all(v["customer"] == _FARM_ALPHA for v in alpha_visits) and len(alpha_visits) > 0,
			[v["name"] for v in alpha_visits],
		)
		check("Alpha sees at least one real recommendation (with a real recommended_item)", len(alpha_recs) > 0 and all(r["customer"] == _FARM_ALPHA for r in alpha_recs), [r["name"] for r in alpha_recs])
		check(
			"Alpha's service history merges both its own orders and visits, nothing else",
			len(alpha_history) == len(alpha_orders) + len(alpha_visits),
			len(alpha_history),
		)

		frappe.set_user(_BETA_USER)
		beta_orders = get_my_orders()
		beta_visits = get_my_technical_visits()
		beta_recs = get_my_recommendations()
		beta_history = get_my_service_history()
		check(
			"Beta sees only its own Sales Orders (customer field on every row == Beta)",
			all(o["customer"] == _FARM_BETA for o in beta_orders) and len(beta_orders) > 0,
			[o["name"] for o in beta_orders],
		)
		check(
			"Beta sees only its own Technical Visits",
			all(v["customer"] == _FARM_BETA for v in beta_visits) and len(beta_visits) > 0,
			[v["name"] for v in beta_visits],
		)
		check("Beta sees at least one real recommendation (with a real recommended_item)", len(beta_recs) > 0 and all(r["customer"] == _FARM_BETA for r in beta_recs), [r["name"] for r in beta_recs])
		check(
			"Beta's service history merges both its own orders and visits, nothing else",
			len(beta_history) == len(beta_orders) + len(beta_visits),
			len(beta_history),
		)

		# Cross-farm negative tests: Beta is still the logged-in user here — try Alpha's real ids.
		alpha_order_name = alpha_orders[0]["name"] if alpha_orders else None

		def _blocked(fn, *args):
			try:
				fn(*args)
				return False
			except frappe.DoesNotExistError:
				return True
			except Exception:
				return False

		check(
			"Beta requesting Alpha's real order id (while authenticated as Beta) is genuinely rejected",
			_blocked(get_my_order_detail, alpha_order_name) and alpha_order_name is not None,
			alpha_order_name,
		)
		alpha_visit_names = {v["name"] for v in alpha_visits}
		beta_visit_names = {v["name"] for v in beta_visits}
		check(
			"Beta's own Technical Visit list contains NONE of Alpha's real visit names",
			not (beta_visit_names & alpha_visit_names) and len(alpha_visit_names) > 0,
			sorted(alpha_visit_names),
		)

		# Reverse direction: Alpha requesting Beta's real ids.
		frappe.set_user(_ALPHA_USER)
		beta_order_name = beta_orders[0]["name"] if beta_orders else None
		check(
			"Alpha requesting Beta's real order id (while authenticated as Alpha) is genuinely rejected",
			_blocked(get_my_order_detail, beta_order_name) and beta_order_name is not None,
			beta_order_name,
		)
		alpha_visits_2 = get_my_technical_visits()
		alpha_visit_names_2 = {v["name"] for v in alpha_visits_2}
		check(
			"Alpha's own Technical Visit list contains NONE of Beta's real visit names",
			not (alpha_visit_names_2 & beta_visit_names) and len(beta_visit_names) > 0,
			sorted(beta_visit_names),
		)

		# Unauthenticated access must also be genuinely rejected, not silently scoped to nothing.
		frappe.set_user("Guest")
		guest_blocked_orders = False
		guest_blocked_visits = False
		try:
			get_my_orders()
		except frappe.AuthenticationError:
			guest_blocked_orders = True
		except Exception:
			guest_blocked_orders = False
		try:
			get_my_technical_visits()
		except frappe.AuthenticationError:
			guest_blocked_visits = True
		except Exception:
			guest_blocked_visits = False
		check("A Guest (unauthenticated) request to get_my_orders() is rejected", guest_blocked_orders, None)
		check("A Guest (unauthenticated) request to get_my_technical_visits() is rejected", guest_blocked_visits, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
