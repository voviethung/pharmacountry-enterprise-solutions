# Platform Hub — Master Landing Site

**This is NOT a master-plan-numbered item (not WEB-01..07).** It exists because of direct,
explicit user feedback given after WEB-01 and WEB-02 were built: "cả website demo này cũng
phải là 1 website dạng cty... mấy cục demo chỉ là khi người dùng chọn vào thôi" — the whole
demo platform should itself present as one company/product website, with the individual
industry demos being things a visitor selects into. WEB-01 and WEB-02 are real, but each is
its own disconnected site with no shared entry point describing what ENTERPRISE_PLATFORM
itself is. This hub is that shared entry point — a THIRD standalone Next.js app, sibling to
`web-01-corporate-catalog/` and `web-02-brand-website/`. See
`documents/project_status.md`'s Phase 7 section (the entry right after WEB-02) for the full
rationale and verification record.

## What this demos

- **`/` (Home)** — what ENTERPRISE_PLATFORM is (a multi-industry ERP demo platform built on
  Frappe/ERPNext v16.36.0), real platform-scale stats (industry pack count, golden demo
  count, capability engine count, live demo count), and the 2 live public demo sites.
- **`/solutions` (Industries & Solutions)** — every real, enabled Industry Pack (27 of them),
  pulled live from the platform's own `Industry Pack` DocType registry, each honestly
  labeled:
  - **Live Demo** (2 packs: Consumer Distribution, Supplement) — links directly to that
    pack's real, dedicated public Next.js site (WEB-01/WEB-02).
  - **ERP System Demo** (24 packs) — a complete, verified golden demo exists (real seeded
    data, end-to-end business flows), explored via Frappe Desk itself, not a public website
    — no fake "visit site" link is ever shown for these.
  - **Not Yet Built** (1 pack, IP-VETERINARY-BIOLOGICAL) — registered in the platform's
    configuration but has no golden demo seed data yet.
- **`/about`** — what the platform is, why this hub exists, and an explicit disclosure that
  this is a demo/portfolio project with fictional/illustrative company data, not a real
  commercial product.

## Why the data is real, not a hardcoded list

The Industries/Solutions page never hardcodes a list of industries in the frontend. It calls
a new guest-whitelisted endpoint that queries the platform's own `Industry Pack` DocType
(seeded by `enterprise_core/setup.py`'s `_INDUSTRY_PACKS` — the platform's real, canonical
industry registry, already used to pair each vertical with its Edition/roles/workspaces/seed
data). If a pack is ever added, renamed, or disabled in that registry, this page reflects it
automatically — no rebuild required.

## Architecture

```
nextjs-demo/hub-landing/                 <- this app (standalone, own lifecycle)
nextjs-demo/web-01-corporate-catalog/    <- sibling app, linked to as a "Live Demo"
nextjs-demo/web-02-brand-website/        <- sibling app, linked to as a "Live Demo"
enterprise-platform/enterprise_core/enterprise_core/enterprise_core/public_api.py
                                          <- SAME file WEB-01/WEB-02 use, extended with a
                                             "Platform Hub" section at the end
```

This app never talks to Frappe's normal authenticated REST/Desk API. It only calls 2 new
`@frappe.whitelist(allow_guest=True, methods=["GET"])` endpoints, added to the same
`public_api.py` file WEB-01/WEB-02 already introduced:

- `enterprise_core.enterprise_core.public_api.get_industry_solutions`
- `enterprise_core.enterprise_core.public_api.get_platform_stats`

### Full field-by-field API surface (nothing else is ever returned)

`get_industry_solutions()`: an array of, per real enabled Industry Pack —
`pack_code`/`pack_name`/`industry_category` (real DocType fields), `summary` (static
presentation copy — see below), `has_golden_demo` (a real computed boolean: does this pack
have at least one `Industry Pack Seed` child row, never the child rows' own content),
`has_live_demo` (whether this pack_code is in a small hardcoded allow-list of exactly 2
packs), `live_demo_label` (a static label, or `null`).

`get_platform_stats()`: `industry_pack_count`, `capability_engine_count` (a single COUNT of
enabled `Capability Engine` rows — no engine_code/engine_name ever returned),
`golden_demo_pack_count`, `live_demo_count` — four integers, never a list of records.

Never read or returned anywhere in this section: `default_edition`,
`terminology_overrides`, the `roles`/`workspaces`/`seeds` child tables' own content, or any
Company/Item/Customer/Sales/financial/transactional data. `Industry Pack`/`Capability
Engine` are pure platform configuration/registry doctypes, not business data — see
`public_api.py`'s own "Platform Hub" module docstring for the full security design,
including why `frappe.db.get_all()` (not `get_list()`) is used here, matching WEB-01/WEB-02's
own established precedent (Guest has no ambient read permission on either doctype, so
`get_list()`'s permission enforcement would return nothing).

### Presentation copy, honestly disclosed

`Industry Pack.description` is a real field but is never populated by
`setup.py`'s `seed_industry_packs()` (grep-confirmed — same platform-wide gap WEB-01/WEB-02
found for `Item.description`/`Item.image`). `_PACK_SUMMARIES` in `public_api.py` supplies a
short, factual one-line summary per pack_code, authored from this project's own real build
records (`setup.py`'s own Golden-Demo-number code comments and
`documents/project_status.md`'s Phase 1–6 entries) — never invented capability claims. It
only ever decorates a pack_code that independently, really exists and is enabled in the DB.

## Why the "ERP System Demo" cards are not clickable

The task considered linking every non-live-demo card to "the real Frappe login." This was
checked and deliberately NOT done: Frappe is multi-tenant and routes purely on the HTTP
`Host` header, and this machine has no DNS/hosts-file entry for `test.demo.local` or
`pharmacountry.vn` (confirmed: `curl http://localhost:8082/login` with no Host override
returns a real `404`, not the login page). A real browser cannot be told to send a custom
`Host` header when a person clicks a link — unlike this app's own server-side API calls,
which use Node's `http` module specifically to work around that limitation. Rather than
present a link that silently 404s for a real visitor, these 24 cards are honest,
non-clickable informational cards, with a note that the demo is explored via Frappe Desk
directly. This is a documented judgment call, not an oversight — the task explicitly allowed
either a working link or an honest non-clickable card, and only the second option is
actually true to this environment.

## Running locally

```bash
npm install
npm run dev
```

Then open the printed local URL. On this dev machine, port 3000 is already used by an
unrelated project and 3001/3002 by WEB-01/WEB-02, so this app is expected to land on
**3003** (verified live at build time).

**To see the "Live Demo" links actually work**, WEB-01 and WEB-02 must also be running
their own `npm run dev` in their own directories (see their own READMEs) — this hub does not
start or manage their lifecycle, it only links to wherever `.env.local`'s `HUB_WEB01_URL`/
`HUB_WEB02_URL` say they are.

## Environment variables (`.env.local`)

```bash
FRAPPE_BASE_URL=http://localhost:8082   # where the Frappe stack's "frontend" service is reachable
FRAPPE_SITE_HOST=test.demo.local        # which Frappe SITE to request (Host-header routed)
HUB_WEB01_URL=http://localhost:3001     # WEB-01's own current dev server URL
HUB_WEB02_URL=http://localhost:3002     # WEB-02's own current dev server URL
```

Same Host-header workaround as WEB-01/WEB-02 for the Frappe API calls (`lib/api.ts` is a
direct reuse of their own `lib/api.ts`). `HUB_WEB01_URL`/`HUB_WEB02_URL` are a pure frontend
deployment fact (which port each sibling app's `next dev` happened to bind) — if you restart
WEB-01/WEB-02 and they bind to different ports, update these two values to match.

To point this same app at the production golden-demo site instead:

```bash
FRAPPE_SITE_HOST=pharmacountry.vn
```

(`FRAPPE_BASE_URL` stays the same — confirmed both sites are served by the same Docker
Frappe stack and the same bench code, and the new `public_api.py` endpoints were verified
live and unauthenticated on both `test.demo.local` and `pharmacountry.vn`.)

## Deployment note

Per master plan §9.1 (the same rule WEB-01/WEB-02 followed), this app's lifecycle is
intentionally **separate** from the Frappe Docker stack — `frappe_docker_demo/compose.yaml`
was NOT modified, and no dedicated `compose.yaml` was added here either.

## What was NOT visually verified

Same honest limitation as WEB-01/WEB-02: this was built and verified in an environment with
no real browser available. Verification was done via `npm run dev` + `curl`, inspecting the
rendered server-side HTML directly — confirming the real Industry Pack count (27), the real
golden-demo count (26), the real capability-engine count (15), all 27 real pack_codes
rendering on the Industries page with the correct Live Demo/ERP System Demo/Not Yet Built
badge for each, and grepping the full rendered HTML of all 3 pages for sensitive-data
keywords (none found — the only "supplier"/"territory" hits are this app's own descriptive
prose, not leaked records). No actual screenshot/visual-rendering QA (CSS layout,
responsiveness, visual polish) was performed.
