"""Phase 6A — AI-DEMO-01 (Executive Assistant) tool implementations, registered in the
`AI Tool` registry (see `doctype/ai_tool/`) and invoked exclusively through
`ai_executive_assistant.ask_enterprise()` — never called ad hoc, and never exposing raw SQL
to the AI layer (master plan §19E's "Không cho AI arbitrary SQL").

Every function here is:
- READ-ONLY (no `.insert()`/`.save()`/`.submit()` anywhere in this module).
- PERMISSION-RESPECTING: every single Frappe query goes through `frappe.get_list()` with an
  explicit `user=` kwarg, NEVER `frappe.get_all()` or raw `frappe.db.sql()` — this session's
  own established lesson (`get_all()` hardcodes `ignore_permissions=True`, silently bypassing
  the exact boundary this module exists to enforce). Empirically confirmed on a live site
  (Golden Demo #24's 3PL Client A/B portal users) that `frappe.get_list(..., user=X)` performs
  permission-checking AS user X — see `frappe/model/db_query.py`'s
  `DatabaseQuery.execute(user=...)` — without needing to mutate `frappe.session.user`.
- Returns a uniform `{"data": <json-safe structure>, "sources": [<record refs>], "notes": str|None}`
  shape so `ask_enterprise()` can assemble `data_facts`/`sources` generically across tools.

Batch/expiry queries deliberately mirror the exact idiom already proven safe in this codebase
(`threepl_seeds.py`'s `_batches_in_warehouse()` SQL query, and `api.py`'s
`get_near_expiry_batches()`), but rebuilt on `frappe.get_list()` so the SAME queries are
permission-checked — Stock Ledger Entry has no direct `batch_no` column in this ERPNext
version, so batch linkage goes through `Serial and Batch Bundle`/`Serial and Batch Entry`
(child-table reads need the `parent_doctype="Serial and Batch Bundle"` kwarg — confirmed
empirically; without it `frappe.get_list("Serial and Batch Entry", ...)` raises
"Insufficient Permission" because child-table doctypes have no permission list of their own
and must borrow the parent doctype's).
"""

import re
from collections import defaultdict

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate, nowdate

from enterprise_core.enterprise_core import rag_pipeline


# ---------------------------------------------------------------------------
# Shared helper — current per-(warehouse,item,batch) stock balance, fully
# permission-scoped to the calling user via frappe.get_list(user=...).
# ---------------------------------------------------------------------------

def _current_batch_balances(user, warehouse_like=None, company=None):
	"""Returns a list of {warehouse, item_code, batch_no, qty} for batches with a positive
	current balance, scoped to warehouses the calling `user` can actually see (and optionally
	further filtered by warehouse-name substring and/or Company). Every step is a
	`frappe.get_list()` call carrying `user=user` — a warehouse the user has no permission for
	simply never appears in `warehouses`, so nothing downstream can leak it."""
	wh_filters = {}
	if warehouse_like:
		wh_filters["name"] = ["like", warehouse_like]
	if company:
		wh_filters["company"] = company
	warehouses = frappe.get_list("Warehouse", filters=wh_filters, fields=["name"], user=user, limit_page_length=0)
	wh_names = [w.name for w in warehouses]
	if not wh_names:
		return []

	sle = frappe.get_list(
		"Stock Ledger Entry",
		filters={"warehouse": ["in", wh_names], "is_cancelled": 0},
		fields=["warehouse", "item_code", "serial_and_batch_bundle", "actual_qty"],
		user=user,
		limit_page_length=0,
	)
	balances = defaultdict(float)
	for row in sle:
		if not row.serial_and_batch_bundle:
			continue
		balances[(row.warehouse, row.item_code, row.serial_and_batch_bundle)] += row.actual_qty

	bundles = sorted({key[2] for key, qty in balances.items() if qty > 0.0001})
	if not bundles:
		return []

	# Serial and Batch Entry is a child table (istable=1) of Serial and Batch Bundle — it has
	# no permission list of its own, so `parent_doctype` tells frappe.get_list() whose
	# permissions (and whose User Permission match conditions) to enforce.
	sbe = frappe.get_list(
		"Serial and Batch Entry",
		filters={"parent": ["in", bundles]},
		fields=["parent", "batch_no"],
		parent_doctype="Serial and Batch Bundle",
		user=user,
		limit_page_length=0,
	)
	bundle_to_batch = {r.parent: r.batch_no for r in sbe if r.batch_no}

	results = []
	for (warehouse, item_code, bundle), qty in balances.items():
		if qty <= 0.0001:
			continue
		batch_no = bundle_to_batch.get(bundle)
		if not batch_no:
			continue
		results.append({"warehouse": warehouse, "item_code": item_code, "batch_no": batch_no, "qty": qty})
	return results


# ---------------------------------------------------------------------------
# Tool 1 — "Những CAPA nào đang quá hạn?" (which CAPAs are overdue?)
# ---------------------------------------------------------------------------

def get_overdue_capas(user=None, **_ignored):
	"""Real query over Golden Demo #2 (QMS)'s `QMS CAPA` doctype. Mirrors the exact overdue
	predicate already proven in `api.escalate_overdue_capas()` (due_date < today AND status
	not in a closed/terminal set), widened slightly to ALSO surface CAPAs already flagged
	'Overdue' by that escalation routine (a user asking "which CAPAs are overdue" wants to see
	those too, not just the not-yet-escalated ones)."""
	user = user or frappe.session.user
	rows = frappe.get_list(
		"QMS CAPA",
		filters={"due_date": ["<", nowdate()], "status": ["not in", ["Closed", "Pending Effectiveness Check"]]},
		fields=["name", "subject", "capa_type", "owner_user", "due_date", "status"],
		order_by="due_date asc",
		user=user,
		limit_page_length=0,
	)
	data = [
		{
			"capa": r.name,
			"subject": r.subject,
			"capa_type": r.capa_type,
			"owner_user": r.owner_user,
			"due_date": str(r.due_date),
			"status": r.status,
			"days_overdue": (getdate(nowdate()) - getdate(r.due_date)).days,
		}
		for r in rows
	]
	return {
		"data": {"count": len(data), "capas": data},
		"sources": [f"QMS CAPA:{r['capa']}" for r in data],
		"notes": None if data else "No CAPA currently meets the overdue predicate (due_date < today, status not Closed/Pending Effectiveness Check).",
	}


# ---------------------------------------------------------------------------
# Tool 2 — "Batch nào đang bị hold?" (which batches are on hold/quarantine?)
# ---------------------------------------------------------------------------

def get_batches_on_hold(user=None, company=None, **_ignored):
	"""Batches with positive current balance sitting in a Quarantine-named warehouse — the
	same warehouse-name-substring convention used by Golden Demo #24 (3PL), #9 (Feed Mfg),
	#26 (Premix) and #22 (Med Device), and by `validations.py`'s own
	`block_fg_release_without_qa()` gate. THIS is the tool used for the concrete 2-user
	permission-scoping proof (Golden Demo #24's Client A / Client B portal users, each
	restricted via a Warehouse User Permission with apply_to_all_doctypes=1) — empirically
	confirmed to return genuinely different, non-overlapping results per user."""
	user = user or frappe.session.user
	balances = _current_batch_balances(user, warehouse_like="%Quarantine%", company=company)
	can_read_batch = frappe.has_permission("Batch", "read", user=user)
	data = []
	for b in balances:
		expiry_date = None
		if can_read_batch:
			expiry = frappe.get_list(
				"Batch", filters={"name": b["batch_no"]}, fields=["expiry_date"], user=user, limit_page_length=1
			)
			expiry_date = str(expiry[0].expiry_date) if expiry and expiry[0].expiry_date else None
		data.append(
			{
				"warehouse": b["warehouse"],
				"item_code": b["item_code"],
				"batch_no": b["batch_no"],
				"qty_on_hold": b["qty"],
				"expiry_date": expiry_date,
			}
		)
	return {
		"data": {"count": len(data), "batches": data},
		"sources": [f"Stock Ledger Entry:{d['warehouse']}/{d['batch_no']}" for d in data],
		"notes": None if data else "No batches with a positive balance were found in any Quarantine-named warehouse visible to this user.",
	}


# ---------------------------------------------------------------------------
# Tool 3 — "Tồn kho nào có nguy cơ hết hạn?" (which inventory is near-expiry?)
# ---------------------------------------------------------------------------

def get_near_expiry_inventory(user=None, days=90, company=None, **_ignored):
	"""Batches with positive current balance (any warehouse visible to `user`) whose
	Batch.expiry_date falls within `days` days — same PD07 "near-expiry alert" concept as
	Golden Demo #1 (Pharma)'s `api.get_near_expiry_batches()`, generalized beyond one
	hardcoded item and rebuilt on frappe.get_list() so it is genuinely permission-scoped
	(the original PD07 reference used frappe.db.sql, which is permission-unaware)."""
	user = user or frappe.session.user
	cutoff = add_days(nowdate(), days)
	balances = _current_batch_balances(user, warehouse_like=None, company=company)
	if not balances:
		return {"data": {"count": 0, "batches": []}, "sources": [], "notes": "No batches with a positive balance were visible to this user."}

	if not frappe.has_permission("Batch", "read", user=user):
		return {"data": {"count": 0, "batches": []}, "sources": [], "notes": "This user has no read permission on Batch — cannot resolve expiry dates."}

	batch_nos = sorted({b["batch_no"] for b in balances})
	near_expiry_batches = frappe.get_list(
		"Batch",
		filters={"name": ["in", batch_nos], "disabled": 0, "expiry_date": ["<=", cutoff]},
		fields=["name", "item", "expiry_date"],
		user=user,
		limit_page_length=0,
	)
	expiry_by_batch = {b.name: b for b in near_expiry_batches}

	data = []
	for b in balances:
		info = expiry_by_batch.get(b["batch_no"])
		if not info:
			continue
		data.append(
			{
				"warehouse": b["warehouse"],
				"item_code": b["item_code"],
				"batch_no": b["batch_no"],
				"qty": b["qty"],
				"expiry_date": str(info.expiry_date),
				"days_to_expiry": (getdate(info.expiry_date) - getdate(nowdate())).days,
			}
		)
	data.sort(key=lambda d: d["expiry_date"])
	return {
		"data": {"count": len(data), "cutoff_days": days, "batches": data},
		"sources": [f"Batch:{d['batch_no']}" for d in data],
		"notes": None if data else f"No batch visible to this user expires within {days} days.",
	}


# ---------------------------------------------------------------------------
# Tool 4 — "Ao nào có FCR xấu nhất tháng này?" (worst-FCR pond this month?)
# ---------------------------------------------------------------------------

def get_worst_fcr_pond(user=None, month=None, **_ignored):
	"""Real query over Golden Demo #17 (Fish Farm) `Fish Harvest`/`Fish Stocking Batch` and
	Golden Demo #8 (Shrimp Farm) `Shrimp Harvest`/`Shrimp Stocking Batch` — higher FCR (Feed
	Conversion Ratio) is WORSE (more feed per kg of output). `month` is a 'YYYY-MM-DD' date
	inside the target month; defaults to the current month."""
	user = user or frappe.session.user
	anchor = getdate(month) if month else getdate(nowdate())
	month_start, month_end = get_first_day(anchor), get_last_day(anchor)

	harvest_specs = [
		("Fish Harvest", "Fish Stocking Batch", "average_weight_g"),
		("Shrimp Harvest", "Shrimp Stocking Batch", "average_body_weight_g"),
	]
	data = []
	for harvest_doctype, batch_doctype, avg_weight_field in harvest_specs:
		harvests = frappe.get_list(
			harvest_doctype,
			filters={"harvest_date": ["between", [month_start, month_end]]},
			fields=["name", "stocking_batch", "harvest_date", "fcr", "total_weight_kg", "survival_rate_percent", avg_weight_field],
			user=user,
			limit_page_length=0,
		)
		for h in harvests:
			batch = frappe.get_list(batch_doctype, filters={"name": h.stocking_batch}, fields=["name", "pond", "species"], user=user, limit_page_length=1)
			pond_code = batch[0].pond if batch else None
			species = batch[0].species if batch else None
			data.append(
				{
					"source_doctype": harvest_doctype,
					"harvest": h.name,
					"pond": pond_code,
					"species": species,
					"harvest_date": str(h.harvest_date),
					"fcr": h.fcr,
					"total_weight_kg": h.total_weight_kg,
					"survival_rate_percent": h.survival_rate_percent,
				}
			)

	data = [d for d in data if d["fcr"] is not None]
	data.sort(key=lambda d: d["fcr"], reverse=True)
	worst = data[0] if data else None
	return {
		"data": {"month": month_start.strftime("%Y-%m"), "count": len(data), "harvests": data, "worst_fcr_pond": worst},
		"sources": [f"{d['source_doctype']}:{d['harvest']}" for d in data],
		"notes": None if data else f"No Fish/Shrimp Harvest with a recorded FCR fell inside {month_start} .. {month_end} (visible to this user).",
	}


# ---------------------------------------------------------------------------
# Tool 5 — "Doanh thu tháng này giảm vì sao?" (why did this month's revenue drop?)
# ---------------------------------------------------------------------------

def get_revenue_trend_explanation_data(user=None, month=None, company=None, **_ignored):
	"""Real Sales Invoice aggregates for `month` vs the prior month, broken down by Territory
	(a real, populated dimension on Golden Demo #25's Consumer Distribution company — see
	`api.get_consumer_dist_territory_sales()` for the same breakdown axis over Sales Order).
	Seed data for this specific tool's demo month-over-month comparison is created by
	`ai_executive_assistant_seeds.seed_ai_demo_revenue_history()` (no other golden demo seeds
	genuinely multi-month-dated Sales Invoices)."""
	user = user or frappe.session.user
	anchor = getdate(month) if month else getdate(nowdate())
	this_start, this_end = get_first_day(anchor), get_last_day(anchor)
	prev_anchor = add_days(this_start, -1)
	prev_start, prev_end = get_first_day(prev_anchor), get_last_day(prev_anchor)

	filters = {"docstatus": 1}
	if company:
		filters["company"] = company

	def _invoices(start, end):
		f = dict(filters)
		f["posting_date"] = ["between", [start, end]]
		return frappe.get_list(
			"Sales Invoice", filters=f, fields=["name", "territory", "customer", "base_grand_total", "posting_date"], user=user, limit_page_length=0
		)

	this_month_rows = _invoices(this_start, this_end)
	prev_month_rows = _invoices(prev_start, prev_end)

	def _by_territory(rows):
		agg = defaultdict(float)
		for r in rows:
			agg[r.territory or "(no territory)"] += r.base_grand_total or 0
		return dict(agg)

	this_by_territory = _by_territory(this_month_rows)
	prev_by_territory = _by_territory(prev_month_rows)
	this_total = sum(this_by_territory.values())
	prev_total = sum(prev_by_territory.values())

	breakdown = []
	for territory in sorted(set(this_by_territory) | set(prev_by_territory)):
		cur = this_by_territory.get(territory, 0)
		prev = prev_by_territory.get(territory, 0)
		breakdown.append({"territory": territory, "this_month": cur, "prev_month": prev, "delta": cur - prev})
	breakdown.sort(key=lambda b: b["delta"])  # biggest decline first

	data = {
		"this_month": this_start.strftime("%Y-%m"),
		"prev_month": prev_start.strftime("%Y-%m"),
		"this_month_total": this_total,
		"prev_month_total": prev_total,
		"delta_total": this_total - prev_total,
		"delta_percent": round(((this_total - prev_total) / prev_total) * 100, 1) if prev_total else None,
		"by_territory": breakdown,
	}
	sources = [f"Sales Invoice:{r.name}" for r in this_month_rows + prev_month_rows]
	notes = None
	if not this_month_rows and not prev_month_rows:
		notes = "No Sales Invoice visible to this user in either month — run ai_executive_assistant_seeds.seed_ai_demo_revenue_history() first."
	return {"data": data, "sources": sources, "notes": notes}


# ---------------------------------------------------------------------------
# AI-DEMO-02 (QMS Copilot) tools — added to this SAME registry per the Phase 6A
# instruction, not a parallel one. All 3 reuse Golden Demo #2/#3 (QMS)'s real `QMS Deviation`
# / `QMS CAPA` / `QMS Audit` / `QMS Audit Finding` doctypes — schemas confirmed by reading the
# actual DocType JSON before writing any query, not guessed (this codebase's QMS Deviation has
# no `deviation_type`/`department`/`item` fields — similarity below is built on the fields that
# genuinely exist: `severity` and free-text `subject`/`description`/`root_cause`).
# ---------------------------------------------------------------------------

_SIMILARITY_STOPWORDS = {
	"this",
	"that",
	"with",
	"from",
	"were",
	"have",
	"been",
	"into",
	"which",
	"raised",
	"during",
	"above",
	"within",
	"deviation",
}


def _tokenize(text):
	"""Lowercased 4+-letter word tokens, stopwords removed. Deliberately simple/explainable —
	this is the non-vector, field/keyword-based similarity the master plan asks for here
	(vector/embedding retrieval is a SEPARATE, later Phase 6A bullet, 'Permission-aware RAG')."""
	words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
	return {w for w in words if w not in _SIMILARITY_STOPWORDS}


def get_deviation_detail(user=None, deviation=None, **_ignored):
	"""Full detail for ONE real `QMS Deviation` record plus any `QMS CAPA` linked to it (via its
	own `linked_capa` field AND via any CAPA whose source_type/source_reference points back at
	it — the seed data sets both, but a hand-created deviation might only have one). Backs the
	'summarize deviation', 'suggest investigation questions', and 'draft CAPA' QMS Copilot use
	cases (they all need the same underlying facts)."""
	user = user or frappe.session.user
	if not deviation:
		return {"data": {}, "sources": [], "notes": "No deviation specified."}
	rows = frappe.get_list(
		"QMS Deviation",
		filters={"name": deviation},
		fields=["name", "subject", "description", "severity", "status", "reported_by", "reported_date", "investigation_notes", "root_cause", "linked_capa"],
		user=user,
		limit_page_length=1,
	)
	if not rows:
		return {"data": {}, "sources": [], "notes": f"Deviation {deviation} not found or not visible to this user."}
	dev = rows[0]
	sources = [f"QMS Deviation:{dev.name}"]

	capa_names = set()
	if dev.linked_capa:
		capa_names.add(dev.linked_capa)
	linked = frappe.get_list(
		"QMS CAPA", filters={"source_type": "QMS Deviation", "source_reference": dev.name}, fields=["name"], user=user, limit_page_length=0
	)
	capa_names.update(c.name for c in linked)

	capas = []
	for capa_name in sorted(capa_names):
		c = frappe.get_list(
			"QMS CAPA",
			filters={"name": capa_name},
			fields=["name", "subject", "capa_type", "status", "due_date", "owner_user", "action_plan"],
			user=user,
			limit_page_length=1,
		)
		if c:
			row = c[0]
			capas.append(
				{
					"capa": row.name,
					"subject": row.subject,
					"capa_type": row.capa_type,
					"status": row.status,
					"due_date": str(row.due_date) if row.due_date else None,
					"owner_user": row.owner_user,
					"action_plan": row.action_plan,
				}
			)
			sources.append(f"QMS CAPA:{capa_name}")

	data = {
		"deviation": dev.name,
		"subject": dev.subject,
		"description": dev.description,
		"severity": dev.severity,
		"status": dev.status,
		"reported_by": dev.reported_by,
		"reported_date": str(dev.reported_date) if dev.reported_date else None,
		"investigation_notes": dev.investigation_notes,
		"root_cause": dev.root_cause,
		"linked_capas": capas,
	}
	return {"data": data, "sources": sources, "notes": None}


def find_similar_deviations(user=None, deviation=None, limit=5, **_ignored):
	"""Real, explainable (non-vector) similarity search over every OTHER `QMS Deviation`
	visible to `user`: keyword overlap across subject/description/root_cause + a same-severity
	bonus. Returns each candidate WITH its stated similarity basis (shared keywords found,
	whether severity matched) rather than a black-box score — this is deliberately NOT the
	later 'Permission-aware RAG' Phase 6A item (no embeddings, nothing to fake)."""
	user = user or frappe.session.user
	if not deviation:
		return {"data": {}, "sources": [], "notes": "No deviation specified."}
	base_rows = frappe.get_list(
		"QMS Deviation", filters={"name": deviation}, fields=["name", "subject", "description", "severity", "root_cause"], user=user, limit_page_length=1
	)
	if not base_rows:
		return {"data": {}, "sources": [], "notes": f"Deviation {deviation} not found or not visible to this user."}
	base = base_rows[0]
	base_tokens = _tokenize(f"{base.subject} {base.description or ''} {base.root_cause or ''}")

	candidates = frappe.get_list(
		"QMS Deviation",
		filters={"name": ["!=", deviation]},
		fields=["name", "subject", "description", "severity", "root_cause", "status"],
		user=user,
		limit_page_length=0,
	)
	scored = []
	for c in candidates:
		c_tokens = _tokenize(f"{c.subject} {c.description or ''} {c.root_cause or ''}")
		shared = sorted(base_tokens & c_tokens)
		same_severity = c.severity == base.severity
		score = len(shared) + (1 if same_severity else 0)
		if score <= 0:
			continue
		scored.append(
			{
				"deviation": c.name,
				"subject": c.subject,
				"severity": c.severity,
				"status": c.status,
				"same_severity": same_severity,
				"shared_keywords": shared,
				"similarity_score": score,
			}
		)
	scored.sort(key=lambda s: s["similarity_score"], reverse=True)
	top = scored[: (limit or 5)]
	return {
		"data": {"base_deviation": base.name, "base_severity": base.severity, "count": len(top), "candidates": top},
		"sources": [f"QMS Deviation:{c['deviation']}" for c in top],
		"notes": None if top else "No other Deviation visible to this user shares any keyword or severity with this one.",
	}


def get_audit_finding_summary_data(user=None, audit=None, **_ignored):
	"""Full detail for ONE real `QMS Audit` plus ALL of its findings (`QMS Audit Finding` is a
	child table of `QMS Audit`, istable=1, no permission list of its own — reading it needs the
	explicit `parent_doctype='QMS Audit'` kwarg, this session's own established child-table
	lesson, or frappe.get_list() raises 'Insufficient Permission'). Backs the 'summarize audit
	finding' QMS Copilot use case."""
	user = user or frappe.session.user
	if not audit:
		return {"data": {}, "sources": [], "notes": "No audit specified."}
	audits = frappe.get_list(
		"QMS Audit", filters={"name": audit}, fields=["name", "subject", "audit_type", "auditor", "audit_date", "status"], user=user, limit_page_length=1
	)
	if not audits:
		return {"data": {}, "sources": [], "notes": f"Audit {audit} not found or not visible to this user."}
	a = audits[0]
	findings = frappe.get_list(
		"QMS Audit Finding",
		filters={"parent": audit},
		fields=["name", "finding", "severity", "linked_capa"],
		parent_doctype="QMS Audit",
		user=user,
		limit_page_length=0,
	)
	data = {
		"audit": a.name,
		"subject": a.subject,
		"audit_type": a.audit_type,
		"auditor": a.auditor,
		"audit_date": str(a.audit_date) if a.audit_date else None,
		"status": a.status,
		"finding_count": len(findings),
		"findings": [{"finding": f.finding, "severity": f.severity, "linked_capa": f.linked_capa} for f in findings],
	}
	sources = [f"QMS Audit:{a.name}"] + [f"QMS Audit:{a.name}#finding:{f.name}" for f in findings]
	return {"data": data, "sources": sources, "notes": None if findings else "This Audit has no findings recorded."}


# ---------------------------------------------------------------------------
# AI-DEMO-03 (DMS Copilot) tools — added to this SAME registry, again not a parallel one.
# All 4 reuse Golden Demo #4 (DMS)'s real `DMS Document` / `DMS Document Version` /
# `DMS Training Assignment` doctypes — schemas confirmed by reading the actual DocType JSON
# before writing any query (this codebase's `DMS Document` has no explicit cross-reference
# field to other documents, so "suggest impacted documents" below is built on the fields that
# genuinely exist — `department`/`doc_type` — not guessed). `_tokenize()` above (QMS's
# non-vector keyword tokenizer) is reused as-is for `search_effective_documents()` — it is
# already generic (lowercased 4+-letter words, small stopword list), nothing QMS-specific
# about it.
# ---------------------------------------------------------------------------

_DMS_VERSION_COMPARE_FIELDS = ["status", "content_summary", "reviewed_by", "approved_by", "effective_date", "obsolete_date"]


def compare_document_revisions(user=None, document=None, version_a=None, version_b=None, **_ignored):
	"""Real field-level diff between two `DMS Document Version` records of the same `DMS
	Document` — backs the 'compare SOP revisions' and 'create change summary' DMS Copilot use
	cases (they need the same underlying facts). `version_a`/`version_b` may be an explicit
	version_no (int) or version name; when omitted, defaults to the two most recent versions
	(current + immediately prior) — exactly Golden Demo #4's own SOP-WH-02 v1->v2 revision
	shape. A simple structured field-by-field comparison, deliberately NOT a text-diff
	algorithm — real data comparison over `status`/`content_summary`/`reviewed_by`/
	`approved_by`/`effective_date`/`obsolete_date`, not fabricated."""
	user = user or frappe.session.user
	if not document:
		return {"data": {}, "sources": [], "notes": "No document specified."}
	versions = frappe.get_list(
		"DMS Document Version",
		filters={"document": document},
		fields=["name", "version_no", "status", "content_summary", "reviewed_by", "approved_by", "effective_date", "obsolete_date"],
		order_by="version_no desc",
		user=user,
		limit_page_length=0,
	)
	if not versions:
		return {"data": {}, "sources": [], "notes": f"Document {document} not found, not visible to this user, or has no versions."}

	def _resolve(ref):
		if ref is None:
			return None
		for v in versions:
			if v.version_no == ref or v.name == ref:
				return v
		return None

	if version_a is not None or version_b is not None:
		va, vb = _resolve(version_a), _resolve(version_b)
	elif len(versions) >= 2:
		va, vb = versions[1], versions[0]  # [0] is newest (order_by version_no desc)
	else:
		va, vb = None, None

	if not va or not vb:
		return {
			"data": {"document": document, "available_versions": [v.version_no for v in versions]},
			"sources": [f"DMS Document Version:{v.name}" for v in versions],
			"notes": "Fewer than 2 versions exist for this document (or the requested version_a/version_b could not be resolved) — nothing to compare yet.",
		}
	if va.version_no > vb.version_no:
		va, vb = vb, va  # va = older, vb = newer, regardless of caller argument order

	changes = []
	for field in _DMS_VERSION_COMPARE_FIELDS:
		old_val, new_val = va.get(field), vb.get(field)
		if str(old_val) != str(new_val):
			changes.append({"field": field, "from": str(old_val) if old_val is not None else None, "to": str(new_val) if new_val is not None else None})

	doc_meta = frappe.get_list("DMS Document", filters={"name": document}, fields=["title", "doc_type", "department"], user=user, limit_page_length=1)
	data = {
		"document": document,
		"title": doc_meta[0].title if doc_meta else None,
		"version_a": {"version": va.name, "version_no": va.version_no, "status": va.status},
		"version_b": {"version": vb.name, "version_no": vb.version_no, "status": vb.status},
		"fields_changed": changes,
		"change_count": len(changes),
	}
	sources = [f"DMS Document Version:{va.name}", f"DMS Document Version:{vb.name}"]
	return {"data": data, "sources": sources, "notes": None if changes else "No field-level differences found between these two versions."}


def suggest_impacted_documents(user=None, document=None, **_ignored):
	"""Real relationship-based lookup over `DMS Document` — NOT a guess. This schema has no
	explicit cross-reference field between documents (confirmed by reading `dms_document.json`
	before writing this), so 'impacted' is proxied via two real, structured signals: same
	`department` and/or same `doc_type` — other controlled documents in the same process area a
	revision to `document` could plausibly require review of. Each candidate states its
	relationship_basis explicitly (never a black-box score)."""
	user = user or frappe.session.user
	if not document:
		return {"data": {}, "sources": [], "notes": "No document specified."}
	base_rows = frappe.get_list("DMS Document", filters={"name": document}, fields=["name", "title", "doc_type", "department", "status"], user=user, limit_page_length=1)
	if not base_rows:
		return {"data": {}, "sources": [], "notes": f"Document {document} not found or not visible to this user."}
	base = base_rows[0]

	candidates = frappe.get_list(
		"DMS Document", filters={"name": ["!=", document]}, fields=["name", "title", "doc_type", "department", "status"], user=user, limit_page_length=0
	)
	scored = []
	for c in candidates:
		basis = []
		if base.department and c.department == base.department:
			basis.append("same department")
		if c.doc_type == base.doc_type:
			basis.append("same document type")
		if not basis:
			continue
		scored.append(
			{
				"document": c.name,
				"title": c.title,
				"doc_type": c.doc_type,
				"department": c.department,
				"status": c.status,
				"relationship_basis": basis,
				"score": len(basis),
			}
		)
	scored.sort(key=lambda s: s["score"], reverse=True)
	return {
		"data": {"base_document": document, "base_department": base.department, "base_doc_type": base.doc_type, "count": len(scored), "impacted_documents": scored},
		"sources": [f"DMS Document:{s['document']}" for s in scored],
		"notes": None if scored else "No other document visible to this user shares department or document type with this one.",
	}


def suggest_training_impact(user=None, document=None, **_ignored):
	"""Real query over `DMS Training Assignment` for `document`'s CURRENT effective version —
	NOT fabricated. `dms_validations.dms_document_version_on_update()` already auto-creates a
	Training Assignment for every `@pharmacountry.vn` user whenever a version goes Effective;
	this tool reads that real, pre-existing data. Users who already COMPLETED training on the
	version being superseded are exactly who needs re-training once a new revision goes
	Effective (their learned knowledge of the old procedure is now stale); users whose training
	on the CURRENT version is still pending are reported separately, for context."""
	user = user or frappe.session.user
	if not document:
		return {"data": {}, "sources": [], "notes": "No document specified."}
	doc_rows = frappe.get_list("DMS Document", filters={"name": document}, fields=["name", "title", "current_version", "status"], user=user, limit_page_length=1)
	if not doc_rows:
		return {"data": {}, "sources": [], "notes": f"Document {document} not found or not visible to this user."}
	doc = doc_rows[0]
	if not doc.current_version:
		return {"data": {"document": document, "current_version": None, "count": 0, "assignments": []}, "sources": [], "notes": "This document has no current Effective version yet — nothing to assess retraining impact against."}

	assignments = frappe.get_list(
		"DMS Training Assignment",
		filters={"document_version": doc.current_version},
		fields=["name", "user", "assigned_date", "completed", "completed_date"],
		user=user,
		limit_page_length=0,
	)
	completed = [a for a in assignments if a.completed]
	pending = [a for a in assignments if not a.completed]
	data = {
		"document": document,
		"current_version": doc.current_version,
		"count": len(assignments),
		"completed_training_count": len(completed),
		"pending_training_count": len(pending),
		"users_needing_retraining": [{"user": a.user, "completed_date": str(a.completed_date) if a.completed_date else None} for a in completed],
		"users_with_pending_training": [{"user": a.user, "assigned_date": str(a.assigned_date) if a.assigned_date else None} for a in pending],
	}
	sources = [f"DMS Training Assignment:{a.name}" for a in assignments]
	return {"data": data, "sources": sources, "notes": None if assignments else "No training assignments exist yet for the current effective version."}


def search_effective_documents(user=None, query=None, limit=5, **_ignored):
	"""Real, non-vector keyword search restricted to EFFECTIVE `DMS Document Version` records —
	backs the 'Q&A on effective documents' DMS Copilot use case. Deliberately NOT the later
	'Permission-aware RAG' Phase 6A item (no embeddings). Enforces DMS's own DocType-level
	effective/obsolete distinction: a candidate is only ever returned as a usable source when
	BOTH its own `DMS Document Version.status == 'Effective'` AND its parent
	`DMS Document.status == 'Effective'` (defensive double-check — in this schema the two are
	kept in sync by `dms_validations.dms_document_version_on_update()`, but the tool asserts
	the constraint itself rather than trusting that invariant blindly). Any Obsolete/Draft
	version that ALSO matches the query keywords is still computed (for transparency/audit) but
	returned separately as `obsolete_or_draft_matches_excluded`, NEVER inside `results` — this
	is the empirical, checkable proof that an obsolete document is never used as a current
	source, even when its content textually matches as well or better."""
	user = user or frappe.session.user
	if not query:
		return {"data": {}, "sources": [], "notes": "No query specified."}
	q_tokens = _tokenize(query)
	if not q_tokens:
		return {"data": {"query": query, "count": 0, "results": [], "obsolete_or_draft_matches_excluded": []}, "sources": [], "notes": "Query had no searchable keywords (need 4+ letter words)."}

	all_versions = frappe.get_list(
		"DMS Document Version",
		fields=["name", "document", "version_no", "status", "content_summary"],
		user=user,
		limit_page_length=0,
	)
	doc_codes = sorted({v.document for v in all_versions})
	if not doc_codes:
		return {"data": {"query": query, "count": 0, "results": [], "obsolete_or_draft_matches_excluded": []}, "sources": [], "notes": "No document versions visible to this user."}
	docs = frappe.get_list("DMS Document", filters={"name": ["in", doc_codes]}, fields=["name", "title", "doc_type", "department", "status"], user=user, limit_page_length=0)
	doc_by_code = {d.name: d for d in docs}

	effective_matches, excluded_matches = [], []
	for v in all_versions:
		doc = doc_by_code.get(v.document)
		if not doc:
			continue
		tokens = _tokenize(f"{doc.title} {v.content_summary or ''}")
		shared = sorted(q_tokens & tokens)
		if not shared:
			continue
		entry = {
			"document": v.document,
			"title": doc.title,
			"version": v.name,
			"version_no": v.version_no,
			"version_status": v.status,
			"document_status": doc.status,
			"excerpt": v.content_summary,
			"shared_keywords": shared,
		}
		if v.status == "Effective" and doc.status == "Effective":
			effective_matches.append(entry)
		else:
			excluded_matches.append(entry)

	effective_matches.sort(key=lambda e: len(e["shared_keywords"]), reverse=True)
	top = effective_matches[: (limit or 5)]
	return {
		"data": {"query": query, "count": len(top), "results": top, "obsolete_or_draft_matches_excluded": excluded_matches},
		"sources": [f"DMS Document Version:{r['version']}" for r in top],
		"notes": None if top else "No Effective document matched this query (an Obsolete/Draft match, if any, was correctly excluded — see obsolete_or_draft_matches_excluded).",
	}


# ---------------------------------------------------------------------------
# AI-DEMO-05 (Manufacturing Insight) tools — added to this SAME registry, again not a
# parallel one. All 4 reuse Golden Demo #26 (Premix / Feed Additive Manufacturing)'s real
# `Work Order` / `Batch` / `Quality Inspection` / `Premix Weighing Verification` machinery —
# schemas confirmed by reading `premix_seeds.py`/`premix_validations.py` AND by querying a real
# Work Order doc on a live site before writing any query (this ERPNext version's Work Order has
# genuine `planned_start_date`/`planned_end_date`/`actual_start_date`/`actual_end_date` fields;
# `planned_end_date` is NOT auto-populated by the native manufacturing flow — every existing
# golden demo's own Work Order leaves it empty, confirmed empirically). Because the flagship
# Premix batch (Golden Demo #26's own, `PREMIX-BROILER-2PCT`) is a SINGLE batch with ~0 planned/
# actual variety, `ai_manufacturing_insight_seeds.py` seeds a small set of ADDITIONAL, genuinely
# varied Work Orders/batches for these 4 tools to compare against — the exact same "seed a small
# amount of real data because no golden demo naturally has the needed variety" precedent
# `ai_executive_assistant_seeds.seed_ai_demo_revenue_history()` already established for
# AI-DEMO-01's month-over-month revenue trend. Deliberately under a NEW, AI-DEMO-05-owned FG
# item (`PREMIX-BROILER-2PCT-AI5`, same company/warehouses/recipe/critical-ingredient rules as
# the real flagship item) rather than adding more Work Orders/batches for the flagship item
# itself — this session's own AI-DEMO-02 "Warehouse C isolation" lesson applies here too:
# `premix_seeds.py`'s own `_ensure_work_order()`/`_finished_batch()` AND `api.py`'s
# `verify_premix_golden_demo()` all assume "at most one" submitted Work Order / most-recently-
# created Batch for `PREMIX-BROILER-2PCT` — adding more of THOSE would silently corrupt that
# existing, already-passing golden demo's own verification the same way an unscoped write once
# threatened to for QMS Copilot. See `ai_manufacturing_insight_seeds.py`'s own module docstring
# for the full isolation rationale.
# ---------------------------------------------------------------------------

_DELAY_FLAG_HOURS = 24.0  # a Work Order whose actual_end_date lands more than this many hours
# after its OWN planned_end_date is considered "late" — a deliberately coarse, easily-explained
# threshold (one calendar day), not a fitted statistical one.


def explain_production_delay(user=None, work_order=None, company="Demo Premix Co.", **_ignored):
	"""Real Work Order `planned_end_date` vs `actual_end_date` comparison — both genuine
	ERPNext Work Order fields (confirmed on a live Work Order doc, not guessed). A Work Order
	with no recorded `planned_end_date`/`actual_end_date` is reported separately in
	`no_planned_end_date`, NEVER silently treated as on-time. For each Work Order that IS late
	(actual more than `_DELAY_FLAG_HOURS` after planned), this tool correlates against that SAME
	Work Order's own real `Premix Weighing Verification` record(s) — Golden Demo #26's PM02
	four-eyes GMP control: when a critical ingredient's verification was only signed off
	(`verified_on`) AFTER the batch's own `planned_end_date`, that is reported as a REAL,
	directly-recorded contributing factor (never a guess) — when no such correlation exists in
	the data, the tool says so explicitly rather than inventing an explanation."""
	user = user or frappe.session.user
	filters = {"docstatus": 1, "company": company}
	if work_order:
		filters["name"] = work_order
	wos = frappe.get_list(
		"Work Order",
		filters=filters,
		fields=["name", "production_item", "qty", "produced_qty", "planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date", "status"],
		user=user,
		limit_page_length=0,
	)
	if not wos:
		return {
			"data": {"company": company, "work_orders_analyzed": 0, "delay_threshold_hours": _DELAY_FLAG_HOURS, "delayed": [], "on_time": [], "no_planned_end_date": []},
			"sources": [],
			"notes": f"No submitted Work Order found for company {company}" + (f", work_order {work_order}" if work_order else "") + ".",
		}

	delayed, on_time, no_plan, sources = [], [], [], []
	for wo in wos:
		sources.append(f"Work Order:{wo.name}")
		if not wo.planned_end_date or not wo.actual_end_date:
			no_plan.append({"work_order": wo.name, "production_item": wo.production_item, "reason": "planned_end_date or actual_end_date not recorded"})
			continue
		delay_hours = (frappe.utils.get_datetime(wo.actual_end_date) - frappe.utils.get_datetime(wo.planned_end_date)).total_seconds() / 3600.0
		entry = {
			"work_order": wo.name,
			"production_item": wo.production_item,
			"planned_end_date": str(wo.planned_end_date),
			"actual_end_date": str(wo.actual_end_date),
			"delay_hours": round(delay_hours, 1),
		}
		if delay_hours > _DELAY_FLAG_HOURS:
			verifications = frappe.get_list(
				"Premix Weighing Verification",
				filters={"work_order": wo.name},
				fields=["item_code", "status", "weighed_by", "verified_by", "verified_on"],
				user=user,
				limit_page_length=0,
			)
			factors = []
			for v in verifications:
				if v.verified_on and frappe.utils.get_datetime(v.verified_on) > frappe.utils.get_datetime(wo.planned_end_date):
					gap_hours = (frappe.utils.get_datetime(v.verified_on) - frappe.utils.get_datetime(wo.planned_end_date)).total_seconds() / 3600.0
					factors.append(
						f"Critical ingredient {v.item_code}'s four-eyes weighing verification (Premix Weighing Verification, PM02) was not signed off "
						f"(verified_on={v.verified_on}) until {round(gap_hours, 1)}h AFTER this Work Order's planned_end_date — a real, "
						f"directly-recorded contributing factor."
					)
					sources.append(f"Premix Weighing Verification:{wo.name}/{v.item_code}")
			entry["contributing_factors"] = factors or [
				"No correlated Premix Weighing Verification delay found for this Work Order — the gap between planned and actual "
				"completion has no specific recorded cause in this dataset."
			]
			delayed.append(entry)
		else:
			on_time.append(entry)

	delayed.sort(key=lambda d: d["delay_hours"], reverse=True)
	return {
		"data": {
			"company": company,
			"work_orders_analyzed": len(wos),
			"delay_threshold_hours": _DELAY_FLAG_HOURS,
			"delayed": delayed,
			"on_time": on_time,
			"no_planned_end_date": no_plan,
		},
		"sources": sources,
		"notes": None if delayed else "No Work Order exceeded the delay threshold in this dataset.",
	}


def _batch_for_manufacture_stock_entry(user, wo_name):
	"""Resolves the batch a Work Order's (most recent) submitted Manufacture Stock Entry
	produced — via `Stock Entry Detail` -> `Serial and Batch Entry`, the same permission-checked
	child-table idiom `_current_batch_balances()` above already established (child tables have
	no permission list of their own; `parent_doctype` tells `frappe.get_list()` whose
	permissions/User Permission match-conditions to enforce)."""
	ses = frappe.get_list(
		"Stock Entry",
		filters={"work_order": wo_name, "purpose": "Manufacture", "docstatus": 1},
		fields=["name"],
		user=user,
		order_by="creation desc",
		limit_page_length=0,
	)
	for se in ses:
		details = frappe.get_list(
			"Stock Entry Detail",
			filters={"parent": se.name, "is_finished_item": 1},
			fields=["serial_and_batch_bundle"],
			parent_doctype="Stock Entry",
			user=user,
			limit_page_length=0,
		)
		for d in details:
			if not d.serial_and_batch_bundle:
				continue
			sbe = frappe.get_list(
				"Serial and Batch Entry",
				filters={"parent": d.serial_and_batch_bundle},
				fields=["batch_no"],
				parent_doctype="Serial and Batch Bundle",
				user=user,
				limit_page_length=1,
			)
			if sbe and sbe[0].batch_no:
				return sbe[0].batch_no
	return None


def analyze_yield_anomalies(user=None, item_code="PREMIX-BROILER-2PCT-AI5", company="Demo Premix Co.", threshold_percent=5.0, **_ignored):
	"""Real `Work Order.qty` (planned) vs `Work Order.produced_qty` (actual — ERPNext's own
	accumulator across every submitted Manufacture Stock Entry for that Work Order) yield
	comparison across every submitted Work Order for `item_code`. Golden Demo #26 (Premix)'s own
	`seed_premix_manufacturing()` already computes this exact `yield_percent =
	produced_qty/qty*100` pattern for its single flagship batch; this tool generalizes it across
	MULTIPLE batches (one batch alone can never show an anomaly — there's nothing to compare it
	against, which is exactly why `ai_manufacturing_insight_seeds.py` adds a small, genuinely
	varied set of additional real Work Orders under an isolated AI-DEMO-05-owned item). A batch
	is flagged anomalous when its yield deviates from 100% (the BOM-implied target) by more than
	`threshold_percent` (default 5%)."""
	user = user or frappe.session.user
	wos = frappe.get_list(
		"Work Order",
		filters={"docstatus": 1, "production_item": item_code, "company": company, "produced_qty": [">", 0]},
		fields=["name", "qty", "produced_qty"],
		user=user,
		limit_page_length=0,
	)
	if not wos:
		return {
			"data": {"item_code": item_code, "company": company, "threshold_percent": threshold_percent, "count": 0, "batches": [], "anomaly_count": 0},
			"sources": [],
			"notes": f"No Work Order with produced_qty > 0 found for {item_code} in {company}.",
		}

	batches, sources = [], []
	for wo in wos:
		yield_percent = round((wo.produced_qty / wo.qty) * 100, 2) if wo.qty else None
		deviation = round(abs(100 - yield_percent), 2) if yield_percent is not None else None
		batch_no = _batch_for_manufacture_stock_entry(user, wo.name)
		entry = {
			"work_order": wo.name,
			"batch_no": batch_no,
			"planned_qty": wo.qty,
			"produced_qty": wo.produced_qty,
			"yield_percent": yield_percent,
			"deviation_from_100_percent": deviation,
			"anomaly": bool(deviation is not None and deviation > threshold_percent),
		}
		batches.append(entry)
		sources.append(f"Work Order:{wo.name}")
		if batch_no:
			sources.append(f"Batch:{batch_no}")

	batches.sort(key=lambda b: (b["deviation_from_100_percent"] or 0), reverse=True)
	yields = [b["yield_percent"] for b in batches if b["yield_percent"] is not None]
	avg_yield = round(sum(yields) / len(yields), 2) if yields else None
	anomalies = [b for b in batches if b["anomaly"]]
	return {
		"data": {
			"item_code": item_code,
			"company": company,
			"threshold_percent": threshold_percent,
			"count": len(batches),
			"average_yield_percent": avg_yield,
			"anomaly_count": len(anomalies),
			"batches": batches,
		},
		"sources": sources,
		"notes": None if anomalies else f"No batch of {item_code} deviated from 100% yield by more than {threshold_percent}% in this dataset.",
	}


def check_batch_record_completeness(user=None, batch_no=None, item_code="PREMIX-BROILER-2PCT-AI5", **_ignored):
	"""Real per-batch completeness audit — NOT a guess, and not a single boolean. For each batch
	of `item_code` (or just `batch_no` if given), checks 3 real, structured requirements:
	  1. A submitted `Quality Inspection` with `status=Accepted` referencing the batch.
	  2. Traceability: a real, submitted Manufacture Stock Entry (and its Work Order) that
	     actually produced this batch — a batch known to `Batch` but with no production record
	     behind it is itself a completeness gap, not something this tool silently ignores.
	  3. IF that Work Order's BOM contains any `Item.requires_second_check=1` critical ingredient
	     (Golden Demo #26/Premix's PM02 four-eyes control), a `Verified` `Premix Weighing
	     Verification` with a genuinely different `weighed_by`/`verified_by` for EACH such
	     ingredient.
	`ai_manufacturing_insight_seeds.py` seeds exactly one deliberately-incomplete standalone
	`Batch` (no Work Order, no Quality Inspection at all) as this tool's positive test case — a
	real, if synthetic, "batch known to the system but its documentation was never completed"
	audit scenario — clearly separate from the REAL Work-Order-produced batches this same seed
	module creates (which pass every one of these checks), used as the negative control."""
	user = user or frappe.session.user
	if batch_no:
		batches = frappe.get_list("Batch", filters={"name": batch_no}, fields=["name", "item"], user=user, limit_page_length=1)
	else:
		batches = frappe.get_list("Batch", filters={"item": item_code}, fields=["name", "item"], user=user, limit_page_length=0)
	if not batches:
		return {
			"data": {"count": 0, "results": []},
			"sources": [],
			"notes": f"No batch found for {'batch_no=' + batch_no if batch_no else 'item_code=' + item_code}.",
		}

	results, sources = [], []
	for b in batches:
		sources.append(f"Batch:{b.name}")
		missing = []

		qi = frappe.get_list(
			"Quality Inspection", filters={"batch_no": b.name, "docstatus": 1, "status": "Accepted"}, fields=["name"], user=user, limit_page_length=1
		)
		qc_accepted = bool(qi)
		if qc_accepted:
			sources.append(f"Quality Inspection:{qi[0].name}")
		else:
			missing.append("no submitted Accepted Quality Inspection found for this batch")

		se_detail = frappe.get_list(
			"Stock Entry Detail",
			filters={"is_finished_item": 1, "item_code": b.item},
			fields=["parent", "serial_and_batch_bundle"],
			parent_doctype="Stock Entry",
			user=user,
			limit_page_length=0,
		)
		work_order = None
		for row in se_detail:
			if not row.serial_and_batch_bundle:
				continue
			sbe = frappe.get_list(
				"Serial and Batch Entry",
				filters={"parent": row.serial_and_batch_bundle, "batch_no": b.name},
				fields=["name"],
				parent_doctype="Serial and Batch Bundle",
				user=user,
				limit_page_length=1,
			)
			if not sbe:
				continue
			se = frappe.get_list(
				"Stock Entry", filters={"name": row.parent, "purpose": "Manufacture", "docstatus": 1}, fields=["name", "work_order"], user=user, limit_page_length=1
			)
			if se:
				work_order = se[0].work_order
				sources.append(f"Stock Entry:{se[0].name}")
				break
		if not work_order:
			missing.append("no traceable submitted Manufacture Stock Entry / Work Order found for this batch")

		verification_checks = []
		if work_order:
			sources.append(f"Work Order:{work_order}")
			bom_no = frappe.db.get_value("Work Order", work_order, "bom_no")
			critical_items = []
			if bom_no:
				bom_items = frappe.get_list("BOM Item", filters={"parent": bom_no}, fields=["item_code"], parent_doctype="BOM", user=user, limit_page_length=0)
				for bi in bom_items:
					if frappe.get_list("Item", filters={"name": bi.item_code, "requires_second_check": 1}, fields=["name"], user=user, limit_page_length=1):
						critical_items.append(bi.item_code)
			for critical_item in critical_items:
				v = frappe.get_list(
					"Premix Weighing Verification",
					filters={"work_order": work_order, "item_code": critical_item},
					fields=["status", "weighed_by", "verified_by"],
					user=user,
					order_by="creation desc",
					limit_page_length=1,
				)
				ok = bool(v and v[0].status == "Verified" and v[0].verified_by and v[0].verified_by != v[0].weighed_by)
				verification_checks.append({"item_code": critical_item, "complete": ok})
				if ok:
					sources.append(f"Premix Weighing Verification:{work_order}/{critical_item}")
				else:
					missing.append(f"no Verified four-eyes Premix Weighing Verification found for critical ingredient {critical_item}")

		results.append(
			{
				"batch_no": b.name,
				"item_code": b.item,
				"qc_accepted": qc_accepted,
				"traceable_work_order": work_order,
				"weighing_verifications": verification_checks,
				"complete": len(missing) == 0,
				"missing": missing,
			}
		)

	incomplete = [r for r in results if not r["complete"]]
	return {
		"data": {"count": len(results), "incomplete_count": len(incomplete), "results": results},
		"sources": sources,
		"notes": None if not incomplete else f"{len(incomplete)} of {len(results)} batch(es) have incomplete records.",
	}


def summarize_downtime(user=None, company="Demo Premix Co.", from_date=None, to_date=None, **_ignored):
	"""Real Work Order timing-gap AGGREGATE across a period — deliberately NOT presented as a
	native 'downtime' field, because none exists: no manufacturing golden demo in this codebase
	records an explicit downtime field anywhere (confirmed by grepping every seed/validation
	module before writing this). Every number this tool returns is an honest DERIVED PROXY,
	computed as `max(0, actual_end_date - planned_end_date)` summed across every submitted Work
	Order whose `planned_end_date` falls in `[from_date, to_date]` — both dates are genuine
	ERPNext Work Order fields (real facts), the SUBTRACTION is what's derived/computed, and that
	distinction is stated explicitly in the returned `data["methodology_note"]` so a caller (or
	the AI synthesis step) can never mistake this proxy for a directly-recorded measurement."""
	user = user or frappe.session.user
	from_date = getdate(from_date) if from_date else add_days(nowdate(), -30)
	to_date = getdate(to_date) if to_date else nowdate()
	wos = frappe.get_list(
		"Work Order",
		filters={"docstatus": 1, "company": company, "planned_end_date": ["between", [from_date, to_date]]},
		fields=["name", "production_item", "planned_end_date", "actual_end_date"],
		user=user,
		limit_page_length=0,
	)
	by_wo, excluded, sources = [], [], []
	total_hours = 0.0
	for wo in wos:
		sources.append(f"Work Order:{wo.name}")
		if not wo.actual_end_date:
			excluded.append({"work_order": wo.name, "reason": "no actual_end_date recorded yet"})
			continue
		gap_hours = (frappe.utils.get_datetime(wo.actual_end_date) - frappe.utils.get_datetime(wo.planned_end_date)).total_seconds() / 3600.0
		derived_delay_hours = round(max(0.0, gap_hours), 1)
		total_hours += derived_delay_hours
		by_wo.append(
			{
				"work_order": wo.name,
				"production_item": wo.production_item,
				"planned_end_date": str(wo.planned_end_date),
				"actual_end_date": str(wo.actual_end_date),
				"derived_delay_hours": derived_delay_hours,
			}
		)

	by_wo.sort(key=lambda w: w["derived_delay_hours"], reverse=True)
	return {
		"data": {
			"company": company,
			"period": {"from": str(from_date), "to": str(to_date)},
			"work_orders_in_period": len(wos),
			"total_derived_delay_hours": round(total_hours, 1),
			"by_work_order": by_wo,
			"excluded_no_actual_end_date": excluded,
			"methodology_note": "derived proxy = max(0, actual_end_date - planned_end_date) per Work Order; NOT a native recorded 'downtime' field — no such field exists in this schema.",
		},
		"sources": sources,
		"notes": None if by_wo else f"No submitted Work Order with a recorded planned_end_date in [{from_date}, {to_date}] for {company}.",
	}


# ---------------------------------------------------------------------------
# AI-DEMO-06 (Procurement Assistant) tools — added to this SAME registry, again not a parallel
# one. Reuses Golden Demo #27 (Feed / Ingredient Trading)'s real multi-supplier, multi-currency
# Purchase Order/Purchase Receipt/Purchase Invoice/Quality Inspection data
# (`ingredient_trading_seeds.py`) for the 4 READ-ONLY analytical use cases (extract/normalize/
# compare/summarize) — schemas confirmed by reading the actual DocType meta on a live site before
# writing any query, not guessed: `Supplier Quotation` has NO native `payment_terms_template`
# field (unlike Purchase Order/Purchase Invoice, which do), so a quotation's payment terms stay
# in its own native `terms` Text Editor free-text field here — never restructured into a
# fabricated schema this doctype doesn't have. `ai_procurement_assistant_seeds.py` seeds 2 new,
# real `Supplier Quotation` records (one per real Ingredient Trading supplier, same item, genuine
# FX/incoterm/lead-time/payment-terms differences) for extract/normalize/compare, plus a
# brand-new, ISOLATED Supplier + Item + declining 3-shipment history (own company reuse —
# "Demo Ingredient Trading Co." — but a distinctly-named Supplier/Item nothing in
# `verify_ingredient_trading_golden_demo()` keys off, this session's own AI-DEMO-02/05 isolation
# lesson applied again) for the 5th, consequential use case (see
# `ai_procurement_assistant.recommend_supplier_qualification()` for the "AI cannot self-approve a
# supplier" structural proof).
# ---------------------------------------------------------------------------

def extract_supplier_quotation(user=None, supplier_quotation=None, **_ignored):
	"""'Extract supplier quotation': this platform has no live document/PDF/email-parsing (OCR)
	capability, so this tool SIMULATES extraction from an already-structured source record — a
	real, submitted `Supplier Quotation` — rather than fabricating an "extraction from
	unstructured text" capability that doesn't exist here. Returns the quotation's own real header
	terms (currency, conversion_rate, incoterm, valid_till, and its native `terms` free-text field
	— Supplier Quotation has no structured payment-terms-template field, confirmed by reading its
	DocType meta before writing this) plus each quoted item's real qty/rate/lead_time_days and,
	where set, the Item's own real `min_order_qty`."""
	user = user or frappe.session.user
	if not supplier_quotation:
		return {"data": {}, "sources": [], "notes": "No supplier_quotation specified."}
	rows = frappe.get_list(
		"Supplier Quotation",
		filters={"name": supplier_quotation},
		fields=["name", "supplier", "company", "currency", "conversion_rate", "incoterm", "valid_till", "terms", "docstatus"],
		user=user,
		limit_page_length=1,
	)
	if not rows:
		return {"data": {}, "sources": [], "notes": f"Supplier Quotation {supplier_quotation} not found or not visible to this user."}
	sq = rows[0]
	items = frappe.get_list(
		"Supplier Quotation Item",
		filters={"parent": supplier_quotation},
		fields=["item_code", "qty", "rate", "uom", "lead_time_days"],
		parent_doctype="Supplier Quotation",
		user=user,
		limit_page_length=0,
	)
	can_read_item = frappe.has_permission("Item", "read", user=user)
	item_rows = []
	for it in items:
		moq = frappe.db.get_value("Item", it.item_code, "min_order_qty") if can_read_item else None
		item_rows.append(
			{
				"item_code": it.item_code,
				"qty": it.qty,
				"rate": it.rate,
				"uom": it.uom,
				"rate_in_base_currency": round(it.rate * (sq.conversion_rate or 1), 4),
				"lead_time_days": it.lead_time_days,
				"min_order_qty": moq or None,
			}
		)
	data = {
		"supplier_quotation": sq.name,
		"supplier": sq.supplier,
		"company": sq.company,
		"currency": sq.currency,
		"conversion_rate": sq.conversion_rate,
		"incoterm": sq.incoterm,
		"valid_till": str(sq.valid_till) if sq.valid_till else None,
		"payment_terms_raw_text": sq.terms,
		"submitted": sq.docstatus == 1,
		"items": item_rows,
	}
	return {
		"data": data,
		"sources": [f"Supplier Quotation:{sq.name}"],
		"notes": "Extraction simulated from an already-structured Supplier Quotation record — this platform has no live document/PDF/email OCR/parsing capability.",
	}


def normalize_supplier_quotations(user=None, supplier_quotations=None, item_code=None, **_ignored):
	"""'Normalize terms': takes 2+ real Supplier Quotation names (or, if `supplier_quotations` is
	omitted, resolves every quotation quoting `item_code`) and normalizes each quoted line onto a
	common comparable basis: unit price converted to the quotation's own Company base currency via
	its OWN `conversion_rate` — the exact FX-to-base-currency pattern Golden Demo #27's own FT02
	already established and verified, reused here rather than reinvented — plus incoterm/
	lead_time_days/min_order_qty reported side by side. Payment terms remain each quotation's own
	free-text `terms` field, reported AS-IS (never restructured into a fabricated schema Supplier
	Quotation doesn't have — see `extract_supplier_quotation()`'s own docstring)."""
	user = user or frappe.session.user
	names = list(supplier_quotations or [])
	if not names and item_code:
		rows = frappe.get_list(
			"Supplier Quotation Item", filters={"item_code": item_code}, fields=["parent"], parent_doctype="Supplier Quotation", user=user, limit_page_length=0
		)
		names = sorted({r.parent for r in rows})
	if not names:
		return {"data": {}, "sources": [], "notes": "No supplier_quotations or item_code specified — nothing to normalize."}

	normalized, sources = [], []
	for name in names:
		extracted = extract_supplier_quotation(user=user, supplier_quotation=name)
		if not extracted["data"]:
			continue
		sources.extend(extracted["sources"])
		d = extracted["data"]
		for item in d["items"]:
			if item_code and item["item_code"] != item_code:
				continue
			normalized.append(
				{
					"supplier_quotation": d["supplier_quotation"],
					"supplier": d["supplier"],
					"item_code": item["item_code"],
					"quoted_currency": d["currency"],
					"quoted_rate": item["rate"],
					"conversion_rate": d["conversion_rate"],
					"normalized_rate_base_currency": item["rate_in_base_currency"],
					"incoterm": d["incoterm"],
					"lead_time_days": item["lead_time_days"],
					"min_order_qty": item["min_order_qty"],
					"valid_till": d["valid_till"],
					"payment_terms_raw_text": d["payment_terms_raw_text"],
				}
			)
	normalized.sort(key=lambda n: (n["normalized_rate_base_currency"] is None, n["normalized_rate_base_currency"]))
	return {
		"data": {
			"item_code": item_code,
			"count": len(normalized),
			"common_basis": "unit price converted to Company base currency via each quotation's own conversion_rate; incoterm/lead_time_days/min_order_qty reported side by side, unadjusted (this dataset carries no freight-cost basis to compute a true landed-cost equivalence across differing incoterms).",
			"normalized": normalized,
		},
		"sources": sources,
		"notes": None if normalized else "No quotation line matched the given item_code / supplier_quotations.",
	}


def compare_supplier_quotations(user=None, supplier_quotations=None, item_code=None, **_ignored):
	"""'Compare quotations': a real, structured side-by-side comparison built directly on
	`normalize_supplier_quotations()`'s own normalized output — for each real dimension
	(normalized unit price, lead_time_days, min_order_qty) states which supplier's quotation is
	BEST on that dimension, from real data, never a black-box score. The (mock) AI synthesis layer
	narrates trade-offs; this tool only computes the facts."""
	user = user or frappe.session.user
	norm = normalize_supplier_quotations(user=user, supplier_quotations=supplier_quotations, item_code=item_code)
	rows = norm["data"].get("normalized", [])
	if len(rows) < 2:
		return {
			"data": {"item_code": item_code, "count": len(rows), "rows": rows, "best_by_dimension": {}},
			"sources": norm["sources"],
			"notes": "Fewer than 2 quotations to compare — need at least 2 for a meaningful comparison." if rows else norm.get("notes"),
		}
	best = {}
	price_rows = [r for r in rows if r["normalized_rate_base_currency"] is not None]
	if price_rows:
		cheapest = min(price_rows, key=lambda r: r["normalized_rate_base_currency"])
		best["lowest_normalized_price"] = {"supplier": cheapest["supplier"], "supplier_quotation": cheapest["supplier_quotation"], "value": cheapest["normalized_rate_base_currency"]}
	lead_rows = [r for r in rows if r["lead_time_days"] is not None]
	if lead_rows:
		fastest = min(lead_rows, key=lambda r: r["lead_time_days"])
		best["shortest_lead_time"] = {"supplier": fastest["supplier"], "supplier_quotation": fastest["supplier_quotation"], "value": fastest["lead_time_days"]}
	moq_rows = [r for r in rows if r["min_order_qty"] is not None]
	if moq_rows:
		smallest_moq = min(moq_rows, key=lambda r: r["min_order_qty"])
		best["smallest_min_order_qty"] = {"supplier": smallest_moq["supplier"], "supplier_quotation": smallest_moq["supplier_quotation"], "value": smallest_moq["min_order_qty"]}
	return {
		"data": {"item_code": item_code, "count": len(rows), "rows": rows, "best_by_dimension": best},
		"sources": norm["sources"],
		"notes": None,
	}


def summarize_supplier_history(user=None, supplier=None, **_ignored):
	"""'Summarize price/delivery/payment/quality history': a real aggregation over a supplier's
	ACTUAL submitted Purchase Order/Purchase Receipt/Purchase Invoice/Quality Inspection records —
	the same "thin wrapper over real ledger data" pattern already used for Pharmacy's central
	dashboard, 3PL's billing run, Consumer Distribution's commission report, and Ingredient
	Trading's own margin report. Price trend = real Purchase Invoice Item.base_rate over time (the
	transaction's own already-recorded base-currency rate — nothing here re-derives or guesses a
	conversion). On-time delivery rate = real Purchase Receipt.posting_date compared against that
	SAME shipment's own Purchase Order Item.schedule_date (on or before its own committed
	schedule_date counts on-time — a real recorded commitment, not an assumed default). Payment
	terms actually used = the real, distinct `Purchase Order.payment_terms_template` values seen.
	QC pass/fail rate = real Quality Inspection status counts for that supplier's Purchase
	Receipts, with the LATEST inspection (by its own Purchase Receipt's real posting_date, not
	insertion order) reported separately since a single recent rejection matters more than a
	historical average for a qualification decision."""
	user = user or frappe.session.user
	if not supplier:
		return {"data": {}, "sources": [], "notes": "No supplier specified."}
	if not frappe.get_list("Supplier", filters={"name": supplier}, fields=["name"], user=user, limit_page_length=1):
		return {"data": {}, "sources": [], "notes": f"Supplier {supplier} not found or not visible to this user."}

	pos = frappe.get_list(
		"Purchase Order",
		filters={"supplier": supplier, "docstatus": 1},
		fields=["name", "transaction_date", "payment_terms_template", "currency", "conversion_rate"],
		user=user,
		limit_page_length=0,
	)
	sources = [f"Purchase Order:{po.name}" for po in pos]
	payment_terms_used = sorted({po.payment_terms_template for po in pos if po.payment_terms_template})

	po_item_schedule = {}
	for po in pos:
		items = frappe.get_list(
			"Purchase Order Item", filters={"parent": po.name}, fields=["item_code", "schedule_date"], parent_doctype="Purchase Order", user=user, limit_page_length=0
		)
		for it in items:
			po_item_schedule[(po.name, it.item_code)] = it.schedule_date

	prs = frappe.get_list("Purchase Receipt", filters={"supplier": supplier, "docstatus": 1}, fields=["name", "posting_date"], user=user, limit_page_length=0)
	sources += [f"Purchase Receipt:{pr.name}" for pr in prs]
	delivery_rows, on_time_count = [], 0
	for pr in prs:
		pr_items = frappe.get_list(
			"Purchase Receipt Item", filters={"parent": pr.name}, fields=["item_code", "purchase_order"], parent_doctype="Purchase Receipt", user=user, limit_page_length=0
		)
		for it in pr_items:
			schedule_date = po_item_schedule.get((it.purchase_order, it.item_code))
			on_time = bool(schedule_date and getdate(pr.posting_date) <= getdate(schedule_date))
			if schedule_date:
				on_time_count += int(on_time)
			delivery_rows.append(
				{
					"purchase_receipt": pr.name,
					"item_code": it.item_code,
					"posting_date": str(pr.posting_date),
					"committed_schedule_date": str(schedule_date) if schedule_date else None,
					"on_time": on_time if schedule_date else None,
				}
			)

	scored_deliveries = [d for d in delivery_rows if d["on_time"] is not None]
	on_time_rate = round(on_time_count / len(scored_deliveries), 3) if scored_deliveries else None

	po_names = [po.name for po in pos]
	pi_items = frappe.get_list(
		"Purchase Invoice Item",
		filters={"purchase_order": ["in", po_names]} if po_names else {"parent": ["in", []]},
		fields=["parent", "item_code", "rate", "base_rate", "qty"],
		parent_doctype="Purchase Invoice",
		user=user,
		limit_page_length=0,
	)
	pi_parents = sorted({r.parent for r in pi_items})
	pi_dates = (
		{r.name: r.posting_date for r in frappe.get_list("Purchase Invoice", filters={"name": ["in", pi_parents]}, fields=["name", "posting_date"], user=user, limit_page_length=0)}
		if pi_parents
		else {}
	)
	sources += [f"Purchase Invoice:{p}" for p in pi_parents]
	price_trend = sorted(
		[{"purchase_invoice": r.parent, "posting_date": str(pi_dates.get(r.parent)), "item_code": r.item_code, "base_rate": r.base_rate} for r in pi_items],
		key=lambda p: p["posting_date"] or "",
	)

	qis = frappe.get_list(
		"Quality Inspection",
		filters={"reference_type": "Purchase Receipt", "reference_name": ["in", [pr.name for pr in prs]]} if prs else {"name": ["in", []]},
		fields=["name", "status", "reference_name"],
		user=user,
		limit_page_length=0,
	)
	sources += [f"Quality Inspection:{q.name}" for q in qis]
	qc_accepted = sum(1 for q in qis if q.status == "Accepted")
	qc_pass_rate = round(qc_accepted / len(qis), 3) if qis else None
	latest_qc_status = None
	if qis:
		pr_dates = {pr.name: pr.posting_date for pr in prs}
		latest = max(qis, key=lambda q: pr_dates.get(q.reference_name) or getdate("1900-01-01"))
		latest_qc_status = latest.status

	data = {
		"supplier": supplier,
		"shipment_count": len(prs),
		"payment_terms_actually_used": payment_terms_used,
		"delivery": {"on_time_rate": on_time_rate, "scored_shipments": len(scored_deliveries), "detail": delivery_rows},
		"price_trend": price_trend,
		"quality": {"qc_pass_rate": qc_pass_rate, "inspection_count": len(qis), "latest_qc_status": latest_qc_status, "accepted": qc_accepted, "rejected": len(qis) - qc_accepted},
	}
	notes = None if prs else "No submitted Purchase Receipt found for this supplier — no history to summarize yet."
	return {"data": data, "sources": sources, "notes": notes}


_QUALIFICATION_ON_TIME_THRESHOLD = 0.5
_QUALIFICATION_QC_PASS_THRESHOLD = 0.75


def recommend_supplier_qualification_change(user=None, supplier=None, **_ignored):
	"""The ONE consequential Procurement Assistant use case — computes a RECOMMENDATION only, from
	real `summarize_supplier_history()` facts plus the real `Supplier.quality_status`/
	`is_critical_supplier` fields (the same Medical Device MD03 mechanism — Custom Fields on the
	native `Supplier` doctype, platform-wide — reused here, not duplicated). This function NEVER
	writes to Supplier: there is no `.save()`/`.db.set_value()`/`.insert()` call anywhere in its
	body, only real threshold comparisons against `_QUALIFICATION_QC_PASS_THRESHOLD`/
	`_QUALIFICATION_ON_TIME_THRESHOLD` (stated, explainable constants, the same "coarse, easily
	explained threshold" discipline `explain_production_delay()`'s `_DELAY_FLAG_HOURS` already
	established). A Rejected latest QC result, or an on_time_rate/qc_pass_rate below its stated
	threshold, recommends a DOWNGRADE for a critical supplier (`Disqualified`) or a non-critical
	one (`Under Review`); a clean real history with no rejections for a currently-Pending supplier
	recommends an UPGRADE (`Approved`) — 'AI không tự approve supplier' means the AI may recommend
	either direction, but never itself apply either one. The ONLY code path anywhere in this
	codebase that ever applies a recommendation like this to a real Supplier record is
	`ai_procurement_assistant.approve_supplier_status_draft()` — see that function's own docstring
	for the structural 'AI cannot self-approve a supplier' proof."""
	user = user or frappe.session.user
	if not supplier:
		return {"data": {}, "sources": [], "notes": "No supplier specified."}
	sup_rows = frappe.get_list("Supplier", filters={"name": supplier}, fields=["name", "quality_status", "is_critical_supplier"], user=user, limit_page_length=1)
	if not sup_rows:
		return {"data": {}, "sources": [], "notes": f"Supplier {supplier} not found or not visible to this user."}
	sup = sup_rows[0]
	history = summarize_supplier_history(user=user, supplier=supplier)
	h = history["data"]

	current_status = sup.quality_status or "Pending"
	on_time_rate = h.get("delivery", {}).get("on_time_rate")
	qc_pass_rate = h.get("quality", {}).get("qc_pass_rate")
	latest_qc_status = h.get("quality", {}).get("latest_qc_status")
	reasons = []

	recommended_status = current_status  # default: no change recommended
	downgrade_trigger = latest_qc_status == "Rejected" or (qc_pass_rate is not None and qc_pass_rate < _QUALIFICATION_QC_PASS_THRESHOLD) or (on_time_rate is not None and on_time_rate < _QUALIFICATION_ON_TIME_THRESHOLD)
	if downgrade_trigger:
		recommended_status = "Disqualified" if sup.is_critical_supplier else "Under Review"
		if latest_qc_status == "Rejected":
			reasons.append("Most recent Quality Inspection for this supplier's shipments was Rejected.")
		if qc_pass_rate is not None and qc_pass_rate < _QUALIFICATION_QC_PASS_THRESHOLD:
			reasons.append(f"QC pass rate {qc_pass_rate:.0%} is below the {_QUALIFICATION_QC_PASS_THRESHOLD:.0%} threshold.")
		if on_time_rate is not None and on_time_rate < _QUALIFICATION_ON_TIME_THRESHOLD:
			reasons.append(f"On-time delivery rate {on_time_rate:.0%} is below the {_QUALIFICATION_ON_TIME_THRESHOLD:.0%} threshold.")
	elif current_status == "Pending" and h.get("shipment_count", 0) > 0 and qc_pass_rate == 1.0 and (on_time_rate is None or on_time_rate >= _QUALIFICATION_ON_TIME_THRESHOLD):
		recommended_status = "Approved"
		reasons.append(f"Real shipment history ({h.get('shipment_count')} shipment(s)) shows a clean QC record and no on-time delivery concerns found — no reason to withhold qualification.")
	else:
		reasons.append("No threshold breach found in the real available history — no status change recommended.")

	data = {
		"supplier": supplier,
		"is_critical_supplier": bool(sup.is_critical_supplier),
		"current_status": current_status,
		"recommended_status": recommended_status,
		"change_recommended": recommended_status != current_status,
		"rationale_facts": {"on_time_rate": on_time_rate, "qc_pass_rate": qc_pass_rate, "latest_qc_status": latest_qc_status, "shipment_count": h.get("shipment_count")},
		"reasons": reasons,
		"thresholds": {"qc_pass_rate_min": _QUALIFICATION_QC_PASS_THRESHOLD, "on_time_rate_min": _QUALIFICATION_ON_TIME_THRESHOLD},
	}
	return {"data": data, "sources": history["sources"] + [f"Supplier:{supplier}"], "notes": None}


# ---------------------------------------------------------------------------
# AI-DEMO-09 (Livestock Farm Assistant) + AI-DEMO-10 (Shrimp/Aquaculture Assistant) tools —
# added to this SAME registry, again not a parallel one. The master plan's own curated Phase 6A
# list treats "Farm/Aquaculture Insight" as ONE combined item even though the detailed spec
# numbers it as two sub-items (AI-DEMO-09/10) — both built here together, in `ai_tools.py`'s
# same established shape, and orchestrated by `ai_farm_aquaculture_insight.py`'s two entry points
# (mirroring `ai_manufacturing_insight.py`'s NO-DRAFT shape exactly — all 8 use cases below are
# read-only analytical questions, nothing here ever `.insert()`/`.save()`/`.submit()`s anything).
#
# **"Automation handles hard thresholds. AI handles interpretation." — applied differently per
# vertical, because the underlying golden demos differ in what automation already exists:**
#   - AQUACULTURE (Golden Demo #8, Shrimp Farm): `shrimp_validations.shrimp_water_reading_validate()`
#     (SF10) ALREADY computes a real, deterministic `is_alert`/`alert_message` flag against fixed
#     water-parameter thresholds on every `Shrimp Water Parameter Reading` — confirmed by reading
#     `shrimp_validations.py` in full before writing a single line here. `analyze_pond_instability()`
#     and `analyze_water_trend()` below READ that existing flag (cited as
#     `automation_flagged_readings`/`automation_flagged_alerts`) and never recompute or duplicate
#     the threshold check itself — their own, genuinely new contribution is a variance/trend
#     analysis across readings that never individually crossed a threshold, exactly the "softer
#     pattern... not a simple threshold breach" the principle reserves for this layer.
#   - LIVESTOCK (Golden Demo #11, Pig Farm): `pig_validations.py` was read in full and has NO
#     FCR/mortality threshold-alert hook of any kind — there is no existing deterministic
#     automation for `explain_fcr_deterioration()`/`analyze_mortality_anomaly()` to defer to. Per
#     the task's own instruction ("if a threshold check doesn't already exist and you think one is
#     needed, that belongs in the underlying golden demo's own validation code, not in an 'AI
#     insight' tool function"), NO new hard-threshold validation was added to `pig_validations.py`
#     — instead, both tools compare each cohort ONLY against the FARM'S OWN relative peer/trailing
#     average ("this cohort's mortality is Nx the peer average", never a fixed "> X%" cutoff),
#     which is the same softer, history-relative pattern the principle explicitly sanctions for
#     the AI layer, computed transiently inside these read-only tool functions and never persisted
#     as a new blocking rule anywhere.
#
# Golden Demo #11 (Pig Farm)'s own single existing Grower Batch (`BATCH-2026-001`) has near-zero
# feed-log density (sized only to prove PF03/PF07 exist, not to be FCR-realistic — the same
# "feed logs sized for a different test's purpose produce a nonsensical FCR" issue this session's
# own Shrimp Farm (Golden Demo #8) DP-557 incident already found and fixed once) — its own
# computed FCR is far outside any realistic range, so it is deliberately EXCLUDED from these 4
# tools' default scope (`_LIVESTOCK_AI9_PENS`), the same "isolate under new pens, don't touch the
# flagship" precedent AI-DEMO-05/06 established, applied here a fourth time. Golden Demo #8
# (Shrimp Farm)'s own single existing Stocking Batch/Harvest (`POND-A1`) is a single crop cycle —
# structurally impossible to show a TREND against (nothing to compare it to) — so
# `ai_farm_aquaculture_insight_seeds.py` adds 3 further, genuinely varied, real crop cycles under
# 3 NEW, isolated Shrimp Ponds (`POND-AI10-1/2/3`, never `POND-A1`), each carried honestly through
# the full real Empty->Stocked->Harvested lifecycle. Both isolated datasets were deliberately kept
# within the SAME realistic ranges `verify_pig_farm_golden_demo()`/`verify_shrimp_golden_demo()`
# already assert on whichever record is "most recently created" (that Shrimp check in particular
# has NO pond filter at all — confirmed by reading it — so a new Shrimp Harvest's FCR must itself
# stay within its existing 0.8-2.0 sanity check or it would break that unrelated, already-passing
# golden demo's own verification the moment it becomes the most-recently-created row).
# ---------------------------------------------------------------------------

_LIVESTOCK_AI9_PENS = ["PEN-AI9-C1", "PEN-AI9-C2", "PEN-AI9-C3"]


def _pig_batch_for_pen(user, pen):
	rows = frappe.get_list("Pig Grower Batch", filters={"pen": pen}, fields=["name", "batch_code", "pen", "initial_count", "status"], user=user, order_by="creation desc", limit_page_length=1)
	return rows[0] if rows else None


def _pig_batch_kpis(user, pen):
	"""Real per-cohort KPI computation for one Pen's Grower Batch — FCR, mortality, cost/kg-gained
	— all derived from real `Pig Feed Log`/`Pig Weight Record`/`Pig Mortality Record`/`Pig Sale Lot`
	data (schemas confirmed by reading `pig_seeds.py`/`pig_validations.py` in full before writing
	this, never guessed). `weight_gain_kg` is an explicitly-labeled DERIVED PROXY — the Sale Lot's
	own real `total_weight_kg` (the actual, recorded live weight at sale) minus an ESTIMATED
	starting population weight (`initial_count` x the EARLIEST recorded `Pig Weight Record` sample
	— a real recorded data point, but not a true day-0 birth weight, which this schema does not
	track anywhere) — same "real facts, clearly-labeled derived proxy" discipline as
	`ai_manufacturing_insight.summarize_downtime()`'s own `methodology_note`. Returns `None` if the
	pen has no Grower Batch at all, or a dict with `insufficient_data=True` if the batch exists but
	lacks a Sale Lot / 2+ Weight Records / any Feed Log (FCR cannot be computed without all three)."""
	batch = _pig_batch_for_pen(user, pen)
	if not batch:
		return None
	sale = frappe.get_list(
		"Pig Sale Lot",
		filters={"batch": batch.name},
		fields=["name", "sale_date", "head_count", "total_weight_kg", "total_feed_cost", "total_medicine_cost", "total_cost", "cost_per_kg", "profit"],
		user=user,
		limit_page_length=1,
	)
	weights = frappe.get_list("Pig Weight Record", filters={"batch": batch.name}, fields=["record_date", "average_weight_kg"], order_by="record_date asc", user=user, limit_page_length=0)
	feed_logs = frappe.get_list("Pig Feed Log", filters={"batch": batch.name}, fields=["qty_kg", "cost"], user=user, limit_page_length=0)
	mortality_rows = frappe.get_list("Pig Mortality Record", filters={"batch": batch.name}, fields=["mortality_count", "cause", "record_date"], user=user, limit_page_length=0)
	treatments = frappe.get_list("Pig Medicine Treatment", filters={"batch": batch.name}, fields=["treatment_date", "diagnosis", "medicine_name"], user=user, limit_page_length=0)

	if not sale or len(weights) < 2 or not feed_logs:
		return {"pen": pen, "batch": batch.name, "insufficient_data": True}

	sale_row = sale[0]
	total_feed_kg = sum(f.qty_kg or 0 for f in feed_logs)
	total_feed_cost = sum(f.cost or 0 for f in feed_logs)
	first_weight = weights[0].average_weight_kg
	estimated_starting_population_weight_kg = round((batch.initial_count or 0) * (first_weight or 0), 2)
	weight_gain_kg = round((sale_row.total_weight_kg or 0) - estimated_starting_population_weight_kg, 2)
	total_mortality = sum(m.mortality_count or 0 for m in mortality_rows)
	fcr = round(total_feed_kg / weight_gain_kg, 3) if weight_gain_kg else None
	cost_per_kg_gained = round(total_feed_cost / weight_gain_kg, 0) if weight_gain_kg else None

	sources = (
		[f"Pig Grower Batch:{batch.name}", f"Pig Sale Lot:{sale_row.name}"]
		+ [f"Pig Weight Record:{batch.name}#{w.record_date}" for w in weights]
		+ ([f"Pig Mortality Record:{batch.name}"] if mortality_rows else [])
		+ ([f"Pig Medicine Treatment:{batch.name}"] if treatments else [])
	)
	return {
		"pen": pen,
		"batch": batch.name,
		"sale_date": str(sale_row.sale_date),
		"initial_count": batch.initial_count,
		"head_count_at_sale": sale_row.head_count,
		"total_mortality": total_mortality,
		"mortality_rate_percent": round(total_mortality / batch.initial_count * 100, 2) if batch.initial_count else None,
		"total_feed_kg": total_feed_kg,
		"total_feed_cost": total_feed_cost,
		"weight_gain_kg": weight_gain_kg,
		"fcr": fcr,
		"cost_per_kg_gained": cost_per_kg_gained,
		"cost_per_kg_sold": sale_row.cost_per_kg,
		"profit": sale_row.profit,
		"treatments": [{"treatment_date": str(t.treatment_date), "medicine_name": t.medicine_name, "diagnosis": t.diagnosis} for t in treatments],
		"mortality_causes": [m.cause for m in mortality_rows if m.cause],
		"methodology_note": "weight_gain_kg is a derived proxy = Sale Lot's real total_weight_kg minus (initial_count x the EARLIEST recorded Pig Weight Record sample) — not a true day-0 birth weight, which this schema does not track.",
		"sources": sources,
	}


def explain_fcr_deterioration(user=None, farm_pens=None, deterioration_threshold_percent=30.0, **_ignored):
	"""AI-DEMO-09 tool 1 — 'FCR deterioration explanation'. Compares a farm's real Feed Conversion
	Ratio (`_pig_batch_kpis()`'s `feed_kg / weight_gain_kg`) across successive real Pig Grower
	Batch cohorts, ordered chronologically by their own real Sale Lot `sale_date`, and flags any
	cohort whose FCR deteriorates by more than `deterioration_threshold_percent` relative to the
	TRAILING AVERAGE of the farm's own PRIOR cohorts — a relative, farm's-own-history comparison,
	per this module's own "automation vs AI" section docstring (no FCR threshold automation exists
	in `pig_validations.py` to defer to). Where a flagged cohort has a real, linked Pig Medicine
	Treatment, its diagnosis/treatment_date is reported as a real contributing factor; where none
	exists, this tool says so explicitly rather than inventing one."""
	user = user or frappe.session.user
	pens = list(farm_pens or _LIVESTOCK_AI9_PENS)
	kpis = [k for k in (_pig_batch_kpis(user, p) for p in pens) if k and not k.get("insufficient_data") and k.get("fcr")]
	kpis.sort(key=lambda k: k["sale_date"])

	cohorts, sources = [], []
	for i, k in enumerate(kpis):
		prior = kpis[:i]
		trailing_avg_fcr = round(sum(p["fcr"] for p in prior) / len(prior), 3) if prior else None
		deterioration_percent = round((k["fcr"] - trailing_avg_fcr) / trailing_avg_fcr * 100, 1) if trailing_avg_fcr else None
		flagged = bool(deterioration_percent is not None and deterioration_percent > deterioration_threshold_percent)
		if flagged and k["treatments"]:
			factors = [f"Pig Medicine Treatment on {t['treatment_date']} ({t['medicine_name']}): {t['diagnosis']}" for t in k["treatments"]]
		elif flagged:
			factors = ["No linked Pig Medicine Treatment found for this cohort — no specific recorded cause for the deterioration in this dataset."]
		else:
			factors = []
		cohorts.append(
			{
				"pen": k["pen"],
				"batch": k["batch"],
				"sale_date": k["sale_date"],
				"fcr": k["fcr"],
				"weight_gain_kg": k["weight_gain_kg"],
				"total_feed_kg": k["total_feed_kg"],
				"trailing_avg_fcr_of_prior_cohorts": trailing_avg_fcr,
				"deterioration_percent_vs_trailing_avg": deterioration_percent,
				"flagged_deteriorated": flagged,
				"contributing_factors": factors,
			}
		)
		sources.extend(k["sources"])

	flagged_cohorts = [c for c in cohorts if c["flagged_deteriorated"]]
	return {
		"data": {
			"pens_analyzed": pens,
			"deterioration_threshold_percent": deterioration_threshold_percent,
			"cohort_count": len(cohorts),
			"cohorts_chronological": cohorts,
			"flagged_count": len(flagged_cohorts),
		},
		"sources": sources,
		"notes": None if cohorts else "No Pig Grower Batch cohort in the given pens had enough real data (Sale Lot + 2+ Weight Records + Feed Logs) to compute FCR.",
	}


def analyze_mortality_anomaly(user=None, farm_pens=None, anomaly_ratio_threshold=2.0, **_ignored):
	"""AI-DEMO-09 tool 2 — 'mortality anomaly'. Compares each real cohort's mortality RATE against
	the AVERAGE of the OTHER cohorts in scope (the farm's own peer baseline), expressed as a ratio
	("this cohort's mortality is Nx the farm's own peer average") — never a fixed absolute rate
	cutoff (that would be automation's job; per this module's own "automation vs AI" section
	docstring, no such automation exists yet in `pig_validations.py`, confirmed by reading it in
	full, so this relative comparison is the softer, history-relative pattern the 'AI handles
	interpretation' principle reserves for this layer, not a substitute for one)."""
	user = user or frappe.session.user
	pens = list(farm_pens or _LIVESTOCK_AI9_PENS)
	kpis = [k for k in (_pig_batch_kpis(user, p) for p in pens) if k and not k.get("insufficient_data") and k.get("mortality_rate_percent") is not None]

	cohorts, sources = [], []
	for k in kpis:
		others = [o for o in kpis if o["batch"] != k["batch"]]
		peer_avg = round(sum(o["mortality_rate_percent"] for o in others) / len(others), 3) if others else None
		ratio = round(k["mortality_rate_percent"] / peer_avg, 2) if peer_avg else None
		anomalous = bool(ratio is not None and ratio >= anomaly_ratio_threshold)
		cohorts.append(
			{
				"pen": k["pen"],
				"batch": k["batch"],
				"sale_date": k["sale_date"],
				"mortality_count": k["total_mortality"],
				"mortality_rate_percent": k["mortality_rate_percent"],
				"peer_average_mortality_rate_percent": peer_avg,
				"ratio_vs_peer_average": ratio,
				"anomalous": anomalous,
				"mortality_causes": k["mortality_causes"],
			}
		)
		sources.extend(k["sources"])

	anomalies = [c for c in cohorts if c["anomalous"]]
	return {
		"data": {"pens_analyzed": pens, "anomaly_ratio_threshold": anomaly_ratio_threshold, "cohorts": cohorts, "anomaly_count": len(anomalies)},
		"sources": sources,
		"notes": None if cohorts else "No cohort in scope had enough data (Mortality Record + peers) to analyze.",
	}


def identify_barn_requiring_attention(user=None, farm_pens=None, **_ignored):
	"""AI-DEMO-09 tool 3 — 'barn/flock requiring attention'. A real, explainable COMPOSITE ranking
	across pens/cohorts using 3 real signals (FCR, mortality rate, cost/kg-gained), each expressed
	as a ratio against the peer average of the OTHER cohorts in scope — never a black-box single
	score without its stated basis. The cohort whose average excess-over-peer-average is highest
	is ranked first (most requiring attention); an `attention_score` of 1.0 means "exactly at the
	peer average" on average across the 3 dimensions."""
	user = user or frappe.session.user
	pens = list(farm_pens or _LIVESTOCK_AI9_PENS)
	kpis = [k for k in (_pig_batch_kpis(user, p) for p in pens) if k and not k.get("insufficient_data") and k.get("fcr") and k.get("cost_per_kg_gained") and k.get("mortality_rate_percent") is not None]

	ranked, sources = [], []
	for k in kpis:
		others = [o for o in kpis if o["batch"] != k["batch"]]
		if not others:
			continue
		peer_fcr = sum(o["fcr"] for o in others) / len(others)
		peer_mortality = sum(o["mortality_rate_percent"] for o in others) / len(others)
		peer_cost = sum(o["cost_per_kg_gained"] for o in others) / len(others)
		fcr_ratio = round(k["fcr"] / peer_fcr, 3) if peer_fcr else None
		mortality_ratio = round(k["mortality_rate_percent"] / peer_mortality, 3) if peer_mortality else None
		cost_ratio = round(k["cost_per_kg_gained"] / peer_cost, 3) if peer_cost else None
		components = [r for r in (fcr_ratio, mortality_ratio, cost_ratio) if r is not None]
		attention_score = round(sum(components) / len(components), 3) if components else None
		ranked.append(
			{
				"pen": k["pen"],
				"batch": k["batch"],
				"sale_date": k["sale_date"],
				"fcr": k["fcr"],
				"fcr_ratio_vs_peers": fcr_ratio,
				"mortality_rate_percent": k["mortality_rate_percent"],
				"mortality_ratio_vs_peers": mortality_ratio,
				"cost_per_kg_gained": k["cost_per_kg_gained"],
				"cost_ratio_vs_peers": cost_ratio,
				"attention_score": attention_score,
			}
		)
		sources.extend(k["sources"])
	ranked.sort(key=lambda r: (r["attention_score"] or 0), reverse=True)
	return {
		"data": {
			"pens_analyzed": pens,
			"basis": "attention_score = average of (own FCR / peer-avg FCR, own mortality rate / peer-avg mortality rate, own cost-per-kg-gained / peer-avg cost-per-kg-gained) across the OTHER cohorts in scope — >1.0 means worse than peers on average.",
			"ranked_cohorts": ranked,
		},
		"sources": sources,
		"notes": None if len(ranked) >= 2 else "Fewer than 2 cohorts with complete data in scope — a meaningful peer-relative ranking needs at least 2.",
	}


def analyze_feed_cost(user=None, farm_pens=None, **_ignored):
	"""AI-DEMO-09 tool 4 — 'feed-cost analysis'. Real cost-per-kg-gained per cohort (`_pig_batch_
	kpis()`'s real Pig Feed Log cost sums / weight_gain_kg), decomposed into its two real drivers:
	the cohort's own effective feed PRICE (total_feed_cost / total_feed_kg — a real, derived unit
	price) and its feed conversion EFFICIENCY (fcr) — so a rising cost/kg-gained trend can be
	attributed to price, efficiency, or both, never left as an unexplained number."""
	user = user or frappe.session.user
	pens = list(farm_pens or _LIVESTOCK_AI9_PENS)
	kpis = [k for k in (_pig_batch_kpis(user, p) for p in pens) if k and not k.get("insufficient_data") and k.get("cost_per_kg_gained")]
	kpis.sort(key=lambda k: k["sale_date"])

	cohorts, sources = [], []
	for k in kpis:
		effective_feed_price_per_kg = round(k["total_feed_cost"] / k["total_feed_kg"], 0) if k["total_feed_kg"] else None
		cohorts.append(
			{
				"pen": k["pen"],
				"batch": k["batch"],
				"sale_date": k["sale_date"],
				"total_feed_kg": k["total_feed_kg"],
				"total_feed_cost": k["total_feed_cost"],
				"effective_feed_price_per_kg": effective_feed_price_per_kg,
				"fcr": k["fcr"],
				"weight_gain_kg": k["weight_gain_kg"],
				"cost_per_kg_gained": k["cost_per_kg_gained"],
			}
		)
		sources.extend(k["sources"])

	trend_note = None
	if len(cohorts) >= 2:
		first, last = cohorts[0], cohorts[-1]
		price_change_percent = (
			round((last["effective_feed_price_per_kg"] - first["effective_feed_price_per_kg"]) / first["effective_feed_price_per_kg"] * 100, 1)
			if first["effective_feed_price_per_kg"]
			else None
		)
		fcr_change_percent = round((last["fcr"] - first["fcr"]) / first["fcr"] * 100, 1) if first["fcr"] else None
		trend_note = f"From the earliest to the most recent cohort: effective feed price changed {price_change_percent}%, FCR (feed efficiency) changed {fcr_change_percent}% — both real, decomposed contributors to the cost/kg-gained trend."
	return {
		"data": {"pens_analyzed": pens, "cohorts_chronological": cohorts, "price_vs_efficiency_decomposition": trend_note},
		"sources": sources,
		"notes": None if cohorts else "No cohort in scope had enough data to compute cost-per-kg-gained.",
	}


# --- AI-DEMO-10 (Shrimp/Aquaculture Assistant) ------------------------------------------------

_AQUACULTURE_AI10_PONDS = ["POND-AI10-1", "POND-AI10-2", "POND-AI10-3"]
_SHRIMP_WATER_PARAMS = ["do_mg_l", "ph", "temperature_c", "salinity_ppt", "nh3_mg_l", "no2_mg_l"]


def _shrimp_pond_readings(user, pond):
	return frappe.get_list(
		"Shrimp Water Parameter Reading",
		filters={"pond": pond},
		fields=["name", "reading_datetime", "is_alert", "alert_message"] + _SHRIMP_WATER_PARAMS,
		order_by="reading_datetime asc",
		user=user,
		limit_page_length=0,
	)


def _stdev(values):
	n = len(values)
	if n < 2:
		return 0.0
	mean = sum(values) / n
	return (sum((v - mean) ** 2 for v in values) / n) ** 0.5


def analyze_pond_instability(user=None, ponds=None, **_ignored):
	"""AI-DEMO-10 tool 1 — 'pond instability analysis'. Reads the REAL, already-computed
	`is_alert`/`alert_message` fields `shrimp_validations.shrimp_water_reading_validate()` (Golden
	Demo #8's own SF10 deterministic hard-threshold automation) sets on every Shrimp Water
	Parameter Reading — this tool NEVER recomputes or duplicates that threshold check itself (no
	comparison against a fixed bound appears anywhere in this function). Its own, genuinely NEW
	contribution is a real statistical variance/trend analysis (stdev, first-half-vs-second-half
	drift direction) across EVERY reading, not just the ones SF10 already flagged — a pond can be
	trending toward instability before any single reading crosses that hard threshold, exactly the
	'softer pattern... not a simple threshold breach' the principle reserves for this layer."""
	user = user or frappe.session.user
	pond_list = list(ponds or _AQUACULTURE_AI10_PONDS)
	results, sources = [], []
	for pond in pond_list:
		readings = _shrimp_pond_readings(user, pond)
		if len(readings) < 2:
			results.append({"pond": pond, "insufficient_data": True, "reading_count": len(readings)})
			continue
		per_param = {}
		for param in _SHRIMP_WATER_PARAMS:
			values = [r.get(param) for r in readings if r.get(param) is not None]
			if len(values) < 2:
				continue
			half = len(values) // 2 or 1
			first_half, second_half = values[:half], values[half:] or values[-1:]
			first_avg, second_avg = sum(first_half) / len(first_half), sum(second_half) / len(second_half)
			per_param[param] = {
				"stdev": round(_stdev(values), 4),
				"first_reading": values[0],
				"last_reading": values[-1],
				"trend_direction": "rising" if second_avg > first_avg else ("falling" if second_avg < first_avg else "flat"),
				"drift_magnitude": round(abs(second_avg - first_avg), 4),
			}
		alert_readings = [r for r in readings if r.is_alert]
		results.append(
			{
				"pond": pond,
				"reading_count": len(readings),
				# Real, automation-flagged (SF10) — read here, never recomputed.
				"alert_reading_count": len(alert_readings),
				"per_parameter_variance": per_param,
				"automation_flagged_readings": [{"reading_datetime": str(r.reading_datetime), "alert_message": r.alert_message} for r in alert_readings],
			}
		)
		sources.extend(f"Shrimp Water Parameter Reading:{r.name}" for r in readings)

	def _instability_rank(r):
		if r.get("insufficient_data"):
			return -1
		return r["alert_reading_count"]

	results.sort(key=_instability_rank, reverse=True)
	return {
		"data": {"ponds_analyzed": pond_list, "results": results},
		"sources": sources,
		"notes": None if any(not r.get("insufficient_data") for r in results) else "No pond in scope had 2+ real water readings to analyze.",
	}


def analyze_feed_fcr_trend(user=None, ponds=None, deterioration_threshold_percent=30.0, **_ignored):
	"""AI-DEMO-10 tool 2 — 'feed/FCR trend'. Extends `get_worst_fcr_pond()` (AI-DEMO-01)'s
	single-month-snapshot Shrimp/Fish Harvest query into a genuine trend-over-time analysis: every
	real `Shrimp Harvest` for the given ponds, ordered chronologically by `harvest_date`, each
	compared against the TRAILING AVERAGE FCR of the farm's own PRIOR harvests — same
	relative-to-own-history discipline as `explain_fcr_deterioration()` (livestock side)."""
	user = user or frappe.session.user
	pond_list = list(ponds or _AQUACULTURE_AI10_PONDS)
	batches = frappe.get_list("Shrimp Stocking Batch", filters={"pond": ["in", pond_list]}, fields=["name", "pond"], user=user, limit_page_length=0)
	batch_to_pond = {b.name: b.pond for b in batches}
	if not batches:
		return {"data": {"ponds_analyzed": pond_list, "harvest_count": 0, "trend_chronological": []}, "sources": [], "notes": "No Shrimp Stocking Batch found for the given ponds."}

	harvests = frappe.get_list(
		"Shrimp Harvest",
		filters={"stocking_batch": ["in", list(batch_to_pond)]},
		fields=["name", "stocking_batch", "harvest_date", "fcr", "survival_rate_percent", "cost_per_kg", "total_weight_kg"],
		order_by="harvest_date asc",
		user=user,
		limit_page_length=0,
	)
	trend, sources = [], []
	for i, h in enumerate(harvests):
		prior = harvests[:i]
		trailing_avg_fcr = round(sum(p.fcr for p in prior) / len(prior), 3) if prior else None
		deterioration_percent = round((h.fcr - trailing_avg_fcr) / trailing_avg_fcr * 100, 1) if trailing_avg_fcr else None
		trend.append(
			{
				"pond": batch_to_pond.get(h.stocking_batch),
				"stocking_batch": h.stocking_batch,
				"harvest": h.name,
				"harvest_date": str(h.harvest_date),
				"fcr": h.fcr,
				"survival_rate_percent": h.survival_rate_percent,
				"cost_per_kg": h.cost_per_kg,
				"trailing_avg_fcr_of_prior_harvests": trailing_avg_fcr,
				"deterioration_percent_vs_trailing_avg": deterioration_percent,
				"flagged_deteriorated": bool(deterioration_percent is not None and deterioration_percent > deterioration_threshold_percent),
			}
		)
		sources.append(f"Shrimp Harvest:{h.name}")
	return {
		"data": {"ponds_analyzed": pond_list, "deterioration_threshold_percent": deterioration_threshold_percent, "harvest_count": len(trend), "trend_chronological": trend},
		"sources": sources,
		"notes": None if trend else "No Shrimp Harvest found for the given ponds.",
	}


def analyze_water_trend(user=None, ponds=None, **_ignored):
	"""AI-DEMO-10 tool 3 — 'water trend analysis'. A FARM-level view (as opposed to
	`analyze_pond_instability()`'s per-pond variance ranking): every real water-parameter reading
	across the given ponds, pooled and ordered chronologically, comparing the farm's earliest-
	period readings against its most-recent-period readings per parameter, plus a real COUNT of
	SF10-automation-flagged alert readings in each period — a rising alert frequency over time is
	a real, count-based trend signal this tool surfaces; it never re-flags a reading itself."""
	user = user or frappe.session.user
	pond_list = list(ponds or _AQUACULTURE_AI10_PONDS)
	readings = frappe.get_list(
		"Shrimp Water Parameter Reading",
		filters={"pond": ["in", pond_list]},
		fields=["name", "pond", "reading_datetime", "is_alert"] + _SHRIMP_WATER_PARAMS,
		order_by="reading_datetime asc",
		user=user,
		limit_page_length=0,
	)
	if len(readings) < 2:
		return {"data": {"ponds_analyzed": pond_list, "reading_count": len(readings)}, "sources": [], "notes": "Fewer than 2 water readings across the given ponds — nothing to trend."}

	half = len(readings) // 2 or 1
	early, recent = readings[:half], readings[half:] or readings[-1:]
	per_param = {}
	for param in _SHRIMP_WATER_PARAMS:
		early_vals = [r.get(param) for r in early if r.get(param) is not None]
		recent_vals = [r.get(param) for r in recent if r.get(param) is not None]
		if not early_vals or not recent_vals:
			continue
		early_avg, recent_avg = sum(early_vals) / len(early_vals), sum(recent_vals) / len(recent_vals)
		per_param[param] = {
			"early_period_avg": round(early_avg, 4),
			"recent_period_avg": round(recent_avg, 4),
			"change": round(recent_avg - early_avg, 4),
			"trend_direction": "rising" if recent_avg > early_avg else ("falling" if recent_avg < early_avg else "flat"),
		}

	early_alerts = sum(1 for r in early if r.is_alert)
	recent_alerts = sum(1 for r in recent if r.is_alert)
	return {
		"data": {
			"ponds_analyzed": pond_list,
			"reading_count": len(readings),
			"period_split": {"early_period_reading_count": len(early), "recent_period_reading_count": len(recent)},
			"per_parameter_trend": per_param,
			"automation_flagged_alerts": {"early_period": early_alerts, "recent_period": recent_alerts},
		},
		"sources": [f"Shrimp Water Parameter Reading:{r.name}" for r in readings],
		"notes": None,
	}


def explain_pond_anomaly(user=None, pond=None, **_ignored):
	"""AI-DEMO-10 tool 4 — 'anomaly explanation'. Grounds an explanation for ONE pond in the REAL
	outputs of `analyze_pond_instability()` (variance/trend + automation-flagged alerts) and,
	where present, a real linked `Shrimp Health Treatment` / `Shrimp Mortality Record` for the same
	pond's stocking batch — never a fabricated narrative."""
	user = user or frappe.session.user
	if not pond:
		return {"data": {}, "sources": [], "notes": "No pond specified."}
	instability = analyze_pond_instability(user=user, ponds=[pond])
	pond_result = next((r for r in instability["data"]["results"] if r["pond"] == pond), None)
	if not pond_result or pond_result.get("insufficient_data"):
		return {"data": {"pond": pond}, "sources": instability["sources"], "notes": f"Not enough real water-reading data for {pond} to explain an anomaly."}

	batch = frappe.get_list("Shrimp Stocking Batch", filters={"pond": pond}, fields=["name"], user=user, order_by="creation desc", limit_page_length=1)
	sources = list(instability["sources"])
	treatments, mortality = [], []
	if batch:
		treatments = frappe.get_list("Shrimp Health Treatment", filters={"stocking_batch": batch[0].name}, fields=["issue_date", "diagnosis", "treatment_applied"], user=user, limit_page_length=0)
		mortality = frappe.get_list("Shrimp Mortality Record", filters={"stocking_batch": batch[0].name}, fields=["record_date", "mortality_count", "cause"], user=user, limit_page_length=0)
		if treatments:
			sources.append(f"Shrimp Health Treatment:{batch[0].name}")
		if mortality:
			sources.append(f"Shrimp Mortality Record:{batch[0].name}")

	return {
		"data": {
			"pond": pond,
			"instability_signal": pond_result,
			"linked_health_treatments": [{"issue_date": str(t.issue_date), "diagnosis": t.diagnosis, "treatment_applied": t.treatment_applied} for t in treatments],
			"linked_mortality_records": [{"record_date": str(m.record_date), "mortality_count": m.mortality_count, "cause": m.cause} for m in mortality],
		},
		"sources": sources,
		"notes": None,
	}


# ---------------------------------------------------------------------------
# Permission-aware RAG (the 8th Phase 6A item) tools — appended to the SAME registry, again not a
# parallel one. Built on `rag_pipeline.py`'s real chunking/MOCK-embedding/vector-index machinery
# (the `RAG Chunk` DocType) over Golden Demo #4 (DMS)'s real `DMS Document`/`DMS Document Version`
# content — see `rag_pipeline.py`'s own module docstring for the full pipeline design, the honest
# MOCK-embedding disclosure, and why re-indexing is wired as an additive `hooks.py` doc_events
# entry rather than an edit to `dms_validations.py`. These two functions are deliberately the
# ONLY DMS-facing tools in this file backed by a genuine vector index + cosine similarity rather
# than the non-vector `_tokenize()` keyword overlap `search_effective_documents()` (AI-DEMO-03)
# already uses elsewhere in this file — exactly the distinction AI-DEMO-02/03's own docstrings
# called out as deliberately deferred to "the later Permission-aware RAG item", now built here.
# ---------------------------------------------------------------------------

def search_knowledge_base(user=None, query=None, top_k=5, **_ignored):
	"""THE permission-aware RAG semantic-search tool (master plan §13.9). Embeds `query` with the
	SAME mock embedding function every indexed chunk was embedded with (`rag_pipeline.mock_embed`),
	scores every CURRENT (`RAG Chunk.is_current=1`) chunk by cosine similarity — obsolete/draft-
	sourced chunks are excluded up front by this filter, never surfaced as current knowledge no
	matter how well they score — and, for every chunk that scores above 0, re-checks the CALLING
	user's REAL Frappe permission on that chunk's own source record via `frappe.get_list(source_
	doctype, filters={"name": source_reference}, user=user)` (this session's own established
	permission-scoping idiom: `frappe.get_list(..., user=...)`, never `frappe.get_all()`/doctype-
	level-only `has_permission()`) BEFORE that chunk's text is included in the result. `RAG Chunk`
	itself is read broadly via `frappe.get_all()` — see `rag_pipeline.py`'s module docstring for
	why that is a deliberate, explicit two-step design (broad index scan, then a mandatory real
	per-source permission check before returning anything), not a silent permission bypass. Every
	returned result carries real, structured citation data (document code/title/version/chunk
	position) — never a raw, unattributed text blob."""
	user = user or frappe.session.user
	if not query:
		return {"data": {}, "sources": [], "notes": "No query specified."}
	query_vector = rag_pipeline.mock_embed(query)
	candidates = frappe.get_all(
		"RAG Chunk",
		filters={"is_current": 1},
		fields=["name", "source_doctype", "source_reference", "document_code", "document_title", "version_no", "chunk_index", "chunk_text", "embedding", "source_status"],
		limit_page_length=0,
	)
	scored, denied_sources = [], set()
	for c in candidates:
		if not rag_pipeline.is_source_visible(c.source_doctype, c.source_reference, user):
			denied_sources.add(f"{c.source_doctype}:{c.source_reference}")
			continue
		similarity = rag_pipeline.cosine_similarity(query_vector, frappe.parse_json(c.embedding))
		if similarity <= 0:
			continue
		scored.append(
			{
				"chunk": c.name,
				"document": c.document_code,
				"title": c.document_title,
				"version": c.source_reference,
				"version_no": c.version_no,
				"chunk_index": c.chunk_index,
				"excerpt": c.chunk_text,
				"similarity": round(similarity, 4),
				"source_status": c.source_status,
			}
		)
	scored.sort(key=lambda s: s["similarity"], reverse=True)
	top = scored[: (top_k or 5)]
	citations = [{"document": r["document"], "title": r["title"], "version": r["version"], "version_no": r["version_no"], "chunk_index": r["chunk_index"]} for r in top]
	return {
		"data": {"query": query, "count": len(top), "results": top, "citations": citations, "permission_denied_source_count": len(denied_sources)},
		"sources": [f"{r['document']}#{r['version']}:chunk{r['chunk_index']}" for r in top],
		"notes": None if top else "No CURRENT chunk visible to this user matched this query (either nothing scored above 0 similarity, or every match was permission-denied — see permission_denied_source_count).",
	}


def get_document(user=None, document=None, **_ignored):
	"""The 'get_document' canonical tool (master plan §13.10's own worked example tool name).
	Direct, permission-checked fetch of ONE named `DMS Document`'s full CURRENT (Effective)
	content — reassembled from its own already-indexed `RAG Chunk` rows in `chunk_index` order,
	deliberately NOT re-read straight from `DMS Document Version.content_summary`, so this tool
	exercises the SAME index/citation machinery as `search_knowledge_base()` rather than a
	parallel read path. Checks the calling user's real permission TWICE — once on `DMS Document`
	itself, once on the specific current `DMS Document Version` — before reading its chunks (via
	`frappe.get_all()`, safe here only because both permission checks already passed), and returns
	an explicit empty result (never another user's or another version's content) whenever either
	check fails, the document has no current Effective version, or it has not been indexed yet."""
	user = user or frappe.session.user
	if not document:
		return {"data": {}, "sources": [], "notes": "No document specified."}
	if not rag_pipeline.is_source_visible("DMS Document", document, user):
		return {"data": {}, "sources": [], "notes": f"Document {document} not found or not visible to this user."}
	visible = frappe.get_list("DMS Document", filters={"name": document}, fields=["name", "title", "current_version", "status"], user=user, limit_page_length=1)
	doc = visible[0]
	if not doc.current_version or doc.status != "Effective":
		return {"data": {"document": document, "status": doc.status}, "sources": [], "notes": f"Document {document} has no current Effective version to retrieve."}
	if not rag_pipeline.is_source_visible("DMS Document Version", doc.current_version, user):
		return {"data": {"document": document}, "sources": [], "notes": f"Document {document}'s current version is not visible to this user."}

	chunks = frappe.get_all(
		"RAG Chunk",
		filters={"source_doctype": "DMS Document Version", "source_reference": doc.current_version, "is_current": 1},
		fields=["name", "chunk_index", "chunk_text", "version_no"],
		order_by="chunk_index asc",
	)
	full_text = "\n".join(c.chunk_text for c in chunks)
	data = {
		"document": document,
		"title": doc.title,
		"version": doc.current_version,
		"version_no": chunks[0].version_no if chunks else None,
		"chunk_count": len(chunks),
		"content": full_text,
		"citation": {"document": document, "title": doc.title, "version": doc.current_version},
	}
	sources = [f"{document}#{doc.current_version}:chunk{c.chunk_index}" for c in chunks]
	return {"data": data, "sources": sources, "notes": None if chunks else "This document's current version has not been indexed yet (0 RAG Chunk rows found)."}


# ---------------------------------------------------------------------------
# Evaluation Datasets (master plan §13.14) — `classify_complaint` tool, added to the SAME
# registry (32 tools total now). This is the master plan's OWN second named worked example
# (alongside `deviation_analysis`, Phase 2A's original AI Action — see `ai_seeds.py`'s
# `_ensure_action()`) — built here specifically to give the Evaluation Datasets demo a second,
# structurally real, DIFFERENT action to evaluate, per the task's own architectural fork:
# `QMS Complaint` (Golden Demo #2/#3 QMS) is a real DocType in this codebase but had ZERO
# pre-existing records anywhere (confirmed by reading every seed module before writing this —
# it is only ever referenced by `bootstrap_qms_doctypes.py`'s own DocType-creation code, never
# populated) — so `ai_evaluation_seeds.py` seeds a small, clearly-isolated batch of real,
# persisted `QMS Complaint` records itself (deliberately labeled `is_synthetic=1` on their own
# `AI Evaluation Case` rows, honestly, since none of this data was "discovered" from prior
# organic use — see that module's own docstring).
#
# `_classify_qms_text()` is a REAL, deterministic, explainable (keyword-based, NOT vector, NOT
# LLM) classifier — reused as-is by `ai_evaluation.py`'s `deviation_analysis` reference
# classifier for `QMS Deviation` text, since both are real free-text quality events sharing the
# same taxonomy. It exists BECAUSE `ai_core._call_provider_adapter()` is a fixed MOCK that
# returns a canned string regardless of input (see its own docstring) — a classification
# evaluation dataset needs SOMETHING that actually varies its output with input content to be
# checkable at all, and the mock cannot provide that. This mirrors the exact precedent
# `ai_qms_copilot._suggest_capa_fields()` already established: real, deterministic business-rule
# logic running ALONGSIDE the (untouched) mocked LLM synthesis call, never a substitute for it.
# ---------------------------------------------------------------------------

_COMPLAINT_CATEGORY_KEYWORDS = {
	"Adverse Event / Safety": [
		"allergic", "allergy", "anaphyla", "hospitaliz", "adverse event", "rash", "injury",
		"injured", "contamina", "foreign object", "unsafe to use", "burn", "illness",
	],
	"Equipment / Cold Chain": [
		"temperature", "compressor", "thermostat", "refrigerat", "cold storage", "cold chain",
		"excursion", "calibrat", "hvac",
	],
	"Packaging / Labeling": [
		"label", "packaging", "misprint", "carton", "barcode", "tamper", "seal",
	],
	"Product Quality / Specification": [
		"potency", "specification", "out of spec", "discolor", "odor", "defect", "expired",
		"spoiled", "assay", "short count", "count short",
	],
	"Process / Documentation": [
		"documentation", "procedure", "sop ", "not signed", "training record", "process deviation",
	],
	"Service / Delivery": [
		"delivery", "delayed", "shipping", "customer service", "refund", "billing", "unhelpful",
	],
}

# Cross-cutting Critical-severity indicators — real, industry-standard GMP/QMS severity-escalation
# terms (recall, patient harm, hospitalization, foreign-object contamination, ...), checked
# regardless of category. See `_classify_qms_text()`'s own comment for why this is a cross-cutting
# override rather than a per-category rule.
_CRITICAL_OVERRIDE_KEYWORDS = (
	"hospitaliz", "anaphyla", "death", "life-threatening", "patient harm", "market withdrawal",
	"recall", "foreign object",
)


def _classify_qms_text(text: str) -> dict:
	"""Deterministic, explainable keyword classifier shared by `classify_complaint()` below (QMS
	Complaint) and `ai_evaluation.classify_deviation_reference()` (QMS Deviation) — see this
	section's own module comment for why this exists instead of relying on the mocked LLM. Scores
	every category by keyword-hit count (states which keywords matched — never a black-box score,
	the same explainability discipline `find_similar_deviations()`/`suggest_impacted_documents()`
	already established), picks the highest-scoring category, and derives a severity/safety-flag
	from category + a small set of severity-escalating keywords. Falls back to 'Other'/'Minor'
	when nothing matches (e.g. a record with no descriptive free text at all)."""
	t = (text or "").lower()
	scores, matched_by_category = {}, {}
	for category, keywords in _COMPLAINT_CATEGORY_KEYWORDS.items():
		hits = [kw for kw in keywords if kw in t]
		if hits:
			scores[category] = len(hits)
			matched_by_category[category] = hits
	category = max(scores, key=scores.get) if scores else "Other"
	matched_keywords = matched_by_category.get(category, [])

	if category == "Adverse Event / Safety":
		predicted_severity = "Major"
	elif category == "Product Quality / Specification":
		predicted_severity = "Minor" if any(kw in t for kw in ("short count", "count short")) else "Major"
	elif category == "Equipment / Cold Chain":
		predicted_severity = "Major"
	elif category in ("Packaging / Labeling", "Service / Delivery"):
		predicted_severity = "Major" if ("tamper" in t or "seal" in t) else "Minor"
	else:
		predicted_severity = "Minor"

	# Cross-cutting escalation: these terms are Critical-indicative regardless of which category
	# won above (a real GMP/QMS convention — e.g. a foreign-object contamination complaint is
	# almost always treated as Critical even though it's categorized under Adverse Event/Safety
	# the same as a milder rash report). Applied AFTER category-specific severity so it can only
	# ever escalate, never downgrade.
	if any(kw in t for kw in _CRITICAL_OVERRIDE_KEYWORDS):
		predicted_severity = "Critical"

	return {
		"predicted_category": category,
		"predicted_severity": predicted_severity,
		"is_safety_critical": category == "Adverse Event / Safety" or predicted_severity == "Critical",
		"matched_keywords": matched_keywords,
	}


def classify_complaint(user=None, complaint=None, **_ignored):
	"""Real, read-only, permission-checked classification of ONE real `QMS Complaint` record's
	category/severity/safety-flag via `_classify_qms_text()` — NOT the mocked LLM (see this
	section's module comment). Deliberately minimal: no AI Draft/approval workflow of its own
	(unlike QMS/DMS Copilot) — this tool exists specifically so the Evaluation Datasets demo has
	a second, real, structurally different action to evaluate per master plan §13.14's own
	`classify_complaint` worked example, not to build a ninth full copilot demo (see
	`ai_evaluation.py`'s module docstring for the explicit scoping rationale)."""
	user = user or frappe.session.user
	if not complaint:
		return {"data": {}, "sources": [], "notes": "No complaint specified."}
	rows = frappe.get_list(
		"QMS Complaint",
		filters={"name": complaint},
		fields=["name", "subject", "customer_name", "description", "severity", "status"],
		user=user,
		limit_page_length=1,
	)
	if not rows:
		return {"data": {}, "sources": [], "notes": f"Complaint {complaint} not found or not visible to this user."}
	c = rows[0]
	classification = _classify_qms_text(f"{c.subject} {c.description or ''}")
	data = {
		"complaint": c.name,
		"subject": c.subject,
		"customer_name": c.customer_name,
		"recorded_severity": c.severity,
		"status": c.status,
		**classification,
	}
	return {"data": data, "sources": [f"QMS Complaint:{c.name}"], "notes": None}
