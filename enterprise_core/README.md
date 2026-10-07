# Enterprise Core

`enterprise_core` is the cross-industry Frappe application that provides the shared product/configuration and SaaS control-plane layer for PharmaCountry Enterprise Solutions.

It is a **fresh product app**, not a wholesale copy of ERP ENLIE. ENLIE remains a mature reference implementation; reusable capabilities are generalized deliberately into this product codebase.

## Current responsibilities

### Product catalog and configuration

- **Capability Engine registry** — 15 shared capability areas.
- **Edition** — commercial product packaging and feature/capability activation.
- **Feature Flag registry** — fine-grained switches within an Edition.
- **Industry Pack registry** — industry roles, workspaces, workflows, seed definitions and terminology/configuration.
- **Demo Template / Seed infrastructure** — idempotent platform/demo setup.

### Commercial Product Core

The real public product catalog currently contains **24 commercial Editions**:

- 8 industry groups.
- Starter / Professional / Enterprise for each group.

The eight groups are Pharmaceutical, Nutraceutical & Cosmetics, Medical Device, Veterinary, Animal Feed, Livestock, Aquaculture, and Meat & Seafood Processing.

The historical `PHARMA_MFG_STARTER` sample Edition remains for compatibility/history but is not a public commercial plan.

### Multi-tenant provisioning

Fresh-site provisioning has been exercised end-to-end against newly created Frappe sites. The provisioning path bootstraps required ERPNext fixtures/defaults, installs `enterprise_core`, activates the selected Edition and keeps public demo showcase data out of real customer tenants.

A generic bootstrap Company may be created on a brand-new headless site so ERPNext setup can complete. Replacing that placeholder with the customer's real first-run company data is a separate onboarding concern.

### Subscription and billing control plane

The app includes:

- `Tenant Subscription`
- `Subscription Event`
- `PayPal Settings`
- Edition monthly/yearly pricing fields
- PayPal Billing Plan integration
- checkout creation and webhook-driven subscription state handling

Billing/control-plane records belong on the platform control-plane site, not in each customer's tenant site.

### Public Hub APIs

The app exposes narrow guest APIs required by the public PharmaCountry Hub and the seven sibling public/demo applications. Public endpoints use explicit allow-lists and should never expose private tenant transaction data, internal credentials or cached payment-provider secrets.

The Hub currently uses platform stats, Industry Pack discovery/detail, public pricing, contact-lead creation and subscription checkout functions.

## Platform model

```text
Capability Engines
        +
Product Edition
        +
Industry Pack
        ↓
Tenant Site
        ↓
Tenant Subscription
```

Capability Engines are reusable business capabilities. Editions package them commercially. Industry Packs adapt the platform to a real operating sector. Each paying customer receives a tenant site with an active Edition and its own data/security boundary.

## Business capability migration/generalization

Do not assume every mature ENLIE business DocType automatically belongs in `enterprise_core`. Before adding a QMS, LIMS, Manufacturing, Validation, HR, R&D, RA or other capability:

1. Inspect the ENLIE implementation.
2. Separate reusable behavior from ENLIE-specific configuration/data.
3. Reuse standard ERPNext behavior where possible.
4. Generalize the reusable capability.
5. Connect it to the Capability Engine / Edition / Industry Pack model.
6. Test on a fresh tenant, not only on the platform demo sites.

## Development

Source lives under `enterprise-platform/enterprise_core/` and is used by the separate Frappe demo/dev runtime through the project's bind-mount/deployment setup.

For architecture and product decisions, read:

- `../CLAUDE.md`
- `../documents/productization/04_commercial_product_architecture.md`
- `../documents/project_status.md`

Do not use an ENLIE production/UAT database as public demo or tenant seed data.
