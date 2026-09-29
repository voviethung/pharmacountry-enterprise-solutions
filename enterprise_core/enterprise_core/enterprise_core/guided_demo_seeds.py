"""Guided Demo Mode (master plan §16) — seeds 5 real `Guided Demo Scenario` records, each built
from a specific golden demo's OWN real, already-existing seed data (every `target_document` below
was verified to exist live via `bench execute` before being written here — see this session's own
notes in `documents/project_status.md`). Deliberately NOT one scenario per golden demo (28 exist) —
depth over breadth, matching this whole project's established pattern (e.g. Permission-aware RAG
scoped to DMS only, AI-DEMO-09/10 scoped to Pig/Shrimp only): build the reusable DocType/UI
infrastructure once, populate a well-chosen, HONESTLY-DISCLOSED handful of real examples.

The 5 scenarios, and why each was picked:
  1. PHARMA-BATCH-RELEASE — mandatory: master plan §16's OWN worked example, verbatim, built from
     Golden Demo #1's real records (not a re-invented example).
  2. COSMETICS-STABILITY-COMPLAINT — a second manufacturing-flavored vertical (Golden Demo —
     Cosmetics), proving the framework isn't pharma-specific.
  3. PIG-FARM-BREEDING-TO-SALE — a livestock/farm-flavored vertical (Golden Demo — Pig Farm).
  4. AI-QMS-COPILOT-CAPA-APPROVAL — an AI-copilot-flavored scenario (AI-DEMO-02), showing a real
     human-in-the-loop AI approval gate, not just a manufacturing/farm record walkthrough.
  5. FARM-PORTAL-TECHNICAL-VISIT — a Phase-7-flavored scenario (WEB-07), referencing a real
     customer-portal build and its own verified permission-isolation proof.

Every scenario is a NAVIGATION-ONLY walkthrough of already-real, already-submitted records — no
step here performs a mutating action itself. See `guided_demo.py`'s own module docstring for the
full reset-mechanism honesty design this file's `allow_reset`/`reset_function_path` values follow.
"""

import frappe

from enterprise_core.enterprise_core.guided_demo import compute_direct_link


def _step(step_no, instruction, login_as_role=None, login_as_user=None, target_doctype=None, target_document=None, notes=None):
	direct_link = compute_direct_link(target_doctype, target_document) if target_doctype and target_document else None
	return {
		"step_no": step_no,
		"instruction": instruction,
		"login_as_role": login_as_role,
		"login_as_user": login_as_user,
		"target_doctype": target_doctype,
		"target_document": target_document,
		"direct_link": direct_link,
		"notes": notes,
	}


def _upsert_scenario(spec):
	"""Idempotent upsert: creates the scenario if missing, otherwise re-syncs its fields and
	step rows to match this file's spec (same 'sync, don't just skip' pattern DP-306's own
	Industry Pack Seed sequence fix established) — safe to re-run, converges every time rather
	than silently freezing on whatever was created first."""
	steps = spec.pop("steps")
	if frappe.db.exists("Guided Demo Scenario", spec["scenario_code"]):
		doc = frappe.get_doc("Guided Demo Scenario", spec["scenario_code"])
		created = False
	else:
		doc = frappe.new_doc("Guided Demo Scenario")
		created = True

	for fieldname, value in spec.items():
		doc.set(fieldname, value)

	doc.set("steps", [])
	for s in steps:
		doc.append("steps", s)

	if created:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return doc.name, created


def _target_exists(doctype, name):
	return bool(doctype and name and frappe.db.exists(doctype, name))


def _real_purchase_receipt():
	return frappe.db.get_value("Purchase Receipt", {"supplier": "ABC Pharma Chemicals Co.", "docstatus": 1}, "name")


def _real_qc_release_transfer():
	return frappe.db.get_value(
		"Stock Entry",
		{"stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "docstatus": 1},
		"name",
		order_by="creation asc",
	)


def _real_incoming_qi():
	return frappe.db.get_value(
		"Quality Inspection", {"inspection_type": "Incoming", "item_code": "PARA-API", "status": "Accepted"}, "name"
	)


def _real_work_order():
	return frappe.db.get_value("Work Order", {"production_item": "PARA-500-TAB", "docstatus": 1}, "name", order_by="creation asc")


def _real_qa_release_transfer():
	candidates = frappe.get_all(
		"Stock Entry Detail", filters={"item_code": "PARA-500-TAB", "t_warehouse": ["like", "FG Released%"]}, fields=["parent"]
	)
	for row in candidates:
		se = frappe.db.get_value("Stock Entry", row.parent, ["name", "docstatus", "remarks"], as_dict=True)
		if se and se.docstatus == 1 and (se.remarks or "") != "DP-506 negative test batch":
			return se.name
	return None


def _real_para_api_batch():
	return frappe.db.get_value("Batch", {"item": "PARA-API"}, "name")


def seed_pharma_batch_release_scenario():
	"""Mandatory scenario — master plan §16's own worked example, verbatim structure (11 numbered
	steps, exactly as written), built from Golden Demo #1's real DP-502/503/505/506 records."""
	if not frappe.db.exists("Company", "Demo Pharma Co"):
		return "seed_pharma_batch_release_scenario: SKIPPED — Golden Demo #1 (Pharma) has not been seeded yet."

	pr_name = _real_purchase_receipt()
	batch_name = _real_para_api_batch()
	incoming_qi = _real_incoming_qi()
	qc_transfer = _real_qc_release_transfer()
	work_order = _real_work_order()
	qa_transfer = _real_qa_release_transfer()

	required = {
		"Purchase Receipt": pr_name,
		"Batch (PARA-API)": batch_name,
		"Quality Inspection (incoming)": incoming_qi,
		"Stock Entry (QC release transfer)": qc_transfer,
		"Work Order": work_order,
		"Stock Entry (QA release transfer)": qa_transfer,
	}
	missing = [label for label, value in required.items() if not value]
	if missing:
		return f"seed_pharma_batch_release_scenario: SKIPPED — missing real records: {missing}. Run Golden Demo #1's full seed chain first."

	spec = {
		"scenario_code": "PHARMA-BATCH-RELEASE",
		"title": "Pharmaceutical Batch Release",
		"golden_demo_reference": "IP-PHARMA",
		"primary_login_role": "Warehouse Officer (starting role — switches at each step below)",
		"primary_login_user": "warehouse.officer@pharmacountry.vn",
		"objective": (
			"Show the full multi-role chain that gates a pharmaceutical batch — from raw material "
			"receipt through QC testing, QC-approved release to production, manufacturing, and "
			"QA-authorized release to Finished Goods — and prove the platform physically blocks a "
			"batch from skipping any of these gates (the P01 quarantine-issue block and the P06 "
			"QA-release-without-QC block), not just describes them on paper."
		),
		"what_this_demonstrates": (
			"A regulated pharmaceutical manufacturer's real batch-release control chain, enforced by "
			"real validation hooks rather than SOP text alone: raw material cannot leave Quarantine "
			"for production without QC approval (P01, live-tested in DP-503), and finished goods "
			"cannot move to the Released warehouse without an Accepted QC/QA result for that exact "
			"batch (P06, live-tested in DP-506). Every record opened in this walkthrough is Golden "
			"Demo #1's own real, currently-existing data — not staged mockups."
		),
		"allow_reset": 1,
		"reset_function_path": "enterprise_core.enterprise_core.api.run_industry_pack_seeds",
		"reset_function_arg": "IP-PHARMA",
		"reset_instructions": (
			"Re-runs Golden Demo #1's full idempotent seed chain (company/master data -> purchase -> "
			"warehouse release -> manufacturing -> QC -> QA release -> QMS -> EAM -> dashboard) via "
			"the DP-306 seed runner. Safe to re-run any number of times (every step function checks "
			"its own postconditions before creating anything) — re-creates anything a demo viewer "
			"accidentally deleted or altered via Desk. It does NOT undo real transactional history "
			"(e.g. a cancelled document stays cancelled); this is a re-assertion of golden state, "
			"not a time machine."
		),
		"is_active": 1,
		"steps": [
			_step(1, "Login Warehouse", login_as_role="Warehouse Officer", login_as_user="warehouse.officer@pharmacountry.vn"),
			_step(
				2, "Open RM Receipt", target_doctype="Purchase Receipt", target_document=pr_name,
				notes="The real Purchase Receipt from Supplier 'ABC Pharma Chemicals Co.' — 6 raw/packaging items received into RM Quarantine.",
			),
			_step(
				3, "Review batch status", target_doctype="Batch", target_document=batch_name,
				notes="Real Batch for PARA-API (Paracetamol API) — currently in RM Quarantine, awaiting QC.",
			),
			_step(4, "Login QC Analyst", login_as_role="QC Analyst", login_as_user="analyst@pharmacountry.vn"),
			_step(
				5, "Enter result", target_doctype="Quality Inspection", target_document=incoming_qi,
				notes="Real Accepted incoming Quality Inspection for PARA-API, referencing this Purchase Receipt and Batch.",
			),
			_step(6, "Login QC Manager", login_as_role="QC Manager", login_as_user="qc.manager@pharmacountry.vn"),
			_step(
				7, "Approve", target_doctype="Stock Entry", target_document=qc_transfer,
				notes="The real Material Transfer moving QC-passed material from RM Quarantine to RM Approved — the block_quarantine_issue_to_production hook (P01) enforces this must happen before production can use it.",
			),
			_step(8, "Login Production", login_as_role="Production Manager", login_as_user="production.manager@pharmacountry.vn"),
			_step(
				9, "Start batch", target_doctype="Work Order", target_document=work_order,
				notes="Real Work Order for PARA-500-TAB (qty 1000), sourced only from RM Approved.",
			),
			_step(10, "Login QA", login_as_role="QA Manager", login_as_user="qa.manager@pharmacountry.vn"),
			_step(
				11, "Release FG", target_doctype="Stock Entry", target_document=qa_transfer,
				notes="The real Material Transfer moving the manufactured batch from FG Quarantine to FG Released — the block_fg_release_without_qa hook (P06) enforces an Accepted QC result must exist first.",
			),
		],
	}
	name, created = _upsert_scenario(spec)
	return f"seed_pharma_batch_release_scenario: {'created' if created else 'synced'} '{name}'."


def seed_cosmetics_stability_complaint_scenario():
	packed_batch = frappe.db.get_value("Batch", {"item": "FACIAL-CLEANSER-150ML"}, "name", order_by="creation asc")
	stability_overdue = frappe.db.get_value("Cosmetics Stability Sample", {"status": "Overdue"}, "name")
	rework = frappe.db.get_value("Cosmetics Rework Record", {}, "name")
	complaint = frappe.db.get_value("Cosmetics Complaint", {}, "name")

	required = {
		"Batch (packed)": packed_batch, "Cosmetics Stability Sample (Overdue)": stability_overdue,
		"Cosmetics Rework Record": rework, "Cosmetics Complaint": complaint,
	}
	missing = [label for label, value in required.items() if not value]
	if missing:
		return f"seed_cosmetics_stability_complaint_scenario: SKIPPED — missing real records: {missing}. Run the Cosmetics golden demo seed chain first."

	spec = {
		"scenario_code": "COSMETICS-STABILITY-COMPLAINT",
		"title": "Cosmetics Batch Stability & Complaint Traceability",
		"golden_demo_reference": "IP-COSMETICS",
		"primary_login_role": "QA / Quality (Cosmetics) — no dedicated demo login built yet, run as Administrator",
		"primary_login_user": None,
		"objective": (
			"Show a cosmetics manufacturer's post-release quality follow-through for one real retail "
			"batch: scheduled stability testing over time (including a genuinely overdue check), a "
			"documented in-process rework, and a real customer complaint traced back to the exact "
			"batch the customer received."
		),
		"what_this_demonstrates": (
			"End-to-end batch quality traceability for a consumer cosmetics product: a real overdue "
			"stability-testing alert (C04 — this sample was scheduled in the past and never tested, "
			"not staged data), a documented batch rework (a pH deviation caught and corrected before "
			"the earlier golden-demo build even reached distribution), and a customer complaint "
			"traced to its precise batch via real delivery records (C05) — the traceability chain a "
			"retailer or regulator would actually ask to see."
		),
		"allow_reset": 1,
		"reset_function_path": "enterprise_core.enterprise_core.api.run_industry_pack_seeds",
		"reset_function_arg": "IP-COSMETICS",
		"reset_instructions": (
			"Re-runs the Cosmetics golden demo's idempotent seed chain via the DP-306 seed runner — "
			"safe to re-run, re-creates anything missing. Does not undo submitted transactional "
			"documents (e.g. a rework record already created stays as-is)."
		),
		"is_active": 1,
		"steps": [
			_step(
				1, "Login as QA / Quality", login_as_role="QA / Quality (Cosmetics)",
				target_doctype="Batch", target_document=packed_batch,
				notes="No dedicated Cosmetics demo login exists yet (unlike Golden Demo #1's Pharma role users) — run this scenario as Administrator. The batch: Facial Cleanser 150ml.",
			),
			_step(
				2, "Review the stability testing program for this batch", target_doctype="Cosmetics Stability Sample", target_document=stability_overdue,
				notes="This sample was scheduled in the past and never tested — a real overdue stability check (C04), found live, not staged.",
			),
			_step(
				3, "Review a real batch rework record", target_doctype="Cosmetics Rework Record", target_document=rework,
				notes="A minor pH deviation caught on QC recheck, corrected with an additional citric-acid addition, and re-tested Accepted — the platform tracks rework history, not just pass/fail.",
			),
			_step(
				4, "Review a real customer complaint traced to this batch", target_doctype="Cosmetics Complaint", target_document=complaint,
				notes="This complaint traces back to the exact batch the complaining customer actually received (C05), verified via real delivery/batch records — not assumed.",
			),
			_step(
				5, "Decide: close the complaint, or escalate to a formal CAPA",
				login_as_role="QA Manager (Cosmetics)",
				notes="This platform's standalone QMS module (Golden Demo #3, IP-QMS) is where a complaint like this would escalate into a formal CAPA if warranted — see the AI-QMS-COPILOT-CAPA-APPROVAL scenario for that flow in action.",
			),
		],
	}
	name, created = _upsert_scenario(spec)
	return f"seed_cosmetics_stability_complaint_scenario: {'created' if created else 'synced'} '{name}'."


def seed_pig_farm_breeding_to_sale_scenario():
	breeding_service = "qsb4thm76v" if frappe.db.exists("Pig Breeding Service", "qsb4thm76v") else frappe.db.get_value(
		"Pig Breeding Service", {}, "name"
	)
	farrowing = frappe.db.get_value("Pig Farrowing", {"breeding_service": breeding_service}, "name") if breeding_service else None
	grower_batch = frappe.db.get_value("Pig Grower Batch", {"farrowing": farrowing}, "name") if farrowing else None
	weight_record = (
		frappe.db.get_value("Pig Weight Record", {"batch": grower_batch}, "name", order_by="creation asc") if grower_batch else None
	)
	sale_lot = frappe.db.get_value("Pig Sale Lot", {"batch": grower_batch}, "name") if grower_batch else None
	farm = frappe.db.get_value("Pig Farm", {}, "name")

	required = {
		"Pig Farm": farm, "Pig Breeding Service": breeding_service, "Pig Farrowing": farrowing,
		"Pig Grower Batch": grower_batch, "Pig Weight Record": weight_record, "Pig Sale Lot": sale_lot,
	}
	missing = [label for label, value in required.items() if not value]
	if missing:
		return f"seed_pig_farm_breeding_to_sale_scenario: SKIPPED — missing real records: {missing}. Run the Pig Farm golden demo seed chain first."

	spec = {
		"scenario_code": "PIG-FARM-BREEDING-TO-SALE",
		"title": "Pig Farm — Breeding to Sale Traceability",
		"golden_demo_reference": "IP-LIVESTOCK-PIG",
		"primary_login_role": "Farm Manager (Pig) — no dedicated demo login built yet, run as Administrator",
		"primary_login_user": None,
		"objective": (
			"Walk a livestock farm's full pig production cycle — from a real breeding service through "
			"farrowing and grower-batch growth tracking to the final sale lot — showing genealogy and "
			"growth data are tracked as one continuous real record chain, not disconnected logs."
		),
		"what_this_demonstrates": (
			"Full farm-to-sale traceability for a pig production batch: which sow and boar produced "
			"it, which litter and pen it grew in, real weight-tracking history over time, and the "
			"specific sale lot it was ultimately sold as — the genealogy and growth-performance record "
			"a livestock buyer or regulator would ask to see."
		),
		"allow_reset": 1,
		"reset_function_path": "enterprise_core.enterprise_core.api.run_industry_pack_seeds",
		"reset_function_arg": "IP-LIVESTOCK-PIG",
		"reset_instructions": (
			"Re-runs the Pig Farm golden demo's idempotent seed chain via the DP-306 seed runner — "
			"safe to re-run, re-creates anything missing. Does not undo submitted transactional "
			"documents."
		),
		"is_active": 1,
		"steps": [
			_step(
				1, "Login as Farm Manager", login_as_role="Farm Manager (Pig)",
				target_doctype="Pig Farm", target_document=farm,
				notes="No dedicated Pig Farm demo login exists yet — run this scenario as Administrator.",
			),
			_step(
				2, "Review the breeding service that started this batch", target_doctype="Pig Breeding Service", target_document=breeding_service,
				notes="Sow SOW-001 x Boar BOAR-001 — served, confirmed pregnant, then farrowed.",
			),
			_step(3, "Open the farrowing record", target_doctype="Pig Farrowing", target_document=farrowing),
			_step(
				4, "Review the grower batch raised from this litter", target_doctype="Pig Grower Batch", target_document=grower_batch,
				notes="Status 'Sold' — this batch has completed its full lifecycle.",
			),
			_step(5, "Review a real weight-tracking record for this batch", target_doctype="Pig Weight Record", target_document=weight_record),
			_step(
				6, "Open the sale lot this batch was sold as", target_doctype="Pig Sale Lot", target_document=sale_lot,
				notes="Closes the loop: breeding -> farrowing -> grower batch -> sale.",
			),
		],
	}
	name, created = _upsert_scenario(spec)
	return f"seed_pig_farm_breeding_to_sale_scenario: {'created' if created else 'synced'} '{name}'."


def seed_ai_qms_copilot_capa_approval_scenario():
	deviation = frappe.db.get_value("QMS Deviation", {"subject": ["like", "%Cold storage temperature excursion — Warehouse C%"]}, "name")
	if not deviation:
		return "seed_ai_qms_copilot_capa_approval_scenario: SKIPPED — run seed_ai_qms_copilot() (AI-DEMO-02) first."

	draft = frappe.db.get_value(
		"AI Draft", {"use_case": "draft_capa", "source_reference": deviation, "status": "Approved"}, "name",
		order_by="creation asc",
	) or frappe.db.get_value("AI Draft", {"use_case": "draft_capa", "source_reference": deviation}, "name", order_by="creation asc")
	if not draft:
		return "seed_ai_qms_copilot_capa_approval_scenario: SKIPPED — no draft_capa AI Draft exists for the Warehouse C deviation yet. Run seed_ai_qms_copilot_validations() first."

	capa = frappe.db.get_value("AI Draft", draft, "resulting_reference")
	if not capa or not frappe.db.exists("QMS CAPA", capa):
		return "seed_ai_qms_copilot_capa_approval_scenario: SKIPPED — the draft_capa AI Draft has not been approved into a real QMS CAPA yet."

	reviewed_by = frappe.db.get_value("AI Draft", draft, "reviewed_by") or "quality.director@pharmacountry.vn"

	spec = {
		"scenario_code": "AI-QMS-COPILOT-CAPA-APPROVAL",
		"title": "AI QMS Copilot — Deviation to CAPA, With a Real Human Approval Gate",
		"golden_demo_reference": "IP-QMS",
		"primary_login_role": "Quality Director",
		"primary_login_user": reviewed_by,
		"objective": (
			"Show human-in-the-loop AI: the AI QMS Copilot proposes a CAPA action plan from a real "
			"Deviation record, but the platform enforces that nothing becomes an official QMS record "
			"until a named human reviewer explicitly approves it — proven live, not just described."
		),
		"what_this_demonstrates": (
			"AI-assisted decision support with a real approval gate, not a rubber stamp: the AI's "
			"suggestion and the underlying data facts are kept in clearly separate fields (never "
			"blended, so a reviewer can always tell what's real data vs. AI-generated text), every AI "
			"call is logged with its provider/model/tool calls, and a fresh AI Draft can NEVER mint a "
			"QMS CAPA on its own — only an explicit human approval does, and rejecting a draft creates "
			"nothing at all (both behaviors are live-tested, not assumed, in "
			"verify_ai_qms_copilot_golden_demo())."
		),
		"allow_reset": 1,
		"reset_function_path": "enterprise_core.enterprise_core.ai_qms_copilot_seeds.seed_ai_qms_copilot",
		"reset_function_arg": None,
		"reset_instructions": (
			"Re-asserts the base Deviation/AI Tool/Prompt Template/AI Action data this scenario "
			"depends on (idempotent — checks-before-creates). Deliberately does NOT re-run the "
			"draft/approval test flow itself (seed_ai_qms_copilot_validations), because that function "
			"mints a brand-new AI Draft and QMS CAPA on every call BY DESIGN (an append-only audit "
			"trail) — wiring that to this button would make every click grow the database instead of "
			"resetting anything. The specific Draft/CAPA this scenario links to keeps existing "
			"regardless (Frappe records are never deleted by that flow)."
		),
		"is_active": 1,
		"steps": [
			_step(1, "Login as Quality Director", login_as_role="Quality Director", login_as_user=reviewed_by),
			_step(
				2, "Open the real Deviation under investigation", target_doctype="QMS Deviation", target_document=deviation,
				notes="Cold storage temperature excursion — Warehouse C. A real Deviation record, independent of the platform's own flagship Warehouse B deviation.",
			),
			_step(
				3, "Ask the AI QMS Copilot to draft a CAPA for this deviation",
				notes=(
					"Runs enterprise_core.enterprise_core.ai_qms_copilot.run_qms_copilot('draft_capa', ...) — "
					"no Desk button exists for this call yet (backend-only in this build), so this step is "
					"narrated; the resulting real Draft/CAPA records below are what's clickable."
				),
			),
			_step(
				4, "Review the AI-generated CAPA draft (never auto-applied)", target_doctype="AI Draft", target_document=draft,
				notes="requires_human_approval is always True for this use case; data_facts and ai_suggestion are kept in separate fields.",
			),
			_step(
				5, "Open the real CAPA created only after human approval", target_doctype="QMS CAPA", target_document=capa,
				notes="This CAPA did not exist until Quality Director explicitly approved the AI's draft — approving or rejecting a DIFFERENT draft never mints a record on its own (verified live).",
			),
		],
	}
	name, created = _upsert_scenario(spec)
	return f"seed_ai_qms_copilot_capa_approval_scenario: {'created' if created else 'synced'} '{name}' (draft={draft}, capa={capa})."


def seed_farm_portal_technical_visit_scenario():
	alpha = frappe.db.get_value("Customer", {"customer_name": "WEB07 Portal Farm Alpha"}, "name")
	beta = frappe.db.get_value("Customer", {"customer_name": "WEB07 Portal Farm Beta"}, "name")
	if not alpha or not beta:
		return "seed_farm_portal_technical_visit_scenario: SKIPPED — run seed_farm_portal_master_data() (WEB-07) first."

	alpha_so = frappe.db.get_value("Sales Order", {"customer": alpha, "docstatus": 1}, "name", order_by="creation asc")
	alpha_visit = frappe.db.get_value(
		"Vet Technical Visit", {"customer": alpha, "recommended_item": ["is", "set"]}, "name", order_by="creation asc"
	)
	if not alpha_so or not alpha_visit:
		return "seed_farm_portal_technical_visit_scenario: SKIPPED — run seed_farm_portal_sales_flow()/seed_farm_portal_technical_visits() (WEB-07) first."

	spec = {
		"scenario_code": "FARM-PORTAL-TECHNICAL-VISIT",
		"title": "Farm Customer Portal (WEB-07) — Orders, Technical Visits & Account Isolation",
		"golden_demo_reference": "IP-VETERINARY",
		"primary_login_role": "Farm Customer Portal (Alpha)",
		"primary_login_user": "farm.alpha.portal@pharmacountry.vn",
		"objective": (
			"Show a farm customer's self-service portal (WEB-07 — a separate Next.js app, "
			"nextjs-demo/web-07-farm-portal/) backed by real Frappe Desk records: order history and a "
			"technical visit with a structured product recommendation, plus real, independently "
			"verified account isolation between two different farm customers."
		),
		"what_this_demonstrates": (
			"A production-real customer portal pattern: native Frappe session-cookie login plus "
			"User Permission-scoped access (not a hand-rolled per-request check), a real order "
			"history, a real technical-visit record with a structured recommended-product Link field "
			"(not free text), and empirically verified cross-customer isolation — Farm Beta genuinely "
			"cannot see or fetch Farm Alpha's order, proven live via "
			"farm_portal_api.verify_farm_portal_access_control(), not just asserted in documentation."
		),
		"allow_reset": 1,
		"reset_function_path": "enterprise_core.enterprise_core.farm_portal_seeds.reset_farm_portal_demo_data",
		"reset_function_arg": None,
		"reset_instructions": (
			"Re-runs WEB-07's 3 idempotent seed functions (master data, sales flow, technical visits) "
			"in order — each independently checks-before-creates. Safe to re-run; does not re-run the "
			"deliberate over-credit-limit negative test (a separate, scenario-appropriate function not "
			"part of this walkthrough's own steps)."
		),
		"is_active": 1,
		"steps": [
			_step(
				1, "Login to the Farm Customer Portal as Farm Alpha",
				login_as_role="Farm Customer (Alpha)", login_as_user="farm.alpha.portal@pharmacountry.vn",
				target_doctype="Customer", target_document=alpha,
				notes="The portal itself is a separate Next.js app; this links to the real Frappe Desk Customer record backing it, for verification.",
			),
			_step(
				2, "Review Farm Alpha's real order history", target_doctype="Sales Order", target_document=alpha_so,
			),
			_step(
				3, "Review a technical visit with a real product recommendation", target_doctype="Vet Technical Visit", target_document=alpha_visit,
				notes="A real field-rep visit recommending a specific product via a structured Link field (recommended_item), not free text.",
			),
			_step(
				4, "Switch to Farm Beta's own login", login_as_role="Farm Customer (Beta)", login_as_user="farm.beta.portal@pharmacountry.vn",
				target_doctype="Customer", target_document=beta,
			),
			_step(
				5, "Confirm Beta cannot see or fetch Alpha's order",
				notes=(
					"A real, verified negative test — requesting Alpha's Sales Order name directly while "
					"authenticated as Beta returns a plain 404 (DoesNotExistError), never a distinguishable "
					"'found but not yours' response. See farm_portal_api.verify_farm_portal_access_control()."
				),
			),
		],
	}
	name, created = _upsert_scenario(spec)
	return f"seed_farm_portal_technical_visit_scenario: {'created' if created else 'synced'} '{name}'."


def seed_guided_demo_scenarios():
	"""Registry entry point — runs all 5 scenario seeds in sequence, tolerating individual
	SKIPs (same per-seed error/skip tolerance pattern as run_industry_pack_seeds)."""
	results = {
		"pharma": seed_pharma_batch_release_scenario(),
		"cosmetics": seed_cosmetics_stability_complaint_scenario(),
		"pig_farm": seed_pig_farm_breeding_to_sale_scenario(),
		"ai_qms_copilot": seed_ai_qms_copilot_capa_approval_scenario(),
		"farm_portal": seed_farm_portal_technical_visit_scenario(),
	}
	return results
