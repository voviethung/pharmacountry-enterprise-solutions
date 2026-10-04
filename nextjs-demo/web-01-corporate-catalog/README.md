# WEB-01 — Corporate + Product Catalog

Enterprise Platform, **Phase 7 — Specialized UX/Portal/Web** (master plan §8, "WEB-01
Corporate + Product Catalog — for a factory/distributor"). This is the platform's first
Next.js/frontend deliverable — a standalone, publicly-accessible corporate website and
product catalog, deployed independently of the Frappe/ERPNext Docker stack (per master plan
§9.1: "do not add Next.js into `frappe_docker_demo/compose.yaml` just to complete the
stack").

## What this demos

A real corporate/catalog site for **Demo Consumer Distribution Co.** (Golden Demo #25,
Consumer Health/Cosmetics Distribution, IP-CONSUMER-DIST) — a real distributor company
already seeded in this platform's ERP data. It shows:

- **Home page** — real company name/country/currency plus featured products.
- **Product catalog** (`/catalog`) — real Items this company actually distributes, with real
  selling prices.
- **Product detail pages** (`/catalog/[itemCode]`) — full description + price + unit for one
  real Item.

Why this company: checked 3 candidates (Golden Demo #1 flagship pharma manufacturer, Golden
Demo #21 cosmetics manufacturer, Golden Demo #25 consumer distributor) before picking one —
only Golden Demo #25 has real, presentable **selling** price data (`Item Price` on the public
"Standard Selling" price list), and it's a genuine distributor, matching WEB-01's own spec
text. Full reasoning is documented in the backend module's docstring (see below).

## Architecture

```
nextjs-demo/web-01-corporate-catalog/   <- this app (standalone, own lifecycle)
enterprise-platform/enterprise_core/enterprise_core/enterprise_core/public_api.py
                                         <- new guest-whitelisted Frappe API this app calls
```

This app never talks to Frappe's normal authenticated REST/Desk API. It only calls 3 new
`@frappe.whitelist(allow_guest=True, methods=["GET"])` endpoints in `public_api.py`:

- `enterprise_core.enterprise_core.public_api.get_company_profile`
- `enterprise_core.enterprise_core.public_api.get_catalog_items`
- `enterprise_core.enterprise_core.public_api.get_item_detail?item_code=...`

Every one of those endpoints returns a hand-picked, explicit field subset — never an internal
field (no cost/valuation rate, stock qty, warehouse, supplier, batch/lot, customer/dealer,
commission, or financial-account data). See that file's own module docstring for the full
security design and field-by-field justification.

All data fetching happens **server-side** (Next.js Server Components), both for SEO and so no
Frappe URL/response is ever visible in client-side network calls.

## Running locally

```bash
npm install
npm run dev
```

Then open the printed local URL (defaults to `http://localhost:3000`, but will pick the next
free port — e.g. `3001` — if something else on the machine is already using it).

## Environment variables (`.env.local`)

```bash
FRAPPE_BASE_URL=http://localhost:8082   # where the Frappe stack's "frontend" service is reachable
FRAPPE_SITE_HOST=test.demo.local        # which Frappe SITE to request (Host-header routed)
```

Frappe is multi-tenant and routes purely on the HTTP `Host` header (there's no separate
port/path per site). This machine has no DNS/hosts-file entry for `test.demo.local` or
`pharmacountry.vn`, so `lib/api.ts` connects to `FRAPPE_BASE_URL` but sends `FRAPPE_SITE_HOST`
as an explicit `Host` header on every request (via Node's `http` module — the Fetch spec
forbids scripts from overriding `Host` on `fetch()`, so plain `fetch()` can't do this).

To point this same app at the production golden-demo site instead of the dev site, change:

```bash
FRAPPE_SITE_HOST=pharmacountry.vn
```

(`FRAPPE_BASE_URL` stays the same as long as both sites are served by the same Docker Frappe
stack, which is the case in this project — confirmed via `bench --site all list-apps`.)

If you run this app on a different machine than the Frappe stack, change `FRAPPE_BASE_URL` to
wherever that stack's HTTP frontend is actually reachable from.

## Deployment note

Per master plan §9.1, this app's lifecycle is intentionally **separate** from the Frappe
Docker stack (`frappe_docker_demo/compose.yaml` was NOT modified). For this demo stage, a
plain `next dev`/`next start` process is sufficient — no dedicated `compose.yaml` was added
for this app, since the master plan explicitly warns against over-building deployment
infrastructure the demo doesn't yet need ("Khong them Next.js/NestJS vao compose nay chi de
'du stack'"). If/when this needs real containerized deployment, give it its own compose file
here, never the Frappe stack's.

## What was NOT visually verified

This was built and verified in an environment with no real browser available — verification
was done via `npm run dev` + `curl`, inspecting the rendered server-side HTML and the
underlying JSON API responses directly (confirming real data renders correctly, and that
requesting an out-of-catalog item code correctly 404s rather than leaking unrelated ERP data).
No actual screenshot/visual-rendering QA (CSS layout, responsiveness, visual polish) was
performed — only that the correct real data reaches the page and no sensitive field appears
anywhere in the HTML or JSON.
