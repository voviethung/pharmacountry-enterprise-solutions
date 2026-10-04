# PharmaCountry Enterprise Solutions

Monorepo for PharmaCountry Enterprise Solutions — a multi-industry ERP platform built on Frappe/ERPNext, and its public-facing web presence at [pharmacountry.vn](https://pharmacountry.vn).

## Layout

- **`nextjs-demo/`** — the public Hub (pharmacountry.vn) and the 7 live demo sub-sites (corporate catalog, brand website, dealer portal, supplier portal, B2C commerce, online pharmacy, farm portal), all Next.js apps with full Vietnamese/English bilingual support.
- **`enterprise-platform/`** — the ERPNext/Frappe backend customizations (`enterprise_core` app) and project documentation.

Each directory was merged in with its full original commit history via `git subtree`.
