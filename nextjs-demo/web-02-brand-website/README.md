# WEB-02 — Brand / Consumer Product Website

Enterprise Platform, **Phase 7 — Specialized UX/Portal/Web** (master plan §8, "WEB-02 Brand /
Consumer Product Website — for a supplement/cosmetics/veterinary brand"). This is the
platform's SECOND Next.js/frontend deliverable, sibling to `nextjs-demo/web-01-corporate-
catalog/`, deployed independently of the Frappe/ERPNext Docker stack (per master plan §9.1:
"do not add Next.js into `frappe_docker_demo/compose.yaml` just to complete the stack").

## What this demos, and why it's different from WEB-01

WEB-01 is a **distributor's** B2B-flavored corporate site + flat price-list catalog (Golden
Demo #25, "Demo Consumer Distribution Co."). WEB-02 is a genuine **consumer brand's own
marketing site** — brand story, a single narrative hero-product page, and a "where to buy"
call to action, with no price list anywhere. It is built for **Demo Supplement Co.** (Golden
Demo #19/#20, IP-SUPPLEMENT), the real ORIGINAL MANUFACTURER of `VITC-1000-EFF` ("Vitamin C
1000mg Effervescent Tablet") — one of the same two products WEB-01's distributor resells — but
told entirely from the brand's own point of view (formula, quality, story), not the
distributor's (price).

Pages:

- **`/` (Home)** — brand tagline/mission, a hero-product teaser, and a "lab-verified quality"
  trust banner using a real, live batch test result.
- **`/product`** — the full hero-product narrative: benefits, an allergen-transparency notice,
  the real published formula (ingredient list with real formula-weight percentages), and the
  real lab specification + latest verified test result.
- **`/our-story`** — brand mission and formulation philosophy.
- **`/where-to-buy`** — a "where to buy" CTA. Deliberately narrative-only (see below) — it does
  not integrate with or duplicate WEB-01's real distributor catalog, but does mention it by
  name for context.

## Why Demo Supplement Co. over Cosmetics or Veterinary

The master plan names 3 possible verticals ("supplement/cosmetics/veterinary brand"). All 3
were checked (grepped `supplement_seeds.py`/`cosmetics_seeds.py`/`vet_mfg_seeds.py`/
`vet_dist_seeds.py`, then confirmed live values via `bench execute` against
`test.demo.local`) before picking one:

- **Demo Cosmetics Co.** (`FACIAL-CLEANSER-150ML`) — a real consumer finished good, but no
  vertical-specific descriptive field beyond generic `has_batch_no`/`shelf_life_in_days` — no
  real data to build a distinctive brand story on besides invented copy.
- **Demo Vet Pharma Co.** (`OXYTET-200-INJ`) — the richest CUSTOM fields of the three
  (`target_species`, `indication`, `withdrawal_period_days`), but those are
  clinical/regulatory label fields for a prescription veterinary injectable sold to
  dealers/vets — a lifestyle "brand site" for it would ring false.
- **Demo Supplement Co. (`VITC-1000-EFF`) — the one picked.** A real, everyday consumer
  wellness product, AND — once the full manufacturing chain is considered, not just the Item
  record — the richest genuinely REAL, verifiable data of the three: a real active Formula
  (BOM) with real ingredient proportions, a real `contains_allergen` flag (Soy Lecithin), and
  a real LIMS Specification + Approved LIMS COA test result (Vitamin C Content, published spec
  950–1050 mg/tablet, latest verified batch tested at 1002 mg/tablet, live-confirmed on both
  `test.demo.local` and `pharmacountry.vn`). That's a genuine, data-backed "lab verified
  quality" claim, not invented copy — see `public_api.py`'s own module docstring (WEB-02
  section) for the full field-by-field reasoning.

## Architecture

```
nextjs-demo/web-02-brand-website/        <- this app (standalone, own lifecycle)
enterprise-platform/enterprise_core/enterprise_core/enterprise_core/public_api.py
                                          <- SAME file WEB-01 uses, extended with a
                                             WEB-02 section (not a separate module —
                                             it's the same guest-only security pattern,
                                             just a different company/item)
```

This app never talks to Frappe's normal authenticated REST/Desk API. It only calls 2 new
`@frappe.whitelist(allow_guest=True, methods=["GET"])` endpoints, added to the same
`public_api.py` file WEB-01 already introduced:

- `enterprise_core.enterprise_core.public_api.get_brand_profile`
- `enterprise_core.enterprise_core.public_api.get_brand_product`

### Full field-by-field API surface (nothing else is ever returned)

`get_brand_profile()`: `company_name`, `country`, `currency` (real Company fields) +
`tagline`/`mission`/`philosophy` (static brand copy, see "Presentation copy" below).

`get_brand_product()`:
- `item_code`, `item_name`, `shelf_life_days`, `contains_allergen` — real `Item` fields.
  `stock_uom` and `item_group` exist on the real Item but are deliberately NOT exposed — not
  consumer-meaningful, so left out rather than included just because they aren't sensitive.
- `category`, `tagline`, `story`, `benefits` — static presentation copy (see below).
- `ingredients: [{item_code, name, percent_of_formula, note}]` — `item_code`/`name` real
  (Item), `percent_of_formula` a real computed value (this ingredient's qty / total formula
  qty on the CURRENT active+default BOM only), `note` static flavor text.
- `quality: {specification: [{parameter_name, unit, min_value, max_value}], verified_on,
  latest_tested_values: {parameter_name: value}}` — all real: the Effective `LIMS
  Specification`'s parameters, and the latest Approved `LIMS COA`'s test result for the SAME
  item (scoped via `LIMS Sample.item_name`, since this platform's shared LIMS chain serves
  multiple golden demos on the same doctypes).

Never read or returned anywhere: cost/valuation rate, stock qty, warehouse, BOM
cost/rate/amount, supplier, batch/lot/serial number, customer/dealer/territory/commission
data, analyst/reviewer/instrument identity, or any other internal Company/Item/Manufacturing
field. See `public_api.py`'s own module docstring (WEB-02 section) for the full security
design and field-by-field justification — same discipline WEB-01 already established, just
extended to a second company/item.

### Presentation copy, honestly disclosed

`Item.description`/`Item.image` are empty on this item too (same platform-wide gap WEB-01
found on its own items). `tagline`/`story`/`benefits`/`mission`/`philosophy`/ingredient
`note` text are short, clearly-labeled PRESENTATION copy authored for this demo in
`public_api.py`'s `_BRAND_COPY`/`_PRODUCT_COPY`/`_INGREDIENT_NOTES` dicts — marketing text, not
a claim of real ERP data. They only ever decorate the real item/ingredient codes returned by
the real, data-driven queries above (they cannot be attached to any other item).

All data fetching happens **server-side** (Next.js Server Components), both for SEO and so no
Frappe URL/response is ever visible in client-side network calls.

## Running locally

```bash
npm install
npm run dev
```

Then open the printed local URL (defaults to `http://localhost:3000`, but will pick the next
free port if something else on the machine — e.g. WEB-01's own dev server — is already using
it).

## Environment variables (`.env.local`)

```bash
FRAPPE_BASE_URL=http://localhost:8082   # where the Frappe stack's "frontend" service is reachable
FRAPPE_SITE_HOST=test.demo.local        # which Frappe SITE to request (Host-header routed)
```

Same Host-header workaround as WEB-01: Frappe is multi-tenant and routes purely on the HTTP
`Host` header, and this machine has no DNS/hosts-file entry for `test.demo.local` or
`pharmacountry.vn`. `lib/api.ts` is a direct reuse of WEB-01's own `lib/api.ts` — it connects
to `FRAPPE_BASE_URL` but sends `FRAPPE_SITE_HOST` as an explicit `Host` header via Node's
`http` module (plain `fetch()` can't do this — the WHATWG Fetch spec forbids scripts from
overriding `Host`).

To point this same app at the production golden-demo site instead:

```bash
FRAPPE_SITE_HOST=pharmacountry.vn
```

(`FRAPPE_BASE_URL` stays the same — confirmed both sites are served by the same Docker Frappe
stack and the same bench code, so no separate "sync" step was needed beyond a
`bench --site <site> clear-cache` after the backend code change.)

## Deployment note

Per master plan §9.1, this app's lifecycle is intentionally **separate** from the Frappe
Docker stack (`frappe_docker_demo/compose.yaml` was NOT modified, and no dedicated
`compose.yaml` was added for this app either — a plain `next dev`/`next start` process is
sufficient for this demo stage, matching WEB-01's own precedent).

## What was NOT visually verified

Same honest limitation as WEB-01: this was built and verified in an environment with no real
browser available. Verification was done via `npm run dev` + `curl`, inspecting the rendered
server-side HTML and the underlying JSON API responses directly — confirming real data (the
real item name, real formula percentages, the real 1002 mg/tablet lab result) renders
correctly on all 4 pages, on both `test.demo.local` and `pharmacountry.vn`, and grepping the
full rendered HTML of all 4 pages for every internal/sensitive keyword this build's
constraints forbid. No actual screenshot/visual-rendering QA (CSS layout, responsiveness,
visual polish) was performed.
