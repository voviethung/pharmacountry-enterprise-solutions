# Enterprise Platform working rules

Before modifying this repository:

1. Read `documents/productization/00_demo_platform_master_plan.md` for historical architecture intent.
2. Read `documents/productization/04_commercial_product_architecture.md` for the current commercial/SaaS product model.
3. Read `documents/project_status.md` and only the business-flow documents relevant to the task.
4. Search existing code before creating new DocTypes, APIs, workflows, modules, or frontends.
5. Keep Frappe/ERPNext as the default business core. Add Next.js only for a justified external UX; add NestJS only for a justified integration/service boundary.
6. Do not copy ENLIE production data, attachments, credentials, or tenant-private records into public demos or customer sites.
7. All AI calls must go through the provider-agnostic AI Gateway and existing governance/permission model.
8. Update relevant documentation when behavior or product architecture changes.
9. Distinguish CODE COMPLETE, MIGRATED, TESTED, UAT READY and DEMO READY. Never mark work complete merely because code was written.

## Current repository truth

This monorepo now contains the active productization code:

- `enterprise_core/` — the current cross-industry Frappe app for product configuration, Industry Packs, Editions, tenant provisioning support, public APIs, subscription/billing control-plane logic, and demo/product platform behavior.
- `documents/` — architecture, audit, productization and project-status documentation.
- Sibling `../nextjs-demo/` at monorepo root — the public PharmaCountry Hub plus seven public/demo Next.js applications.

The older statement that the product app is "not inside this repo yet" is obsolete.

## ENLIE is reference-only for productization

The historical ERP implementation remains at:

`D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\`

Use it as a reference implementation for mature business flows. Do not modify the ENLIE runtime for Enterprise Platform tasks and do not wholesale-copy ENLIE code/data into `enterprise_core`. Generalize reusable capabilities deliberately.

A stale predecessor may exist at `D:\ME\ERP_ENLIE\vnpharma\vnpharma\`; treat it as legacy.

## Known name collision

Other NestJS/Next.js PharmaCountry marketplace/directory codebases under paths such as `D:\ME\Pharmacountry\`, `D:\ME\Quantri-pharmacountry\`, and `D:\ME\ERP_ENLIE\pharmacountry_be\/_fe\/_db\` are separate products. Do not merge them into this ERP/SaaS codebase merely because they share the PharmaCountry name.

## Commercial product model

The current public/commercial model is:

`Capability Engines + Product Edition + Industry Pack -> Tenant Site -> Tenant Subscription`

Current canonical platform catalog:

- 15 shared Capability Engines.
- 24 commercial Editions: 8 industry groups x Starter / Professional / Enterprise.
- 27 Industry Packs, including horizontal/cross-industry QMS, DMS, LIMS and EAM packs.
- Fresh-site tenant provisioning has been exercised end-to-end.
- PayPal subscription/billing support and public pricing/signup flows exist.

`PHARMA_MFG_STARTER` is an old illustrative sample Edition retained for backward compatibility/history. It is not a public commercial plan and must not be reintroduced into public pricing, signup or checkout flows.

## Public Hub

`nextjs-demo/hub-landing/` is the commercial company/product website, not merely a demo index. Its product-facing routes include:

- `/products`
- `/solutions` (industry solutions)
- `/platform`
- `/pricing`
- `/signup`
- `/checkout/success`
- `/checkout/cancel`
- `/about`
- `/contact`

The seven sibling Next.js applications remain live/demo experiences that prove specific public, portal, commerce, pharmacy and farm use cases.

## SaaS control plane

Subscription/billing records and PayPal configuration belong on the platform control-plane site. A customer tenant receives its own Frappe site and active Edition. Do not move billing secrets into tenant sites.

Current known lifecycle gaps should be treated as explicit roadmap work rather than silently assumed complete: automatic hostname/DNS provisioning, first-run company onboarding, customer self-service administration, upgrade/downgrade/cancel flows, and full renewal/payment-failure operations.
