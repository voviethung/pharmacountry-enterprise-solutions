"""Phase 6A — Permission-aware RAG seed data + validations. Registers the 2 new `AI Tool` rows
this demo adds to the SAME registry every prior Phase 6A item built (`search_knowledge_base`,
`get_document`), the `permission_aware_rag_synthesis` Prompt Template/AI Action (NO-DRAFT —
`human_review_required=0`, see `ai_permission_aware_rag.py`'s own documented design decision),
and a brand-new, ISOLATED `DMS Document` (`SOP-CAL-01`) with 3 real chronological revisions —
NOT a reuse of Golden Demo #4/AI-DEMO-03's own `SOP-WH-02` (deliberately: AI-DEMO-03's own
`search_effective_documents()` Q&A exclusion proof already depends on SOP-WH-02's exact v1/v2
content pair, and this demo separately needs to trigger a LIVE v2->v3 status transition mid-
validation to prove the re-index-on-change test — reusing SOP-WH-02 for that would risk exactly
the kind of cross-demo collision this session's own lessons warn about, even though the two
demos' actual assertions don't overlap; a dedicated document removes any doubt).

**Why DMS Document/Version alone, not also QMS Audit Finding or LIMS Specification (breadth)**:
the task's own instruction explicitly allows "depth over breadth ... if DMS alone lets you prove
all 5 RAG tests convincingly." DMS Document/Version already has, natively, exactly the version-
lifecycle + Effective/Obsolete status machinery master plan §13.9 demands (version metadata,
obsolete-must-not-be-current, revision-triggers-reindex) — no other doctype in this codebase has
an equivalent real multi-version lifecycle to index against. Adding a second source type would
add real engineering surface (a second `source_doctype` branch in `rag_pipeline.index_document_
version()`, itself DMS Document Version-specific by name) without strengthening any of the 5
named tests, so it was deliberately left out here — flagged, not silently skipped.

**3 real, chronological revisions, each promoted through the SAME real Draft -> Under Review ->
Approved -> Effective lifecycle `dms_seeds.py`'s own SOP-WH-02 uses** (so every one of this
demo's re-index events is a genuine save-triggered hook firing, never a direct RAG Chunk write):
v1 (90-day calibration interval), v2 (60-day interval + SMS alert — created at SEED time, so
`seed_ai_permission_aware_rag()` itself already exercises one real Effective/Obsolete swap), and
v3 (30-day interval + redundant sensor — created LIVE inside `seed_ai_permission_aware_rag_
validations()`'s own `_test_reindex_on_version_change()`, specifically so the re-index test can
capture real before/after RAG Chunk state around one live status-change event, not just inspect
already-settled seed-time data). All 3 revisions deliberately share the SAME core vocabulary
(pressure gauge, calibration, certified reference standard, preventive maintenance, critical
instrumentation, Quality Assurance, GMP-critical process step, tagged out of service) so a query
against the CURRENT revision's subject matter genuinely, demonstrably ALSO matches the two
Obsolete revisions via the same mock embedding — the empirical basis for the 'Obsolete doc not
used as current' proof (mirroring AI-DEMO-03's own cold-storage-logs proof, but via the real
embedding/cosine-similarity path instead of literal keyword overlap).
"""

import frappe

from enterprise_core.enterprise_core import rag_pipeline
from enterprise_core.enterprise_core.ai_permission_aware_rag import (
	QUESTION_TOOL_MAP,
	ask_knowledge_base,
	get_document_content,
)

_DOC_CODE = "SOP-CAL-01"
_DOC_TITLE = "Pressure Gauge Calibration & Preventive Maintenance"
_DOC_DEPARTMENT = "Metrology"

_AUTHORIZED_USER = "qa.manager@pharmacountry.vn"  # real Quality Manager role -> CAN read DMS Document/Version
_REVIEWER = "quality.director@pharmacountry.vn"
# A real, pre-existing portal user (Golden Demo #24 / 3PL) whose ONLY role is "Stock User" —
# confirmed by reading threepl_seeds.py's own _ensure_client_users() — which is NOT one of DMS
# Document/DMS Document Version's 2 permission-holding roles (System Manager, Quality Manager).
# Reused deliberately rather than creating a new fixture: this is the SAME real user AI-DEMO-01's
# own `get_batches_on_hold()` proof already established as this codebase's standard "genuinely
# has zero relevant permission" negative-control identity.
_UNAUTHORIZED_USER = "client.a.3pl@pharmacountry.vn"

_V1_CONTENT = (
	"Calibrate the pressure gauge on Tank 3 every 90 days using a certified reference standard "
	"traceable to national metrology standards. Preventive maintenance for critical instrumentation "
	"shall be scheduled at the same 90 day interval. Any deviation found during calibration must be "
	"logged in the equipment maintenance record and escalated to the Quality Assurance team "
	"immediately.\n\n"
	"Operators must verify the calibration sticker date before using any pressure gauge in a "
	"GMP-critical process step. A gauge past its calibration due date must be removed from service "
	"and tagged out of service until recalibrated."
)

_V2_CONTENT = (
	"Calibrate the pressure gauge on Tank 3 every 60 days using a certified reference standard "
	"traceable to national metrology standards, per the revised metrology audit findings. "
	"Preventive maintenance for critical instrumentation shall now be scheduled at the same 60 day "
	"interval, with an automated SMS alert sent to the Metrology team five days before the due date. "
	"Any deviation found during calibration must be logged in the equipment maintenance record and "
	"escalated to the Quality Assurance team immediately.\n\n"
	"Operators must verify the calibration sticker date before using any pressure gauge in a "
	"GMP-critical process step. A gauge past its calibration due date must be removed from service "
	"and tagged out of service until recalibrated, and the redundant backup gauge must be installed "
	"within one hour."
)

_V3_CONTENT = (
	"Calibrate the pressure gauge on Tank 3 every 30 days using a certified reference standard "
	"traceable to national metrology standards, per the latest metrology audit findings and a "
	"recent near-miss deviation. Preventive maintenance for critical instrumentation shall now be "
	"scheduled at the same 30 day interval, with an automated SMS alert sent to the Metrology team "
	"five days before the due date, and a redundant sensor is now required on Tank 3 at all times. "
	"Any deviation found during calibration must be logged in the equipment maintenance record and "
	"escalated to the Quality Assurance team immediately.\n\n"
	"Operators must verify the calibration sticker date before using any pressure gauge in a "
	"GMP-critical process step. A gauge past its calibration due date must be removed from service "
	"and tagged out of service until recalibrated, and the redundant backup gauge must be installed "
	"within one hour."
)

_RAG_QUERY = "pressure gauge calibration interval"


# ---------------------------------------------------------------------------
# AI Tool registry additions (2 tools, appended to the existing shared registry)
# ---------------------------------------------------------------------------

_AI_TOOLS = [
	(
		"search_knowledge_base",
		"Search Knowledge Base (Permission-aware RAG)",
		"Real embedding-based (MOCK embedding, real vector math) semantic search over the RAG Chunk index, permission-filtered per source record and restricted to is_current=1 chunks only.",
		"enterprise_core.enterprise_core.ai_tools.search_knowledge_base",
		"DMS Document Version",
	),
	(
		"get_document",
		"Get Document (Permission-aware RAG)",
		"Direct, permission-checked fetch of one named DMS Document's current Effective content, reassembled from its own indexed RAG Chunk rows — the master plan's own canonical 'get_document' tool.",
		"enterprise_core.enterprise_core.ai_tools.get_document",
		"DMS Document",
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
	if frappe.db.exists("Prompt Template", {"template_code": "permission_aware_rag_synthesis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "permission_aware_rag_synthesis",
			"version": 1,
			"system_instruction": (
				"You are an enterprise knowledge assistant answering a question strictly from REAL, "
				"tool-retrieved chunks of approved, CURRENT (Effective) controlled documents that the "
				"asking user has been independently confirmed to have real permission to read. Never "
				"invent facts beyond the retrieved chunks, never fetch additional data yourself, never "
				"run or suggest SQL, and never treat an Obsolete or Draft document version as current "
				"knowledge. Every answer must be traceable to the real source document/version/chunk "
				"citations provided as context — cite them, never present the answer as if it had no "
				"source."
			),
			"input_schema": frappe.as_json({"question_code": "string", "search_knowledge_base|get_document": "object (real retrieved, permission-filtered, citation-bearing chunk data)"}),
			"output_schema": frappe.as_json({"answer": "string — grounded strictly in the retrieved, cited chunks"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", "permission_aware_rag_synthesis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "permission_aware_rag_synthesis",
			"description": "Permission-aware RAG — synthesizes an answer strictly from real, permission-filtered, currency-filtered, citation-bearing retrieved chunks. Read-only Q&A/retrieval, NO-DRAFT (never attached to or mistaken for a human-authored record — see ai_permission_aware_rag.py's own module docstring).",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "permission_aware_rag_synthesis", "version": 1}, "name"),
			"allowed_tools": ",".join(code for code, *_ in _AI_TOOLS),
			"human_review_required": 0,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Isolated demo Document + 2 real seed-time revisions (v3 is created live, in validations).
# ---------------------------------------------------------------------------

def _ensure_document():
	if frappe.db.exists("DMS Document", _DOC_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "DMS Document",
			"document_code": _DOC_CODE,
			"title": _DOC_TITLE,
			"doc_type": "SOP",
			"department": _DOC_DEPARTMENT,
			"status": "Draft",
			"requires_training": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _promote_version(version_no, content):
	"""Creates (if missing) `DMS Document Version` `version_no` with `content` and walks it
	through the SAME real Draft -> Under Review -> Approved -> Effective lifecycle `dms_seeds.py`'s
	own `_ensure_version_1_effective()`/`_ensure_version_2_revision()` use. Each `.save()` call
	genuinely fires BOTH `dms_validations.dms_document_version_on_update()` (D02/D04 — supersedes
	the prior Effective sibling) AND this build's own additive `rag_pipeline.reindex_document_
	version_on_update()` hook — so every promotion here is a REAL save-triggered re-index event,
	never a manual/direct RAG Chunk write. Idempotent: returns the existing version untouched (no
	re-save, no hook re-fire) if it already exists."""
	existing = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": version_no}, "name")
	if existing:
		return existing, False
	v = frappe.get_doc(
		{
			"doctype": "DMS Document Version",
			"document": _DOC_CODE,
			"version_no": version_no,
			"status": "Draft",
			"content_summary": content,
		}
	)
	v.insert(ignore_permissions=True)
	v.status = "Under Review"
	v.reviewed_by = _AUTHORIZED_USER
	v.save(ignore_permissions=True)
	v.status = "Approved"
	v.approved_by = _REVIEWER
	v.save(ignore_permissions=True)
	v.status = "Effective"
	v.effective_date = frappe.utils.nowdate()
	v.save(ignore_permissions=True)
	return v.name, True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_permission_aware_rag():
	"""Phase 6A — Permission-aware RAG. Registers the 2 new AI Tools, the permission_aware_rag_
	synthesis Prompt Template + AI Action (reusing the existing, unmodified CE-13 AI foundation
	router/policy/logging), the isolated SOP-CAL-01 document with its v1->v2 real revision (v3 is
	created live inside validations — see module docstring), and defensively backfills the RAG
	index for every DMS Document Version that already existed BEFORE this Phase 6A item's hook was
	registered (Golden Demo #4's own SOP-WH-02, whose versions were saved by earlier seed runs)."""
	tools_created = _ensure_ai_tools()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	doc_created = _ensure_document()
	v1_name, v1_created = _promote_version(1, _V1_CONTENT)
	v2_name, v2_created = _promote_version(2, _V2_CONTENT)
	backfill = rag_pipeline.reindex_all_effective_documents()
	return (
		f"seed_ai_permission_aware_rag: AI Tools created: {tools_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"Document {_DOC_CODE} {'created' if doc_created else 'already existed'}. "
		f"v1 {'promoted to Effective' if v1_created else 'already existed'} ({v1_name}). "
		f"v2 {'promoted to Effective' if v2_created else 'already existed'} ({v2_name}), which "
		f"real-hook-flipped v1 to Obsolete. Corpus backfill: {backfill['versions_indexed']} version(s) "
		f"indexed, {backfill['total_chunks']} total chunk(s), {backfill['current_chunks']} current."
	)


# ---------------------------------------------------------------------------
# Validations — the 5 RAG tests from master plan §19F, each proven empirically.
# ---------------------------------------------------------------------------

def _test_reindex_on_version_change():
	"""RAG test #4 — 'Version update triggers re-index'. Captures live before-state (v2's chunks
	are the CURRENT ones), triggers a REAL status-change event (v3 promoted to Effective via the
	same lifecycle every other version here uses — a genuine `.save()`, never a manual RAG Chunk
	write), then re-queries RAG Chunk directly to prove the index actually changed: v2's chunks
	flip to is_current=0/Obsolete, v3's chunks appear as is_current=1/Effective — with NO manual
	`index_document_version()` call anywhere in this function. Safe to re-run (idempotent): once
	v3 already exists, `_promote_version()` is a no-op and this function simply re-confirms the
	same already-settled invariant holds."""
	v2_name = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 2}, "name")
	if not v2_name:
		frappe.throw("_test_reindex_on_version_change: v2 not found — run seed_ai_permission_aware_rag() first.")
	v3_already_existed = frappe.db.exists("DMS Document Version", {"document": _DOC_CODE, "version_no": 3})
	if not v3_already_existed:
		before_v2_chunks = frappe.get_all("RAG Chunk", filters={"source_reference": v2_name}, fields=["is_current"])
		if not before_v2_chunks or not all(c.is_current for c in before_v2_chunks):
			frappe.throw(f"_test_reindex_on_version_change: setup problem — v2's chunks should ALL be is_current=1 before v3 is promoted. Got: {before_v2_chunks}")

	v3_name, v3_created = _promote_version(3, _V3_CONTENT)  # the real trigger event

	v2_chunks_after = frappe.get_all("RAG Chunk", filters={"source_reference": v2_name}, fields=["is_current", "source_status"])
	v3_chunks_after = frappe.get_all("RAG Chunk", filters={"source_reference": v3_name}, fields=["is_current", "source_status"])
	if not v2_chunks_after or any(c.is_current for c in v2_chunks_after):
		frappe.throw(f"RAG test #4 FAILED: v2's chunks should ALL be is_current=0 (Obsolete) after v3 went Effective. Got: {v2_chunks_after}")
	if any(c.source_status != "Obsolete" for c in v2_chunks_after):
		frappe.throw(f"RAG test #4 FAILED: v2's chunks' source_status should be 'Obsolete' after re-index. Got: {v2_chunks_after}")
	if not v3_chunks_after or not all(c.is_current for c in v3_chunks_after):
		frappe.throw(f"RAG test #4 FAILED: v3's chunks should ALL be is_current=1 (Effective) immediately after promotion, with NO manual reindex call. Got: {v3_chunks_after}")

	return (
		f"RAG test #4 (version update triggers re-index) CONFIRMED: promoting v3 ({v3_name}, "
		f"created={v3_created}) via a real .save() automatically flipped v2's {len(v2_chunks_after)} "
		f"chunk(s) to Obsolete/is_current=0 and indexed v3's {len(v3_chunks_after)} chunk(s) as "
		f"Effective/is_current=1 — via the real hooks.py on_update hook, no manual reindex call."
	)


def _test_effective_doc_retrieved():
	"""RAG test #1 — 'Effective doc retrieved'. get_document_content() returns SOP-CAL-01's real
	CURRENT (v3) content — the 30-day interval revision — not a stale/older one."""
	resp = get_document_content(_DOC_CODE, user=_AUTHORIZED_USER)
	data = resp["data_facts"]["get_document"]
	v3_name = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 3}, "name")
	if data.get("version") != v3_name:
		frappe.throw(f"RAG test #1 FAILED: expected current Effective version {v3_name}, got {data.get('version')!r}.")
	if "30 day" not in data.get("content", ""):
		frappe.throw(f"RAG test #1 FAILED: retrieved content does not reflect the latest Effective revision (30-day interval). Got: {data.get('content')!r}")
	if data.get("chunk_count", 0) < 2:
		frappe.throw(f"RAG test #1 FAILED: expected multiple real chunks (chunking pipeline proof), got chunk_count={data.get('chunk_count')}.")
	return f"RAG test #1 (Effective doc retrieved) CONFIRMED: get_document_content({_DOC_CODE}) returned the real current version {v3_name} ({data['chunk_count']} chunks, 30-day interval content)."


def _test_obsolete_not_used_as_current():
	"""RAG test #2 — 'Obsolete doc not used as current'. Both v1 and v2 (now BOTH Obsolete after
	v3's promotion) share the same core vocabulary as v3 and DO score a real, non-zero cosine
	similarity against the query (proven directly against their stored embeddings, bypassing the
	is_current filter) — proving the exclusion is real filtering, not a lucky non-match — yet
	NEITHER ever appears in search_knowledge_base()'s actual results, only v3 (current) does."""
	resp = ask_knowledge_base(_RAG_QUERY, user=_AUTHORIZED_USER, top_k=10)
	results = resp["data_facts"]["search_knowledge_base"]["results"]
	result_versions = {r["version"] for r in results}
	v3_name = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": 3}, "name")
	if v3_name not in result_versions:
		frappe.throw(f"RAG test #2 setup FAILED: current v3 ({v3_name}) not found in results: {result_versions}")

	query_vector = rag_pipeline.mock_embed(_RAG_QUERY)
	for version_no in (1, 2):
		v_name = frappe.db.get_value("DMS Document Version", {"document": _DOC_CODE, "version_no": version_no}, "name")
		v_status = frappe.db.get_value("DMS Document Version", v_name, "status")
		if v_status != "Obsolete":
			frappe.throw(f"RAG test #2 setup FAILED: v{version_no} ({v_name}) should be Obsolete by now, is {v_status!r}.")
		if v_name in result_versions:
			frappe.throw(f"RAG test #2 FAILED: Obsolete v{version_no} ({v_name}) was incorrectly returned as current knowledge. Results: {result_versions}")
		chunks = frappe.get_all("RAG Chunk", filters={"source_reference": v_name}, fields=["embedding"])
		similarities = [rag_pipeline.cosine_similarity(query_vector, frappe.parse_json(c.embedding)) for c in chunks]
		if not any(s > 0 for s in similarities):
			frappe.throw(f"RAG test #2 setup FAILED: Obsolete v{version_no}'s chunks don't even match the query vocabulary (similarities={similarities}) — cannot prove the exclusion is doing real work, not just a non-match.")

	return (
		f"RAG test #2 (obsolete doc not used as current) CONFIRMED: query {_RAG_QUERY!r} genuinely "
		f"matches BOTH Obsolete v1/v2 (real, non-zero cosine similarity against their stored "
		f"embeddings) AND current v3 — only v3 ({v3_name}) is ever returned by search_knowledge_base(), "
		f"v1/v2 are excluded purely by the is_current=1 filter, never by chance non-match."
	)


def _test_permission_denied_user_cannot_retrieve():
	"""RAG test #3 — 'User without permission cannot retrieve'. Same query, 2 real, differently-
	permissioned users: qa.manager@pharmacountry.vn (real Quality Manager role -> CAN read DMS
	Document/Version) gets real results; client.a.3pl@... (real Stock User role only, Golden
	Demo #24's own portal user, no DMS permission at all) gets ZERO — and the zero is explained by
	permission_denied_source_count > 0 (proving the source WAS scored and matched, then correctly
	excluded by a real per-user frappe.get_list(..., user=...) permission check), not by a
	coincidental non-match."""
	authorized = ask_knowledge_base(_RAG_QUERY, user=_AUTHORIZED_USER)
	denied = ask_knowledge_base(_RAG_QUERY, user=_UNAUTHORIZED_USER)
	auth_data = authorized["data_facts"]["search_knowledge_base"]
	denied_data = denied["data_facts"]["search_knowledge_base"]
	if auth_data["count"] == 0:
		frappe.throw("RAG test #3 setup FAILED: the authorized user got 0 results — cannot prove a permission DIFFERENCE without a genuine positive case.")
	if denied_data["count"] != 0:
		frappe.throw(f"RAG test #3 FAILED: the unauthorized user ({_UNAUTHORIZED_USER}) unexpectedly got results: {denied_data['results']}")
	if denied_data["permission_denied_source_count"] == 0:
		frappe.throw("RAG test #3 FAILED: the unauthorized user's 0 results should be explained by permission_denied_source_count > 0 (proving real permission filtering fired), got 0.")
	return (
		f"RAG test #3 (user without permission cannot retrieve) CONFIRMED: {_AUTHORIZED_USER} "
		f"(real Quality Manager role) got {auth_data['count']} result(s); {_UNAUTHORIZED_USER} "
		f"(real Stock User role only, zero DMS permission) got 0 results, with "
		f"permission_denied_source_count={denied_data['permission_denied_source_count']} confirming "
		f"the source(s) WERE matched then correctly excluded by a real per-user permission check."
	)


def _test_citations_correct():
	"""RAG test #5 — 'Source citations correct'. Every citation search_knowledge_base()/
	get_document_content() returns is cross-checked against the REAL live DocType records it
	claims to cite (document/version/version_no) — never a fabricated or mismatched reference."""
	resp = ask_knowledge_base(_RAG_QUERY, user=_AUTHORIZED_USER)
	citations = resp["citations"]
	if not citations:
		frappe.throw("RAG test #5 FAILED: ask_knowledge_base() returned no citations at all.")
	for c in citations:
		real = frappe.db.get_value("DMS Document Version", c["version"], ["document", "version_no"], as_dict=True)
		if not real or real.document != c["document"] or real.version_no != c["version_no"]:
			frappe.throw(f"RAG test #5 FAILED: citation {c} does not match the real DMS Document Version record {real}.")

	doc_resp = get_document_content(_DOC_CODE, user=_AUTHORIZED_USER)
	doc_citation = doc_resp["citations"][0] if doc_resp.get("citations") else None
	real_doc = frappe.db.get_value("DMS Document", _DOC_CODE, ["title", "current_version"], as_dict=True)
	if not doc_citation or doc_citation.get("version") != real_doc.current_version or doc_citation.get("title") != real_doc.title:
		frappe.throw(f"RAG test #5 FAILED: get_document_content() citation {doc_citation} does not match the real DMS Document record {real_doc}.")

	return f"RAG test #5 (source citations correct) CONFIRMED: {len(citations)} search citation(s) and 1 get_document citation all cross-checked against real, live DocType records."


def _test_idempotent_reindex():
	"""Not one of the 5 named RAG tests, but required by this build's own workflow: re-running the
	bulk indexer must never duplicate chunk rows."""
	before = frappe.db.count("RAG Chunk", {"document_code": _DOC_CODE})
	rag_pipeline.reindex_all_effective_documents()
	rag_pipeline.reindex_all_effective_documents()
	after = frappe.db.count("RAG Chunk", {"document_code": _DOC_CODE})
	if before != after:
		frappe.throw(f"Idempotency FAILED: RAG Chunk count for {_DOC_CODE} changed from {before} to {after} after re-running the bulk indexer twice.")
	return f"Idempotency CONFIRMED: RAG Chunk count for {_DOC_CODE} stayed at {after} across 2 extra re-index passes."


def _test_use_cases_no_draft_shape():
	"""Structural proof this demo's own documented design decision actually holds: neither use
	case's response contains an ai_suggestion/draft field anywhere, and both call through the
	fixed registry mapping (no arbitrary tool/SQL execution)."""
	responses = {
		"ask_knowledge_base": ask_knowledge_base(_RAG_QUERY, user=_AUTHORIZED_USER),
		"get_document_content": get_document_content(_DOC_CODE, user=_AUTHORIZED_USER),
	}
	for question_code, resp in responses.items():
		expected_tools = QUESTION_TOOL_MAP[question_code]
		if resp["tools_called"] != expected_tools:
			frappe.throw(f"'{question_code}': tools_called={resp['tools_called']}, expected {expected_tools}.")
		if "ai_suggestion" in resp:
			frappe.throw(f"NO-DRAFT shape FAILED for '{question_code}': found an ai_suggestion field, expected none.")
		if not resp.get("job_log") or not frappe.db.exists("AI Job Log", resp["job_log"]):
			frappe.throw(f"'{question_code}': no AI Job Log entry written.")
	return "NO-DRAFT shape CONFIRMED: neither use case's response carries an ai_suggestion/draft field; both call the fixed registry mapping and write a real AI Job Log entry."


def seed_ai_permission_aware_rag_validations():
	"""Runs all 5 named RAG tests (master plan §19F) plus the NO-DRAFT shape proof and the
	idempotency proof, in an order where later checks can depend on earlier ones' real side
	effects (the re-index test's live v3 promotion must run before the effective/obsolete/
	citation checks that assume v3 is already the current version)."""
	shape = _test_use_cases_no_draft_shape()
	reindex = _test_reindex_on_version_change()
	effective = _test_effective_doc_retrieved()
	obsolete = _test_obsolete_not_used_as_current()
	permission = _test_permission_denied_user_cannot_retrieve()
	citations = _test_citations_correct()
	idempotent = _test_idempotent_reindex()
	return f"seed_ai_permission_aware_rag_validations: {shape} {reindex} {effective} {obsolete} {permission} {citations} {idempotent}"
