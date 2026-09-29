"""Phase 6A — Permission-aware RAG (master plan §13.9 "RAG / Enterprise Knowledge", lines
~1231-1264; RAG test list §19F lines ~3304-3310), the eighth Phase 6A item, built directly on top
of AI-DEMO-01/02/03/05/06/09/10's shared infrastructure — the SAME `AI Tool` registry, the SAME
`ai_core.run_ai_action()` mock synthesis call. `rag_pipeline.py` is this build's own genuinely new
contribution (chunking + MOCK embedding + vector index + re-indexing — see its module docstring);
this module is the orchestration layer, mirroring `ask_manufacturing_insight()`'s shape exactly.

**Design decision, documented here rather than made silently: this demo follows AI-DEMO-01/05/
09/10's NO-DRAFT shape, NOT AI-DEMO-02/03/06's `AI Draft`/human-approval shape.** Both of this
demo's use cases (`ask_knowledge_base` — free-text semantic Q&A over the indexed corpus, and
`get_document_content` — a direct named-document fetch) are READ-ONLY retrieval-plus-synthesis
answered straight back to the asking user; neither authors interpretive text that gets attached
to, or could be mistaken for, a human-authored entry on another real business record — the exact
same structural distinction Manufacturing Insight's own docstring drew ("Insight," not "Copilot").
This is also explicitly foreshadowed by AI-DEMO-03's own module docstring, which named THIS demo
by description when explaining why `qa_effective_documents` was deliberately NOT built as a
vector/embedding tool: "Q&A over effective documents is NOT anchored to one authored record" —
the same reasoning applies here, one level more so, since this demo's whole point is retrieval,
not drafting a suggestion for someone else's record.

**What stands in for "human review" here, since there is no approval step**: master plan §13.9's
own mandatory list gives this demo a DIFFERENT, built-in safeguard instead of an approval
workflow — "Source citation trong UI" (source citation in the UI). Every answer this module
returns carries real, structured `citations` (document code/title/version/chunk position) the
asking human can independently verify against the real source record themselves, at read time,
rather than requiring a SEPARATE reviewer to approve the text before anyone sees it. This is a
different but equally real safeguard, not an absence of one — documented here as this build's own
interpretive choice, exactly like AI-DEMO-03 documented its own "why all 5 use cases require
approval" choice.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action

_RAG_ACTION_CODE = "permission_aware_rag_synthesis"

# Fixed use_case -> AI Tool mapping — same "no free-text NLP tool selection, no arbitrary SQL"
# posture as every other Phase 6A copilot/insight module in this codebase.
QUESTION_TOOL_MAP = {
	"ask_knowledge_base": ["search_knowledge_base"],
	"get_document_content": ["get_document"],
}


def _run_rag(question_code: str, user: str | None = None, **params) -> dict:
	"""Shared orchestration for both use cases — resolves question_code -> the registered AI Tool
	from the SAME `AI Tool` registry every prior Phase 6A item built, executes it AS `user` (real
	permission enforcement lives inside the tool itself — see `ai_tools.search_knowledge_base()`/
	`get_document()`), and hands the real, already permission-filtered + citation-bearing tool
	output to the EXISTING, unmodified `run_ai_action()` mock synthesis call. Response shape is
	structurally IDENTICAL to `ask_manufacturing_insight()`'s NO-DRAFT shape (`data_facts`/
	`ai_interpretation`/`citations`/`sources`/`tools_called`/...) — no `ai_suggestion`/draft field
	anywhere, by the documented design decision above."""
	user = user or frappe.session.user
	if question_code not in QUESTION_TOOL_MAP:
		frappe.throw(f"Permission-aware RAG: unknown question_code '{question_code}'. Known: {sorted(QUESTION_TOOL_MAP)}.")

	tool_code = QUESTION_TOOL_MAP[question_code][0]
	if not frappe.db.exists("AI Tool", tool_code):
		frappe.throw(f"Permission-aware RAG: AI Tool '{tool_code}' is not registered.")
	tool = frappe.get_doc("AI Tool", tool_code)
	if not tool.enabled:
		frappe.throw(f"Permission-aware RAG: AI Tool '{tool_code}' is disabled by the Tool Registry.")
	fn = frappe.get_attr(tool.python_function_path)
	result = fn(user=user, **params)

	data_facts = {tool_code: result["data"]}
	sources = result.get("sources") or []
	citations = result["data"].get("citations")
	if citations is None and result["data"].get("citation"):
		citations = [result["data"]["citation"]]
	citations = citations or []

	ai_result = run_ai_action(
		_RAG_ACTION_CODE,
		context={"question_code": question_code, **data_facts},
		user=user,
		tool_calls=[tool_code],
		retrieved_sources=sources,
	)

	return {
		"question_code": question_code,
		"data_facts": data_facts,
		"ai_interpretation": ai_result["output"],
		# Structured citation data — master plan §13.9 "Source citation trong UI" — kept
		# structurally separate from the mock synthesis text, never blended into free prose.
		"citations": citations,
		"sources": sources,
		"tool_notes": {tool_code: result["notes"]} if result.get("notes") else {},
		"tools_called": [tool_code],
		"provider": ai_result["provider"],
		"model": ai_result["model"],
		"fallback_used": ai_result["fallback_used"],
		"job_log": ai_result["job_log"],
	}


def ask_knowledge_base(query: str, user: str | None = None, top_k: int = 5) -> dict:
	"""Free-text permission-aware semantic search over the indexed, permission- and currency-
	filtered knowledge base — RAG test 'Effective doc retrieved' / 'Obsolete doc not used as
	current' / 'User without permission cannot retrieve' / 'Source citations correct' are all
	provable directly from this one entry point's real response."""
	return _run_rag("ask_knowledge_base", user=user, query=query, top_k=top_k)


def get_document_content(document: str, user: str | None = None) -> dict:
	"""Direct named-document fetch via the same permission-checked, citation-bearing index path
	as `ask_knowledge_base()` (backs the `get_document` canonical tool, master plan §13.10)."""
	return _run_rag("get_document_content", user=user, document=document)
