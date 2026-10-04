"""WEB-03 — B2B Customer / Dealer Portal (Phase 7, master plan §8 lines ~2563-2564: "WEB-03 B2B
Customer / Dealer Portal — Catalog, price, stock, order, invoice, debt, return."). Seed module for
2 real, ISOLATED dealer Customer + User + User Permission records, backing the authenticated
`dealer_portal_api.py` and the standalone Next.js app in `nextjs-demo/web-03-dealer-portal/`.

WHY NEW, ISOLATED DEALERS — NOT GOLDEN DEMO #25's OWN HANOI/SAIGON DEALERS:
  Golden Demo #25 (consumer_dist_seeds.py) already has 2 real dealers (Golden Health Hanoi/Saigon
  Dealer Co.) with a documented "exactly N Sales Order/Delivery Note/Sales Invoice" idempotency
  assumption baked into its own `seed_consumer_dist_*` guards and `verify_consumer_dist_golden_demo`
  assertions. This session's own prior lessons (AI-DEMO-02's CAPA duplication, etc.) are explicit
  that writing NEW test transactions against an EXISTING flagship demo's own dealer risks exactly
  this kind of silent cross-demo corruption. So WEB-03 gets its OWN 2 dealers, in the SAME company
  (Demo Consumer Distribution Co.) and SAME customer group/price list/warehouse (genuine reuse of
  real master data, not a parallel company) but with globally distinct names/po_no prefixes
  (`WEB03-...`) that cannot collide with any `CD0x-...`/`FLOW-...` po_no Golden Demo #25 already
  uses or asserts against.

DEALER DESIGN — one deliberately-within-limit dealer, one deliberately-tight-limit dealer:
  - "WEB03 Portal Dealer Alpha" — generous credit limit (20,000,000 VND), used for the portal's
    HAPPY PATH: browsing catalog with dealer pricing, a real pre-seeded order/invoice history, and
    (via the API itself, not this seed script) a genuine new in-limit order placed live through the
    dealer_portal_api.place_order() endpoint during backend verification.
  - "WEB03 Portal Dealer Beta" — deliberately tight credit limit (3,000,000 VND), used to prove the
    portal's place_order() endpoint respects REAL ERPNext credit-limit validation (native
    Customer.check_credit_limit(), same mechanism as Golden Demo #25's own CD04), not a hand-rolled
    imitation of it. A legitimate small order fits; a deliberately oversized order does not.

PORTAL USER DESIGN — mirrors Golden Demo #24 (3PL)'s proven "restricted portal user" pattern
(threepl_seeds.py's `_ensure_client_users()`), the closest existing precedent in this codebase for
"give one external-facing login access to only its own slice of ERP data":
  - 2 real, distinct Frappe Users (`dealer.alpha.portal@pharmacountry.vn` /
    `dealer.beta.portal@pharmacountry.vn`, same demo password convention as 3PL,
    `Demo@1234` — a placeholder demo credential, documented here and in the portal app's own
    README, never hardcoded into frontend page components).
  - Roles: native `Sales User` (create/submit own Sales Order, read Sales Invoice — the exact
    permissions a real dealer-portal login needs) + `Stock User` (read Bin/stock data for
    availability). Both are STANDARD ERPNext roles, deliberately not a hand-rolled custom Role —
    the security boundary is the User Permission below, not the role's own (otherwise
    company-wide) doctype grants.
  - One `User Permission` per dealer user: `allow="Customer"`, `for_value=<their own Customer>`,
    `apply_to_all_doctypes=1` — same mechanism 3PL proved cascades automatically (via
    frappe.get_list()/permission-aware ORM calls) to any OTHER doctype with a top-level Link to
    Customer: Sales Order, Sales Invoice, Delivery Note, Quotation, etc. A dealer's own `Sales
    User`/`Stock User` role grants would otherwise let them see EVERY customer's Sales
    Order/Invoice company-wide; this User Permission is what narrows that down to "only documents
    whose `customer` field is their own" — confirmed empirically in
    `dealer_portal_api.verify_dealer_portal_access_control()` (called from
    `enterprise_core.enterprise_core.api.verify_dealer_portal_demo()`), not just asserted.

`dealer_portal_api.py`'s own module docstring documents the full authentication design (Frappe
session cookie via native `/api/method/login`, held server-side by the Next.js app, never exposed
to browser JS) — this module only concerns itself with the real ERP-side data/identity fixtures
that design depends on.
"""

import frappe
from frappe.utils import add_days, nowdate

from enterprise_core.enterprise_core.consumer_dist_seeds import _ensure_sales_flow

_COMPANY_NAME = "Demo Consumer Distribution Co."
_DC_WAREHOUSE = "Distribution Center - DCD"

_VITC_ITEM = "VITC-1000-EFF"
_FACIAL_ITEM = "FACIAL-CLEANSER-150ML"

_DEALER_CUSTOMER_GROUP = "Consumer Health Dealers"
_DEALER_PRICE_LIST = "Dealer Tier Price List (Consumer Dist Demo)"
_VITC_DEALER_RATE = 210000

_TERRITORY_NORTH = "Northern Vietnam Dealer Territory"
_TERRITORY_SOUTH = "Southern Vietnam Dealer Territory"
_SALES_PERSON_NORTH = "Le Thi Hoa (Consumer Dist Demo)"
_SALES_PERSON_SOUTH = "Pham Van Minh (Consumer Dist Demo)"

_DEALER_ALPHA = "WEB03 Portal Dealer Alpha"
_DEALER_BETA = "WEB03 Portal Dealer Beta"
_ALPHA_CREDIT_LIMIT = 20000000
_BETA_CREDIT_LIMIT = 3000000

_DEMO_USER_DOMAIN = "pharmacountry.vn"
_DEMO_USER_PASSWORD = "Demo@1234"
_ALPHA_USER = f"dealer.alpha.portal@{_DEMO_USER_DOMAIN}"
_BETA_USER = f"dealer.beta.portal@{_DEMO_USER_DOMAIN}"


# ---------------------------------------------------------------------------
# Master data — 2 isolated dealer Customers + portal Users + User Permission
# ---------------------------------------------------------------------------

def _ensure_dealer_customer(name, territory, credit_limit):
	created = False
	if not frappe.db.exists("Customer", {"customer_name": name}):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": _DEALER_CUSTOMER_GROUP,
				"territory": territory,
				"default_price_list": _DEALER_PRICE_LIST,
			}
		).insert(ignore_permissions=True)
		created = True
	existing_limit = frappe.db.get_value(
		"Customer Credit Limit", {"parent": name, "company": _COMPANY_NAME}, ["name", "credit_limit"], as_dict=True
	)
	if existing_limit:
		if existing_limit.credit_limit != credit_limit:
			frappe.db.set_value("Customer Credit Limit", existing_limit.name, "credit_limit", credit_limit)
	else:
		customer = frappe.get_doc("Customer", name)
		customer.append("credit_limits", {"company": _COMPANY_NAME, "credit_limit": credit_limit})
		customer.save(ignore_permissions=True)
	return created


_PORTAL_ROLES = ("Sales User", "Stock User", "Accounts User")
# "Accounts User" is required for base (permlevel 0) READ on Sales Invoice — confirmed by reading
# erpnext/accounts/doctype/sales_invoice/sales_invoice.json's own `permissions` list: only
# "Accounts Manager"/"Accounts User" carry permlevel-0 read there (native role "All" only gets a
# restricted permlevel-1 read). A disclosed, deliberate simplification: "Accounts User" is a
# broader native role than the minimum a real production dealer login would want (it also grants
# visibility into e.g. Payment Entry/Journal Entry doctypes that aren't Customer-linked), but the
# User Permission created below still enforces the hard requirement (no cross-dealer leakage) for
# every doctype that DOES carry a top-level Customer link, which covers every endpoint this portal
# actually exposes (Sales Order/Sales Invoice/Delivery Note). A production build would likely
# replace this with a purpose-built custom Role carrying only the exact DocPerms needed, via Role
# Permission Manager, instead of reusing a stock ERPNext role wholesale.


def _ensure_portal_user(email, first_name, customer):
	created = False
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"send_welcome_email": 0,
				"new_password": _DEMO_USER_PASSWORD,
				"roles": [{"role": r} for r in _PORTAL_ROLES],
			}
		).insert(ignore_permissions=True)
		created = True
	else:
		user_doc = frappe.get_doc("User", email)
		existing_roles = {r.role for r in user_doc.roles}
		missing = [r for r in _PORTAL_ROLES if r not in existing_roles]
		if missing:
			for r in missing:
				user_doc.append("roles", {"role": r})
			user_doc.save(ignore_permissions=True)
			created = True
	# Customer-scoped User Permission, apply_to_all_doctypes=1 — see module docstring for the full
	# reasoning (same mechanism as 3PL's Warehouse-scoped precedent, proven to cascade to any
	# doctype with a top-level Link to Customer via frappe.get_list()/ORM reads).
	if not frappe.db.exists("User Permission", {"user": email, "allow": "Customer", "for_value": customer}):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Customer", "for_value": customer, "apply_to_all_doctypes": 1}
		).insert(ignore_permissions=True)
		created = True
	return created


def seed_dealer_portal_master_data():
	"""WEB-03 master data — 2 isolated dealer Customers (Alpha: generous credit limit, happy-path
	demo; Beta: deliberately tight credit limit, credit-block proof), each with exactly one portal
	User restricted via a Customer-scoped User Permission to their own data only."""
	if not frappe.db.exists("Company", _COMPANY_NAME):
		return "seed_dealer_portal_master_data: SKIPPED — run seed_consumer_dist_master_data first."
	alpha_created = _ensure_dealer_customer(_DEALER_ALPHA, _TERRITORY_NORTH, _ALPHA_CREDIT_LIMIT)
	beta_created = _ensure_dealer_customer(_DEALER_BETA, _TERRITORY_SOUTH, _BETA_CREDIT_LIMIT)
	alpha_user_created = _ensure_portal_user(_ALPHA_USER, "Dealer Alpha Portal", _DEALER_ALPHA)
	beta_user_created = _ensure_portal_user(_BETA_USER, "Dealer Beta Portal", _DEALER_BETA)
	return (
		f"seed_dealer_portal_master_data: Alpha customer {'created' if alpha_created else 'already existed'} "
		f"(credit_limit={_ALPHA_CREDIT_LIMIT}), Beta customer {'created' if beta_created else 'already existed'} "
		f"(credit_limit={_BETA_CREDIT_LIMIT}). Alpha user {'created' if alpha_user_created else 'already existed'}, "
		f"Beta user {'created' if beta_user_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# Pre-seeded order/invoice history (happy path — Alpha only)
# ---------------------------------------------------------------------------

def seed_dealer_portal_sales_flow():
	"""A real, submitted Sales Order -> Delivery Note -> Sales Invoice chain for Dealer Alpha only
	(via consumer_dist_seeds.py's own already-debugged `_ensure_sales_flow` helper — reusing the
	exact code that already fixed the "which Delivery Note is the original vs. the return" bug,
	rather than re-risking that same bug in a second implementation), so the portal's "my
	orders"/"my invoices"/"my debt" pages have real, non-empty history the moment the frontend is
	built, independent of whatever orders get placed live through the API during verification.
	Dealer Beta deliberately gets NO pre-seeded flow here — its only order is the live credit-limit
	proof in `seed_dealer_portal_credit_test()`, so its portal view stays minimal/predictable."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_ALPHA}):
		return "seed_dealer_portal_sales_flow: SKIPPED — run seed_dealer_portal_master_data first."
	so, dn, si = _ensure_sales_flow(
		_DEALER_ALPHA, _TERRITORY_NORTH, _VITC_ITEM, 15, _VITC_DEALER_RATE, _SALES_PERSON_NORTH, "WEB03-ALPHA-FLOW-1"
	)
	return f"seed_dealer_portal_sales_flow: Alpha SO/DN/SI = {so}/{dn}/{si}."


# ---------------------------------------------------------------------------
# Credit-limit proof (Beta) — mirrors Golden Demo #25's own CD04, on an isolated dealer
# ---------------------------------------------------------------------------

def _test_beta_credit_block():
	"""Deliberately over-limit Sales Order for Dealer Beta (credit_limit=3,000,000): 50 units at
	the dealer rate (10,500,000) is far beyond the limit. Native
	erpnext.selling.doctype.customer.customer.check_credit_limit() (same mechanism as Golden Demo
	#25's own CD04, confirmed there by reading the actual source) must block this at submit."""
	if frappe.db.exists("Sales Order", {"po_no": "WEB03-BETA-CREDIT-TEST", "customer": _DEALER_BETA}):
		return True
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DEALER_BETA,
			"company": _COMPANY_NAME,
			"territory": _TERRITORY_SOUTH,
			"delivery_date": add_days(nowdate(), 7),
			"po_no": "WEB03-BETA-CREDIT-TEST",
			"items": [{"item_code": _VITC_ITEM, "qty": 50, "rate": _VITC_DEALER_RATE, "warehouse": _DC_WAREHOUSE}],
		}
	)
	blocked = False
	try:
		so.insert(ignore_permissions=True)
		so.submit()
	except frappe.ValidationError:
		blocked = True
		if so.name and frappe.db.exists("Sales Order", so.name):
			actual_docstatus = frappe.db.get_value("Sales Order", so.name, "docstatus")
			if actual_docstatus == 1:
				frappe.get_doc("Sales Order", so.name).cancel()
			else:
				frappe.delete_doc("Sales Order", so.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("WEB-03 credit-limit test FAILED: over-credit-limit dealer order was not blocked!")
	return True


def seed_dealer_portal_credit_test():
	"""A real, small, WITHIN-LIMIT Sales Order for Dealer Beta (proves the happy path also works
	for the tight-limit dealer, not just Alpha), plus the deliberate over-limit negative test."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_BETA}):
		return "seed_dealer_portal_credit_test: SKIPPED — run seed_dealer_portal_master_data first."
	so, dn, si = _ensure_sales_flow(
		_DEALER_BETA, _TERRITORY_SOUTH, _VITC_ITEM, 5, _VITC_DEALER_RATE, _SALES_PERSON_SOUTH, "WEB03-BETA-FLOW-1"
	)
	blocked = _test_beta_credit_block()
	return f"seed_dealer_portal_credit_test: Beta in-limit SO/DN/SI = {so}/{dn}/{si}. Over-limit block={blocked}."
