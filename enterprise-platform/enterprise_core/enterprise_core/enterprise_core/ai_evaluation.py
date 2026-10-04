"""Phase 6A — Evaluation Datasets (master plan §13.14 "AI Evaluation", lines ~1365-1382), the
NINTH and final curated Phase 6A item. Builds the evaluation-dataset shape the master plan asks
for around this platform's own real AI Actions:

    Mỗi action quan trọng phải có evaluation dataset — every important AI action must have an
    evaluation dataset (§13.14's own `classify_complaint` example: 100 labeled cases, expected
    category, expected severity range, false-positive/negative tracking; its `deviation_analysis`
    example: human-review rubric, groundedness, source support, hallucination flag,
    actionability) — và không đổi model production chỉ vì benchmark chung tốt hơn, phải chạy
    regression trên evaluation set nội bộ (never swap the production model just because it scores
    better on a generic public benchmark; any model change must be regression-tested against this
    platform's OWN internal evaluation set first).

Two real actions are evaluated here, both already real (not hypothetical) on this platform:
  - `deviation_analysis` — Phase 2A's own original AI Action (`ai_seeds.py`'s `_ensure_action()`),
    tied to Golden Demo #2/#3's real `QMS Deviation` records.
  - `classify_complaint` — a NEW, deliberately minimal action built for this demo (see
    `ai_tools.classify_complaint()`'s own docstring for why: `QMS Complaint` is a real DocType
    with zero pre-existing records anywhere on this platform, and the master plan names
    `classify_complaint` as its own canonical worked example, so building it gives the closest
    fidelity to spec while reusing real, if newly-seeded, QMS data).

**The central honesty constraint this module is built around**: `ai_core._call_provider_adapter()`
is a fixed MOCK — it returns a canned string (`"[MOCK — no live provider call made] ..."`)
regardless of input content, and that is a HARD constraint this build must not change (no real
LLM API, no real credentials). That means "does the AI's output match the expected label"
scoring would be completely vacuous if it were scored against the mock's own raw text — the mock
never actually reasons about content, so it can never be caught getting a classification right OR
wrong. To make this evaluation dataset genuinely REAL and MEANINGFUL rather than a rubber stamp,
this module checks two separable things per case:
  1. **Pipeline health** — does `ai_core.run_ai_action()` (the real, unmodified router/fallback/
     audit-logging machinery) actually succeed end-to-end for this action, using the platform's
     real AI Model/Provider configuration at the time of the run? This is what lets
     `check_model_swap_safe()` below catch a REAL regression (e.g. a candidate model that lacks a
     required capability breaks routing entirely) — a class of failure a generic public benchmark
     score would never reveal, which is exactly the governance principle §13.14 asks to make
     "concretely demonstrable, not just a docstring comment."
  2. **Classification correctness** — a REAL, deterministic, explainable (keyword-based, non-LLM,
     non-vector) classifier (`ai_tools._classify_qms_text()`, reused here for `QMS Deviation` via
     `classify_deviation_reference()`) produces the actual category/severity/secondary-flag
     prediction that gets checked against each case's labeled ground truth — mirroring the exact
     "real deterministic business-rule logic alongside the untouched mock" precedent
     `ai_qms_copilot._suggest_capa_fields()` already established. This is NOT the "AI" the master
     plan is describing being production-graded elsewhere in this platform; it is a real,
     inspectable stand-in that makes THIS evaluation harness meaningful today, honestly documented
     as such everywhere it appears (code, DocType field labels, and project_status.md).

**What is NOT honestly measurable given the hard mock constraint, and is NOT faked here**:
groundedness, hallucination-flag accuracy, and actionability are all fundamentally about
judging *generated narrative quality* — since the mock's narrative is a fixed template that never
varies with input, it can never be caught being ungrounded, hallucinating, or non-actionable in a
way that would let a scoring function tell a good case from a bad one. `AI Evaluation Run` carries
real DocType fields for these (so the RUBRIC/SCORING INFRASTRUCTURE genuinely exists, per the
master plan's own `deviation_analysis` rubric list), but `run_evaluation()` always leaves them
`None` ("N/A") with a fixed, honest `rubric_scoring_notes` explanation — never a fabricated
number. `source_support_score` is the one rubric-adjacent dimension that IS real: it directly
checks whether each case's returned `sources` citation list actually contains the real record the
case is about.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action
from enterprise_core.enterprise_core.ai_tools import _classify_qms_text, classify_complaint

REGRESSION_THRESHOLD_PERCENT_DEFAULT = 5.0

NOT_APPLICABLE_MOCKED = "N/A - mock adapter does not vary output"

RUBRIC_SCORING_NOTES = (
	"groundedness_score/hallucination_flag_rate/actionability_score are intentionally left NULL "
	"('N/A') for every run of this evaluation harness. ai_core._call_provider_adapter() is a "
	"fixed MOCK that returns a canned string regardless of input content (see its own docstring) "
	"— it never actually reasons about the real data handed to it, so it can never be caught "
	"being ungrounded, hallucinating, or non-actionable in a way a scoring function could "
	"meaningfully distinguish. Scoring these numerically would fabricate a quality signal the "
	"mock cannot produce (per this build's own explicit constraint against inventing fictitious "
	"AI-quality metrics). source_support_score IS real and computed: the percentage of cases "
	"whose real, structured `sources` citation list correctly includes the case's own real input "
	"record. category_match / severity_match / false_positive_count / false_negative_count ARE "
	"real and deterministic, checked against each case's own labeled ground truth via a real, "
	"explainable (keyword-based, non-LLM, non-vector) classifier — see "
	"ai_tools._classify_qms_text()."
)


# ---------------------------------------------------------------------------
# deviation_analysis reference classification — see module docstring for why this exists.
# ---------------------------------------------------------------------------

def classify_deviation_reference(deviation: dict) -> dict:
	"""Real, deterministic reference classification for a `QMS Deviation` row — reuses the SAME
	keyword taxonomy `ai_tools._classify_qms_text()` already established for `classify_complaint`
	(both are real free-text quality events). `capa_likely_needed` is a real, deterministic
	GMP-severity convention already used elsewhere in this codebase's own seed data
	(`qms_seeds.py` always opens a CAPA for its Major deviations) — Major/Critical -> CAPA likely
	needed, Minor -> not, not a fabricated guess."""
	text = " ".join(
		filter(None, [deviation.get("subject"), deviation.get("description"), deviation.get("investigation_notes"), deviation.get("root_cause")])
	)
	classification = _classify_qms_text(text)
	classification["capa_likely_needed"] = classification["predicted_severity"] in ("Major", "Critical")
	return classification


# ---------------------------------------------------------------------------
# Per-action case runners — each returns (classification: dict|None, sources: list, ai_context: dict, error: str|None)
# ---------------------------------------------------------------------------

def _run_deviation_case(case, user):
	rows = frappe.get_list(
		"QMS Deviation",
		filters={"name": case.input_reference},
		fields=["name", "subject", "description", "severity", "investigation_notes", "root_cause"],
		user=user,
		limit_page_length=1,
	)
	if not rows:
		return None, [], {}, f"QMS Deviation {case.input_reference} not found or not visible to user {user}."
	dev = rows[0]
	classification = classify_deviation_reference(dev)
	sources = [f"QMS Deviation:{dev.name}"]
	ai_context = {"subject": dev.subject, "severity": dev.severity, "investigation_notes": dev.investigation_notes or dev.root_cause or ""}
	return classification, sources, ai_context, None


def _run_complaint_case(case, user):
	result = classify_complaint(user=user, complaint=case.input_reference)
	if not result["data"]:
		return None, [], {}, result.get("notes") or f"QMS Complaint {case.input_reference} not found or not visible to user {user}."
	classification = result["data"]
	sources = result["sources"]
	ai_context = {"subject": classification.get("subject"), "description": None, "severity": classification.get("recorded_severity")}
	return classification, sources, ai_context, None


_ACTION_RUNNERS = {
	"deviation_analysis": (_run_deviation_case, "capa_likely_needed"),
	"classify_complaint": (_run_complaint_case, "is_safety_critical"),
}


# ---------------------------------------------------------------------------
# The evaluation harness itself
# ---------------------------------------------------------------------------

def run_evaluation(action_code: str, user: str | None = None, is_model_swap_check: bool = False, extra_note: str | None = None) -> dict:
	"""Loads every enabled `AI Evaluation Case` for `action_code`, and for EACH one: runs the
	real action pipeline (`ai_core.run_ai_action()`, unmodified) AS `user` and a real,
	deterministic classifier producing an actual category/severity/secondary-flag prediction,
	compares both against the case's real labeled ground truth, tallies pass/fail (+ false-
	positive/negative for the secondary flag), computes the honestly-scoreable rubric dimensions
	(see module docstring), persists a new `AI Evaluation Run` row (append-only, same precedent
	as AI Job Log/AI Draft), and returns a structured report. A per-case pipeline failure (e.g.
	`run_ai_action()` finds no eligible AI Model) is caught and counted as a FAILED case rather
	than crashing the whole run — this is exactly what lets `check_model_swap_safe()` below
	observe a real pass-rate regression when a candidate model breaks routing."""
	user = user or frappe.session.user
	if action_code not in _ACTION_RUNNERS:
		frappe.throw(f"run_evaluation: no evaluation runner registered for action_code {action_code!r}. Known: {sorted(_ACTION_RUNNERS)}.")
	runner, secondary_flag_field = _ACTION_RUNNERS[action_code]

	cases = frappe.get_list(
		"AI Evaluation Case",
		filters={"action_code": action_code, "enabled": 1},
		fields=["name", "case_code", "input_reference", "expected_category", "expected_severity", "secondary_flag_name", "expected_secondary_flag"],
		order_by="case_code asc",
		user=user,
		limit_page_length=0,
	)
	if not cases:
		frappe.throw(f"run_evaluation: no enabled AI Evaluation Case rows found for action_code {action_code!r} — run seed_ai_evaluation_datasets() first.")

	results = []
	passed = 0
	false_positive_count = 0
	false_negative_count = 0
	source_support_hits = 0
	used_provider = used_model = None

	for case in cases:
		classification, sources, ai_context, error = runner(case, user)
		pipeline_ok = classification is not None
		if pipeline_ok:
			try:
				ai_result = run_ai_action(action_code, context=ai_context, user=user, tool_calls=[action_code], retrieved_sources=sources)
				used_provider, used_model = ai_result["provider"], ai_result["model"]
			except Exception as e:  # noqa: BLE001 - a pipeline failure (e.g. no eligible model) is a real, countable case failure, not a crash
				pipeline_ok = False
				error = str(e)

		predicted_category = classification.get("predicted_category") if pipeline_ok else None
		predicted_severity = classification.get("predicted_severity") if pipeline_ok else None
		predicted_secondary = bool(classification.get(secondary_flag_field)) if pipeline_ok else False
		expected_secondary = bool(case.expected_secondary_flag)

		category_match = pipeline_ok and predicted_category == case.expected_category
		severity_match = pipeline_ok and predicted_severity == case.expected_severity
		case_passed = pipeline_ok and category_match and severity_match

		if expected_secondary and not predicted_secondary:
			false_negative_count += 1
		elif not expected_secondary and predicted_secondary:
			false_positive_count += 1

		source_ok = pipeline_ok and any(case.input_reference in (s or "") for s in sources)
		if source_ok:
			source_support_hits += 1
		if case_passed:
			passed += 1

		results.append(
			{
				"case_code": case.case_code,
				"input_reference": case.input_reference,
				"pipeline_ok": pipeline_ok,
				"expected_category": case.expected_category,
				"predicted_category": predicted_category,
				"category_match": category_match,
				"expected_severity": case.expected_severity,
				"predicted_severity": predicted_severity,
				"severity_match": severity_match,
				"secondary_flag_name": case.secondary_flag_name,
				"expected_secondary_flag": expected_secondary,
				"predicted_secondary_flag": predicted_secondary,
				"source_support_ok": source_ok,
				"passed": case_passed,
				"error": None if pipeline_ok else error,
			}
		)

	total = len(results)
	pass_rate_percent = round(passed / total * 100, 1) if total else 0.0
	source_support_score = round(source_support_hits / total * 100, 1) if total else 0.0

	previous = frappe.get_list(
		"AI Evaluation Run",
		filters={"action_code": action_code},
		fields=["name", "pass_rate_percent"],
		order_by="creation desc",
		limit_page_length=1,
		ignore_permissions=True,
	)
	regression = None
	if previous:
		delta = round(pass_rate_percent - previous[0].pass_rate_percent, 1)
		regression = {
			"previous_run": previous[0].name,
			"previous_pass_rate_percent": previous[0].pass_rate_percent,
			"current_pass_rate_percent": pass_rate_percent,
			"delta_percent": delta,
			"regressed": delta < -REGRESSION_THRESHOLD_PERCENT_DEFAULT,
		}

	run_doc = frappe.get_doc(
		{
			"doctype": "AI Evaluation Run",
			"action_code": action_code,
			"run_datetime": frappe.utils.now_datetime(),
			"provider_code": used_provider,
			"model_code": used_model,
			"is_model_swap_check": 1 if is_model_swap_check else 0,
			"total_cases": total,
			"passed_cases": passed,
			"failed_cases": total - passed,
			"pass_rate_percent": pass_rate_percent,
			"false_positive_count": false_positive_count,
			"false_negative_count": false_negative_count,
			"source_support_score": source_support_score,
			"groundedness_score": NOT_APPLICABLE_MOCKED,
			"hallucination_flag_rate": NOT_APPLICABLE_MOCKED,
			"actionability_score": NOT_APPLICABLE_MOCKED,
			"rubric_scoring_notes": RUBRIC_SCORING_NOTES,
			"regression_vs_previous_run": frappe.as_json(regression) if regression else None,
			"results_json": frappe.as_json(results),
			"run_by": user,
			"notes": extra_note,
		}
	)
	run_doc.insert(ignore_permissions=True)

	return {
		"run": run_doc.name,
		"action_code": action_code,
		"total_cases": total,
		"passed_cases": passed,
		"failed_cases": total - passed,
		"pass_rate_percent": pass_rate_percent,
		"false_positive_count": false_positive_count,
		"false_negative_count": false_negative_count,
		"source_support_score": source_support_score,
		"regression": regression,
		"results": results,
		"provider": used_provider,
		"model": used_model,
	}


# ---------------------------------------------------------------------------
# The model-swap regression-governance function — master plan §13.14's own principle, made
# concretely demonstrable.
# ---------------------------------------------------------------------------

def check_model_swap_safe(action_code: str, candidate_model_code: str, user: str | None = None, regression_threshold_percent: float = REGRESSION_THRESHOLD_PERCENT_DEFAULT) -> dict:
	"""Concrete, REAL implementation of master plan §13.14's governance principle: "Không đổi
	model production chỉ vì benchmark chung tốt hơn; phải chạy regression trên evaluation set nội
	bộ" (never swap the production model just because it scores better on a generic public
	benchmark; any model change must be regression-tested against this platform's own internal
	evaluation set first).

	Runs the REAL evaluation harness TWICE — once against the CURRENT production AI Model/
	Provider configuration (baseline) and once with `candidate_model_code` temporarily made the
	ONLY enabled `AI Model` for the whole site (a real `ai_core._eligible_models()` routing
	change, restored in a `finally` block exactly like `ai_seeds.py`'s own `_test_fallback()`/
	`_test_policy_block()` precedent) — and returns an ALLOW/BLOCK verdict from a REAL pass-rate
	comparison between two REAL, persisted `AI Evaluation Run` records. There is no second real
	LLM in this demo (the hard mock constraint applies throughout), so this cannot demonstrate a
	quality-of-narrative regression — but it CAN and DOES demonstrate a real, concrete regression
	class a generic public benchmark score would never reveal: a candidate model that lacks a
	capability `action_code` requires makes `run_ai_action()` genuinely unable to route AT ALL
	(every case's pipeline_ok becomes False), which is exactly the kind of blind spot this
	governance principle exists to catch before a model swap ever reaches production."""
	user = user or frappe.session.user
	if not frappe.db.exists("AI Model", {"model_code": candidate_model_code}):
		frappe.throw(f"check_model_swap_safe: AI Model with model_code {candidate_model_code!r} does not exist.")

	baseline = run_evaluation(action_code, user=user, extra_note=f"Baseline run (current production model configuration) for a model-swap regression check against candidate '{candidate_model_code}'.")

	# AI Model autonames on 'hash' — `name` (the docname) is never the same as `model_code`, so
	# every lookup/comparison below must go through the real `model_code` field, never `name`.
	all_models = frappe.get_all("AI Model", fields=["name", "model_code", "enabled"])
	original_enabled = {m.name: m.enabled for m in all_models}
	try:
		for m in all_models:
			frappe.db.set_value("AI Model", m.name, "enabled", 1 if m.model_code == candidate_model_code else 0)
		candidate = run_evaluation(
			action_code,
			user=user,
			is_model_swap_check=True,
			extra_note=f"HYPOTHETICAL model swap check: '{candidate_model_code}' temporarily made the ONLY enabled AI Model site-wide, then restored.",
		)
	finally:
		for name, enabled in original_enabled.items():
			frappe.db.set_value("AI Model", name, "enabled", enabled)

	delta = round(candidate["pass_rate_percent"] - baseline["pass_rate_percent"], 1)
	regressed = delta < -regression_threshold_percent
	verdict = "BLOCKED" if regressed else "ALLOWED"
	reason = (
		f"Candidate model '{candidate_model_code}' pass rate {candidate['pass_rate_percent']}% vs. baseline "
		f"{baseline['pass_rate_percent']}% on this platform's OWN internal '{action_code}' evaluation set "
		f"(delta {delta:+.1f} pts, block threshold -{regression_threshold_percent} pts). "
		+ (
			"BLOCKED: regression exceeds threshold — do NOT promote this model to production for this action, "
			"regardless of any generic public benchmark score it may have."
			if regressed
			else "ALLOWED: no regression beyond threshold detected against the internal evaluation set."
		)
	)
	return {
		"action_code": action_code,
		"candidate_model_code": candidate_model_code,
		"verdict": verdict,
		"regressed": regressed,
		"baseline_run": baseline["run"],
		"baseline_pass_rate_percent": baseline["pass_rate_percent"],
		"candidate_run": candidate["run"],
		"candidate_pass_rate_percent": candidate["pass_rate_percent"],
		"delta_percent": delta,
		"regression_threshold_percent": regression_threshold_percent,
		"reason": reason,
	}
