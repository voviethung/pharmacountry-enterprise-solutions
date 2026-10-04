# Enterprise Core

Cross-industry ERP capability platform layer for the ENTERPRISE_PLATFORM demo/product effort.

This is a **fresh** Frappe app — no code or history copied from ERP ENLIE (see
`documents/productization/01_productization_audit.md` §7, Decision 1: ENLIE stays a
read-only reference; specific DocTypes get copied and generalized on demand, never wholesale).

## What lives here (Phase 2 / EPIC DP-300)

- **Edition** — which capability engines/features a site has turned on.
- **Feature Flag registry** — fine-grained toggles within an edition.
- **Industry Pack registry** — role/workspace/workflow/seed-data templates per industry
  (Pharma, Aquaculture, Livestock, ...), per master plan §4.
- **Demo template registry** — reusable demo-site definitions built from Editions + Industry Packs.
- **Seed runner** — idempotent application of an Industry Pack's default data to a site.

None of the 15 Capability Engines' actual business DocTypes (QMS, LIMS, Farm Management, ...)
live in this app — those get added as separate apps/modules later, each declaring which
Edition/Industry Pack it belongs to. This app is the **configuration layer that turns
capability engines on and off**, not the capability engines themselves.

## Development

Source lives here on the host (`enterprise-platform/enterprise_core/`) and is bind-mounted
into the `frappe_docker_demo` stack's containers via
`overrides/compose.enterprise-core-dev.yaml` — edit here, changes are live in the container
immediately (Python) or after `bench build`/`bench migrate` (JS/DocType schema changes).

Installed on site `test.demo.local` for development (not the public `pharmacountry.vn` site —
that one stays clean until this app is stable enough to expose).
