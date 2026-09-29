# User Guides — Enterprise Platform

Documentation written for the people who actually use this platform day to day — QA managers, farm managers, quality directors, warehouse staff, and the farm customers using its self-service portal — not for engineers reading a build log. If you're looking for build history, technical task tracking, or verification evidence, see `documents/project_status.md` and the master plan instead; this directory is deliberately free of internal task codes and build-process narration.

## What's covered here — and what isn't (read this first)

This platform has roughly **28 "golden demo" business scenarios** across manufacturing, farm/livestock, and other verticals, plus several customer-facing portal websites. **This documentation set covers 5 of them, in full, plus one platform-wide administrator guide.** These 5 were chosen because they are the exact same 5 real, verified scenarios built into the platform's own **Guided Demo Mode** ("Start Demo" button, found under the Guided Demo Scenario list in Desk) — so the written guides below and the live click-through walkthrough tell the same real story, one in prose, one as an interactive Desk dialog.

**Covered in full (Quick Start + Role Guide + Process Guide each):**

| # | Scenario | Industry | Primary role covered |
|---|---|---|---|
| 1 | [Pharmaceutical Batch Release](pharma-batch-release/quick-start.md) | Pharmaceutical manufacturing | QC Manager |
| 2 | [Cosmetics Batch Stability & Complaint Traceability](cosmetics-stability-complaint/quick-start.md) | Cosmetics manufacturing | QA Manager |
| 3 | [Pig Farm — Breeding to Sale](pig-farm-breeding-to-sale/quick-start.md) | Livestock / pig farming | Farm Manager |
| 4 | [AI QMS Copilot — Deviation to CAPA](ai-qms-copilot-capa-approval/quick-start.md) | Quality management + AI | Quality Director |
| 5 | [Farm Customer Portal — Orders & Technical Visits](farm-portal-technical-visit/quick-start.md) | Veterinary / customer self-service portal | Farm Customer |

**Plus one platform-wide guide:**

- [**Administrator Guide**](administrator-guide.md) — Industry Packs/editions, seeding & reset, roles & permissions (including the User Permission-based portal scoping pattern), the AI Provider/Model/Policy layer, and where to find and extend Guided Demo Mode's scenarios. This single guide covers platform administration generally, rather than one Administrator Guide per scenario — matching how these concerns actually work (they're system-wide settings, not per-transaction-type ones).

**Honestly NOT covered yet:** the other ~23 golden demos (the platform's other Quality Management workflows beyond the AI-copilot angle, Document Management, Laboratory Information Management, Equipment/Asset Management as a standalone module, Feed manufacturing, Shrimp/Aquaculture farming, every other Livestock/Aqua/Commercial-vertical golden demo not listed above) and the platform's other customer/partner-facing portal sites (the 3PL client portal, the dealer portal, the supplier portal, and others) do **not** have a written guide in this directory yet. Do not read this documentation set as implying broader coverage than what's listed above — if you need a guide for one of these, that's a real, open piece of work, not something already done and merely unlinked.

## How each guide is structured

Every scenario has three documents, each aimed at a different need:

1. **Quick Start** — 5 to 10 minutes. Gets you oriented and looking at real, working records fast. Start here if you're new to a scenario or demoing it to someone else for the first time.
2. **Role Guide** — everything the single most central role in that scenario needs to do their actual job in the system: how to create, review, approve, amend, cancel, which reports to use, common errors, and FAQ.
3. **Process Guide** — the complete end-to-end business process, across every role involved, told as one continuous story from start to finish. Read this when you need the whole picture, not just one person's slice of it.

## Navigating by role

| If you are a... | Start with |
|---|---|
| QC Manager (pharmaceutical manufacturing) | [Pharma Batch Release → Role Guide](pharma-batch-release/role-guide-qc-manager.md) |
| QA Manager (cosmetics) | [Cosmetics Stability & Complaint → Role Guide](cosmetics-stability-complaint/role-guide-qa-manager.md) |
| Farm Manager (pig farm) | [Pig Farm Breeding to Sale → Role Guide](pig-farm-breeding-to-sale/role-guide-farm-manager.md) |
| Quality Director (AI-assisted CAPA approval) | [AI QMS Copilot → Role Guide](ai-qms-copilot-capa-approval/role-guide-quality-director.md) |
| A farm customer using the self-service portal | [Farm Portal → Role Guide](farm-portal-technical-visit/role-guide-farm-customer.md) |
| A platform administrator | [Administrator Guide](administrator-guide.md) |
| A salesperson giving a live demo | Any scenario's Quick Start, plus the platform's own **Guided Demo Mode** ("Start Demo" button on the matching Guided Demo Scenario record) for a click-through version with direct record links |

## A note on accuracy

Every specific claim in these guides — field names, button labels, role names, error messages, record structures — was checked against the platform's real, running code and live data before being written, not invented from a plausible-sounding guess. Where a genuine gap exists in the platform today (for example, some verticals not yet having dedicated demo logins, or one AI feature currently being triggered by a backend call rather than a Desk button), that gap is stated plainly in the relevant guide rather than glossed over or worked around silently in the documentation.
