# Process Guide — Pig Farm: Breeding to Sale (End to End)

## Purpose

This is the complete lifecycle of one pig production batch on the demo farm — from a specific breeding pairing through to a completed sale — including the operational detail (feeding, health, growth, mortality, cost) that the Quick Start skips over.

## Prerequisites

- No dedicated per-role login exists yet for this vertical (see the [Administrator Guide](../administrator-guide.md)) — run as Administrator today.
- Farm layout: **Demo Pig Farm - Dong Nai** has a Breeding pen and a Nursery/Grower pen. Breeding stock (sows, boars) are tracked individually by tag ID; production batches of growing pigs are tracked as a group (a Grower Batch), not animal-by-animal.

## Roles involved

| Role | Responsibility |
|---|---|
| **Farm Manager** | Owns the entire flow below — breeding records, health and feed logging, growth tracking, and sale. |

## The process, step by step

### 1. Breeding

A specific sow (SOW-001, Yorkshire) and boar (BOAR-001, Duroc) are recorded in a **Pig Breeding Service**, with a service date. The record's status starts as **Served**.

### 2. Pregnancy confirmation

Once pregnancy is confirmed, the service's status is updated to **Confirmed Pregnant**. This status field follows a real, enforced lifecycle — the system will reject an attempt to move it backward once it has advanced (for example, you cannot reset a "Farrowed" record back to "Served").

### 3. Farrowing

When the litter is born, a **Pig Farrowing** record is created against the breeding service, capturing the farrowing date, how many piglets were born alive, and how many were born dead. In this example: 12 born alive, 1 born dead.

### 4. The grower batch begins

The litter (minus one further pre-weaning loss, recorded separately as a Mortality Record) becomes a **Pig Grower Batch** — a single record representing the whole group of growing pigs, housed in the Nursery/Grower pen, with its own batch code and weaning date. Its stage starts at "Nursery" and its status is "Active."

### 5. Ongoing farm operations against the batch

While the batch grows, several kinds of records accumulate against it, each with real business meaning:

- **Feeding** — periodic **Pig Feed Log** entries record what was fed, how much, and its cost. These costs accumulate toward the batch's eventual cost-per-kilogram calculation.
- **Vaccination** — **Pig Vaccination** records track scheduled and administered vaccines. In this example, one vaccine (Classical Swine Fever) was administered on schedule; a second (Foot-and-Mouth Disease) is deliberately left overdue in the demo data — its due date has passed with no administered date recorded, and the system reflects that as a genuine, current "Overdue" status rather than hiding it.
- **Medicine treatment** — a **Pig Medicine Treatment** record captures a diagnosis (in this example, a mild respiratory infection in part of the batch), the medicine used, and — critically — a **withdrawal period** in days: the minimum time that must pass after treatment before any animal from this batch can be sold.
- **Weight tracking** — periodic **Pig Weight Record** entries capture average weight and sample size, showing the batch's growth curve over time.
- **Mortality** — any losses are recorded as a **Pig Mortality Record** with a stated cause, so the batch's final head count is always accurate and explained.

### 6. Sale

Once the batch is ready, a **Pig Sale Lot** is created: the customer, head count, total weight, sale price, and any other cost. The system automatically computes the batch's total accumulated cost (feed + medicine + other), the resulting cost per kilogram, and the profit on the sale — figures drawn directly from the operational records kept throughout the batch's life, not entered separately.

*What the system enforces here:* the sale date must fall **after** any active medicine withdrawal period has fully elapsed. In this example, the treatment's 10-day withdrawal period ends 5 days before the sale actually happens — provably satisfied, not just assumed. Attempting to sell within the withdrawal window is blocked outright.

Once sold, the Grower Batch's own status updates to **Sold**, marking its lifecycle as complete.

## Closing the loop

At any point afterward, starting from the **Pig Sale Lot**, you can trace backward through the exact chain that produced it: which batch it was, which farrowing and litter that batch came from, and which specific sow and boar produced that litter. This is the traceability a livestock buyer, auditor, or your own quality process would actually want to see — a real, connected record chain, not separate logs that have to be manually cross-referenced.

## Reports

- **Pig Grower Batch** list, filtered by `status`/`stage`.
- **Pig Vaccination** list, filtered by `status = Overdue`, for health-compliance follow-up.
- **Pig Sale Lot** list, for cost-per-kg and profit review across completed sales.
- **Pig Mortality Record** list, for loss-rate review over time.

## Common errors across the process

| Message / situation | Root cause |
|---|---|
| Duplicate animal tag ID rejected | Every breeding animal's tag ID must be unique across the farm. |
| Backward status transition on a Breeding Service rejected | The breeding lifecycle (Served → Confirmed Pregnant → Farrowed) only moves forward. |
| Sale blocked during a medicine withdrawal period | A genuine food-safety rule — the sale date must be after the withdrawal period ends for any treated animal in the batch. |
| A vaccination shows "Overdue" | Real, current data — a scheduled vaccination whose due date has passed with no administered date recorded. |

## FAQ

**Is a Grower Batch tracked animal-by-animal or as a group?** As a group — feed, vaccination, medicine, weight, and mortality are all recorded against the batch as a whole, which matches how a real nursery/grower operation is actually managed day to day.

**What stops someone from selling animals too soon after treatment?** A hard validation check compares the sale date against the treatment date plus its recorded withdrawal period, and blocks the sale if it would fall inside that window — it isn't left to memory or a paper checklist.

**Where does the profit figure on a Sale Lot come from?** It's computed from the batch's own accumulated feed, medicine, and other recorded costs versus the sale price and any other cost entered at time of sale — a real calculation over real records, not a manually typed number.
