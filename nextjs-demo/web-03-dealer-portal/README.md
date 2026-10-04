# WEB-03 — B2B Customer / Dealer Portal

Phase 7 "Specialized UX/Portal/Web" (master plan §8, lines ~2563-2564): *"WEB-03 B2B Customer /
Dealer Portal — Catalog, price, stock, order, invoice, debt, return."*

This is the **fourth** Phase 7 frontend built in this project (after WEB-01 Corporate + Product
Catalog, WEB-02 Brand/Consumer Product Website, and the user-requested Platform Hub) and the
**first authenticated one**. WEB-01/02/Hub are all guest-only public sites with zero login. This
app is the opposite: a real dealer logs in with a real password and sees **only their own**
negotiated pricing, stock, orders, invoices, debt/credit position, and returns — never another
dealer's.

## What this demonstrates

- Real Frappe session-cookie login (native `/api/method/login`), never a hand-rolled password
  check.
- Real per-dealer data scoping, enforced by a `Customer`-scoped native Frappe `User Permission`
  (`apply_to_all_doctypes=1`) — the same mechanism Golden Demo #24 (3PL/Cold Chain) proved for
  Warehouse-scoped client isolation, reused here for Customer-scoped dealer isolation.
- Real order placement (`Sales Order`) that respects real ERPNext validation, including the
  native credit-limit block.
- Real returns (`Delivery Note` return, via ERPNext's native `make_return_doc()`).
- An empirical, two-dealer cross-access proof — not just an assertion — that dealer A cannot see
  or fetch dealer B's data under any circumstance.

## Authentication design

**Chosen: Frappe's native session-cookie login, held server-side, never exposed to the browser.**

1. The browser submits username/password to this app's own `/api/auth/login` Route Handler
   (`app/api/auth/login/route.ts`) — never directly to Frappe.
2. That Route Handler calls Frappe's real `POST /api/method/login` endpoint server-side
   (`lib/frappeAuth.ts`), obtaining a real Frappe session cookie (`sid`).
3. It immediately uses that `sid` to call `dealer_portal_api.get_my_profile()`, which both (a)
   confirms the login is a real, provisioned dealer account (rejects e.g. `Administrator`, which
   has no `Customer` User Permission) and (b) fetches a real Frappe CSRF token needed for later
   state-changing calls.
4. It creates its **own** opaque, random session token (`lib/session.ts`, `crypto.randomBytes`)
   mapped server-side to `{ frappeSid, csrfToken, user, customer, ... }`, and sends the browser
   **only that opaque token**, as an `httpOnly` cookie scoped to this app's own origin.

The real Frappe `sid` is **never sent to the browser** — not even inside an `httpOnly` cookie.
Every protected page/API route resolves the session server-side (`lib/auth.ts`'s
`requireSession()`) and uses the stored `frappeSid` to call the backend directly from the Next.js
server process. Client-side JavaScript never sees a Frappe credential, and even a full network
trace of the browser's own traffic only ever shows this app's own random token.

**Why not a per-dealer API key/secret?** Rejected as the wrong mechanism for a human logging in
with a password — there's no realistic UX for a customer typing an API secret into a login form,
and the master plan explicitly asks for a customer-facing *portal*, not a machine-to-machine
integration endpoint.

**Disclosed limitation**: `lib/session.ts`'s session store is an in-memory `Map`, pinned onto
`globalThis` (see the "real bug found" note below). It lives only in this Next.js server
process's memory — every dealer is logged out if the server restarts. A real production
deployment would back this with a shared, persistent store (Redis, or an encrypted/signed cookie
carrying the Frappe `sid` itself) so sessions survive a restart and work across multiple server
instances behind a load balancer. Accepted here as a documented demo simplification, not an
oversight.

## Real bug found + fixed during this build

Next.js compiles Route Handlers (`app/api/.../route.ts`) and Server Components/layouts into
**separate bundles**. A plain `const sessions = new Map()` at module scope in `lib/session.ts`
got **duplicated** across those bundles — each bundle held its own, independent `Map` instance in
the same Node process. A session created by `/api/auth/login`'s Route Handler bundle was
therefore invisible to the `(portal)` layout's Server Component bundle, which always saw an empty
map and redirected straight back to `/login` even immediately after a successful login with a
valid cookie. Confirmed empirically with `curl` in **both** `next dev` and a production
`next build` + `next start` — not a dev-only artifact. Fixed by pinning the `Map` onto
`globalThis`, a true process-wide singleton unaffected by how many separate module instances of
the file get bundled (the same well-known workaround used to avoid creating multiple
`PrismaClient` instances in Next.js apps).

## Per-dealer data scoping — how it's proven, not just asserted

Backend: `enterprise_core/enterprise_core/enterprise_core/dealer_portal_api.py`. Every function
resolves "which dealer" via `_get_my_customer()`, which reads `frappe.session.user` (the
framework-authenticated identity of the current request) and looks up the `Customer` a `User
Permission` links it to. **No function accepts a `customer`/`dealer_id` parameter from the
caller.** Every list/read is filtered explicitly by the resolved customer, backed by the native
User Permission cascade (which restricts `frappe.get_list()`/native permission checks on Sales
Order/Sales Invoice/Delivery Note automatically), and re-asserted in Python against every
returned row before it's ever sent back.

Backend test fixtures: `enterprise_core/enterprise_core/enterprise_core/dealer_portal_seeds.py`
creates 2 real, **isolated** dealer Customers on top of Golden Demo #25 (Demo Consumer
Distribution Co.) — deliberately NOT Golden Demo #25's own flagship Hanoi/Saigon dealers, to avoid
corrupting that golden demo's own documented idempotency assumptions:

| Dealer | Customer | Credit limit | Purpose |
|---|---|---|---|
| Alpha | `WEB03 Portal Dealer Alpha` | 20,000,000 VND | Happy path — pre-seeded order/invoice history |
| Beta | `WEB03 Portal Dealer Beta` | 3,000,000 VND | Deliberately tight — proves the real ERPNext credit-limit block through this portal's own `place_order()` |

**Empirical two-dealer proof** (`dealer_portal_api.verify_dealer_portal_access_control()`, called
from `enterprise_core.enterprise_core.api.verify_dealer_portal_demo()` — part of this platform's
standard `verify_*` regression sweep): logs in as Alpha, confirms every returned order/invoice/debt
row belongs to Alpha; logs in as Beta, same; then, still authenticated as Beta, requests one of
Alpha's real Sales Order names directly (`get_my_order_detail`) and confirms it is genuinely
rejected (`DoesNotExistError` — a plain 404, not a distinguishable "found but not yours" response
that would itself leak the order's existence); repeats in the reverse direction; and confirms a
Guest (unauthenticated) request is rejected outright.

This was **also** verified against the actual running Next.js app via `curl` (not just the
backend function in isolation) — logging in as each dealer, browsing every page, placing a real
order, filing a real return, and directly requesting the other dealer's real order URL:

```
Beta requesting /orders/<Alpha's real order id>  -> HTTP 404
Alpha requesting /orders/<Beta's real order id>  -> HTTP 404
Unauthenticated request to /dashboard             -> HTTP 307 -> /login
Cookie held by the browser                        -> our own opaque token, never a real Frappe sid
```

## Real order placement, including the real credit-limit block

Placing an order (`POST /api/orders` -> `dealer_portal_api.place_order()`) builds and submits a
real `Sales Order` with `customer` **always** the session-resolved dealer (the request body only
ever carries `item_code`/`qty` — there is no `customer` field to spoof) and runs with **no**
`ignore_permissions`, so it is genuinely permission-checked as the real logged-in dealer user.
Empirically verified live through this app's own API:

```
Alpha places a real, in-limit order (2 x VITC-1000-EFF)
  -> real Sales Order SAL-ORD-2026-00032 created, grand_total 420,000 VND

Alpha attempts a deliberately oversized order (500 x VITC-1000-EFF, ~105M VND vs a 20M limit)
  -> rejected with ERPNext's own real, unmodified message:
     "Please contact your administrator to extend the credit limits for WEB03 Portal Dealer Alpha."
```

That second message is native ERPNext's own `Customer.check_credit_limit()` validation firing for
real — not an imitation of it.

## Returns

`POST /api/returns` -> `dealer_portal_api.request_return()` re-checks the target `Delivery Note`'s
own `customer` field against the session-resolved dealer *before* doing anything, then files a
real return via ERPNext's native `make_return_doc()` (the same mechanism Golden Demo #25's own
CD05 return uses). Verified live: filing a return against Alpha's own delivery created a real
return `Delivery Note` with the correct negative amount, which then correctly appears only on
Alpha's own "My Returns" page.

## Known, disclosed simplification: the `Accounts User` role

Dealer portal users are granted 3 native ERPNext roles: `Sales User`, `Stock User`, and
`Accounts User` (see `dealer_portal_seeds.py`'s `_PORTAL_ROLES` for the full reasoning).
`Accounts User` is required because only `Accounts Manager`/`Accounts User` carry base
(permlevel-0) **read** permission on `Sales Invoice` in ERPNext's own stock role permissions —
confirmed by reading `sales_invoice.json` directly rather than assuming. This is a broader native
role than the strict minimum a production dealer login would want (it also grants visibility into
doctypes like `Payment Entry`/`Journal Entry` that aren't `Customer`-linked), but the `Customer`
User Permission still enforces the **hard** requirement — no cross-dealer leakage — for every
doctype this portal actually touches. A production build would likely replace this with a
purpose-built custom Role carrying only the exact `DocPerm`s needed.

## Setup

```bash
npm install
npm run dev     # http://localhost:3004 (or whatever port is free — see hub-landing's own
                 # .env.local comment for the sequential-port convention: WEB-01=3001,
                 # WEB-02=3002, Hub=3003, WEB-03=3004)
```

### Environment variables (`.env.local`)

| Variable | Purpose | Dev default |
|---|---|---|
| `FRAPPE_BASE_URL` | Where the Frappe HTTP frontend is reachable | `http://localhost:8082` |
| `FRAPPE_SITE_HOST` | Which Frappe site to request (Host-header routed) | `test.demo.local` |

Swap `FRAPPE_SITE_HOST` to `pharmacountry.vn` to point this same app at the production
golden-demo site instead.

### Test dealer credentials (demo only — never hardcoded into page components)

| Dealer | Email | Password |
|---|---|---|
| Alpha (happy path, generous credit) | `dealer.alpha.portal@pharmacountry.vn` | `Demo@1234` |
| Beta (tight credit limit, proves the credit-limit block) | `dealer.beta.portal@pharmacountry.vn` | `Demo@1234` |

These accounts exist on both `test.demo.local` and `pharmacountry.vn` (seeded via
`enterprise_core.enterprise_core.dealer_portal_seeds`, run once per site via
`bench execute`).

## Pages

- `/login` — real login form, posts to `/api/auth/login`.
- `/dashboard` — profile summary, debt snapshot, open-order count, quick links.
- `/catalog` — real product catalog priced at the logged-in dealer's own price list, plus real
  live stock at the shared Distribution Center warehouse.
- `/orders` — the dealer's own order history, plus a real place-order form.
- `/orders/[name]` — one order's detail — 404s if it exists but belongs to another dealer.
- `/invoices` — the dealer's own Sales Invoices, with real outstanding amounts.
- `/debt` — real outstanding balance, credit limit, available credit, utilization bar.
- `/returns` — the dealer's own returns, plus a real file-a-return form against their own
  deliveries only.

## Verification performed

- `npm run build` (production build, including TypeScript typecheck) and `npm run lint`: both
  pass clean.
- Full authenticated flow tested via `curl` against both `next start` (production build) and
  against **both** Frappe sites (`test.demo.local` and `pharmacountry.vn`, by swapping
  `FRAPPE_SITE_HOST`): login, every page, real order placement (including the real credit-limit
  block), a real return, cross-dealer 404 proof in both directions, unauthenticated-redirect
  proof, and bad-password rejection.
- Backend: `enterprise_core.enterprise_core.api.verify_dealer_portal_demo()` re-run multiple
  times on both sites (idempotent — no duplicate orders/customers/users on repeated runs); the
  full 37-function `verify_*` regression sweep (including
  `verify_consumer_dist_golden_demo()`, re-run multiple times) passes 36→37/37 on both sites after
  this addition.
- **No real browser/visual screenshot QA was performed or is claimed** — same honest disclosure
  as WEB-01/WEB-02/Hub. Verification here was `curl`/rendered-HTML-content-based (including a
  sensitive-keyword grep sweep across every authenticated page, confirming zero leakage of the
  other dealer's name/orders/invoices and no raw internal field names), not visual/layout QA.
