"""Golden Demo #25 — Consumer Health / Cosmetics Distribution (master plan DEMO 06, "PHASE 6"
item 6), IP-CONSUMER-DIST. A DISTRIBUTOR/WHOLESALER of TPBVSK (supplement) and cosmetics/personal
care products through a dealer network — NOT a manufacturer. Downstream of Golden Demo #20
(Supplement, VITC-1000-EFF) and Golden Demo #21 (Cosmetics, FACIAL-CLEANSER-150ML), whose finished
Items are reused directly (Item isn't company-scoped) rather than inventing new products; this
Company receives them via its own Material Receipt into its own warehouse and distributes them
onward, matching the "distributor buys finished goods, doesn't make them" narrative.

ZERO new DocTypes and ZERO new Custom Fields — the single most native-reuse-heavy golden demo of
this session (sales/distribution is ERPNext's home turf). Every "special characteristic" in the
master plan maps directly onto stock native ERPNext schema, verified against real source before
writing any code:
- Dealer: plain `Customer` (customer_group "Consumer Health Dealers", customer_type "Company")
  plus a native `Sales Partner` (commission_rate, territory) via `Customer.default_sales_partner`
  — same mechanism as Golden Demo #10 (Veterinary Distribution)'s VD02 dealer.
- Price policy / Customer price list (CD01): native `Price List` + `Item Price`, assigned per
  Customer via `default_price_list`.
- Promotion period (CD02): native `Pricing Rule.valid_from`/`valid_upto`, same mechanism as
  Golden Demo #23 (Pharmacy Chain)'s RX06, this time asserting BOTH edges of the window (a
  Sales Order dated inside gets the discount, one dated after `valid_upto` does not).
- Territory (CD03) + Sales target (no lettered test, part of the "special characteristics" list
  but not one of CD01-06): native `Territory` tree with `territory_manager` + `targets` (Target
  Detail) + `Monthly Distribution`, same pattern as Golden Demo #10's VD01/VD05.
- Dealer credit (CD04): native `Customer.credit_limits` (Customer Credit Limit child table) +
  `Sales Order.check_credit_limit()` / `Sales Invoice.check_credit_limit()`, both calling the
  same `erpnext.selling.doctype.customer.customer.check_credit_limit()`, which throws a plain
  `frappe.throw(...)` — i.e. `frappe.ValidationError`, confirmed by reading the actual source
  (not assumed) before writing the negative test, same class as Golden Demo #2's PD04 and #10's
  VD04.
- Salesperson / Commission report (CD06): native `Sales Team` child table on Sales Order/Sales
  Invoice. Read `erpnext/controllers/selling_controller.py`'s `calculate_contribution()` before
  writing any code: it ALREADY computes `Sales Team.incentives` per row
  (`allocated_amount * commission_rate / 100`, where `allocated_amount` comes from
  `amount_eligible_for_commission * allocated_percentage / 100`) automatically on submit, gated
  only by `Item.grant_commission` (default 0, fetched onto `Sales Order/Invoice Item
  .grant_commission`) being truthy. So CD06 needed no commission math of its own — just
  `Item.grant_commission = 1` on the two reused Items, `sales_team` rows on the Sales Invoices,
  and an aggregate query (`get_consumer_dist_commission_report()` in api.py) summing the
  NATIVE `incentives` field grouped by `sales_person`, the same "thin wrapper over real ledger
  data" idiom as `get_pharmacy_central_dashboard()`.
- Returns (CD05): native `make_return_doc("Delivery Note", ...)`, same mechanism as Golden
  Demo #2's PD05/PD06 (Delivery Note returns, confirmed by reading
  `erpnext/controllers/sales_and_purchase_return.py`'s field-mapping of `batch_no`/
  `serial_and_batch_bundle` from the source doc's own rows — no manual batch correction needed,
  unlike Pharmacy's POS Invoice return which needed the `payments` table patched by hand).
"""

import frappe
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Consumer Distribution Co."
_COMPANY_ABBR = "DCD"
_DC_WAREHOUSE = f"Distribution Center - {_COMPANY_ABBR}"

_VITC_ITEM = "VITC-1000-EFF"  # reused from Golden Demo #20 (Supplement)
_FACIAL_ITEM = "FACIAL-CLEANSER-150ML"  # reused from Golden Demo #21 (Cosmetics)

_DEALER_CUSTOMER_GROUP = "Consumer Health Dealers"
_RETAIL_CUSTOMER_GROUP = "Consumer Health Retail Customers"

_TERRITORY_NORTH = "Northern Vietnam Dealer Territory"
_TERRITORY_SOUTH = "Southern Vietnam Dealer Territory"

_SALES_PERSON_NORTH = "Le Thi Hoa (Consumer Dist Demo)"
_SALES_PERSON_SOUTH = "Pham Van Minh (Consumer Dist Demo)"
_MONTHLY_DISTRIBUTION = "Standard Distribution (Consumer Dist Demo)"

_SALES_PARTNER_HANOI = "Golden Health Hanoi Dealer Network"
_SALES_PARTNER_SAIGON = "Golden Health Saigon Dealer Network"

_DEALER_HANOI = "Golden Health Hanoi Dealer Co."
_DEALER_SAIGON = "Golden Health Saigon Dealer Co."
_RETAIL_CUSTOMER = "Local Wellness Retail Customer"

_DEALER_PRICE_LIST = "Dealer Tier Price List (Consumer Dist Demo)"
_VITC_STANDARD_RATE = 260000
_VITC_DEALER_RATE = 210000
_FACIAL_STANDARD_RATE = 95000  # kept inline on Sales Order rows (not an Item Price), same
# "explicit rate, let the Pricing Rule engine override it" idiom as Pharmacy's RX06 — CD02
# doesn't depend on Item Price resolution at all, only on Pricing Rule validity dates.

_PRICING_RULE_NAME = "Consumer Dist Tet Cosmetics Promotion"
_PROMO_DISCOUNT_PCT = 15

_CREDIT_LIMIT_HANOI = 15000000  # generously above every legitimate Hanoi-dealer transaction in
# this demo (CD01's 2,100,000 + the sales-flow's 4,200,000 = 6,300,000 combined, even allowing
# for a transient double-count between Sales-Order-based and GL-based outstanding during
# invoicing) while CD04's own dedicated test order (150 x 210,000 = 31,500,000) blows past it
# unambiguously — avoids the "one fixed limit can't satisfy both a small legitimate order and a
# blocked oversized one" fragility Golden Demo #2's PD04 comment already warned about.


# ---------------------------------------------------------------------------
# Master data (DP-666)
# ---------------------------------------------------------------------------

def _ensure_company():
	created = False
	if not frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
		created = True
	# cost_center/default_receivable_account/round_off_cost_center aren't reliably
	# auto-populated by Company creation (Cosmetics/Pharmacy/3PL all hit this gap) — checked
	# unconditionally, not only right after creation, so a re-run against an already-existing
	# company still repairs a field that came back empty for any reason.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "default_receivable_account"):
		frappe.db.set_value("Company", _COMPANY_NAME, "default_receivable_account", f"Debtors - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "round_off_cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "round_off_cost_center", f"Main - {_COMPANY_ABBR}")
	return created


def _ensure_warehouse():
	if frappe.db.exists("Warehouse", _DC_WAREHOUSE):
		return False
	frappe.get_doc({"doctype": "Warehouse", "warehouse_name": _DC_WAREHOUSE.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)
	return True


def _ensure_sales_persons():
	created = 0
	for sp in (_SALES_PERSON_NORTH, _SALES_PERSON_SOUTH):
		if not frappe.db.exists("Sales Person", sp):
			frappe.get_doc({"doctype": "Sales Person", "sales_person_name": sp, "is_group": 0, "parent_sales_person": "Sales Team"}).insert(ignore_permissions=True)
			created += 1
	return created


def _ensure_monthly_distribution():
	if frappe.db.exists("Monthly Distribution", _MONTHLY_DISTRIBUTION):
		return False
	months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
	frappe.get_doc(
		{"doctype": "Monthly Distribution", "distribution_id": _MONTHLY_DISTRIBUTION, "fiscal_year": "2026", "percentages": [{"month": m, "percentage_allocation": 100.0 / 12} for m in months]}
	).insert(ignore_permissions=True)
	return True


def _ensure_territories():
	created = 0
	for name, manager, target_qty, target_amount in (
		(_TERRITORY_NORTH, _SALES_PERSON_NORTH, 2000, 400000000),
		(_TERRITORY_SOUTH, _SALES_PERSON_SOUTH, 1500, 300000000),
	):
		if frappe.db.exists("Territory", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Territory",
				"territory_name": name,
				"parent_territory": "All Territories",
				"is_group": 0,
				"territory_manager": manager,
				"targets": [{"item_group": "All Item Groups", "fiscal_year": "2026", "distribution_id": _MONTHLY_DISTRIBUTION, "target_qty": target_qty, "target_amount": target_amount}],
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_customer_groups():
	for name in (_DEALER_CUSTOMER_GROUP, _RETAIL_CUSTOMER_GROUP):
		if not frappe.db.exists("Customer Group", name):
			frappe.get_doc({"doctype": "Customer Group", "customer_group_name": name, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_sales_partners():
	created = 0
	for name, territory in ((_SALES_PARTNER_HANOI, _TERRITORY_NORTH), (_SALES_PARTNER_SAIGON, _TERRITORY_SOUTH)):
		if not frappe.db.exists("Sales Partner", name):
			frappe.get_doc({"doctype": "Sales Partner", "partner_name": name, "territory": territory, "commission_rate": 5}).insert(ignore_permissions=True)
			created += 1
	return created


def _ensure_dealers():
	created = 0
	for name, territory, partner in ((_DEALER_HANOI, _TERRITORY_NORTH, _SALES_PARTNER_HANOI), (_DEALER_SAIGON, _TERRITORY_SOUTH, _SALES_PARTNER_SAIGON)):
		if frappe.db.exists("Customer", {"customer_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": _DEALER_CUSTOMER_GROUP,
				"territory": territory,
				"default_sales_partner": partner,
			}
		).insert(ignore_permissions=True)
		created += 1
	if not frappe.db.exists("Customer", {"customer_name": _RETAIL_CUSTOMER}):
		frappe.get_doc(
			{"doctype": "Customer", "customer_name": _RETAIL_CUSTOMER, "customer_type": "Individual", "customer_group": _RETAIL_CUSTOMER_GROUP, "territory": _TERRITORY_NORTH}
		).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_grant_commission():
	"""CD06 prerequisite — Sales/Sales Invoice Item.grant_commission is fetched from
	Item.grant_commission (default 0). Without this, ERPNext's own native
	calculate_contribution() would compute amount_eligible_for_commission = 0 and every Sales
	Team row's incentives would silently stay 0."""
	changed = 0
	for item_code in (_VITC_ITEM, _FACIAL_ITEM):
		if not frappe.db.get_value("Item", item_code, "grant_commission"):
			frappe.db.set_value("Item", item_code, "grant_commission", 1)
			changed += 1
	return changed


def _ensure_opening_stock():
	"""Guarded on the EXISTENCE of a Stock Ledger Entry in this warehouse for this item, not a
	balance threshold — later steps (sales flow, returns) consume/restore this stock, so a
	balance-based guard would silently re-trigger on every registry re-run once stock is drawn
	down (the exact fragility class called out for this session)."""
	if frappe.db.exists("Stock Ledger Entry", {"warehouse": _DC_WAREHOUSE, "item_code": _VITC_ITEM}):
		return False
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
	se.append("items", {"item_code": _VITC_ITEM, "qty": 500, "t_warehouse": _DC_WAREHOUSE, "use_serial_batch_fields": 1, "basic_rate": 150000})
	se.append("items", {"item_code": _FACIAL_ITEM, "qty": 300, "t_warehouse": _DC_WAREHOUSE, "use_serial_batch_fields": 1, "basic_rate": 60000})
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def seed_consumer_dist_master_data():
	"""DP-666 — Company, Distribution Center warehouse, Sales Persons + Territories (North/South,
	each with a native sales target via Territory.targets), dealer network (Customer Group +
	2 Sales Partners + 2 dealer Customers + 1 retail Customer), grant_commission flag on the 2
	reused Items (CD06 prerequisite), and opening stock received into the Distribution Center."""
	company_created = _ensure_company()
	warehouse_created = _ensure_warehouse()
	sp_created = _ensure_sales_persons()
	_ensure_monthly_distribution()
	territories_created = _ensure_territories()
	_ensure_customer_groups()
	partners_created = _ensure_sales_partners()
	dealers_created = _ensure_dealers()
	grant_commission_changed = _ensure_grant_commission()
	stock_created = _ensure_opening_stock()
	return (
		f"seed_consumer_dist_master_data: Company {'created' if company_created else 'already existed'}. "
		f"Warehouse {'created' if warehouse_created else 'already existed'}. {sp_created} new Sales Person(s). "
		f"{territories_created} new Territory(ies). {partners_created} new Sales Partner(s). {dealers_created} new Customer(s). "
		f"grant_commission set on {grant_commission_changed} Item(s). Opening stock {'received' if stock_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# CD01 — Customer price list (DP-667)
# ---------------------------------------------------------------------------

def _ensure_item_price(item_code, price_list, rate):
	existing = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list, "selling": 1}, ["name", "price_list_rate"], as_dict=True)
	if existing:
		if existing.price_list_rate == rate:
			return False
		frappe.db.set_value("Item Price", existing.name, "price_list_rate", rate)
		return True
	frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": price_list, "selling": 1, "price_list_rate": rate, "currency": "VND"}).insert(ignore_permissions=True)
	return True


def _ensure_dealer_price_list():
	if frappe.db.exists("Price List", _DEALER_PRICE_LIST):
		return False
	frappe.get_doc({"doctype": "Price List", "price_list_name": _DEALER_PRICE_LIST, "selling": 1, "currency": "VND", "enabled": 1}).insert(ignore_permissions=True)
	return True


def seed_consumer_dist_price_policy():
	"""DP-667 — CD01, customer price list. A dedicated Price List for the dealer tier, assigned
	to the Hanoi dealer via Customer.default_price_list, proven against a plain retail Customer
	on Standard Selling: the dealer Sales Order must resolve a lower rate automatically (via
	ERPNext's own price-list resolution during insert/validate, not a hand-set rate) than the
	retail one."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_HANOI}):
		return "seed_consumer_dist_price_policy: SKIPPED — run seed_consumer_dist_master_data first."

	pl_created = _ensure_dealer_price_list()
	_ensure_item_price(_VITC_ITEM, "Standard Selling", _VITC_STANDARD_RATE)
	_ensure_item_price(_VITC_ITEM, _DEALER_PRICE_LIST, _VITC_DEALER_RATE)
	if frappe.db.get_value("Customer", _DEALER_HANOI, "default_price_list") != _DEALER_PRICE_LIST:
		frappe.db.set_value("Customer", _DEALER_HANOI, "default_price_list", _DEALER_PRICE_LIST)

	dealer_so_name = frappe.db.exists("Sales Order", {"po_no": "CD01-DEALER-PRICE-TEST"})
	if not dealer_so_name:
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": _DEALER_HANOI,
				"company": _COMPANY_NAME,
				"selling_price_list": _DEALER_PRICE_LIST,
				"territory": _TERRITORY_NORTH,
				"delivery_date": add_days(nowdate(), 7),
				"po_no": "CD01-DEALER-PRICE-TEST",
				"items": [{"item_code": _VITC_ITEM, "qty": 10, "warehouse": _DC_WAREHOUSE, "grant_commission": 1}],
			}
		)
		so.insert(ignore_permissions=True)
		dealer_rate = so.items[0].rate
		so.submit()
		dealer_so_name = so.name
	else:
		dealer_rate = frappe.db.get_value("Sales Order Item", {"parent": dealer_so_name}, "rate")

	retail_so_name = frappe.db.exists("Sales Order", {"po_no": "CD01-RETAIL-PRICE-TEST"})
	if not retail_so_name:
		so2 = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": _RETAIL_CUSTOMER,
				"company": _COMPANY_NAME,
				"selling_price_list": "Standard Selling",
				"territory": _TERRITORY_NORTH,
				"delivery_date": add_days(nowdate(), 7),
				"po_no": "CD01-RETAIL-PRICE-TEST",
				"items": [{"item_code": _VITC_ITEM, "qty": 5, "warehouse": _DC_WAREHOUSE}],
			}
		)
		so2.insert(ignore_permissions=True)
		retail_rate = so2.items[0].rate
		so2.submit()
		retail_so_name = so2.name
	else:
		retail_rate = frappe.db.get_value("Sales Order Item", {"parent": retail_so_name}, "rate")

	if not (dealer_rate and retail_rate and dealer_rate < retail_rate):
		frappe.throw(f"CD01 FAILED: dealer rate {dealer_rate} is not below retail rate {retail_rate}.")
	return f"seed_consumer_dist_price_policy: Price List {'created' if pl_created else 'already existed'}. CD01 CONFIRMED — dealer rate {dealer_rate} vs retail rate {retail_rate}."


# ---------------------------------------------------------------------------
# CD02 — Promotion period (DP-668)
# ---------------------------------------------------------------------------

def seed_consumer_dist_promotion():
	"""DP-668 — CD02, promotion period. A native Pricing Rule with a valid_from/valid_upto
	window on the cosmetics item, tested on BOTH edges: a Sales Order dated inside the window
	must get the discounted rate, one dated well after valid_upto must NOT (transaction_date is
	the field Pricing Rule validity is checked against for doctypes that have it — confirmed by
	reading erpnext/accounts/doctype/pricing_rule/utils.py before writing this)."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_SAIGON}):
		return "seed_consumer_dist_promotion: SKIPPED — run seed_consumer_dist_master_data first."

	valid_from = add_days(nowdate(), -5)
	valid_upto = add_days(nowdate(), 10)
	rule_created = False
	if not frappe.db.exists("Pricing Rule", {"title": _PRICING_RULE_NAME}):
		frappe.get_doc(
			{
				"doctype": "Pricing Rule",
				"title": _PRICING_RULE_NAME,
				"apply_on": "Item Code",
				"items": [{"item_code": _FACIAL_ITEM}],
				"selling": 1,
				"company": _COMPANY_NAME,
				"currency": "VND",
				"rate_or_discount": "Discount Percentage",
				"discount_percentage": _PROMO_DISCOUNT_PCT,
				"valid_from": valid_from,
				"valid_upto": valid_upto,
			}
		).insert(ignore_permissions=True)
		rule_created = True

	inside_so_name = frappe.db.exists("Sales Order", {"po_no": "CD02-PROMO-INSIDE"})
	if not inside_so_name:
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": _DEALER_SAIGON,
				"company": _COMPANY_NAME,
				"territory": _TERRITORY_SOUTH,
				"transaction_date": nowdate(),
				"delivery_date": add_days(nowdate(), 7),
				"po_no": "CD02-PROMO-INSIDE",
				"items": [{"item_code": _FACIAL_ITEM, "qty": 5, "rate": _FACIAL_STANDARD_RATE, "warehouse": _DC_WAREHOUSE}],
			}
		)
		so.insert(ignore_permissions=True)
		inside_rate = so.items[0].rate
		so.submit()
		inside_so_name = so.name
	else:
		inside_rate = frappe.db.get_value("Sales Order Item", {"parent": inside_so_name}, "rate")

	outside_date = add_days(valid_upto, 30)
	outside_so_name = frappe.db.exists("Sales Order", {"po_no": "CD02-PROMO-OUTSIDE"})
	if not outside_so_name:
		so2 = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": _DEALER_SAIGON,
				"company": _COMPANY_NAME,
				"territory": _TERRITORY_SOUTH,
				"transaction_date": outside_date,
				"delivery_date": add_days(outside_date, 7),
				"po_no": "CD02-PROMO-OUTSIDE",
				"items": [{"item_code": _FACIAL_ITEM, "qty": 5, "rate": _FACIAL_STANDARD_RATE, "warehouse": _DC_WAREHOUSE}],
			}
		)
		so2.insert(ignore_permissions=True)
		outside_rate = so2.items[0].rate
		so2.submit()
		outside_so_name = so2.name
	else:
		outside_rate = frappe.db.get_value("Sales Order Item", {"parent": outside_so_name}, "rate")

	if not (inside_rate and inside_rate < _FACIAL_STANDARD_RATE):
		frappe.throw(f"CD02 FAILED (inside window): rate was {inside_rate}, expected < {_FACIAL_STANDARD_RATE}.")
	if outside_rate != _FACIAL_STANDARD_RATE:
		frappe.throw(f"CD02 FAILED (outside window): rate was {outside_rate}, expected == {_FACIAL_STANDARD_RATE} (no discount).")
	return (
		f"seed_consumer_dist_promotion: Pricing Rule {'created' if rule_created else 'already existed'}. "
		f"CD02 CONFIRMED — inside-window rate {inside_rate} (< {_FACIAL_STANDARD_RATE}), outside-window rate {outside_rate} (== {_FACIAL_STANDARD_RATE})."
	)


# ---------------------------------------------------------------------------
# CD03 — Sales territory (DP-669, no new data — asserts attribution already made by CD01/CD02)
# ---------------------------------------------------------------------------

def seed_consumer_dist_territory_check():
	"""DP-669 — CD03, sales territory. No new seed data of its own: confirms that the Sales
	Orders CD01/CD02 already created were correctly attributed to their dealer's Territory, and
	that the territory-scoped aggregate (get_consumer_dist_territory_sales(), a plain SQL
	aggregate grouped by territory — same idiom as every prior golden demo's dashboard
	function) resolves real, non-zero totals for both territories."""
	from enterprise_core.enterprise_core.api import get_consumer_dist_territory_sales

	hanoi_territory = frappe.db.get_value("Sales Order", {"po_no": "CD01-DEALER-PRICE-TEST"}, "territory")
	saigon_territory = frappe.db.get_value("Sales Order", {"po_no": "CD02-PROMO-INSIDE"}, "territory")
	if not (hanoi_territory and saigon_territory):
		return "seed_consumer_dist_territory_check: SKIPPED — run seed_consumer_dist_price_policy and seed_consumer_dist_promotion first."
	if hanoi_territory != _TERRITORY_NORTH:
		frappe.throw(f"CD03 FAILED: Hanoi dealer Sales Order territory was {hanoi_territory}, expected {_TERRITORY_NORTH}.")
	if saigon_territory != _TERRITORY_SOUTH:
		frappe.throw(f"CD03 FAILED: Saigon dealer Sales Order territory was {saigon_territory}, expected {_TERRITORY_SOUTH}.")
	aggregate = get_consumer_dist_territory_sales()
	territories_with_sales = {row.territory for row in aggregate if row.total_amount}
	if not ({_TERRITORY_NORTH, _TERRITORY_SOUTH} <= territories_with_sales):
		frappe.throw(f"CD03 FAILED: territory-scoped aggregate missing real sales for North/South. Got: {aggregate}")
	return f"seed_consumer_dist_territory_check: CD03 CONFIRMED — Hanoi->{hanoi_territory}, Saigon->{saigon_territory}, aggregate covers both territories."


# ---------------------------------------------------------------------------
# CD04 — Dealer credit (DP-670)
# ---------------------------------------------------------------------------

def _ensure_credit_limit():
	existing_row = frappe.db.get_value("Customer Credit Limit", {"parent": _DEALER_HANOI, "company": _COMPANY_NAME}, ["name", "credit_limit"], as_dict=True)
	if existing_row:
		if existing_row.credit_limit == _CREDIT_LIMIT_HANOI:
			return False
		frappe.db.set_value("Customer Credit Limit", existing_row.name, "credit_limit", _CREDIT_LIMIT_HANOI)
		return True
	customer = frappe.get_doc("Customer", _DEALER_HANOI)
	customer.append("credit_limits", {"company": _COMPANY_NAME, "credit_limit": _CREDIT_LIMIT_HANOI})
	customer.save(ignore_permissions=True)
	return True


def _test_cd04_credit_block():
	"""CD04 negative test. Native ERPNext credit limit check
	(erpnext.selling.doctype.customer.customer.check_credit_limit, called from both
	Sales Order.on_submit and Sales Invoice.on_submit) — confirmed by reading the actual source
	that it raises via a plain frappe.throw(...), i.e. frappe.ValidationError, not a dedicated
	exception subclass, before writing this except clause. 150 units at the dealer rate
	(31,500,000) is deliberately far beyond the 15,000,000 limit even combined with every
	legitimate Hanoi-dealer transaction in this demo."""
	if frappe.db.exists("Sales Order", {"po_no": "CD04-CREDIT-TEST", "customer": _DEALER_HANOI}):
		return True
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DEALER_HANOI,
			"company": _COMPANY_NAME,
			"territory": _TERRITORY_NORTH,
			"delivery_date": add_days(nowdate(), 7),
			"po_no": "CD04-CREDIT-TEST",
			"items": [{"item_code": _VITC_ITEM, "qty": 150, "rate": _VITC_DEALER_RATE, "warehouse": _DC_WAREHOUSE}],
		}
	)
	blocked = False
	try:
		so.insert(ignore_permissions=True)
		so.submit()
	except frappe.ValidationError:
		blocked = True
		# check_credit_limit() throws from inside submit()'s own flow, by which point Frappe
		# may already have flipped docstatus to 1 in this uncommitted transaction even though
		# the save didn't truly succeed (same lesson as Golden Demo #2's PD04) — branch on
		# actual docstatus rather than assuming a blocked submit always leaves a plain draft.
		if so.name and frappe.db.exists("Sales Order", so.name):
			actual_docstatus = frappe.db.get_value("Sales Order", so.name, "docstatus")
			if actual_docstatus == 1:
				frappe.get_doc("Sales Order", so.name).cancel()
			else:
				frappe.delete_doc("Sales Order", so.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("CD04 negative test FAILED: over-credit-limit dealer order was not blocked!")
	return True


def seed_consumer_dist_credit():
	"""DP-670 — CD04, dealer credit. Native Customer Credit Limit + native check_credit_limit()."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_HANOI}):
		return "seed_consumer_dist_credit: SKIPPED — run seed_consumer_dist_master_data first."
	limit_changed = _ensure_credit_limit()
	blocked = _test_cd04_credit_block()
	return f"seed_consumer_dist_credit: Credit limit {'set' if limit_changed else 'already correct'} ({_CREDIT_LIMIT_HANOI}). CD04 CONFIRMED credit-limit-block={blocked}."


# ---------------------------------------------------------------------------
# Sales flow — warehouse -> delivery -> receivable, with commission attribution (DP-671)
# ---------------------------------------------------------------------------

def _ensure_sales_flow(customer, territory, item_code, qty, rate, sales_person, po_no):
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

	so_name = frappe.db.exists("Sales Order", {"po_no": po_no})
	if not so_name:
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer,
				"company": _COMPANY_NAME,
				"territory": territory,
				"delivery_date": add_days(nowdate(), 5),
				"po_no": po_no,
				"items": [{"item_code": item_code, "qty": qty, "rate": rate, "warehouse": _DC_WAREHOUSE, "grant_commission": 1}],
				"sales_team": [{"sales_person": sales_person, "allocated_percentage": 100, "commission_rate": 5}],
			}
		)
		so.insert(ignore_permissions=True)
		so.submit()
		so_name = so.name

	# Scoped via _find_original_delivery_note (defined below) rather than a raw
	# {"against_sales_order": so_name} lookup — once a return exists against this SO's own
	# Delivery Note, the return's rows ALSO carry against_sales_order=so_name (make_return_doc
	# copies it forward), so an unscoped query is ambiguous and can pick the return itself.
	# Real bug found live: on a registry re-run after CD05's return existed, this exact
	# unscoped lookup picked the return Delivery Note, made dn_name falsy-but-truthy correct
	# name yet wrong document, found no Sales Invoice against IT, and created a bogus new
	# Sales Invoice FROM THE RETURN (negative qty/amount), silently corrupting the CD06
	# commission totals — caught by a manual idempotency re-run, not by any single seed step's
	# own self-report.
	dn_name = _find_original_delivery_note(so_name)
	if not dn_name:
		dn = make_delivery_note(so_name)
		dn.insert(ignore_permissions=True)
		dn.submit()
		dn_name = dn.name

	si_name = frappe.db.get_value("Sales Invoice Item", {"delivery_note": dn_name}, "parent")
	if not si_name:
		si = make_sales_invoice(dn_name)
		if not si.get("sales_team"):
			si.append("sales_team", {"sales_person": sales_person, "allocated_percentage": 100, "commission_rate": 5})
		for row in si.items:
			row.grant_commission = 1
		si.insert(ignore_permissions=True)
		si.submit()
		si_name = si.name

	return so_name, dn_name, si_name


def seed_consumer_dist_sales_flow():
	"""DP-671 — the user guide's "sales order -> warehouse -> delivery -> receivable" chain for
	both dealers, with native Sales Team commission attribution feeding CD06. Hanoi's Delivery
	Note is the one CD05's return will be filed against."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_HANOI}):
		return "seed_consumer_dist_sales_flow: SKIPPED — run seed_consumer_dist_master_data first."

	hanoi_so, hanoi_dn, hanoi_si = _ensure_sales_flow(
		_DEALER_HANOI, _TERRITORY_NORTH, _VITC_ITEM, 20, _VITC_DEALER_RATE, _SALES_PERSON_NORTH, "CD05-FLOW-HANOI"
	)
	saigon_so, saigon_dn, saigon_si = _ensure_sales_flow(
		_DEALER_SAIGON, _TERRITORY_SOUTH, _FACIAL_ITEM, 30, _FACIAL_STANDARD_RATE, _SALES_PERSON_SOUTH, "FLOW-SAIGON"
	)
	return f"seed_consumer_dist_sales_flow: Hanoi SO/DN/SI = {hanoi_so}/{hanoi_dn}/{hanoi_si}. Saigon SO/DN/SI = {saigon_so}/{saigon_dn}/{saigon_si}."


# ---------------------------------------------------------------------------
# CD05 — Return linked original lot (DP-672)
# ---------------------------------------------------------------------------

def _find_original_delivery_note(sales_order):
	"""Scoped lookup — once a return exists, its own rows ALSO carry
	against_sales_order=sales_order (make_return_doc copies it forward), so an unscoped query
	on Delivery Note Item alone is ambiguous and can pick the return itself instead of the
	original (found live: `against_sales_order` query returned the return DN on a re-run,
	the same class of "unscoped lookup grabs the wrong document" bug this session's lessons
	warn about for Batch lookups). Explicitly excludes is_return=1 via a join on the parent."""
	rows = frappe.db.sql(
		"""select dni.parent from `tabDelivery Note Item` dni
		inner join `tabDelivery Note` dn on dn.name = dni.parent
		where dni.against_sales_order = %s and dn.is_return = 0 and dn.docstatus = 1
		order by dn.creation asc limit 1""",
		(sales_order,),
	)
	return rows[0][0] if rows else None


def _ensure_return():
	hanoi_so = frappe.db.get_value("Sales Order", {"po_no": "CD05-FLOW-HANOI"}, "name")
	if not hanoi_so:
		return False, None
	original_dn = _find_original_delivery_note(hanoi_so)
	if not original_dn:
		return False, None
	if frappe.db.exists("Delivery Note", {"return_against": original_dn, "docstatus": 1}):
		return False, original_dn

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dn_return = make_return_doc("Delivery Note", original_dn)
	# 4 of the 20 delivered units come back — make_return_doc's own field mapping carries the
	# SAME batch_no/serial_and_batch_bundle from the source row forward (confirmed by reading
	# sales_and_purchase_return.py before relying on this), so no manual batch correction is
	# needed here, unlike Pharmacy's POS Invoice return which needed its payments table patched.
	dn_return.items[0].qty = -4
	dn_return.insert(ignore_permissions=True)
	dn_return.submit()
	return True, original_dn


def seed_consumer_dist_return():
	"""DP-672 — CD05, return linked original lot. A partial return against Hanoi's real
	Delivery Note from the sales flow, via ERPNext's native make_return_doc()."""
	if not frappe.db.exists("Sales Order", {"po_no": "CD05-FLOW-HANOI", "docstatus": 1}):
		return "seed_consumer_dist_return: SKIPPED — run seed_consumer_dist_sales_flow first."
	return_created, against_dn = _ensure_return()
	if not against_dn:
		frappe.throw("CD05 FAILED: could not find the original Delivery Note to return against.")
	original_batch = frappe.db.get_value("Delivery Note Item", {"parent": against_dn}, "batch_no")
	return_dn = frappe.db.get_value("Delivery Note", {"return_against": against_dn, "docstatus": 1}, "name")
	return_batch = frappe.db.get_value("Delivery Note Item", {"parent": return_dn}, "batch_no")
	if not (original_batch and original_batch == return_batch):
		frappe.throw(f"CD05 FAILED: return batch {return_batch} does not match the original delivery's batch {original_batch}.")
	return f"seed_consumer_dist_return: Return {'created' if return_created else 'already existed'} against {against_dn}. CD05 CONFIRMED — same batch {original_batch} on both sides."


# ---------------------------------------------------------------------------
# CD06 — Commission report + sales dashboard (DP-673)
# ---------------------------------------------------------------------------

def seed_consumer_dist_dashboard():
	"""DP-673 — CD06, commission report, plus the user guide's final "sales dashboard" step. No
	seed action of its own: just confirms the aggregate queries in api.py resolve real,
	non-zero data (native Sales Team.incentives summed per Sales Person)."""
	from enterprise_core.enterprise_core.api import get_consumer_dist_commission_report, get_consumer_dist_sales_dashboard

	if not frappe.db.exists("Sales Invoice", {"company": _COMPANY_NAME, "docstatus": 1}):
		return "seed_consumer_dist_dashboard: SKIPPED — run seed_consumer_dist_sales_flow first."

	commission = get_consumer_dist_commission_report()
	persons_with_commission = {row.sales_person for row in commission if row.total_commission}
	if not ({_SALES_PERSON_NORTH, _SALES_PERSON_SOUTH} <= persons_with_commission):
		frappe.throw(f"CD06 FAILED: commission report missing real commission for both Sales Persons. Got: {commission}")

	dashboard = get_consumer_dist_sales_dashboard()
	if not dashboard.get("stock_by_item"):
		frappe.throw("Sales dashboard FAILED: no stock data resolved for the Distribution Center.")
	return f"seed_consumer_dist_dashboard: CD06 CONFIRMED — commission report + sales dashboard resolve real data for both Sales Persons. {commission}"


# ---------------------------------------------------------------------------
# Catalog expansion (P2 post-launch reviewer fix, NOT a master-plan DP item) — this is the
# SINGLE company WEB-01 (catalog.pharmacountry.vn) and WEB-05 (shop.pharmacountry.vn) actually
# read from (see public_api.py/b2c_commerce_api.py's own `_safe_item_codes()` — a real, live
# SQL join requiring BOTH a real Stock Ledger Entry for this company AND a real selling Item
# Price on "Standard Selling"; no hardcoded item_code list anywhere in either frontend). A
# reviewer correctly flagged both public sites as looking too thin (2 products, no category
# breadth) because this Company had only ever received 2 finished goods. This function
# receives the SAME way the golden demo's own DP-666 already established (a fresh Material
# Receipt into the Distribution Center, no reference back to the manufacturer's own batch —
# Item isn't company-scoped, so this Company can receive/resell a finished good it never
# itself made) for 6 new REAL finished goods reused from Golden Demo #20 (5 new supplement
# products, supplement_seeds.py's seed_supplement_catalog_expansion()) and Golden Demo #21 (1
# new cosmetic, cosmetics_seeds.py's seed_cosmetics_catalog_expansion()) — run those two seed
# functions on this same site FIRST so these Items actually exist before this one runs.
#
# Real, honest category grouping for WEB-05's "3-4 categories" ask — grounded in what each
# item actually is, not an invented label: "Vitamins" (VITC-1000-EFF, VITD3-1000-SG,
# MULTIVIT-COMP-TAB), "Minerals & Specialty Supplements" (ZINC-50-TAB, OMEGA3-1000-SG,
# PROBIOTIC-10B-CAP), "Skincare" (FACIAL-CLEANSER-150ML, FACIAL-TONER-200ML) — 8 products
# across 3 real categories total once this runs, up from 2 products / 0 category breadth.
# ---------------------------------------------------------------------------

_EXPANSION_ITEMS = {
	# item_code: (receive_qty, receive_basic_rate, selling_price_list_rate)
	"VITD3-1000-SG": (300, 180000, 300000),
	"ZINC-50-TAB": (250, 90000, 150000),
	"MULTIVIT-COMP-TAB": (280, 140000, 230000),
	"OMEGA3-1000-SG": (260, 200000, 330000),
	"PROBIOTIC-10B-CAP": (200, 220000, 360000),
	"FACIAL-TONER-200ML": (350, 45000, 75000),
}


def seed_consumer_dist_catalog_expansion():
	"""P2 catalog-widening fix — receives 6 new real finished goods (5 supplement + 1
	cosmetics, reused from Golden Demo #20/#21, Item isn't company-scoped) into the
	Distribution Center via a real Material Receipt, and gives each a real selling Item Price
	on the public "Standard Selling" price list — the exact 2 real, data-driven conditions
	WEB-01's/WEB-05's own `_safe_item_codes()` queries require. Guarded per-item on Stock
	Ledger Entry EXISTENCE (this session's own established idempotency lesson), never a
	balance, so a later order/return against one of these items can never re-trigger a
	duplicate receipt."""
	if not frappe.db.exists("Company", _COMPANY_NAME):
		return "seed_consumer_dist_catalog_expansion: SKIPPED — run seed_consumer_dist_master_data first."

	missing_items = [code for code in _EXPANSION_ITEMS if not frappe.db.exists("Item", code)]
	if missing_items:
		return f"seed_consumer_dist_catalog_expansion: SKIPPED — Item(s) not found yet, run seed_supplement_catalog_expansion/seed_cosmetics_catalog_expansion on this site first: {missing_items}"

	receipts_created = 0
	prices_created = 0
	for item_code, (qty, basic_rate, sell_rate) in _EXPANSION_ITEMS.items():
		if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _DC_WAREHOUSE, "item_code": item_code}):
			se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt", "company": _COMPANY_NAME})
			se.append("items", {"item_code": item_code, "qty": qty, "t_warehouse": _DC_WAREHOUSE, "use_serial_batch_fields": 1, "basic_rate": basic_rate})
			se.insert(ignore_permissions=True)
			se.submit()
			receipts_created += 1
		if _ensure_item_price(item_code, "Standard Selling", sell_rate):
			prices_created += 1

	return f"seed_consumer_dist_catalog_expansion: {receipts_created} new Material Receipt(s), {prices_created} Item Price row(s) set/confirmed on Standard Selling, across {len(_EXPANSION_ITEMS)} item(s)."
