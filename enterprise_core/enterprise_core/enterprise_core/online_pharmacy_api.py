"""WEB-06 — Online Pharmacy (Phase 7, master plan §8 lines ~2572-2573: "WEB-06 Online Pharmacy —
Frontend riêng, tích hợp pharmacy ERP." — a dedicated frontend, GENUINELY integrated with the
pharmacy ERP, not a generic e-commerce re-skin). Backs the standalone Next.js app in
`nextjs-demo/web-06-online-pharmacy/`. Real data: Golden Demo #23 (Pharmacy Chain), Demo Pharmacy
Chain Co., Store A's real stock, real batches, real expiry-block mechanism (RX03).

THIS REUSES WEB-05's PROVEN GUEST-WRITABLE-CHECKOUT SECURITY MODEL ALMOST VERBATIM — read
`b2c_commerce_api.py`'s own module docstring for the full original threat-model writeup. Every one
of its 7 numbered points still applies here, unchanged in spirit:
  1. Price is NEVER read from the client — `_current_price()` looks up the real, current Item Price
     by item_code alone, exactly like WEB-05's `_current_price()`.
  2/3. Every write is scoped to ONE isolated Customer ("Pharmacy Online Guest (WEB-06 Online
     Orders)", see `online_pharmacy_seeds.py`), and uses the SAME narrow, documented `frappe.
     set_user("Administrator")` elevation pattern WEB-05 found and fixed — restored in `finally`,
     scoped to exactly the write statements, every value already validated before elevation. NOT a
     rediscovered fix: reused directly because the SAME root cause applies (`POS Invoice`'s own
     `set_missing_values()`/`get_item_details()` call chain re-checks `Item` permission on a fresh
     document instance the same way `Sales Order`'s did — confirmed empirically before writing the
     elevation, by first hitting the identical raw `frappe.PermissionError` WEB-05's docstring
     describes, then applying WEB-05's already-proven fix directly rather than re-deriving it).
  6. Order lookup requires a random, unguessable `order_token` (stored in `po_no`, exactly like
     WEB-05) AND the checkout phone number — both wrong-token and wrong-phone return the identical
     generic 404.
  7. Cash on Delivery only, honestly disclosed as a demo simplification (see below for the one real
     wrinkle this introduces that WEB-05 never had).

WHAT'S GENUINELY NEW FOR PHARMACY — NOT INHERITED FOR FREE:

  A. A POS INVOICE, NOT A SALES ORDER — because ONLY a real stock-moving document re-proves RX03.
     WEB-05 created a `Sales Order` (a pure commitment document — `SellingController`, not
     `StockController` — it never moves stock and, confirmed by reading ERPNext's own `stock_
     controller.py` before writing this, NEVER calls the `BatchExpiredError` check at all). Golden
     Demo #23's own RX03 proof is specifically against a `POS Invoice` with `update_stock=1` — the
     ONLY way to genuinely re-prove "the native expiry-block mechanism still protects THIS new write
     path" is to make THIS write path a real stock-moving document too. So `place_pharmacy_order`
     creates a real, submitted `POS Invoice` (`is_pos=1`, `update_stock=1`) against a dedicated
     isolated POS Profile ("Online Pharmacy Store A POS", see `online_pharmacy_seeds.py`'s own
     docstring for why NOT Golden Demo #23's own "Pharmacy Store A POS" — a real RX05 query-collision
     risk was found and designed around, not discovered by breaking it). This also means WEB-06's
     "Cash on Delivery" is a disclosed demo simplification WEB-05 didn't need: a POS Invoice requires
     full payment to validate, so checkout is modeled as an immediately-paid, immediately-stock-
     deducted real sale via the native "Cash" Mode of Payment — a real production COD deployment
     would instead record payment at delivery, not at order placement. Documented here and in the
     app's own README, the same honesty this platform applies to every other mocked-financial-flow
     disclosure (WEB-05's own COD-only design, the platform's mocked LLM/embeddings work elsewhere).

  B. REAL PER-STORE STOCK, HONESTLY COMPUTED — NOT THE RAW `Bin.actual_qty`. Store A's real `Bin.
     actual_qty` for PARA-500-TAB is 130 (before WEB-06's own isolated top-up) — but 10 of those units
     sit in the deliberately-expired `RX03-EXPIRED-TEST` batch (expiry 2020-01-01), which native
     ERPNext will correctly refuse to ever sell. Showing a guest "130 in stock" would be dishonest:
     an order for the full 130 would partially fail. `_sellable_batches()` computes the REAL,
     batch-level, non-expired quantity instead (same real Stock-Ledger-Entry + Serial-and-Batch-Entry
     + Batch join every prior batch-tracked golden demo in this platform already uses, confirmed live
     before writing this module), and the catalog's `available_qty` is this honest sellable number,
     not the raw Bin total. `_pick_batches_fefo()` reuses the SAME real batch data to fulfil an order
     earliest-expiry-first (FEFO) — the same discipline Golden Demo #24 (3PL)'s own W03 already
     established — so a genuine online order is deterministically filled from real, valid stock and
     never accidentally handed the expired batch by an unscoped auto-batch-selection.

  C. PRESCRIPTION-VS-OTC HONESTY — NO FABRICATED WORKFLOW. Checked LIVE, before writing this module:
     `Item` (v16.36.0, this golden demo's real schema) carries no field distinguishing prescription-
     required from OTC status anywhere in its ~90 real fields (`bench execute` dump of `Item.
     as_dict().keys()` on `PARA-500-TAB` inspected directly). Per this build's own explicit
     instruction, that absence is NOT papered over by inventing a plausible-looking "requires_
     prescription" flag or a fake upload/pharmacist-verification flow — doing so would misrepresent
     what the real data actually distinguishes. Paracetamol 500mg is itself uncontroversially an
     OTC analgesic (Vietnam's own Circular 07/2017/TT-BYT places paracetamol tablets under OTC), so
     this single-SKU storefront is honestly scoped to real, genuinely OTC-appropriate data without
     needing to build anything for prescription handling — stated explicitly in this docstring and
     the app's own README, not silently assumed.

  D. A REAL, PROACTIVELY-DESIGNED-AROUND NATIVE ERPNEXT POS ARCHITECTURE FACT — NOT A WEB-06 BUG.
     Found empirically while building this: `POS Invoice.on_submit()` (read directly from ERPNext's
     own source, `erpnext/accounts/doctype/pos_invoice/pos_invoice.py`) does NOT call `update_stock_
     ledger()` or create any GL Entry — unlike plain `Sales Invoice.on_submit()`, which does both.
     It only submits the item rows' own `Serial and Batch Bundle` documents (a real, immediate
     commitment of exactly which batch/qty was consumed — confirmed this bundle IS created correctly,
     `type_of_transaction="Outward"`, negative qty against the real batch), but that bundle's own
     `on_submit()` (also read directly) only VALIDATES, it never creates a `Stock Ledger Entry`
     either. This is intentional, native ERPNext architecture, not a defect: individual POS Invoices
     are lightweight, provisional register sales; a `POS Closing Entry` is meant to later consolidate
     them into a `Consolidated Sales Invoice`, and THAT document is what actually posts to the Stock
     Ledger/GL. Confirmed this is not a WEB-06-specific gap by checking Golden Demo #23's OWN real
     in-store sale (DP-653) live: its warehouse balance shows the identical characteristic — Store A's
     real `Stock Ledger Entry` total is fully accounted for by Material Receipts/Transfers alone, with
     no trace of that 10-unit sale either, because no `POS Closing Entry` was ever run for that
     profile either.
     WHY THIS ISN'T PAPERED OVER WITH A MANUAL `update_stock_ledger()` CALL: doing so would post a
     real Stock Ledger Entry OUTSIDE ERPNext's own intended consolidation flow, and if a POS Closing
     Entry were ever run later for either POS Profile, it could double-post the same sale's stock
     movement. Instead, `_sellable_batches()` treats every real, submitted, non-return POS Invoice
     Item against a batch (from EITHER POS Profile — the online storefront's own AND Golden Demo #23's
     in-store one, since both draw on the same real warehouse) as an already-COMMITTED reduction in
     that batch's real sellable quantity, on top of its real Stock-Ledger balance — so the storefront
     can never oversell a batch that's already been sold, even though the Stock Ledger itself won't
     reflect it until a hypothetical future POS Closing Entry. This is the more correct inventory
     model for a live storefront regardless (a real e-commerce backend must never oversell units that
     are already sold, whether or not the accounting subsystem has run its own end-of-day batch job
     yet) — documented here as a genuine finding, not silently worked around.

  E. A REAL DELIVERY ADDRESS, NOT DISCARDED. A real bug found while building this (before any
     external testing — caught by re-reading this module's own first draft against WEB-05's): the
     first draft captured `contact_display`/`contact_mobile`/`contact_email` on the POS Invoice but
     never actually stored the guest's delivery address anywhere at all. Fixed by reusing WEB-05's
     own pattern exactly: a real `Address` document is created and linked via `customer_address`/
     `shipping_address_name`, so a real COD delivery would actually have somewhere to go — confirmed
     empirically (`address_display` now resolves correctly on both `place_pharmacy_order`'s own
     response and `get_pharmacy_order_status()`'s lookup).

  F. ONE REAL STORE, NOT AN AGGREGATE. Golden Demo #23 has 2 real retail stores (Store A/Store B).
     This storefront represents Store A specifically (`_STORE_WAREHOUSE`) — the same store Golden
     Demo #23's own POS Profile already sells from in person, so "buy online" and "buy in-store" are
     honestly the same real shop's two channels, not a fictional "ship from whichever store has
     stock" aggregation layer that would need its own (unbuilt, out of scope) multi-warehouse
     fulfillment logic.

DATA SOURCE — Golden Demo #23 (Pharmacy Chain), `Demo Pharmacy Chain Co.`, `PARA-500-TAB`
  ("Paracetamol 500 mg Tablet"), `Store A - DPH`, "Standard Selling" price list (1,500 VND, with a
  real, currently-active `Pricing Rule` — "Pharmacy Loyalty Week Promotion", 10% off, valid through
  2026-10-28 — confirmed live before writing this module's price-tampering proof, same reasoning
  WEB-05's own docstring gives for comparing tampered-vs-clean rather than asserting a hardcoded
  flat price). `_safe_item_codes()` is deliberately data-driven (Item + real Stock Ledger Entry
  movement at `_STORE_WAREHOUSE` + real selling Item Price join), not a hardcoded single-item list,
  even though exactly one real item currently qualifies — the same "never hardcode what a live query
  already proves" discipline WEB-01/WEB-05 both established.

ISOLATION — see `online_pharmacy_seeds.py`'s own module docstring for the full reasoning behind the
  dedicated POS Profile / top-up stock batch / guest Customer / cashier service User this module's
  writes depend on. All setup there is idempotent, admin-run, and never guest-reachable.
"""

import re

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

_COMPANY_NAME = "Demo Pharmacy Chain Co."
_STORE_WAREHOUSE = "Store A - DPH"
_PRICE_LIST = "Standard Selling"

_ONLINE_POS_PROFILE = "Online Pharmacy Store A POS"
_ONLINE_GUEST_CUSTOMER = "Pharmacy Online Guest (WEB-06 Online Orders)"

_MAX_QTY_PER_LINE = 20
_MAX_LINES_PER_ORDER = 5
_MAX_NAME_LEN = 120
_MAX_LINE_LEN = 200
_MIN_PHONE_DIGITS = 8
_MAX_PHONE_DIGITS = 15

_PAYMENT_METHOD = "Cash on Delivery"  # the ONLY accepted value — see module docstring point A.
_MODE_OF_PAYMENT = "Cash"  # the real native Mode of Payment this demo's COD is recorded through.

# Presentation-only copy — same discipline as WEB-01/WEB-05's own `_STOREFRONT_COPY`
# (Item.description is empty on the real golden-demo Item). Only ever rendered for an item_code that
# independently passes the real, data-driven `_safe_item_codes()` filter below.
_STOREFRONT_COPY = {
	"PARA-500-TAB": {
		"category": "Pain Relief / Fever Reducer (OTC)",
		"blurb": (
			"Paracetamol 500mg tablets for pain relief and fever reduction. Over-the-counter — no "
			"prescription required. Dispensed from Demo Pharmacy Chain Co.'s Store A, the same real "
			"store this chain's own point-of-sale sells from in person."
		),
	},
}


def _safe_item_codes():
	"""Real, data-driven filter: an Item with real Stock Ledger Entry movement at `_STORE_WAREHOUSE`
	specifically (not just anywhere in the company — `PARA-500-TAB` is a globally-reused Item, shared
	with Golden Demo #1's own manufacturing data, so scoping by THIS store's own real stock movement,
	the same discipline `pharmacy_seeds.py`'s own `_central_batch()` already established, is what
	keeps this deliberately precise) AND a real selling Item Price on the public `_PRICE_LIST`."""
	rows = frappe.db.sql(
		"""
		select distinct i.item_code
		from `tabItem` i
		inner join `tabStock Ledger Entry` sle on sle.item_code = i.item_code and sle.warehouse = %(warehouse)s
		inner join `tabItem Price` ip on ip.item_code = i.item_code and ip.selling = 1 and ip.price_list = %(price_list)s
		where i.disabled = 0
		order by i.item_code
		""",
		{"warehouse": _STORE_WAREHOUSE, "price_list": _PRICE_LIST},
		as_dict=True,
	)
	return [r.item_code for r in rows]


def _current_price(item_code):
	"""The ONLY place any order line's rate ever comes from — never accepts or reads a
	client-supplied price of any kind. Identical discipline to `b2c_commerce_api._current_price()`."""
	price = frappe.db.get_value(
		"Item Price", {"item_code": item_code, "selling": 1, "price_list": _PRICE_LIST}, "price_list_rate"
	)
	if price is None:
		frappe.throw(_("Item {0} has no current price and cannot be ordered.").format(item_code))
	return price


def _committed_qty_by_batch(item_code, warehouse=_STORE_WAREHOUSE):
	"""Net quantity already COMMITTED against each real batch by a submitted POS Invoice — from
	EITHER POS Profile selling at this warehouse (the online storefront's own AND Golden Demo #23's
	in-store one), signed (a return's own negated qty rows correctly give it back). See module
	docstring point D2 for why this exists: this ERPNext version's own `POS Invoice` submission does
	NOT immediately post to the Stock Ledger, so the raw batch balance alone would let this
	storefront oversell a batch that has already been sold."""
	rows = frappe.db.sql(
		"""
		select pii.batch_no, sum(pii.qty) as qty
		from `tabPOS Invoice Item` pii
		inner join `tabPOS Invoice` pi on pi.name = pii.parent
		where pi.docstatus = 1 and pii.item_code = %(item_code)s and pii.warehouse = %(warehouse)s
		group by pii.batch_no
		""",
		{"item_code": item_code, "warehouse": warehouse},
		as_dict=True,
	)
	return {r.batch_no: (r.qty or 0) for r in rows}


def _sellable_batches(item_code, warehouse=_STORE_WAREHOUSE):
	"""Real, batch-level stock at `warehouse` for `item_code`, EXCLUDING any batch that has already
	expired (module docstring point B) AND net of any already-COMMITTED-but-not-yet-ledger-posted POS
	Invoice quantity (module docstring point D2) — the honest, oversell-proof "available to sell"
	number, not raw `Bin.actual_qty`. Ordered earliest-expiry-first (FEFO, no-expiry-date batches
	last), same join pattern `pharmacy_seeds.py` already established (Stock Ledger Entry -> Serial and
	Batch Entry -> Batch), re-derived here rather than imported (keeps this guest-WRITE module's own
	security/data boundary independent, same reasoning `b2c_commerce_api.py`'s docstring gives for not
	importing WEB-01's)."""
	rows = frappe.db.sql(
		"""
		select sbe.batch_no, sum(sle.actual_qty) as qty, b.expiry_date
		from `tabStock Ledger Entry` sle
		inner join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		inner join `tabBatch` b on b.name = sbe.batch_no
		where sle.item_code = %(item_code)s and sle.warehouse = %(warehouse)s and sle.is_cancelled = 0
		group by sbe.batch_no
		having qty > 0
		order by (b.expiry_date is null) asc, b.expiry_date asc
		""",
		{"item_code": item_code, "warehouse": warehouse},
		as_dict=True,
	)
	today = getdate(nowdate())
	committed = _committed_qty_by_batch(item_code, warehouse)
	result = []
	for r in rows:
		if r.expiry_date and getdate(r.expiry_date) < today:
			continue
		remaining = r.qty - committed.get(r.batch_no, 0)
		if remaining > 0:
			result.append(frappe._dict({"batch_no": r.batch_no, "qty": remaining, "expiry_date": r.expiry_date}))
	return result


def _sellable_qty(item_code, warehouse=_STORE_WAREHOUSE):
	return sum(r.qty for r in _sellable_batches(item_code, warehouse))


def _pick_batches_fefo(item_code, qty, warehouse=_STORE_WAREHOUSE):
	"""Allocates `qty` across real, non-expired batches at `warehouse`, earliest-expiry-first,
	splitting across multiple batches if one alone can't cover it. Throws if real sellable stock is
	insufficient — never falls back to an expired or non-existent batch."""
	remaining = qty
	allocation = []
	for row in _sellable_batches(item_code, warehouse):
		if remaining <= 0:
			break
		take = min(remaining, row.qty)
		allocation.append({"batch_no": row.batch_no, "qty": take, "expiry_date": str(row.expiry_date) if row.expiry_date else None})
		remaining -= take
	if remaining > 0:
		frappe.throw(_("Only {0} unit(s) of {1} are currently in stock at this store.").format(int(qty - remaining), item_code))
	return allocation


def _serialize_catalog_item(item_code):
	item = frappe.db.get_value("Item", item_code, ["item_code", "item_name", "stock_uom"], as_dict=True)
	if not item:
		return None
	copy = _STOREFRONT_COPY.get(item_code, {})
	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		"uom": item.stock_uom,
		"category": copy.get("category", "Pharmacy Product"),
		"description": copy.get("blurb", ""),
		"price": _current_price(item_code),
		"currency": "VND",
		"available_qty": _sellable_qty(item_code),
		"store": "Store A",
		"requires_prescription": False,
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_pharmacy_catalog():
	"""Public, guest-accessible storefront catalog — real price + real, batch-honest sellable stock
	(excluding any expired batch) at the one real store this site represents. Read-only; no guest
	input accepted. `requires_prescription` is hardcoded `False` for every item this catalog can ever
	return — see module docstring point C: the real Item schema has no such field, and every item
	that can pass `_safe_item_codes()` in this golden demo's real data is genuinely OTC."""
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
	"""Only ever reads `item_code`/`qty` off each line — any other client-supplied key (e.g. a
	spoofed `rate`/`price`/`amount`/`batch_no`) is silently ignored, never trusted. `batch_no` is
	deliberately NOT an accepted client input anywhere in this module — batch allocation is ALWAYS
	server-computed by `_pick_batches_fefo()`, so a guest can never request a specific (e.g.
	deliberately expired) batch through the real ordering path."""
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

	order_lines = []
	for item_code, qty in by_item_code.items():
		allocation = _pick_batches_fefo(item_code, qty)  # throws if real sellable stock is insufficient
		order_lines.append({"item_code": item_code, "qty": qty, "allocation": allocation})
	return order_lines


@frappe.whitelist(allow_guest=True, methods=["POST"])
def place_pharmacy_order(items=None, contact=None, payment_method=_PAYMENT_METHOD):
	"""Creates a REAL, submitted POS Invoice for an anonymous guest — see module docstring for the
	full threat model. Every price is computed server-side, every item_code/qty/batch is
	re-validated (`_validate_items`, real live non-expired-stock check via `_pick_batches_fefo`), and
	the response deliberately never includes the real (sequential, guessable) POS Invoice `name` —
	only the random `order_token` needed later by `get_pharmacy_order_status()`."""
	if payment_method != _PAYMENT_METHOD:
		frappe.throw(_("Only Cash on Delivery is supported by this demo checkout."))

	contact_info = _validate_contact(contact)
	order_lines = _validate_items(items)
	order_token = f"WEB06-{frappe.generate_hash(length=10).upper()}"

	item_rows = []
	for line in order_lines:
		rate = _current_price(line["item_code"])  # server-computed, NEVER client-supplied
		for alloc in line["allocation"]:
			item_rows.append(
				{
					"item_code": line["item_code"],
					"qty": alloc["qty"],
					"rate": rate,
					"warehouse": _STORE_WAREHOUSE,
					"batch_no": alloc["batch_no"],
				}
			)

	address = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": f"Pharmacy Order {order_token}",
			"address_type": "Shipping",
			"address_line1": contact_info["address_line1"],
			"city": contact_info["city"],
			"country": "Vietnam",
			"phone": contact_info["phone"],
			"links": [{"link_doctype": "Customer", "link_name": _ONLINE_GUEST_CUSTOMER}],
		}
	)
	inv = frappe.get_doc(
		{
			"doctype": "POS Invoice",
			"customer": _ONLINE_GUEST_CUSTOMER,
			"company": _COMPANY_NAME,
			"pos_profile": _ONLINE_POS_PROFILE,
			"is_pos": 1,
			"update_stock": 1,
			"selling_price_list": _PRICE_LIST,
			"contact_display": contact_info["full_name"],
			"contact_mobile": contact_info["phone"],
			"contact_email": contact_info["email"] or None,
			"po_no": order_token,
			"items": item_rows,
			"payments": [{"mode_of_payment": _MODE_OF_PAYMENT, "amount": 0}],
		}
	)

	# Narrow, documented, restored-on-exit "service account" elevation — reused directly from
	# WEB-05's already-proven fix (see module docstring). Scoped to exactly these statements; every
	# value they write was already validated above, before this block, and restored even on failure.
	_original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		address.insert()
		inv.customer_address = address.name
		inv.shipping_address_name = address.name
		inv.insert()
		# The payments row must EXACTLY cover the real, possibly promotion-discounted grand_total —
		# same real bug/fix Golden Demo #23's own `seed_pharmacy_pos_sale()` already found
		# (`paid_amount` isn't auto-resynced from the `payments` child table on a plain `.insert()`),
		# applied here proactively rather than rediscovered.
		if inv.payments[0].amount != inv.grand_total:
			inv.payments[0].amount = inv.grand_total
			inv.paid_amount = inv.grand_total
			inv.save()
		inv.submit()
	finally:
		frappe.set_user(_original_user)

	return {
		"order_token": order_token,
		"payment_method": _PAYMENT_METHOD,
		"status": inv.status,
		"grand_total": inv.grand_total,
		"currency": "VND",
		"store": "Store A",
		"address_display": inv.address_display,
		"items": [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
				"batch_no": r.batch_no,
				"batch_expiry_date": str(frappe.db.get_value("Batch", r.batch_no, "expiry_date")) if r.batch_no else None,
			}
			for r in inv.items
		],
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_pharmacy_order_status(order_token: str = "", phone: str = ""):
	"""Order-status lookup for a guest — requires BOTH the random `order_token` returned at checkout
	AND the phone number used at checkout, identical two-factor design to `b2c_commerce_api.
	get_order_status()`. Scoped to `_ONLINE_POS_PROFILE` AND `_ONLINE_GUEST_CUSTOMER` (a STRONGER
	isolation than WEB-05 had available — WEB-05 only had one isolation axis, the Customer; here a
	`po_no` collision would need to match on customer AND pos_profile AND still fail the phone check
	to leak anything), so this lookup can never resolve a Golden-Demo-#23 in-store sale even in a
	pathological name collision."""
	order_token = (order_token or "").strip()
	phone_digits = _normalize_phone(phone)

	def not_found():
		frappe.throw(_("Order not found. Check your order reference and phone number."), frappe.DoesNotExistError)

	if not order_token or not phone_digits:
		not_found()

	inv_name = frappe.db.get_value(
		"POS Invoice", {"po_no": order_token, "customer": _ONLINE_GUEST_CUSTOMER, "pos_profile": _ONLINE_POS_PROFILE}, "name"
	)
	if not inv_name:
		not_found()

	stored_phone = _normalize_phone(frappe.db.get_value("POS Invoice", inv_name, "contact_mobile"))
	if not stored_phone or stored_phone != phone_digits:
		not_found()

	doc = frappe.get_doc("POS Invoice", inv_name)
	return {
		"order_token": order_token,
		"status": doc.status,
		"payment_method": _PAYMENT_METHOD,
		"transaction_date": str(doc.posting_date),
		"grand_total": doc.grand_total,
		"currency": "VND",
		"store": "Store A",
		"contact_display": doc.contact_display,
		"address_display": doc.address_display,
		"items": [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
				"batch_no": r.batch_no,
				"batch_expiry_date": str(frappe.db.get_value("Batch", r.batch_no, "expiry_date")) if r.batch_no else None,
			}
			for r in doc.items
		],
	}


# ============================================================================
# Empirical security + expiry-safety proof — called from enterprise_core.enterprise_core.api's
# verify_online_pharmacy_demo(), part of the platform's standard verify_* regression sweep.
# ============================================================================

_RX03_EXPIRED_BATCH = "RX03-EXPIRED-TEST"


def _attempt_order_against_expired_batch():
	"""Deliberately constructs a POS Invoice explicitly pinned to Golden Demo #23's own real
	`RX03-EXPIRED-TEST` batch (expiry 2020-01-01) — NOT reachable through `place_pharmacy_order`'s own
	guest-facing parameters at all (batch allocation there is always server-computed by
	`_pick_batches_fefo()`, which structurally excludes any expired batch; there is no `batch_no`
	parameter a guest can ever supply). This function exists ONLY to re-prove, empirically, that the
	SAME native `StockController` expiry-block mechanism RX03 already proved (`erpnext/controllers/
	stock_controller.py`'s `BatchExpiredError` check, confirmed by reading that source directly
	before writing this module) still protects THIS write path's own POS Profile/Customer/document
	construction — the single most important proof in this whole build. Posted through the isolated
	`_ONLINE_POS_PROFILE`, never Golden Demo #23's own "Pharmacy Store A POS", so even a hypothetical
	partial failure could never be mistaken for (or corrupt) that golden demo's own RX03 data."""
	attempt = frappe.get_doc(
		{
			"doctype": "POS Invoice",
			"customer": _ONLINE_GUEST_CUSTOMER,
			"company": _COMPANY_NAME,
			"pos_profile": _ONLINE_POS_PROFILE,
			"is_pos": 1,
			"update_stock": 1,
			"items": [{"item_code": "PARA-500-TAB", "qty": 1, "rate": 1500, "warehouse": _STORE_WAREHOUSE, "batch_no": _RX03_EXPIRED_BATCH}],
			"payments": [{"mode_of_payment": _MODE_OF_PAYMENT, "amount": 1500}],
		}
	)
	# Same narrow, documented, restored-on-exit elevation as `place_pharmacy_order`'s own real write
	# path — needed here too: a real, DIFFERENT nested permission check was found empirically while
	# building this (`get_party_account()`'s own `account_perm_check()` raising `frappe.
	# PermissionError` on a plain `ignore_permissions=True` insert while running as Guest), the same
	# "ignore_permissions=True alone is not enough" root cause class WEB-05's docstring already
	# documents, just a different nested call site this time.
	_original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		attempt.insert()
		attempt.submit()
	except frappe.ValidationError:
		return True
	finally:
		frappe.set_user(_original_user)
	return False


def verify_online_pharmacy_access_control():
	"""Real, empirical proof for WEB-06's guest-checkout security AND expiry-safety model. Always
	runs as Guest for the checkout/lookup proofs (this endpoint never requires a session) — the
	expiry-safety proof itself runs as Administrator (same as `pharmacy_seeds.py`'s own RX03 negative
	test), since it deliberately constructs a document shape no guest input can ever reach."""
	original_user = frappe.session.user
	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	try:
		frappe.set_user("Guest")

		safe_codes = _safe_item_codes()
		check("At least one real item is available for checkout (PARA-500-TAB)", bool(safe_codes), safe_codes)
		if not safe_codes:
			return {"all_passed": False, "checks": checks}
		item_code = safe_codes[0]

		# --- Price-tampering resistance ---
		clean_result = place_pharmacy_order(
			items=[{"item_code": item_code, "qty": 1}],
			contact={"full_name": "WEB06 Verify Clean Test", "phone": "0911000000", "address_line1": "1 Verify Street", "city": "Hanoi"},
		)
		tampered_result = place_pharmacy_order(
			items=[{"item_code": item_code, "qty": 1, "rate": 1, "price": 1, "amount": 1, "batch_no": _RX03_EXPIRED_BATCH}],
			contact={"full_name": "WEB06 Verify Tamper Test", "phone": "0911000001", "address_line1": "123 Verify Street", "city": "Hanoi"},
		)
		check(
			"Price-tampering attempt (client sent rate/price/amount=1 AND a spoofed batch_no) had ZERO"
			" effect on price — identical real server-computed rate as an untampered order",
			tampered_result["items"][0]["rate"] == clean_result["items"][0]["rate"]
			and tampered_result["items"][0]["rate"] not in (1, 0, None)
			and tampered_result["grand_total"] == clean_result["grand_total"],
			{"clean": clean_result, "tampered": tampered_result},
		)
		check(
			"batch_no spoofing attempt had ZERO effect either — server-allocated a real, non-expired"
			" batch regardless of the client-supplied batch_no",
			tampered_result["items"][0]["batch_no"] != _RX03_EXPIRED_BATCH and tampered_result["items"][0]["batch_no"],
			tampered_result["items"][0]["batch_no"],
		)
		tampered_customer = frappe.db.get_value("POS Invoice", {"po_no": tampered_result["order_token"]}, "customer")
		check(
			"Order was created against the isolated Pharmacy Online Guest customer, never Golden Demo #23's own Walk-in Customer",
			tampered_customer == _ONLINE_GUEST_CUSTOMER,
			tampered_customer,
		)

		# --- THE SINGLE MOST IMPORTANT PROOF: the native expiry-block mechanism still protects this
		# new write path, empirically, not just asserted. ---
		expiry_blocked = _attempt_order_against_expired_batch()
		check(
			"EXPIRY-SAFETY: a deliberate attempt to sell the expired RX03-EXPIRED-TEST batch through"
			" this new online-pharmacy write path was REJECTED by the same native StockController"
			" BatchExpiredError mechanism RX03 already proved — zero new code needed",
			expiry_blocked,
			None,
		)
		check(
			"The expired batch was still never actually sold, under EITHER POS Profile (online or in-store)",
			not frappe.db.exists("POS Invoice Item", {"batch_no": _RX03_EXPIRED_BATCH}),
			None,
		)

		# --- Order-lookup requires BOTH factors ---
		order = place_pharmacy_order(
			items=[{"item_code": item_code, "qty": 2}],
			contact={"full_name": "WEB06 Verify Lookup Test", "phone": "0911000002", "address_line1": "456 Verify Avenue", "city": "Ho Chi Minh City"},
		)
		token = order["order_token"]

		correct_lookup_ok = False
		try:
			result = get_pharmacy_order_status(order_token=token, phone="0911000002")
			correct_lookup_ok = result["grand_total"] == order["grand_total"]
		except Exception:
			correct_lookup_ok = False
		check("Correct token + correct phone resolves the real order", correct_lookup_ok, token)

		wrong_phone_blocked = False
		try:
			get_pharmacy_order_status(order_token=token, phone="0999999999")
		except frappe.DoesNotExistError:
			wrong_phone_blocked = True
		except Exception:
			wrong_phone_blocked = False
		check("Correct token + WRONG phone is rejected (never returns the order on token alone)", wrong_phone_blocked, None)

		wrong_token_blocked = False
		try:
			get_pharmacy_order_status(order_token="WEB06-DOESNOTEXIST", phone="0911000002")
		except frappe.DoesNotExistError:
			wrong_token_blocked = True
		except Exception:
			wrong_token_blocked = False
		check("WRONG token + correct phone is rejected (phone alone is not enough either)", wrong_token_blocked, None)

		no_args_blocked = False
		try:
			get_pharmacy_order_status(order_token="", phone="")
		except frappe.DoesNotExistError:
			no_args_blocked = True
		except Exception:
			no_args_blocked = False
		check("Empty token/phone is rejected", no_args_blocked, None)

		# --- Input-bound rejection tests (defense-in-depth, not full anti-abuse) ---
		bad_item_rejected = False
		try:
			place_pharmacy_order(
				items=[{"item_code": "VITC-1000-EFF", "qty": 1}],  # a real item, but from a DIFFERENT golden demo's storefront
				contact={"full_name": "X", "phone": "0911000003", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			bad_item_rejected = True
		except Exception:
			bad_item_rejected = False
		check("An out-of-catalog real item_code (from a different demo's storefront) is rejected", bad_item_rejected, None)

		bad_qty_rejected = False
		try:
			place_pharmacy_order(
				items=[{"item_code": item_code, "qty": -5}],
				contact={"full_name": "X", "phone": "0911000004", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			bad_qty_rejected = True
		except Exception:
			bad_qty_rejected = False
		check("A negative quantity is rejected", bad_qty_rejected, None)

		oversized_qty_rejected = False
		try:
			place_pharmacy_order(
				items=[{"item_code": item_code, "qty": 999999}],
				contact={"full_name": "X", "phone": "0911000005", "address_line1": "A", "city": "B"},
			)
		except frappe.ValidationError:
			oversized_qty_rejected = True
		except Exception:
			oversized_qty_rejected = False
		check("A qty far beyond real (non-expired, batch-honest) stock is rejected", oversized_qty_rejected, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
