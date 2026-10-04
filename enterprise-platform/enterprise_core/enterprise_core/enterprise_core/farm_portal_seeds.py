"""WEB-07 — Farm Customer / Technical Service Portal (Phase 7, master plan §8 line ~2575-2576:
"WEB-07 Farm Customer / Technical Service Portal — Farm account, orders, technical visits,
treatment/feed recommendations, service history."). Seed module for 2 real, ISOLATED farm
Customer + User + User Permission records, backing the authenticated `farm_portal_api.py` and the
standalone Next.js app in `nextjs-demo/web-07-farm-portal/`.

REAL DATA INVESTIGATION (done before writing any of this — see also this module's own docstring
references below):
  - Golden Demo #10 (Veterinary Distribution, master plan DEMO 16) is the ONLY golden demo in this
    platform with a real "technical visit" concept: `Vet Technical Visit` (VD07), already created
    by `bootstrap_vet_dist_doctypes.py`, already populated with one real record tied to Golden Demo
    #10's own dealer ("VetCare Mekong Dealer Co."). This is reused directly (via
    `bootstrap_farm_portal_doctypes.py`'s small additive schema changes — see that module's own
    docstring) rather than inventing a parallel "Farm Visit" DocType from scratch.
  - Master plan DEMO 20 "Feed Distribution & Dealer Management" (FD07 "Technical visit") was NEVER
    built as a golden demo in this project (confirmed: `documents/project_status.md`'s own golden
    demo list runs #1-#28, none of which is DEMO 20) — so there is no second, alternative source of
    real technical-visit data to check.
  - Golden Demos #11/#12/#13/#14 (Pig/Poultry/Cattle/Hatchery Farm) are the FARMS' OWN internal
    operations, each its own separate Company — none of them is modeled as a Customer of Golden
    Demo #10's Demo Vet Pharma Co., so there is no real, pre-existing cross-demo link to reuse the
    way Golden Demo #28 (Meat Processing) genuinely sourced from Golden Demo #11's own `Pig Sale
    Lot`. No such link was fabricated here either.

WHY 2 NEW, ISOLATED FARM CUSTOMERS — NOT GOLDEN DEMO #10's OWN "VetCare Mekong Dealer Co.":
  Golden Demo #10's own `verify_vet_dist_golden_demo()` (VD01-VD07) asserts against that exact
  Customer/Sales Order/Vet Technical Visit data (e.g. VD07 checks a `Vet Technical Visit` exists
  for that specific customer) — writing new portal test data directly onto it risks exactly the
  kind of silent cross-demo idempotency corruption this session's own prior lessons (WEB-03's own
  docstring, AI-DEMO-02's CAPA duplication, etc.) already warn about. It is also a poor semantic
  fit regardless: "VetCare Mekong Dealer Co." is explicitly a DEALER (a `Sales Partner`/reseller,
  matching DEMO 16's own "manufacturer -> regional dealer -> veterinary shop/farm" chain), not the
  FARM customer this master plan item specifically asks for. So WEB-07 gets its OWN 2 farm
  Customers, in the SAME company (Demo Vet Pharma Co.), SAME territory/sales person/item/warehouse
  (genuine reuse of real master data, not a parallel company) but with globally distinct
  names/po_no prefixes (`WEB07-...`) that cannot collide with any `VD0x-...` po_no or customer name
  Golden Demo #10 already uses or asserts against.

FARM DESIGN — one deliberately-within-limit farm, one deliberately-tight-limit farm (same pattern
as WEB-03's Alpha/Beta dealers):
  - "WEB07 Portal Farm Alpha" (a cattle farm) — generous credit limit (10,000,000 VND), used for
    the portal's HAPPY PATH: a real pre-seeded order history and 2 real Technical Visit records
    (one WITH a real product recommendation, one a plain follow-up visit with none — deliberately
    not uniform, since a real field rep doesn't recommend a new product on every single visit).
  - "WEB07 Portal Farm Beta" (a swine farm) — deliberately tight credit limit (2,000,000 VND), used
    to prove the portal's `place_order()` endpoint respects REAL ERPNext credit-limit validation
    (native `Customer.check_credit_limit()`, the exact same mechanism Golden Demo #10's own VD04
    proved), not a hand-rolled imitation of it. Also has 2 real Technical Visit records (same
    with-recommendation / follow-up-only split, tailored to swine rather than cattle).
  Both farms buy the SAME real item Golden Demo #9/#10 already manufactures/distributes,
  `OXYTET-200-INJ` (Oxytetracycline 200mg/mL Injectable Solution) — genuinely indicated for both
  species (Golden Demo #10's own VD07 record already describes it as "withdrawal period and dosing
  for cattle/swine"), so recommending it to a cattle farm AND a swine farm is not a stretch.

PORTAL USER DESIGN — same pattern as WEB-03/04 (dealer_portal_seeds.py/supplier_portal_seeds.py):
  - 2 real, distinct Frappe Users (`farm.alpha.portal@pharmacountry.vn` /
    `farm.beta.portal@pharmacountry.vn`, same demo password convention, `Demo@1234` — a
    placeholder demo credential, documented here and in the portal app's own README, never
    hardcoded into frontend page components).
  - Role: native `Sales User` only (create/submit own Sales Order, read Sales Order — the
    minimum a farm-portal login needs for ordering) plus the new read-only `Vet Technical Visit`
    `Custom DocPerm` `bootstrap_farm_portal_doctypes.py` adds to that SAME native role. Deliberately
    NOT `Stock User` (unlike WEB-03) — this portal never exposes live stock/availability, only the
    farm's own orders/visits/recommendations/service history, so that extra role grant would be
    unused surface area.
  - One `User Permission` per farm user: `allow="Customer"`, `for_value=<their own Customer>`,
    `apply_to_all_doctypes=1` — the SAME mechanism WEB-03/04/10 all already rely on, confirmed here
    to cascade to `Vet Technical Visit` too (a doctype with a top-level `customer` Link field,
    exactly like Sales Order) once the base role read permission exists (see
    `bootstrap_farm_portal_doctypes.py`) — proven empirically, not just asserted, in
    `farm_portal_api.verify_farm_portal_access_control()`.

`farm_portal_api.py`'s own module docstring documents the full authentication design (Frappe
session cookie via native `/api/method/login`, held server-side by the Next.js app, never exposed
to browser JS, identical to WEB-03/04) — this module only concerns itself with the real ERP-side
data/identity fixtures that design depends on.
"""

import frappe
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Vet Pharma Co."
_FG_ITEM = "OXYTET-200-INJ"
_FG_RELEASED = "FG Released - DVP"
_TERRITORY = "Mekong Delta Region"
_SALES_PERSON = "Tran Van Rep (Vet Demo)"

_FARM_CUSTOMER_GROUP = "Veterinary Farm Customers"

_FARM_ALPHA = "WEB07 Portal Farm Alpha"
_FARM_BETA = "WEB07 Portal Farm Beta"
_ALPHA_CREDIT_LIMIT = 10000000
_BETA_CREDIT_LIMIT = 2000000
_FARM_RATE = 220000  # farm/retail rate, deliberately above VD03's 180,000 dealer wholesale rate

_DEMO_USER_DOMAIN = "pharmacountry.vn"
_DEMO_USER_PASSWORD = "Demo@1234"
_ALPHA_USER = f"farm.alpha.portal@{_DEMO_USER_DOMAIN}"
_BETA_USER = f"farm.beta.portal@{_DEMO_USER_DOMAIN}"


# ---------------------------------------------------------------------------
# Master data — 2 isolated farm Customers + portal Users + User Permission
# ---------------------------------------------------------------------------

def _ensure_farm_customer_group():
	if not frappe.db.exists("Customer Group", _FARM_CUSTOMER_GROUP):
		frappe.get_doc(
			{"doctype": "Customer Group", "customer_group_name": _FARM_CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}
		).insert(ignore_permissions=True)
		return True
	return False


def _ensure_farm_customer(name, credit_limit):
	created = False
	if not frappe.db.exists("Customer", {"customer_name": name}):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Individual",
				"customer_group": _FARM_CUSTOMER_GROUP,
				"territory": _TERRITORY,
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


_PORTAL_ROLES = ("Sales User",)


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
	if not frappe.db.exists("User Permission", {"user": email, "allow": "Customer", "for_value": customer}):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Customer", "for_value": customer, "apply_to_all_doctypes": 1}
		).insert(ignore_permissions=True)
		created = True
	return created


def seed_farm_portal_master_data():
	"""WEB-07 master data — 2 isolated farm Customers (Alpha: generous credit limit, happy-path
	demo; Beta: deliberately tight credit limit, credit-block proof), each with exactly one portal
	User restricted via a Customer-scoped User Permission to their own data only."""
	if not frappe.db.exists("Item", _FG_ITEM):
		return "seed_farm_portal_master_data: SKIPPED — run Golden Demo #9's seed_vet_mfg_master_data first."
	if not frappe.db.exists("DocType", "Vet Technical Visit"):
		return "seed_farm_portal_master_data: SKIPPED — run Golden Demo #10's bootstrap_vet_dist_doctypes.run first."
	_ensure_farm_customer_group()
	alpha_created = _ensure_farm_customer(_FARM_ALPHA, _ALPHA_CREDIT_LIMIT)
	beta_created = _ensure_farm_customer(_FARM_BETA, _BETA_CREDIT_LIMIT)
	alpha_user_created = _ensure_portal_user(_ALPHA_USER, "Farm Alpha Portal", _FARM_ALPHA)
	beta_user_created = _ensure_portal_user(_BETA_USER, "Farm Beta Portal", _FARM_BETA)
	return (
		f"seed_farm_portal_master_data: Alpha customer {'created' if alpha_created else 'already existed'} "
		f"(credit_limit={_ALPHA_CREDIT_LIMIT}), Beta customer {'created' if beta_created else 'already existed'} "
		f"(credit_limit={_BETA_CREDIT_LIMIT}). Alpha user {'created' if alpha_user_created else 'already existed'}, "
		f"Beta user {'created' if beta_user_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# Pre-seeded order history (happy path — Alpha) + credit-limit proof (Beta)
# ---------------------------------------------------------------------------

def _ensure_sales_order_and_delivery(customer, qty, po_no):
	existing_so = frappe.db.exists("Sales Order", {"po_no": po_no, "customer": customer, "docstatus": 1})
	if existing_so:
		return existing_so, False, False
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": customer,
			"company": _COMPANY_NAME,
			"territory": _TERRITORY,
			"po_no": po_no,
			"delivery_date": add_days(nowdate(), 7),
			"items": [{"item_code": _FG_ITEM, "qty": qty, "warehouse": _FG_RELEASED, "rate": _FARM_RATE}],
		}
	)
	so.insert(ignore_permissions=True)
	so.submit()

	dn_created = False
	if not frappe.db.exists("Delivery Note", {"against_sales_order": so.name, "docstatus": 1}):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

		dn = make_delivery_note(so.name)
		dn.insert(ignore_permissions=True)
		dn.submit()
		dn_created = True
	return so.name, True, dn_created


def seed_farm_portal_sales_flow():
	"""A real, submitted Sales Order -> Delivery Note (batch/expiry-tracked, same mechanism as
	Golden Demo #10's own VD03) for Farm Alpha (a real, in-limit happy-path order) and a real,
	real, in-limit order for Farm Beta too — its only OTHER order is the deliberate over-limit
	negative test in `seed_farm_portal_credit_test()`."""
	if not frappe.db.exists("Customer", {"customer_name": _FARM_ALPHA}):
		return "seed_farm_portal_sales_flow: SKIPPED — run seed_farm_portal_master_data first."
	alpha_so, alpha_created, alpha_dn = _ensure_sales_order_and_delivery(_FARM_ALPHA, 20, "WEB07-ALPHA-FLOW-1")
	beta_so, beta_created, beta_dn = _ensure_sales_order_and_delivery(_FARM_BETA, 5, "WEB07-BETA-FLOW-1")
	return (
		f"seed_farm_portal_sales_flow: Alpha SO {alpha_so} ({'created' if alpha_created else 'already existed'}, "
		f"DN {'created' if alpha_dn else 'already existed'}). Beta SO {beta_so} "
		f"({'created' if beta_created else 'already existed'}, DN {'created' if beta_dn else 'already existed'})."
	)


def _test_beta_credit_block():
	"""Deliberately over-limit Sales Order for Farm Beta (credit_limit=2,000,000): 15 units at the
	farm rate (3,300,000) is beyond the limit. Native
	erpnext.selling.doctype.customer.customer.check_credit_limit() (same mechanism Golden Demo
	#10's own VD04 and WEB-03's own credit test already proved) must block this at submit."""
	if frappe.db.exists("Sales Order", {"po_no": "WEB07-BETA-CREDIT-TEST", "customer": _FARM_BETA}):
		return True
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _FARM_BETA,
			"company": _COMPANY_NAME,
			"territory": _TERRITORY,
			"po_no": "WEB07-BETA-CREDIT-TEST",
			"delivery_date": add_days(nowdate(), 7),
			"items": [{"item_code": _FG_ITEM, "qty": 15, "warehouse": _FG_RELEASED, "rate": _FARM_RATE}],
		}
	)
	blocked = False
	try:
		so.insert(ignore_permissions=True)
		so.submit()
	except frappe.ValidationError:
		blocked = True
		if so.name and frappe.db.exists("Sales Order", so.name):
			if frappe.db.get_value("Sales Order", so.name, "docstatus") == 1:
				frappe.get_doc("Sales Order", so.name).cancel()
			else:
				frappe.delete_doc("Sales Order", so.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("WEB-07 credit-limit test FAILED: over-credit-limit farm order was not blocked!")
	return True


def seed_farm_portal_credit_test():
	"""The deliberate over-limit negative test for Farm Beta."""
	if not frappe.db.exists("Sales Order", {"customer": _FARM_BETA, "docstatus": 1}):
		return "seed_farm_portal_credit_test: SKIPPED — run seed_farm_portal_sales_flow first."
	blocked = _test_beta_credit_block()
	return f"seed_farm_portal_credit_test: Beta over-limit block={blocked}."


# ---------------------------------------------------------------------------
# Technical visits + real product recommendations — small, honestly-scoped, real
# ---------------------------------------------------------------------------

def _ensure_visit(customer, visit_date, products_discussed, notes, follow_up_date, recommended_item=None):
	if frappe.db.exists("Vet Technical Visit", {"customer": customer, "visit_date": visit_date, "notes": notes}):
		return False
	doc = frappe.get_doc(
		{
			"doctype": "Vet Technical Visit",
			"customer": customer,
			"visit_date": visit_date,
			"sales_person": _SALES_PERSON,
			"products_discussed": products_discussed,
			"notes": notes,
			"follow_up_date": follow_up_date,
		}
	)
	if recommended_item:
		doc.recommended_item = recommended_item
	doc.insert(ignore_permissions=True)
	return True


def seed_farm_portal_technical_visits():
	"""4 real, small, honestly-scoped Technical Visit records (2 per farm) reusing Golden Demo
	#10's own `Vet Technical Visit` DocType (see this module's own docstring for why no new
	DocType was created) — deliberately NOT a large fabricated dataset. One visit per farm carries
	a real structured product recommendation (`recommended_item`); the other is a plain follow-up
	with none, since a real field rep doesn't recommend a new product on every visit."""
	if not frappe.db.exists("Customer", {"customer_name": _FARM_ALPHA}):
		return "seed_farm_portal_technical_visits: SKIPPED — run seed_farm_portal_master_data first."

	created = 0
	if _ensure_visit(
		_FARM_ALPHA,
		add_days(nowdate(), -20),
		"Oxytetracycline 200mg/mL — dosing guidance for cattle mastitis treatment.",
		"Farm reported early mastitis symptoms in 3 cows; discussed treatment protocol and the "
		"withdrawal period required before the next milk/meat sale.",
		add_days(nowdate(), -10),
		recommended_item=_FG_ITEM,
	):
		created += 1
	if _ensure_visit(
		_FARM_ALPHA,
		add_days(nowdate(), -5),
		"",
		"Follow-up visit: farm confirmed the recommended treatment was completed and the "
		"withdrawal period was correctly observed before sale.",
		None,
	):
		created += 1
	if _ensure_visit(
		_FARM_BETA,
		add_days(nowdate(), -15),
		"Oxytetracycline 200mg/mL — respiratory infection control in weaner pigs.",
		"Farm requested a dosing chart for swine; discussed correct dosage per body weight.",
		add_days(nowdate(), 15),
		recommended_item=_FG_ITEM,
	):
		created += 1
	if _ensure_visit(
		_FARM_BETA,
		add_days(nowdate(), -3),
		"",
		"Follow-up visit: farm placed a repeat order after the last visit; confirmed correct "
		"dosing was applied with no adverse reaction.",
		None,
	):
		created += 1
	return f"seed_farm_portal_technical_visits: {created} new visit(s) created (idempotent — 4 total expected)."


def reset_farm_portal_demo_data():
	"""Guided Demo Mode reset for the FARM-PORTAL-TECHNICAL-VISIT scenario. Chains the 3
	genuinely idempotent WEB-07 seed functions above (each independently checks-before-creates —
	confirmed by reading them, not assumed) in their required order. Deliberately does NOT call
	`seed_farm_portal_credit_test()` here — that function is scenario-appropriate for WEB-07's own
	golden-demo build but is a negative-test proof, not part of this guided demo's own steps."""
	return {
		"master_data": seed_farm_portal_master_data(),
		"sales_flow": seed_farm_portal_sales_flow(),
		"technical_visits": seed_farm_portal_technical_visits(),
	}
