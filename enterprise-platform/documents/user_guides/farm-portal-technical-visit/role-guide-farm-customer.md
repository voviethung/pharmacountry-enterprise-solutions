# Role Guide — Farm Customer (Portal User)

## Purpose

As a farm customer using the self-service portal, you can review your own account's order history, see technical visit notes and product recommendations from your field representative, place new orders, and see your complete service history — all scoped strictly to your own farm, with no way to see any other customer's data.

## Prerequisites

- Login: your farm's own portal account (e.g. `farm.alpha.portal@pharmacountry.vn` in the demo), password `Demo@1234` for demo accounts.
- Native system role: **Sales User** (a standard, restricted role — not an internal staff account).
- Access the portal at its own dedicated web address — it's a separate application from the internal back-office system.

## Roles

| Role | Responsibility |
|---|---|
| **Farm Customer (you)** | Views your own orders and technical visits, places new orders. |
| Field representative (internal staff, not a portal role) | Conducts technical visits and records product recommendations on your account. |

## How to create

The one thing you create yourself in the portal is a new order:
1. Open the product catalog (currently one real product: an injectable veterinary antibiotic, with its target species, indication, and withdrawal period shown).
2. Enter the quantity you want.
3. Submit. The price is fixed by the system (you can't set your own price), and the order is created as a real order tied to your farm account only.

## How to review

- **My Orders** — every order your farm has placed, with status, totals, and PO reference.
- Opening a specific order shows its full line-item detail.
- **Technical Visits** — every recorded visit from your field representative, including notes and follow-up dates.
- **My Recommendations** — the subset of your technical visits that included a specific recommended product, shown together with that product's real details (target species, indication, withdrawal period) so you can see exactly why it was suggested.
- **Service History** — a single combined timeline merging your orders and technical visits together by date, so you can see your whole relationship with the business at a glance.

## How to approve

There's no separate internal approval step visible to you as the customer — submitting an order is itself the final action on your side. What happens next (whether the order goes through) depends on standard business rules, most importantly your farm's credit limit (see Common Errors).

## How to amend

Orders you've already submitted aren't directly editable from the portal — if you need to change quantity or details, place a new order or contact your representative, the same way you would with any submitted sales order elsewhere in this platform.

## How to cancel

Order cancellation, if needed, is handled the same way as any other sales order cancellation in the system — typically through your sales representative rather than a self-service "cancel" button in the portal.

## Reports

- **My Orders**, sorted with the most recent first.
- **My Recommendations**, showing only visits that resulted in a specific product suggestion.
- **Service History**, the unified timeline of everything above.

## Common errors

| Message / situation | What it means |
|---|---|
| A new order is rejected for exceeding your credit limit | A real, enforced financial control — each farm has its own credit limit, and the system will not let an order push your account past it. If you believe this is wrong, contact your account representative rather than retrying with a different quantity. |
| Trying to look up another farm's order or visit fails with "not found" | This is intentional and correct — the portal never distinguishes between "that record doesn't exist" and "that record exists but isn't yours," specifically so no one can use error messages to fish for information about other customers. |
| You don't see a product you expected in the catalog | The portal's catalog is intentionally limited to the specific products actually available through this channel — check with your representative if you're expecting something not shown. |

## FAQ

**Can I see other farms' orders or pricing?** No, under any circumstances — every list and lookup in the portal is scoped strictly to your own farm's account, checked more than once by the system (not just filtered in the display), and this has been independently, empirically verified — not just assumed to work.

**Does the portal show my real Frappe login session details?** No — behind the scenes, the portal keeps your real session credentials on the server side only and gives your browser a separate, opaque session token. You never need to think about this as a user; it's mentioned here only for completeness.

**What's a "technical visit"?** A record of your field representative visiting your farm, with any notes and — often — a specific product recommendation. It's the same kind of visit record your rep would otherwise only be able to show you on paper or by phone; the portal just makes it visible to you directly, whenever you want to check it.
