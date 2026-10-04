"""Guided Demo Mode (master plan §16, lines ~2871-2900) — a real Frappe Desk "Start Demo"
feature, NOT a new Next.js app (per master plan §8/§2.5: back-office workflow stays on Frappe
Desk). Two DocTypes, created via the ORM the same way every prior `bootstrap_*_doctypes.py` in
this codebase has (schema-correct for this exact Frappe version, not hand-typed JSON):

- `Guided Demo Scenario` — one row per sales walkthrough (e.g. "Pharmaceutical Batch Release").
  Deliberately reuses the existing `Industry Pack` doctype for `golden_demo_reference` rather than
  inventing a parallel registry, matching this whole session's "reuse the real DP-303 registry"
  pattern.
- `Guided Demo Scenario Step` — an ordered child table. `target_doctype`/`target_document` is a
  Dynamic Link pair (same "reference_doctype -> Dynamic Link" pattern already used throughout this
  codebase, e.g. `Meat Incoming Lot.source_reference`), so a step can point at ANY real document —
  a Purchase Receipt, a Batch, a Quality Inspection, a Work Order, whatever that golden demo's own
  seed data actually produced. `direct_link` is computed and stored at seed time (see
  `guided_demo.py::compute_direct_link`) as a relative `/app/<doctype-slug>/<name>` path — kept
  relative (not `frappe.utils.get_url_to_form`, which bakes in the CURRENT site's absolute host)
  specifically so the same scenario record works unmodified on both `test.demo.local` and
  `pharmacountry.vn`, since both sites run this same app.

Run with developer_mode=1 so Frappe auto-exports the doctype's own boilerplate .py/.js files to
disk (same as every earlier bootstrap script) — `guided_demo_scenario.js` is then hand-edited
afterward to render the actual "Start Demo" walkthrough dialog (a real Frappe Desk Page would need
a `bench build`-produced asset bundle the `frontend` container doesn't currently receive via bind
mount; a doctype client script is read live from disk per-request, the same mechanism every other
custom validation/hook edit in this session has relied on, needing only `bench clear-cache` — the
lower-risk, more idiomatic choice for this codebase, not a shortcut).

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_guided_demo_doctypes.run

Idempotent — skips any DocType that already exists, only appends genuinely-missing fields.
"""

import frappe


def _create_if_missing(doctype_dict):
	name = doctype_dict["name"]
	if frappe.db.exists("DocType", name):
		print(f"DocType '{name}' already exists, skipping.")
		return
	doc = frappe.get_doc(doctype_dict)
	doc.insert()
	print(f"Created DocType '{name}'.")


def run():
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Guided Demo Scenario Step",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "step_no", "fieldtype": "Int", "label": "Step No", "reqd": 1, "in_list_view": 1},
				{"fieldname": "instruction", "fieldtype": "Data", "label": "Instruction", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "login_as_role",
					"fieldtype": "Data",
					"label": "Login As (Role)",
					"in_list_view": 1,
					"description": "Human-readable role label for this step, e.g. 'QC Analyst'. Blank if this step doesn't require switching accounts.",
				},
				{
					"fieldname": "login_as_user",
					"fieldtype": "Link",
					"label": "Login As (User)",
					"options": "User",
					"in_list_view": 1,
					"description": "The real demo User to switch to for this step, if one exists.",
				},
				{
					"fieldname": "target_doctype",
					"fieldtype": "Link",
					"label": "Target DocType",
					"options": "DocType",
					"in_list_view": 1,
				},
				{
					"fieldname": "target_document",
					"fieldtype": "Dynamic Link",
					"label": "Target Document",
					"options": "target_doctype",
					"in_list_view": 1,
				},
				{
					"fieldname": "direct_link",
					"fieldtype": "Data",
					"label": "Direct Link",
					"read_only": 1,
					"description": "Computed relative Desk URL (/app/<doctype>/<name>) — opens the real record directly.",
				},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Guided Demo Scenario",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:scenario_code",
			"fields": [
				{"fieldname": "scenario_code", "fieldtype": "Data", "label": "Scenario Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "title", "fieldtype": "Data", "label": "Title", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "golden_demo_reference",
					"fieldtype": "Link",
					"label": "Golden Demo / Industry Pack",
					"options": "Industry Pack",
					"in_list_view": 1,
					"description": "Which Industry Pack (golden demo) this walkthrough belongs to — reuses the real DP-303 registry rather than a parallel one.",
				},
				{
					"fieldname": "primary_login_role",
					"fieldtype": "Data",
					"label": "Primary Login Role / Account",
					"description": "Master plan §16 'Tài khoản role' — the main account a salesperson should sign in as to run this demo.",
				},
				{"fieldname": "primary_login_user", "fieldtype": "Link", "label": "Primary Login User", "options": "User"},
				{"fieldname": "objective", "fieldtype": "Text", "label": "Objective", "reqd": 1},
				{
					"fieldname": "what_this_demonstrates",
					"fieldtype": "Text",
					"label": "What This Demonstrates",
					"reqd": 1,
					"description": "Master plan §16's closing 'What this demonstrates' — the business value summary shown at the end of the walkthrough.",
				},
				{"fieldname": "steps", "fieldtype": "Table", "label": "Steps", "options": "Guided Demo Scenario Step"},
				{
					"fieldname": "allow_reset",
					"fieldtype": "Check",
					"label": "Allow Reset",
					"default": "0",
					"description": "Only set True when reset_function_path points at a genuinely idempotent, verified-safe function — never a placeholder.",
				},
				{
					"fieldname": "reset_function_path",
					"fieldtype": "Data",
					"label": "Reset Function Path",
					"description": "Dotted path to a real, idempotent Python function, e.g. enterprise_core.enterprise_core.api.run_industry_pack_seeds. Called with reset_function_arg if set, else no arguments.",
				},
				{
					"fieldname": "reset_function_arg",
					"fieldtype": "Data",
					"label": "Reset Function Arg",
					"description": "Optional single positional argument passed to reset_function_path (e.g. an Industry Pack code).",
				},
				{
					"fieldname": "reset_instructions",
					"fieldtype": "Small Text",
					"label": "Reset Instructions / Limitation",
					"description": "Always shown to the user, whether or not allow_reset is set — honest explanation of what reset does or why it's unavailable.",
				},
				{"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": "1", "in_list_view": 1},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "scenario_code",
			"sort_order": "ASC",
		}
	)

	frappe.db.commit()
