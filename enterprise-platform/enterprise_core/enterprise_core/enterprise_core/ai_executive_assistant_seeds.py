"""Phase 6A — AI-DEMO-01 (Executive Assistant) + Tool Registry seed data. Registers the 5
approved `AI Tool`s (see `ai_tools.py`), the `ask_enterprise_synthesis` Prompt
Template/AI Action used by every question, synthetic multi-month revenue-history Sales
Invoices (no other golden demo seeds genuinely multi-month-dated Sales Invoices — verified by
reading every seed module before writing this one), and validation functions proving: all 5
example questions answer with real data, the 2-user permission-scoping claim (Golden Demo
#24's 3PL Client A/B portal users), and the data-fact/AI-interpretation structural separation.
"""

import frappe
from frappe.utils import add_days, get_first_day, nowdate

from enterprise_core.enterprise_core.ai_executive_assistant import QUESTION_TOOL_MAP, ask_enterprise
from enterprise_core.enterprise_core.threepl_seeds import seed_3pl_master_data

# Golden Demo #24 (3PL)'s already-seeded, already-permission-scoped portal users — reused
# verbatim per the master plan's own explicit hint that this is "a directly relevant
# precedent". `seed_3pl_master_data()` is idempotent and called defensively below so this
# module never depends on Phase 6's seed order having already run it.
_CLIENT_A_USER = "client.a.3pl@pharmacountry.vn"
_CLIENT_B_USER = "client.b.3pl@pharmacountry.vn"
_CLIENT_A_QUARANTINE_WH = "Client A Quarantine - D3PL"
_CLIENT_B_QUARANTINE_WH = "Client B Quarantine - D3PL"

# ---------------------------------------------------------------------------
# AI Tool registry (5 tools)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"get_overdue_capas",
		"Overdue CAPAs",
		"Real QMS CAPA records past due_date and not Closed/Pending Effectiveness Check (Golden Demo #2 QMS).",
		"enterprise_core.enterprise_core.ai_tools.get_overdue_capas",
		"QMS CAPA",
	),
	(
		"get_batches_on_hold",
		"Batches On Hold",
		"Batches with positive current balance sitting in a Quarantine-named warehouse (Golden Demo #24 3PL / #9 Feed / #26 Premix / #22 Med Device hold pattern).",
		"enterprise_core.enterprise_core.ai_tools.get_batches_on_hold",
		"Stock Ledger Entry",
	),
	(
		"get_near_expiry_inventory",
		"Near-Expiry Inventory",
		"Batches with positive current balance expiring within N days (PD07 near-expiry pattern, Golden Demo #1 Pharma), generalized across warehouses/companies.",
		"enterprise_core.enterprise_core.ai_tools.get_near_expiry_inventory",
		"Stock Ledger Entry",
	),
	(
		"get_worst_fcr_pond",
		"Worst-FCR Pond This Month",
		"Worst (highest) Feed Conversion Ratio pond this month across Fish Harvest (Golden Demo #17) and Shrimp Harvest (Golden Demo #8).",
		"enterprise_core.enterprise_core.ai_tools.get_worst_fcr_pond",
		"Fish Harvest",
	),
	(
		"get_revenue_trend_explanation_data",
		"Revenue Trend Explanation Data",
		"Sales Invoice revenue this month vs prior month, broken down by Territory (Golden Demo #25 Consumer Distribution).",
		"enterprise_core.enterprise_core.ai_tools.get_revenue_trend_explanation_data",
		"Sales Invoice",
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


def _ensure_prompt_template():
	if frappe.db.exists("Prompt Template", {"template_code": "ask_enterprise_synthesis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "ask_enterprise_synthesis",
			"version": 1,
			"system_instruction": (
				"You are an enterprise operations assistant answering one of a FIXED set of approved business "
				"questions (CAPA overdue status, batch hold status, near-expiry inventory, aquaculture FCR, "
				"revenue trend). You are given REAL, tool-sourced structured data as context — never invent "
				"facts, never fetch additional data yourself, never run or suggest SQL. Produce a concise "
				"interpretation grounded ONLY in the provided data. Your output is an interpretation, not a "
				"substitute for the underlying data facts, which are returned and logged separately."
			),
			"input_schema": frappe.as_json({"question_code": "string", "<tool_code>": "object (tool-specific structured data)"}),
			"output_schema": frappe.as_json({"interpretation": "string"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", "ask_enterprise_synthesis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "ask_enterprise_synthesis",
			"description": "AI-DEMO-01 Executive Assistant — synthesizes an interpretation over real tool output for one of 5 approved demo questions.",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "ask_enterprise_synthesis", "version": 1}, "name"),
			"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS),
			"human_review_required": 1,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Synthetic revenue history — Consumer Distribution company (Golden Demo #25), 2 territories,
# 2 months. Guarded by transaction (po_no) EXISTENCE, not balance (this session's own lesson
# that balance-based idempotency guards are fragile).
# ---------------------------------------------------------------------------

_CD_COMPANY = "Demo Consumer Distribution Co."
_DEALER_HANOI = "Golden Health Hanoi Dealer Co."
_DEALER_SAIGON = "Golden Health Saigon Dealer Co."
_TERRITORY_NORTH = "Northern Vietnam Dealer Territory"
_TERRITORY_SOUTH = "Southern Vietnam Dealer Territory"
_VITC_ITEM = "VITC-1000-EFF"
_FACIAL_ITEM = "FACIAL-CLEANSER-150ML"
_VITC_DEALER_RATE = 210000
_FACIAL_STANDARD_RATE = 95000

# (po_no marker, customer, territory, item, qty, rate, month_offset [0=this month, -1=prev])
_REVENUE_INVOICES = [
	("AI-DEMO-01-REV-PREV-NORTH", _DEALER_HANOI, _TERRITORY_NORTH, _VITC_ITEM, 40, _VITC_DEALER_RATE, -1),
	("AI-DEMO-01-REV-PREV-SOUTH", _DEALER_SAIGON, _TERRITORY_SOUTH, _FACIAL_ITEM, 60, _FACIAL_STANDARD_RATE, -1),
	("AI-DEMO-01-REV-THIS-NORTH", _DEALER_HANOI, _TERRITORY_NORTH, _VITC_ITEM, 5, _VITC_DEALER_RATE, 0),
	("AI-DEMO-01-REV-THIS-SOUTH", _DEALER_SAIGON, _TERRITORY_SOUTH, _FACIAL_ITEM, 50, _FACIAL_STANDARD_RATE, 0),
]


def _month_anchor_date(month_offset, day=10):
	"""Returns the `day`-th day of (current month + month_offset). Only 0 (this month) and -1
	(prior month) are used by `_REVENUE_INVOICES` above."""
	if month_offset not in (0, -1):
		raise ValueError("_month_anchor_date only supports month_offset 0 or -1")
	first_of_this_month = get_first_day(nowdate())
	anchor = first_of_this_month if month_offset == 0 else get_first_day(add_days(first_of_this_month, -1))
	return add_days(anchor, day - 1)


def _ensure_credit_headroom(customer, company, min_limit):
	"""Golden Demo #25 (Consumer Distribution) enforces a real ERPNext customer credit limit
	(CD04) — a site that already has other invoices against this dealer (e.g. a longer-running
	production site) can be close enough to that limit that this seed's own synthetic
	invoices would legitimately trip `check_credit_limit()` on submit. Raises (never lowers)
	the company-scoped `Customer Credit Limit` row so this demo's OWN data never depends on
	how much unrelated invoice history happens to already exist. Idempotent: only writes when
	the current limit is below `min_limit`."""
	doc = frappe.get_doc("Customer", customer)
	row = next((r for r in doc.credit_limits if r.company == company), None)
	if row and (row.credit_limit or 0) >= min_limit:
		return False
	if row:
		row.credit_limit = min_limit
	else:
		doc.append("credit_limits", {"company": company, "credit_limit": min_limit})
	doc.save(ignore_permissions=True)
	return True


def seed_ai_demo_revenue_history():
	"""Creates 4 submitted Sales Invoices (2 territories x 2 months) against the real Golden
	Demo #25 (Consumer Distribution) company/customers/items so
	`get_revenue_trend_explanation_data()` has genuine, non-degenerate month-over-month data —
	no existing golden demo seeds multi-month-dated Sales Invoices (confirmed by reading every
	seed module: every seeded Sales Invoice/Order lands on `nowdate()`, the day the seed script
	happened to run). North territory (Hanoi dealer) is deliberately the larger driver of the
	simulated decline so `get_revenue_trend_explanation_data()`'s by-territory breakdown tells
	a real, checkable story, not just a single aggregate number."""
	if not frappe.db.exists("Company", _CD_COMPANY):
		return "seed_ai_demo_revenue_history: SKIPPED — Consumer Distribution company not found. Run Golden Demo #25's seeds first."

	_ensure_credit_headroom(_DEALER_HANOI, _CD_COMPANY, 100_000_000)
	_ensure_credit_headroom(_DEALER_SAIGON, _CD_COMPANY, 100_000_000)

	created = []
	for po_no, customer, territory, item_code, qty, rate, month_offset in _REVENUE_INVOICES:
		if frappe.db.exists("Sales Invoice", {"po_no": po_no}):
			continue
		posting_date = _month_anchor_date(month_offset)
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": _CD_COMPANY,
				"customer": customer,
				"territory": territory,
				"po_no": po_no,
				"posting_date": posting_date,
				"set_posting_time": 1,
				"update_stock": 0,
				"items": [{"item_code": item_code, "qty": qty, "rate": rate}],
			}
		)
		si.insert(ignore_permissions=True)
		si.submit()
		created.append(si.name)
	return f"seed_ai_demo_revenue_history: created {created or 'none (already existed)'}."


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_executive_assistant():
	"""Phase 6A / AI-DEMO-01 — registers the 5 AI Tools, the ask_enterprise_synthesis Prompt
	Template + AI Action (reusing the existing, unmodified CE-13 AI foundation
	router/policy/logging — see ai_core.run_ai_action()), and the synthetic revenue-history
	demo data. Idempotent: safe to re-run any number of times."""
	client_users_ready = seed_3pl_master_data()
	tools_created = _ensure_ai_tools()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	revenue_result = seed_ai_demo_revenue_history()
	return (
		f"seed_ai_executive_assistant: 3PL master data step: '{client_users_ready}'. "
		f"AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"{revenue_result}"
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _test_all_questions_answer():
	"""Every one of the 5 example questions from the master plan answers with the
	data_facts/ai_interpretation/sources/tools_called shape populated, as Administrator."""
	results = {}
	for question_code, expected_tools in QUESTION_TOOL_MAP.items():
		resp = ask_enterprise(question_code, user="Administrator")
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "data_facts" not in resp or expected_tools[0] not in resp["data_facts"]:
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': data_facts missing tool output.")
		if not resp.get("ai_interpretation"):
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': no ai_interpretation returned.")
		if not resp.get("provider") or not resp.get("model"):
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': provider/model not logged in response.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': no AI Job Log entry written.")
		logged_tools = frappe.db.get_value("AI Job Log", resp["job_log"], "tool_calls")
		if not logged_tools or frappe.parse_json(logged_tools) != expected_tools:
			frappe.throw(f"AI-DEMO-01 smoke test FAILED for '{question_code}': AI Job Log.tool_calls={logged_tools!r}, expected {expected_tools}.")
		results[question_code] = resp
	return results


def _test_permission_scoping():
	"""THE concrete 2-user permission-scoping proof (master plan acceptance criteria:
	permission-aware + "không trả dữ liệu ngoài quyền"). Asks the SAME question
	('batches_on_hold') as Client A's and Client B's 3PL portal users (Golden Demo #24, each
	restricted via a Warehouse User Permission with apply_to_all_doctypes=1) and asserts:
	(1) the two answers are genuinely different, (2) Client A's answer contains ONLY Client
	A's warehouse data and NEVER Client B's (and vice versa) — checked by directly inspecting
	the returned data_facts, not by trusting a status flag."""
	resp_a = ask_enterprise("batches_on_hold", user=_CLIENT_A_USER)
	resp_b = ask_enterprise("batches_on_hold", user=_CLIENT_B_USER)

	batches_a = resp_a["data_facts"]["get_batches_on_hold"]["batches"]
	batches_b = resp_b["data_facts"]["get_batches_on_hold"]["batches"]

	warehouses_a = {b["warehouse"] for b in batches_a}
	warehouses_b = {b["warehouse"] for b in batches_b}

	if not warehouses_a:
		frappe.throw("AI-DEMO-01 permission test FAILED: Client A saw ZERO batches on hold — setup problem (expected to see its own Quarantine warehouse).")
	if not warehouses_b:
		frappe.throw("AI-DEMO-01 permission test FAILED: Client B saw ZERO batches on hold — setup problem (expected to see its own Quarantine warehouse).")
	if warehouses_a == warehouses_b:
		frappe.throw(f"AI-DEMO-01 permission test FAILED: Client A and Client B got IDENTICAL warehouse sets ({warehouses_a}) — no real scoping happened.")
	if any("Client B" in w for w in warehouses_a):
		frappe.throw(f"AI-DEMO-01 permission LEAK: Client A's Ask Enterprise answer contained Client B's warehouse data: {warehouses_a}")
	if any("Client A" in w for w in warehouses_b):
		frappe.throw(f"AI-DEMO-01 permission LEAK: Client B's Ask Enterprise answer contained Client A's warehouse data: {warehouses_b}")
	if _CLIENT_A_QUARANTINE_WH not in warehouses_a:
		frappe.throw(f"AI-DEMO-01 permission test FAILED: Client A's answer didn't include its own quarantine warehouse. Got: {warehouses_a}")
	if _CLIENT_B_QUARANTINE_WH not in warehouses_b:
		frappe.throw(f"AI-DEMO-01 permission test FAILED: Client B's answer didn't include its own quarantine warehouse. Got: {warehouses_b}")

	# Sources (citations) must also be scoped — not just the summarized data.
	if any("Client B" in s for s in resp_a["sources"]) or any("Client A" in s for s in resp_b["sources"]):
		frappe.throw("AI-DEMO-01 permission LEAK: cross-client warehouse name found inside a 'sources' citation list.")

	return f"seed_ai_executive_assistant permission proof: Client A -> {sorted(warehouses_a)}, Client B -> {sorted(warehouses_b)} (disjoint, correctly scoped)."


def _test_fact_interpretation_separation():
	"""The response must structurally separate the real data fact from the AI's own
	interpretation — never blended into one opaque string."""
	resp = ask_enterprise("overdue_capas", user="Administrator")
	if "data_facts" not in resp or "ai_interpretation" not in resp:
		frappe.throw("AI-DEMO-01 fact/interpretation test FAILED: response missing one of data_facts/ai_interpretation top-level keys.")
	if not isinstance(resp["data_facts"], dict):
		frappe.throw("AI-DEMO-01 fact/interpretation test FAILED: data_facts is not a structured dict.")
	if not isinstance(resp["ai_interpretation"], str):
		frappe.throw("AI-DEMO-01 fact/interpretation test FAILED: ai_interpretation is not a plain string field.")
	facts = resp["data_facts"]["get_overdue_capas"]
	if "count" not in facts or "capas" not in facts:
		frappe.throw(f"AI-DEMO-01 fact/interpretation test FAILED: get_overdue_capas data_facts missing expected keys. Got: {facts}")
	return True


def seed_ai_executive_assistant_validations():
	"""Runs all 3 validations end-to-end: 5-question smoke test, the 2-user permission proof,
	and the fact/interpretation structural-separation check."""
	smoke = _test_all_questions_answer()
	permission_proof = _test_permission_scoping()
	separation = _test_fact_interpretation_separation()
	return (
		f"seed_ai_executive_assistant_validations: all {len(smoke)} example questions answered. "
		f"{permission_proof} Fact/interpretation separation CONFIRMED ({separation})."
	)
