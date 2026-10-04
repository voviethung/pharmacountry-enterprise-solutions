"""Phase 6A — AI-DEMO-06 (Procurement Assistant) seed data + validations. Registers the 5 new
`AI Tool` rows this demo adds to the SAME registry AI-DEMO-01/02/03/05 built (`extract_supplier_
quotation`, `normalize_supplier_quotations`, `compare_supplier_quotations`,
`summarize_supplier_history`, `recommend_supplier_qualification_change`), 2 Prompt Template/AI
Action pairs (one NO-DRAFT for the 4 analytical use cases, one DRAFT-gated for the supplier-
qualification recommendation — see `ai_procurement_assistant.py`'s own module docstring for the
hybrid-design rationale), and 2 kinds of new demo data:

1. **2 real `Supplier Quotation` records** on Golden Demo #27 (Ingredient Trading)'s real
   `SOYBEAN-MEAL-48` item, one from each of its 2 real suppliers (Cargill Asia Trading Pte Ltd,
   Nutreco South America S.A.) — genuinely different currency conversion_rate (different quote
   dates), incoterm, per-item rate/lead_time_days, and free-text payment terms, so
   `normalize_supplier_quotations()`/`compare_supplier_quotations()` have a real, non-trivial
   2-supplier comparison to resolve (Nutreco quotes a lower per-kg price but a 35-day lead time
   vs Cargill's faster 21 days — a genuine trade-off, not a contrived one-sided example).
   `Supplier Quotation` did not exist anywhere in this codebase before this demo (confirmed by
   grep) — these are the platform's first, and this demo's own seed data, not a fixture
   borrowed from Golden Demo #27's own DP-680..685 seed chain (which never created one).

2. **A brand-new, ISOLATED Supplier + Item + declining 3-shipment history** for the
   supplier-qualification-recommendation use case — reuses Golden Demo #27's own Company/
   warehouses/USD-payable-account plumbing (safe: `verify_ingredient_trading_golden_demo()`'s own
   8 checks are all keyed to specific, differently-named suppliers/items/PO titles — confirmed by
   reading `api.verify_ingredient_trading_golden_demo()` in full before writing this — so a
   distinctly-named 3rd supplier/item cannot collide with any of them, and
   `get_ingredient_trading_margin_report()`'s own per-item aggregation is a super-set-safe
   `{"SOYBEAN-MEAL-48", "FISH-MEAL-65"} <= items_with_positive_margin` SUBSET check, not an exact
   match, so a 3rd item's margin row is harmless) but a completely distinct Supplier
   ("Mekong AgriSource Trading Co. (AI-DEMO-06)") and Item ("CORN-GLUTEN-MEAL-60") nothing else in
   the codebase assumes uniqueness over — this session's own AI-DEMO-02 "Warehouse C
   isolation"/AI-DEMO-05 "PREMIX-BROILER-2PCT-AI5 isolation" lesson applied a third time. 3 real
   Purchase Order -> Purchase Receipt -> Quality Inspection (-> Purchase Invoice, for the first 2)
   chains, spaced ~120/~75/~30 days apart, with a genuinely WORSENING trend on both delivery
   (on-time, then 11 days late, then 14 days late) and quality (Accepted comfortably-in-spec,
   Accepted borderline, then genuinely Rejected via Quality Inspection's own native reading-vs-
   min/max auto-status computation — confirmed by reading
   `erpnext/stock/doctype/quality_inspection/quality_inspection.py`'s `validate()` before relying
   on this, not guessed) — real data a qualification-downgrade recommendation can be honestly
   built on, not a fabricated narrative. The supplier starts `is_critical_supplier=1`,
   `quality_status="Approved"` (an already-qualified critical supplier whose real recent
   performance has since declined — the master plan's own "recommend disqualifying Supplier X due
   to declining QC pass rate" scenario, verbatim).

   `recommend_supplier_qualification_change()`'s "recommend an UPGRADE for a clean-history Pending
   supplier" branch is proven for free using Golden Demo #27's OWN real Cargill Asia Trading data
   — READ ONLY, nothing is ever written to Cargill's Supplier record by this demo (confirmed live:
   Cargill's `quality_status` sits at the Custom Field's own default, "Pending", `is_critical_
   supplier` at its own default, 0/False, with one real on-time Accepted-QC shipment — exactly the
   'clean real history, still Pending' shape the upgrade branch is built for).
"""

import inspect

import frappe
from frappe.utils import add_days, nowdate

from enterprise_core.enterprise_core.ai_drafts import create_ai_draft
from enterprise_core.enterprise_core.ai_procurement_assistant import (
	ANALYTICAL_USE_CASE_TOOL_MAP,
	approve_supplier_status_draft,
	ask_procurement_assistant,
	recommend_supplier_qualification,
	reject_supplier_status_draft,
)
from enterprise_core.enterprise_core.ai_tools import recommend_supplier_qualification_change as _recommend_tool
from enterprise_core.enterprise_core.ingredient_trading_seeds import (
	_USD_PAYABLE_ACCOUNT as _DIT_USD_PAYABLE_ACCOUNT,
	_batch_from_receipt,
	_locale_reading,
	seed_ingredient_trading_master_data,
)

_COMPANY_NAME = "Demo Ingredient Trading Co."
_QUARANTINE_WAREHOUSE = "Import Quarantine - DIT"
_SOY_ITEM = "SOYBEAN-MEAL-48"
_SUPPLIER_CARGILL = "Cargill Asia Trading Pte Ltd"
_SUPPLIER_NUTRECO = "Nutreco South America S.A."

_SQ_CARGILL_MARKER = "AI6-SQ-CARGILL-SOY-01"
_SQ_NUTRECO_MARKER = "AI6-SQ-NUTRECO-SOY-01"

_SUPPLIER_GROUP_AI6 = "AI-DEMO-06 Test Suppliers"
_SUPPLIER_AI6 = "Mekong AgriSource Trading Co. (AI-DEMO-06)"
_ITEM_AI6 = "CORN-GLUTEN-MEAL-60"
_QC_SPEC_AI6 = "Crude Protein % (Corn Gluten Meal)"
_PAYMENT_TERMS_AI6 = "Net 30 (AI-DEMO-06 Procurement Demo)"

_REVIEWER = "procurement.officer@pharmacountry.vn"


# ---------------------------------------------------------------------------
# AI Tool registry additions (5 tools, appended to AI-DEMO-01/02/03/05's registry)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"extract_supplier_quotation",
		"Extract Supplier Quotation",
		"Simulated extraction from an already-structured Supplier Quotation record (no live document/OCR parsing in this platform).",
		"enterprise_core.enterprise_core.ai_tools.extract_supplier_quotation",
		"Supplier Quotation",
	),
	(
		"normalize_supplier_quotations",
		"Normalize Supplier Quotation Terms",
		"Normalizes 2+ Supplier Quotations onto a common comparable basis (base-currency price via each quotation's own conversion_rate, incoterm, lead_time_days, min_order_qty).",
		"enterprise_core.enterprise_core.ai_tools.normalize_supplier_quotations",
		"Supplier Quotation",
	),
	(
		"compare_supplier_quotations",
		"Compare Supplier Quotations",
		"Real, structured side-by-side comparison over normalized quotation data, states which supplier wins on each real dimension.",
		"enterprise_core.enterprise_core.ai_tools.compare_supplier_quotations",
		"Supplier Quotation",
	),
	(
		"summarize_supplier_history",
		"Summarize Supplier Price/Delivery/Payment/Quality History",
		"Real aggregation over a supplier's actual Purchase Order/Purchase Receipt/Purchase Invoice/Quality Inspection history.",
		"enterprise_core.enterprise_core.ai_tools.summarize_supplier_history",
		"Purchase Order",
	),
	(
		"recommend_supplier_qualification_change",
		"Recommend Supplier Qualification Change",
		"Read-only recommendation (never a write) for a Supplier.quality_status change, from real history facts plus stated thresholds. AI does not itself approve suppliers.",
		"enterprise_core.enterprise_core.ai_tools.recommend_supplier_qualification_change",
		"Supplier",
	),
]


def _ensure_ai_tools():
	created = []
	for tool_code, label, description, path, permission_doctype in _AI_TOOLS:
		if frappe.db.exists("AI Tool", tool_code):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Tool",
				"tool_code": tool_code,
				"label": label,
				"description": description,
				"python_function_path": path,
				"required_permission_doctype": permission_doctype,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append(tool_code)
	return created


def _ensure_prompt_templates_and_actions():
	created = []
	if not frappe.db.exists("Prompt Template", {"template_code": "procurement_assistant_synthesis", "version": 1}):
		frappe.get_doc(
			{
				"doctype": "Prompt Template",
				"template_code": "procurement_assistant_synthesis",
				"version": 1,
				"system_instruction": (
					"You are a Procurement Assistant answering one of 4 approved analytical questions "
					"(extract a supplier quotation, normalize quotation terms, compare quotations, summarize a "
					"supplier's price/delivery/payment/quality history). You are given REAL, tool-sourced "
					"structured procurement data as context — never invent facts, never fetch additional data "
					"yourself, never run or suggest SQL. Produce a concise interpretation grounded ONLY in the "
					"provided data. You never decide or authorize anything about a supplier's qualification "
					"status — that is a separate, human-approved decision this assistant never makes on its own."
				),
				"input_schema": frappe.as_json({"use_case": "string", "source_reference": "string", "<tool_code>": "object (tool-specific structured data)"}),
				"output_schema": frappe.as_json({"interpretation": "string"}),
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append("procurement_assistant_synthesis Prompt Template")
	if not frappe.db.exists("AI Action", "procurement_assistant_synthesis"):
		frappe.get_doc(
			{
				"doctype": "AI Action",
				"action_code": "procurement_assistant_synthesis",
				"description": "AI-DEMO-06 Procurement Assistant — synthesizes an interpretation over real procurement tool output for one of 4 approved analytical questions. Read-only: never drafts, never mints or authorizes any record.",
				"required_capabilities": "reasoning",
				"preferred_provider": "anthropic",
				"fallback_policy": "Next Eligible Model",
				"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "procurement_assistant_synthesis", "version": 1}, "name"),
				"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS[:4]),
				"human_review_required": 0,
				"max_cost_usd": 0.05,
				"retention_policy": "Store Full",
			}
		).insert(ignore_permissions=True)
		created.append("procurement_assistant_synthesis AI Action")

	if not frappe.db.exists("Prompt Template", {"template_code": "procurement_supplier_qualification_synthesis", "version": 1}):
		frappe.get_doc(
			{
				"doctype": "Prompt Template",
				"template_code": "procurement_supplier_qualification_synthesis",
				"version": 1,
				"system_instruction": (
					"You are a Procurement Assistant producing a SUPPLIER QUALIFICATION RECOMMENDATION. You are "
					"given REAL, tool-sourced structured supplier history and threshold facts as context — never "
					"invent facts. Your output is ALWAYS a recommendation/draft for a qualified human procurement "
					"reviewer — it is NEVER final, NEVER auto-applied, and you must never claim the supplier's "
					"status has already changed. AI không tự approve supplier — you may recommend either an "
					"upgrade or a downgrade, but applying it is always a separate, explicit human decision."
				),
				"input_schema": frappe.as_json({"use_case": "string", "source_reference": "string (Supplier)", "recommend_supplier_qualification_change": "object"}),
				"output_schema": frappe.as_json({"draft": "string — a recommendation requiring human approval, never auto-final"}),
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append("procurement_supplier_qualification_synthesis Prompt Template")
	if not frappe.db.exists("AI Action", "procurement_supplier_qualification_synthesis"):
		frappe.get_doc(
			{
				"doctype": "AI Action",
				"action_code": "procurement_supplier_qualification_synthesis",
				"description": "AI-DEMO-06 Procurement Assistant — supplier qualification recommendation. Always requires human approval; AI never applies the Supplier.quality_status change itself (master plan: 'AI không tự approve supplier').",
				"required_capabilities": "reasoning",
				"preferred_provider": "anthropic",
				"fallback_policy": "Next Eligible Model",
				"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "procurement_supplier_qualification_synthesis", "version": 1}, "name"),
				"allowed_tools": "recommend_supplier_qualification_change",
				"human_review_required": 1,
				"max_cost_usd": 0.05,
				"retention_policy": "Store Full",
			}
		).insert(ignore_permissions=True)
		created.append("procurement_supplier_qualification_synthesis AI Action")
	return created


# ---------------------------------------------------------------------------
# Part 1 — 2 real Supplier Quotations on SOYBEAN-MEAL-48 (extract/normalize/compare fixtures)
# ---------------------------------------------------------------------------

def _ensure_supplier_quotation(marker, supplier, currency, conversion_rate, incoterm, valid_till_days, terms_text, item_code, qty, rate, lead_time_days):
	existing = frappe.db.exists("Supplier Quotation", {"title": marker})
	if existing:
		return existing, False
	sq = frappe.get_doc(
		{
			"doctype": "Supplier Quotation",
			"supplier": supplier,
			"company": _COMPANY_NAME,
			"title": marker,
			"currency": currency,
			"conversion_rate": conversion_rate,
			"incoterm": incoterm,
			"valid_till": add_days(nowdate(), valid_till_days),
			"terms": terms_text,
			"items": [{"item_code": item_code, "qty": qty, "rate": rate, "warehouse": _QUARANTINE_WAREHOUSE, "lead_time_days": lead_time_days}],
		}
	)
	sq.insert(ignore_permissions=True)
	sq.submit()
	return sq.name, True


def seed_ai_procurement_quotations():
	"""2 real Supplier Quotations for SOYBEAN-MEAL-48 — Cargill (faster lead time, higher
	per-kg price, safer advance+30-days payment terms) vs Nutreco (cheaper per-kg price even after
	FX conversion, slower 35-day lead time, Letter-of-Credit-at-sight terms) — a genuine,
	non-contrived trade-off for `compare_supplier_quotations()` to resolve."""
	if not frappe.db.exists("Item", _SOY_ITEM):
		return "seed_ai_procurement_quotations: SKIPPED — Golden Demo #27 (Ingredient Trading) master data not found, run its own seed chain first."

	cargill_name, cargill_created = _ensure_supplier_quotation(
		_SQ_CARGILL_MARKER,
		_SUPPLIER_CARGILL,
		"USD",
		24700,
		"CIF",
		30,
		"Payment terms: 30% advance T/T on order confirmation, 70% balance within 30 days after Bill of Lading date. Quality per standard soybean meal 48% protein spec.",
		_SOY_ITEM,
		50000,
		0.43,
		21,
	)
	nutreco_name, nutreco_created = _ensure_supplier_quotation(
		_SQ_NUTRECO_MARKER,
		_SUPPLIER_NUTRECO,
		"USD",
		24850,
		"FOB",
		45,
		"Payment terms: 100% via irrevocable Letter of Credit at sight against shipping documents.",
		_SOY_ITEM,
		50000,
		0.415,
		35,
	)
	return (
		f"seed_ai_procurement_quotations: Cargill Supplier Quotation {'created' if cargill_created else 'already existed'} ({cargill_name}). "
		f"Nutreco Supplier Quotation {'created' if nutreco_created else 'already existed'} ({nutreco_name})."
	)


# ---------------------------------------------------------------------------
# Part 2 — isolated Supplier/Item + declining 3-shipment history (qualification-recommendation fixture)
# ---------------------------------------------------------------------------

def _ensure_supplier_group_ai6():
	if not frappe.db.exists("Supplier Group", _SUPPLIER_GROUP_AI6):
		frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": _SUPPLIER_GROUP_AI6, "parent_supplier_group": "All Supplier Groups", "is_group": 0}).insert(ignore_permissions=True)


def _ensure_supplier_ai6():
	existing = frappe.db.exists("Supplier", {"supplier_name": _SUPPLIER_AI6})
	if existing:
		return existing, False
	_ensure_supplier_group_ai6()
	sup = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": _SUPPLIER_AI6,
			"supplier_group": _SUPPLIER_GROUP_AI6,
			"supplier_type": "Company",
			"country": "Myanmar",
			"default_currency": "USD",
			"is_critical_supplier": 1,
			"quality_status": "Approved",
			"accounts": [{"company": _COMPANY_NAME, "account": _DIT_USD_PAYABLE_ACCOUNT}],
		}
	)
	sup.insert(ignore_permissions=True)
	return sup.name, True


def _ensure_item_ai6():
	if frappe.db.exists("Item", _ITEM_AI6):
		return False
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": _ITEM_AI6,
			"item_name": "Corn Gluten Meal 60% Protein (Feed Grade, Imported) — AI-DEMO-06",
			"item_group": "Raw Material",
			"stock_uom": "Kg",
			"is_stock_item": 1,
			"has_batch_no": 1,
			"create_new_batch": 1,
			"batch_number_series": f"{_ITEM_AI6}-.####",
			"inspection_required_before_purchase": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_payment_terms_template():
	if frappe.db.exists("Payment Terms Template", _PAYMENT_TERMS_AI6):
		return _PAYMENT_TERMS_AI6
	frappe.get_doc(
		{
			"doctype": "Payment Terms Template",
			"template_name": _PAYMENT_TERMS_AI6,
			"terms": [{"invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date", "credit_days": 30}],
		}
	).insert(ignore_permissions=True)
	return _PAYMENT_TERMS_AI6


def _ensure_po_ai6(marker, transaction_date, schedule_date, qty, rate, conversion_rate, payment_terms_template):
	existing = frappe.db.exists("Purchase Order", {"title": marker})
	if existing:
		return existing, False
	supplier = frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_AI6}, "name")
	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"supplier": supplier,
			"company": _COMPANY_NAME,
			"currency": "USD",
			"conversion_rate": conversion_rate,
			"title": marker,
			"transaction_date": transaction_date,
			"schedule_date": schedule_date,
			"payment_terms_template": payment_terms_template,
			"items": [{"item_code": _ITEM_AI6, "qty": qty, "rate": rate, "warehouse": _QUARANTINE_WAREHOUSE, "schedule_date": schedule_date}],
		}
	)
	po.insert(ignore_permissions=True)
	po.submit()
	return po.name, True


def _ensure_receipt_ai6(po_name, posting_date, received_qty):
	existing = frappe.db.get_value("Purchase Receipt Item", {"purchase_order": po_name, "item_code": _ITEM_AI6}, "parent")
	if existing and frappe.db.get_value("Purchase Receipt", existing, "docstatus") == 1:
		return existing, False
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	pr = make_purchase_receipt(po_name)
	# Real ERPNext gotcha found live: assigning `posting_date` alone silently gets reset back to
	# today at insert/submit unless `set_posting_time=1` is ALSO set (confirmed by reading the
	# actual behavior on a live throwaway doc before relying on this, not guessed) — the same
	# "backdated transaction" lever a real user would flip via the "Edit Posting Date/Time"
	# checkbox in the UI.
	pr.posting_date = posting_date
	pr.set_posting_time = 1
	for row in pr.items:
		if row.item_code == _ITEM_AI6:
			row.received_qty = received_qty
			row.qty = received_qty
			row.use_serial_batch_fields = 1
	pr.insert(ignore_permissions=True)
	pr.submit()
	return pr.name, True


def _ensure_qi_parameter_ai6():
	if frappe.db.exists("Quality Inspection Parameter", _QC_SPEC_AI6):
		return False
	frappe.get_doc({"doctype": "Quality Inspection Parameter", "parameter": _QC_SPEC_AI6, "description": "Crude protein content, % by weight (corn gluten meal feed-grade spec)."}).insert(ignore_permissions=True)
	return True


def _ensure_quality_inspection_ai6(pr_name, batch_no, reading):
	existing = frappe.db.get_value("Quality Inspection", {"reference_name": pr_name, "item_code": _ITEM_AI6, "batch_no": batch_no}, "name")
	if existing:
		return existing, False, frappe.db.get_value("Quality Inspection", existing, "status")
	_ensure_qi_parameter_ai6()
	qi = frappe.get_doc(
		{
			"doctype": "Quality Inspection",
			"inspection_type": "Incoming",
			"reference_type": "Purchase Receipt",
			"reference_name": pr_name,
			"item_code": _ITEM_AI6,
			"batch_no": batch_no,
			"sample_size": 5,
			"company": _COMPANY_NAME,
			"inspected_by": frappe.session.user,
			# min/max spec (58-65% crude protein) — status is auto-computed by native
			# Quality Inspection.validate() from whether the reading falls in range (confirmed by
			# reading erpnext/stock/doctype/quality_inspection/quality_inspection.py before relying
			# on this, not guessed), never set manually here.
			"readings": [{"specification": _QC_SPEC_AI6, "numeric": 1, "min_value": 58, "max_value": 65, "reading_1": _locale_reading(reading)}],
		}
	)
	qi.insert(ignore_permissions=True)
	qi.submit()
	return qi.name, True, qi.status


def _ensure_purchase_invoice_ai6(pr_name, posting_date):
	existing = frappe.db.get_value("Purchase Invoice Item", {"purchase_receipt": pr_name}, "parent")
	if existing and frappe.db.get_value("Purchase Invoice", existing, "docstatus") == 1:
		return existing, False
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	pi = make_purchase_invoice(pr_name)
	pi.posting_date = posting_date
	pi.set_posting_time = 1  # same real gotcha as _ensure_receipt_ai6() above
	pi.insert(ignore_permissions=True)
	pi.submit()
	return pi.name, True


# (marker, order_days_ago, schedule_lead_days, actual_delay_days, qty, received_qty, rate_usd,
#  conversion_rate, qc_reading, invoice) — a genuinely WORSENING trend across all 3 shipments.
_SHIPMENTS = [
	("AI6-PO-CGM-01", 120, 14, 0, 10000, 10000, 0.38, 24500, 61.0, True),  # on-time; comfortably in-spec
	("AI6-PO-CGM-02", 75, 14, 11, 10000, 9800, 0.385, 24800, 58.5, True),  # 11 days late; borderline in-spec
	("AI6-PO-CGM-03", 30, 14, 14, 10000, 9500, 0.39, 25000, 55.0, False),  # 14 days late; genuinely Rejected (below 58% min) — deliberately NOT invoiced
]


def seed_ai_procurement_supplier_history():
	"""The isolated Supplier + Item + 3-shipment declining history — the real data
	`recommend_supplier_qualification_change()`'s downgrade branch is honestly built on. See
	module docstring for the full isolation rationale."""
	if not frappe.db.exists("Account", _DIT_USD_PAYABLE_ACCOUNT):
		return "seed_ai_procurement_supplier_history: SKIPPED — Golden Demo #27 (Ingredient Trading)'s USD payable account not found, run its own seed chain first."

	supplier_name, supplier_created = _ensure_supplier_ai6()
	item_created = _ensure_item_ai6()
	payment_terms = _ensure_payment_terms_template()

	shipments_created = []
	qc_results = []
	for marker, order_days_ago, lead_days, delay_days, qty, received_qty, rate, conv_rate, reading, invoice in _SHIPMENTS:
		transaction_date = add_days(nowdate(), -order_days_ago)
		schedule_date = add_days(transaction_date, lead_days)
		posting_date = add_days(schedule_date, delay_days)

		po_name, po_created = _ensure_po_ai6(marker, transaction_date, schedule_date, qty, rate, conv_rate, payment_terms)
		pr_name, pr_created = _ensure_receipt_ai6(po_name, posting_date, received_qty)
		batch_no = _batch_from_receipt(pr_name, _ITEM_AI6)
		qi_name, qi_created, qi_status = _ensure_quality_inspection_ai6(pr_name, batch_no, reading)
		qc_results.append(f"{marker}:{qi_status}")

		pi_name = None
		if invoice:
			pi_name, _ = _ensure_purchase_invoice_ai6(pr_name, posting_date)

		if po_created or pr_created or qi_created:
			shipments_created.append(f"{marker}:{po_name}/{pr_name}/{qi_name}" + (f"/{pi_name}" if pi_name else " (not invoiced)"))

	return (
		f"seed_ai_procurement_supplier_history: Supplier {'created' if supplier_created else 'already existed'} ({supplier_name}, critical, Approved). "
		f"Item {'created' if item_created else 'already existed'} ({_ITEM_AI6}). "
		f"Shipments: {shipments_created or 'none (already existed)'}. QC results: {qc_results}."
	)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_procurement_assistant():
	"""Phase 6A / AI-DEMO-06 — registers the 5 new AI Tools, the 2 Prompt Template/AI Action
	pairs (NO-DRAFT analytical + DRAFT-gated qualification), the 2 Supplier Quotation fixtures,
	and the isolated declining-supplier-history fixture. Idempotent: safe to re-run any number of
	times. Calls `seed_ingredient_trading_master_data()` defensively (safe, no Work-Order-like
	"at most one" ambiguity there) and otherwise self-skips with a clear message if Golden Demo
	#27's own fuller seed chain (import shipment / supplier lot & QC) hasn't run yet."""
	base = seed_ingredient_trading_master_data()
	tools_created = _ensure_ai_tools()
	actions_created = _ensure_prompt_templates_and_actions()
	quotations_result = seed_ai_procurement_quotations()
	history_result = seed_ai_procurement_supplier_history()
	return (
		f"seed_ai_procurement_assistant: base Ingredient Trading master data: '{base}'. "
		f"AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Templates/AI Actions created: {actions_created or 'none (already existed)'}. "
		f"'{quotations_result}' '{history_result}'"
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _test_all_analytical_use_cases_answer():
	"""All 4 analytical use cases run end-to-end with real tool data and NO ai_suggestion/draft
	field (proving the documented NO-DRAFT shape for these 4, mirroring AI-DEMO-05's own proof)."""
	source_ref_by_use_case = {
		"extract_quotation": frappe.db.get_value("Supplier Quotation", {"title": _SQ_CARGILL_MARKER}, "name"),
		"normalize_terms": _SOY_ITEM,
		"compare_quotations": _SOY_ITEM,
		"summarize_supplier_history": frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_AI6}, "name"),
	}
	results = {}
	for use_case, expected_tools in ANALYTICAL_USE_CASE_TOOL_MAP.items():
		source_reference = source_ref_by_use_case[use_case]
		resp = ask_procurement_assistant(use_case, source_reference, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-06 smoke test FAILED for '{use_case}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "data_facts" not in resp or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-06 smoke test FAILED for '{use_case}': data_facts missing tool output.")
		if not resp.get("ai_interpretation"):
			frappe.throw(f"AI-DEMO-06 smoke test FAILED for '{use_case}': no ai_interpretation returned.")
		if "ai_suggestion" in resp:
			frappe.throw(f"AI-DEMO-06 smoke test FAILED for '{use_case}': response unexpectedly contains an ai_suggestion/draft field — these 4 use cases are documented NO-DRAFT.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-06 smoke test FAILED for '{use_case}': no AI Job Log entry written.")
		results[use_case] = resp
	return results


def _test_normalize_and_compare_real_tradeoff(results):
	"""normalize_supplier_quotations()/compare_supplier_quotations() resolve the REAL, genuine
	trade-off this demo's own seed data was built with: Nutreco is cheaper per-kg even after FX
	conversion to base currency, but Cargill has the shorter lead time — checked by DIRECTION
	(which supplier wins each dimension), not brittle hardcoded numbers."""
	norm = results["normalize_terms"]["data_facts"]["normalize_supplier_quotations"]
	if norm["count"] != 2:
		frappe.throw(f"AI-DEMO-06 normalize test FAILED: expected 2 normalized quotation rows for {_SOY_ITEM}, got {norm['count']}.")
	by_supplier = {r["supplier"]: r for r in norm["normalized"]}
	if not ({_SUPPLIER_CARGILL, _SUPPLIER_NUTRECO} <= set(by_supplier)):
		frappe.throw(f"AI-DEMO-06 normalize test FAILED: expected both Cargill and Nutreco quotations, got {sorted(by_supplier)}.")
	if by_supplier[_SUPPLIER_NUTRECO]["normalized_rate_base_currency"] >= by_supplier[_SUPPLIER_CARGILL]["normalized_rate_base_currency"]:
		frappe.throw(f"AI-DEMO-06 normalize test FAILED: expected Nutreco's normalized (base-currency) price to be LOWER than Cargill's. Got: {by_supplier}")

	cmp_facts = results["compare_quotations"]["data_facts"]["compare_supplier_quotations"]
	best = cmp_facts.get("best_by_dimension", {})
	if best.get("lowest_normalized_price", {}).get("supplier") != _SUPPLIER_NUTRECO:
		frappe.throw(f"AI-DEMO-06 compare test FAILED: expected Nutreco to win on lowest_normalized_price. Got: {best.get('lowest_normalized_price')}")
	if best.get("shortest_lead_time", {}).get("supplier") != _SUPPLIER_CARGILL:
		frappe.throw(f"AI-DEMO-06 compare test FAILED: expected Cargill to win on shortest_lead_time. Got: {best.get('shortest_lead_time')}")
	return f"normalize/compare CONFIRMED: Nutreco cheaper ({by_supplier[_SUPPLIER_NUTRECO]['normalized_rate_base_currency']} vs {by_supplier[_SUPPLIER_CARGILL]['normalized_rate_base_currency']} base-currency/kg), Cargill faster ({best['shortest_lead_time']['value']} vs {best['lowest_normalized_price']})."


def _test_supplier_history_real_decline(results):
	"""summarize_supplier_history() reflects the REAL, deliberately-worsening 3-shipment trend for
	the isolated AI-DEMO-06 supplier (1/3 on-time, latest QC Rejected), and — as a real positive
	control, READ-ONLY over Golden Demo #27's own untouched Cargill data — a clean-history supplier
	shows no such decline."""
	facts = results["summarize_supplier_history"]["data_facts"]["summarize_supplier_history"]
	if facts["shipment_count"] != 3:
		frappe.throw(f"AI-DEMO-06 history test FAILED: expected 3 shipments for the isolated supplier, got {facts['shipment_count']}.")
	if facts["quality"]["latest_qc_status"] != "Rejected":
		frappe.throw(f"AI-DEMO-06 history test FAILED: expected latest_qc_status='Rejected', got {facts['quality']['latest_qc_status']!r}.")
	if not (facts["delivery"]["on_time_rate"] is not None and facts["delivery"]["on_time_rate"] < 0.5):
		frappe.throw(f"AI-DEMO-06 history test FAILED: expected on_time_rate < 0.5 (declining delivery), got {facts['delivery']['on_time_rate']}.")
	if _PAYMENT_TERMS_AI6 not in facts["payment_terms_actually_used"]:
		frappe.throw(f"AI-DEMO-06 history test FAILED: expected payment_terms_actually_used to include {_PAYMENT_TERMS_AI6!r}, got {facts['payment_terms_actually_used']}.")

	cargill_history = _recommend_tool_history_for_cargill()
	if cargill_history["quality"]["latest_qc_status"] == "Rejected":
		frappe.throw("AI-DEMO-06 history test FAILED: real positive-control supplier (Cargill) unexpectedly shows a Rejected QC result — seed data assumption invalid.")
	return f"supplier-history CONFIRMED: isolated supplier on_time_rate={facts['delivery']['on_time_rate']}, latest_qc_status=Rejected; Cargill (positive control, untouched real data) shows no rejection."


def _recommend_tool_history_for_cargill():
	from enterprise_core.enterprise_core.ai_tools import summarize_supplier_history

	return summarize_supplier_history(user="Administrator", supplier=_SUPPLIER_CARGILL)["data"]


def _test_recommend_qualification_and_approval():
	"""THE defining acceptance-criteria proof for this demo — 'AI không tự approve supplier':
	  (a) recommend_supplier_qualification() NEVER changes Supplier.quality_status itself, even
	      though it invokes the (mock) AI synthesis step — checked by a live before/after read.
	  (b) the fresh draft correctly recommends a DOWNGRADE ('Disqualified', since the isolated
	      supplier is_critical_supplier=1) grounded in the real declining-history facts.
	  (c) a REAL, distinct human reviewer (procurement.officer) must explicitly approve before
	      Supplier.quality_status changes; approving mints exactly that one real change.
	  (d) rejecting a second recommendation leaves quality_status unchanged.
	  (e) every structural self-approval guard fires: no reviewed_by, a bogus reviewed_by, a raw
	      self-approval save, and re-deciding an already-decided draft.
	  (f) a REAL positive control: Golden Demo #27's own untouched Cargill Asia Trading data
	      recommends an UPGRADE ('Approved') from its real 'Pending' status — proving the tool
	      distinguishes good and bad suppliers, not just flags everything.
	"""
	supplier = frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_AI6}, "name")
	if not supplier:
		frappe.throw("AI-DEMO-06 qualification test setup FAILED: isolated supplier not found — run seed_ai_procurement_supplier_history() first.")

	status_before = frappe.db.get_value("Supplier", supplier, "quality_status")
	resp = recommend_supplier_qualification(supplier, user="Administrator")
	status_immediately_after = frappe.db.get_value("Supplier", supplier, "quality_status")
	if status_immediately_after != status_before:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: recommend_supplier_qualification() itself changed Supplier.quality_status ({status_before!r} -> {status_immediately_after!r}) — the AI must NEVER self-apply a recommendation.")

	suggestion = resp["ai_suggestion"]
	if suggestion.get("suggested_fields", {}).get("recommended_status") != "Disqualified":
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: expected a 'Disqualified' recommendation for the declining critical supplier, got {suggestion.get('suggested_fields')}.")
	if suggestion.get("requires_human_approval") is not True or suggestion.get("approval_status") != "Draft":
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: fresh recommendation must be requires_human_approval=True, approval_status='Draft'. Got: {suggestion}")
	draft_name = suggestion["draft"]
	draft = frappe.get_doc("AI Draft", draft_name)
	if draft.resulting_reference:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: fresh draft {draft_name} already has resulting_reference={draft.resulting_reference!r} — should be empty until approved.")

	# (e1) no reviewed_by
	blocked_no_reviewer = False
	try:
		approve_supplier_status_draft(draft_name, reviewed_by=None)
	except frappe.ValidationError:
		blocked_no_reviewer = True
	if not blocked_no_reviewer:
		frappe.throw("AI-DEMO-06 qualification test FAILED: approve_supplier_status_draft() with reviewed_by=None was not blocked.")

	# (e2) bogus (non-existent) reviewed_by — real Link-field-style integrity, not just a missing check
	blocked_bogus_reviewer = False
	try:
		approve_supplier_status_draft(draft_name, reviewed_by="not.a.real.user@nowhere.fake")
	except frappe.ValidationError:
		blocked_bogus_reviewer = True
	if not blocked_bogus_reviewer:
		frappe.throw("AI-DEMO-06 qualification test FAILED: approve_supplier_status_draft() with a non-existent reviewed_by was not blocked.")
	if frappe.db.get_value("Supplier", supplier, "quality_status") != status_before:
		frappe.throw("AI-DEMO-06 qualification test FAILED: a blocked approval attempt still changed Supplier.quality_status.")

	# (e3) raw self-approval (no reviewed_by) via a direct save on a throwaway draft
	guard_draft = create_ai_draft(
		copilot_code="procurement_assistant", use_case="supplier_qualification_recommendation", source_doctype="Supplier", source_reference=supplier,
		content="[AI-DEMO-06 negative test draft — should never reach Approved without reviewed_by.]",
	)
	guard_draft.status = "Approved"  # deliberately no reviewed_by set
	blocked_self_approval = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked_self_approval = True
	if not blocked_self_approval:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: AI Draft {guard_draft.name} was saved as Approved WITHOUT reviewed_by — self-approval guard did not fire.")

	# (c) real approval, by a real distinct human reviewer.
	if not frappe.db.exists("User", _REVIEWER) or _REVIEWER == "Administrator":
		frappe.throw(f"AI-DEMO-06 qualification test setup FAILED: reviewer {_REVIEWER!r} must be a real, distinct human user.")
	returned_supplier = approve_supplier_status_draft(draft_name, reviewed_by=_REVIEWER, review_notes="Reviewed declining QC/delivery trend — approved disqualification recommendation.")
	if returned_supplier != supplier:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: approve_supplier_status_draft() returned {returned_supplier!r}, expected {supplier!r}.")
	status_after_approval = frappe.db.get_value("Supplier", supplier, "quality_status")
	if status_after_approval != "Disqualified":
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: Supplier.quality_status={status_after_approval!r} after approval, expected 'Disqualified'.")
	draft.reload()
	if draft.status != "Approved" or draft.reviewed_by != _REVIEWER or draft.resulting_doctype != "Supplier" or draft.resulting_reference != supplier:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: draft {draft_name} not correctly finalized. status={draft.status}, reviewed_by={draft.reviewed_by}, resulting_doctype={draft.resulting_doctype}, resulting_reference={draft.resulting_reference}.")
	log = frappe.db.get_value("AI Job Log", draft.generated_by_job_log, ["accepted", "final_record_reference"], as_dict=True)
	if not log or not log.accepted or log.final_record_reference != supplier:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: AI Job Log {draft.generated_by_job_log} not updated with accepted=1/final_record_reference={supplier!r}. Got: {log}")

	# (e4) re-deciding an already-Approved draft is blocked.
	blocked_redecision = False
	try:
		reject_supplier_status_draft(draft_name, reviewed_by=_REVIEWER)
	except frappe.ValidationError:
		blocked_redecision = True
	if not blocked_redecision:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: an already-Approved draft {draft_name} was re-decided — finality guard did not fire.")

	# (d) a SECOND recommendation, rejected -> leaves quality_status unchanged.
	resp2 = recommend_supplier_qualification(supplier, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	reject_supplier_status_draft(draft2_name, reviewed_by=_REVIEWER, review_notes="Already disqualified — no further action needed.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	if draft2.status != "Rejected" or draft2.resulting_reference:
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: rejected draft2 {draft2_name} not correctly finalized. status={draft2.status}, resulting_reference={draft2.resulting_reference}.")
	if frappe.db.get_value("Supplier", supplier, "quality_status") != "Disqualified":
		frappe.throw("AI-DEMO-06 qualification test FAILED: rejecting draft2 changed Supplier.quality_status away from 'Disqualified'.")

	# (f) positive control — real, untouched Cargill data recommends an UPGRADE.
	cargill_status_before = frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status")
	cargill_resp = recommend_supplier_qualification(_SUPPLIER_CARGILL, user="Administrator")
	cargill_status_after = frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status")
	if cargill_status_after != cargill_status_before:
		frappe.throw("AI-DEMO-06 qualification test FAILED: recommend_supplier_qualification() changed Cargill's real quality_status merely by generating a recommendation.")
	cargill_fields = cargill_resp["ai_suggestion"]["suggested_fields"]
	if cargill_fields.get("recommended_status") != "Approved":
		frappe.throw(f"AI-DEMO-06 qualification test FAILED: expected an 'Approved' UPGRADE recommendation for clean-history Cargill (current status {cargill_status_before!r}), got {cargill_fields}.")
	# Deliberately do NOT approve this one — Cargill's real Supplier record must stay untouched by
	# this demo's own validations (isolation discipline: only the AI-DEMO-06-owned supplier's
	# status is ever actually applied here).
	reject_supplier_status_draft(cargill_resp["ai_suggestion"]["draft"], reviewed_by=_REVIEWER, review_notes="AI-DEMO-06 validation: positive-control recommendation only, deliberately not applied to avoid mutating Golden Demo #27's own untouched Supplier data.")
	if frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status") != cargill_status_before:
		frappe.throw("AI-DEMO-06 qualification test FAILED: Cargill's real Supplier.quality_status was mutated by this demo's own validations.")

	return (
		f"qualification-recommendation CONFIRMED: isolated supplier {supplier} recommended 'Disqualified' (real declining history), never self-applied, "
		f"approved by {_REVIEWER} -> real quality_status change; a second draft rejected -> unchanged; every self-approval guard fired; "
		f"real positive control (Cargill, untouched) recommended an 'Approved' UPGRADE from real clean history, left unapplied and unmutated."
	)


def _strip_docstring(source):
	"""Removes a function's own leading triple-quoted docstring before a substring/write-call
	scan — otherwise this very module's own docstrings (which quote `.save()`/`.insert()` etc. IN
	PROSE, describing what must NOT be there) would false-positive the check that's supposed to
	prove they really aren't."""
	first = source.find('"""')
	if first == -1:
		return source
	second = source.find('"""', first + 3)
	if second == -1:
		return source
	return source[:first] + source[second + 3 :]


def _test_structural_no_self_approval_proof():
	"""Static source-level proof, not just behavioral: the ONLY place in this codebase that ever
	writes `Supplier.quality_status`/`is_critical_supplier` as a consequence of an AI
	recommendation is `approve_supplier_status_draft()` — the read-only tool and the orchestration
	entry point contain ZERO such write calls (checked on the CODE only, docstring prose
	stripped — see `_strip_docstring()`)."""
	from enterprise_core.enterprise_core import ai_procurement_assistant

	tool_source = _strip_docstring(inspect.getsource(_recommend_tool))
	if "frappe.db.set_value" in tool_source or ".save(" in tool_source or ".insert(" in tool_source:
		frappe.throw(f"AI-DEMO-06 structural test FAILED: recommend_supplier_qualification_change() (the tool) contains a write call — it must be read-only. Source:\n{tool_source}")

	orchestration_source = _strip_docstring(inspect.getsource(ai_procurement_assistant.recommend_supplier_qualification))
	if "frappe.db.set_value" in orchestration_source or ("Supplier" in orchestration_source and (".save(" in orchestration_source or ".insert(" in orchestration_source)):
		frappe.throw(f"AI-DEMO-06 structural test FAILED: recommend_supplier_qualification() (orchestration) appears to write a record directly — it must only call the read-only tool and create_ai_draft(). Source:\n{orchestration_source}")

	approve_source = _strip_docstring(inspect.getsource(ai_procurement_assistant.approve_supplier_status_draft))
	write_count = approve_source.count('frappe.db.set_value("Supplier"')
	if write_count != 1:
		frappe.throw(f"AI-DEMO-06 structural test FAILED: expected EXACTLY ONE Supplier.quality_status write site inside approve_supplier_status_draft(), found {write_count}. Source:\n{approve_source}")
	if "reviewed_by" not in approve_source:
		frappe.throw("AI-DEMO-06 structural test FAILED: approve_supplier_status_draft() does not reference reviewed_by at all — the single write site must be gated behind an explicit human reviewer.")

	return "structural proof CONFIRMED: zero Supplier-write call sites in the tool or orchestration entry point; exactly one, reviewed_by-gated, write site inside approve_supplier_status_draft()."


def seed_ai_procurement_assistant_validations():
	"""Runs all validations end-to-end: the 4-use-case analytical smoke test, the real normalize/
	compare trade-off proof, the real declining-supplier-history proof (with Cargill as a real,
	untouched positive control), THE mandatory-approval / 'AI không tự approve supplier' proof
	(including every structural guard and a real positive-control upgrade recommendation), and the
	static source-level no-self-approval proof."""
	smoke = _test_all_analytical_use_cases_answer()
	tradeoff = _test_normalize_and_compare_real_tradeoff(smoke)
	history = _test_supplier_history_real_decline(smoke)
	qualification = _test_recommend_qualification_and_approval()
	structural = _test_structural_no_self_approval_proof()
	return f"seed_ai_procurement_assistant_validations: all {len(smoke)} analytical use cases ran end-to-end (NO-DRAFT confirmed). {tradeoff} {history} {qualification} {structural}"
