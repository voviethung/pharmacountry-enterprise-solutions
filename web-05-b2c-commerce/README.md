# WEB-05 — B2C Commerce

Phase 7 (Specialized UX/Portal/Web) item, master plan §8 lines ~2569-2570: *"WEB-05 B2C Commerce —
Consumer products."* The sixth Phase 7 build on this platform, and the first guest-facing site that
also **writes** real data: an anonymous shopper can browse, add to cart, and check out — creating a
real, submitted ERPNext Sales Order — without ever logging in.

## What this is, and how it fits the rest of Phase 7

| Site | Guest access | Can write? |
|---|---|---|
| WEB-01 (Corporate Catalog) | Yes | No |
| WEB-02 (Brand Website) | Yes | No |
| WEB-03 (B2B Dealer Portal) | No (real login) | Yes |
| WEB-04 (Supplier/RFQ Portal) | No (real login) | Yes |
| **WEB-05 (this app)** | **Yes** | **Yes** |

WEB-05 sells the same 2 real consumer products WEB-01 already catalogs and WEB-02 tells the brand
story for (`VITC-1000-EFF` — Vitamin C 1000mg Effervescent Tablet, made by Demo Supplement Co.;
`FACIAL-CLEANSER-150ML` — Facial Cleanser 150ml Bottle), sold by the same real distributor, **Demo
Consumer Distribution Co.** (Golden Demo #25), on the same public "Standard Selling" price list
WEB-01 established. This ties the whole Phase 7 story together: WEB-01 is the distributor's
corporate catalog, WEB-02 is the manufacturer's brand story, WEB-03 is the B2B dealer channel, and
WEB-05 is where an end consumer would actually buy the product online.

## The genuinely new risk this app introduces

Every backend endpoint this app calls lives in a new module,
`enterprise_core/enterprise_core/enterprise_core/b2c_commerce_api.py` — read its own module
docstring for the full threat model. In short:

1. **No price/rate is ever trusted from the browser.** The cart and checkout form only ever send
   `item_code`/`qty`. The real price is looked up server-side, by item_code, from the same current
   `Item Price` WEB-01's catalog shows — even if a tampered request stuffs a `rate`/`price`/`amount`
   field into the payload, it is silently ignored. This was proven empirically (not just asserted) —
   see `verify_b2c_commerce_access_control()` in the backend module, and the live `curl` tests below.
2. **A guest can only ever create one kind of thing**: exactly one Address + one Sales Order, always
   against a single, dedicated, isolated "Web Store Guest" Customer — never Golden Demo #25's own
   flagship dealers, never a WEB-03 portal dealer.
3. **Order lookup requires two factors.** After checkout you get a random, unguessable order
   reference (`WEB05-XXXXXXXXXX`) — not the real, sequential Sales Order name, which is never
   returned to the browser at all. Looking up an order later (`/track`) requires **both** that
   reference **and** the phone number used at checkout; either one alone returns the exact same
   generic "not found" response.
4. **Cash on Delivery only.** There is no real payment gateway anywhere in this platform and none
   was added here — this is the only payment method the checkout form offers, and it's disclosed as
   such on every relevant page.
5. **Input bounds, honestly not real anti-abuse.** Quantities are capped, item codes are checked
   against a real, data-driven safe list, a live stock check runs before the order is created, and
   contact fields are length/shape-checked. **This is not rate limiting, not a CAPTCHA, and not
   fraud detection** — a real production deployment of a guest-checkout endpoint like this would need
   all three. Documented here as honestly as this platform discloses its mocked payment/LLM/
   embeddings work elsewhere.

Two real bugs were found and fixed while building the backend (see the module docstring for the
full account): `insert(ignore_permissions=True)` on the Sales Order alone wasn't enough, because
ERPNext's own `set_missing_values()` internally re-checks permission on a *separate* `Item` document;
and the "obvious" next fix — a global `frappe.flags.ignore_permissions = True` — was proven **not**
to work either, by reading Frappe's own source rather than guessing twice. The actual fix elevates to
a narrowly-scoped `Administrator` "service account" context for exactly the 3 real write statements,
restored in a `finally` block even on failure — the same pattern a real production guest-checkout
backend would use.

## Pages

- `/` — home, featured products, how-ordering-works summary.
- `/shop` — full catalog with real live stock counts and an "Add to Cart" control per item.
- `/cart` — client-side cart (see below), quantity edit, remove, indicative total.
- `/checkout` — guest contact form (name, phone, address, optional email) + Cash-on-Delivery
  confirmation; submits to this app's own `/api/checkout` Route Handler.
- `/confirmation` — the order reference and real confirmed total, read from this browser's own
  `sessionStorage` right after a successful checkout (not re-fetched from the backend by reference
  alone — see the design note below).
- `/track` — look up a past order by reference **and** phone number.

## Cart design

The cart is plain client-side state (`components/CartProvider.tsx`, a React Context persisted to
this browser's own `localStorage`) — there is no server-side cart/session for this demo. It only
becomes a real backend interaction once at checkout time. This is a deliberate, disclosed
simplification: no cross-device cart, and clearing browser storage clears the cart. The price/name
shown in the cart is a snapshot taken from the real catalog at "Add to Cart" time, for display only
— the real, authoritative price is always recomputed server-side at checkout and can legitimately
differ (e.g. a currently-active promotion, like the real "Consumer Dist Tet Cosmetics Promotion"
pricing rule found live on Demo Consumer Distribution Co. during this build, discounted the Facial
Cleanser from 95,000 to 80,750 VND) — the UI discloses this on both the shop and checkout pages.

## Order confirmation / lookup design

`place_web_order` returns a random `order_token` (`WEB05-XXXXXXXXXX`, ~40 bits of entropy) and
**never** the real, sequential Sales Order name. The confirmation page reads that response directly
out of `sessionStorage` right after checkout (so a guest can see their own just-placed order without
a second round-trip that would need to accept the token alone). Any *later* lookup — a new browser
tab, a different day — goes through `/track`, which requires **both** the order token **and** the
checkout phone number; the backend returns the identical generic "not found" error whether the token
is wrong, the phone is wrong, or the order simply doesn't exist, so a guessed token can never be
distinguished from a genuine one with the wrong phone.

## Security verification performed (via real HTTP `curl`, before and after building the frontend)

```
POST place_web_order with {"rate": 1, "price": 1} on a real item
  -> real order created, charged the REAL catalog price (260,000 VND), tampered fields ignored

GET get_order_status with the correct token + correct phone  -> HTTP 200, real order detail
GET get_order_status with the correct token + WRONG phone     -> HTTP 404, generic message
GET get_order_status with a WRONG token + correct phone       -> HTTP 404, identical generic message
GET get_order_status with no token/phone at all               -> HTTP 404 (backend) / 400 (frontend)

POST place_web_order with qty=-3                              -> HTTP 417 ValidationError, rejected
POST place_web_order with a real but out-of-catalog item_code -> HTTP 417 ValidationError, rejected
POST place_web_order with qty far beyond real stock-on-hand   -> HTTP 417 ValidationError, rejected
```

All of the above were re-verified against the real, running production (`next start`) build of this
app itself, not just the raw Frappe API, on both `test.demo.local` and `pharmacountry.vn` (the
`.env.local` `FRAPPE_SITE_HOST` was temporarily swapped to `pharmacountry.vn`, rebuilt, verified, then
reverted to `test.demo.local` as the checked-in dev default — home/shop are statically prerendered at
build time, so this swap requires a rebuild, not just an env change).

The full rendered HTML of every page was grepped for internal/sensitive keywords
(`valuation_rate`, `warehouse`, `supplier`, `batch_no`, `commission`, `credit_limit`, `cost_center`,
`territory`, `sales_person`, other golden demos'/portals' real customer names) — zero matches on any
page.

**No real browser/visual screenshot QA was performed or is claimed** — same honest disclosure as
every prior WEB-0X app in this platform; verification here was HTTP/JSON/rendered-HTML-content-based.

## Setup

```
npm install
npm run dev      # http://localhost:3006 by default (see below)
npm run build && npm run start   # production build
npm run lint
```

### Environment variables (`.env.local`)

```
FRAPPE_BASE_URL=http://localhost:8082      # the demo stack's published Frappe frontend port
FRAPPE_SITE_HOST=test.demo.local           # Host-header-routed site (swap to pharmacountry.vn for prod)
```

Frappe is multi-tenant and routes purely on the HTTP `Host` header; this machine has no DNS entry for
either site name, so `lib/api.ts` reuses WEB-01/02/03/04's own Node `http`-module workaround verbatim
(plain `fetch()` forbids scripts from setting the `Host` header at all).

## What this demo deliberately does NOT do

- No real payment gateway of any kind — Cash on Delivery is the only option, by design.
- No real anti-abuse/rate-limiting/CAPTCHA — see point 5 above. A production deployment of a guest-
  checkout endpoint would need this.
- No cross-device/server-side cart — the cart lives only in this browser's own `localStorage`.
- No containerized deployment (`frappe_docker_demo/compose.yaml` was not touched; this app runs as a
  plain `next dev`/`next start` process, matching every prior WEB-0X app's own precedent).
- No real browser/visual screenshot QA (disclosed above).
