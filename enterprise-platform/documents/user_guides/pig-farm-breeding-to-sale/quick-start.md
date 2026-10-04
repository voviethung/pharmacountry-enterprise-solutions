# Quick Start — Pig Farm: Breeding to Sale Traceability

**Time needed:** 5–10 minutes
**What you'll see:** one pig litter's complete journey — which sow and boar produced it, how it grew, and what it was ultimately sold as — tracked as one continuous, connected record chain.

## Purpose

A livestock buyer, auditor, or your own farm manager should be able to ask "where did this batch of pigs come from, and how did it perform?" and get a real, traceable answer. This quick start walks through exactly that, for one real batch on the demo farm.

## Prerequisites

- A working login. **Note:** there is not yet a dedicated Farm Manager demo login for this vertical (unlike the Pharmaceutical scenario's five role-specific accounts) — this scenario is viewed via an Administrator account today. See the [Administrator Guide](../administrator-guide.md) for how one would be added.
- No other setup required.

## The fastest path

1. Open the **Pig Farm** record — "Demo Pig Farm - Dong Nai." This farm has two pens set up: a breeding pen and a nursery/grower pen.
2. Open the **Pig Breeding Service** record. It shows a specific sow (SOW-001, a Yorkshire) mated with a specific boar (BOAR-001, a Duroc) — the record's status moves through a real lifecycle: served, then confirmed pregnant, then farrowed.
3. Open the linked **Pig Farrowing** record — the litter this service actually produced (12 born alive, 1 born dead).
4. Open the **Pig Grower Batch** raised from that litter. Its status shows **Sold** — this specific batch has completed its whole lifecycle, from nursery pen through to sale.
5. Open one of its **Pig Weight Record** entries — a real, dated weight-tracking sample taken partway through the batch's growth.
6. Open the **Pig Sale Lot** this batch was ultimately sold as. This closes the loop: **breeding → farrowing → grower batch → sale**, all as one connected chain, not separate disconnected logs.

## Where to go next

- **[Role Guide — Farm Manager](role-guide-farm-manager.md)** — the day-to-day operational tasks (feed, vaccination, medicine, weighing, mortality, sale) a farm manager actually performs.
- **[Process Guide](process-guide.md)** — the complete operational story, including the parts this quick tour skips over (feeding, health records, cost tracking).

## Common errors / things that look like errors but aren't

| What you see | What it means |
|---|---|
| No dedicated "Farm Manager" login exists yet | A genuine, disclosed gap for this vertical — run the scenario as Administrator for now. |
| A vaccination record shows status "Overdue" | Real, current data — a scheduled vaccination that's past its due date with no administered date recorded. This is deliberate: the system surfaces it as an action item rather than hiding it. |

## FAQ

**Is this real farm data or a mockup?** It's built the same way as every other example on this platform: real records, real parent/child links between them (breeding service → farrowing → grower batch → sale lot), not a static illustration.

**Can a batch be sold before its full lifecycle is tracked?** The system tracks the batch's stage (e.g. Nursery) and status (Active/Sold) explicitly, so you can always tell where a given batch is in its life — and, as covered in the Role Guide, certain sales are blocked outright if a health-related restriction (like a medicine withdrawal period) hasn't yet passed.
