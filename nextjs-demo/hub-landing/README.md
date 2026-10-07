# PharmaCountry Hub — Commercial Product Website

`hub-landing` is the public company/product website for PharmaCountry Enterprise Solutions at `pharmacountry.vn`.

It is no longer just a demo index. The Hub now presents the platform as a commercial multi-industry enterprise software/SaaS product, while the seven sibling Next.js apps remain concrete public/demo experiences.

## Public information architecture

- **`/`** — company/product homepage, platform scale, live demo experiences and AI/automation overview.
- **`/products`** — product-first catalog of the platform's 15 real Capability Engines.
- **`/solutions`** — industry solutions backed by the real `Industry Pack` registry.
- **`/platform`** — commercial platform architecture: Frappe/ERPNext core, Capability Engines, Editions, Industry Packs, tenant sites and subscriptions.
- **`/pricing`** — real priced Editions read from the Frappe backend.
- **`/signup`** — validates a selected public Edition and collects tenant/company/customer details.
- **`/checkout/success`** / **`/checkout/cancel`** — PayPal checkout return surfaces; payment/subscription truth comes from the backend webhook flow.
- **`/about`** — company/platform background and explicit Frappe/ERPNext technology positioning.
- **`/contact`** — public contact form writing a real CRM Lead and triggering the configured notification email path.

The header is intentionally product-first: **Products → Industries → Platform → Pricing → Contact**. The logo remains the Home link.

## Product model exposed by the Hub

The commercial product model is:

`Capability Engines + Product Edition + Industry Pack -> Tenant Site -> Tenant Subscription`

Current platform facts used by the public product story:

- 15 shared Capability Engines.
- 24 commercial Editions: 8 industry groups x Starter / Professional / Enterprise.
- 27 Industry Packs.
- Fresh tenant-site provisioning tested end-to-end as a separate backend/operations workflow.
- PayPal-backed Tenant Subscription lifecycle foundation.
- Seven sibling Next.js public/demo applications.

### Legacy sample Edition

`PHARMA_MFG_STARTER` was the original illustrative Edition used to prove the Edition mechanism before the real commercial catalog existed. It is retained in the backend for history/backward compatibility but is **not a public commercial plan**.

It is explicitly rejected/hidden at every public commercial boundary:

- `/pricing`
- `/signup`
- `/api/checkout`
- `enterprise_core.enterprise_core.paypal_billing.create_subscription_checkout`

The public catalog should show the real `PHARMA_STARTER`, `PHARMA_PROFESSIONAL`, and `PHARMA_ENTERPRISE` Editions instead.

## Backend APIs used by the Hub

The Hub calls guest-whitelisted functions from `enterprise_core` through `lib/api.ts`, using the Node `http` Host-header workaround required by the current Frappe multi-site routing environment.

Important endpoints include:

- `enterprise_core.enterprise_core.public_api.get_platform_stats`
- `enterprise_core.enterprise_core.public_api.get_industry_solutions`
- `enterprise_core.enterprise_core.public_api.get_industry_pack_detail`
- `enterprise_core.enterprise_core.public_api.get_pricing_plans`
- `enterprise_core.enterprise_core.public_api.submit_contact_lead`
- `enterprise_core.enterprise_core.paypal_billing.create_subscription_checkout`

The pricing endpoint only exposes the Edition fields required by a public pricing page. Internal PayPal plan IDs, capability child tables and feature-flag child tables are not exposed by that endpoint.

## Live/demo applications

The monorepo contains seven sibling Next.js applications:

- `web-01-corporate-catalog`
- `web-02-brand-website`
- `web-03-dealer-portal`
- `web-04-supplier-portal`
- `web-05-b2c-commerce`
- `web-06-online-pharmacy`
- `web-07-farm-portal`

A single Industry Pack may have more than one public experience, so the Hub groups live demos by pack and renders each real configured demo link under it rather than duplicating the industry card.

Deployment URLs are supplied through `HUB_WEB01_URL` ... `HUB_WEB07_URL`. There is deliberately no localhost fallback for a public visitor.

## Environment variables

Typical development configuration:

```bash
FRAPPE_BASE_URL=http://localhost:8082
FRAPPE_SITE_HOST=test.demo.local
HUB_WEB01_URL=http://localhost:3001
HUB_WEB02_URL=http://localhost:3002
HUB_WEB03_URL=http://localhost:3003
HUB_WEB04_URL=http://localhost:3004
HUB_WEB05_URL=http://localhost:3005
HUB_WEB06_URL=http://localhost:3006
HUB_WEB07_URL=http://localhost:3007
```

Actual ports/URLs are deployment facts; use the values that match the running environment.

## Billing, provisioning and activation boundaries

The public Next.js application starts checkout but is not the billing or provisioning source of truth.

1. Visitor selects a priced public Edition.
2. `/signup` re-validates the selected Edition against backend pricing data.
3. `/api/checkout` validates the request and starts PayPal checkout.
4. The control-plane Frappe site stores a Pending `Tenant Subscription`.
5. PayPal webhook events drive subscription state changes.
6. The webhook attempts to activate the purchased Edition on the named tenant site **if that site already exists**.
7. Creating a missing Frappe tenant site, publishing its DNS/Cloudflare hostname and applying first-run company/admin onboarding remain separate provisioning steps.

The browser success page therefore never claims that a tenant is already ready merely because PayPal redirected back successfully.

PayPal credentials and billing control-plane data must never be moved into public frontend code or customer tenant sites.

## Current known SaaS gaps

Do not present these as complete until implemented and runtime-qualified:

- Automatic tenant creation/orchestration triggered from the commercial lifecycle.
- Automatic Cloudflare/DNS hostname provisioning.
- First-run tenant company/admin onboarding replacing generic bootstrap defaults.
- Customer self-service account/subscription administration.
- Upgrade/downgrade/cancel orchestration.
- Full renewal, payment-failure and recovery operations.

## Development

```bash
npm install
npm run dev
```

The Hub uses Next.js App Router, TypeScript, Tailwind and `next-intl` for Vietnamese/English locale routing. Backend-reading pages use dynamic rendering where required so live Frappe data is not frozen at build time.
