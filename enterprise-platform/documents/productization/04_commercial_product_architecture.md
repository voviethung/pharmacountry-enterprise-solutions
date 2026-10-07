# COMMERCIAL PRODUCT ARCHITECTURE — PHARMACOUNTRY ENTERPRISE SOLUTIONS

**Status:** CURRENT PRODUCT MODEL  
**Purpose:** Canonical commercial/SaaS vocabulary and architecture for product, website, provisioning, billing and future development.  
**Supersedes:** Older assumptions that PharmaCountry Enterprise Solutions is only a demo/portfolio platform.

---

## 1. Product positioning

PharmaCountry Enterprise Solutions is a **multi-industry enterprise software platform**, not a pharmaceutical-only ERP and not a collection of unrelated industry-specific codebases.

The platform sells reusable business capabilities packaged into Editions and adapted by Industry Packs.

Canonical model:

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

The customer buys a usable business system/Edition, not an internal implementation concept such as a Golden Demo number or Capability Engine code.

---

## 2. Canonical entities

### 2.1 Capability Engine

A **Capability Engine** is a reusable functional product capability shared across industries.

Current registry contains 15 engines:

1. ERP Core
2. CRM & Sales
3. Procurement
4. WMS & Logistics
5. Manufacturing / MRP
6. QMS
7. DMS & Training
8. LIMS / Laboratory
9. EAM / CMMS / Validation
10. Farm Management
11. Traceability
12. Commerce / Portal
13. AI & Automation Platform
14. HR Performance & Competency
15. R&D & Regulatory Affairs (RA)

Capability Engines are the reusable building blocks of the platform. They are not the primary public pricing unit.

### 2.2 Product Edition

A **Product Edition** is a commercial package of enabled Capability Engines and feature flags.

Current real commercial catalog:

- 8 industry groups.
- 3 tiers per group: Starter, Professional, Enterprise.
- 24 commercial Editions total.

Industry groups:

- Pharmaceutical
- Nutraceutical & Cosmetics
- Medical Device
- Veterinary
- Animal Feed
- Livestock
- Aquaculture
- Meat & Seafood Processing

Tier intent:

- **Starter** — operational core needed to begin using the platform.
- **Professional** — broader commercial/operational capabilities plus the group's specialist industry engines.
- **Enterprise** — Professional plus advanced AI, HR/performance and R&D/RA capabilities where applicable.

The exact enabled-engine set is defined in code and remains the source of truth.

### 2.3 Legacy sample Edition

`PHARMA_MFG_STARTER` is the original illustrative Edition used to prove the Edition mechanism before the real Product Core catalog existed.

Rules:

- Keep it only for backward compatibility/history while existing links/settings may still reference it.
- Do not show it on public pricing.
- Do not accept it through public signup.
- Do not accept it through the public Next.js checkout boundary.
- New customer deployments use the real `PHARMA_STARTER`, `PHARMA_PROFESSIONAL` or `PHARMA_ENTERPRISE` Editions.

A future migration may retire/delete it only after checking all Link fields, settings and existing subscription references.

### 2.4 Industry Pack

An **Industry Pack** adapts the shared platform to a real industry/use case through role/workspace/workflow/seed/configuration mappings and domain terminology/data patterns.

Industry Pack is not equivalent to a separate product codebase.

Examples include pharmaceutical manufacturing, pharmacy, cold-chain/3PL, supplement, cosmetics, medical device, veterinary, feed, livestock, aquaculture and processing packs.

Horizontal/cross-industry packs such as QMS, DMS, LIMS and EAM can act as specialist add-ons rather than a vertical industry group.

### 2.5 Tenant Site

A **Tenant Site** is a customer's isolated Frappe site/data boundary.

Each customer tenant must have:

- its own site hostname;
- its own customer/business data;
- an active Product Edition;
- tenant-specific users, permissions and configuration;
- no public-demo showcase data unless explicitly created by that customer's own onboarding/import process.

Fresh-site provisioning has been exercised end-to-end. Public demo data is gated away from real customer tenant provisioning.

### 2.6 Tenant Subscription

A **Tenant Subscription** is the control-plane commercial record governing a tenant's purchased Edition and billing state.

Current status model includes:

- Pending
- Trial
- Active
- Past Due
- Canceled

The subscription record includes tenant site, company/customer identity, Edition, billing cycle, payment-provider references and event history.

Subscription/billing data belongs on the control-plane site; it is not duplicated into each customer tenant.

### 2.7 Demo

A **Demo** proves a workflow, industry implementation or external UX. It is not automatically a sellable Edition.

Demo terminology must stay separate from commercial terminology:

```text
Golden Demo / Live Demo / WEB-01..07
= proof / sales / verification experience

Edition / Subscription / Tenant
= commercial product lifecycle
```

Do not use internal demo numbers as customer-facing product names.

---

## 3. Current SaaS lifecycle

Current implemented flow:

```text
Visitor
  ↓
Products / Industry Solutions
  ↓
Pricing
  ↓
Choose Industry Edition + Starter/Professional/Enterprise
  ↓
Signup
  ↓
PayPal Checkout
  ↓
Tenant Subscription (Pending)
  ↓
PayPal event/webhook
  ↓
Subscription state / activation logic
  ↓
Tenant Site + active Edition
```

The browser success page is informational only. It must never be the source of truth for payment or tenant activation.

---

## 4. Public website information architecture

The public Hub should be product-first rather than demo-first.

Primary navigation:

```text
Products
Industries
Platform
Pricing
Contact
```

The logo acts as Home.

Recommended content hierarchy:

1. **Products** — what functional systems/capabilities PharmaCountry provides.
2. **Industries** — how the shared platform is configured for specific sectors.
3. **Platform** — architecture, multi-tenant model, AI/governance and integration story.
4. **Pricing** — real Product Editions and billing cycles.
5. **Demos** — proof that selected workflows/external experiences actually run.
6. **Company/Contact/Resources** — trust, onboarding and sales support.

Public language should not require a buyer to understand internal names such as `CE-06`, `IP-PHARMA`, Golden Demo IDs or DP task numbers.

---

## 5. Product vs Industry rule

This distinction is mandatory:

```text
PRODUCT / CAPABILITY
= what the customer needs to do
ERP, CRM, WMS, Manufacturing, QMS, DMS, LIMS, EAM, Farm, AI, etc.

INDUSTRY PACK
= how those capabilities are configured for a sector
Pharma, Veterinary, Animal Feed, Livestock, Aquaculture, etc.
```

A pharmaceutical customer may use ERP + Manufacturing + QMS + DMS + LIMS + EAM.
A distribution customer may use ERP + CRM + Procurement + WMS + Commerce.
A livestock customer may use ERP + Farm Management + Traceability + Procurement.

The platform must not imply that QMS/DMS/GMP is required for every customer.

---

## 6. Multi-tenant rules

1. Never copy ENLIE production/UAT data into customer tenants.
2. Never seed public showcase users/companies/transactions into normal customer tenants.
3. Customer sites receive platform registries and only the configuration/data justified by their Edition, Industry Pack and onboarding.
4. Billing secrets remain on the control plane.
5. Tenant permissions and data isolation are mandatory boundaries, not presentation choices.
6. Test provisioning on truly fresh sites; existing demo sites cannot prove fresh-install correctness.

---

## 7. Billing rules

Current provider integration is PayPal Subscriptions.

Rules:

- Public pricing reads real Edition prices from backend data.
- An Edition with no real price must not silently become a free plan.
- Cached PayPal plan IDs are internal data and must not be exposed by public pricing APIs.
- Checkout creates a Pending subscription; payment-provider events determine the real subscription state.
- A public frontend must never trust query parameters as the sole validation of an Edition.
- Legacy/sample Editions must not be accepted by the public commercial path.

---

## 8. Source-of-truth hierarchy for commercial work

When product/commercial architecture and older demo documents disagree, use this order:

1. Runtime behavior + current source code.
2. This commercial product architecture document.
3. Current business-flow specifications.
4. `documents/project_status.md`.
5. `00_demo_platform_master_plan.md` and older audit notes for historical context.

Do not silently restore an older demo-only assumption because an old README or comment still contains it.

---

## 9. Current known gaps / next commercial milestones

The following are not yet considered fully closed merely because the base subscription flow exists:

### 9.1 Automatic tenant hostname/DNS provisioning

Fresh Frappe-site provisioning works, but Cloudflare/DNS hostname publication still needs full automation and runtime qualification.

### 9.2 First-run tenant onboarding

A new headless site can use generic bootstrap defaults so ERPNext setup completes. A commercial onboarding flow still needs to capture and apply the customer's real:

- company legal/display name;
- abbreviation;
- country/currency;
- accounting/fiscal defaults;
- first administrator/user setup;
- industry-specific onboarding choices.

### 9.3 Customer self-service portal

Needed lifecycle actions include:

- account/company profile;
- subscription view;
- invoice/payment history where available;
- plan upgrade/downgrade;
- cancellation/reactivation;
- tenant/admin support actions.

### 9.4 Renewal and payment-failure operations

Past-due, retry, recovery, suspension/grace-period and cancellation rules require explicit operational design and UAT.

### 9.5 Production deployment qualification

Billing, provisioning, permission boundaries, backup/restore, tenant isolation and upgrade paths require production-oriented test evidence before declaring a full commercial SaaS launch complete.

---

## 10. Development decision rule

Before adding a feature, decide which layer owns it:

- Generic enterprise function → Capability Engine/core.
- Commercial packaging → Edition/Feature Flag.
- Industry adaptation → Industry Pack.
- Customer-specific configuration/data → Tenant onboarding/configuration.
- Payment/account lifecycle → SaaS control plane.
- Public/specialized user experience → Next.js frontend only when justified.

Avoid implementing the same business rule independently in multiple frontends or Industry Packs. The business source of truth should remain in the Frappe/ERPNext platform layer whenever practical.
