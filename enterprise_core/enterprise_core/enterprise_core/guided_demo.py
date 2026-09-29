"""Guided Demo Mode (master plan §16, lines ~2871-2900) — backend support for the "Start Demo"
Frappe Desk feature. See `bootstrap_guided_demo_doctypes.py` for the DocType design rationale and
`guided_demo_seeds.py` for the actual seeded scenarios.

Reset design (master plan §5.3 "Reset demo", read in full before writing this):
- §5.3 describes a full-site snapshot/reset/backup pipeline (`scripts/reset-site.sh`,
  `demo-lock.sh`) — destructive, whole-site, and explicitly NOT to be run "trong khi có guided
  demo sales" (while a guided sales demo is in progress). That mechanism already exists (DP-206)
  but is the wrong tool for a per-scenario "Reset Scenario" button on a live walkthrough.
- Every scenario this session seeds only NAVIGATES already-real, already-submitted golden-demo
  records — no step itself performs a mutating action, so there is nothing a viewer's clicking
  needs to be undone. "Reset" here can only honestly mean "re-assert the scenario's canonical
  golden-demo data" (re-create anything a demo viewer separately deleted/altered via Desk) — which
  is EXACTLY what this codebase's own idempotent seed functions already do (the DP-307 pattern
  proven safe-to-re-run across every one of the 28 golden demos this session built).
- `reset_function_path` is therefore only ever wired to a function this session has read and
  confirmed is genuinely idempotent (checks-before-creates) — never to a one-shot validation/test
  seed that mints new append-only audit records on every call (e.g. AI QMS Copilot's own
  `seed_ai_qms_copilot_validations`, which deliberately creates a fresh AI Draft/QMS CAPA every
  run as its own audit-trail proof — wiring THAT to a "Reset" button would make every demo viewer's
  click quietly grow the database). Scenarios without a safe function available have
  `allow_reset=0` and an honest `reset_instructions` explaining why, rather than a fake button.
"""

from urllib.parse import quote

import frappe


def compute_direct_link(doctype: str, name: str) -> str | None:
	"""Relative Desk URL for a document, e.g. ("Purchase Receipt", "MAT-PRE-2026-00003") ->
	"/app/purchase-receipt/MAT-PRE-2026-00003". Deliberately relative (not
	frappe.utils.get_url_to_form, which bakes in the CURRENT site's absolute host) so the same
	stored value opens the right record whether viewed on test.demo.local or pharmacountry.vn."""
	if not doctype or not name:
		return None
	slug = doctype.strip().lower().replace(" ", "-")
	return f"/app/{slug}/{quote(str(name), safe='')}"


@frappe.whitelist()
def reset_guided_demo_scenario(scenario_code: str) -> dict:
	"""Called from the "Start Demo" dialog's Reset button. Honest by construction: if the
	scenario doesn't declare both allow_reset AND a reset_function_path, this returns
	status="not_available" with the scenario's own reset_instructions rather than doing nothing
	silently or attempting something destructive."""
	scenario = frappe.get_doc("Guided Demo Scenario", scenario_code)

	if not scenario.allow_reset or not scenario.reset_function_path:
		return {
			"status": "not_available",
			"message": scenario.reset_instructions
			or "No reset mechanism has been built for this scenario — it only navigates existing records, nothing to reset.",
		}

	try:
		fn = frappe.get_attr(scenario.reset_function_path)
		result = fn(scenario.reset_function_arg) if scenario.reset_function_arg else fn()
		frappe.db.commit()
		return {"status": "ok", "result": result}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="Guided Demo Scenario reset failed", message=frappe.get_traceback())
		return {"status": "error", "message": str(e)}
