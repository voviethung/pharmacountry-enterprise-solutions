// Curated, per-Industry-Pack "what this demo actually proves" content for the Hub's
// `/solutions/[packCode]` detail page.
//
// SOURCING (read before editing): every field below is transcribed/paraphrased from this
// platform's own real, already-written engineering documentation —
// `documents/project_status.md`'s Phase 3-6 Golden Demo write-ups and
// `documents/productization/00_demo_platform_master_plan.md`'s DEMO 01-32 test-ID sections
// (both in the `enterprise-platform` repo) — never invented marketing copy. Test IDs
// (e.g. "Q01"-"Q08") are this platform's own real, documented acceptance-criteria codes;
// `testDescriptions` paraphrase the real text next to each ID; `businessFlowSummary` paraphrases
// project_status.md's own real narrative for that golden demo; `notableBugsFixed` are real,
// documented incidents from that demo's build, not illustrative examples.
//
// WHY A CURATED FILE, NOT A LIVE BACKEND CALL: this content's source of truth
// (`project_status.md`) is static engineering documentation, not live transactional data — it
// changes only when a human writes a new demo up, not per-request. Building a new backend
// endpoint that re-parses a markdown file at runtime would add real fragility (markdown
// structure drift, Docker build-time-vs-runtime path issues — see this repo's own Dockerfile
// comments) for zero benefit over checking a reviewed extract into this frontend's own repo,
// which is exactly how `public_api.py`'s own `_PACK_SUMMARIES` dict already treats this same
// class of content one step up (a short one-liner instead of this page's fuller detail).
//
// LANGUAGE: authored in English only, same honest limitation already disclosed for
// `industry_category`/`summary` on the Solutions page (see that page's own `languageNote`
// translation) — this content is sourced from this platform's own English-language internal
// engineering documentation, and translating it would risk drifting from the real source text.
// The detail page's own STATIC chrome (headings, labels) is fully bilingual via
// messages/{vi,en}.json; only this real, sourced content itself stays English.
//
// COVERAGE: all 26 of the 27 real Industry Packs that have an actual golden demo (has_golden_demo
// = true, confirmed live) have an entry here. The 27th, IP-VETERINARY-BIOLOGICAL, genuinely has
// zero seed data (confirmed live via `Industry Pack Seed` query) — it deliberately has NO entry
// in this map; see `NOT_YET_BUILT_NOTE` below for the one honest, sourced sentence the detail
// page shows for it instead (the master plan's own phase-1-scoped, never-built VB01-VB06 intent).

export interface IndustryPackContent {
  /** e.g. "Golden Demo #1" or "Golden Demo #9 & #10" when a pack spans two numbered demos. */
  goldenDemoLabel: string;
  /** Real demo company/site name used in the seed data, when the source text names one. */
  companyName?: string;
  /** Real, documented acceptance-criteria/test IDs for this demo (e.g. ["Q01", ..., "Q08"]). */
  testIds: string[];
  /** id -> short, real, paraphrased description of what that test proves. */
  testDescriptions: Record<string, string>;
  /**
   * Test IDs in `testIds` that the master plan documents as intended scope, but which
   * project_status.md's own write-up does not separately confirm as built-and-verified for
   * this specific golden demo (usually because a later, related golden demo realized the same
   * proof instead). Rendered with a distinct, honest "spec'd" marker rather than silently
   * listed as equally proven as everything else.
   */
  unconfirmedTestIds?: string[];
  /** 2-4 real sentences paraphrasing the demo's actual business flow. */
  businessFlowSummary: string;
  /** Real, documented bugs found/fixed while building this demo (0-3 items). */
  notableBugsFixed?: string[];
}

export const NOT_YET_BUILT_PACK_CODE = "IP-VETERINARY-BIOLOGICAL";

// The one honest, sourced sentence for the pack with no golden demo at all — paraphrased from
// the master plan's own DEMO 15 section, which documents an INTENDED (never built) VB01-VB06
// test scope explicitly marked "Scope phase 1" with the caveat "do not claim this is a full
// biopharma MES at this phase."
export const NOT_YET_BUILT_NOTE =
  "This pack has zero seed data or documented test IDs — confirmed directly against the live registry, not assumed. The platform's own master plan does describe an intended future scope for it (seed/strain traceability, biological batch genealogy, cold-storage handling, QC-gated release, and recall trace, referenced there as tests VB01–VB06), explicitly scoped as \"phase 1\" and explicitly not claimed to be a full biopharma manufacturing execution system — but none of that was ever actually built: no seed function, no seeded company, no verifiable demo.";

export const PACK_CONTENT: Record<string, IndustryPackContent> = {
  "IP-PHARMA": {
    goldenDemoLabel: "Golden Demo #1 & #2",
    companyName: "Demo Pharma Co.",
    testIds: [
      "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10",
      "PD01", "PD02", "PD03", "PD04", "PD05", "PD06", "PD07",
    ],
    testDescriptions: {
      P01: "Raw material can't be issued from Quarantine straight into production",
      P02: "Only a Released-status batch may be issued",
      P03: "A Work Order must use the currently effective BOM version",
      P04: "Consumption beyond tolerance needs a warning or approval",
      P05: "An out-of-limit in-process QC check raises a real quality event",
      P06: "Finished goods without QA release can't move to the Released warehouse",
      P07: "Batch genealogy traces raw material through to finished goods",
      P08: "A recall report traces finished goods to the customers who received them",
      P09: "The production user can't self-approve their own QA release",
      P10: "An obsolete document can't remain a current work instruction",
      PD01: "FEFO (first-expiry-first-out) picking suggestion on delivery",
      PD02: "An expired batch cannot be shipped",
      PD03: "A recalled batch blocks delivery",
      PD04: "Customer credit limit is enforced before a sale",
      PD05: "A customer return restores stock to the correct original batch",
      PD06: "Trace which customers received a given batch",
      PD07: "Near-expiry batches raise an alert",
    },
    unconfirmedTestIds: ["P02", "P03", "P04", "P07", "P08", "P09", "P10"],
    businessFlowSummary:
      "Demo Pharma Co. runs the full pharma chain: purchasing raw materials into Quarantine, QC-releasing them to Approved, manufacturing PARA-500-TAB tablets against a BOM, in-process QC, and QA batch release to a Released finished-goods warehouse. Golden Demo #2 extends the same company into wholesale distribution — a genuine second manufacturing batch (deliberately backdated expiry) gives FEFO picking a real choice, then sells to wholesale customer \"ABC Pharmacy Chain Co.\" with expiry blocking, recall blocking, credit-limit enforcement, returns, and batch-to-customer traceability all proven live.",
    notableBugsFixed: [
      "A missing shelf_life_in_days value blocked expiry tracking until set explicitly.",
      "BOM packaging quantities were wrongly set per-tablet instead of per-batch, leaving packaging consumption near zero until corrected.",
      "A partially-applied stock receipt (submitted but only some ledger entries posted) was resolved by cancelling the document rather than force-deleting it.",
    ],
  },

  "IP-QMS": {
    goldenDemoLabel: "Golden Demo #3",
    testIds: ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08"],
    testDescriptions: {
      Q01: "A Deviation can't reach Closed without a recorded root cause",
      Q02: "A CAPA's owner can't also be the person who closes it (segregation of duties)",
      Q03: "An overdue CAPA automatically escalates to Overdue status",
      Q04: "A CAPA can't close without an effectiveness check and evidence, on or after its due date",
      Q05: "Change Control impact flags drive its Draft → Under Review → Approved workflow",
      Q06: "An out-of-spec lab result automatically creates a linked CAPA and Deviation",
      Q07: "A Major audit finding links to a CAPA",
      Q08: "Every QMS record keeps a full, real audit trail",
    },
    businessFlowSummary:
      "A cold-storage temperature excursion is investigated as a Deviation, root-caused, and linked to a CAPA that can only close after a genuine effectiveness check performed by someone other than the CAPA's own owner. The same run also seeds a Change Control flagging an SOP for revision (picked up later by the DMS golden demo), an out-of-spec lab result, an audit finding, and a recall/risk/supplier-quality record, for full coverage of all 9 QMS modules.",
    notableBugsFixed: [
      "The CAPA-escalation step originally bypassed Frappe's own audit trail, silently defeating the full-audit-trail test for that one event.",
      "Cross-module link fields used friendly labels instead of the literal DocType names the linking mechanism actually validates against, breaking every cross-module link until fixed.",
      "None of the 9 new QMS doctypes had change tracking enabled, so the audit-trail test initially showed zero history despite everything else working correctly.",
    ],
  },

  "IP-DMS": {
    goldenDemoLabel: "Golden Demo #4",
    testIds: ["D01", "D02", "D03", "D04", "D05", "D06", "D07"],
    testDescriptions: {
      D01: "An Effective or Obsolete document version's content is immutable",
      D02: "Only the Effective version shows as the current one",
      D03: "Going Effective auto-creates a training assignment for every relevant user",
      D04: "A superseded version automatically flips to Obsolete, archived rather than deleted",
      D05: "A controlled print event is logged",
      D06: "Revising a document keeps its full version history",
      D07: "Users who are assigned training but haven't completed it are flagged",
    },
    businessFlowSummary:
      "The exact SOP the QMS golden demo's Change Control flagged for revision goes through Draft → Under Review → Approved → Effective as Version 1, auto-assigning training to every demo user. A Version 2 revision (referencing the earlier audit finding) then supersedes it, flipping Version 1 to Obsolete while preserving its full history.",
    notableBugsFixed: [
      "One integrity check used an existence query with no real filter, so it always returned true regardless of the actual data — a bug pattern later swept and fixed platform-wide.",
    ],
  },

  "IP-LIMS": {
    goldenDemoLabel: "Golden Demo #5",
    testIds: ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08"],
    testDescriptions: {
      L01: "A duplicate sample (same batch, type, and date) is blocked",
      L02: "Testing against a Draft (not yet approved) specification is blocked",
      L03: "An analyst can't review their own test result (segregation of duties)",
      L04: "Pass/fail is always recomputed server-side from spec limits, never trusted from manual entry",
      L05: "An out-of-spec result automatically creates a linked QMS out-of-spec record",
      L06: "A reviewed test result can't be silently edited afterward",
      L07: "A Certificate of Analysis can only be approved once its test is Approved",
      L08: "Testing on an instrument with overdue calibration is blocked",
    },
    businessFlowSummary:
      "The standalone LIMS runs a full sample lifecycle — receive, assign, test, record result, review, approve — for a Paracetamol tablet batch, then deliberately produces an out-of-spec assay result to prove it automatically raises a real linked quality record, finally issuing a Certificate of Analysis once the test is Approved.",
    notableBugsFixed: [
      "An automated quality-event hook updated the very document that triggered it from inside its own save event, causing a timestamp-conflict error and a real partial-write incident.",
      "A later, unrelated demo's reuse of the same shared analyst account broke this demo's own segregation-of-duties check by matching the wrong specification — fixed by scoping the check explicitly.",
    ],
  },

  "IP-EAM": {
    goldenDemoLabel: "Golden Demo #6",
    testIds: ["E01", "E02", "E03", "E04", "E05", "E06", "E07"],
    testDescriptions: {
      E01: "Preventive maintenance auto-schedules",
      E02: "Overdue calibration is visible and queryable",
      E03: "A breakdown creates a real repair work order",
      E04: "Spare-part consumption is recorded on the repair",
      E05: "A qualification (IQ/OQ/PQ) links to specific equipment",
      E06: "Equipment can't be qualified or used while its calibration is overdue",
      E07: "Full equipment service history is retained",
    },
    businessFlowSummary:
      "Built almost entirely on native ERP asset-management machinery plus two new records (Calibration Record, Qualification): a passing calibration lets an equipment qualification succeed; a real breakdown (a drive-belt failure) creates a repair consuming a spare part; a second qualification attempt against deliberately overdue calibration is correctly blocked.",
    notableBugsFixed: [
      "A \"latest calibration\" lookup ordered by the wrong date field, which could have let a block-worthy qualification through — caught before it ever ran live.",
    ],
  },

  "IP-FEED": {
    goldenDemoLabel: "Golden Demo #7",
    companyName: "Demo Feed Mill Co.",
    testIds: ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
    testDescriptions: {
      F01: "Formula (BOM) revision",
      F02: "Ingredient substitution requires a Pending → Approved workflow",
      F03: "Weighing tolerance (±3%) is enforced during manufacture",
      F04: "Batch genealogy is traceable",
      F05: "Yield is computed from actual manufacturing output",
      F06: "The QC release gate reuses the pharma golden demo's own hook unmodified",
      F07: "A cross-contamination sequencing flag blocks running an allergen-free feed right after an allergen feed",
      F08: "Silo stock can be queried",
    },
    businessFlowSummary:
      "Demo Feed Mill Co. produces an allergen-containing Pig Starter Feed and an allergen-free Pig Grower Feed through weighing, mixing, QC, and release. The demo proves a formula revision, an approved ingredient substitution, and that running the allergen-free feed right after the allergen feed on the same line is blocked unless a line-cleaning log resolves it.",
    notableBugsFixed: [
      "An item's allergen flag was left off by default, so the cross-contamination check initially had nothing to block.",
      "The same always-true existence-check bug from the QMS build recurred here, prompting a platform-wide grep sweep for the pattern.",
      "The pharma golden demo's own integrity check had a stale hardcoded assumption (a single batch size) that broke once a second batch existed — rewritten to derive expectations dynamically from ledger data.",
    ],
  },

  "IP-SHRIMP": {
    goldenDemoLabel: "Golden Demo #8",
    companyName: "Demo Shrimp Farm — Bac Lieu",
    testIds: ["SF01", "SF02", "SF03", "SF04", "SF05", "SF06", "SF07", "SF08", "SF09", "SF10"],
    testDescriptions: {
      SF01: "A pond correctly flips from Empty to Stocked on stocking",
      SF02: "An already-stocked pond can't be double-stocked",
      SF03: "Daily feed log recorded",
      SF04: "Water-quality reading recorded",
      SF05: "Growth sample recorded",
      SF06: "Health treatment recorded",
      SF07: "Mortality recorded",
      SF08: "Harvest KPIs computed from the batch's own recorded history",
      SF09: "Cost per kilogram computed server-side",
      SF10: "A water reading below a safe threshold raises an alert",
    },
    businessFlowSummary:
      "A full shrimp crop cycle at Demo Shrimp Farm — Bac Lieu: an empty pond is stocked with 250,000 post-larvae, then feed, water quality, growth, health, and mortality are logged (including one deliberately below-threshold water reading) before harvest, with survival rate, feed-conversion ratio, and cost per kilogram computed from the batch's own recorded operational history.",
    notableBugsFixed: [
      "Early feed-log entries were sized unrealistically small, producing an impossible feed-conversion ratio, later rescaled to a realistic value with an added sanity check.",
      "A water-reading duplicate check used the current timestamp instead of the reading's own date, letting readings silently duplicate on every re-run.",
      "The stocking idempotency check only matched still-active batches, so re-running the seed after a crop finished tried to re-stock the same pond and hit its own block.",
    ],
  },

  "IP-VETERINARY": {
    goldenDemoLabel: "Golden Demo #9 & #10",
    companyName: "Demo Vet Pharma Co.",
    testIds: [
      "VPM01", "VPM02", "VPM03", "VPM04", "VPM05", "VPM06", "VPM07",
      "VD01", "VD02", "VD03", "VD04", "VD05", "VD06", "VD07",
    ],
    testDescriptions: {
      VPM01: "Species/indication/withdrawal-period master data",
      VPM02: "Formula/BOM revision",
      VPM03: "Batch and expiry tracked through production",
      VPM04: "QC release gate, reusing the pharma golden demo's own hook unmodified",
      VPM05: "Traceability",
      VPM06: "Recall, reusing the QMS golden demo's recall mechanism directly",
      VPM07: "Label version, reusing the DMS golden demo's document lifecycle",
      VD01: "Territory ownership",
      VD02: "Dealer-tier pricing",
      VD03: "Batch and expiry tracked on delivery to a dealer",
      VD04: "Dealer credit limit enforcement",
      VD05: "Territory sales target",
      VD06: "Recall trace to a dealer",
      VD07: "A technical visit log linked to a specific dealer",
    },
    unconfirmedTestIds: ["VPM05"],
    businessFlowSummary:
      "Demo Vet Pharma Co. manufactures an injectable oxytetracycline product, reusing the pharma golden demo's own manufacturing, QC, and QA-release machinery almost unmodified. Golden Demo #10 then distributes that same product to a regional dealer, \"VetCare Mekong Dealer Co.,\" proving territory ownership, dealer credit limits, batch-tracked delivery, a technical-visit log, and a full recall-to-dealer trace.",
    notableBugsFixed: [
      "An invalid unit-of-measure code for liters had to be corrected to the platform's real unit name.",
      "A BOM revision on a batch with an already-submitted work order couldn't be cancelled outright — fixed by flipping which version is the default, the correct pattern for revising legitimate history rather than fixing a mistake.",
      "A sales-territory distribution required its percentages to sum to exactly 100%, and required a new leaf-level customer group rather than reusing a group-level node.",
    ],
  },

  "IP-LIVESTOCK-PIG": {
    goldenDemoLabel: "Golden Demo #11",
    testIds: ["PF01", "PF02", "PF03", "PF04", "PF05", "PF06", "PF07", "PF08"],
    testDescriptions: {
      PF01: "Animal/batch tag uniqueness",
      PF02: "Breeding lifecycle: service → confirmed pregnant → farrowing → grower batch",
      PF03: "Feed consumption logged",
      PF04: "Vaccination due/administered/overdue, always recomputed server-side",
      PF05: "Medicine withdrawal period computed and enforced before sale",
      PF06: "Mortality recorded",
      PF07: "Cost allocation (feed, medicine, other) and profit computed server-side",
      PF08: "Trace to the real customer sale lot",
    },
    businessFlowSummary:
      "A sow and boar are bred through service, confirmed pregnancy, and farrowing, producing a grower batch in a pen; feed, vaccination (one deliberately overdue), medicine treatment with a computed withdrawal period, and mortality are logged; the batch is sold only after its withdrawal period has elapsed, with cost and profit computed from its own recorded history.",
    notableBugsFixed: [
      "A duplicate-tag negative test initially caught the wrong exception type, since the real duplicate-entry error is a different error class than expected — the fix was then reused by five later farm golden demos.",
    ],
  },

  "IP-LIVESTOCK-POULTRY": {
    goldenDemoLabel: "Golden Demo #12",
    testIds: ["PO01", "PO02", "PO03", "PO04", "PO05", "PO06", "PO07"],
    testDescriptions: {
      PO01: "Flock lifecycle and unique flock code",
      PO02: "Daily mortality recorded",
      PO03: "Feed consumption logged",
      PO04: "Vaccine schedule, with one flock deliberately overdue",
      PO05: "Weight curve recorded",
      PO06: "Egg output tested as Layer-only, with a real negative test against a Broiler flock",
      PO07: "Sale/harvest with server-recomputed cost, profit, and livability",
    },
    businessFlowSummary:
      "One Broiler flock and one Layer flock are placed as day-old chicks into empty houses, tracked through feed, vaccination, weight, mortality, and (Layer-only) egg production, then both sold as poultry sale lots with cost, profit, and livability computed from recorded history.",
  },

  "IP-LIVESTOCK-CATTLE": {
    goldenDemoLabel: "Golden Demo #13",
    testIds: ["CT01", "CT02", "CT03", "CT04", "CT05", "CT06", "CT07"],
    testDescriptions: {
      CT01: "Pedigree: sire/dam linkage, sex-validated and unique",
      CT02: "Reproduction lifecycle: service → confirmed pregnant → calving",
      CT03: "Milk record, female-only",
      CT04: "Treatment (e.g. mastitis) recorded",
      CT05: "Feed ration logs",
      CT06: "Culling or sale as two distinct terminal outcomes",
      CT07: "Cost per animal or group, computed server-side",
    },
    businessFlowSummary:
      "An individually-tracked dairy herd (no pen/batch grouping, unlike the other farm demos) — a registered sire and dam are bred, producing a calf whose pedigree links back automatically; milking, mastitis treatment, and feed ration logs accrue against the dam; the calf is eventually sold to a dairy cooperative and the dam is culled to a meat trader, each with server-computed cost and profit.",
  },

  "IP-HATCHERY": {
    goldenDemoLabel: "Golden Demo #14",
    testIds: ["H01", "H02", "H03", "H04", "H05", "H06"],
    testDescriptions: {
      H01: "Egg batch traced to its parent stock",
      H02: "Incubator assignment follows an Empty → Occupied lifecycle guard",
      H03: "Hatch rate computed server-side from egg count",
      H04: "Chick grading total can't exceed the batch's initial count",
      H05: "Vaccination, with one deliberately overdue",
      H06: "Customer dispatch is traceable",
    },
    businessFlowSummary:
      "The deepest farm pipeline in the platform's demos — parent stock, egg batch, incubation, hatch result, chick batch, grading, vaccination, and dispatch — with one trace function walking the whole chain from parent stock through to the receiving customer.",
  },

  "IP-AQUAFEED": {
    goldenDemoLabel: "Golden Demo #15",
    testIds: ["AF01", "AF02", "AF03", "AF04", "AF05", "AF06", "AF07"],
    testDescriptions: {
      AF01: "Formula by species and life stage",
      AF02: "Pellet specification (size, buoyancy)",
      AF03: "Extrusion process recorded",
      AF04: "Batch QC",
      AF05: "Lot trace, reusing the compound feed golden demo's genealogy logic unmodified",
      AF06: "Finished-feed release gate, reusing the pharma golden demo's own hook",
      AF07: "Yield computed from actual output",
    },
    businessFlowSummary:
      "One of the most reuse-heavy golden demos in the platform — two shrimp feed products (a post-larvae stage and a grower stage, with different pellet specs) go through the same purchase, manufacture, extrusion-log, QC, and release pipeline every prior manufacturing golden demo already proved.",
  },

  "IP-AQUA-ENVIRONMENT": {
    goldenDemoLabel: "Golden Demo #16",
    testIds: ["AE01", "AE02", "AE03", "AE04", "AE05", "AE06"],
    testDescriptions: {
      AE01: "Formula revision",
      AE02: "Batch/lot tracking",
      AE03: "QC",
      AE04: "Label version, reusing the DMS document lifecycle",
      AE05: "Release gate, reusing the pharma golden demo's own hook",
      AE06: "Distribution trace, reusing the pharma distribution golden demo's own trace function unmodified",
    },
    businessFlowSummary:
      "The leanest golden demo in the platform (zero new record types) — a pond-water probiotic (Bacillus subtilis) is purchased, manufactured, QC'd, released, revised to a new formula version, given a labeled document version, and distributed to a new dealer, entirely through machinery already proven by 15 prior golden demos.",
  },

  "IP-FISH": {
    goldenDemoLabel: "Golden Demo #17",
    testIds: ["FF01", "FF02", "FF03", "FF04", "FF05", "FF06", "FF07"],
    testDescriptions: {
      FF01: "Pond stocking flips it from Empty to Stocked",
      FF02: "Biomass estimate, computed server-side as part of growth sampling",
      FF03: "Feed logged",
      FF04: "Growth sample recorded",
      FF05: "Mortality recorded",
      FF06: "Harvest KPIs: survival rate, feed-conversion ratio, cost per kilogram",
      FF07: "Traceability from farm through pond, species, and harvest",
    },
    businessFlowSummary:
      "A Pangasius (Cá Tra) pond in An Giang province is stocked, tracked through feed, growth sampling, and mortality, before a harvest computes realistic survival-rate, feed-conversion, and cost KPIs from the batch's own recorded history.",
    notableBugsFixed: [
      "A biomass-estimate calculation summed all mortality with no date filter, and growth samples were seeded out of chronological order, producing two identical (wrong) population estimates — fixed by filtering by date and reordering the seed sequence.",
    ],
  },

  "IP-AQUA-HATCHERY": {
    goldenDemoLabel: "Golden Demo #18",
    testIds: ["AH01", "AH02", "AH03", "AH04", "AH05", "AH06"],
    testDescriptions: {
      AH01: "Broodstock trace and duplicate-tag uniqueness",
      AH02: "Spawning batch, sex-validated parents",
      AH03: "Larval survival rate computed server-side from egg count",
      AH04: "Nursery batch creation, grading total constrained to the initial count",
      AH05: "Health record",
      AH06: "Seed batch dispatch to a real customer",
    },
    businessFlowSummary:
      "A whiteleg-shrimp broodstock hatchery in Ninh Thuan province: broodstock → spawning → larval batch → nursery → graded seed batch (Grade A, Grade B, and reject) → dispatch to a new dealer customer group.",
  },

  "IP-SEAFOOD-PROCESSING": {
    goldenDemoLabel: "Golden Demo #19",
    testIds: ["SP01", "SP02", "SP03", "SP04", "SP05", "SP06", "SP07", "SP08"],
    testDescriptions: {
      SP01: "Harvest lot receiving, sourced from a real upstream shrimp harvest record",
      SP02: "Grade/yield computed server-side, blocked from exceeding received weight",
      SP03: "Processing batch (e.g. peeled)",
      SP04: "Packing lot",
      SP05: "Cold storage record",
      SP06: "Shipment closes the packing/cold-storage lifecycle",
      SP07: "One consolidated trace from carton back through batch, harvest, and pond",
      SP08: "Recall simulation, reusing the QMS golden demo's recall record as-is",
    },
    businessFlowSummary:
      "Plugs directly into the shrimp farm golden demo's real harvest record (not synthetic data) — receiving, grading, processing, packing into cartons, cold storage, and shipment to a Japanese export customer, with a full farm-to-carton trace resolving all the way back to the originating pond.",
  },

  "IP-SUPPLEMENT": {
    goldenDemoLabel: "Golden Demo #20",
    testIds: ["S01", "S02", "S03", "S04", "S05", "S06"],
    testDescriptions: {
      S01: "A formula revision doesn't retroactively change an already-manufactured batch",
      S02: "Allergen/critical-ingredient flag on a formula component",
      S03: "Artwork version, reusing the DMS document lifecycle",
      S04: "Batch expiry computed by a shelf-life rule",
      S05: "Certificate of Analysis generated from an Approved LIMS result, full chain",
      S06: "Traceability from ingredient through lots to customers",
    },
    businessFlowSummary:
      "Produces a Vitamin C effervescent tablet (a formula that genuinely contains the allergen soy lecithin) through purchase, manufacture, QC, and release; revises the formula without altering the already-manufactured batch; versions its artwork document; runs the batch through the full LIMS chain to produce a Certificate of Analysis; and distributes it with full traceability.",
    notableBugsFixed: [
      "Reusing a shared LIMS analyst account across demos broke an earlier golden demo's own review-segregation check by non-deterministically matching this demo's own result instead — fixed by scoping the check to a specific specification.",
    ],
  },

  "IP-COSMETICS": {
    goldenDemoLabel: "Golden Demo #21",
    companyName: "Demo Cosmetics Co.",
    testIds: ["C01", "C02", "C03", "C04", "C05", "C06"],
    testDescriptions: {
      C01: "Formula revision",
      C02: "Bulk-batch and packed-batch genealogy across a two-stage manufacturing process",
      C03: "Packaging/artwork version",
      C04: "Stability sample schedule across multiple conditions and time points",
      C05: "A complaint traces back to the specific batch and customer",
      C06: "Rework doesn't lose genealogy",
    },
    businessFlowSummary:
      "Demo Cosmetics Co.'s first genuine two-stage manufacturing flow: a Bulk batch is QC-released, then consumed as an ingredient by a Packed batch, itself QC-released — the finished-goods release gate fires twice with no changes to the underlying mechanism. A stability schedule, a customer complaint tied to a real delivered batch, and a rework (reprocessing remaining Bulk stock) all prove genealogy survives real stock movements.",
    notableBugsFixed: [
      "A manufacturing work order defaulted to multi-level explosion, silently exploding the Bulk ingredient into its own raw materials instead of consuming it as a single item.",
      "A rework step tried to consume the full original batch quantity, but most was already used by packed production — fixed to compute the actual remaining quantity dynamically.",
      "Batch-lookup logic picked the wrong batch once a second batch of the same item existed — fixed to identify the batch by which work order actually produced it.",
    ],
  },

  "IP-MEDICAL-DEVICE": {
    goldenDemoLabel: "Golden Demo #22",
    companyName: "Demo MedDevice Co.",
    testIds: ["MD01", "MD02", "MD03", "MD04", "MD05", "MD06", "MD07"],
    testDescriptions: {
      MD01: "Serial number uniqueness",
      MD02: "Only an Approved design-change record's BOM can become the default",
      MD03: "A critical supplier must be Approved before a purchase order is allowed",
      MD04: "A failed incoming inspection blocks moving material into work-in-progress",
      MD05: "A finished serial number traces back to its consumed components",
      MD06: "A complaint links to a specific serial number or lot",
      MD07: "Overdue equipment calibration blocks a configured work-order operation",
    },
    businessFlowSummary:
      "Dual-tracks a finished device by both batch AND serial number. A critical supplier must be Approved before purchasing; a BOM revision needs an Approved design-change record; components pass incoming inspection (one batch deliberately rejected) before reaching work-in-progress; assembly is blocked against equipment with overdue calibration; the finished serialized device traces back to its components and to a customer complaint.",
    notableBugsFixed: [
      "A material transfer into work-in-progress moved only one of four required components, causing an opaque valuation error during assembly.",
      "Asset-category setup initially omitted a required accounts table, a gap first found back in the pharma golden demo's own EAM step.",
    ],
  },

  "IP-PHARMACY": {
    goldenDemoLabel: "Golden Demo #23",
    testIds: ["RX01", "RX02", "RX03", "RX04", "RX05", "RX06", "RX07"],
    testDescriptions: {
      RX01: "A store sees only its own stock",
      RX02: "Head-office replenishment to a store",
      RX03: "An expired product is blocked at the point of sale",
      RX04: "Inter-store batch transfer",
      RX05: "Point-of-sale return, correctly reversing payment records",
      RX06: "Promotion pricing applies automatically",
      RX07: "A central dashboard aggregates stock and sales across stores",
    },
    businessFlowSummary:
      "A multi-branch pharmacy chain: head office purchases centrally, replenishes Store A, transfers stock from Store A to Store B, sells and returns through point-of-sale, applies a promotion, and blocks an expired-batch sale at the register — rolled into a central stock/sales dashboard.",
    notableBugsFixed: [
      "A site-level point-of-sale configuration setting blocked any non-return sale outright until corrected.",
      "A point-of-sale return correctly reversed line items but not its own payment record, a mismatch caught immediately on save.",
      "An idempotency guard checked live stock balance instead of whether the transaction already existed, silently re-triggering replenishment on every re-run.",
    ],
  },

  "IP-3PL-COLDCHAIN": {
    goldenDemoLabel: "Golden Demo #24",
    testIds: ["W01", "W02", "W03", "W04", "W05", "W06"],
    testDescriptions: {
      W01: "One client cannot see another client's stock",
      W02: "A temperature excursion automatically creates an event",
      W03: "FEFO outbound picking",
      W04: "Quarantined stock is blocked from shipping until QC-released",
      W05: "Inventory reconciliation corrects a count discrepancy",
      W06: "Billing aggregates real service usage per client",
    },
    businessFlowSummary:
      "A cold-chain 3PL warehouse operator holds segregated stock for two clients, each with its own quarantine/released pair and temperature band: portal users see only their own client's stock, temperature excursions are flagged automatically, outbound follows FEFO, quarantined stock can't ship until released, a stock reconciliation corrects a count discrepancy, and billing is aggregated per client from real ledger and delivery data.",
    notableBugsFixed: [
      "Auto-generated batch expiry dates didn't read the actual expiry entered at receiving, silently defeating the FEFO test until fixed.",
      "A stock reconciliation scoped to one batch initially set that batch's absolute quantity rather than adjusting the warehouse total correctly.",
      "The first sales invoice on this pack required a company accounting setting no prior golden demo had ever needed.",
    ],
  },

  "IP-CONSUMER-DIST": {
    goldenDemoLabel: "Golden Demo #25",
    companyName: "Demo Consumer Distribution Co.",
    testIds: ["CD01", "CD02", "CD03", "CD04", "CD05", "CD06"],
    testDescriptions: {
      CD01: "Dealer-specific price list",
      CD02: "Promotion validity window, tested on both edges",
      CD03: "Sales correctly attributed to a sales territory",
      CD04: "Dealer credit limit enforcement",
      CD05: "A return automatically carries forward the original batch",
      CD06: "Commission report aggregated from real sales data",
    },
    businessFlowSummary:
      "Distributes finished goods from two upstream golden demos (the Vitamin C effervescent tablet and the facial cleanser) through a two-territory dealer network — dealer-tier pricing, a time-boxed promotion, territory-attributed sales, dealer credit limits, a partial return, and a commission report all resolve from the platform's native schema with essentially no custom code.",
    notableBugsFixed: [
      "Two prior golden demos' own integrity checks did unscoped batch lookups that had worked until this demo created a second batch of the same shared item — fixed with a proper batch-to-ledger join.",
      "A sales-flow lookup wasn't scoped to exclude returns, so once a return existed it created a bogus second invoice from the return itself, corrupting commission totals.",
    ],
  },

  "IP-PREMIX": {
    goldenDemoLabel: "Golden Demo #26",
    companyName: "Demo Premix Co.",
    testIds: ["PM01", "PM02", "PM03", "PM04", "PM05", "PM06", "PM07"],
    testDescriptions: {
      PM01: "Micro-ingredient weighing tolerance, tighter than compound feed's generic tolerance",
      PM02: "A critical ingredient requires a second person's verification before manufacture",
      PM03: "Mixing must follow the formula's declared sequence order",
      PM04: "A formula requires Approved status to become the default",
      PM05: "Lot trace, reusing the compound feed golden demo's genealogy logic unmodified",
      PM06: "Potency stays within tolerance on the Certificate of Analysis",
      PM07: "Yield and reconciliation",
    },
    businessFlowSummary:
      "Demo Premix Co. produces a vitamin/mineral concentrate for feed mills: a bulk carrier dilutes several gram-scale micro-ingredients (including safety-critical selenium) mixed in a specific declared sequence, with the critical ingredient requiring a second person's verification before manufacture, tighter micro-weighing tolerance than generic feed manufacturing, and a Certificate of Analysis confirming potency.",
    notableBugsFixed: [
      "An unrelated demo's own BOM-approval check was unscoped and blocked any new default formula platform-wide until scoped correctly to its own company.",
      "An initial tolerance test picked a deviation value that was intercepted by a different, more generic tolerance check before ever reaching this demo's own tighter check — fixed by choosing a value strictly between the two thresholds.",
    ],
  },

  "IP-INGREDIENT-TRADING": {
    goldenDemoLabel: "Golden Demo #27",
    companyName: "Demo Ingredient Trading Co.",
    testIds: ["FT01", "FT02", "FT03", "FT04", "FT05", "FT06", "FT07"],
    testDescriptions: {
      FT01: "Shipment quantity reconciliation: ordered vs. received vs. invoiced",
      FT02: "Foreign-exchange handling on an import purchase",
      FT03: "Supplier lot is traceable",
      FT04: "Incoming QC gates release",
      FT05: "A committed-quantity contract blocks over-commitment",
      FT06: "Price history across multiple dated price records",
      FT07: "Margin report from real purchase vs. sales data",
    },
    businessFlowSummary:
      "A pure trading company (no manufacturing) importing soybean meal and fish meal with real FX exposure and transit shrinkage, receiving with incoming QC, reselling to domestic feed mills under a committed-quantity contract, and tracking price history and margin per ingredient.",
    notableBugsFixed: [
      "An early draft referenced a field that only exists on sales orders, not purchase orders, causing a database error.",
      "A foreign-currency purchase invoice failed against the company's local-currency-only default account until a dedicated foreign-currency account was set up.",
      "A quality-inspection reading value that worked on the development site was rejected on the production site because of a locale-specific number format difference.",
    ],
  },

  "IP-MEAT-PROCESSING": {
    goldenDemoLabel: "Golden Demo #28",
    companyName: "Dong Nai Meat Processing Plant",
    testIds: ["MP01", "MP02", "MP03", "MP04", "MP05", "MP06", "MP07"],
    testDescriptions: {
      MP01: "Incoming lot sourced from a real upstream pig sale lot",
      MP02: "Two-stage yield (live weight → carcass → cut), each stage blocked from exceeding its input",
      MP03: "Multi-source processing-batch genealogy, one batch consuming two incoming lots",
      MP04: "A QC hold blocks packing until released",
      MP05: "Cold storage record",
      MP06: "A finished lot traces back to its source animal and farm",
      MP07: "A recall-impact query resolves either upstream lot to the same downstream distributed lot",
    },
    businessFlowSummary:
      "Dong Nai Meat Processing Plant receives two incoming pig lots — one a real, already-sold lot from the pig-farm golden demo, the other a self-contained direct-farm intake — processes both together into one batch, holds it for QC before packing, cold-stores it, and distributes it to a customer, with a recall-impact query proving either incoming lot traces to the same finished, distributed lot.",
    notableBugsFixed: [
      "A finished-lot's total packed weight was marked read-only but nothing computed it server-side, so it silently saved as empty on the first run.",
    ],
  },
};

export function getPackContent(packCode: string): IndustryPackContent | undefined {
  return PACK_CONTENT[packCode];
}
