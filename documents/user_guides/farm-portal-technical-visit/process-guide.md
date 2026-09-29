# Process Guide — Farm Customer Portal: Technical Visit to Order, and Account Isolation (End to End)

## Purpose

This is the full story of how a farm customer's relationship with the business flows through the self-service portal — from a field representative's visit and product recommendation, through the farm reviewing and acting on it, to placing an order — and, just as importantly, the real guarantee that one farm's data is never visible to another.

## Prerequisites

- Two demo farm accounts: `farm.alpha.portal@pharmacountry.vn` (Farm Alpha, a cattle farm, generous credit limit) and `farm.beta.portal@pharmacountry.vn` (Farm Beta, a swine farm, tighter credit limit), both password `Demo@1234`.
- The portal is a separate web application from the internal back-office Desk, backed by the same underlying real customer/order records.

## Roles involved

| Role | Responsibility |
|---|---|
| Field representative (internal staff) | Visits the farm, records notes and any product recommendation. |
| **Farm Customer (Alpha or Beta)** | Logs into the portal, reviews visits/recommendations, places and reviews orders — for their own farm only. |

## The process, step by step

### 1. A field representative visits the farm

Before anything appears in the portal, a real **Vet Technical Visit** record is created (by internal staff, not the farm) — capturing the visit date, which sales person conducted it, what was discussed, any notes, a follow-up date, and — for some visits — a specific **recommended product**, linked as a real catalog item rather than typed as free text.

### 2. The farm logs into its own portal

The farm's own staff log in using their portal account (e.g. Farm Alpha's account). Behind the scenes, the portal's login uses the platform's real, native session-based authentication — the same underlying mechanism as the back-office system, just wrapped in the portal's own separate web application. The farm's real session token never leaves the server; the browser only holds an opaque, unusable-elsewhere token.

The one thing every function in the portal does before showing anything is figure out **which farm is asking** — by looking at who's logged in, never by trusting anything the farm's own browser claims about its identity. This single check is what everything else in the portal's data isolation depends on.

### 3. The farm reviews its order history

Opening **My Orders** shows every real Sales Order tied to that farm's account, most recent first. Opening a specific order shows its full detail — items, quantities, rates, totals.

### 4. The farm reviews its technical visits and recommendations

Opening **Technical Visits** shows every visit recorded for that farm. **My Recommendations** narrows this to visits that included an actual recommended product, and enriches each one with that product's real details (which species it's for, what it's indicated for, and its withdrawal period) — so the farm can see not just *that* something was recommended, but *why*.

### 5. The farm places a new order

Using the one real, sellable product this portal currently offers (an injectable veterinary antibiotic), the farm enters a quantity and submits. The order is created as a genuine Sales Order:
- The customer on the order is always the farm that's actually logged in — never something the farm's own request could override.
- The unit price is fixed by the system — the farm's request only ever specifies quantity, so there's nothing for a customer to under-price.
- The order runs through the platform's real, standard validation — including its credit-limit check. If the order would push the farm's account past its credit limit, it is blocked, exactly as it would be for any sales order placed anywhere else in the system.

### 6. The farm reviews its combined service history

**Service History** merges the farm's own orders and technical visits into one chronological timeline — assembled entirely from data already scoped to that farm, never a separately maintained or riskier data source.

### 7. Switching farms proves the isolation is real

Logging out and logging in as a different farm (Beta instead of Alpha) shows a completely different set of orders and visits — nothing carries over, and nothing from the previous farm's session lingers. To make the guarantee concrete rather than just assumed:
- While logged in as Beta, attempting to look up one of Alpha's real order reference numbers fails with an ordinary "not found" — not a distinguishable "found, but access denied" message. This is deliberate: an error message that confirmed *something* existed under that reference would itself leak information.
- The reverse direction is checked too: Alpha cannot look up any of Beta's real reference numbers either.
- An unauthenticated visitor (not logged in at all) is rejected outright when trying to reach any of this data — there's no "logged out but still see something" state.

This isolation has been independently, empirically tested — logging in as each real farm account and attempting exactly these cross-account lookups — rather than simply assumed to work because the code looks correct.

## Reports

- **My Orders** / order detail, per farm.
- **Technical Visits** and **My Recommendations**, per farm.
- **Service History**, the unified per-farm timeline.

## Common errors across the process

| Message / situation | Root cause |
|---|---|
| "Order not found" for a reference number you know exists (for another farm) | Deliberate — the portal never reveals whether a record exists if it doesn't belong to you. |
| A new order is blocked for exceeding the credit limit | The same real financial control used platform-wide; each farm's limit is set individually (in this demo, Beta's is deliberately tighter than Alpha's). |
| Trying to reach any portal function while logged out | Rejected outright — there is no guest-accessible version of any farm-specific data. |

## FAQ

**Is the account-isolation guarantee just a filter on what's displayed, or something deeper?** Deeper — the system checks farm ownership at more than one layer (who's allowed to even query this type of record, an explicit filter naming the exact farm, and a final re-check that every single row actually belongs to that farm before it's returned), so even a configuration mistake at one layer couldn't silently leak another farm's data through.

**Can a farm see prices or products meant for a different customer segment?** The catalog shown is honestly limited to the one real product this portal currently sells — there's no per-farm price list beyond the single server-fixed rate in this build.

**What happens to a technical visit that didn't result in a recommendation?** It still shows up under Technical Visits (with whatever notes were recorded), just not under My Recommendations, which is specifically the subset that named a real product.
