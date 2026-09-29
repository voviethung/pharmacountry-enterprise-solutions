"""Phase 6A — Evaluation Datasets (master plan §13.14), seed data + validations. The NINTH and
final curated Phase 6A item — once this is confirmed working on both sites, Phase 6A is complete
(9/9).

Registers:
  1. The `classify_complaint` AI Tool + Prompt Template + AI Action (appended to the SAME shared
     `AI Tool` registry AI-DEMO-01 built — 32 tools total now), mirroring `deviation_analysis`'s
     own Phase 2A registration shape in `ai_seeds.py`.
  2. A small, deliberately capability-incomplete `AI Model` fixture (`legacy-chat-only`, kept
     DISABLED except during `check_model_swap_safe()`'s own negative-scenario validation below) —
     used ONLY to demonstrate a real, concrete model-swap REGRESSION being caught and blocked;
     never enabled in normal site operation.
  3. Two new, isolated `QMS Deviation` records (`AI-EVAL-DEVIATION-01/02`) — added ONLY because
     Golden Demo #2/#3 + AI-DEMO-02's real, pre-existing Deviations (5 of them platform-wide:
     "Warehouse B", "Warehouse C", "Packaging label misprint", "Q01-TEST-DEVIATION", "Deviation
     raised from OOS...") don't exhibit Critical severity or a Process/Documentation category —
     these 2 give the `deviation_analysis` evaluation dataset that missing coverage, per this
     task's own "add a FEW new labeled ones only if you need specific severity/category coverage
     the existing real data doesn't have" instruction. The other 5 cases are the REAL, organic,
     pre-existing records, labeled with their own real recorded fields — not fabricated.
  4. Twelve new, isolated `QMS Complaint` records (`AI-EVAL-COMPLAINT-01`..`12`) — ALL of them, by
     necessity: `QMS Complaint` is a real DocType in this codebase (Golden Demo #2/#3 QMS) but had
     ZERO pre-existing records anywhere on this platform before this build (confirmed by reading
     every seed module first — it is only ever referenced by `bootstrap_qms_doctypes.py`'s own
     DocType-creation code). Two of the twelve are DELIBERATE, honestly-documented classifier
     failures (a false negative and a false positive — see `_COMPLAINT_CASES` below) proving the
     false-positive/negative TRACKING mechanism actually fires on a real mismatch, not just
     trivially reporting zero forever.
  5. `AI Evaluation Case` rows labeling all of the above (7 for `deviation_analysis`, 12 for
     `classify_complaint`), and validations that run the real evaluation harness
     (`ai_evaluation.run_evaluation()`) end-to-end for both actions plus both
     `check_model_swap_safe()` scenarios (an ALLOWED same-capability swap, a BLOCKED
     capability-incompatible swap).
"""

import frappe

from enterprise_core.enterprise_core.ai_evaluation import check_model_swap_safe, run_evaluation
from enterprise_core.enterprise_core.qms_seeds import seed_deviation_capa_flow, seed_qms_oos_oot, seed_qms_validations

# ---------------------------------------------------------------------------
# classify_complaint registration — mirrors ai_seeds.py's deviation_analysis shape exactly.
# ---------------------------------------------------------------------------

_CLASSIFY_COMPLAINT_ACTION_CODE = "classify_complaint"


def _ensure_ai_tool():
	if frappe.db.exists("AI Tool", "classify_complaint"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Tool",
			"tool_code": "classify_complaint",
			"label": "Classify Complaint",
			"description": "Real, deterministic, explainable (keyword-based) category/severity/safety-flag classification for one QMS Complaint (Golden Demo #2/#3 QMS). Built for the Evaluation Datasets demo (master plan §13.14).",
			"python_function_path": "enterprise_core.enterprise_core.ai_tools.classify_complaint",
			"required_permission_doctype": "QMS Complaint",
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_prompt_template():
	if frappe.db.exists("Prompt Template", {"template_code": "classify_complaint", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "classify_complaint",
			"version": 1,
			"system_instruction": (
				"You are a GMP/QMS complaint triage assistant. Given a customer complaint's subject and "
				"description, suggest a plausible category (Adverse Event / Safety, Product Quality / "
				"Specification, Packaging / Labeling, Process / Documentation, Service / Delivery, Other) and "
				"severity (Minor/Major/Critical). Always flag that your output requires human QA review before "
				"acting on it, especially for any suggested Adverse Event / Safety classification."
			),
			"input_schema": frappe.as_json({"subject": "string", "description": "string"}),
			"output_schema": frappe.as_json({"suggested_category": "string", "suggested_severity": "string", "is_safety_critical": "boolean"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_ai_action():
	if frappe.db.exists("AI Action", _CLASSIFY_COMPLAINT_ACTION_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": _CLASSIFY_COMPLAINT_ACTION_CODE,
			"description": "Suggest category/severity for a QMS Complaint (Evaluation Datasets demo, master plan §13.14's own worked example) — deliberately minimal, no AI Draft workflow of its own (see ai_tools.classify_complaint()'s docstring).",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "classify_complaint", "version": 1}, "name"),
			"allowed_tools": "classify_complaint",
			"human_review_required": 1,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# Model-swap-regression negative-scenario fixture — a real AI Model deliberately missing the
# "reasoning" capability BOTH deviation_analysis and classify_complaint require. Kept disabled
# except transiently inside check_model_swap_safe() itself (which restores every AI Model's
# enabled state in a `finally` block, same precedent as ai_seeds.py's own _test_fallback()/
# _test_policy_block()) — never eligible in normal site operation.
# ---------------------------------------------------------------------------

MODEL_SWAP_INCOMPATIBLE_MODEL_CODE = "legacy-chat-only"
MODEL_SWAP_SAFE_MODEL_CODE = "llama-3.3-70b-fast"  # already seeded by ai_seeds.py, already has "reasoning"


def _ensure_model_swap_fixture():
	if frappe.db.exists("AI Model", {"provider": "groq", "model_code": MODEL_SWAP_INCOMPATIBLE_MODEL_CODE}):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Model",
			"provider": "groq",
			"model_code": MODEL_SWAP_INCOMPATIBLE_MODEL_CODE,
			"context_window": 8000,
			"input_types": "text",
			"output_types": "text",
			"capabilities": "chat",  # deliberately NOT "reasoning" — the whole point of this fixture
			"latency_class": "Fast",
			"privacy_class": "Public Cloud",
			"enabled": 0,  # stays disabled — only check_model_swap_safe()'s own negative test enables it, transiently
			"priority": 999,
		}
	).insert(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# deviation_analysis — 2 new, isolated Deviations for Critical severity + Process/Documentation
# category coverage the 5 real, pre-existing Deviations don't have.
# ---------------------------------------------------------------------------

_REPORTER = "qa.manager@pharmacountry.vn"

_NEW_DEVIATIONS = [
	{
		"subject": "AI-EVAL-DEVIATION-01 — Critical potency failure prior to release",
		"description": "Batch failed potency specification significantly below the validated range during pre-release testing.",
		"severity": "Critical",
		"investigation_notes": "Risk assessment identified potential patient harm had the batch reached market, triggering an immediate market withdrawal review.",
		"root_cause": "Uncontrolled raw material substitution — wrong active ingredient lot dispensed during weighing.",
		"expected_category": "Product Quality / Specification",
		"expected_severity": "Critical",
		"expected_capa_likely_needed": 1,
	},
	{
		"subject": "AI-EVAL-DEVIATION-02 — Batch record entry not signed in real time",
		"description": "A procedure deviation from the SOP's real-time documentation requirement — the batch record entry was not signed contemporaneously.",
		"severity": "Minor",
		"investigation_notes": "Operator confirmed the step was performed but the signature was applied at end of shift rather than at the time of the step.",
		"root_cause": "Procedure deviation — real-time documentation requirement not followed.",
		"expected_category": "Process / Documentation",
		"expected_severity": "Minor",
		"expected_capa_likely_needed": 0,
	},
]


def _ensure_new_deviations():
	created = []
	for spec in _NEW_DEVIATIONS:
		if frappe.db.exists("QMS Deviation", {"subject": spec["subject"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "QMS Deviation",
				"subject": spec["subject"],
				"description": spec["description"],
				"severity": spec["severity"],
				"status": "Under Investigation",
				"reported_by": _REPORTER,
				"investigation_notes": spec["investigation_notes"],
				"root_cause": spec["root_cause"],
			}
		).insert(ignore_permissions=True)
		created.append(spec["subject"])
	return created


# ---------------------------------------------------------------------------
# classify_complaint — 12 new, isolated Complaints. QMS Complaint has ZERO pre-existing records
# anywhere on this platform (see module docstring), so ALL 12 are newly authored here — honestly
# marked is_synthetic=1 on their AI Evaluation Case rows. #10 and #11 are DELIBERATE classifier
# mismatches (a false negative and a false positive respectively) — see each one's own comment.
# ---------------------------------------------------------------------------

_COMPLAINT_CASES = [
	{
		"subject": "AI-EVAL-COMPLAINT-01 — Severe allergic reaction after use",
		"customer_name": "Nguyen Thi Hoa",
		"description": "Customer reported a severe allergic reaction requiring hospitalization shortly after taking the product.",
		"severity": "Critical",
		"expected_category": "Adverse Event / Safety",
		"expected_severity": "Critical",
		"expected_is_safety_critical": 1,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-02 — Skin rash after topical application",
		"customer_name": "Tran Van Minh",
		"description": "Customer developed a mild skin rash on the application area; no other symptoms reported.",
		"severity": "Major",
		"expected_category": "Adverse Event / Safety",
		"expected_severity": "Major",
		"expected_is_safety_critical": 1,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-03 — Capsules discolored with unusual odor",
		"customer_name": "Le Thi Lan",
		"description": "Several capsules in the bottle appeared discolored and had an unusual odor compared to normal batches.",
		"severity": "Major",
		"expected_category": "Product Quality / Specification",
		"expected_severity": "Major",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-04 — Tablet count short in bottle",
		"customer_name": "Pham Quoc Bao",
		"description": "Bottle received with a short count — 2 tablets missing from the stated quantity on the pack.",
		"severity": "Minor",
		"expected_category": "Product Quality / Specification",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-05 — Wrong lot number printed on carton",
		"customer_name": "Vo Thi Kim",
		"description": "The outer carton label was misprinted with the wrong lot number for this shipment.",
		"severity": "Minor",
		"expected_category": "Packaging / Labeling",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-06 — Tamper-evident seal broken on arrival",
		"customer_name": "Hoang Van Duc",
		"description": "The bottle's tamper-evident seal was broken when the package arrived, cap was not secure.",
		"severity": "Major",
		"expected_category": "Packaging / Labeling",
		"expected_severity": "Major",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-07 — Delivery arrived three days late",
		"customer_name": "Do Thi Mai",
		"description": "Package delivery was delayed by three days beyond the promised window.",
		"severity": "Minor",
		"expected_category": "Service / Delivery",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-08 — Unhelpful customer service regarding refund",
		"customer_name": "Bui Van Thanh",
		"description": "Customer service representative was unhelpful when requesting a refund for a damaged item.",
		"severity": "Minor",
		"expected_category": "Service / Delivery",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-09 — General dissatisfaction with product",
		"customer_name": "Ngo Thi Thu",
		"description": "Customer stated they were not satisfied with the product overall, without specifying further detail.",
		"severity": "Minor",
		"expected_category": "Other",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		# DELIBERATE FALSE NEGATIVE: a cautious human reviewer would flag any "felt unwell after use"
		# report as Adverse Event/Safety regardless of how vague it is, but this simple keyword
		# classifier finds no trigger keyword at all and predicts Other/Minor/not-safety-critical —
		# an honest, real limitation this evaluation dataset is specifically built to surface, not
		# hide. Proves false_negative_count in AI Evaluation Run actually increments on a real
		# mismatch rather than trivially staying zero.
		"subject": "AI-EVAL-COMPLAINT-10 — Felt unwell after use",
		"customer_name": "Dang Van Hung",
		"description": "Customer mentioned feeling generally unwell sometime after using the product and wanted to flag it just in case, no further detail provided.",
		"severity": "Major",
		"expected_category": "Adverse Event / Safety",
		"expected_severity": "Major",
		"expected_is_safety_critical": 1,
	},
	{
		# DELIBERATE FALSE POSITIVE: the word "burning" (from a mechanical friction smell, nothing
		# medical) collides with this classifier's "burn" safety keyword — a real, explainable
		# keyword-classifier limitation (not contrived to be unsolvable, just a genuine homonym
		# collision a real deployment would need to refine). Proves false_positive_count actually
		# increments on a real mismatch.
		"subject": "AI-EVAL-COMPLAINT-11 — Pump mechanism produces a burning smell",
		"customer_name": "Ly Thi Nga",
		"description": "The lotion pump produces a burning smell from friction after repeated use; the product itself works fine and there is no concern reported.",
		"severity": "Minor",
		"expected_category": "Product Quality / Specification",
		"expected_severity": "Minor",
		"expected_is_safety_critical": 0,
	},
	{
		"subject": "AI-EVAL-COMPLAINT-12 — Foreign object found in product",
		"customer_name": "Truong Thi Yen",
		"description": "Customer found a foreign object embedded in the product, raising contamination concerns.",
		"severity": "Critical",
		"expected_category": "Adverse Event / Safety",
		"expected_severity": "Critical",
		"expected_is_safety_critical": 1,
	},
]


def _ensure_complaints():
	created = []
	for spec in _COMPLAINT_CASES:
		if frappe.db.exists("QMS Complaint", {"subject": spec["subject"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "QMS Complaint",
				"subject": spec["subject"],
				"customer_name": spec["customer_name"],
				"description": spec["description"],
				"severity": spec["severity"],
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		created.append(spec["subject"])
	return created


# ---------------------------------------------------------------------------
# AI Evaluation Case rows
# ---------------------------------------------------------------------------

# (subject substring to look up the real deviation name, expected_category, expected_severity,
# expected_capa_likely_needed, is_synthetic)
_DEVIATION_ANALYSIS_CASES = [
	("Cold storage temperature excursion — Warehouse B", "Equipment / Cold Chain", "Major", 1, 0),
	("Q01-TEST-DEVIATION", "Other", "Minor", 0, 0),
	("Deviation raised from OOS", "Product Quality / Specification", "Major", 1, 0),
	("Cold storage temperature excursion — Warehouse C", "Equipment / Cold Chain", "Major", 1, 0),
	("Packaging label misprint — Batch 552199A", "Packaging / Labeling", "Minor", 0, 0),
	("AI-EVAL-DEVIATION-01", "Product Quality / Specification", "Critical", 1, 1),
	("AI-EVAL-DEVIATION-02", "Process / Documentation", "Minor", 0, 1),
]


def _ensure_evaluation_cases():
	created = []
	for i, (subject_like, expected_category, expected_severity, expected_capa, is_synthetic) in enumerate(_DEVIATION_ANALYSIS_CASES, start=1):
		case_code = f"deviation_analysis-{i:02d}"
		if frappe.db.exists("AI Evaluation Case", case_code):
			continue
		dev_name = frappe.db.get_value("QMS Deviation", {"subject": ["like", f"%{subject_like}%"]}, "name")
		if not dev_name:
			frappe.throw(f"seed_ai_evaluation_datasets: expected QMS Deviation matching '{subject_like}' not found — run seed_deviation_capa_flow()/seed_qms_oos_oot()/_ensure_new_deviations() first.")
		frappe.get_doc(
			{
				"doctype": "AI Evaluation Case",
				"case_code": case_code,
				"action_code": "deviation_analysis",
				"source_doctype": "QMS Deviation",
				"input_reference": dev_name,
				"expected_category": expected_category,
				"expected_severity": expected_severity,
				"secondary_flag_name": "capa_likely_needed",
				"expected_secondary_flag": expected_capa,
				"expected_output_notes": f"Labeled from {'a newly-seeded isolated' if is_synthetic else 'the real, pre-existing organic'} QMS Deviation record ({dev_name}).",
				"is_synthetic": is_synthetic,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append(case_code)

	for i, spec in enumerate(_COMPLAINT_CASES, start=1):
		case_code = f"classify_complaint-{i:02d}"
		if frappe.db.exists("AI Evaluation Case", case_code):
			continue
		complaint_name = frappe.db.get_value("QMS Complaint", {"subject": spec["subject"]}, "name")
		if not complaint_name:
			frappe.throw(f"seed_ai_evaluation_datasets: expected QMS Complaint '{spec['subject']}' not found — run _ensure_complaints() first.")
		frappe.get_doc(
			{
				"doctype": "AI Evaluation Case",
				"case_code": case_code,
				"action_code": _CLASSIFY_COMPLAINT_ACTION_CODE,
				"source_doctype": "QMS Complaint",
				"input_reference": complaint_name,
				"expected_category": spec["expected_category"],
				"expected_severity": spec["expected_severity"],
				"secondary_flag_name": "is_safety_critical",
				"expected_secondary_flag": spec["expected_is_safety_critical"],
				"expected_output_notes": f"Newly-seeded isolated QMS Complaint ({complaint_name}) — QMS Complaint had zero pre-existing records platform-wide before this demo.",
				"is_synthetic": 1,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		created.append(case_code)
	return created


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_ai_evaluation_datasets():
	"""Phase 6A / Evaluation Datasets (master plan §13.14) — the ninth and final curated Phase 6A
	item. Depends on Golden Demo #2/#3's own QMS seeds already having run (called defensively
	here, idempotent, same precedent as ai_qms_copilot_seeds.seed_ai_qms_copilot())."""
	base_flow = seed_deviation_capa_flow()
	oos_flow = seed_qms_oos_oot()
	seed_qms_validations()  # ensures Q01-TEST-DEVIATION exists
	tool_created = _ensure_ai_tool()
	template_created = _ensure_prompt_template()
	action_created = _ensure_ai_action()
	fixture_created = _ensure_model_swap_fixture()
	deviations_created = _ensure_new_deviations()
	complaints_created = _ensure_complaints()
	cases_created = _ensure_evaluation_cases()
	return (
		f"seed_ai_evaluation_datasets: base flow: '{base_flow}' '{oos_flow}'. "
		f"classify_complaint AI Tool {'created' if tool_created else 'already existed'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"AI Action {'created' if action_created else 'already existed'}. "
		f"Model-swap fixture {'created' if fixture_created else 'already existed'}. "
		f"New Deviations created: {deviations_created or 'none (already existed)'}. "
		f"New Complaints created: {complaints_created or 'none (already existed)'}. "
		f"AI Evaluation Cases created: {len(cases_created)} ({cases_created or 'none (already existed)'})."
	)


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def _test_deviation_analysis_evaluation():
	report = run_evaluation("deviation_analysis", user="Administrator")
	if report["total_cases"] < 7:
		frappe.throw(f"Evaluation Datasets test FAILED: expected >=7 deviation_analysis cases, got {report['total_cases']}.")
	if report["passed_cases"] < 6:  # at least 6/7 real+isolated cases should classify correctly
		frappe.throw(f"Evaluation Datasets test FAILED: deviation_analysis pass rate too low: {report}")
	run_doc = frappe.get_doc("AI Evaluation Run", report["run"])
	from enterprise_core.enterprise_core.ai_evaluation import NOT_APPLICABLE_MOCKED

	if run_doc.groundedness_score != NOT_APPLICABLE_MOCKED or run_doc.hallucination_flag_rate != NOT_APPLICABLE_MOCKED or run_doc.actionability_score != NOT_APPLICABLE_MOCKED:
		frappe.throw(f"Evaluation Datasets test FAILED: mock-dependent rubric fields should honestly read '{NOT_APPLICABLE_MOCKED}', got groundedness={run_doc.groundedness_score}, hallucination={run_doc.hallucination_flag_rate}, actionability={run_doc.actionability_score}.")
	if not run_doc.rubric_scoring_notes:
		frappe.throw("Evaluation Datasets test FAILED: rubric_scoring_notes (the honesty disclosure) is empty.")
	if report["source_support_score"] != 100.0:
		frappe.throw(f"Evaluation Datasets test FAILED: expected 100% source_support_score for deviation_analysis (every case's real deviation should appear in its own sources), got {report['source_support_score']}.")
	return report


def _test_classify_complaint_evaluation():
	report = run_evaluation("classify_complaint", user="Administrator")
	if report["total_cases"] < 12:
		frappe.throw(f"Evaluation Datasets test FAILED: expected >=12 classify_complaint cases, got {report['total_cases']}.")
	if report["false_positive_count"] < 1:
		frappe.throw(f"Evaluation Datasets test FAILED: expected >=1 false positive (AI-EVAL-COMPLAINT-11's deliberate 'burning' collision) to prove FP tracking fires, got {report['false_positive_count']}.")
	if report["false_negative_count"] < 1:
		frappe.throw(f"Evaluation Datasets test FAILED: expected >=1 false negative (AI-EVAL-COMPLAINT-10's deliberate vague report) to prove FN tracking fires, got {report['false_negative_count']}.")
	if report["passed_cases"] < 9:  # 10 of 12 should genuinely pass; 2 are deliberate misses
		frappe.throw(f"Evaluation Datasets test FAILED: classify_complaint pass rate too low given only 2 deliberate mismatches: {report}")
	if report["source_support_score"] != 100.0:
		frappe.throw(f"Evaluation Datasets test FAILED: expected 100% source_support_score for classify_complaint, got {report['source_support_score']}.")
	return report


def _test_model_swap_safe_allowed():
	"""A same-capability candidate model (already real, already enabled) should NOT regress the
	deterministic classifiers at all (they don't depend on provider/model) — ALLOWED, delta ~0."""
	result = check_model_swap_safe("classify_complaint", MODEL_SWAP_SAFE_MODEL_CODE, user="Administrator")
	if result["verdict"] != "ALLOWED":
		frappe.throw(f"Evaluation Datasets test FAILED: expected ALLOWED for a capability-compatible model swap, got {result}.")
	if result["regressed"]:
		frappe.throw(f"Evaluation Datasets test FAILED: capability-compatible swap incorrectly flagged as regressed: {result}.")
	return result


def _test_model_swap_safe_blocked():
	"""A candidate model missing the 'reasoning' capability required by classify_complaint should
	make EVERY case's pipeline fail (no eligible AI Model) — a REAL 0% pass rate, genuinely
	regressed vs. baseline, correctly BLOCKED."""
	result = check_model_swap_safe("classify_complaint", MODEL_SWAP_INCOMPATIBLE_MODEL_CODE, user="Administrator")
	if result["verdict"] != "BLOCKED":
		frappe.throw(f"Evaluation Datasets test FAILED: expected BLOCKED for a capability-incompatible model swap, got {result}.")
	if not result["regressed"]:
		frappe.throw(f"Evaluation Datasets test FAILED: capability-incompatible swap NOT flagged as regressed: {result}.")
	if result["candidate_pass_rate_percent"] != 0.0:
		frappe.throw(f"Evaluation Datasets test FAILED: expected candidate_pass_rate_percent=0.0 (every case's pipeline should fail with no eligible model), got {result['candidate_pass_rate_percent']}.")
	# Confirm every AI Model's enabled state was genuinely restored afterward (finally block proof).
	still_disabled = frappe.db.get_value("AI Model", {"provider": "groq", "model_code": MODEL_SWAP_INCOMPATIBLE_MODEL_CODE}, "enabled")
	anthropic_restored = frappe.db.get_value("AI Model", {"provider": "anthropic", "model_code": "claude-sonnet-5"}, "enabled")
	if still_disabled != 0 or not anthropic_restored:
		frappe.throw(f"Evaluation Datasets test FAILED: AI Model enabled states were not correctly restored after the model-swap check (fixture enabled={still_disabled}, anthropic restored={anthropic_restored}).")
	return result


def seed_ai_evaluation_datasets_validations():
	"""Runs the real evaluation harness end-to-end for both actions, and both model-swap-safety
	scenarios (allowed + blocked) — every assertion re-derives from a REAL AI Evaluation Run
	record, never trusting a self-report."""
	deviation_report = _test_deviation_analysis_evaluation()
	complaint_report = _test_classify_complaint_evaluation()
	swap_allowed = _test_model_swap_safe_allowed()
	swap_blocked = _test_model_swap_safe_blocked()
	return (
		f"seed_ai_evaluation_datasets_validations: deviation_analysis {deviation_report['passed_cases']}/{deviation_report['total_cases']} passed "
		f"(pass_rate={deviation_report['pass_rate_percent']}%). classify_complaint {complaint_report['passed_cases']}/{complaint_report['total_cases']} passed "
		f"(pass_rate={complaint_report['pass_rate_percent']}%, false_positive={complaint_report['false_positive_count']}, false_negative={complaint_report['false_negative_count']}). "
		f"model-swap-safe ALLOWED scenario CONFIRMED ({swap_allowed['verdict']}, delta={swap_allowed['delta_percent']}). "
		f"model-swap-safe BLOCKED scenario CONFIRMED ({swap_blocked['verdict']}, delta={swap_blocked['delta_percent']})."
	)
