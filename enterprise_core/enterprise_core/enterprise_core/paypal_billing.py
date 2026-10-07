"""PayPal Subscriptions billing integration — the "Subscription/Billing" roadmap step, built on
top of the 24 real product Editions from setup.py's "chuẩn hóa Product Core" and the real
scripts/provision-tenant.sh multi-tenant provisioning step.

ARCHITECTURE: this module runs on the CONTROL-PLANE site — the one real site where PayPal
Settings is configured and Subscription records live (today: pharmacountry.vn, the platform's
own main real site) — never on a tenant's own site. A tenant's own site only ever receives a
single activate_edition() call (enterprise_core.setup.activate_edition), made here via a direct
cross-site `frappe.init(site=...)` connection — the exact same mechanism `bench --site X
execute` itself uses under the hood, valid because every tenant site lives in the same shared
bench, just its own separate database — never an HTTP round-trip to the tenant site.

SECURITY: webhook_api() below is guest-whitelisted (PayPal calls it directly, no session) and is
the one real write path a stranger could try to forge — it verifies every request's signature
against PayPal's own /v1/notifications/verify-webhook-signature endpoint BEFORE trusting a
single field of the payload, refusing anything that doesn't verify. The checkout-creation path
(create_subscription_checkout) is also guest-whitelisted (a real signup flow has no session yet)
but only ever creates a Pending-status record and a legitimate PayPal approval link — it never
activates anything by itself.

NOT YET WIRED: no public pricing/checkout PAGE calls create_subscription_checkout() yet (that's
a Next.js page, future work) — this module is the backend half, usable today via the Frappe API
directly. PayPal Settings must be configured (Client ID/Secret from
https://developer.paypal.com > Apps & Credentials, Sandbox first) and each Edition's
monthly_price/yearly_price set before any of this actually works — ensure_billing_plan() refuses
to create a Billing Plan for an unpriced Edition rather than silently charging $0.
"""

import frappe
import requests
from frappe.utils import add_months, add_years, getdate, nowdate

_DEMO_SHOWCASE_SITES = {"test.demo.local", "pharmacountry.vn"}


def _settings():
	settings = frappe.get_single("PayPal Settings")
	if not settings.client_id or not settings.get_password("client_secret"):
		frappe.throw("PayPal Settings is not configured yet (Client ID / Secret missing).")
	return settings


def _base_url(settings=None):
	settings = settings or _settings()
	return "https://api-m.sandbox.paypal.com" if settings.mode == "Sandbox" else "https://api-m.paypal.com"


def _access_token(settings=None):
	settings = settings or _settings()
	resp = requests.post(
		f"{_base_url(settings)}/v1/oauth2/token",
		auth=(settings.client_id, settings.get_password("client_secret")),
		data={"grant_type": "client_credentials"},
		timeout=20,
	)
	resp.raise_for_status()
	return resp.json()["access_token"]


def _request(method, path, body=None, settings=None):
	settings = settings or _settings()
	resp = requests.request(
		method,
		f"{_base_url(settings)}{path}",
		json=body,
		headers={
			"Authorization": f"Bearer {_access_token(settings)}",
			"Content-Type": "application/json",
			"Prefer": "return=representation",
		},
		timeout=20,
	)
	if resp.status_code >= 400:
		frappe.throw(f"PayPal API {method} {path} failed ({resp.status_code}): {resp.text[:500]}")
	return resp.json() if resp.text else {}


def _ensure_product(settings) -> str:
	if settings.product_id:
		return settings.product_id
	product = _request(
		"POST",
		"/v1/catalogs/products",
		{
			"name": "PharmaCountry Enterprise Solutions",
			"description": "Multi-industry ERP subscriptions — one Product, one Billing Plan per Edition/cycle.",
			"type": "SERVICE",
			"category": "SOFTWARE",
		},
		settings,
	)
	settings.db_set("product_id", product["id"])
	return product["id"]


def ensure_billing_plan(edition_code: str, billing_cycle: str) -> str:
	"""Returns a real PayPal Billing Plan ID for this Edition/cycle, creating it on PayPal (and
	caching the ID on the Edition doc) the first time it's needed — every later call for the
	same Edition/cycle just returns the cached ID, never creates a duplicate Plan. Refuses to
	create a Plan for an Edition that has no real price set, rather than ever charging $0."""
	if billing_cycle not in ("Monthly", "Yearly"):
		frappe.throw(f"Unknown billing_cycle '{billing_cycle}' — must be 'Monthly' or 'Yearly'.")

	edition = frappe.get_doc("Edition", edition_code)
	cached_field = "paypal_monthly_plan_id" if billing_cycle == "Monthly" else "paypal_yearly_plan_id"
	if edition.get(cached_field):
		return edition.get(cached_field)

	price_field = "monthly_price" if billing_cycle == "Monthly" else "yearly_price"
	price = edition.get(price_field)
	if not price:
		frappe.throw(
			f"Edition '{edition_code}' has no {price_field} set — set a real price before "
			f"creating a Billing Plan for it (never auto-priced at $0)."
		)

	settings = _settings()
	product_id = _ensure_product(settings)
	interval_unit = "MONTH" if billing_cycle == "Monthly" else "YEAR"

	plan = _request(
		"POST",
		"/v1/billing/plans",
		{
			"product_id": product_id,
			"name": f"{edition.edition_name} ({billing_cycle})",
			"description": edition.description or edition.edition_name,
			"billing_cycles": [
				{
					"frequency": {"interval_unit": interval_unit, "interval_count": 1},
					"tenure_type": "REGULAR",
					"sequence": 1,
					"total_cycles": 0,  # 0 = runs until cancelled, standard SaaS subscription.
					"pricing_scheme": {
						"fixed_price": {"value": f"{float(price):.2f}", "currency_code": settings.default_currency}
					},
				}
			],
			"payment_preferences": {
				"auto_bill_outstanding": True,
				"payment_failure_threshold": 2,
			},
		},
		settings,
	)

	edition.db_set(cached_field, plan["id"])
	return plan["id"]


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_subscription_checkout(
	edition_code: str,
	billing_cycle: str,
	tenant_site: str,
	company_name: str,
	customer_email: str,
	return_url: str,
	cancel_url: str,
):
	"""Starts a real PayPal subscription checkout for a prospective tenant. Returns the PayPal
	approval URL to redirect the browser to — nothing is activated yet; that only happens once
	PayPal calls webhook_api() with BILLING.SUBSCRIPTION.ACTIVATED after the customer actually
	approves and pays. Creates a local Subscription record with status "Pending" so the whole
	checkout attempt is tracked even if the customer never completes it."""
	if frappe.db.exists("Tenant Subscription", {"tenant_site": tenant_site, "status": ["in", ["Pending", "Trial", "Active"]]}):
		frappe.throw(f"'{tenant_site}' already has a pending or active subscription.")

	plan_id = ensure_billing_plan(edition_code, billing_cycle)
	settings = _settings()

	paypal_sub = _request(
		"POST",
		"/v1/billing/subscriptions",
		{
			"plan_id": plan_id,
			"subscriber": {"email_address": customer_email, "name": {"given_name": company_name}},
			"application_context": {
				"brand_name": "PharmaCountry Enterprise Solutions",
				"user_action": "SUBSCRIBE_NOW",
				"return_url": return_url,
				"cancel_url": cancel_url,
			},
		},
		settings,
	)

	edition = frappe.get_doc("Edition", edition_code)
	price_field = "monthly_price" if billing_cycle == "Monthly" else "yearly_price"

	sub = frappe.get_doc(
		{
			"doctype": "Tenant Subscription",
			"tenant_site": tenant_site,
			"company_name": company_name,
			"customer_email": customer_email,
			"edition": edition_code,
			"billing_cycle": billing_cycle,
			"status": "Pending",
			"amount": edition.get(price_field),
			"currency": settings.default_currency,
			"paypal_subscription_id": paypal_sub["id"],
			"paypal_plan_id": plan_id,
		}
	)
	sub.insert(ignore_permissions=True)
	sub.log_event("created", f"Checkout started for {tenant_site} / {edition_code} / {billing_cycle}")

	approval_url = next(
		(link["href"] for link in paypal_sub.get("links", []) if link.get("rel") == "approve"), None
	)
	if not approval_url:
		frappe.throw("PayPal did not return an approval link for this subscription.")

	return {"approval_url": approval_url, "subscription": sub.name}


def _verify_webhook_signature(headers: dict, raw_body: str, settings) -> bool:
	if not settings.webhook_id:
		frappe.log_error(
			title="PayPal webhook received with no Webhook ID configured",
			message="PayPal Settings.webhook_id is empty — cannot verify webhook authenticity. Rejecting.",
		)
		return False

	verification = _request(
		"POST",
		"/v1/notifications/verify-webhook-signature",
		{
			"auth_algo": headers.get("Paypal-Auth-Algo"),
			"cert_url": headers.get("Paypal-Cert-Url"),
			"transmission_id": headers.get("Paypal-Transmission-Id"),
			"transmission_sig": headers.get("Paypal-Transmission-Sig"),
			"transmission_time": headers.get("Paypal-Transmission-Time"),
			"webhook_id": settings.webhook_id,
			"webhook_event": frappe.parse_json(raw_body),
		},
		settings,
	)
	return verification.get("verification_status") == "SUCCESS"


def _activate_tenant_edition(tenant_site: str, edition_code: str) -> None:
	"""Cross-site call into the tenant's OWN database (same shared bench, different site) — see
	this module's own docstring for why this is the correct mechanism, not an HTTP call. Never
	raises past this function: a tenant site being briefly unreachable must not corrupt the
	control-plane's own Subscription record or crash webhook processing (PayPal retries webhooks
	on a non-2xx response, but this failure mode warrants a human looking at logs, not an
	automatic retry storm)."""
	try:
		frappe.init(site=tenant_site)
		frappe.connect()
		try:
			from enterprise_core.enterprise_core.setup import activate_edition

			activate_edition(edition_code)
		finally:
			frappe.destroy()
	except Exception:
		frappe.log_error(
			title=f"Failed to activate Edition '{edition_code}' on tenant site '{tenant_site}'",
			message=frappe.get_traceback(),
		)


def _extend_period(subscription, billing_cycle: str) -> None:
	base = getdate(subscription.current_period_end) if subscription.current_period_end else getdate()
	subscription.current_period_end = (
		add_months(base, 1) if billing_cycle == "Monthly" else add_years(base, 1)
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook_api():
	"""PayPal's own webhook endpoint for this platform — register this URL
	(https://pharmacountry.vn/api/method/enterprise_core.enterprise_core.paypal_billing.webhook_api)
	in the PayPal Developer Dashboard's Webhooks section for the same app PayPal Settings uses,
	then copy the Webhook ID it gives you into PayPal Settings.webhook_id."""
	raw_body = frappe.request.get_data(as_text=True)
	settings = _settings()

	if not _verify_webhook_signature(dict(frappe.request.headers), raw_body, settings):
		frappe.local.response.http_status_code = 400
		return {"error": "signature verification failed"}

	event = frappe.parse_json(raw_body)
	event_type = event.get("event_type", "")
	resource = event.get("resource", {})
	paypal_subscription_id = resource.get("id") or resource.get("billing_agreement_id")

	if not paypal_subscription_id:
		# Not every PayPal webhook event is subscription-shaped (PayPal sends many event types to
		# the same webhook URL) — ignore anything we can't map to a real Subscription record.
		return {"status": "ignored", "reason": "no subscription id in payload"}

	sub_name = frappe.db.get_value("Tenant Subscription", {"paypal_subscription_id": paypal_subscription_id})
	if not sub_name:
		frappe.log_error(
			title="PayPal webhook for unknown subscription",
			message=f"event_type={event_type} paypal_subscription_id={paypal_subscription_id}",
		)
		return {"status": "ignored", "reason": "unknown subscription"}

	sub = frappe.get_doc("Tenant Subscription", sub_name)

	if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
		sub.status = "Active"
		_extend_period(sub, sub.billing_cycle)
		sub.save(ignore_permissions=True)
		frappe.db.commit()
		sub.log_event(event_type, "Subscription activated by PayPal.")
		_activate_tenant_edition(sub.tenant_site, sub.edition)

	elif event_type == "PAYMENT.SALE.COMPLETED":
		if sub.status in ("Pending", "Past Due"):
			sub.status = "Active"
		_extend_period(sub, sub.billing_cycle)
		sub.save(ignore_permissions=True)
		frappe.db.commit()
		sub.log_event(event_type, "Renewal payment completed.")

	elif event_type in ("BILLING.SUBSCRIPTION.SUSPENDED", "PAYMENT.SALE.DENIED"):
		sub.status = "Past Due"
		sub.save(ignore_permissions=True)
		frappe.db.commit()
		sub.log_event(event_type, "Payment failed or subscription suspended by PayPal — needs follow-up.")

	elif event_type in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED"):
		sub.status = "Canceled"
		sub.save(ignore_permissions=True)
		frappe.db.commit()
		# Deliberately does NOT deactivate the tenant's Edition automatically — a sudden feature
		# lockout on a billing event is a real-customer-impacting action a human should confirm
		# first, not something this webhook silently does. Logged clearly for follow-up instead.
		sub.log_event(event_type, "Subscription cancelled/expired — tenant Edition NOT auto-deactivated; review manually.")

	else:
		sub.log_event(event_type, "Unhandled event type, logged for visibility only.")

	return {"status": "processed"}
