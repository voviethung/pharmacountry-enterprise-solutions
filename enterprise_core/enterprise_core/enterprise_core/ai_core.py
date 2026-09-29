"""Phase 2A — AI & Automation Foundation (master plan CE-13 §13.2). The abstraction call
pattern business modules must use — `run_ai_action(action_code, context)` — never a provider
SDK directly (§13.2's own explicit anti-pattern warning: no module should import openai/
anthropic/groq clients itself).

`_call_provider_adapter()` is a clearly-labeled MOCK: no live API keys exist in this demo
environment, and master plan §13.18 forbids storing real keys in app config/client code
regardless. The parts that ARE real and fully working here are exactly what Phase 2A asks
for: capability-based routing, tenant policy enforcement, fallback-on-failure, and full
audit logging (AI Job Log) — the actual adapter HTTP call is the one piece deliberately
deferred, per master plan's own "chưa cần build RAG/agent phức tạp ở bước này" guidance.
"""

import time

import frappe


def _get_tenant_policy():
	return frappe.get_single("AI Tenant Policy")


def _eligible_models(required_capabilities: str, preferred_provider: str | None = None) -> list:
	"""Router (§13.6): filters AI Model by capability match, provider.enabled, and the site's
	AI Tenant Policy allowed_providers list, ordered by priority — the preferred provider (if
	any and eligible) is tried first, everything else forms the fallback chain (§13.7)."""
	required = {c.strip() for c in required_capabilities.split(",") if c.strip()}
	policy = _get_tenant_policy()
	allowed_providers = None
	if policy.allowed_providers:
		allowed_providers = {p.strip() for p in policy.allowed_providers.split(",") if p.strip()}

	models = frappe.get_all(
		"AI Model", filters={"enabled": 1}, fields=["name", "provider", "model_code", "capabilities", "priority"], order_by="priority asc"
	)
	eligible = []
	for m in models:
		model_caps = {c.strip() for c in (m.capabilities or "").split(",") if c.strip()}
		if not required.issubset(model_caps):
			continue
		provider = frappe.db.get_value("AI Provider", m.provider, ["enabled", "provider_code"], as_dict=True)
		if not provider or not provider.enabled:
			continue
		if allowed_providers is not None and provider.provider_code not in allowed_providers:
			continue
		eligible.append(m)

	if preferred_provider:
		eligible.sort(key=lambda m: (frappe.db.get_value("AI Provider", m.provider, "provider_code") != preferred_provider, m.priority))
	return eligible


def _call_provider_adapter(provider_code: str, model_code: str, prompt_ref: str, context: dict) -> dict:
	"""MOCK adapter — see module docstring. A real implementation would dispatch on
	provider_type (OpenAI/Anthropic/Groq/OpenAI-Compatible/Local-Private/Custom) to the
	matching HTTP client, using AI Provider.base_url + a secret resolved via
	api_key_secret — never a literal key stored here."""
	return {
		"output": f"[MOCK — no live provider call made] Processed via {provider_code}/{model_code} using prompt '{prompt_ref}'. Context keys: {list(context.keys())}.",
		"tokens_used": 128,
		"cost_usd": 0.002,
	}


def run_ai_action(
	action_code: str,
	context: dict,
	user: str | None = None,
	tool_calls: list | None = None,
	retrieved_sources: list | None = None,
) -> dict:
	"""§13.2's abstraction call pattern. Every call is audit-logged to AI Job Log (§13.12)
	regardless of outcome — blocked-by-policy and failed attempts are logged too, not just
	successes.

	`tool_calls`/`retrieved_sources` are optional additions (Phase 6A / AI-DEMO-01) — they
	populate AI Job Log's own pre-existing `tool_calls`/`retrieved_sources` fields (present in
	the schema since Phase 2A but unused until now: no caller had tool-calling data to log).
	Callers that don't pass them behave exactly as before — this is additive, not a redesign;
	`_call_provider_adapter()` below is untouched."""
	user = user or frappe.session.user
	policy = _get_tenant_policy()
	action = frappe.get_doc("AI Action", action_code)

	log = {
		"doctype": "AI Job Log",
		"user": user,
		"site": frappe.local.site,
		"action": action_code,
		"input_source_refs": frappe.as_json(list(context.keys())),
		"tool_calls": frappe.as_json(tool_calls) if tool_calls else None,
		"retrieved_sources": frappe.as_json(retrieved_sources) if retrieved_sources else None,
	}

	if policy.ai_mode == "Disabled":
		log["status"] = "Blocked by Policy"
		frappe.get_doc(log).insert(ignore_permissions=True)
		frappe.throw(f"AI is Disabled for this site (AI Tenant Policy) — action '{action_code}' blocked.")

	eligible = _eligible_models(action.required_capabilities, action.preferred_provider)
	if not eligible:
		log["status"] = "Failed"
		frappe.get_doc(log).insert(ignore_permissions=True)
		frappe.throw(f"No eligible AI Model found for action '{action_code}' (required capabilities: {action.required_capabilities}).")

	prompt = frappe.get_doc("Prompt Template", action.prompt_template)
	prompt_ref = f"{prompt.template_code} v{prompt.version}"

	start = time.time()
	result, used_model, used_provider_code, used_fallback, last_error = None, None, None, False, None
	for model in eligible:
		provider_code = frappe.db.get_value("AI Provider", model.provider, "provider_code")
		try:
			result = _call_provider_adapter(provider_code, model.model_code, prompt_ref, context)
			used_model = model
			used_provider_code = provider_code
			break
		except Exception as e:  # noqa: BLE001 - deliberately broad: any adapter failure should fall through to the next eligible model
			last_error = e
			continue
	# fallback = didn't get the action's OWN preferred provider — not "wasn't first in
	# whatever list remained after filtering." A disabled preferred provider is filtered out
	# of `eligible` entirely, so the next candidate becomes index 0 and would never register
	# as a fallback under an index-based check (found via testing: an index check always
	# reported fallback_used=False whenever the preferred provider was simply unavailable).
	if used_provider_code and action.preferred_provider:
		used_fallback = used_provider_code != action.preferred_provider

	latency_ms = int((time.time() - start) * 1000)
	if result is None:
		log["status"] = "Failed"
		log["latency_ms"] = latency_ms
		frappe.get_doc(log).insert(ignore_permissions=True)
		frappe.throw(f"All eligible providers failed for action '{action_code}': {last_error}")

	log.update(
		{
			"provider": used_model.provider,
			"model": used_model.model_code,
			"prompt_template_version": prompt_ref,
			"output": result["output"],
			"tokens_used": result["tokens_used"],
			"estimated_cost_usd": result["cost_usd"],
			"latency_ms": latency_ms,
			"status": "Fallback Used" if used_fallback else "Success",
		}
	)
	log_doc = frappe.get_doc(log).insert(ignore_permissions=True)
	return {
		"output": result["output"],
		"provider": used_model.provider,
		"model": used_model.model_code,
		"fallback_used": used_fallback,
		"job_log": log_doc.name,
	}
