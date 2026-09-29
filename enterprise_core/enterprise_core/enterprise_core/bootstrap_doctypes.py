"""One-off helper (DP-301/DP-302) to create DocTypes via the ORM instead of hand-written
JSON, so Frappe generates schema-correct files for this exact version. Run with
developer_mode=1:

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_doctypes.run

Idempotent — skips any DocType that already exists, and only appends genuinely-missing
fields to ones that do (never overwrites an existing field).
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


def _add_field_if_missing(doctype_name, field_dict):
	doc = frappe.get_doc("DocType", doctype_name)
	if any(f.fieldname == field_dict["fieldname"] for f in doc.fields):
		print(f"Field '{field_dict['fieldname']}' already exists on '{doctype_name}', skipping.")
		return
	doc.append("fields", field_dict)
	doc.save()
	print(f"Added field '{field_dict['fieldname']}' to '{doctype_name}'.")


def run():
	# --- DP-301: Capability Engine registry + Edition ---------------------------------
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Capability Engine",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:engine_code",
			"fields": [
				{"fieldname": "engine_code", "fieldtype": "Data", "label": "Engine Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "engine_name", "fieldtype": "Data", "label": "Engine Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "category", "fieldtype": "Select", "label": "Category", "options": "Core\nIndustry\nAI", "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "engine_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Edition Capability Engine",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "capability_engine", "fieldtype": "Link", "label": "Capability Engine", "options": "Capability Engine", "reqd": 1, "in_list_view": 1},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
			],
		}
	)

	# --- DP-302: Feature Flag registry (created before Edition needs to reference it) --
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Feature Flag",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:feature_code",
			"fields": [
				{"fieldname": "feature_code", "fieldtype": "Data", "label": "Feature Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "feature_name", "fieldtype": "Data", "label": "Feature Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "capability_engine", "fieldtype": "Link", "label": "Capability Engine", "options": "Capability Engine", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "default_enabled", "fieldtype": "Check", "label": "Default Enabled", "default": "0"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "feature_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Edition Feature Flag",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "feature_flag", "fieldtype": "Link", "label": "Feature Flag", "options": "Feature Flag", "reqd": 1, "in_list_view": 1},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Edition",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:edition_code",
			"fields": [
				{"fieldname": "edition_name", "fieldtype": "Data", "label": "Edition Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "edition_code", "fieldtype": "Data", "label": "Edition Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "is_default", "fieldtype": "Check", "label": "Is Default", "default": "0"},
				{"fieldname": "disabled", "fieldtype": "Check", "label": "Disabled", "default": "0"},
				{"fieldname": "capability_engines", "fieldtype": "Table", "label": "Capability Engines", "options": "Edition Capability Engine"},
				{"fieldname": "feature_flags", "fieldtype": "Table", "label": "Feature Flags", "options": "Edition Feature Flag"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "edition_code",
			"sort_order": "ASC",
		}
	)
	# Edition may already exist from a prior DP-301-only run (before DP-302 added the
	# feature_flags field) — the create above would have been skipped, so patch it in.
	_add_field_if_missing(
		"Edition",
		{"fieldname": "feature_flags", "fieldtype": "Table", "label": "Feature Flags", "options": "Edition Feature Flag"},
	)

	# --- DP-302: site-wide "which Edition is active" pointer ---------------------------
	# A business-module app (once one exists) reads this via
	# enterprise_core.api.is_feature_enabled/is_capability_engine_enabled instead of
	# hard-coding behavior per site.
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Enterprise Core Settings",
			"module": "Enterprise Core",
			"custom": 0,
			"issingle": 1,
			"fields": [
				{"fieldname": "active_edition", "fieldtype": "Link", "label": "Active Edition", "options": "Edition"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
		}
	)

	# --- DP-303: Industry Pack registry --------------------------------------------------
	# Per master plan §4: "mỗi pack phải là cấu hình + workflow + terminology + seed data +
	# dashboard + report; không copy core code." This registry entity itself only carries
	# identity, category, an optional linked Edition, and terminology overrides — role
	# template (DP-304), workspace template (DP-305) and seed registry (DP-306) are
	# separate, not-yet-built concerns; deliberately not stubbing Link fields to DocTypes
	# that don't exist yet.
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Industry Pack Terminology",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "context", "fieldtype": "Data", "label": "Context", "description": "Where this term appears, e.g. a DocType or field label", "in_list_view": 1, "reqd": 1},
				{"fieldname": "default_term", "fieldtype": "Data", "label": "Default Term", "in_list_view": 1, "reqd": 1},
				{"fieldname": "override_term", "fieldtype": "Data", "label": "Override Term", "in_list_view": 1, "reqd": 1},
			],
		}
	)

	# --- DP-304: Role template registry (created before Industry Pack needs to reference it) --
	# A Role Template is a reusable, human-meaningful role definition (e.g. "QA Manager")
	# that can be shared across multiple Industry Packs — it's a separate registry from
	# Industry Pack itself so the same template doesn't get redefined per pack. `frappe_role`
	# is optional: wiring a template to a real Frappe Role/permission set is a later,
	# per-role decision (DP-400 Demo Factory territory), not something this registry forces.
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Role Template",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:template_code",
			"fields": [
				{"fieldname": "template_code", "fieldtype": "Data", "label": "Template Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "frappe_role", "fieldtype": "Link", "label": "Frappe Role", "options": "Role", "description": "Optional — the actual Frappe Role this template maps to, once one is assigned."},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "template_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Industry Pack Role",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "role_template", "fieldtype": "Link", "label": "Role Template", "options": "Role Template", "reqd": 1, "in_list_view": 1},
				{"fieldname": "is_required", "fieldtype": "Check", "label": "Is Required", "default": "1", "in_list_view": 1},
			],
		}
	)

	# --- DP-305: Workspace template registry (created before Industry Pack references it) --
	# Same pattern as DP-304's Role Template: a named, reusable workspace concept (e.g.
	# "QA/QC Workspace") that Industry Packs declare a need for, optionally mapped to a real
	# Frappe Workspace once one is built. `frappe_workspace` left blank on purpose.
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Workspace Template",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:template_code",
			"fields": [
				{"fieldname": "template_code", "fieldtype": "Data", "label": "Template Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "frappe_workspace", "fieldtype": "Link", "label": "Frappe Workspace", "options": "Workspace", "description": "Optional — the actual Frappe Workspace this template maps to, once one is built."},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "template_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Industry Pack Workspace",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "workspace_template", "fieldtype": "Link", "label": "Workspace Template", "options": "Workspace Template", "reqd": 1, "in_list_view": 1},
				{"fieldname": "is_required", "fieldtype": "Check", "label": "Is Required", "default": "1", "in_list_view": 1},
			],
		}
	)

	# --- DP-306: Seed registry -----------------------------------------------------------
	# Unlike Role/Workspace Template (which are just labels), a Seed Template must actually
	# be runnable — master plan Phase 2 calls this a "Seed runner", not just a list. Each
	# template's `seed_function` is a dotted path to real code; enterprise_core.api.
	# run_industry_pack_seeds() dispatches to it in `sequence` order.
	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Seed Template",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:template_code",
			"fields": [
				{"fieldname": "template_code", "fieldtype": "Data", "label": "Template Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "seed_type", "fieldtype": "Select", "label": "Seed Type", "options": "Master Data\nTransaction\nDemo Scenario", "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "seed_function", "fieldtype": "Data", "label": "Seed Function", "reqd": 1, "description": "Dotted path to a Python function, e.g. enterprise_core.seeds.seed_demo_company — called with no arguments by the runner."},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "template_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Industry Pack Seed",
			"module": "Enterprise Core",
			"custom": 0,
			"istable": 1,
			"fields": [
				{"fieldname": "seed_template", "fieldtype": "Link", "label": "Seed Template", "options": "Seed Template", "reqd": 1, "in_list_view": 1},
				{"fieldname": "sequence", "fieldtype": "Int", "label": "Sequence", "default": "10", "in_list_view": 1},
				{"fieldname": "is_required", "fieldtype": "Check", "label": "Is Required", "default": "1", "in_list_view": 1},
			],
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Industry Pack",
			"module": "Enterprise Core",
			"custom": 0,
			"autoname": "field:pack_code",
			"fields": [
				{"fieldname": "pack_code", "fieldtype": "Data", "label": "Pack Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "pack_name", "fieldtype": "Data", "label": "Pack Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "industry_category", "fieldtype": "Select", "label": "Industry Category", "options": "Pharmaceutical\nNutraceutical\nCosmetics\nMedical Device\nVeterinary\nAnimal Feed\nLivestock\nAquaculture\nProcessing\nHorizontal / Cross-Industry", "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "default_edition", "fieldtype": "Link", "label": "Default Edition", "options": "Edition", "description": "Which Edition (capability engine bundle) this pack is typically paired with, if one exists yet."},
				{"fieldname": "terminology_overrides", "fieldtype": "Table", "label": "Terminology Overrides", "options": "Industry Pack Terminology"},
				{"fieldname": "roles", "fieldtype": "Table", "label": "Roles", "options": "Industry Pack Role"},
				{"fieldname": "workspaces", "fieldtype": "Table", "label": "Workspaces", "options": "Industry Pack Workspace"},
				{"fieldname": "seeds", "fieldtype": "Table", "label": "Seeds", "options": "Industry Pack Seed"},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1"},
			],
			"permissions": [
				{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}
			],
			"sort_field": "pack_code",
			"sort_order": "ASC",
		}
	)
	# Industry Pack may already exist from an earlier DP-303/304/305-only run.
	_add_field_if_missing(
		"Industry Pack",
		{"fieldname": "roles", "fieldtype": "Table", "label": "Roles", "options": "Industry Pack Role"},
	)
	_add_field_if_missing(
		"Industry Pack",
		{"fieldname": "workspaces", "fieldtype": "Table", "label": "Workspaces", "options": "Industry Pack Workspace"},
	)
	_add_field_if_missing(
		"Industry Pack",
		{"fieldname": "seeds", "fieldtype": "Table", "label": "Seeds", "options": "Industry Pack Seed"},
	)

	frappe.db.commit()
