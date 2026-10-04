# Role Guide — Farm Manager (Pig Farm)

## Purpose

As Farm Manager, you're responsible for the full operational life of every animal and every batch on the farm: breeding, farrowing, feeding, health (vaccination and medicine), growth tracking, mortality recording, and finally sale — with cost and profit visible at the end of it.

## Prerequisites

- **Disclosed gap:** there is not yet a dedicated `farm.manager`-style login for this vertical (unlike the Pharmaceutical scenario's five role-specific accounts). Until one is provisioned, use an Administrator login. See the [Administrator Guide](../administrator-guide.md) for how one would be added, following the same pattern used for the Pharma demo users.
- Familiarity with the farm's basic layout: a **Pig Farm** contains multiple **Pig Pens** (e.g. a Breeding pen, a Nursery/Grower pen), and individual breeding animals (sows, boars) are tracked by a unique tag ID.

## Roles

There is currently one operational role covering this whole flow in the demo (Farm Manager, run as Administrator). A real deployment might split breeding/health record-keeping from sales, but the platform doesn't yet have that split modeled with separate logins for this vertical.

## How to create

The full breeding-to-sale record chain, in the order you'd actually create it:

1. **Pig Breeding Service** — record a sow mated with a boar, with the service date. Status starts as "Served."
2. Move the service to **"Confirmed Pregnant"** once pregnancy is confirmed (this is a controlled status transition — see Common Errors below).
3. **Pig Farrowing** — once the litter is born, record it against the breeding service: how many born alive, how many born dead, and the farrowing date.
4. **Pig Grower Batch** — the litter (minus any very early pre-weaning loss, tracked separately as a Mortality Record) becomes a grower batch in a nursery/grower pen, with its own batch code and weaning date.
5. Ongoing operational records against that batch as it grows:
   - **Pig Feed Log** — feed product, quantity, and cost, recorded periodically.
   - **Pig Vaccination** — vaccine name, due date, and (once given) administered date.
   - **Pig Medicine Treatment** — medicine name, diagnosis, and a **withdrawal period** in days (the time that must pass after treatment before the animal can be sold for meat).
   - **Pig Weight Record** — average weight and sample count, taken periodically to track growth.
   - **Pig Mortality Record** — any losses, with a recorded cause.
6. **Pig Sale Lot** — once the batch is ready, record the sale: customer, head count, total weight, sale price, and any other cost. The system automatically calculates cost per kilogram and profit for that lot from the batch's accumulated feed/medicine/other costs.

## How to review

- Open the **Pig Grower Batch** record directly to see its current stage and status (Active vs. Sold), and use its linked records (feed logs, vaccinations, treatments, weight records, mortality) to review its full operational history in one place.
- Review the **Pig Breeding Service** status to confirm where an animal is in its reproductive cycle (Served → Confirmed Pregnant → Farrowed).

## How to approve

There's no separate multi-person approval step in this flow today — the Farm Manager role records and confirms each stage directly (e.g. confirming pregnancy, confirming a batch is ready to sell). The system's enforcement comes from blocking invalid actions (see Common Errors) rather than requiring a second person's sign-off.

## How to amend

Standard Frappe behavior applies: once a record like a Pig Sale Lot is submitted/finalized, correct it via cancel-then-amend rather than direct editing, to keep a clean history. For records that stay in draft/editable states longer (like feed logs), you can edit directly until they're finalized.

## How to cancel

Cancel a record if it was created in genuine error (e.g. a duplicate feed log entry) — but check first whether anything downstream depends on it (for example, a Sale Lot that already used a batch's accumulated cost figures).

## Reports

- **Pig Grower Batch** list, filtered by `status` (Active/Sold) or `stage`, to see what's currently on the farm versus already sold.
- **Pig Vaccination** list, filtered by `status = Overdue`, as your recurring health-compliance check.
- **Pig Sale Lot** list to review cost-per-kg and profit across completed sales.

## Common errors

| Message / situation | What it means |
|---|---|
| A duplicate animal tag ID is rejected when creating a new breeding animal | Every animal's tag ID must be unique — the system will not let you register a second animal under a tag that's already in use. |
| An attempt to move a breeding service backward (e.g. from "Farrowed" back to "Served") is blocked | The breeding lifecycle only moves forward — this protects the record from being accidentally reset once a litter has already been recorded against it. |
| An attempt to sell a batch is blocked because it falls within a medicine's withdrawal period | This is a genuine food-safety enforcement: if an animal was treated with medicine that has (for example) a 10-day withdrawal period, the system will not allow a sale dated before that period has fully elapsed. Wait until the withdrawal period has passed, or reconsider which animals are included in the sale. |
| A vaccination shows "Overdue" | A real, current gap — the due date has passed with no administered date recorded. Treat it as an action item, not a data error. |

## FAQ

**Can I sell an animal immediately after treating it with medicine?** Not if doing so would fall within that medicine's recorded withdrawal period — the system actively blocks a Sale Lot dated too soon after treatment, as a real food-safety safeguard, not just a warning.

**What happens to a pre-weaning loss?** It's recorded as a Mortality Record and reflected in the grower batch's initial count, so the batch's numbers stay accurate from the very start rather than only accounting for losses that happen after weaning.

**How is profit on a sale lot calculated?** From the batch's accumulated real costs (feed, medicine treatment, and any other recorded cost) against the sale price recorded on the Sale Lot — it's a computed figure drawn from the same records you've been keeping throughout the batch's life, not a separately entered number.
