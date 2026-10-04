// Curated "Operation" and "Software" tags per Industry Pack, for the `/solutions` page's
// filter UI (P1 reviewer feedback: 27 packs as one undifferentiated list is hard to navigate).
//
// SOURCING: every tag below is derived directly from `industryPackContent.ts`'s own real,
// documented `businessFlowSummary`/`testDescriptions` for that pack (itself sourced from
// `documents/project_status.md`'s golden-demo write-ups — see that file's header comment), or
// for IP-VETERINARY-BIOLOGICAL (no golden demo at all) from `NOT_YET_BUILT_NOTE`'s own
// paraphrase of the master plan's intended scope. Nothing here is guessed or copy-pasted
// across unrelated packs — e.g. only packs whose real business flow actually reaches a
// customer/dealer/store are tagged "Distribution"/"Retail"; only packs whose real flow is a
// standalone quality/document/lab/equipment system are tagged with that specific Operation.
//
// TWO DIMENSIONS:
//   - `operations`: the real business FUNCTION(S) the pack's golden demo actually exercises
//     (what a buyer clicks through), e.g. "manufacturing", "farm", "retail".
//   - `software`: the real platform MODULE(S)/system(s) that operation runs on, e.g. "erp",
//     "qms", "farmManagement". A pack commonly has 1-3 of each.
//
// Both sets of keys are translated in messages/{vi,en}.json under `solutions.operations.*` and
// `solutions.software.*` — this file only supplies the canonical keys and per-pack mapping.

export const OPERATION_KEYS = [
  "manufacturing",
  "quality",
  "laboratory",
  "documentControl",
  "assetMaintenance",
  "farm",
  "processing",
  "distribution",
  "retail",
  "warehousing",
  "trading",
] as const;

export type OperationKey = (typeof OPERATION_KEYS)[number];

export const SOFTWARE_KEYS = [
  "erp",
  "qms",
  "dms",
  "lims",
  "eamCmms",
  "wms",
  "farmManagement",
  "crm",
  "pos",
] as const;

export type SoftwareKey = (typeof SOFTWARE_KEYS)[number];

export interface PackTags {
  operations: OperationKey[];
  software: SoftwareKey[];
}

export const PACK_TAGS: Record<string, PackTags> = {
  // Full GMP pharma manufacturing (Golden Demo #1) extended into wholesale distribution with
  // FEFO/credit-limit/recall (Golden Demo #2) — real manufacturing + real distribution flow.
  "IP-PHARMA": { operations: ["manufacturing", "quality", "distribution"], software: ["erp", "qms", "wms"] },

  // Standalone Deviation/CAPA/Change Control/OOS/audit/recall system — pure quality function.
  "IP-QMS": { operations: ["quality"], software: ["qms"] },

  // Standalone document lifecycle + training-assignment system.
  "IP-DMS": { operations: ["documentControl"], software: ["dms"] },

  // Standalone sample/test/COA lab system.
  "IP-LIMS": { operations: ["laboratory"], software: ["lims"] },

  // Standalone calibration/qualification/breakdown-repair equipment system.
  "IP-EAM": { operations: ["assetMaintenance"], software: ["eamCmms"] },

  // Compound feed manufacturing with its own QC release gate and cross-contamination control.
  "IP-FEED": { operations: ["manufacturing", "quality"], software: ["erp", "qms"] },

  // Pond stocking through harvest — real farm operations, no manufacturing/distribution step.
  "IP-SHRIMP": { operations: ["farm"], software: ["farmManagement"] },

  // Injectable manufacturing (Golden Demo #9) distributed to a regional dealer with territory/
  // credit/technical-visit tracking (Golden Demo #10) — manufacturing + real dealer distribution.
  "IP-VETERINARY": { operations: ["manufacturing", "distribution"], software: ["erp", "crm"] },

  // Not yet built (zero seed data, confirmed live) — intended scope per NOT_YET_BUILT_NOTE is
  // biological batch manufacturing/genealogy; no software module was ever actually wired up.
  "IP-VETERINARY-BIOLOGICAL": { operations: ["manufacturing"], software: [] },

  "IP-LIVESTOCK-PIG": { operations: ["farm"], software: ["farmManagement"] },
  "IP-LIVESTOCK-POULTRY": { operations: ["farm"], software: ["farmManagement"] },
  "IP-LIVESTOCK-CATTLE": { operations: ["farm"], software: ["farmManagement"] },

  // Parent stock -> egg batch -> incubation -> chick batch -> dispatch — a farm-family
  // operation (rearing/breeding), not manufacturing or distribution.
  "IP-HATCHERY": { operations: ["farm"], software: ["farmManagement"] },

  // Aquafeed manufacturing reusing the compound-feed manufacturing/QC/release pipeline.
  "IP-AQUAFEED": { operations: ["manufacturing", "quality"], software: ["erp", "qms"] },

  // Probiotic manufacturing, QC, release, and distribution to a dealer — leanest golden demo,
  // zero new record types, entirely reused manufacturing + distribution machinery.
  "IP-AQUA-ENVIRONMENT": { operations: ["manufacturing", "distribution"], software: ["erp"] },

  "IP-FISH": { operations: ["farm"], software: ["farmManagement"] },
  "IP-AQUA-HATCHERY": { operations: ["farm"], software: ["farmManagement"] },

  // Receiving, grading, processing, packing, cold storage, shipment — real processing +
  // warehousing (cold storage) flow, not farm or manufacturing.
  "IP-SEAFOOD-PROCESSING": { operations: ["processing", "warehousing"], software: ["erp", "wms"] },

  // Nutraceutical manufacturing with a full LIMS-backed Certificate of Analysis chain.
  "IP-SUPPLEMENT": { operations: ["manufacturing", "quality"], software: ["erp", "qms", "lims"] },

  // Two-stage (bulk -> packed) cosmetics manufacturing with stability studies and complaints.
  "IP-COSMETICS": { operations: ["manufacturing", "quality"], software: ["erp", "qms"] },

  // Supplier qualification, incoming inspection, serialized assembly, complaint trace.
  "IP-MEDICAL-DEVICE": { operations: ["manufacturing", "quality"], software: ["erp", "qms"] },

  // Multi-branch pharmacy chain: replenishment, inter-store transfer, point-of-sale, promotions
  // — a real retail/POS operation, not manufacturing.
  "IP-PHARMACY": { operations: ["retail"], software: ["pos", "wms"] },

  // Cold-chain 3PL warehouse operator holding segregated client stock — pure warehousing.
  "IP-3PL-COLDCHAIN": { operations: ["warehousing"], software: ["wms"] },

  // Distributes finished goods from two upstream demos through a dealer network — pricing,
  // territory, credit, commission — a real distribution operation.
  "IP-CONSUMER-DIST": { operations: ["distribution"], software: ["erp", "crm"] },

  // Vitamin/mineral premix manufacturing with tighter micro-weighing tolerance and dual
  // verification for critical ingredients.
  "IP-PREMIX": { operations: ["manufacturing", "quality"], software: ["erp", "qms"] },

  // Pure trading company (no manufacturing) — import, incoming QC, resale under contract,
  // price history, margin reporting.
  "IP-INGREDIENT-TRADING": { operations: ["trading", "quality"], software: ["erp", "qms"] },

  // Receives incoming pig lots, processes into batches, QC hold before packing, cold storage,
  // distribution — real processing + warehousing + distribution flow.
  "IP-MEAT-PROCESSING": { operations: ["processing", "warehousing", "distribution"], software: ["erp", "wms"] },
};

export function getPackTags(packCode: string): PackTags | undefined {
  return PACK_TAGS[packCode];
}
