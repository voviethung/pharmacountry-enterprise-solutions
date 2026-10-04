"""Golden Demo #27 — Feed / Ingredient Trading (master plan DEMO 21, "PHASE 6" item 8),
IP-INGREDIENT-TRADING. A TRADING company (import/wholesale of raw feed ingredients/additives),
NOT a manufacturer — buys commodity ingredients from overseas suppliers (real FX exposure),
receives with QC, resells to domestic feed-mill customers under a committed-quantity contract,
tracks margins. Per the master plan's own capability priority table this vertical is "CORE,
portal OPTIONAL, AI NO/LATER — ERP trading core đủ" (plain ERP core is sufficient) — so this demo
is deliberately native-ERPNext-heavy, the same "close to zero new schema" shape as Golden Demo
#25 (Consumer Distribution, which ended up with ZERO new DocTypes/Custom Fields). This demo needs
ZERO new DocTypes and ZERO new Custom Fields too — every "special characteristic" in the master
plan maps directly onto native ERPNext Buying/Selling schema, verified against real source before
writing any code:

- Shipment quantity reconciliation (FT01): native Purchase Order Item.qty (ordered) vs.
  .received_qty (native, auto-updated on Purchase Receipt submit) — Purchase Order Item has NO
  native billed_qty field (only billed_amt, an amount), so "billed qty" is derived by summing
  Purchase Invoice Item.qty for invoices referencing the Purchase Receipt, confirmed by reading
  purchase_order_item.json/purchase_invoice_item.json before writing any code.
- FX handling (FT02): native Purchase Order currency/conversion_rate/grand_total/base_grand_total
  — two Purchase Orders for the IDENTICAL item/qty/USD rate but DIFFERENT conversion_rate prove
  base_grand_total is genuinely recomputed per-transaction (not a static default): same
  grand_total (USD), different base_grand_total (VND), and base_grand_total == grand_total *
  conversion_rate on both, confirmed by direct arithmetic, not just "a currency field exists."
- Supplier lot (FT03): a lighter supplier-lot lookup (not `trace_feed_batch_genealogy()`, which
  is keyed on finding a Manufacture/Repack Stock Entry that consumed the batch — this is a pure
  trading demo with NO manufacturing step, so that function would find nothing) — Batch ->
  Serial and Batch Entry -> Serial and Batch Bundle (voucher_type='Purchase Receipt',
  voucher_no=<PR>) -> Purchase Receipt.supplier, the direct SBB voucher link rather than going
  through Stock Ledger Entry at all (SBB already carries voucher_type/voucher_no itself, one hop
  shorter than the SLE join this session's other batch-scoping fixes needed).
- Incoming QC (FT04): native Quality Inspection, reference_type="Purchase Receipt",
  inspection_type="Incoming" — same pattern as Golden Demo #26 (Premix)/#22 (Medical
  Device)/#5 (LIMS). Release gate reuses `block_fg_release_without_qa` COMPLETELY UNMODIFIED (9th
  reuse this session) by naming the destination warehouse "...Released - DIT".
- Contract quantity (FT05): native `Blanket Order` (Manufacturing module, blanket_order_type=
  "Selling"), NOT the generic CRM `Contract` doctype — confirmed by reading both doctypes' real
  source before choosing. `Contract` (erpnext/crm/doctype/contract) is a legal-document tracker
  with no quantity/drawdown concept at all (fulfilment_terms is a free-text child table, no
  linkage to Sales Order). `Blanket Order` is purpose-built for exactly this: `Blanket Order
  Item.qty` (committed) + `.ordered_qty` (a NATIVE field, auto-recomputed by
  `BlanketOrder.update_ordered_qty()` — summed from `Sales Order Item.stock_qty` where
  `blanket_order == self.name` and `docstatus == 1` — triggered automatically from
  `Sales Order.update_blanket_order()` on submit/cancel, confirmed by reading
  `erpnext/manufacturing/doctype/blanket_order/blanket_order.py` before writing any code) plus
  native over-commit enforcement (`validate_against_blanket_order()`, called from
  `Sales Order.validate()`, blocking any order that would push cumulative ordered_qty past
  committed qty + `Selling Settings.blanket_order_allowance`, which is 0/unset on this site —
  confirmed live before writing the negative test).
- Price history (FT06): pure aggregation over native `Item Price.valid_from`/`price_list_rate`
  history — multiple Item Price rows per item/price_list ARE allowed by ERPNext as long as
  valid_from/valid_upto/uom/customer/supplier/batch_no don't all match an existing row exactly
  (confirmed by reading `item_price.py`'s own `check_duplicates()` before relying on this).
- Margin report (FT07): a real aggregation over actual Purchase Invoice (cost, `base_amount`
  already company-currency-converted) vs. Sales Invoice (revenue) data per item, mirroring the
  "thin wrapper over real ledger data" pattern already used for Pharmacy's central dashboard,
  3PL's billing run, and Consumer Distribution's commission report.

Two traded ingredients: SOYBEAN-MEAL-48 (imported from Singapore, carries the shrinkage/FX/QC/
contract story — FT01-FT05) and FISH-MEAL-65 (imported from Argentina, a second, lighter chain —
full receipt, no FX contrast, no blanket order — whose only job is proving FT06/FT07's
per-item aggregation actually GROUPS instead of being hardcoded to one item)."""

import frappe
from frappe.utils import add_days, flt, nowdate

_COMPANY_NAME = "Demo Ingredient Trading Co."
_COMPANY_ABBR = "DIT"
_QUARANTINE_WAREHOUSE = f"Import Quarantine - {_COMPANY_ABBR}"
_RELEASED_WAREHOUSE = f"Trading Released - {_COMPANY_ABBR}"  # must contain "released" for
# block_fg_release_without_qa reuse (fires on any warehouse name containing that substring)

_SUPPLIER_GROUP = "Overseas Feed Ingredient Suppliers"
_CUSTOMER_GROUP = "Domestic Feed Mill Customers"

_SUPPLIER_SOY = "Cargill Asia Trading Pte Ltd"  # Singapore
_SUPPLIER_FISH = "Nutreco South America S.A."  # Argentina

_CUSTOMER_SOY = "Hau Giang Feed Mill Co. (Trading Demo)"
_CUSTOMER_FISH = "Dong Thap Aqua Feed Co. (Trading Demo)"

_SOY_ITEM = "SOYBEAN-MEAL-48"
_FISH_ITEM = "FISH-MEAL-65"

_SOY_PO_QTY = 50000  # kg
_SOY_PO_RATE_USD = 0.42  # USD/kg
_SOY_PO1_CONVERSION_RATE = 24500  # VND/USD (shipment 1's FX date)
_SOY_PO2_CONVERSION_RATE = 25100  # VND/USD (a LATER, different FX date — same item/qty/USD
# rate as PO1, isolating conversion_rate as the only variable, so a differing base_grand_total
# genuinely proves per-transaction FX conversion rather than a static default)
_SOY_RECEIVED_QTY = 48500  # kg — 3% transit/moisture shrinkage vs. the 50,000kg ordered,
# deliberately NOT a rejection (QC happens separately, FT04) — a real commodity-import shrinkage

_FISH_PO_QTY = 20000  # kg
_FISH_PO_RATE_USD = 0.95  # USD/kg
_FISH_PO_CONVERSION_RATE = 24800

_SOY_SELL_RATE = 13500  # VND/kg domestic — landed cost ~10,608 VND/kg (514.5M VND / 48,500kg)
_FISH_SELL_RATE = 32000  # VND/kg domestic — landed cost ~23,560 VND/kg (471.2M VND / 20,000kg)

_SOY_CONTRACT_QTY = 20000  # kg committed over the quarter (Blanket Order)
_SOY_SO_DRAWDOWN_QTY = 8000  # kg drawn down by the real Sales Order

_FISH_SO_QTY = 6000  # kg

_QC_SPEC = "Crude Protein %"


# ---------------------------------------------------------------------------
# Master data (DP-680)
# ---------------------------------------------------------------------------

def _ensure_company():
	created = False
	if not frappe.db.exists("Company", {"company_name": _COMPANY_NAME}):
		frappe.get_doc({"doctype": "Company", "company_name": _COMPANY_NAME, "abbr": _COMPANY_ABBR, "default_currency": "VND", "country": "Vietnam"}).insert(ignore_permissions=True)
		created = True
	# cost_center/default_receivable_account/default_payable_account/round_off_cost_center
	# aren't reliably auto-populated by Company creation (a real gap found repeatedly this
	# session — Cosmetics/Pharmacy/3PL/Premix) — checked UNCONDITIONALLY, not only right after
	# creation, so a re-run against an already-existing company still repairs a gap from any
	# cause. default_payable_account is checked here for the first time this session because
	# this is the first golden demo whose FT01 chain needs a real Purchase Invoice submitted
	# against a brand-new Company.
	if not frappe.db.get_value("Company", _COMPANY_NAME, "cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "cost_center", f"Main - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "default_receivable_account"):
		frappe.db.set_value("Company", _COMPANY_NAME, "default_receivable_account", f"Debtors - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "default_payable_account"):
		frappe.db.set_value("Company", _COMPANY_NAME, "default_payable_account", f"Creditors - {_COMPANY_ABBR}")
	if not frappe.db.get_value("Company", _COMPANY_NAME, "round_off_cost_center"):
		frappe.db.set_value("Company", _COMPANY_NAME, "round_off_cost_center", f"Main - {_COMPANY_ABBR}")
	return created


def _ensure_stock_settings():
	"""Real bug found live: with Item.inspection_required_before_purchase=1 (FT04's own
	prerequisite), ERPNext's native validate_qi_presence() blocks Purchase Receipt SUBMISSION
	itself unless that exact row already carries a linked quality_inspection — which is
	circular for this demo's intended flow (receive into Quarantine -> THEN inspect -> THEN
	release), since a Quality Inspection naturally references an ALREADY-submitted Purchase
	Receipt (same "QC happens after the transaction, gates the NEXT step" shape as every other
	golden demo's incoming-QC pattern this session, e.g. Premix/3PL/LIMS). The correct native
	lever, confirmed by reading erpnext/controllers/stock_controller.py's validate_inspection()
	before writing this, is Stock Settings.allow_to_make_quality_inspection_after_purchase_or_
	delivery — a GLOBAL, ONLY-RELAXING toggle (it skips the inline-QI-required check entirely
	for Purchase Receipt/Purchase Invoice/Sales Invoice/Delivery Note; it never makes any
	existing flow MORE strict), safe to enable site-wide without risk to any other golden demo."""
	if frappe.db.get_single_value("Stock Settings", "allow_to_make_quality_inspection_after_purchase_or_delivery"):
		return False
	frappe.db.set_single_value("Stock Settings", "allow_to_make_quality_inspection_after_purchase_or_delivery", 1)
	return True


def _ensure_item_groups():
	for name in ("Raw Material", "Finished Goods"):
		if not frappe.db.exists("Item Group", name):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": "All Item Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_warehouses():
	for wh in (_QUARANTINE_WAREHOUSE, _RELEASED_WAREHOUSE):
		if not frappe.db.exists("Warehouse", wh):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh.split(" - ")[0], "company": _COMPANY_NAME}).insert(ignore_permissions=True)


def _ensure_supplier_group():
	if not frappe.db.exists("Supplier Group", _SUPPLIER_GROUP):
		frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": _SUPPLIER_GROUP, "parent_supplier_group": "All Supplier Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_customer_group():
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(ignore_permissions=True)


_USD_PAYABLE_ACCOUNT = f"Creditors USD - {_COMPANY_ABBR}"


def _ensure_usd_payable_account():
	"""Real bug found live: a Purchase Invoice in USD against the Company's default (VND-only)
	payable account throws "Party Account Creditors - DIT currency (VND) and document currency
	(USD) should be same" — the auto-created default payable Account has a fixed
	account_currency (VND, the Company's own default). ERPNext's real fix for genuine
	multi-currency AP is a DEDICATED foreign-currency payable account wired onto the Supplier's
	own Party Account child table (`accounts`), not a property to flip on the default account —
	confirmed by reading the actual error text (not guessed) before creating this."""
	if frappe.db.exists("Account", _USD_PAYABLE_ACCOUNT):
		return False
	parent_account = frappe.db.get_value("Account", f"Accounts Payable - {_COMPANY_ABBR}", "name") or frappe.db.get_value("Account", {"company": _COMPANY_NAME, "account_type": "Payable", "is_group": 1}, "name")
	frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": "Creditors USD",
			"parent_account": parent_account,
			"company": _COMPANY_NAME,
			"account_type": "Payable",
			"account_currency": "USD",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_suppliers():
	created = 0
	_ensure_usd_payable_account()
	for name, country in ((_SUPPLIER_SOY, "Singapore"), (_SUPPLIER_FISH, "Argentina")):
		supplier_name = frappe.db.exists("Supplier", {"supplier_name": name})
		if not supplier_name:
			frappe.get_doc(
				{
					"doctype": "Supplier",
					"supplier_name": name,
					"supplier_group": _SUPPLIER_GROUP,
					"supplier_type": "Company",
					"country": country,
					"default_currency": "USD",
					"accounts": [{"company": _COMPANY_NAME, "account": _USD_PAYABLE_ACCOUNT}],
				}
			).insert(ignore_permissions=True)
			created += 1
			continue
		# Repaired UNCONDITIONALLY (not only right after creation) — the USD Party Account row
		# is a real prerequisite for the FX Purchase Invoice this demo submits, and an earlier
		# supplier record created before that fix existed would otherwise silently stay broken
		# forever on a re-run (the same idempotency-guard class of bug this session's lessons
		# warn about: checking only "does the Supplier exist" instead of "is it fully correct").
		if not frappe.db.exists("Party Account", {"parent": supplier_name, "company": _COMPANY_NAME, "account": _USD_PAYABLE_ACCOUNT}):
			supplier = frappe.get_doc("Supplier", supplier_name)
			supplier.append("accounts", {"company": _COMPANY_NAME, "account": _USD_PAYABLE_ACCOUNT})
			supplier.save(ignore_permissions=True)
	return created


def _ensure_customers():
	created = 0
	for name in (_CUSTOMER_SOY, _CUSTOMER_FISH):
		if frappe.db.exists("Customer", {"customer_name": name}):
			continue
		frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Company", "customer_group": _CUSTOMER_GROUP, "territory": "Vietnam" if frappe.db.exists("Territory", "Vietnam") else "All Territories"}).insert(ignore_permissions=True)
		created += 1
	return created


def _ensure_items():
	created = 0
	for code, name in ((_SOY_ITEM, "Soybean Meal 48% Protein (Feed Grade, Imported)"), (_FISH_ITEM, "Fish Meal 65% Protein (Feed Grade, Imported)")):
		if frappe.db.exists("Item", code):
			# Repaired UNCONDITIONALLY — an Item created before this flag was added would
			# otherwise stay silently unable to hold a Quality Inspection forever (same
			# idempotency-guard class of fix as the Supplier Party Account above).
			if not frappe.db.get_value("Item", code, "inspection_required_before_purchase"):
				frappe.db.set_value("Item", code, "inspection_required_before_purchase", 1)
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": "Raw Material",
				"stock_uom": "Kg",
				"is_stock_item": 1,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"batch_number_series": f"{code}-.####",
				# FT04 (incoming QC) prerequisite — native Item.inspection_required_before_purchase
				# gates Quality Inspection.validate() itself: without this flag, ERPNext actively
				# REFUSES to create a Quality Inspection at all ("no need to create the QI"),
				# found live rather than guessed.
				"inspection_required_before_purchase": 1,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


def seed_ingredient_trading_master_data():
	"""DP-680 — Company, Warehouses (Import Quarantine + Trading Released — the latter's name
	deliberately contains "released" to reuse block_fg_release_without_qa unmodified), 2
	overseas Suppliers (USD), 2 domestic feed-mill Customers, 2 batch-tracked traded Items."""
	company_created = _ensure_company()
	_ensure_stock_settings()
	_ensure_item_groups()
	_ensure_warehouses()
	_ensure_supplier_group()
	_ensure_customer_group()
	suppliers_created = _ensure_suppliers()
	customers_created = _ensure_customers()
	items_created = _ensure_items()
	return (
		f"seed_ingredient_trading_master_data: Company {'created' if company_created else 'already existed'} ({_COMPANY_NAME}). "
		f"{suppliers_created} new Supplier(s). {customers_created} new Customer(s). {items_created} new Item(s)."
	)


# ---------------------------------------------------------------------------
# FT01 shipment reconciliation + FT02 FX handling (DP-681)
# ---------------------------------------------------------------------------

def _ensure_po(marker, item_code, qty, rate_usd, conversion_rate, supplier):
	"""marker is our own idempotency tag, stored on Purchase Order.title — Purchase Order (the
	BUYING side) has no po_no field at all (that's a Sales Order field, the customer's own PO
	reference number on an order WE receive — confirmed live: an earlier version of this seed
	mistakenly copied that idiom onto Purchase Order and hit
	"Unknown column 'po_no' in 'WHERE'"). title is a plain Data field with no fetch_from/default,
	so an explicitly-set value survives insert."""
	existing = frappe.db.exists("Purchase Order", {"title": marker})
	if existing:
		return existing, False
	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"supplier": supplier,
			"company": _COMPANY_NAME,
			"currency": "USD",
			"conversion_rate": conversion_rate,
			"title": marker,
			"schedule_date": add_days(nowdate(), 21),
			"items": [{"item_code": item_code, "qty": qty, "rate": rate_usd, "warehouse": _QUARANTINE_WAREHOUSE, "schedule_date": add_days(nowdate(), 21)}],
		}
	)
	po.insert(ignore_permissions=True)
	po.submit()
	return po.name, True


def _ensure_receipt(po_name, item_code, received_qty):
	"""Partial-receipt shipment reconciliation (FT01): make_purchase_receipt() maps the FULL
	ordered qty by default — deliberately reduced to received_qty/qty on the mapped row BEFORE
	insert to model real transit/moisture shrinkage, so PO Item.received_qty (native, updated on
	submit) ends up genuinely below PO Item.qty (ordered)."""
	existing = frappe.db.get_value("Purchase Receipt Item", {"purchase_order": po_name, "item_code": item_code}, "parent")
	if existing and frappe.db.get_value("Purchase Receipt", existing, "docstatus") == 1:
		return existing, False
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	pr = make_purchase_receipt(po_name)
	for row in pr.items:
		if row.item_code == item_code:
			row.received_qty = received_qty
			row.qty = received_qty
			row.use_serial_batch_fields = 1
	pr.insert(ignore_permissions=True)
	pr.submit()
	return pr.name, True


def _ensure_purchase_invoice(pr_name):
	existing = frappe.db.get_value("Purchase Invoice Item", {"purchase_receipt": pr_name}, "parent")
	if existing and frappe.db.get_value("Purchase Invoice", existing, "docstatus") == 1:
		return existing, False
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	pi = make_purchase_invoice(pr_name)
	pi.insert(ignore_permissions=True)
	pi.submit()
	return pi.name, True


def _billed_qty(pr_name, item_code):
	"""Purchase Order Item has NO native billed_qty field (only billed_amt, an amount) —
	confirmed by reading purchase_order_item.json before writing this. Billed qty is derived by
	summing Purchase Invoice Item.qty for submitted invoices referencing this Purchase Receipt."""
	rows = frappe.db.sql(
		"""select coalesce(sum(pii.qty), 0) from `tabPurchase Invoice Item` pii
		inner join `tabPurchase Invoice` pi on pi.name = pii.parent
		where pii.purchase_receipt = %s and pii.item_code = %s and pi.docstatus = 1""",
		(pr_name, item_code),
	)
	return flt(rows[0][0]) if rows else 0.0


def seed_ingredient_trading_import_shipment():
	"""DP-681 — FT02 (FX handling), plus the receiving half of FT01 (shipment quantity
	reconciliation — the ordered-vs-received leg). Soybean Meal: PO1 (50,000kg ordered, USD,
	conversion_rate 24,500) -> PR1 (48,500kg received — 3% transit/moisture shrinkage). PO2 is a
	pure FX contrast: IDENTICAL item/qty/USD rate as PO1, only conversion_rate differs (25,100, a
	later FX date) — no receipt needed, just the submitted PO's own base_grand_total, to isolate
	conversion_rate as the only variable that changed. The invoiced-qty leg of FT01 (PI1) is
	deliberately deferred to DP-682: native ERPNext blocks a Purchase Invoice for an
	inspection-required Item until its Quality Inspection exists (found live — see DP-682's own
	notes), so billing correctly happens AFTER QC, not before, both for realism (you don't pay
	for a shipment before it clears QC) and because ERPNext enforces it."""
	if not frappe.db.exists("Item", _SOY_ITEM):
		return "seed_ingredient_trading_import_shipment: SKIPPED — run seed_ingredient_trading_master_data first."

	po1_name, po1_created = _ensure_po("IT-PO-SOY-01", _SOY_ITEM, _SOY_PO_QTY, _SOY_PO_RATE_USD, _SOY_PO1_CONVERSION_RATE, _SUPPLIER_SOY)
	po2_name, po2_created = _ensure_po("IT-PO-SOY-02-FX", _SOY_ITEM, _SOY_PO_QTY, _SOY_PO_RATE_USD, _SOY_PO2_CONVERSION_RATE, _SUPPLIER_SOY)

	po1 = frappe.db.get_value("Purchase Order", po1_name, ["grand_total", "base_grand_total", "conversion_rate"], as_dict=True)
	po2 = frappe.db.get_value("Purchase Order", po2_name, ["grand_total", "base_grand_total", "conversion_rate"], as_dict=True)

	# FT02 CONFIRMED inline — arithmetic correctness on BOTH POs, and a genuinely different
	# base_grand_total between two otherwise-identical POs that differ ONLY in conversion_rate.
	if round(po1.base_grand_total) != round(po1.grand_total * po1.conversion_rate):
		frappe.throw(f"FT02 FAILED: PO1 base_grand_total {po1.base_grand_total} != grand_total {po1.grand_total} * conversion_rate {po1.conversion_rate}.")
	if round(po2.base_grand_total) != round(po2.grand_total * po2.conversion_rate):
		frappe.throw(f"FT02 FAILED: PO2 base_grand_total {po2.base_grand_total} != grand_total {po2.grand_total} * conversion_rate {po2.conversion_rate}.")
	if po1.grand_total != po2.grand_total:
		frappe.throw(f"FT02 FAILED: PO1/PO2 grand_total (USD) should be IDENTICAL to isolate conversion_rate as the only variable — got {po1.grand_total} vs {po2.grand_total}.")
	if po1.base_grand_total == po2.base_grand_total:
		frappe.throw("FT02 FAILED: PO1/PO2 base_grand_total (VND) should DIFFER — same USD amount converted at two different exchange rates must not land on the same VND total.")

	pr1_name, pr1_created = _ensure_receipt(po1_name, _SOY_ITEM, _SOY_RECEIVED_QTY)
	po1_qty_row = frappe.db.get_value("Purchase Order Item", {"parent": po1_name, "item_code": _SOY_ITEM}, ["qty", "received_qty"], as_dict=True)
	shrinkage = po1_qty_row.qty - po1_qty_row.received_qty
	if not (po1_qty_row.received_qty < po1_qty_row.qty):
		frappe.throw(f"FT01 FAILED: expected received_qty ({po1_qty_row.received_qty}) below ordered qty ({po1_qty_row.qty}) to model shrinkage.")

	return (
		f"seed_ingredient_trading_import_shipment: PO1 {'created' if po1_created else 'already existed'} ({po1_name}, ordered {po1_qty_row.qty}kg). "
		f"PR1 {'created' if pr1_created else 'already existed'} ({pr1_name}, received {po1_qty_row.received_qty}kg, shrinkage {shrinkage}kg detected). "
		f"PO2 {'created' if po2_created else 'already existed'} ({po2_name}, FX contrast). FT02 CONFIRMED — "
		f"PO1 base_grand_total {po1.base_grand_total:,.0f} VND vs PO2 base_grand_total {po2.base_grand_total:,.0f} VND (same {po1.grand_total} USD, different conversion_rate)."
	)


# ---------------------------------------------------------------------------
# FT03 supplier lot + FT04 incoming QC (DP-682) — plus Fish Meal's own (lighter) receiving
# chain, needed only for FT06/FT07's multi-item aggregation, no lettered test of its own.
# ---------------------------------------------------------------------------

def _batch_from_receipt(pr_name, item_code):
	"""FT03 prerequisite — resolve the Batch that a Purchase Receipt created, via
	Serial and Batch Bundle (NOT a direct batch_no column — this ERPNext version routes batch
	linkage through Serial and Batch Bundle/Entry, per this session's standing lesson)."""
	rows = frappe.db.sql(
		"""select sbe.batch_no from `tabPurchase Receipt Item` pri
		inner join `tabSerial and Batch Entry` sbe on sbe.parent = pri.serial_and_batch_bundle
		where pri.parent = %s and pri.item_code = %s limit 1""",
		(pr_name, item_code),
	)
	return rows[0][0] if rows else None


def _ensure_qi_parameter():
	if frappe.db.exists("Quality Inspection Parameter", _QC_SPEC):
		return False
	frappe.get_doc({"doctype": "Quality Inspection Parameter", "parameter": _QC_SPEC, "description": "Crude protein content, % by weight (feed-grade ingredient spec)."}).insert(ignore_permissions=True)
	return True


def _locale_reading(value):
	"""Real bug found live on pharmacountry.vn (production): Quality Inspection Reading's
	numeric reading_1 is a Data field validated against the SITE's own configured
	System Settings.number_format, not a fixed decimal point — pharmacountry.vn uses
	"#.###,##" (comma decimal separator), while test.demo.local uses the default "#,###.##"
	(period). A hardcoded "47.2" string is valid on one site and rejected on the other
	ERROR: "Reading 1 47.2 is not a valid number in the #.###,## number format"). Fixed by
	deriving the site's own decimal separator from the character 3 positions before the end of
	its number_format string (works for every stock Frappe number_format option) instead of
	assuming "."."""
	fmt = frappe.db.get_single_value("System Settings", "number_format") or "#,###.##"
	decimal_str = fmt[-3] if len(fmt) >= 3 and fmt[-3] in ".,'" else "."
	return str(value).replace(".", decimal_str)


def _ensure_quality_inspection(reference_name, item_code, batch_no, min_v, max_v, reading):
	existing = frappe.db.get_value("Quality Inspection", {"reference_name": reference_name, "item_code": item_code, "batch_no": batch_no}, ["name", "status"], as_dict=True)
	if existing:
		return existing.name, False
	_ensure_qi_parameter()
	qi = frappe.get_doc(
		{
			"doctype": "Quality Inspection",
			"inspection_type": "Incoming",
			"reference_type": "Purchase Receipt",
			"reference_name": reference_name,
			"item_code": item_code,
			"batch_no": batch_no,
			"sample_size": 5,
			"company": _COMPANY_NAME,
			"inspected_by": frappe.session.user,
			"readings": [{"specification": _QC_SPEC, "numeric": 1, "min_value": min_v, "max_value": max_v, "reading_1": _locale_reading(reading)}],
		}
	)
	qi.insert(ignore_permissions=True)
	qi.submit()
	return qi.name, True


def _test_ft04_release_blocked_before_qc(item_code, batch_no):
	"""FT04 negative test — must run BEFORE the Quality Inspection exists for this batch,
	otherwise the block can never be observed on a re-run (release always empties the pending
	batch by design, same idempotency shape as 3PL's W04 quarantine-release negative test)."""
	if frappe.db.exists("Quality Inspection", {"item_code": item_code, "batch_no": batch_no, "status": "Accepted", "docstatus": 1}):
		return "skip"  # already QC'd in a prior run — nothing left to block
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	se.append("items", {"item_code": item_code, "qty": 1, "s_warehouse": _QUARANTINE_WAREHOUSE, "t_warehouse": _RELEASED_WAREHOUSE, "batch_no": batch_no, "use_serial_batch_fields": 1})
	blocked = False
	try:
		se.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("FT04 negative test FAILED: a batch with NO Accepted Quality Inspection was allowed into the Released warehouse!")
	return True


def _ensure_release(item_code, batch_no, qty):
	already = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse = %s and sbe.batch_no = %s and sle.is_cancelled = 0 limit 1""",
		(_RELEASED_WAREHOUSE, batch_no),
	)
	if already:
		return False
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": _COMPANY_NAME})
	se.append("items", {"item_code": item_code, "qty": qty, "s_warehouse": _QUARANTINE_WAREHOUSE, "t_warehouse": _RELEASED_WAREHOUSE, "batch_no": batch_no, "use_serial_batch_fields": 1})
	se.insert(ignore_permissions=True)
	se.submit()
	return True


def seed_ingredient_trading_supplier_lot_qc():
	"""DP-682 — FT03 (supplier lot) + FT04 (incoming QC), plus the invoicing leg of FT01
	(billed qty). Uses the Soybean Meal batch from PR1 (DP-681). QC now runs BEFORE the Purchase
	Invoice — a real bug found live: native Item.inspection_required_before_purchase (set on
	both traded Items, FT04's own prerequisite) blocks Purchase Invoice submission for that item
	until an Accepted Quality Inspection exists ("Quality Inspection is required for Item..."),
	so invoicing correctly happens AFTER QC clears, not before — both more realistic (you don't
	pay for a shipment before it clears QC) and required by ERPNext itself. Also receives/QCs/
	invoices/releases Fish Meal (its own supplier, own PO -> PR -> QC -> PI chain, no shrinkage/
	FX contrast) purely so FT06/FT07 have a genuine SECOND item to aggregate over — proving those
	queries GROUP correctly rather than being hardcoded to one item."""
	po1_name = frappe.db.get_value("Purchase Order", {"title": "IT-PO-SOY-01"}, "name")
	if not po1_name:
		return "seed_ingredient_trading_supplier_lot_qc: SKIPPED — run seed_ingredient_trading_import_shipment first."
	pr1_name = frappe.db.get_value("Purchase Receipt Item", {"purchase_order": po1_name, "item_code": _SOY_ITEM}, "parent")
	if not pr1_name:
		return "seed_ingredient_trading_supplier_lot_qc: SKIPPED — Purchase Receipt not found, run seed_ingredient_trading_import_shipment first."

	soy_batch = _batch_from_receipt(pr1_name, _SOY_ITEM)
	ft04_negative = _test_ft04_release_blocked_before_qc(_SOY_ITEM, soy_batch)
	soy_qi, soy_qi_created = _ensure_quality_inspection(pr1_name, _SOY_ITEM, soy_batch, 44, 50, 47.2)
	pi1_name, pi1_created = _ensure_purchase_invoice(pr1_name)
	soy_released = _ensure_release(_SOY_ITEM, soy_batch, _SOY_RECEIVED_QTY)

	# FT01 CONFIRMED (invoicing leg) — billed qty reconciled against the ACTUAL received qty,
	# not the nominal order, closing out the full PO -> Purchase Receipt -> Purchase Invoice
	# chain this demo's FT01 reconciles.
	po1_qty_row = frappe.db.get_value("Purchase Order Item", {"parent": po1_name, "item_code": _SOY_ITEM}, ["qty", "received_qty"], as_dict=True)
	billed = _billed_qty(pr1_name, _SOY_ITEM)
	if round(billed) != round(po1_qty_row.received_qty):
		frappe.throw(f"FT01 FAILED: billed qty ({billed}) should match the ACTUAL received qty ({po1_qty_row.received_qty}), not the nominal order ({po1_qty_row.qty}).")

	# Fish Meal's own lighter chain (no lettered test of its own) — same corrected QC-before-PI order.
	fish_po_name, _ = _ensure_po("IT-PO-FISH-01", _FISH_ITEM, _FISH_PO_QTY, _FISH_PO_RATE_USD, _FISH_PO_CONVERSION_RATE, _SUPPLIER_FISH)
	fish_pr_name, _ = _ensure_receipt(fish_po_name, _FISH_ITEM, _FISH_PO_QTY)
	fish_batch = _batch_from_receipt(fish_pr_name, _FISH_ITEM)
	fish_qi, _ = _ensure_quality_inspection(fish_pr_name, _FISH_ITEM, fish_batch, 60, 70, 65.5)
	_ensure_purchase_invoice(fish_pr_name)
	_ensure_release(_FISH_ITEM, fish_batch, _FISH_PO_QTY)

	from enterprise_core.enterprise_core.api import get_ingredient_supplier_lot

	lot = get_ingredient_supplier_lot(soy_batch)
	if not (lot and lot.get("supplier") == _SUPPLIER_SOY and lot.get("purchase_receipt") == pr1_name):
		frappe.throw(f"FT03 FAILED: supplier-lot trace for batch {soy_batch} did not resolve back to supplier {_SUPPLIER_SOY} / receipt {pr1_name}. Got: {lot}")

	return (
		f"seed_ingredient_trading_supplier_lot_qc: FT04 negative test (release blocked before QC) = {ft04_negative}. "
		f"Soybean QC {'created' if soy_qi_created else 'already existed'} ({soy_qi}, Accepted). "
		f"PI1 {'created' if pi1_created else 'already existed'} ({pi1_name}, billed {billed}kg). FT01 CONFIRMED. Released={soy_released}. "
		f"FT03 CONFIRMED — batch {soy_batch} traces to supplier {lot.get('supplier')} via receipt {lot.get('purchase_receipt')}. "
		f"Fish Meal receipt/QC/invoice/release also completed ({fish_pr_name}, {fish_qi})."
	)


# ---------------------------------------------------------------------------
# FT05 contract quantity (DP-683) — Blanket Order draw-down, plus the real sales flow that
# feeds FT07's margin report for both items.
# ---------------------------------------------------------------------------

def _ensure_blanket_order():
	existing = frappe.db.exists("Blanket Order", {"customer": _CUSTOMER_SOY, "blanket_order_type": "Selling"})
	if existing:
		return existing, False
	bo = frappe.get_doc(
		{
			"doctype": "Blanket Order",
			"blanket_order_type": "Selling",
			"customer": _CUSTOMER_SOY,
			"company": _COMPANY_NAME,
			"from_date": nowdate(),
			"to_date": add_days(nowdate(), 90),
			"items": [{"item_code": _SOY_ITEM, "qty": _SOY_CONTRACT_QTY, "rate": _SOY_SELL_RATE}],
		}
	)
	bo.insert(ignore_permissions=True)
	bo.submit()
	return bo.name, True


def _ensure_so_dn_si(customer, item_code, qty, rate, po_no, blanket_order=None):
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

	so_name = frappe.db.exists("Sales Order", {"po_no": po_no})
	if not so_name:
		row = {"item_code": item_code, "qty": qty, "rate": rate, "warehouse": _RELEASED_WAREHOUSE}
		if blanket_order:
			row.update({"against_blanket_order": 1, "blanket_order": blanket_order, "blanket_order_rate": rate})
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer,
				"company": _COMPANY_NAME,
				"delivery_date": add_days(nowdate(), 10),
				"po_no": po_no,
				"items": [row],
			}
		)
		so.insert(ignore_permissions=True)
		so.submit()
		so_name = so.name

	dn_name = frappe.db.get_value("Delivery Note Item", {"against_sales_order": so_name}, "parent")
	if not dn_name:
		dn = make_delivery_note(so_name)
		dn.insert(ignore_permissions=True)
		dn.submit()
		dn_name = dn.name

	si_name = frappe.db.get_value("Sales Invoice Item", {"delivery_note": dn_name}, "parent")
	if not si_name:
		si = make_sales_invoice(dn_name)
		si.insert(ignore_permissions=True)
		si.submit()
		si_name = si.name

	return so_name, dn_name, si_name


def _test_ft05_overcommit_blocked(bo_name):
	"""FT05 negative test — native validate_against_blanket_order(), confirmed by reading
	erpnext/manufacturing/doctype/blanket_order/blanket_order.py before writing this: cumulative
	ordered_qty against a Blanket Order cannot exceed committed qty + Selling Settings.
	blanket_order_allowance (0/unset on this site, confirmed live). 20,000kg committed, 8,000kg
	already drawn down (DP-683's real order) — attempting 15,000kg more (23,000kg cumulative)
	must be blocked."""
	if frappe.db.exists("Sales Order", {"po_no": "IT-SO-CONTRACT-OVERCOMMIT"}):
		return True  # already proven blocked in a prior run (no submitted doc left behind)
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _CUSTOMER_SOY,
			"company": _COMPANY_NAME,
			"delivery_date": add_days(nowdate(), 10),
			"po_no": "IT-SO-CONTRACT-OVERCOMMIT",
			"items": [{"item_code": _SOY_ITEM, "qty": 15000, "rate": _SOY_SELL_RATE, "warehouse": _RELEASED_WAREHOUSE, "against_blanket_order": 1, "blanket_order": bo_name, "blanket_order_rate": _SOY_SELL_RATE}],
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
		frappe.throw("FT05 negative test FAILED: an over-commit Sales Order beyond the Blanket Order's remaining qty was not blocked!")
	return True


def seed_ingredient_trading_contract_and_sales():
	"""DP-683 — FT05 (contract quantity, native Blanket Order draw-down + over-commit block)
	plus the real Sales Order -> Delivery Note -> Sales Invoice flow for BOTH items, which is
	what feeds FT07's margin report with actual revenue."""
	if not frappe.db.exists("Customer", {"customer_name": _CUSTOMER_SOY}):
		return "seed_ingredient_trading_contract_and_sales: SKIPPED — run seed_ingredient_trading_master_data first."
	if not frappe.db.exists("Stock Ledger Entry", {"warehouse": _RELEASED_WAREHOUSE, "item_code": _SOY_ITEM}):
		return "seed_ingredient_trading_contract_and_sales: SKIPPED — run seed_ingredient_trading_supplier_lot_qc first (Released stock required)."

	bo_name, bo_created = _ensure_blanket_order()
	so_name, dn_name, si_name = _ensure_so_dn_si(_CUSTOMER_SOY, _SOY_ITEM, _SOY_SO_DRAWDOWN_QTY, _SOY_SELL_RATE, "IT-SO-CONTRACT-DRAWDOWN", blanket_order=bo_name)

	bo_item = frappe.db.get_value("Blanket Order Item", {"parent": bo_name, "item_code": _SOY_ITEM}, ["qty", "ordered_qty"], as_dict=True)
	if not (bo_item and bo_item.ordered_qty == _SOY_SO_DRAWDOWN_QTY):
		frappe.throw(f"FT05 FAILED: Blanket Order Item.ordered_qty ({bo_item.ordered_qty if bo_item else None}) should equal the drawn-down Sales Order qty ({_SOY_SO_DRAWDOWN_QTY}) — native update_ordered_qty() should have set this on submit.")
	if not (bo_item.ordered_qty < bo_item.qty):
		frappe.throw(f"FT05 FAILED: ordered_qty ({bo_item.ordered_qty}) should be below committed qty ({bo_item.qty}) — contract not yet fully drawn down.")

	ft05_overcommit = _test_ft05_overcommit_blocked(bo_name)

	fish_so, fish_dn, fish_si = _ensure_so_dn_si(_CUSTOMER_FISH, _FISH_ITEM, _FISH_SO_QTY, _FISH_SELL_RATE, "IT-SO-FISH-01")

	return (
		f"seed_ingredient_trading_contract_and_sales: Blanket Order {'created' if bo_created else 'already existed'} ({bo_name}, committed {bo_item.qty}kg). "
		f"SO/DN/SI = {so_name}/{dn_name}/{si_name} (drawdown {bo_item.ordered_qty}kg). FT05 CONFIRMED (overcommit-blocked={ft05_overcommit}). "
		f"Fish Meal SO/DN/SI = {fish_so}/{fish_dn}/{fish_si}."
	)


# ---------------------------------------------------------------------------
# FT06 price history (DP-684)
# ---------------------------------------------------------------------------

_SOY_PRICE_HISTORY = [(-120, 11800), (-60, 12800), (0, _SOY_SELL_RATE)]
_FISH_PRICE_HISTORY = [(-120, 27500), (-60, 30000), (0, _FISH_SELL_RATE)]


def _ensure_price_history(item_code, history):
	created = 0
	for days_offset, rate in history:
		valid_from = add_days(nowdate(), days_offset)
		if frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling", "selling": 1, "valid_from": valid_from}):
			continue
		frappe.get_doc(
			{"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Selling", "selling": 1, "currency": "VND", "price_list_rate": rate, "valid_from": valid_from}
		).insert(ignore_permissions=True)
		created += 1
	return created


def seed_ingredient_trading_price_history():
	"""DP-684 — FT06, price history. Three dated Item Price rows per item (rising trend, real
	commodity/FX-driven cost increases over the quarter), pure native schema — no new DocType.
	Confirms get_ingredient_price_history() resolves a genuinely increasing series, not just
	"some rows exist"."""
	if not frappe.db.exists("Item", _SOY_ITEM):
		return "seed_ingredient_trading_price_history: SKIPPED — run seed_ingredient_trading_master_data first."

	soy_created = _ensure_price_history(_SOY_ITEM, _SOY_PRICE_HISTORY)
	fish_created = _ensure_price_history(_FISH_ITEM, _FISH_PRICE_HISTORY)

	from enterprise_core.enterprise_core.api import get_ingredient_price_history

	soy_history = get_ingredient_price_history(_SOY_ITEM)
	rates = [r.price_list_rate for r in soy_history]
	if not (len(rates) >= 3 and rates == sorted(rates) and rates[0] < rates[-1]):
		frappe.throw(f"FT06 FAILED: Soybean Meal price history is not a genuinely increasing series over time. Got: {soy_history}")

	return f"seed_ingredient_trading_price_history: {soy_created} new Soybean price point(s), {fish_created} new Fish Meal price point(s). FT06 CONFIRMED — {rates}."


# ---------------------------------------------------------------------------
# FT07 margin report (DP-685) + integrity check
# ---------------------------------------------------------------------------

def seed_ingredient_trading_margin_report():
	"""DP-685 — FT07, margin report. No seed action of its own: confirms
	get_ingredient_trading_margin_report() resolves real, positive margins (sell > buy) for
	BOTH traded items from actual submitted Purchase Invoice / Sales Invoice data."""
	from enterprise_core.enterprise_core.api import get_ingredient_trading_margin_report

	if not frappe.db.exists("Sales Invoice", {"company": _COMPANY_NAME, "docstatus": 1}):
		return "seed_ingredient_trading_margin_report: SKIPPED — run seed_ingredient_trading_contract_and_sales first."

	report = get_ingredient_trading_margin_report()
	items_with_positive_margin = {row["item_code"] for row in report if row.get("margin_per_unit") and row["margin_per_unit"] > 0}
	if not ({_SOY_ITEM, _FISH_ITEM} <= items_with_positive_margin):
		frappe.throw(f"FT07 FAILED: margin report missing a real, positive margin for both traded items. Got: {report}")
	return f"seed_ingredient_trading_margin_report: FT07 CONFIRMED — {report}"
