# WEB-07 — Farm Customer / Technical Service Portal

Phase 7 "Specialized UX/Portal/Web" (master plan §8, line ~2575-2576): *"WEB-07 Farm Customer /
Technical Service Portal — Farm account, orders, technical visits, treatment/feed recommendations,
service history."*

This is the **seventh and last** master-plan-numbered Phase 7 frontend built in this project (after
WEB-01 Corporate + Product Catalog, WEB-02 Brand/Consumer Product Website, the user-requested
Platform Hub, WEB-03 B2B Dealer Portal, WEB-04 Supplier/RFQ Portal, WEB-05 B2C Commerce, and WEB-06
Online Pharmacy). It is structurally the closest possible twin of **WEB-03** (an authenticated
portal with real per-account data isolation) — the entire authentication architecture below is
reused verbatim from WEB-03/WEB-04, not redesigned. What's genuinely new is the domain: a real
FARM customer of a veterinary distributor, not a retail dealer or a supplier.

## What this demonstrates

- Real Frappe session-cookie login (native `/api/method/login`), never a hand-rolled password
  check — identical mechanism to WEB-03/WEB-04.
- Real per-farm data scoping, enforced by a `Customer`-scoped native Frappe `User Permission`
  (`apply_to_all_doctypes=1`) — proven to cascade correctly not only to `Sales Order` (as WEB-03
  already proved) but also to `Vet Technical Visit`, a custom DocType, once that DocType was given
  a base read permission for the portal's role (see "Real bug/gap found + fixed" below).
- Real order placement (`Sales Order`) against a real veterinary product, respecting real ERPNext
  credit-limit validation.
- Real technical visit records and treatment/feed recommendations — reused from Golden Demo #10
  (Veterinary Distribution)'s own `Vet Technical Visit` DocType, not a fabricated dataset.
- An empirical, two-farm cross-access proof — not just an assertion — that farm A cannot see or
  fetch farm B's orders/technical visits/recommendations/service history under any circumstance.

## Real data this portal is built on — and why

Investigated before writing any code (see `farm_portal_seeds.py`'s own module docstring for the
full discussion):

- **Golden Demo #10 (Veterinary Distribution, master plan DEMO 16)** is the only golden demo in
  this platform with a real "technical visit" concept: `Vet Technical Visit` (its own VD07 test),
  already created and already populated with one real record for that golden demo's own dealer.
  This DocType is reused directly — no new "Farm Visit" DocType was created.
- Master plan DEMO 20 ("Feed Distribution & Dealer Management", which also names a "technical
  visit" test, FD07) was **never built** as a golden demo in this project (confirmed against
  `documents/project_status.md`'s own golden demo list, #1-#28) — so there was no second real
  source of technical-visit data to consider.
- Golden Demos #11-#14 (Pig/Poultry/Cattle/Hatchery Farm) are the farms' own INTERNAL operations,
  each its own separate Company — none of them is modeled as a Customer of Golden Demo #10's Demo
  Vet Pharma Co., so there was no real, pre-existing cross-demo link to reuse (unlike Golden Demo
  #28/Meat Processing, which genuinely sourced from Golden Demo #11's own `Pig Sale Lot`). None was
  fabricated here either — this portal's 2 farm customers are new, isolated fixtures (see below),
  honestly documented as such.

**Why 2 NEW farm Customers, not Golden Demo #10's own "VetCare Mekong Dealer Co."**: that Customer
is explicitly a DEALER (a `Sales Partner`/reseller — matching DEMO 16's own "manufacturer ->
regional dealer -> veterinary shop/farm" chain), not the FARM this master plan item specifically
asks for, and its own `verify_vet_dist_golden_demo()` asserts against that exact Customer's data —
writing new portal test data onto it would risk the same cross-demo idempotency corruption this
session's prior lessons already warn about. So WEB-07 provisions its own 2 isolated farm
Customers, in the SAME company/territory/sales person/item/warehouse (genuine reuse of real master
data) but with globally distinct names/po_no prefixes.

## Did this need a new DocType? Only a minimal, additive extension — not a new one

Per this build's own instructions, a large fabricated "technical visits" dataset was explicitly
out of scope. Since Golden Demo #10 already has a real, justified `Vet Technical Visit` DocType,
**no new DocType was created.** Two small, additive schema changes closed the only real gap (see
`bootstrap_farm_portal_doctypes.py`'s own module docstring for the full reasoning):

1. A `Custom Field` (`recommended_item`, Link -> Item) on `Vet Technical Visit` — lets a visit
   optionally name a real recommended product, structuring what was previously only free text.
2. A read-only `Custom DocPerm` granting the native `Sales User` role read access to
   `Vet Technical Visit` (previously only `System Manager` had any access at all) — this is what
   lets the native `User Permission` cascade actually restrict which visits a farm portal login can
   see, the same mechanism already relied on for Sales Order/Sales Invoice/Supplier Quotation.

Both are plain DB rows (`Custom Field`/`Custom DocPerm`), independent of the base DocType's own
JSON — they work identically on `test.demo.local` (`developer_mode`) and `pharmacountry.vn` (no
`developer_mode`).

Only **4 real Technical Visit records** were seeded (2 per farm) — a small, honestly-scoped
dataset, not a large fictional one. One visit per farm names a real recommended product; the other
is a plain follow-up with none, since a real field rep doesn't recommend a new product on every
visit.

## Authentication design

**Chosen: Frappe's native session-cookie login, held server-side, never exposed to the browser —
identical to WEB-03/WEB-04, reused verbatim.**

1. The browser submits username/password to this app's own `/api/auth/login` Route Handler
   (`app/api/auth/login/route.ts`) — never directly to Frappe.
2. That Route Handler calls Frappe's real `POST /api/method/login` endpoint server-side
   (`lib/frappeAuth.ts`), obtaining a real Frappe session cookie (`sid`).
3. It immediately uses that `sid` to call `farm_portal_api.get_my_profile()`, which both (a)
   confirms the login is a real, provisioned farm account (rejects e.g. `Administrator`, which has
   no `Customer` User Permission) and (b) fetches a real Frappe CSRF token needed for later
   state-changing calls.
4. It creates its **own** opaque, random session token (`lib/session.ts`, `crypto.randomBytes`)
   mapped server-side to `{ frappeSid, csrfToken, user, customer, ... }`, and sends the browser
   **only that opaque token**, as an `httpOnly` cookie scoped to this app's own origin.

The real Frappe `sid` is **never sent to the browser** — not even inside an `httpOnly` cookie.
Every protected page/API route resolves the session server-side (`lib/auth.ts`'s
`requireSession()`) and uses the stored `frappeSid` to call the backend directly from the Next.js
server process.

**`globalThis`-pinned session store applied from the start.** WEB-03 discovered that Next.js
compiles Route Handlers and Server Components into separate bundles, which duplicates a plain
module-level `Map`. This app's `lib/session.ts` pins the session `Map` onto `globalThis` from the
very first version of this file — not rediscovered by breaking it here.

**Disclosed limitation**: the session store is an in-memory `Map`. It lives only in this Next.js
server process's memory — every farm is logged out if the server restarts. Accepted here as a
documented demo simplification, same as every prior WEB-0X portal.

## Per-farm data scoping — how it's proven, not just asserted

Backend: `enterprise_core/enterprise_core/enterprise_core/farm_portal_api.py`. Every function
resolves "which farm" via `_get_my_farm()`, which reads `frappe.session.user` and looks up the
`Customer` a `User Permission` links it to. **No function accepts a `customer`/`farm_id`
parameter from the caller.** Every list/read (`Sales Order` AND `Vet Technical Visit`, both of
which carry a top-level `customer` Link field) is filtered explicitly by the resolved farm,
backed by the native User Permission cascade, and re-asserted in Python against every returned row
before it's ever sent back.

Backend test fixtures: `enterprise_core/enterprise_core/enterprise_core/farm_portal_seeds.py`
creates 2 real, **isolated** farm Customers on top of Golden Demo #10 (Demo Vet Pharma Co.):

| Farm | Customer | Credit limit | Purpose |
|---|---|---|---|
| Alpha (a cattle farm) | `WEB07 Portal Farm Alpha` | 10,000,000 VND | Happy path — pre-seeded order + 2 technical visits (1 with a real recommendation) |
| Beta (a swine farm) | `WEB07 Portal Farm Beta` | 2,000,000 VND | Deliberately tight — proves the real ERPNext credit-limit block through this portal's own `place_order()`; also has its own 2 technical visits |

**Empirical two-farm proof** (`farm_portal_api.verify_farm_portal_access_control()`, called from
`enterprise_core.enterprise_core.api.verify_farm_portal_demo()` — part of this platform's standard
`verify_*` regression sweep): logs in as Alpha, confirms every returned order/visit/recommendation
row belongs to Alpha; logs in as Beta, same; then, still authenticated as Beta, requests one of
Alpha's real Sales Order names directly (`get_my_order_detail`) and confirms it is genuinely
rejected (`DoesNotExistError` — a plain 404); confirms Beta's own technical-visit list contains
none of Alpha's real visit names (and vice versa); repeats in the reverse direction; and confirms a
Guest (unauthenticated) request is rejected outright.

This was **also** verified against the actual running Next.js app via `curl` (not just the backend
function in isolation) — logging in as each farm, browsing every page, placing a real order, and
directly requesting the other farm's real order URL, on **both** `test.demo.local` and
`pharmacountry.vn`:

```
Beta requesting /orders/<Alpha's real order id>  -> HTTP 404
Alpha requesting /orders/<Beta's real order id>  -> HTTP 404
Unauthenticated request to /dashboard             -> HTTP 307 -> /login
Bad password                                      -> HTTP 401, rejected
Alpha's rendered pages grepped for "Beta"/credit_limit/Administrator -> zero matches
Beta's rendered visits page mentions "swine"/"weaner", never "mastitis" (Alpha's own visit topic)
```

## Real order placement, including the real credit-limit block

Placing an order (`POST /api/orders` -> `farm_portal_api.place_order()`) builds and submits a real
`Sales Order` for the ONE real sellable product this portal offers (`OXYTET-200-INJ`, Golden Demo
#9/#10's own real finished good) with `customer` **always** the session-resolved farm and `rate` a
server-side constant — the request body only ever carries `qty`, so there is nothing for a client
to spoof. Runs with **no** `ignore_permissions`, so it is genuinely permission-checked. Empirically
verified live:

```
Alpha places a real, in-limit order (2-3 x OXYTET-200-INJ) -> real Sales Order created
Beta attempts a deliberately oversized order (50 x OXYTET-200-INJ, ~11M VND vs a 2M limit)
  -> rejected with ERPNext's own real, unmodified message:
     "Please contact your administrator to extend the credit limits for WEB07 Portal Farm Beta."
```

That message is native ERPNext's own `Customer.check_credit_limit()` validation firing for real.

## Setup

```bash
npm install
npm run dev     # http://localhost:3008 (or whatever port is free — see hub-landing's own
                 # .env.local comment for the sequential-port convention: WEB-01=3001,
                 # WEB-02=3002, Hub=3003, WEB-03=3004, WEB-04=3005, WEB-05=3006, WEB-06=3007,
                 # WEB-07=3008)
```

### Environment variables (`.env.local`)

| Variable | Purpose | Dev default |
|---|---|---|
| `FRAPPE_BASE_URL` | Where the Frappe HTTP frontend is reachable | `http://localhost:8082` |
| `FRAPPE_SITE_HOST` | Which Frappe site to request (Host-header routed) | `test.demo.local` |

Swap `FRAPPE_SITE_HOST` to `pharmacountry.vn` to point this same app at the production
golden-demo site instead.

### Test farm credentials (demo only — never hardcoded into page components)

| Farm | Email | Password |
|---|---|---|
| Alpha (happy path, generous credit, cattle farm) | `farm.alpha.portal@pharmacountry.vn` | `Demo@1234` |
| Beta (tight credit limit, proves the credit-limit block, swine farm) | `farm.beta.portal@pharmacountry.vn` | `Demo@1234` |

These accounts exist on both `test.demo.local` and `pharmacountry.vn` (seeded via
`enterprise_core.enterprise_core.farm_portal_seeds`, run once per site via `bench execute`, called
automatically by `enterprise_core.enterprise_core.api.verify_farm_portal_demo()`).

## Pages

- `/login` — real login form, posts to `/api/auth/login`.
- `/dashboard` — profile summary, order/visit/recommendation counts, quick links.
- `/orders` — the farm's own order history, plus a real place-order form for the one real
  orderable product.
- `/orders/[name]` — one order's detail — 404s if it exists but belongs to another farm.
- `/visits` — the farm's own real Technical Visit records (products discussed, notes, follow-up
  date, recommended item if any).
- `/recommendations` — the subset of the farm's own visits that named a real recommended product,
  enriched with that product's real veterinary fields (target species, indication, withdrawal
  period).
- `/history` — a unified chronological timeline merging the farm's own orders and technical visits.

## Verification performed

- `npm run build` (production build, including TypeScript typecheck) and `npm run lint`: both
  pass clean.
- Backend endpoints tested directly via `curl` (guest rejection, login, profile, orders, technical
  visits, recommendations, service history, place_order, credit-limit block, cross-farm rejection)
  **before** the frontend was built.
- Full authenticated flow tested via `curl` against the running production build (`next start`) on
  **both** Frappe sites (`test.demo.local` and `pharmacountry.vn`, by swapping `FRAPPE_SITE_HOST`
  and rebuilding): login, every page, real order placement, cross-farm 404 proof in both
  directions, unauthenticated-redirect proof, bad-password rejection, and a full sensitive-keyword
  grep sweep of every rendered page (zero leaks of the other farm's name/orders/visits).
- Backend: `enterprise_core.enterprise_core.api.verify_farm_portal_demo()` re-run multiple times on
  both sites (idempotent — no duplicate farms/orders/visits/users on repeated runs); the full
  41-function `verify_*` regression sweep (including `verify_vet_dist_golden_demo()`, re-run twice)
  passes 41/41 on both sites after this addition.
- **No real browser/visual screenshot QA was performed or is claimed** — same honest disclosure as
  every prior WEB-0X app. Verification here was `curl`/rendered-HTML-content-based, not
  visual/layout QA.
