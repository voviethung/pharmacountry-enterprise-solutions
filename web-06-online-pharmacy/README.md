# WEB-06 — Online Pharmacy

Phase 7 (Specialized UX/Portal/Web) item, master plan §8 lines ~2572-2573: *"WEB-06 Online Pharmacy —
Frontend riêng, tích hợp pharmacy ERP"* (a dedicated frontend, genuinely integrated with the pharmacy
ERP). The seventh Phase 7 build on this platform, and structurally the closest twin to WEB-05: an
anonymous shopper can browse, add to cart, and check out — creating a real, submitted ERPNext POS
Invoice — without ever logging in. What's new here is pharmacy-specific: real per-store, batch/expiry
honest stock, and an empirical proof that the native ERPNext batch-expiry-block mechanism still
protects this new guest-writable checkout path.

## What this is, and how it fits the rest of Phase 7

| Site | Guest access | Can write? |
|---|---|---|
| WEB-01 (Corporate Catalog) | Yes | No |
| WEB-02 (Brand Website) | Yes | No |
| WEB-03 (B2B Dealer Portal) | No (real login) | Yes |
| WEB-04 (Supplier/RFQ Portal) | No (real login) | Yes |
| WEB-05 (B2C Commerce) | Yes | Yes |
| **WEB-06 (this app)** | **Yes** | **Yes** |

WEB-06 sells the one real, presentable OTC product Golden Demo #23 (Pharmacy Chain) has — `PARA-500-
TAB` ("Paracetamol 500 mg Tablet", 1,500 VND on "Standard Selling") — from **Demo Pharmacy Chain Co.**,
specifically **Store A**, the same real store Golden Demo #23's own point-of-sale (`Pharmacy Store A
POS`) already sells from in person. Buying online and buying in-store are honestly the same real
shop's two channels.

## Read this first: this app reuses WEB-05's proven guest-checkout security model almost verbatim

Every backend endpoint this app calls lives in a new module,
`enterprise_core/enterprise_core/enterprise_core/online_pharmacy_api.py` — read its own module
docstring for the full threat model, which explicitly documents what's reused from `b2c_commerce_
api.py` vs. what's genuinely new. In short, reused unchanged:

1. **No price is ever trusted from the browser.** The cart and checkout form only ever send
   `item_code`/`qty`. The real price (and, new here, the real batch) is computed/allocated
   server-side — even a tampered request stuffing `rate`/`price`/`amount`/`batch_no` into the payload
   has zero effect. Proven empirically, not just asserted (`verify_online_pharmacy_access_control()`
   in the backend module, and the live `curl` tests below).
2. **A guest can only ever write against one isolated identity**: a dedicated Customer ("Pharmacy
   Online Guest (WEB-06 Online Orders)") and a dedicated POS Profile ("Online Pharmacy Store A POS")
   — never Golden Demo #23's own "Pharmacy Walk-in Customer" or its own "Pharmacy Store A POS" (kept
   separate specifically to avoid corrupting that golden demo's own RX05 return-lookup, which resolves
   "the" sale for its POS Profile without any ordering — see `online_pharmacy_seeds.py`'s own
   docstring for the full reasoning).
3. **Order lookup requires two factors.** After checkout you get a random, unguessable order
   reference (`WEB06-XXXXXXXXXX`) — not the real, sequential POS Invoice name. Looking up an order
   later (`/track`) requires **both** that reference **and** the phone number used at checkout.
4. **Cash on Delivery only**, with one new, disclosed wrinkle: a POS Invoice needs full payment to
   validate, so checkout is modeled as an immediately-paid, immediately-recorded real sale via the
   native "Cash" Mode of Payment — a real production COD deployment would record payment at delivery
   instead. Disclosed here and in the module docstring, the same honesty this platform applies to
   every mocked-financial-flow elsewhere.
5. **Input bounds, honestly not real anti-abuse** — same disclosed limitation as WEB-05.

The exact same narrow, documented `frappe.set_user("Administrator")` elevation pattern WEB-05 found
and proved (scoped to only the real write statements, restored in `finally`, only after every input
is already validated) is reused directly here — not rediscovered. It was needed again for a genuinely
different nested permission check this time (`get_party_account()`'s own `account_perm_check()`, not
`get_item_details()`), confirmed empirically before reusing the fix rather than assumed to be
identical.

## What's genuinely new for pharmacy

- **Real, batch-honest per-store stock.** Store A's raw `Bin.actual_qty` includes 10 units sitting in
  a deliberately-expired test batch (`RX03-EXPIRED-TEST`) that can never actually be sold — the
  catalog's `available_qty` is computed from real, non-expired batches only, net of quantities already
  committed by other real, submitted POS Invoices (see the module docstring's finding on why POS
  Invoice submission in this ERPNext version doesn't immediately post to the Stock Ledger — a real,
  proactively-designed-around native architecture fact, not a WEB-06 bug).
- **FEFO batch allocation, server-side, always.** A guest never chooses or even sees a batch before
  ordering — `_pick_batches_fefo()` always allocates the earliest-expiring, non-expired batch(es) that
  cover the requested quantity.
- **The expiry-safety proof — the single most important thing this build verifies.** A deliberate
  attempt to sell the expired `RX03-EXPIRED-TEST` batch through this new write path is rejected by the
  exact same native `StockController` `BatchExpiredError` mechanism Golden Demo #23's own RX03 test
  already proved — zero new validation code was written for this; it's the same native ERPNext
  behavior, empirically re-checked against this new checkout path.
- **Prescription-vs-OTC honesty.** Checked live before building this: `Item` in this platform's real
  data has no field distinguishing prescription-required from OTC status. Rather than inventing one
  (or a fake prescription-upload workflow), this storefront states that fact plainly and stays scoped
  to Paracetamol, which is genuinely, uncontroversially OTC — see the shop page's own "OTC — no
  prescription needed" badge and this README.
- **A real delivery address, not discarded.** A real `Address` document is created and linked to every
  order (same pattern WEB-05 established) — found and fixed as a real gap during this build's own
  review before any external testing.

## Pages

- `/` — home, featured product, how-ordering-works summary (including the batch/expiry and OTC
  disclosures).
- `/shop` — catalog with real live per-store stock (already excluding expired batches) and an "Add to
  Cart" control.
- `/cart` — client-side cart (see below), quantity edit, remove, indicative total.
- `/checkout` — guest contact form (name, phone, address, optional email) + Cash-on-Delivery
  confirmation; submits to this app's own `/api/checkout` Route Handler.
- `/confirmation` — the order reference, real confirmed total, and the real batch/expiry date each
  line was filled from, read from this browser's own `sessionStorage` right after checkout.
- `/track` — look up a past order by reference **and** phone number.

## Cart design

Identical to WEB-05: plain client-side state (`components/CartProvider.tsx`, a React Context
persisted to `localStorage`), no server-side cart/session. The price shown in the cart is a snapshot
for display only — the real price AND the real, non-expired batch allocation are always computed
server-side at checkout.

## Order confirmation / lookup design

`place_pharmacy_order` returns a random `order_token` (`WEB06-XXXXXXXXXX`) and never the real POS
Invoice name. `/track` requires **both** the order token **and** the checkout phone number — scoped
additionally to the isolated `_ONLINE_POS_PROFILE`/`_ONLINE_GUEST_CUSTOMER`, a stronger isolation than
WEB-05 had available (WEB-05 only had the Customer as an isolation axis).

## Security + expiry-safety verification performed (via real HTTP `curl`, before and after building the frontend)

```
POST place_pharmacy_order with {"rate":1,"price":1,"amount":1,"batch_no":"RX03-EXPIRED-TEST"}
  -> real order created, charged the REAL catalog price (1,350 VND w/ active 10% promotion),
     filled from a REAL non-expired batch — every tampered field ignored

Deliberate attempt to sell RX03-EXPIRED-TEST directly (server-side proof, no guest input path exists
for this — batch_no is never a guest-facing parameter)
  -> REJECTED by the native StockController BatchExpiredError mechanism, same as Golden Demo #23's
     own RX03 proof — zero new validation code needed

GET get_pharmacy_order_status with the correct token + correct phone  -> HTTP 200, real order detail
GET get_pharmacy_order_status with the correct token + WRONG phone     -> HTTP 404, generic message
GET get_pharmacy_order_status with a WRONG token + correct phone       -> HTTP 404, identical message

POST place_pharmacy_order with qty=-5                                  -> HTTP 417, rejected
POST place_pharmacy_order with a real item from a DIFFERENT storefront -> HTTP 417, rejected
POST place_pharmacy_order with qty far beyond real sellable stock      -> HTTP 417, rejected
```

All of the above were re-verified against the real, running production (`next start`) build of this
app itself, not just the raw Frappe API, on both `test.demo.local` and `pharmacountry.vn` (the
`.env.local` `FRAPPE_SITE_HOST` was temporarily swapped, rebuilt, verified — including a live
price-tampering order placed against the real `pharmacountry.vn` database and confirmed to land there,
not on `test.demo.local` — then reverted to `test.demo.local` as the checked-in dev default).

The full rendered HTML of every page was grepped for internal/sensitive keywords (`valuation_rate`,
`supplier`, `commission`, `credit_limit`, `cost_center`, `sales_person`, `Pharmacy Walk-in Customer`,
`Administrator`) — zero matches on any page.

**No real browser/visual screenshot QA was performed or is claimed** — same honest disclosure as
every prior WEB-0X app in this platform; verification here was HTTP/JSON/rendered-HTML-content-based.

## Setup

```
npm install
npm run dev      # http://localhost:3007 by default (see below)
npm run build && npm run start   # production build
npm run lint
```

### Environment variables (`.env.local`)

```
FRAPPE_BASE_URL=http://localhost:8082      # the demo stack's published Frappe frontend port
FRAPPE_SITE_HOST=test.demo.local           # Host-header-routed site (swap to pharmacountry.vn for prod)
```

Frappe is multi-tenant and routes purely on the HTTP `Host` header; this machine has no DNS entry for
either site name, so `lib/api.ts` reuses WEB-01/02/03/04/05's own Node `http`-module workaround
verbatim (plain `fetch()` forbids scripts from setting the `Host` header at all).

### One-time backend setup (already run against both sites in this build)

`online_pharmacy_seeds.py`'s `seed_online_pharmacy_setup()` must be run once via `bench execute`
(never guest-reachable) before this app's checkout can succeed — it creates the isolated POS Profile,
the isolated Customer, a small isolated top-up stock batch (protects Golden Demo #23's own flagship
batch from repeated verification-time depletion — see that module's docstring), a dedicated cashier
service User, and opens a POS Opening Entry. It is idempotent and safe to re-run.

## What this demo deliberately does NOT do

- No real payment gateway of any kind — Cash on Delivery is the only option, modeled as an
  immediately-recorded Cash sale (see point 4 above for the honest disclosure of why).
- No real anti-abuse/rate-limiting/CAPTCHA — same disclosed limitation as WEB-05.
- No prescription-upload/pharmacist-verification workflow — the real Item data has no
  prescription-vs-OTC field to honestly build one from; see "What's genuinely new for pharmacy" above.
- No cross-device/server-side cart — the cart lives only in this browser's own `localStorage`.
- No multi-store aggregation — this storefront represents Store A specifically, not "ship from
  whichever store has stock."
- No containerized deployment (`frappe_docker_demo/compose.yaml` was not touched; this app runs as a
  plain `next dev`/`next start` process, matching every prior WEB-0X app's own precedent).
- No real browser/visual screenshot QA (disclosed above).
