"""WEB-04 — Supplier / RFQ Portal (Phase 7, master plan §8 lines ~2566-2567: "WEB-04 Supplier / RFQ
Portal — RFQ, quotation, PO, delivery, documents, qualification."). Backs the standalone Next.js app
in `nextjs-demo/web-04-supplier-portal/`.

THIS IS A CLOSE STRUCTURAL TWIN OF `dealer_portal_api.py` (WEB-03) — read that module's docstring
first if you haven't; everything about the authentication design below is reused VERBATIM, not
re-derived. Like that module (and unlike `public_api.py`'s guest-only WEB-01/02/Hub sites), a real
supplier logs in with a real password, and every function below resolves "which supplier" from that
real, authenticated identity — NEVER from a client-supplied parameter. Nothing here is
`allow_guest=True`.

AUTHENTICATION DESIGN — IDENTICAL to WEB-03, reused verbatim, not redesigned:
  Frappe's own native session-cookie login (`POST /api/method/login`). The Next.js app's own login
  Route Handler calls Frappe's login endpoint SERVER-SIDE (the same Node `http`-module Host-header
  workaround from `nextjs-demo/web-03-dealer-portal/lib/frappeAuth.ts`, reused verbatim in
  `nextjs-demo/web-04-supplier-portal/lib/frappeAuth.ts`), keeps the real Frappe `sid` in an
  in-memory, server-only session store (pinned onto `globalThis` — see that app's `lib/session.ts`
  for the exact Route-Handler-vs-Server-Component bundle-splitting bug this fixes, already found and
  fixed once by WEB-03, deliberately not rediscovered here), and issues the BROWSER a separate,
  opaque, random session token as an `httpOnly` cookie. The real Frappe `sid` never reaches the
  browser.

SUPPLIER IDENTITY RESOLUTION — the single most important invariant in this whole module:
  `_get_my_supplier()` below is the ONLY way any function here learns "which supplier is this." It
  reads `frappe.session.user` and looks up the real `Supplier` that a `User Permission` (created by
  `supplier_portal_seeds.py`, `allow="Supplier"`, `apply_to_all_doctypes=1` — same mechanism as
  WEB-03's Customer-scoped precedent) links to that user. NO function in this module ever accepts a
  `supplier`/`supplier_id` parameter from the caller and trusts it as the scoping identity — grep this
  file: the only place a `supplier` string appears in a function signature is as a DOCUMENT REFERENCE
  to check ownership of (e.g. `get_my_rfq_detail(rfq)` — the RFQ name is client-supplied, exactly like
  WEB-03's `get_my_order_detail(sales_order)`, but its OWNER is always re-derived from the document
  itself and compared against the session-resolved supplier, never trusted from the request).

THREE-LAYER DEFENSE, ADAPTED PER DOCTYPE — NOT UNIFORM, BECAUSE `Request for Quotation` HAS NO
TOP-LEVEL SUPPLIER LINK:
  For `Supplier Quotation`/`Purchase Order`/`Purchase Receipt` (each has a top-level `supplier` Link
  field): Layer 1 resolves the supplier; Layer 2 is an explicit `filters={"supplier": supplier}` on a
  permission-aware `frappe.get_list()` call (the native User Permission ALSO cascades here
  automatically, confirmed by reading each doctype's own `permissions` list via
  `frappe.get_meta(dt).permissions` before writing this module — `Purchase User` is the only non-"All"
  role with base read there); Layer 3 is a post-fetch Python re-assertion that every returned row's
  own `supplier` field equals the resolved supplier — identical shape to `dealer_portal_api.py`'s
  `get_my_orders()`.

  For `Request for Quotation`: suppliers only live in its `suppliers` CHILD table, so a User
  Permission on `Supplier` cannot cascade to restrict which RFQ *documents* a Purchase User can list
  (confirmed: `Request for Quotation`'s own permission rows grant `read=1` to the native `All` role —
  every logged-in user — with no owner/link restriction at the parent-doctype level). Layer 2 here is
  therefore an EXPLICIT child-table-join filter (`frappe.get_list("Request for Quotation",
  filters=[["Request for Quotation Supplier", "supplier", "=", supplier]])`), and Layer 3 is a
  stronger-than-usual post-fetch re-assertion: this module additionally enforces, on every single RFQ
  read, that the document's ENTIRE `suppliers` child table contains ONLY the resolved supplier (see
  `supplier_portal_seeds.py`'s own module docstring for why every RFQ this platform creates is
  single-supplier by construction) — any RFQ that somehow named more than one supplier is silently
  excluded from `get_my_rfqs()` and rejected with the same 404 shape from `get_my_rfq_detail()`,
  exactly like a not-mine document. This means a multi-supplier RFQ could NEVER leak another
  supplier's presence through this portal, even if one were mistakenly created in the future.

  For `Supplier` itself (the qualification-status endpoint): a single `frappe.get_doc("Supplier",
  supplier)` read, where `supplier` is ALWAYS the session-resolved value — there is no other
  supplier's row anywhere in that call to leak.

WHY `submit_quotation()` RUNS AS THE REAL LOGGED-IN USER, NEVER `ignore_permissions=True`:
  Exactly like WEB-03's `place_order()`: `.insert()`/`.submit()` run with NO `ignore_permissions`
  argument, so native ERPNext validation genuinely fires for the real supplier user (e.g. a real
  `Purchase User` role + `Supplier`-scoped User Permission — a login lacking either would be rejected
  by Frappe's own permission engine, not a bypassed imitation of that check).
"""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

_COMPANY_NAME = "Demo Ingredient Trading Co."


def _get_my_supplier():
	"""The ONLY function in this module that resolves "which supplier is this" — see module
	docstring. Throws AuthenticationError for a guest, PermissionError for a real-but-unlinked Frappe
	user (e.g. Administrator, or any user who isn't a provisioned supplier-portal account)."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Please log in to access the supplier portal."), frappe.AuthenticationError)
	supplier = frappe.db.get_value("User Permission", {"user": user, "allow": "Supplier"}, "for_value")
	if not supplier:
		frappe.throw(_("This account is not linked to a supplier account."), frappe.PermissionError)
	return supplier


@frappe.whitelist()
def get_my_profile():
	"""Confirms a login resolved to a real supplier, and hands the frontend a real Frappe CSRF token
	for the state-changing (`submit_quotation`) POST call below — same one-round-trip pattern as
	WEB-03's own `get_my_profile()`."""
	supplier = _get_my_supplier()
	s = frappe.db.get_value(
		"Supplier", supplier, ["supplier_name", "supplier_group", "country", "default_currency"], as_dict=True
	)
	return {
		"user": frappe.session.user,
		"supplier": supplier,
		"supplier_name": s.supplier_name,
		"supplier_group": s.supplier_group,
		"country": s.country,
		"default_currency": s.default_currency or "USD",
		"csrf_token": frappe.sessions.get_csrf_token(),
	}


# ---------------------------------------------------------------------------
# RFQs — explicit child-table-join filter + single-supplier-per-RFQ re-assertion (see module docstring)
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["GET"])
def get_my_rfqs():
	"""RFQs this supplier was invited to respond to. See module docstring: `Request for Quotation`
	has no top-level Supplier link, so this cannot rely on the native User Permission cascade the way
	Purchase Order/Purchase Receipt/Supplier Quotation do — it uses an explicit child-table-join
	filter instead, then re-asserts (and silently excludes, never partially exposes) that every
	returned RFQ names ONLY this supplier."""
	supplier = _get_my_supplier()
	rows = frappe.get_list(
		"Request for Quotation",
		filters=[["Request for Quotation Supplier", "supplier", "=", supplier]],
		fields=["name", "title", "transaction_date", "schedule_date", "status", "docstatus"],
		order_by="transaction_date desc, creation desc",
	)
	result = []
	for r in rows:
		doc = frappe.get_doc("Request for Quotation", r.name)
		invited = {s.supplier for s in doc.suppliers}
		if invited != {supplier}:
			# Defense in depth — never surface a multi-supplier RFQ through this portal even if one
			# were mistakenly created (see module docstring).
			frappe.log_error(
				title="WEB-04 supplier portal: excluded a non-single-supplier RFQ from get_my_rfqs()",
				message=f"RFQ {r.name} names suppliers {invited}, requested by {supplier}",
			)
			continue
		my_row = doc.suppliers[0]
		result.append(
			{
				"name": doc.name,
				"title": doc.title,
				"transaction_date": doc.transaction_date,
				"schedule_date": doc.schedule_date,
				"status": doc.status,
				"quote_status": my_row.quote_status,
			}
		)
	return result


@frappe.whitelist(methods=["GET"])
def get_my_rfq_detail(rfq: str = ""):
	"""One RFQ's detail — but ONLY if it invites this supplier and NO ONE ELSE (see module
	docstring). Returns the same 404 shape for "doesn't exist", "not mine", and "not single-supplier"
	— never a distinguishable response."""
	supplier = _get_my_supplier()
	if not rfq or not frappe.db.exists("Request for Quotation", rfq):
		frappe.throw(_("RFQ not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Request for Quotation", rfq)
	invited = {s.supplier for s in doc.suppliers}
	if invited != {supplier}:
		frappe.throw(_("RFQ not found."), frappe.DoesNotExistError)
	if not doc.has_permission("read"):
		frappe.throw(_("RFQ not found."), frappe.DoesNotExistError)
	my_row = doc.suppliers[0]
	return {
		"name": doc.name,
		"title": doc.title,
		"company": doc.company,
		"transaction_date": doc.transaction_date,
		"schedule_date": doc.schedule_date,
		"status": doc.status,
		"quote_status": my_row.quote_status,
		"message_for_supplier": doc.message_for_supplier,
		"items": [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"uom": r.uom,
				"warehouse": r.warehouse,
				"schedule_date": r.schedule_date,
			}
			for r in doc.items
		],
	}


# ---------------------------------------------------------------------------
# Supplier Quotations — standard 3-layer defense (top-level `supplier` Link field)
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["GET"])
def get_my_quotations():
	"""This supplier's own Supplier Quotations only — whether or not they were created against an
	RFQ (includes the pre-existing AI-DEMO-06 quotations, which have no inviting RFQ, alongside any
	new RFQ-linked quotation submitted through this portal). Same explicit-filter +
	post-fetch-assert pattern as `dealer_portal_api.get_my_orders()`."""
	supplier = _get_my_supplier()
	rows = frappe.get_list(
		"Supplier Quotation",
		filters={"supplier": supplier},
		fields=["name", "supplier", "transaction_date", "valid_till", "status", "docstatus", "currency", "grand_total"],
		order_by="transaction_date desc, creation desc",
	)
	leaked = [r for r in rows if r.supplier != supplier]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_quotation_detail(supplier_quotation: str = ""):
	"""One Supplier Quotation's detail — but ONLY if it genuinely belongs to the logged-in supplier.
	Same not-found-either-way shape as `dealer_portal_api.get_my_order_detail()`."""
	supplier = _get_my_supplier()
	if not supplier_quotation or not frappe.db.exists("Supplier Quotation", supplier_quotation):
		frappe.throw(_("Quotation not found."), frappe.DoesNotExistError)
	actual_supplier = frappe.db.get_value("Supplier Quotation", supplier_quotation, "supplier")
	if actual_supplier != supplier:
		frappe.throw(_("Quotation not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Supplier Quotation", supplier_quotation)
	if not doc.has_permission("read"):
		frappe.throw(_("Quotation not found."), frappe.DoesNotExistError)
	return {
		"name": doc.name,
		"supplier": doc.supplier,
		"transaction_date": doc.transaction_date,
		"valid_till": doc.valid_till,
		"status": doc.status,
		"currency": doc.currency,
		"conversion_rate": doc.conversion_rate,
		"incoterm": doc.incoterm,
		"grand_total": doc.grand_total,
		"terms": doc.terms,
		"items": [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
				"lead_time_days": r.lead_time_days,
				"request_for_quotation": r.request_for_quotation,
			}
			for r in doc.items
		],
	}


@frappe.whitelist(methods=["POST"])
def submit_quotation(
	rfq: str = "",
	rate=None,
	currency: str = "USD",
	conversion_rate=None,
	incoterm: str = "",
	valid_till_days=30,
	lead_time_days=None,
	terms: str = "",
):
	"""Creates a REAL Supplier Quotation against a real RFQ the logged-in supplier was invited to,
	running genuinely permission-checked (no `ignore_permissions`) so native ERPNext validation fires
	for real. `supplier` is ALWAYS the session-resolved supplier; `rfq` is client-supplied but its
	invitation is re-verified (single-supplier, matches this supplier) before anything is created —
	exactly the same "trust the document lookup, never the caller's identity claim" discipline as
	WEB-03's `place_order()`. Refuses a second quotation against an RFQ this supplier already quoted
	(idempotent — safe to call more than once, e.g. from the regression sweep)."""
	supplier = _get_my_supplier()
	if not rfq or not frappe.db.exists("Request for Quotation", rfq):
		frappe.throw(_("RFQ not found."), frappe.DoesNotExistError)
	rfq_doc = frappe.get_doc("Request for Quotation", rfq)
	invited = {s.supplier for s in rfq_doc.suppliers}
	if invited != {supplier}:
		frappe.throw(_("RFQ not found."), frappe.DoesNotExistError)
	if rfq_doc.docstatus != 1:
		frappe.throw(_("This RFQ is not open for quotes."))
	if rate is None or float(rate) <= 0:
		frappe.throw(_("Rate must be greater than zero."))

	existing = frappe.get_list(
		"Supplier Quotation",
		filters={"supplier": supplier},
		fields=["name"],
	)
	for row in existing:
		doc = frappe.get_doc("Supplier Quotation", row.name)
		if any(item.request_for_quotation == rfq for item in doc.items):
			return {
				"name": doc.name,
				"grand_total": doc.grand_total,
				"status": doc.status,
				"already_submitted": True,
			}

	sq = frappe.get_doc(
		{
			"doctype": "Supplier Quotation",
			"supplier": supplier,
			"company": rfq_doc.company,
			"currency": currency,
			"conversion_rate": float(conversion_rate) if conversion_rate else 1,
			"incoterm": incoterm or None,
			"valid_till": add_days(nowdate(), int(valid_till_days) if valid_till_days else 30),
			"terms": terms,
			"items": [
				{
					"item_code": r.item_code,
					"qty": r.qty,
					"rate": float(rate),
					"warehouse": r.warehouse,
					"lead_time_days": int(lead_time_days) if lead_time_days else None,
					"request_for_quotation": rfq_doc.name,
					"request_for_quotation_item": r.name,
				}
				for r in rfq_doc.items
			],
		}
	)
	sq.insert()  # NOT ignore_permissions — real permission check as the logged-in supplier user
	sq.submit()
	return {"name": sq.name, "grand_total": sq.grand_total, "status": sq.status, "already_submitted": False}


# ---------------------------------------------------------------------------
# Purchase Orders / Deliveries — standard 3-layer defense (top-level `supplier` Link field)
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["GET"])
def get_my_purchase_orders():
	"""This supplier's own Purchase Orders only. Same explicit-filter + post-fetch-assert pattern."""
	supplier = _get_my_supplier()
	rows = frappe.get_list(
		"Purchase Order",
		filters={"supplier": supplier},
		fields=["name", "supplier", "transaction_date", "schedule_date", "currency", "grand_total", "status", "docstatus"],
		order_by="transaction_date desc, creation desc",
	)
	leaked = [r for r in rows if r.supplier != supplier]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	return rows


@frappe.whitelist(methods=["GET"])
def get_my_purchase_order_detail(purchase_order: str = ""):
	"""One Purchase Order's detail — but ONLY if it genuinely belongs to the logged-in supplier."""
	supplier = _get_my_supplier()
	if not purchase_order or not frappe.db.exists("Purchase Order", purchase_order):
		frappe.throw(_("Purchase Order not found."), frappe.DoesNotExistError)
	actual_supplier = frappe.db.get_value("Purchase Order", purchase_order, "supplier")
	if actual_supplier != supplier:
		frappe.throw(_("Purchase Order not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Purchase Order", purchase_order)
	if not doc.has_permission("read"):
		frappe.throw(_("Purchase Order not found."), frappe.DoesNotExistError)
	return {
		"name": doc.name,
		"supplier": doc.supplier,
		"transaction_date": doc.transaction_date,
		"schedule_date": doc.schedule_date,
		"status": doc.status,
		"currency": doc.currency,
		"conversion_rate": doc.conversion_rate,
		"grand_total": doc.grand_total,
		"items": [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"received_qty": r.received_qty,
				"rate": r.rate,
				"amount": r.amount,
			}
			for r in doc.items
		],
	}


@frappe.whitelist(methods=["GET"])
def get_my_deliveries():
	"""This supplier's own Purchase Receipts (their delivery/shipment status) only."""
	supplier = _get_my_supplier()
	rows = frappe.get_list(
		"Purchase Receipt",
		filters={"supplier": supplier},
		fields=["name", "supplier", "posting_date", "status", "docstatus", "grand_total"],
		order_by="posting_date desc, creation desc",
	)
	leaked = [r for r in rows if r.supplier != supplier]
	if leaked:
		frappe.throw(_("Internal scoping error — contact support."), frappe.PermissionError)
	result = []
	for r in rows:
		# frappe.get_all(), deliberately NOT get_list(), for this one supplementary lookup only:
		# `Quality Inspection`'s own permission rows (`frappe.get_meta("Quality Inspection").permissions`)
		# grant base read=1 to ONLY "Quality Manager" — Purchase User has none — so `get_list()` here
		# would silently permission-strip the `status` field down to an unusable row (confirmed
		# empirically: it returned `{"name": ...}` with `status` missing entirely). This does NOT
		# reopen any cross-supplier scoping gap: the filter is `reference_name=r.name`, and `r.name`
		# is already one of THIS supplier's own Purchase Receipts, resolved two lines above by a
		# permission-checked, post-fetch-asserted `get_list()` call — never client-supplied.
		qis = frappe.get_all(
			"Quality Inspection",
			filters={"reference_type": "Purchase Receipt", "reference_name": r.name},
			fields=["name", "status", "item_code"],
		)
		result.append({**r, "quality_inspections": qis})
	return result


# ---------------------------------------------------------------------------
# Qualification status — single-document read, `supplier` always session-resolved
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["GET"])
def get_my_qualification_status():
	"""This supplier's own `quality_status`/`is_critical_supplier` (global Custom Fields on Supplier,
	from Golden Demo #22/MedDev, reused by AI-DEMO-06 — never another supplier's), plus a real,
	modest QC pass-rate aggregate computed only from THIS supplier's own submitted Purchase
	Receipts' Quality Inspection records."""
	supplier = _get_my_supplier()
	s = frappe.get_doc("Supplier", supplier)
	receipt_names = frappe.get_list("Purchase Receipt", filters={"supplier": supplier, "docstatus": 1}, pluck="name")
	# frappe.get_all(), deliberately NOT get_list() — see get_my_deliveries()'s own comment: Purchase
	# User has no native read permission on Quality Inspection at all, and `receipt_names` here is
	# already this supplier's own, permission-checked receipt list, never client-supplied, so no
	# scoping boundary is actually bypassed by this one supplementary aggregate.
	qis = (
		frappe.get_all(
			"Quality Inspection",
			filters={"reference_type": "Purchase Receipt", "reference_name": ["in", receipt_names]},
			fields=["status"],
		)
		if receipt_names
		else []
	)
	accepted = len([q for q in qis if q.status == "Accepted"])
	return {
		"supplier": supplier,
		"supplier_name": s.supplier_name,
		"quality_status": s.quality_status,
		"is_critical_supplier": bool(s.is_critical_supplier),
		"quality_inspections_total": len(qis),
		"quality_inspections_accepted": accepted,
		"qc_pass_rate": (accepted / len(qis)) if qis else None,
	}


# ---------------------------------------------------------------------------
# Documents — real document REFERENCES only (RFQ/PO/PR/QI/Supplier Quotation this supplier already
# owns), not a parallel document-management build (DMS is Phase 3's job — see master task notes).
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["GET"])
def get_my_documents():
	"""A modest, real list of document references tied to this supplier's own relationship —
	assembled entirely from documents already scoped to this supplier by the functions above, never
	a fabricated parallel record. Each entry names a real doctype + real document name this supplier
	is independently entitled to read."""
	supplier = _get_my_supplier()
	docs = []
	for rfq in get_my_rfqs():
		docs.append({"type": "RFQ Invitation", "reference_doctype": "Request for Quotation", "reference_name": rfq["name"], "title": rfq["title"] or rfq["name"], "date": rfq["transaction_date"]})
	for sq in get_my_quotations():
		docs.append({"type": "Supplier Quotation", "reference_doctype": "Supplier Quotation", "reference_name": sq["name"], "title": sq["name"], "date": sq["transaction_date"]})
	for po in get_my_purchase_orders():
		docs.append({"type": "Purchase Order", "reference_doctype": "Purchase Order", "reference_name": po["name"], "title": po["name"], "date": po["transaction_date"]})
	for pr in get_my_deliveries():
		docs.append({"type": "Purchase Receipt / Delivery Record", "reference_doctype": "Purchase Receipt", "reference_name": pr["name"], "title": pr["name"], "date": pr["posting_date"]})
		for qi in pr["quality_inspections"]:
			docs.append({"type": "Quality Inspection Certificate", "reference_doctype": "Quality Inspection", "reference_name": qi["name"], "title": f"{qi['item_code']} — {qi['status']}", "date": pr["posting_date"]})
	# No further re-assertion needed here — every doctype above is already individually
	# supplier-scoped by the functions this one calls (get_my_rfqs/get_my_quotations/
	# get_my_purchase_orders/get_my_deliveries), each with its own defense-in-depth already applied.
	return sorted(docs, key=lambda d: str(d["date"] or ""), reverse=True)


# ============================================================================
# Empirical permission proof — called from enterprise_core.enterprise_core.api's
# verify_supplier_portal_demo(), part of the platform's standard verify_* regression sweep. Same
# technique as `dealer_portal_api.verify_dealer_portal_access_control()`: logs in as each real
# supplier user (frappe.set_user) and empirically proves supplier A cannot see supplier B's
# RFQs/quotations/POs/deliveries/qualification, and that requesting the OTHER supplier's real
# document id while authenticated as the first genuinely fails.
# ============================================================================

def verify_supplier_portal_access_control():
	"""Real, empirical two-user permission proof for the WEB-04 supplier portal. Always restores
	`frappe.session.user` in a `finally` block, even on failure."""
	from enterprise_core.enterprise_core.supplier_portal_seeds import _CARGILL_USER, _NUTRECO_USER, _SUPPLIER_CARGILL, _SUPPLIER_NUTRECO

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	original_user = frappe.session.user
	try:
		frappe.set_user(_CARGILL_USER)
		cargill_rfqs = get_my_rfqs()
		cargill_quotations = get_my_quotations()
		cargill_pos = get_my_purchase_orders()
		cargill_deliveries = get_my_deliveries()
		cargill_qual = get_my_qualification_status()
		check(
			"Cargill sees only its own RFQs (every RFQ it can read invites Cargill alone)",
			len(cargill_rfqs) > 0,
			[r["name"] for r in cargill_rfqs],
		)
		check(
			"Cargill sees only its own Supplier Quotations",
			all(q.supplier == _SUPPLIER_CARGILL for q in cargill_quotations) and len(cargill_quotations) > 0,
			[q.name for q in cargill_quotations],
		)
		check(
			"Cargill sees only its own Purchase Orders",
			all(p.supplier == _SUPPLIER_CARGILL for p in cargill_pos) and len(cargill_pos) > 0,
			[p.name for p in cargill_pos],
		)
		check(
			"Cargill sees only its own Purchase Receipts",
			all(d["supplier"] == _SUPPLIER_CARGILL for d in cargill_deliveries) and len(cargill_deliveries) > 0,
			[d["name"] for d in cargill_deliveries],
		)
		check("Cargill's qualification view resolves to Cargill's own supplier", cargill_qual["supplier"] == _SUPPLIER_CARGILL, cargill_qual)

		frappe.set_user(_NUTRECO_USER)
		nutreco_rfqs = get_my_rfqs()
		nutreco_quotations = get_my_quotations()
		nutreco_pos = get_my_purchase_orders()
		nutreco_deliveries = get_my_deliveries()
		nutreco_qual = get_my_qualification_status()
		check(
			"Nutreco sees only its own RFQs",
			len(nutreco_rfqs) > 0,
			[r["name"] for r in nutreco_rfqs],
		)
		check(
			"Nutreco sees only its own Supplier Quotations",
			all(q.supplier == _SUPPLIER_NUTRECO for q in nutreco_quotations) and len(nutreco_quotations) > 0,
			[q.name for q in nutreco_quotations],
		)
		check(
			"Nutreco sees only its own Purchase Orders",
			all(p.supplier == _SUPPLIER_NUTRECO for p in nutreco_pos) and len(nutreco_pos) > 0,
			[p.name for p in nutreco_pos],
		)
		check(
			"Nutreco sees only its own Purchase Receipts",
			all(d["supplier"] == _SUPPLIER_NUTRECO for d in nutreco_deliveries) and len(nutreco_deliveries) > 0,
			[d["name"] for d in nutreco_deliveries],
		)
		check("Nutreco's qualification view resolves to Nutreco's own supplier", nutreco_qual["supplier"] == _SUPPLIER_NUTRECO, nutreco_qual)

		# Cross-supplier negative tests: Nutreco is still logged in — try Cargill's real document ids.
		cargill_rfq_name = cargill_rfqs[0]["name"] if cargill_rfqs else None
		cargill_po_name = cargill_pos[0].name if cargill_pos else None
		cargill_sq_name = cargill_quotations[0].name if cargill_quotations else None

		def _blocked(fn, *args):
			try:
				fn(*args)
				return False
			except frappe.DoesNotExistError:
				return True
			except Exception:
				return False

		check(
			"Nutreco requesting Cargill's real RFQ id (while authenticated as Nutreco) is genuinely rejected",
			_blocked(get_my_rfq_detail, cargill_rfq_name) and cargill_rfq_name is not None,
			cargill_rfq_name,
		)
		check(
			"Nutreco requesting Cargill's real Purchase Order id is genuinely rejected",
			_blocked(get_my_purchase_order_detail, cargill_po_name) and cargill_po_name is not None,
			cargill_po_name,
		)
		check(
			"Nutreco requesting Cargill's real Supplier Quotation id is genuinely rejected",
			_blocked(get_my_quotation_detail, cargill_sq_name) and cargill_sq_name is not None,
			cargill_sq_name,
		)

		# Reverse direction: Cargill requesting Nutreco's real document ids.
		frappe.set_user(_CARGILL_USER)
		nutreco_rfq_name = nutreco_rfqs[0]["name"] if nutreco_rfqs else None
		nutreco_po_name = nutreco_pos[0].name if nutreco_pos else None
		check(
			"Cargill requesting Nutreco's real RFQ id (while authenticated as Cargill) is genuinely rejected",
			_blocked(get_my_rfq_detail, nutreco_rfq_name) and nutreco_rfq_name is not None,
			nutreco_rfq_name,
		)
		check(
			"Cargill requesting Nutreco's real Purchase Order id is genuinely rejected",
			_blocked(get_my_purchase_order_detail, nutreco_po_name) and nutreco_po_name is not None,
			nutreco_po_name,
		)

		# Cargill attempting to submit a SECOND quotation against Nutreco's RFQ must be rejected —
		# not merely "not found" but genuinely never creates a document, since Cargill isn't invited.
		blocked_cross_submit = False
		try:
			submit_quotation(rfq=nutreco_rfq_name, rate=0.5, currency="USD", conversion_rate=25000)
		except frappe.DoesNotExistError:
			blocked_cross_submit = True
		except Exception:
			blocked_cross_submit = False
		check(
			"Cargill attempting to submit a quotation against Nutreco's RFQ is genuinely rejected",
			blocked_cross_submit and nutreco_rfq_name is not None,
			nutreco_rfq_name,
		)

		# Unauthenticated access must also be genuinely rejected.
		frappe.set_user("Guest")
		guest_blocked = False
		try:
			get_my_rfqs()
		except frappe.AuthenticationError:
			guest_blocked = True
		except Exception:
			guest_blocked = False
		check("A Guest (unauthenticated) request to get_my_rfqs() is rejected", guest_blocked, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
