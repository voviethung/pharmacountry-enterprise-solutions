"""Phase 6A — Permission-aware RAG (master plan §13.9 "RAG / Enterprise Knowledge", lines
~1231-1264; RAG test list §19F lines ~3304-3310). The eighth Phase 6A build, and the first one
to build genuinely new INDEXING infrastructure rather than just query tools over existing data.

This module is the pipeline's real, working backbone — everything master plan §13.9 asks for
EXCEPT the two pieces this platform's AI layer has been deliberately mock-only for since Phase
2A (`ai_core._call_provider_adapter()`'s own docstring): a live LLM call, and now also a live
embedding-model call. The mandated pipeline shape is:

    Approved content -> extract -> normalize -> chunk -> embedding -> vector index -> retrieval
    -> permission filter -> LLM answer

Mapped onto this module + `ai_tools.search_knowledge_base()`/`ai_tools.get_document()` +
`ai_permission_aware_rag.py`:
  - extract/normalize: `index_document_version()` reads the real `content_summary` field off a
    real `DMS Document Version` (Golden Demo #4/AI-DEMO-03's same source data — no separate
    "approved content" store exists in this codebase, and DMS Document/Version IS exactly the
    "SOP/Specification/Policy" source category master plan §13.9's own "Nguồn dữ liệu" list
    names first).
  - chunk: `chunk_text()` — a real, simple paragraph-then-fixed-word-count splitter over that
    real text. Not a placeholder: it genuinely produces >1 chunk for multi-sentence content and
    is exercised end-to-end by this build's own seed data (see `ai_permission_aware_rag_seeds.py`).
  - embedding: `mock_embed()` — see its own docstring for the full, honest MOCK disclosure. This
    is the ONE deliberately-simulated step, by explicit instruction (no real embedding API/model/
    credentials/network call is permitted in this demo platform, exactly like no real LLM call
    is). Everything around it — chunking, indexing, similarity math, permission filtering,
    obsolete exclusion, re-indexing-on-change — is genuinely real, not simulated.
  - vector index: the `RAG Chunk` DocType (see its own JSON docstring fields) — a real Frappe
    table, not an in-memory structure, so it survives restarts and is genuinely re-queryable.
  - retrieval: `ai_tools.search_knowledge_base()`'s cosine-similarity scan over `RAG Chunk` rows
    filtered to `is_current=1`.
  - permission filter: applied INSIDE `search_knowledge_base()`/`get_document()` (not here) via
    `frappe.get_list(source_doctype, ..., user=user)` on each candidate chunk's own source
    record — this session's own established "get_list(), never get_all(), for anything
    permission-sensitive" idiom, applied per-chunk so a user's access is checked against the REAL
    source record, not against `RAG Chunk` itself (see module docstring note below on why RAG
    Chunk's own DocType permission is deliberately System-Manager-only and is NOT the access-
    control mechanism).
  - LLM answer: `ai_permission_aware_rag.py` hands the permission-filtered, citation-bearing
    chunks to the EXISTING, unmodified `ai_core.run_ai_action()` mock synthesis call — the same
    "real data in, mocked synthesis out" shape every other Phase 6A demo already uses.

**Why `RAG Chunk`'s own DocType permission is System-Manager-only, and that is NOT a bug**: a
single flat DocType-level permission list cannot correctly express "a user may read this row IFF
they can read ITS SOURCE record" when different chunks can (in a future extension) come from
different source DocTypes with different permission rules. So access control is enforced in
application code — `search_knowledge_base()`/`get_document()` read `RAG Chunk` broadly via
`frappe.get_all()` (safe here specifically because it is immediately followed by an explicit,
mandatory `frappe.get_list(source_doctype, filters={"name": source_reference}, user=user)` check
against the REAL source record before any chunk's text is ever returned to a caller — this is a
deliberate two-step design, not the silent, undocumented bypass this session's own lessons warn
against elsewhere) — see those two functions' own docstrings in `ai_tools.py` for the concrete
proof this is empirically exercised with two differently-permissioned real users.

**Why re-indexing is wired via an ADDITIONAL `hooks.py` doc_events entry, not by editing
`dms_validations.py`**: `dms_validations.dms_document_version_on_update()` (Golden Demo #4's own
D02/D04 logic) already flips a superseded Effective version to Obsolete via a real `.save()`
call, and `hooks.py` doc_events supports a LIST of handlers per event — so `reindex_document_
version_on_update()` below is registered as a SECOND, purely-additive entry for `DMS Document
Version`'s `on_update` event, run unconditionally (not gated on `doc.status == "Effective"`)
so that EVERY revision/status transition (Draft, Approved, Effective, and the automatic Obsolete
flip of a superseded sibling) re-indexes immediately. Because the sibling's own `.save()` inside
`dms_validations`' handler independently re-triggers this SAME hook list for the sibling, BOTH
sides of an Effective/Obsolete swap are re-indexed from ONE real user action (promoting a new
version) with no direct code dependency on `dms_validations`' internals — this is what makes RAG
test #4 ("version update triggers re-index") a real, live event rather than a manual/batch step.
"""

import hashlib
import math
import re

import frappe

# A MOCK embedding is intentionally low-dimensional and simple — see mock_embed()'s own
# docstring. 64 buckets is plenty to give genuinely different short SOP paragraphs distinct,
# comparable vectors without pretending to be a real semantic embedding space.
_EMBEDDING_DIMS = 64

# Fixed-size word-count chunking, applied within each paragraph — deliberately simple/explainable
# (this is the "chunk" pipeline step being proven architecturally, not a production chunking
# strategy). A short one-paragraph content_summary correctly yields exactly 1 chunk; a longer,
# multi-sentence SOP paragraph yields several, in stable chunk_index order.
_WORDS_PER_CHUNK = 22


def chunk_text(text: str, words_per_chunk: int = _WORDS_PER_CHUNK) -> list[str]:
	"""Real text chunking (master plan §13.9 pipeline step 3, "chunk") over REAL document content
	— paragraphs first (split on blank lines, the real structure a human author would use), then
	each paragraph further split into fixed `words_per_chunk`-word pieces so no single chunk grows
	unbounded. Returns an ORDERED list — callers persist `chunk_index` as this list's own index,
	never re-derived later, so re-indexing always reproduces the same chunk boundaries for
	unchanged text (needed for the idempotency proof: re-running the indexer without a real
	content change must not grow or reorder chunks)."""
	text = (text or "").strip()
	if not text:
		return []
	paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
	if not paragraphs:
		paragraphs = [text]
	chunks: list[str] = []
	for paragraph in paragraphs:
		words = paragraph.split()
		if not words:
			continue
		for i in range(0, len(words), words_per_chunk):
			chunk = " ".join(words[i : i + words_per_chunk])
			if chunk:
				chunks.append(chunk)
	return chunks


def mock_embed(text: str, dims: int = _EMBEDDING_DIMS) -> list[float]:
	"""**MOCK embedding function** — explicitly, honestly a simulation, exactly like
	`ai_core._call_provider_adapter()` is an honest, clearly-labeled MOCK LLM call. This platform
	makes NO real embedding-provider API call (no OpenAI/Cohere/sentence-transformers, no network
	call, no ML library dependency) — per this build's own hard architectural constraint, a real
	embedding model was deliberately NOT wired in, matching how no real LLM is wired in anywhere
	else in this codebase.

	What it actually computes, in plain deterministic Python: lowercased alphanumeric word tokens
	are hashed (SHA-256, so the mapping is stable across process restarts — a plain `hash()` in
	Python is salted per-process and would NOT be) into one of `dims` fixed buckets, each
	occurrence incrementing that bucket's count (a hashed bag-of-words TERM-FREQUENCY vector, the
	"hashing trick" a real embedding pipeline's own feature-hashing stage sometimes also uses,
	minus any learned semantic structure), then L2-normalized so cosine similarity between two
	such vectors is a meaningful, bounded [-1, 1] measure and — because both vectors are already
	unit-length — a plain dot product IS the cosine similarity (see `cosine_similarity()` below).

	Deterministic by design: the SAME text always embeds to the SAME vector. This is a genuine,
	load-bearing property this build's re-indexing/idempotency tests rely on — but it is not
	itself a shortcut unique to being a mock: a real embedding model at a fixed model version is
	also deterministic for the same input. What this function does NOT do, and a real embedding
	model would: capture synonymy/semantic meaning beyond shared surface tokens. Two chunks
	that discuss the same concept in entirely different words would NOT score similar here — this
	is the one honestly-simulated step in an otherwise real pipeline, per this build's explicit
	instruction not to add a real embedding dependency."""
	vector = [0.0] * dims
	tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
	for token in tokens:
		bucket = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % dims
		vector[bucket] += 1.0
	norm = math.sqrt(sum(v * v for v in vector))
	if norm > 0:
		vector = [v / norm for v in vector]
	return vector


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
	"""Plain-Python cosine similarity — no numpy dependency (checked: not a hard requirement of
	this environment, and this vector size/row count needs none). Both `mock_embed()` outputs are
	already L2-normalized, so this reduces to a dot product, but the function is written generally
	(re-normalizing defensively) so it is correct even if ever called with a non-normalized
	vector."""
	if not vector_a or not vector_b or len(vector_a) != len(vector_b):
		return 0.0
	dot = sum(a * b for a, b in zip(vector_a, vector_b))
	norm_a = math.sqrt(sum(a * a for a in vector_a))
	norm_b = math.sqrt(sum(b * b for b in vector_b))
	if norm_a == 0 or norm_b == 0:
		return 0.0
	return dot / (norm_a * norm_b)


def index_document_version(version_name: str) -> dict:
	"""Real (re)indexing of ONE `DMS Document Version` into `RAG Chunk` rows — the "vector index"
	pipeline step, made idempotent and re-index-safe: every call DELETES this version's existing
	chunks first, then re-chunks/re-embeds/re-inserts from the version's CURRENT `content_summary`
	and CURRENT effective/obsolete status. This is what makes re-running the indexer safe (no
	duplicate/growing chunk rows across repeated calls — proven by this build's own idempotency
	test) AND what makes it a genuine re-index rather than an append-only log (calling this again
	after the version's status changes correctly flips every one of its chunks' `is_current`/
	`source_status`, not just newly-written ones).

	`is_current` is computed exactly like `ai_tools.search_effective_documents()`'s own defensive
	double-check: a chunk is only ever current when BOTH its own `DMS Document Version.status ==
	'Effective'` AND its parent `DMS Document.status == 'Effective'` — the same invariant
	`dms_validations.dms_document_version_on_update()` keeps in sync, asserted independently here
	rather than trusted blindly."""
	version = frappe.get_doc("DMS Document Version", version_name)
	doc_meta = frappe.db.get_value("DMS Document", version.document, ["title", "status"], as_dict=True)
	is_current = bool(version.status == "Effective" and doc_meta and doc_meta.status == "Effective")

	# Real re-index, not append-only growth — delete this version's own prior chunks first.
	frappe.db.delete("RAG Chunk", {"source_doctype": "DMS Document Version", "source_reference": version_name})

	chunks = chunk_text(version.content_summary)
	now = frappe.utils.now_datetime()
	for index, chunk in enumerate(chunks):
		frappe.get_doc(
			{
				"doctype": "RAG Chunk",
				"source_doctype": "DMS Document Version",
				"source_reference": version_name,
				"document_code": version.document,
				"document_title": doc_meta.title if doc_meta else None,
				"version_no": version.version_no,
				"chunk_index": index,
				"chunk_text": chunk,
				"embedding": frappe.as_json(mock_embed(chunk)),
				"source_status": version.status,
				"is_current": 1 if is_current else 0,
				"indexed_on": now,
			}
		).insert(ignore_permissions=True)

	return {
		"version": version_name,
		"document": version.document,
		"version_no": version.version_no,
		"chunks_indexed": len(chunks),
		"is_current": is_current,
		"source_status": version.status,
	}


def reindex_document_version_on_update(doc, method=None):
	"""`hooks.py` doc_events — an ADDITIONAL `on_update` handler for `DMS Document Version`,
	alongside (never replacing) `dms_validations.dms_document_version_on_update()`. See this
	module's own docstring for why this fires unconditionally (not gated on
	`doc.status == "Effective"`) and how that naturally re-indexes BOTH sides of an Effective/
	Obsolete swap from one real save."""
	index_document_version(doc.name)


def is_source_visible(source_doctype: str, source_reference: str, user: str) -> bool:
	"""Real per-user permission check on a chunk's own source record — `frappe.get_list(...,
	user=user)`, never `frappe.get_all()`/doctype-level-only `has_permission()` (this session's own
	established idiom). Real, empirically-found gotcha this function exists to handle correctly:
	`frappe.get_list()` raises `frappe.PermissionError` (rather than returning an empty list) when
	`user` has NO read permission on the DocType AT ALL — as opposed to a row-level restriction
	(e.g. a User Permission) that simply filters the result set down to nothing. Both cases mean
	the same thing from a retrieval caller's point of view ("this user cannot see this record"), so
	both are normalized to a single boolean here rather than leaking a raw PermissionError up
	through `ai_tools.search_knowledge_base()`/`get_document()` (found empirically while first
	building this demo's own permission-proof test with a real zero-DMS-permission user — see
	`ai_permission_aware_rag_seeds.py`'s own RAG test #3)."""
	try:
		rows = frappe.get_list(source_doctype, filters={"name": source_reference}, fields=["name"], user=user, limit_page_length=1)
	except frappe.PermissionError:
		return False
	return bool(rows)


def reindex_all_effective_documents() -> dict:
	"""Bulk (re)index entry point for seed/bootstrap use — indexes every `DMS Document Version`
	that currently exists, in `version_no` order per document (so an older version's chunks are
	written, then a newer one's, matching real chronological indexing). Idempotent: safe to call
	repeatedly (each call deletes-then-recreates each version's own chunks, never accumulating
	duplicates) — used by `ai_permission_aware_rag_seeds.py` to guarantee the whole DMS corpus is
	indexed before this demo's own validations run, without depending on save-time hook timing
	for versions that already existed before this Phase 6A item was built."""
	versions = frappe.get_all("DMS Document Version", fields=["name"], order_by="document asc, version_no asc")
	results = [index_document_version(v.name) for v in versions]
	return {
		"versions_indexed": len(results),
		"total_chunks": sum(r["chunks_indexed"] for r in results),
		"current_chunks": sum(r["chunks_indexed"] for r in results if r["is_current"]),
	}
