# WEB-04 — Supplier / RFQ Portal

Enterprise Platform Phase 7, master plan §8 (lines ~2566-2567): *"WEB-04 Supplier / RFQ Portal —
RFQ, quotation, PO, delivery, documents, qualification."*

This is a **close structural twin of WEB-03** (`nextjs-demo/web-03-dealer-portal/`) — the same
authenticated-portal architecture, reused verbatim, applied to suppliers instead of dealers. If
you've read WEB-03's README, most of this will look familiar on purpose: the hard architectural
problems (real session login without exposing the Frappe `sid` to the browser, per-account data
isolation) were already solved there and are reused here rather than re-derived.

## What this demo shows

A real supplier (Cargill Asia Trading Pte Ltd, or Nutreco South America S.A. — both real suppliers
from Golden Demo #27, Ingredient Trading) logs in and sees **only their own**:

- **RFQs** they've been invited to respond to (`Request for Quotation`)
- **Quotations** they've submitted (`Supplier Quotation`) — whether created via this portal or
  pre-existing (both suppliers already had a real `Supplier Quotation` from AI-DEMO-06's
  Procurement Assistant demo)
- **Purchase Orders** issued to them
- **Deliveries** (`Purchase Receipt`) and each shipment's own Quality Inspection result
- **Documents** — a real list of document references tied to their own relationship (RFQ
  invitations, quotations, POs, receipts, QC certificates) — not a parallel document-management
  build
- **Qualification status** — their own `quality_status` / `is_critical_supplier` (global Custom
  Fields from Golden Demo #22/Medical Device, reused by AI-DEMO-06's procurement-qualification
  workflow)

Never another supplier's data, under any circumstance — this is the single hardest constraint on
this build and the one most heavily tested (see "Isolation testing" below).

## Why Cargill / Nutreco, not new isolated suppliers

Unlike WEB-03 (which minted brand-new dealers because Golden Demo #25's own dealers carry a baked-in
"exactly N Sales Order" idempotency assumption), this build reuses Golden Demo #27's real Cargill
Asia Trading Pte Ltd / Nutreco South America S.A. suppliers directly. Both `ingredient_trading_seeds.py`
and `ai_procurement_assistant_seeds.py` were read in full before making this call: every idempotency
guard in both files is a marker/title existence check, never a "does this supplier have exactly N
documents" count — so it was confirmed safe to layer new, distinctly-titled documents on top. Reusing
these two real, richly-populated suppliers (genuine multi-currency PO/PR/PI/QI history, 2 real
pre-existing Supplier Quotations) gives the portal an immediately-plausible demo with zero fabricated
backstory. See `enterprise_core/enterprise_core/enterprise_core/supplier_portal_seeds.py`'s own module
docstring for the full reasoning, including why the isolated demo-only suppliers used by AI-DEMO-06's
and Golden Demo #22's own validation (`Mekong AgriSource Trading Co. (AI-DEMO-06)`,
`MedTech Precision Components Ltd.`) were deliberately left untouched.

## RFQ design — one supplier per RFQ, never a shared multi-supplier document

Native ERPNext's `Request for Quotation` doctype supports inviting multiple suppliers in one
document's `suppliers` child table. This build deliberately does **not** use that shape — every RFQ
here names exactly one supplier. Reasoning: a shared multi-supplier RFQ would hold another supplier's
quote_status/contact rows inside the very document THIS supplier is otherwise entitled to read, so
every read would need careful per-row scrubbing — one missed field would be a real cross-supplier
leak. One-supplier-per-RFQ removes that entire risk category by construction. The backend additionally
asserts this invariant defensively on every read (see `supplier_portal_api.py`'s module docstring) —
even a future, mistakenly-created multi-supplier RFQ could never be served through this portal. The
real trade-off: this portal cannot demonstrate ERPNext's native side-by-side RFQ comparison workflow
(multiple suppliers responding to the identical RFQ) — a deliberate simplification given the hard
isolation constraint, not an oversight.

The demo data seeds 2 RFQs: Cargill's (`WEB04-RFQ-CARGILL-01`) is answered — the seed script logs in
AS Cargill's real portal user and calls the same `submit_quotation()` the live portal exposes, so the
write path is proven end-to-end before you ever open the app. Nutreco's (`WEB04-RFQ-NUTRECO-01`) is
deliberately left unanswered, showing a genuine "invited, awaiting your response" state next to
Nutreco's own unrelated pre-existing quotation.

## Authentication design — identical to WEB-03, not redesigned

Frappe's own native session-cookie login (`POST /api/method/login`), never a hand-rolled login or a
per-supplier API key. The critical decision, reused verbatim from WEB-03: the real Frappe `sid` is
**never sent to the browser**.

1. Browser submits email/password to this app's own `/api/auth/login` Route Handler.
2. That Route Handler calls Frappe's real login endpoint **server-side** (`lib/frappeAuth.ts`), using
   Node's raw `http` module instead of `fetch()` — `fetch()`/undici forbids scripts from setting the
   `Host` header, and Frappe is multi-tenant, routing purely on that header, with no local DNS entry
   for `test.demo.local`/`pharmacountry.vn` on this machine. This workaround (and the identical one in
   `lib/api.ts` for authenticated data calls) is reused verbatim from WEB-01/02/03.
3. On success, it immediately calls `get_my_profile()` with that real `sid` — this both confirms the
   login is a genuinely provisioned supplier account (not e.g. Administrator) and fetches a CSRF token
   in the same round trip.
4. It mints an **opaque, random session token** (`lib/session.ts`), stores the real `sid` + CSRF token
   server-side, keyed by that token, and sets ONLY the opaque token as an `httpOnly` cookie on the
   browser. The browser's JS can never read it (`httpOnly`) and never sees the real Frappe `sid` at
   all, even in a network trace.

### The `globalThis` fix — reused from the start, not rediscovered

WEB-03 found and fixed a real bug: Next.js compiles Route Handlers (`app/api/.../route.ts`) and Server
Components/layouts into **separate bundles**. A plain `const sessions = new Map()` at module scope
gets duplicated across those bundles — a session created by the login Route Handler's bundle would be
invisible to the `(portal)` layout's Server Component bundle, which would always see an empty Map and
redirect straight back to `/login` even with a valid cookie. `lib/session.ts` fixes this by pinning the
Map onto `globalThis` (a true process-wide singleton), applied here from the very first commit rather
than re-discovered by failure.

### Disclosed limitation

Sessions live only in this Node process's memory — a server restart logs everyone out. Accepted for
this demo (same as WEB-03), not silently glossed over.

## Per-supplier scoping mechanism (backend)

`enterprise_core/enterprise_core/enterprise_core/supplier_portal_api.py`'s `_get_my_supplier()` is the
**only** function in that module that resolves "which supplier is this" — always from
`frappe.session.user` via a `Supplier`-scoped `User Permission` (`apply_to_all_doctypes=1`, created by
`supplier_portal_seeds.py`), never from a client-supplied parameter. Defense is layered, but NOT
uniform across doctypes — read that module's docstring for the full reasoning:

- `Supplier Quotation` / `Purchase Order` / `Purchase Receipt` / `Supplier` (each has a top-level
  `supplier` Link field): explicit filter + native `User Permission` cascade (via `frappe.get_list()`)
  + post-fetch Python re-assertion — the same 3-layer shape WEB-03 established for `Customer`.
- `Request for Quotation` (suppliers only live in a **child table** — no top-level Supplier link, so
  the native cascade cannot apply): an explicit child-table-join filter, plus a **stronger** re-
  assertion that the ENTIRE `suppliers` child table names only the resolved supplier — never a partial
  scrub. Every RFQ this platform seeds is single-supplier by construction (see above), so this check
  should always pass in practice; it exists as defense-in-depth against a future mistake.

`submit_quotation()` (the one write endpoint) runs as the real, logged-in supplier user — no
`ignore_permissions` anywhere in that call chain — so native ERPNext validation and Frappe's own
permission engine (role + User Permission) both fire for real.

## Isolation testing — empirical, not just asserted

Backend: `verify_supplier_portal_access_control()` in `supplier_portal_api.py`, called from
`verify_supplier_portal_demo()` in `api.py` (part of the platform's standard `verify_*` regression
sweep, 38 functions as of this build). It logs in as each real supplier user (`frappe.set_user`) and
empirically proves: each supplier sees only their own RFQs/quotations/POs/deliveries/qualification;
requesting the OTHER supplier's real document id while authenticated as the first is genuinely
rejected (not merely unasserted); a Cargill session attempting to submit a quotation against Nutreco's
RFQ is rejected; and an unauthenticated (Guest) request is rejected.

This was independently re-verified via curl against the actual running Next.js production build (not
just the backend function), both suppliers logged in with real sessions:

```
Cargill requesting Nutreco's RFQ detail   -> HTTP 404
Nutreco requesting Cargill's RFQ detail   -> HTTP 404
Cargill requesting her own RFQ detail     -> HTTP 200
Cargill requesting Nutreco's Quotation    -> HTTP 404
Nutreco requesting Cargill's Quotation    -> HTTP 404
Cargill requesting Nutreco's Purchase Order -> HTTP 404
Nutreco requesting Cargill's Purchase Order -> HTTP 404
Unauthenticated request to /dashboard     -> HTTP 307 (redirect to /login)
Nutreco submitting a quotation against Cargill's RFQ -> {"error":"RFQ not found."}
```

No real browser/visual screenshot QA was performed or is claimed — verification here means: `npm run
build`/`npm run lint` clean, and curl-based functional + isolation testing against the actual running
production build, on both `test.demo.local` (dev) and `pharmacountry.vn` (production) backends.

## Setup

```bash
npm install
npm run dev     # or: npm run build && npm run start
```

### Environment variables (`.env.local`)

```
FRAPPE_BASE_URL=http://localhost:8082   # the Docker stack's frontend service port
FRAPPE_SITE_HOST=test.demo.local        # or pharmacountry.vn for production
```

Frappe is multi-tenant and routes purely on the HTTP `Host` header; this machine has no local DNS
entry for either site name, so the header is set explicitly per request (see `lib/api.ts` /
`lib/frappeAuth.ts`) rather than embedded in the URL.

### Test supplier credentials

Two portal logins are seeded by `supplier_portal_seeds.py` (`seed_supplier_portal_demo_data()`,
idempotent, safe to re-run):

| Supplier | Email | Password |
|---|---|---|
| Cargill Asia Trading Pte Ltd | `supplier.cargill.portal@pharmacountry.vn` | `Demo@1234` |
| Nutreco South America S.A. | `supplier.nutreco.portal@pharmacountry.vn` | `Demo@1234` |

These are placeholder demo credentials for a non-production sandbox — documented here, never
hardcoded into any page component (the login page only shows a placeholder hint in the email field).

## Pages

| Route | What it shows |
|---|---|
| `/login` | Sign in |
| `/dashboard` | Summary stat tiles + quick links |
| `/rfqs`, `/rfqs/[name]` | RFQ invitations; the detail page embeds a "submit your quotation" form when still Pending |
| `/quotations`, `/quotations/[name]` | Submitted Supplier Quotations, RFQ-linked or not |
| `/purchase-orders`, `/purchase-orders/[name]` | Purchase Orders issued to this supplier |
| `/deliveries` | Purchase Receipts + each shipment's Quality Inspection result |
| `/qualification` | This supplier's own `quality_status` / `is_critical_supplier` + a real QC pass-rate aggregate |
| `/documents` | Document references assembled from the real records above |

## Stack

Next.js 16.3.6 (App Router, Turbopack), React 19.2.8, TypeScript 5, Tailwind CSS v4 (CSS-driven via
`@theme inline`, no `tailwind.config.*` file) — identical versions to WEB-01/02/03, for consistency
across this project's Next.js apps.

## A real, pre-existing data artifact noticed (not caused by this build)

While verifying Cargill's Purchase Orders through this portal, 2 extra Purchase Orders were found on
Cargill (`docstatus=1`, no `title`, same item/qty/rate as `IT-PO-SOY-01`) with a creation timestamp
about 2 minutes *before* the correctly-titled `IT-PO-SOY-01`/`IT-PO-SOY-02-FX`. This predates this
session (the dev site's containers had already been running for hours before this build started) and
looks like an orphan left behind by an earlier run of `ingredient_trading_seeds.py`'s `_ensure_po()`
before it reliably set `title` — `verify_ingredient_trading_golden_demo()` already tolerates it (its
own checks are keyed to specific titled documents, not counts), so it was left alone rather than
deleted. It does mean Cargill's "My Purchase Orders" page in this portal shows 4 rows instead of 2.
Flagged here rather than silently fixed, since deleting another demo's real submitted documents is
outside this build's scope.
