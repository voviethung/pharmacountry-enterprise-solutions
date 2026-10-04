"""Phase 2A — AI & Automation Foundation seed data. Demonstrates the CE-13 abstraction
end-to-end: 2 providers/models (so a real fallback chain exists, not just one path), one
Action tied to Golden Demo #3's QMS Deviation, an AI-assisted Automation Rule, and a Tenant
Policy — then proves routing, fallback-on-failure, and policy-blocking all actually work, not
just that the registry records exist.
"""

import frappe

from enterprise_core.enterprise_core.ai_core import run_ai_action


def _ensure_providers():
	created = []
	providers = [
		("anthropic", "Anthropic", "Anthropic", "https://api.anthropic.com", 1, 1, 1, 1, 0),
		("groq", "Groq", "Groq", "https://api.groq.com", 1, 1, 0, 0, 0),
		("openai-compat-selfhosted", "Self-Hosted OpenAI-Compatible", "OpenAI-Compatible", "http://private-ai.internal/v1", 0, 1, 0, 0, 0),
	]
	for code, name, ptype, url, enabled, tools, structured, vision, embeddings in providers:
		if frappe.db.exists("AI Provider", code):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Provider",
				"provider_code": code,
				"display_name": name,
				"provider_type": ptype,
				"base_url": url,
				"api_key_secret": f"secret://ai-providers/{code}" if enabled else "",
				"enabled": enabled,
				"data_policy": "No Training on Data",
				"supports_tools": tools,
				"supports_structured_output": structured,
				"supports_vision": vision,
				"supports_embeddings": embeddings,
			}
		).insert(ignore_permissions=True)
		created.append(code)
	return created


def _ensure_models():
	created = []
	models = [
		("anthropic", "claude-sonnet-5", "chat,reasoning,structured_output,tool_use,long_context", 10),
		("groq", "llama-3.3-70b-fast", "chat,reasoning", 20),
	]
	for provider, model_code, capabilities, priority in models:
		if frappe.db.exists("AI Model", {"provider": provider, "model_code": model_code}):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Model",
				"provider": provider,
				"model_code": model_code,
				"context_window": 200000,
				"input_types": "text",
				"output_types": "text,structured",
				"capabilities": capabilities,
				"latency_class": "Standard" if provider == "anthropic" else "Fast",
				"privacy_class": "Public Cloud",
				"enabled": 1,
				"priority": priority,
			}
		).insert(ignore_permissions=True)
		created.append(model_code)
	return created


def _ensure_prompt_template():
	if frappe.db.exists("Prompt Template", {"template_code": "deviation_analysis", "version": 1}):
		return False
	frappe.get_doc(
		{
			"doctype": "Prompt Template",
			"template_code": "deviation_analysis",
			"version": 1,
			"system_instruction": (
				"You are a GMP quality assistant. Given a deviation's subject, severity and investigation notes, "
				"suggest a plausible root cause category and whether a CAPA is likely needed. Always flag that "
				"your output requires human QA review before acting on it."
			),
			"input_schema": frappe.as_json({"subject": "string", "severity": "string", "investigation_notes": "string"}),
			"output_schema": frappe.as_json({"suggested_root_cause_category": "string", "capa_likely_needed": "boolean"}),
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_action():
	if frappe.db.exists("AI Action", "deviation_analysis"):
		return False
	frappe.get_doc(
		{
			"doctype": "AI Action",
			"action_code": "deviation_analysis",
			"description": "Suggest root cause category and CAPA-need for a QMS Deviation (Golden Demo #3).",
			"required_capabilities": "reasoning",
			"preferred_provider": "anthropic",
			"fallback_policy": "Next Eligible Model",
			"prompt_template": frappe.db.get_value("Prompt Template", {"template_code": "deviation_analysis", "version": 1}, "name"),
			"human_review_required": 1,
			"max_cost_usd": 0.05,
			"retention_policy": "Store Full",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_automation_rule():
	if frappe.db.exists("Automation Rule", {"rule_name": "AI-assisted deviation triage"}):
		return False
	frappe.get_doc(
		{
			"doctype": "Automation Rule",
			"rule_name": "AI-assisted deviation triage",
			"trigger_type": "AI-Assisted",
			"source_doctype": "QMS Deviation",
			"event": "after_insert",
			"ai_action": "deviation_analysis",
			"actions": "Calls run_ai_action('deviation_analysis', ...) to suggest a root cause category for QA review — suggestion only, never auto-applied (human_review_required=1 on the Action).",
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_tenant_policy():
	policy = frappe.get_single("AI Tenant Policy")
	if policy.ai_mode == "Platform Managed":
		return False
	policy.ai_mode = "Platform Managed"
	policy.allowed_providers = "anthropic,groq"
	policy.notes = "Demo default — matches the two enabled providers seeded here. openai-compat-selfhosted stays disabled to demonstrate policy-driven provider control."
	policy.save(ignore_permissions=True)
	return True


def seed_ai_foundation():
	"""DP-1001..DP-1109 (abbreviated) — the CE-13 registry: 2 enabled Providers + 1 disabled
	(policy-control demo), 2 Models forming a real fallback chain, 1 Prompt Template, 1 Action
	tied to Golden Demo #3's QMS Deviation, 1 AI-Assisted Automation Rule, Tenant Policy set
	to Platform Managed."""
	providers_created = _ensure_providers()
	models_created = _ensure_models()
	template_created = _ensure_prompt_template()
	action_created = _ensure_action()
	rule_created = _ensure_automation_rule()
	policy_updated = _ensure_tenant_policy()
	return (
		f"seed_ai_foundation: Providers created: {providers_created or 'none (already existed)'}. "
		f"Models created: {models_created or 'none (already existed)'}. "
		f"Prompt Template {'created' if template_created else 'already existed'}. "
		f"Action {'created' if action_created else 'already existed'}. "
		f"Automation Rule {'created' if rule_created else 'already existed'}. "
		f"Tenant Policy {'set to Platform Managed' if policy_updated else 'already Platform Managed'}."
	)


def _test_happy_path():
	"""Proves run_ai_action() actually routes to the PREFERRED provider (anthropic, priority
	10) when it's eligible, and writes a correct, queryable audit log entry."""
	result = run_ai_action(
		"deviation_analysis",
		{"subject": "Cold storage temperature excursion", "severity": "Major", "investigation_notes": "Compressor thermostat drift."},
	)
	if result["provider"] != "anthropic" or result["fallback_used"]:
		frappe.throw(f"AI happy-path test FAILED: expected provider=anthropic, fallback_used=False, got {result}.")
	log_exists = frappe.db.exists("AI Job Log", {"action": "deviation_analysis", "status": "Success", "provider": "anthropic"})
	if not log_exists:
		frappe.throw("AI happy-path test FAILED: no matching Success AI Job Log entry was written.")
	return True


def _test_fallback():
	"""Disables the preferred provider (anthropic) so the router must fall back to groq
	(priority 20, still eligible) — proves the fallback CHAIN works, not just the single
	happy path. Restores anthropic afterward so the demo's default state stays intact."""
	frappe.db.set_value("AI Provider", "anthropic", "enabled", 0)
	try:
		result = run_ai_action(
			"deviation_analysis",
			{"subject": "Fallback test deviation", "severity": "Minor", "investigation_notes": "n/a — testing router fallback."},
		)
		if result["provider"] != "groq" or not result["fallback_used"]:
			frappe.throw(f"AI fallback test FAILED: expected provider=groq, fallback_used=True, got {result}.")
		log_exists = frappe.db.exists("AI Job Log", {"action": "deviation_analysis", "status": "Fallback Used", "provider": "groq"})
		if not log_exists:
			frappe.throw("AI fallback test FAILED: no matching 'Fallback Used' AI Job Log entry was written.")
	finally:
		frappe.db.set_value("AI Provider", "anthropic", "enabled", 1)
	return True


def _test_policy_block():
	"""Sets AI Mode to Disabled and confirms run_ai_action() refuses to call ANY provider
	(not just the preferred one) and still writes an audit log entry for the blocked attempt.
	Restores Platform Managed afterward."""
	policy = frappe.get_single("AI Tenant Policy")
	policy.ai_mode = "Disabled"
	policy.save(ignore_permissions=True)
	blocked = False
	try:
		try:
			run_ai_action("deviation_analysis", {"subject": "Policy block test", "severity": "Minor", "investigation_notes": "n/a"})
		except frappe.ValidationError:
			blocked = True
		if not blocked:
			frappe.throw("AI policy-block test FAILED: an action was allowed through while AI Mode is Disabled!")
		log_exists = frappe.db.exists("AI Job Log", {"action": "deviation_analysis", "status": "Blocked by Policy"})
		if not log_exists:
			frappe.throw("AI policy-block test FAILED: no matching 'Blocked by Policy' AI Job Log entry was written.")
	finally:
		policy.ai_mode = "Platform Managed"
		policy.save(ignore_permissions=True)
	return True


def seed_ai_validations():
	"""DP-1109-equivalent — proves routing, fallback, and policy enforcement all actually
	work end-to-end, not just that the registry records exist. Each test temporarily perturbs
	shared state (provider enabled flag, tenant AI mode) and restores it in a finally block —
	safe to re-run, and doesn't leave the demo in an altered state for anything that runs
	after it."""
	happy = _test_happy_path()
	fallback = _test_fallback()
	policy_block = _test_policy_block()
	return f"seed_ai_validations: happy-path routing CONFIRMED ({happy}). fallback CONFIRMED ({fallback}). policy-block CONFIRMED ({policy_block})."
