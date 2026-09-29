"""Phase 2A — AI & Automation Foundation (master plan CE-13 / EPIC DP-1000/1100, "PHASE 2A"
in the phase list — placed BEFORE Phase 3 in the master plan's own sequence but not built
until now). DocTypes for the abstraction layer, same ORM-based creation pattern as the other
bootstrap_*_doctypes.py files.

Master plan is explicit that full AI (RAG/agents) is NOT required at this stage — only that
"phải tạo abstraction đúng ngay từ đầu" (the abstraction must be correct from the start). So
this creates the registry + orchestration layer (Provider/Model/Action/Prompt/Job
Log/Automation Rule/Tenant Policy) with a real routing/fallback/audit-logging engine
(ai_core.py), but the actual "adapter" that would call a live OpenAI/Anthropic/Groq API is a
clearly-labeled mock — no API keys exist in this demo environment, and master plan §13.18
explicitly forbids storing real API keys in app config/client code anyway.

    bench --site <site> execute enterprise_core.enterprise_core.bootstrap_ai_doctypes.run
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
			"name": "AI Provider",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:provider_code",
			"fields": [
				{"fieldname": "provider_code", "fieldtype": "Data", "label": "Provider Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "display_name", "fieldtype": "Data", "label": "Display Name", "reqd": 1, "in_list_view": 1},
				{
					"fieldname": "provider_type",
					"fieldtype": "Select",
					"label": "Provider Type",
					"options": "OpenAI\nAnthropic\nGroq\nGoogle Gemini\nOpenAI-Compatible\nLocal/Private\nCustom",
					"reqd": 1,
					"in_list_view": 1,
				},
				{"fieldname": "base_url", "fieldtype": "Data", "label": "Base URL"},
				{
					"fieldname": "api_key_secret",
					"fieldtype": "Data",
					"label": "API Key Secret Reference",
					"description": "A reference/name into a secrets store — master plan §13.18 forbids storing the real key here or in any client-visible config.",
				},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
				{"fieldname": "timeout_seconds", "fieldtype": "Int", "label": "Timeout (seconds)", "default": "30"},
				{"fieldname": "rate_limit_per_minute", "fieldtype": "Int", "label": "Rate Limit (requests/min)"},
				{"fieldname": "data_policy", "fieldtype": "Select", "label": "Data Policy", "options": "No Training on Data\nMay Train on Data\nUnknown"},
				{"fieldname": "region", "fieldtype": "Data", "label": "Region"},
				{"fieldname": "supports_streaming", "fieldtype": "Check", "label": "Supports Streaming"},
				{"fieldname": "supports_tools", "fieldtype": "Check", "label": "Supports Tools"},
				{"fieldname": "supports_structured_output", "fieldtype": "Check", "label": "Supports Structured Output"},
				{"fieldname": "supports_embeddings", "fieldtype": "Check", "label": "Supports Embeddings"},
				{"fieldname": "supports_vision", "fieldtype": "Check", "label": "Supports Vision"},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "provider_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "AI Model",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "provider", "fieldtype": "Link", "label": "Provider", "options": "AI Provider", "reqd": 1, "in_list_view": 1},
				{"fieldname": "model_code", "fieldtype": "Data", "label": "Model Code", "reqd": 1, "in_list_view": 1},
				{"fieldname": "context_window", "fieldtype": "Int", "label": "Context Window (tokens)"},
				{"fieldname": "input_types", "fieldtype": "Data", "label": "Input Types", "description": "Comma-separated: text, image, audio"},
				{"fieldname": "output_types", "fieldtype": "Data", "label": "Output Types", "description": "Comma-separated: text, structured, embeddings"},
				{
					"fieldname": "capabilities",
					"fieldtype": "Data",
					"label": "Capabilities",
					"reqd": 1,
					"in_list_view": 1,
					"description": "Comma-separated: chat, reasoning, structured_output, tool_use, long_context, embeddings, vision, classification, extraction",
				},
				{"fieldname": "cost_input_per_1k", "fieldtype": "Currency", "label": "Cost per 1K Input Tokens (USD)", "precision": "6"},
				{"fieldname": "cost_output_per_1k", "fieldtype": "Currency", "label": "Cost per 1K Output Tokens (USD)", "precision": "6"},
				{"fieldname": "latency_class", "fieldtype": "Select", "label": "Latency Class", "options": "Fast\nStandard\nSlow"},
				{"fieldname": "privacy_class", "fieldtype": "Select", "label": "Privacy Class", "options": "Public Cloud\nEnterprise Cloud\nPrivate/On-Prem"},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
				{"fieldname": "priority", "fieldtype": "Int", "label": "Priority (lower = tried first)", "default": "100", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "priority",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Prompt Template",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "template_code", "fieldtype": "Data", "label": "Template Code", "reqd": 1, "in_list_view": 1},
				{"fieldname": "version", "fieldtype": "Int", "label": "Version", "reqd": 1, "default": "1", "in_list_view": 1},
				{"fieldname": "system_instruction", "fieldtype": "Long Text", "label": "System Instruction", "reqd": 1},
				{"fieldname": "input_schema", "fieldtype": "Code", "label": "Input Schema (JSON)", "options": "JSON"},
				{"fieldname": "output_schema", "fieldtype": "Code", "label": "Output Schema (JSON)", "options": "JSON"},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
				{"fieldname": "change_history", "fieldtype": "Small Text", "label": "Change History Note"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "AI Action",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "field:action_code",
			"fields": [
				{"fieldname": "action_code", "fieldtype": "Data", "label": "Action Code", "reqd": 1, "unique": 1, "in_list_view": 1},
				{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
				{"fieldname": "required_capabilities", "fieldtype": "Data", "label": "Required Capabilities", "reqd": 1, "description": "Comma-separated, matched against AI Model.capabilities"},
				{"fieldname": "preferred_provider", "fieldtype": "Link", "label": "Preferred Provider", "options": "AI Provider"},
				{"fieldname": "fallback_policy", "fieldtype": "Select", "label": "Fallback Policy", "options": "Next Eligible Model\nFail Closed\nQueue for Retry", "default": "Next Eligible Model"},
				{"fieldname": "prompt_template", "fieldtype": "Link", "label": "Prompt Template", "options": "Prompt Template", "reqd": 1, "in_list_view": 1},
				{"fieldname": "allowed_tools", "fieldtype": "Data", "label": "Allowed Tools", "description": "Comma-separated"},
				{"fieldname": "required_permission", "fieldtype": "Link", "label": "Required Permission (Role)", "options": "Role"},
				{"fieldname": "human_review_required", "fieldtype": "Check", "label": "Human Review Required", "default": "1", "in_list_view": 1},
				{"fieldname": "max_cost_usd", "fieldtype": "Currency", "label": "Max Cost (USD)", "precision": "4"},
				{"fieldname": "retention_policy", "fieldtype": "Select", "label": "Retention Policy", "options": "Store Full\nStore Metadata Only\nDo Not Store"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "action_code",
			"sort_order": "ASC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "AI Job Log",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 0,
			"autoname": "hash",
			"fields": [
				{"fieldname": "user", "fieldtype": "Link", "label": "User", "options": "User", "in_list_view": 1},
				{"fieldname": "site", "fieldtype": "Data", "label": "Site/Tenant", "in_list_view": 1},
				{"fieldname": "action", "fieldtype": "Link", "label": "AI Action", "options": "AI Action", "reqd": 1, "in_list_view": 1},
				{"fieldname": "timestamp", "fieldtype": "Datetime", "label": "Timestamp", "default": "now", "in_list_view": 1},
				{"fieldname": "provider", "fieldtype": "Link", "label": "Provider Used", "options": "AI Provider"},
				{"fieldname": "model", "fieldtype": "Data", "label": "Model Used"},
				{"fieldname": "prompt_template_version", "fieldtype": "Data", "label": "Prompt Template Version"},
				{"fieldname": "input_source_refs", "fieldtype": "Small Text", "label": "Input Source References"},
				{"fieldname": "retrieved_sources", "fieldtype": "Small Text", "label": "Retrieved Sources"},
				{"fieldname": "tool_calls", "fieldtype": "Small Text", "label": "Tool Calls"},
				{"fieldname": "output", "fieldtype": "Long Text", "label": "Output"},
				{"fieldname": "tokens_used", "fieldtype": "Int", "label": "Tokens Used"},
				{"fieldname": "estimated_cost_usd", "fieldtype": "Currency", "label": "Estimated Cost (USD)", "precision": "6"},
				{"fieldname": "latency_ms", "fieldtype": "Int", "label": "Latency (ms)"},
				{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Success\nFallback Used\nFailed\nBlocked by Policy", "in_list_view": 1},
				{"fieldname": "user_feedback", "fieldtype": "Select", "label": "User Feedback", "options": "\nHelpful\nNot Helpful"},
				{"fieldname": "accepted", "fieldtype": "Check", "label": "Accepted"},
				{"fieldname": "edited", "fieldtype": "Check", "label": "Edited Before Use"},
				{"fieldname": "final_record_reference", "fieldtype": "Data", "label": "Final Record Reference"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "timestamp",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "Automation Rule",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"autoname": "hash",
			"fields": [
				{"fieldname": "rule_name", "fieldtype": "Data", "label": "Rule Name", "reqd": 1, "in_list_view": 1},
				{"fieldname": "trigger_type", "fieldtype": "Select", "label": "Trigger Type", "options": "Event-Based\nSchedule-Based\nThreshold-Based\nAI-Assisted", "reqd": 1, "in_list_view": 1},
				{"fieldname": "source_doctype", "fieldtype": "Link", "label": "Source DocType", "options": "DocType"},
				{"fieldname": "event", "fieldtype": "Data", "label": "Event", "description": "e.g. after_insert, on_update, on_submit"},
				{"fieldname": "conditions", "fieldtype": "Code", "label": "Conditions (JSON)", "options": "JSON"},
				{"fieldname": "ai_action", "fieldtype": "Link", "label": "AI Action (if AI-Assisted)", "options": "AI Action"},
				{"fieldname": "actions", "fieldtype": "Small Text", "label": "Actions Taken"},
				{"fieldname": "delay_minutes", "fieldtype": "Int", "label": "Delay (minutes)"},
				{"fieldname": "escalation", "fieldtype": "Small Text", "label": "Escalation"},
				{"fieldname": "retry_count", "fieldtype": "Int", "label": "Retry Count", "default": "0"},
				{"fieldname": "enabled", "fieldtype": "Check", "label": "Enabled", "default": "1", "in_list_view": 1},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
			"sort_field": "modified",
			"sort_order": "DESC",
		}
	)

	_create_if_missing(
		{
			"doctype": "DocType",
			"name": "AI Tenant Policy",
			"module": "Enterprise Core",
			"custom": 0,
			"track_changes": 1,
			"issingle": 1,
			"fields": [
				{
					"fieldname": "ai_mode",
					"fieldtype": "Select",
					"label": "AI Mode",
					"options": "Disabled\nExternal Providers\nCustomer API Key\nPlatform Managed\nPrivate Endpoint\nHybrid",
					"default": "Disabled",
					"reqd": 1,
				},
				{"fieldname": "allowed_providers", "fieldtype": "Small Text", "label": "Allowed Providers", "description": "Comma-separated AI Provider codes; blank = all enabled providers allowed"},
				{"fieldname": "data_residency", "fieldtype": "Data", "label": "Data Residency Requirement"},
				{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			],
			"permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "select": 1, "share": 1}],
		}
	)
