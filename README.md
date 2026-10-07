# PharmaCountry Enterprise Solutions

Monorepo for **PharmaCountry Enterprise Solutions** — a multi-industry enterprise software and SaaS platform built on Frappe/ERPNext, with the public company/product website at [pharmacountry.vn](https://pharmacountry.vn).

## Current product architecture

The platform is built around a shared product model rather than separate ERP codebases per industry:

`Capability Engines + Product Edition + Industry Pack -> Tenant Site -> Subscription`

Current platform catalog:

- **15 shared Capability Engines** covering ERP Core, CRM & Sales, Procurement, WMS & Logistics, Manufacturing/MRP, QMS, DMS & Training, LIMS, EAM/CMMS/Validation, Farm Management, Traceability, Commerce/Portal, AI & Automation, HR Performance & Competency, and R&D/RA.
- **24 commercial Editions**: 8 industry groups x Starter / Professional / Enterprise.
- **27 Industry Packs** spanning pharmaceutical, nutraceutical/cosmetics, medical device, veterinary, animal feed, livestock, aquaculture, processing, and horizontal QMS/DMS/LIMS/EAM solutions.
- **Fresh-site multi-tenant provisioning** tested end-to-end against real new Frappe sites.
- **Subscription/billing foundation** with Tenant Subscription, PayPal integration, public pricing and signup/checkout flows.

`PHARMA_MFG_STARTER` is a retained historical/sample Edition and is not a public commercial plan.

## Repository layout

- **`enterprise-platform/`** — the Frappe/ERPNext product platform (`enterprise_core`) and project/productization documentation.
- **`nextjs-demo/hub-landing/`** — the public PharmaCountry commercial Hub with Products, Industries/Solutions, Platform, Pricing, Signup, Contact and demo discovery.
- **`nextjs-demo/web-01..07-*`** — seven Next.js public/demo applications: corporate catalog, brand website, dealer portal, supplier portal, B2C commerce, online pharmacy and farm portal. They support Vietnamese/English UI and demonstrate dedicated external UX on top of the shared ERP core.

The repository was assembled from the earlier `enterprise-platform` and `nextjs-demo` histories via git subtree and is now the primary monorepo for this product effort.

## Source-of-truth documents

For architecture/product work, read:

1. `enterprise-platform/CLAUDE.md`
2. `enterprise-platform/documents/productization/04_commercial_product_architecture.md`
3. `enterprise-platform/documents/project_status.md`
4. The business-flow documentation relevant to the task

`00_demo_platform_master_plan.md` remains useful historical context, but the commercial product architecture document reflects the current Product Edition / tenant / subscription model.
