# Quick Start — Farm Customer Portal: Orders, Technical Visits & Account Isolation

**Time needed:** 5–10 minutes
**What you'll see:** a farm customer's own self-service web portal — order history, a technical visit with a product recommendation — and real proof that one farm customer can never see another farm's data, even by directly guessing at a record.

## Purpose

This is a customer-facing self-service portal, not an internal back-office screen. A real farm — a paying customer of the veterinary pharmaceutical business — logs in with their own account and sees only their own information. This quick start shows you the portal from that farm's point of view, and then proves the isolation between two different farms is real.

## Prerequisites

- Two demo farm accounts exist for this walkthrough:
  | Farm | Login | Notes |
  |---|---|---|
  | Farm Alpha (a cattle farm) | `farm.alpha.portal@pharmacountry.vn` | Generous credit limit |
  | Farm Beta (a swine farm) | `farm.beta.portal@pharmacountry.vn` | Tighter credit limit |
  Shared demo password: `Demo@1234`.
- The portal is a separate, dedicated web application (not the internal back-office screens used elsewhere in this platform) — access it at the farm portal's own web address rather than the main Desk login.

## The fastest path

1. **Log in as Farm Alpha.** You'll land on your own account dashboard — nothing here belongs to any other farm.
2. Open **My Orders**. You'll see Farm Alpha's real order history for the one veterinary product this portal currently offers (an injectable antibiotic, OXYTET-200-INJ).
3. Open **Technical Visits** (or **My Recommendations**). You'll see a real visit record from a field representative, including a specific recommended product — not just a free-text note, but a structured recommendation tied to a real catalog item.
4. **Log out, then log in as Farm Beta** (a completely different, unrelated farm account).
5. Confirm Farm Beta's own order history and technical visits are completely different from Farm Alpha's — and that there is no menu, search box, or link anywhere in the portal that would let Farm Beta browse or find Farm Alpha's data.
6. If you want to try to break it: note down one of Farm Alpha's real order reference numbers while logged in as Alpha, then try to look it up while logged in as Beta. It fails — not with a "you're not allowed to see this" message that would confirm the order exists, but with an ordinary "not found," exactly as if it never existed at all.

## Where to go next

- **[Role Guide — Farm Customer](role-guide-farm-customer.md)** — everything a farm's own staff can do in the portal day to day.
- **[Process Guide](process-guide.md)** — the full story from a field rep's technical visit through to placing and reviewing an order, and the account-isolation guarantee in more depth.

## Common errors

| What you see | What it means |
|---|---|
| "Order not found" when trying to look up another farm's order number | Correct, deliberate behavior — the portal doesn't distinguish between "doesn't exist" and "exists but isn't yours," specifically so a curious or malicious user can't use the error message itself to confirm another farm's record numbers. |
| You can't place an order past your credit limit | Correct behavior — the same real credit-limit protection used in the back-office system also applies here; a farm with a tight credit limit (like Beta) will hit this if an order would exceed it. |

## FAQ

**Is this the same login as the internal back-office system?** It uses the same underlying account system, but the portal itself is a separate, purpose-built web application for customers — farm staff never see or need access to the internal Desk screens used by warehouse, QC, or sales staff.

**What happens if I try to order more than my farm's credit limit allows?** The order is blocked by the same real financial control used throughout this platform — this isn't a portal-specific rule, it's the same credit-limit enforcement that applies to any sales order in the system.

**Why is there only one product in the catalog?** This demo is honestly scoped to the one real veterinary product this platform's data actually supports (an injectable antibiotic) rather than inventing a larger fictional catalog — see the Administrator Guide for more on how demo scope decisions like this are made across the platform.
