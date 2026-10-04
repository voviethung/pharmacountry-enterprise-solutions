"""WEB-04 — Supplier / RFQ Portal (Phase 7, master plan §8 lines ~2566-2567: "WEB-04 Supplier / RFQ
Portal — RFQ, quotation, PO, delivery, documents, qualification."). Seed module for 2 real portal
Users + Supplier-scoped User Permissions, plus 2 new, ISOLATED Request for Quotation documents,
backing the authenticated `supplier_portal_api.py` and the standalone Next.js app in
`nextjs-demo/web-04-supplier-portal/`.

WHY REUSE Cargill Asia Trading Pte Ltd / Nutreco South America S.A. — NOT NEW, ISOLATED SUPPLIERS:
  Unlike WEB-03 (which minted brand-new dealers because Golden Demo #25's own dealers carry a
  baked-in "exactly N Sales Order" idempotency assumption), the two real suppliers this build reuses
  — Cargill Asia Trading Pte Ltd and Nutreco South America S.A. (Golden Demo #27, Ingredient
  Trading) — were confirmed SAFE to build on top of by reading both `ingredient_trading_seeds.py`
  and `ai_procurement_assistant_seeds.py` in full before writing a single line here: every guard in
  both files is a MARKER/TITLE existence check (`frappe.db.exists("Purchase Order", {"title":
  marker})`, `frappe.db.exists("Supplier Quotation", {"title": marker})`), never a "does this
  supplier have exactly N related documents" count. Reusing these two real suppliers — which already
  carry a genuine multi-currency PO/PR/PI/QI history AND 2 real pre-existing Supplier Quotations
  (`AI6-SQ-CARGILL-SOY-01`/`AI6-SQ-NUTRECO-SOY-01`) — gives the portal an immediately-plausible,
  richly-populated demo with zero fabricated backstory. This module only ever creates NEW documents
  using the globally-distinct `WEB04-...` title-marker prefix below, so nothing here can ever collide
  with `IT-PO-...`/`AI6-SQ-...` markers or corrupt either golden demo's own idempotency assumptions.
  The isolated, demo-only suppliers used by AI-DEMO-06's own qualification-workflow validation
  (`Mekong AgriSource Trading Co. (AI-DEMO-06)`) and Golden Demo #22/MedDev
  (`MedTech Precision Components Ltd.`) are deliberately left untouched by this module.

RFQ DESIGN DECISION — ONE SUPPLIER PER Request for Quotation, NEVER A SHARED MULTI-SUPPLIER RFQ:
  Native ERPNext's `Request for Quotation` doctype supports inviting MULTIPLE suppliers in a single
  document's `suppliers` child table — a real, common pattern (compare quotes from several vendors
  against one shared RFQ). This module deliberately does NOT use that shared-document shape. Each
  RFQ created here names EXACTLY one supplier. Reasoning: this project's hardest constraint is that
  no supplier may ever see another supplier's data under any circumstance. A shared multi-supplier
  RFQ document would hold OTHER suppliers' quote_status/contact rows inside the SAME document a
  supplier is otherwise entitled to read — every read of that document would need to carefully
  scrub every other supplier's rows before returning it to the frontend, and a single missed field
  would be a real cross-supplier leak. Giving each supplier their OWN RFQ document removes that
  entire risk category by construction: there is structurally no other supplier's data anywhere in
  a document a given supplier can read. `supplier_portal_api.py`'s `get_my_rfqs()`/
  `get_my_rfq_detail()` additionally assert this invariant defensively on every read (see that
  module's docstring) — even a future, mistakenly-created multi-supplier RFQ could never be served
  through this portal. The real trade-off documented here, not silently glossed over: this means the
  portal cannot demonstrate ERPNext's native side-by-side RFQ comparison workflow (all suppliers
  responding to the identical RFQ) — a deliberate, proportionate simplification given the hard
  isolation constraint, not an oversight.

FLOW DESIGN — one supplier responds, one stays pending (a genuinely mixed, realistic story):
  - `WEB04-RFQ-CARGILL-01`: Cargill invited to quote 30,000 kg of Soybean Meal 48%. This module's
    own `seed_supplier_portal_quotation_response()` then logs in AS Cargill's real portal user
    (`frappe.set_user`, no `ignore_permissions`) and calls the SAME `submit_quotation()` function the
    live portal API exposes, proving the write path works end-to-end as a genuinely-authenticated,
    permission-checked supplier — not a seed-side shortcut. Cargill's portal therefore shows: 1 RFQ
    (Responded), 2 Supplier Quotations (the pre-existing AI6 one + this new one), full PO/PR/QI
    history.
  - `WEB04-RFQ-NUTRECO-01`: Nutreco invited to quote 20,000 kg of Soybean Meal 48%, deliberately left
    UNANSWERED (status stays "Pending") — Nutreco's portal shows a genuine "invited, awaiting your
    response" state alongside their own pre-existing AI6 quotation (which was never linked to any
    RFQ) and their own PO/PR/QI history. This mixed story (one supplier responded, one hasn't) is
    more realistic than a bare, symmetrical list.

PORTAL USER DESIGN — mirrors WEB-03/3PL's proven "restricted portal user" pattern:
  - 2 real, distinct Frappe Users (`supplier.cargill.portal@pharmacountry.vn` /
    `supplier.nutreco.portal@pharmacountry.vn`, same demo password convention as WEB-03/3PL,
    `Demo@1234` — a placeholder demo credential, documented here and in the portal app's own README,
    never hardcoded into frontend page components).
  - Role: native `Purchase User` only — confirmed by reading each relevant doctype's own permission
    rows (`frappe.get_meta(dt).permissions`) before choosing this: `Purchase User` is the ONLY
    non-"All" role carrying base (permlevel 0) read on `Supplier Quotation`/`Purchase Order`/
    `Purchase Receipt`/`Supplier`, and carries `submit=1` on `Supplier Quotation` (required for a
    supplier to actually submit their own quotation for real). `Request for Quotation` itself
    already grants `read=1` to the native `All` role (every logged-in user), so no extra role is
    needed there. This is, like WEB-03's own `Accounts User` choice, a BROADER native role than the
    minimum a real production supplier login would want (it also grants visibility into e.g. other
    Buying-module doctypes not Supplier-linked) — a disclosed, deliberate simplification. The
    `User Permission` created below still enforces the hard no-cross-supplier-leakage requirement for
    every doctype that carries a top-level Supplier link, which covers every endpoint this portal
    actually exposes.
  - One `User Permission` per supplier user: `allow="Supplier"`, `for_value=<their own Supplier>`,
    `apply_to_all_doctypes=1` — same mechanism WEB-03/3PL proved cascades automatically (via
    `frappe.get_list()`/permission-aware ORM calls) to any doctype with a top-level Link to Supplier:
    Supplier Quotation, Purchase Order, Purchase Receipt. `Request for Quotation` does NOT carry a
    top-level Supplier link (suppliers only live in its child table) so this cascade does NOT apply
    there — `supplier_portal_api.py` compensates with an explicit child-table-join filter AND a
    post-fetch Python re-assertion instead (see that module's docstring for the full reasoning).

`supplier_portal_api.py`'s own module docstring documents the full authentication design (Frappe
session cookie via native `/api/method/login`, held server-side by the Next.js app, never exposed to
browser JS — IDENTICAL mechanism to WEB-03, reused verbatim) — this module only concerns itself with
the real ERP-side data/identity fixtures that design depends on.
"""

import frappe
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Ingredient Trading Co."
_QUARANTINE_WAREHOUSE = "Import Quarantine - DIT"

_ITEM_SOY = "SOYBEAN-MEAL-48"

_SUPPLIER_CARGILL = "Cargill Asia Trading Pte Ltd"
_SUPPLIER_NUTRECO = "Nutreco South America S.A."

_DEMO_USER_DOMAIN = "pharmacountry.vn"
_DEMO_USER_PASSWORD = "Demo@1234"
_CARGILL_USER = f"supplier.cargill.portal@{_DEMO_USER_DOMAIN}"
_NUTRECO_USER = f"supplier.nutreco.portal@{_DEMO_USER_DOMAIN}"

_PORTAL_ROLES = ("Purchase User",)
# See module docstring: the only non-"All" role carrying base read on Supplier
# Quotation/Purchase Order/Purchase Receipt/Supplier, and submit=1 on Supplier Quotation.

_RFQ_CARGILL_MARKER = "WEB04-RFQ-CARGILL-01"
_RFQ_NUTRECO_MARKER = "WEB04-RFQ-NUTRECO-01"
_RFQ_CARGILL_QTY = 30000
_RFQ_NUTRECO_QTY = 20000

_CARGILL_QUOTE_RATE = 0.44  # USD/kg — a fresh, distinct quote from Cargill's existing AI6 quote
_CARGILL_QUOTE_CONVERSION_RATE = 24900
_CARGILL_QUOTE_LEAD_TIME_DAYS = 18


# ---------------------------------------------------------------------------
# Master data — 2 portal Users + Supplier-scoped User Permission
# ---------------------------------------------------------------------------

def _ensure_portal_user(email, first_name, supplier):
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
	# Supplier-scoped User Permission, apply_to_all_doctypes=1 — see module docstring.
	if not frappe.db.exists("User Permission", {"user": email, "allow": "Supplier", "for_value": supplier}):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Supplier", "for_value": supplier, "apply_to_all_doctypes": 1}
		).insert(ignore_permissions=True)
		created = True
	return created


def seed_supplier_portal_master_data():
	"""WEB-04 master data — 2 portal Users on the 2 real, pre-existing Ingredient Trading suppliers
	(Cargill/Nutreco), each restricted via a Supplier-scoped User Permission to their own data only.
	Does NOT create the Suppliers themselves — those are Golden Demo #27's own real fixtures."""
	if not frappe.db.exists("Supplier", _SUPPLIER_CARGILL) or not frappe.db.exists("Supplier", _SUPPLIER_NUTRECO):
		return "seed_supplier_portal_master_data: SKIPPED — run seed_ingredient_trading_master_data first."
	cargill_user_created = _ensure_portal_user(_CARGILL_USER, "Cargill Supplier Portal", _SUPPLIER_CARGILL)
	nutreco_user_created = _ensure_portal_user(_NUTRECO_USER, "Nutreco Supplier Portal", _SUPPLIER_NUTRECO)
	return (
		f"seed_supplier_portal_master_data: Cargill user {'created' if cargill_user_created else 'already existed'}, "
		f"Nutreco user {'created' if nutreco_user_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# RFQ invitations — one isolated, single-supplier RFQ per supplier (see module docstring)
# ---------------------------------------------------------------------------

def _ensure_rfq(marker, supplier, qty):
	existing = frappe.db.exists("Request for Quotation", {"title": marker})
	if existing:
		return existing, False
	rfq = frappe.get_doc(
		{
			"doctype": "Request for Quotation",
			"title": marker,
			"company": _COMPANY_NAME,
			"transaction_date": nowdate(),
			"message_for_supplier": "Please provide your best quote for the items listed below.",
			"suppliers": [{"supplier": supplier}],
			"items": [
				{
					"item_code": _ITEM_SOY,
					"qty": qty,
					"uom": "Kg",
					"stock_uom": "Kg",
					"conversion_factor": 1,
					"warehouse": _QUARANTINE_WAREHOUSE,
					"schedule_date": add_days(nowdate(), 30),
				}
			],
		}
	)
	rfq.insert(ignore_permissions=True)
	rfq.submit()
	return rfq.name, True


def seed_supplier_portal_rfq_flow():
	"""2 real, isolated, single-supplier RFQs: Cargill invited for 30,000kg, Nutreco for 20,000kg —
	both Soybean Meal 48%, both distinct in quantity from any existing Golden Demo #27/AI-DEMO-06
	document (which use 50,000kg). Neither RFQ names more than one supplier (see module docstring)."""
	if not frappe.db.exists("Supplier", _SUPPLIER_CARGILL) or not frappe.db.exists("Supplier", _SUPPLIER_NUTRECO):
		return "seed_supplier_portal_rfq_flow: SKIPPED — run seed_ingredient_trading_master_data first."
	cargill_rfq, cargill_created = _ensure_rfq(_RFQ_CARGILL_MARKER, _SUPPLIER_CARGILL, _RFQ_CARGILL_QTY)
	nutreco_rfq, nutreco_created = _ensure_rfq(_RFQ_NUTRECO_MARKER, _SUPPLIER_NUTRECO, _RFQ_NUTRECO_QTY)
	return (
		f"seed_supplier_portal_rfq_flow: Cargill RFQ {cargill_rfq} {'created' if cargill_created else 'already existed'}, "
		f"Nutreco RFQ {nutreco_rfq} {'created' if nutreco_created else 'already existed'}."
	)


# ---------------------------------------------------------------------------
# Live quotation response — Cargill responds for real, through the real API, as the real user
# ---------------------------------------------------------------------------

def seed_supplier_portal_quotation_response():
	"""Logs in AS Cargill's real portal user (frappe.set_user, restored in `finally`, no
	`ignore_permissions` anywhere in this call chain) and calls the SAME `submit_quotation()`
	function the live Next.js portal calls, so this seed step is itself proof the write path works
	end-to-end for a genuinely-authenticated, permission-checked supplier — not a seed-side
	shortcut. Idempotent: `submit_quotation()` itself refuses a second quotation against an
	RFQ that already has one from the calling supplier (see `supplier_portal_api.py`)."""
	from enterprise_core.enterprise_core.supplier_portal_api import submit_quotation

	rfq = frappe.db.get_value("Request for Quotation", {"title": _RFQ_CARGILL_MARKER}, "name")
	if not rfq:
		return "seed_supplier_portal_quotation_response: SKIPPED — run seed_supplier_portal_rfq_flow first."
	original_user = frappe.session.user
	try:
		frappe.set_user(_CARGILL_USER)
		result = submit_quotation(
			rfq=rfq,
			rate=_CARGILL_QUOTE_RATE,
			currency="USD",
			conversion_rate=_CARGILL_QUOTE_CONVERSION_RATE,
			incoterm="CIF",
			valid_till_days=30,
			lead_time_days=_CARGILL_QUOTE_LEAD_TIME_DAYS,
			terms="Payment terms: 30% advance T/T on order confirmation, 70% balance within 21 days after Bill of Lading date.",
		)
	finally:
		frappe.set_user(original_user)
	return f"seed_supplier_portal_quotation_response: {result}"


def seed_supplier_portal_demo_data():
	"""Top-level orchestrator — idempotent, safe to re-run any number of times. This IS the seed
	re-entry point for the regression sweep (not wired into after_install/after_migrate — see
	`verify_supplier_portal_demo()` in api.py, same precedent as WEB-03's own
	`dealer_portal_seeds.py`)."""
	m1 = seed_supplier_portal_master_data()
	m2 = seed_supplier_portal_rfq_flow()
	m3 = seed_supplier_portal_quotation_response()
	return f"{m1} | {m2} | {m3}"
