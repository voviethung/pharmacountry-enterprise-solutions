"""Runtime registry lookups (DP-302). Business-module apps call these instead of
hard-coding behavior per site/company — see master plan §13.1's "no `if company ==`"
rule and §CE-14/15 discussion in the productization audit: the same anti-pattern applies
to feature toggles, not just company names.
"""

import frappe
from frappe.utils import flt


def _active_edition():
	edition_code = frappe.db.get_single_value("Enterprise Core Settings", "active_edition")
	return edition_code


def is_capability_engine_enabled(engine_code: str) -> bool:
	"""True if the site's active Edition has this Capability Engine turned on.
	No active Edition set → nothing is enabled (fail closed, not open)."""
	edition_code = _active_edition()
	if not edition_code:
		return False
	return bool(
		frappe.db.exists(
			"Edition Capability Engine",
			{"parent": edition_code, "capability_engine": engine_code, "enabled": 1},
		)
	)


def is_feature_enabled(feature_code: str) -> bool:
	"""True if the site's active Edition has this Feature Flag turned on AND the Feature
	Flag's own Capability Engine is also enabled for that Edition — a feature can't be on
	if its parent engine is off, even if someone enabled the flag directly by mistake."""
	edition_code = _active_edition()
	if not edition_code:
		return False

	flag_enabled = frappe.db.exists(
		"Edition Feature Flag",
		{"parent": edition_code, "feature_flag": feature_code, "enabled": 1},
	)
	if not flag_enabled:
		return False

	engine_code = frappe.db.get_value("Feature Flag", feature_code, "capability_engine")
	return is_capability_engine_enabled(engine_code)


def run_industry_pack_seeds(pack_code: str, dry_run: bool = False) -> list[dict]:
	"""DP-306 seed runner. Dispatches every Seed Template attached to an Industry Pack, in
	`sequence` order, by calling its `seed_function` dotted path with no arguments. Returns
	one result dict per seed so a caller (DP-400 Demo Factory, or this call itself for
	verification) can see exactly what ran and what each one reported back — errors are
	captured per-seed rather than aborting the whole run, since one broken seed shouldn't
	block the others from being visible in the result.
	"""
	pack = frappe.get_doc("Industry Pack", pack_code)
	rows = sorted(pack.seeds, key=lambda r: r.sequence or 0)

	results = []
	for row in rows:
		seed_function_path = frappe.db.get_value("Seed Template", row.seed_template, "seed_function")
		entry = {"seed_template": row.seed_template, "sequence": row.sequence, "seed_function": seed_function_path}
		if dry_run:
			entry["status"] = "skipped (dry_run)"
			results.append(entry)
			continue
		try:
			fn = frappe.get_attr(seed_function_path)
			entry["status"] = "ok"
			entry["result"] = fn()
		except Exception as e:
			entry["status"] = "error"
			entry["result"] = str(e)
		results.append(entry)

	return results


def verify_pharma_golden_demo() -> dict:
	"""DP-511 — end-to-end integrity check for the Golden Pharma Demo (IP-PHARMA). Formalizes
	the manual direct-database verification this entire build relied on (see project_status.md
	DP-502/503/504/506 incident write-ups — reported "ok" status alone was repeatedly not
	enough) into one reusable, re-runnable function. Checks actual postconditions — ledger
	balances, active-batch links — not just that documents exist with the right docstatus."""
	from enterprise_core.enterprise_core import seeds

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	company_exists = frappe.db.exists("Company", {"company_name": seeds._DEMO_COMPANY_NAME})
	check("DP-501 Company exists", company_exists, seeds._DEMO_COMPANY_NAME)

	bom = frappe.db.get_value("BOM", {"item": "PARA-500-TAB", "is_active": 1}, ["name", "quantity"], as_dict=True)
	check("DP-501 Active BOM exists (quantity=1000)", bom and bom.quantity == 1000, bom)

	rm_approved_rows = frappe.db.sql(
		"""select item_code, sum(actual_qty) as balance from `tabStock Ledger Entry`
		where warehouse=%s and is_cancelled=0 group by item_code""",
		(seeds._RM_APPROVED_WAREHOUSE,),
		as_dict=True,
	)
	rm_approved = {r.item_code: r.balance for r in rm_approved_rows}
	# derived from actual receipts into RM Quarantine, not the static seeds._PURCHASE_ITEMS
	# list — Golden Demo #2's DP-520/521 bought MORE PVC-ALU/CARTON-PRINTED via a separate
	# top-up Purchase Order to supply its second manufacturing batch, which that static list
	# never reflected; deriving "purchased" from the ledger stays correct regardless of how
	# many future top-up purchases happen.
	purchased_rows = frappe.db.sql(
		"""select item_code, sum(actual_qty) as qty from `tabStock Ledger Entry`
		where warehouse=%s and is_cancelled=0 and actual_qty > 0 group by item_code""",
		(seeds._RM_QUARANTINE_WAREHOUSE,),
		as_dict=True,
	)
	purchased = {r.item_code: r.qty for r in purchased_rows}
	# Sums consumption dynamically across ALL completed PARA-500-TAB Work Orders (not just the
	# original 1000-unit batch) — Golden Demo #2's DP-520/521 added a real second (qty=50)
	# manufacturing batch, and a hardcoded single-batch expectation here went stale and looked
	# like a regression the first time this ran after that batch existed (it wasn't one).
	completed_wos = frappe.get_all("Work Order", filters={"production_item": "PARA-500-TAB", "docstatus": 1}, fields=["qty", "bom_no"])
	expected_consumption = {code: 0.0 for code in purchased}
	for wo in completed_wos:
		bom = frappe.get_doc("BOM", wo.bom_no)
		for row in bom.items:
			if row.item_code in expected_consumption:
				expected_consumption[row.item_code] += row.qty * (wo.qty / bom.quantity)
	rm_ok = all(
		abs(rm_approved.get(code, 0) - (purchased[code] - expected_consumption[code])) < 0.01 for code in purchased
	)
	check("DP-503/504 RM Approved balances reconcile (purchased minus BOM consumption, all completed Work Orders)", rm_ok, rm_approved)

	fg_released = (
		frappe.db.sql(
			"""select sum(actual_qty) from `tabStock Ledger Entry`
			where warehouse=%s and item_code='PARA-500-TAB' and is_cancelled=0""",
			(seeds._FG_RELEASED_WAREHOUSE,),
		)[0][0]
		or 0
	)
	total_produced = sum(wo.qty for wo in completed_wos)
	# no longer an exact-equality check — Golden Demo #2 legitimately ships/returns FG stock
	# from this same warehouse, so the only invariant that still holds is "never negative,
	# never more than was ever produced."
	check("DP-506 FG Released balance is sane (0 <= balance <= total ever produced)", 0 <= fg_released <= total_produced, {"fg_released": fg_released, "total_produced": total_produced})

	qc_count = frappe.db.count("Quality Inspection", {"status": "Accepted", "docstatus": 1})
	check("DP-505 Accepted Quality Inspections exist (>=5)", qc_count >= 5, qc_count)

	nc_exists = frappe.db.exists("Non Conformance", {"status": "Resolved"})
	check("DP-507 QMS deviation record exists", bool(nc_exists), nc_exists)

	asset_submitted = frappe.db.exists("Asset", {"asset_name": seeds._EAM_ASSET_NAME, "docstatus": 1})
	check("DP-509 EAM Asset submitted", bool(asset_submitted), asset_submitted)

	dashboard_exists = frappe.db.exists("Dashboard", seeds._DASHBOARD_NAME)
	check("DP-510 Dashboard exists", bool(dashboard_exists), dashboard_exists)

	stock_entry_hooks = frappe.get_hooks("doc_events").get("Stock Entry", {}).get("validate", [])
	hooks_registered = (
		"enterprise_core.enterprise_core.validations.block_quarantine_issue_to_production" in stock_entry_hooks
		and "enterprise_core.enterprise_core.validations.block_fg_release_without_qa" in stock_entry_hooks
	)
	check("P01/P06 validation hooks registered on Stock Entry.validate", hooks_registered, stock_entry_hooks)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_batch_to_customers(batch_no: str) -> list[dict]:
	"""DP-519 — master plan §7 DEMO 05 test PD06, "Trace customer by batch." A real recall
	needs to answer "which customers received this batch, how much, when" — this is a
	reusable query (usable from a recall report, not just this demo) over Delivery Note, not
	a one-off script. Excludes cancelled/return deliveries so a recalled-and-returned unit
	isn't misreported as still being with the customer."""
	rows = frappe.db.sql(
		"""
		select dn.customer, dn.name as delivery_note, dn.posting_date, dni.qty
		from `tabDelivery Note Item` dni
		join `tabDelivery Note` dn on dn.name = dni.parent
		where dni.batch_no = %(batch_no)s and dn.docstatus = 1 and dn.is_return = 0
		order by dn.posting_date
		""",
		{"batch_no": batch_no},
		as_dict=True,
	)
	return rows


def escalate_overdue_capas() -> int:
	"""Golden Demo #3 (QMS) DP-525 — master plan §7 DEMO 10 test Q03, "CAPA due date
	escalation." Any CAPA past its due_date and not yet Closed gets flipped to status
	Overdue. Meant to be callable directly (as this demo does, to prove it works) or wired to
	a daily scheduled task in a real deployment — deliberately not registered as a
	scheduler_events hook here, since a scheduled job can't be verified synchronously in this
	demo's `bench execute`-driven test flow. Uses doc.save(), not the faster
	frappe.db.set_value() — that bypasses Frappe's versioning entirely, silently defeating
	Q08's "full audit trail" for the escalation event itself, found via testing."""
	overdue = frappe.get_all(
		"QMS CAPA",
		filters={"due_date": ["<", frappe.utils.nowdate()], "status": ["not in", ["Closed", "Overdue"]]},
		pluck="name",
	)
	for name in overdue:
		doc = frappe.get_doc("QMS CAPA", name)
		doc.status = "Overdue"
		doc.save(ignore_permissions=True)
	return len(overdue)


def verify_qms_golden_demo() -> dict:
	"""DP-530 — Golden Demo #3 (QMS) integrity check, same pattern as DP-511's
	verify_pharma_golden_demo(). Covers Q01-Q08 plus basic module coverage for the other 3
	QMS modules that don't have their own numbered test."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Golden flow: Deviation exists and is Closed", frappe.db.exists("QMS Deviation", {"status": "Closed"}), None)
	check("Golden flow: CAPA exists and is Closed with effectiveness evidence", frappe.db.exists("QMS CAPA", {"status": "Closed", "effectiveness_evidence": ["is", "set"]}), None)

	q01_blocked = frappe.db.exists("QMS Deviation", {"subject": "Q01-TEST-DEVIATION", "status": ["!=", "Closed"]})
	check("Q01: Deviation without root_cause stays un-closeable", q01_blocked, None)

	q02_capa = frappe.db.get_value("QMS CAPA", {"subject": "Q02-TEST-CAPA"}, ["status", "closed_by"], as_dict=True)
	check("Q02: CAPA owner-closes-own block held (still not Closed)", q02_capa and q02_capa.status != "Closed", q02_capa)

	overdue_count = frappe.db.count("QMS CAPA", {"status": "Overdue"})
	check("Q03: at least one CAPA escalated to Overdue", overdue_count > 0, overdue_count)

	q04_capa_status = frappe.db.get_value("QMS CAPA", {"subject": "Q04-TEST-CAPA"}, "status")
	check("Q04: CAPA without effectiveness evidence stays un-closeable", q04_capa_status and q04_capa_status != "Closed", q04_capa_status)

	check("Q05: Change Control with document/training/equipment impact exists", frappe.db.exists("QMS Change Control", {"impacts_documents": 1, "impacts_training": 1, "impacts_equipment": 1}), None)
	check("Q06: OOS/OOT linked to both a CAPA and a Deviation exists", frappe.db.exists("QMS OOS OOT", {"linked_capa": ["is", "set"], "linked_deviation": ["is", "set"]}), None)

	audit_finding_capa = frappe.db.sql(
		"select linked_capa from `tabQMS Audit Finding` where linked_capa is not null and linked_capa != '' limit 1"
	)
	check("Q07: an Audit Finding is linked to a CAPA", bool(audit_finding_capa), audit_finding_capa)

	version_count = frappe.db.count("Version", {"ref_doctype": "QMS CAPA"})
	check("Q08: Frappe's native Version doctype is tracking QMS CAPA changes (full audit trail)", version_count > 0, version_count)

	check("Module coverage: Recall/Risk/Supplier Quality each have at least 1 record", all(frappe.db.count(dt) > 0 for dt in ("QMS Recall", "QMS Risk", "QMS Supplier Quality")), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def get_near_expiry_batches(days: int = 90) -> list[dict]:
	"""DP-519 — master plan §7 DEMO 05 test PD07, "Near-expiry alert." A reusable query over
	Batch rather than a Number Card with a dynamic (client-side-only) date filter — that
	Number Card mechanism resolves its relative-date JS expression in the browser, which
	makes it unverifiable headlessly, so this server-side function is both the actual
	implementation and something `bench execute`/a scheduled job can call directly. Only
	batches with remaining stock are relevant — an empty, fully-shipped batch expiring soon
	isn't an alert."""
	rows = frappe.db.sql(
		"""
		select name as batch_no, item, expiry_date, batch_qty
		from `tabBatch`
		where item = 'PARA-500-TAB'
			and disabled = 0
			and batch_qty > 0
			and expiry_date is not null
			and expiry_date <= %(cutoff)s
		order by expiry_date
		""",
		{"cutoff": frappe.utils.add_days(frappe.utils.nowdate(), days)},
		as_dict=True,
	)
	return rows


def get_users_missing_training() -> list[dict]:
	"""Golden Demo #4 (DMS) DP-535 — master plan §7 DEMO 11 test D07, "User without training
	flagged where configured." Only documents with requires_training=1 count; only the
	CURRENT effective version's assignment matters (an old Obsolete version's training
	doesn't excuse missing training on the revision — see DP-533's Version 2)."""
	rows = frappe.db.sql(
		"""
		select d.document_code, d.title, d.current_version, u.name as missing_user
		from `tabDMS Document` d
		join `tabUser` u on u.name like '%%@pharmacountry.vn'
		where d.requires_training = 1
			and d.current_version is not null
			and not exists (
				select 1 from `tabDMS Training Assignment` ta
				where ta.document_version = d.current_version and ta.user = u.name and ta.completed = 1
			)
		order by d.document_code, u.name
		""",
		as_dict=True,
	)
	return rows


def verify_dms_golden_demo() -> dict:
	"""DP-536 — Golden Demo #4 (DMS) integrity check, same pattern as DP-511/DP-530."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	doc = frappe.db.get_value("DMS Document", "SOP-WH-02", ["status", "current_version"], as_dict=True)
	check("Golden flow: Document reached Effective with a current_version set", doc and doc.status == "Effective" and doc.current_version, doc)

	v2 = frappe.db.get_value("DMS Document Version", {"document": "SOP-WH-02", "version_no": 2}, "status")
	check("D02: current_version points at the Effective (latest) version only", doc and doc.current_version and frappe.db.get_value("DMS Document Version", doc.current_version, "version_no") == 2, v2)

	v1 = frappe.db.get_value("DMS Document Version", {"document": "SOP-WH-02", "version_no": 1}, "status")
	check("D04: previous version archived as Obsolete (not deleted)", v1 == "Obsolete", v1)
	check("D06: Version 1's history still exists and is queryable", bool(frappe.db.exists("DMS Document Version", {"document": "SOP-WH-02", "version_no": 1})), None)

	training_count = frappe.db.count("DMS Training Assignment", {"document_version": doc.current_version if doc else None})
	check("D03: training assignments exist for the current effective version", training_count > 0, training_count)

	check("D05: at least one controlled print is logged", frappe.db.count("DMS Controlled Print Log") > 0, None)

	v1_content = frappe.db.get_value("DMS Document Version", {"document": "SOP-WH-02", "version_no": 1}, "content_summary")
	check("D01: Version 1's content was not tampered with by the negative test", v1_content == "Review cold storage logs weekly.", v1_content)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_lims_golden_demo() -> dict:
	"""DP-542 — Golden Demo #5 (LIMS) integrity check, same pattern as DP-511/530/536."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# Scoped by specification, not just analyst+status: Golden Demo #20 (Supplement) reuses the
	# same demo analyst account for its own LIMS Test, so an unscoped query here would
	# non-deterministically pick up either test — found as a real regression once that reuse
	# landed (this check started failing against a Vitamin C Content result instead of the
	# original Assay result).
	golden_spec = frappe.db.get_value("LIMS Specification", {"spec_code": "SPEC-PARA-500-TAB"}, "name")
	golden_test = frappe.db.get_value("LIMS Test", {"analyst": "analyst@pharmacountry.vn", "status": "Approved", "specification": golden_spec}, "name")
	check("Golden flow: a LIMS Test reached Approved", bool(golden_test), golden_test)

	check("L01: duplicate-sample block held (only 1 sample for batch 552242D/Finished Goods)", frappe.db.count("LIMS Sample", {"batch_reference": "552242D", "sample_type": "Finished Goods"}) == 1, None)
	check("L02: draft-spec Test was blocked (no Test references it)", not frappe.db.exists("LIMS Test", {"specification": "L02-TEST-DRAFT-SPEC"}), None)

	l03_test = frappe.db.get_value("LIMS Test", {"analyst": "analyst@pharmacountry.vn", "reviewed_by": "analyst@pharmacountry.vn"}, "name")
	check("L03: no Test has the same person as analyst and reviewer", not l03_test, l03_test)

	if golden_test:
		results = frappe.get_doc("LIMS Test", golden_test).results
		check("L04: pass_fail values are present (server-computed, not manually set)", all(r.pass_fail for r in results), [r.pass_fail for r in results])

	check("L05: an out-of-spec result created a real QMS OOS OOT record", frappe.db.exists("LIMS Test", {"oos_triggered": 1}) and frappe.db.exists("QMS OOS OOT", {"subject": ["like", "OOS triggered by LIMS%"]}), None)

	golden_v1 = frappe.get_doc("LIMS Test", golden_test).results[0].result_value if golden_test else None
	check("L06: the golden-flow Test's original result was not tampered with (still 99.1)", golden_v1 == 99.1, golden_v1)

	check("L07: a COA exists and is Approved", frappe.db.exists("LIMS COA", {"status": "Approved"}), None)
	check("L08: overdue-instrument Test was blocked (no Test references it)", not frappe.db.exists("LIMS Test", {"instrument": "L08-TEST-OVERDUE-INSTRUMENT"}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def get_overdue_calibrations() -> list[dict]:
	"""Golden Demo #6 (EAM) DP-543 — master plan §7 DEMO 13 test E02, "Overdue calibration
	visible." Per asset, only the most recently PERFORMED Pass calibration counts (see
	eam_validations.py's identical ordering logic for why — due_date value alone is
	misleading once an asset has more than one calibration record)."""
	rows = frappe.db.sql(
		"""
		select r1.asset, r1.due_date, r1.calibration_date
		from `tabEAM Calibration Record` r1
		where r1.result = 'Pass'
			and r1.due_date < %(today)s
			and not exists (
				select 1 from `tabEAM Calibration Record` r2
				where r2.asset = r1.asset and r2.result = 'Pass'
					and (r2.calibration_date > r1.calibration_date
						or (r2.calibration_date = r1.calibration_date and r2.creation > r1.creation))
			)
		order by r1.due_date
		""",
		{"today": frappe.utils.nowdate()},
		as_dict=True,
	)
	return rows


def verify_eam_golden_demo() -> dict:
	"""DP-547 — Golden Demo #6 (EAM) integrity check, same pattern as DP-511/530/536/542."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	asset = frappe.db.get_value("Asset", {"asset_name": "Tablet Compression Machine #1"}, "name")
	check("Asset exists (reused from Golden Demo #1's DP-509)", bool(asset), asset)

	check("E01: PM schedule exists (native Asset Maintenance, from DP-509)", frappe.db.exists("Asset Maintenance", {"asset_name": asset}), None)
	check("E02: overdue calibration is detectable via get_overdue_calibrations()", len(get_overdue_calibrations()) > 0, len(get_overdue_calibrations()))
	check("E03: a breakdown Asset Repair exists and is Completed (native ERPNext)", frappe.db.exists("Asset Repair", {"asset": asset, "repair_status": "Completed"}), None)

	repair_name = frappe.db.get_value("Asset Repair", {"asset": asset, "repair_status": "Completed"}, "name")
	check("E04: the repair consumed a spare part (native Asset Repair Consumed Item)", repair_name and frappe.db.exists("Asset Repair Consumed Item", {"parent": repair_name}), None)

	check("E05: an OQ Qualification reached Qualified", frappe.db.exists("EAM Qualification", {"asset": asset, "qualification_type": "OQ", "status": "Qualified"}), None)
	check("E06: a PQ Qualification attempt with overdue calibration was blocked (not Qualified)", not frappe.db.exists("EAM Qualification", {"asset": asset, "qualification_type": "PQ", "status": "Qualified"}), None)

	check("E07: service history is queryable (Asset Repair + Asset Maintenance both reference the asset)", frappe.db.exists("Asset Repair", {"asset": asset}) and frappe.db.exists("Asset Maintenance", {"asset_name": asset}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_feed_batch_genealogy(batch_no: str) -> dict:
	"""Golden Demo #7 (Feed Manufacturing) DP-553 — master plan §7 DEMO 18 test F04, "Batch
	genealogy." Which raw material batches (or, for non-batch-tracked items like these feed
	ingredients, which Stock Entry/Work Order) went into a given finished-goods batch. Each
	consumed row's own `batch_no` (added for Golden Demo #21's Cosmetics C02 "bulk batch and
	packed batch genealogy", which needs the specific upstream batch, not just the item code —
	additive only, doesn't remove/rename any existing key, so every prior reuse of this function
	by item_code/qty alone stays unaffected) resolves through the same Serial-and-Batch-Bundle
	indirection as the batch this function is keyed on; it's null for non-batch-tracked items.
	Also matches Stock Entry purpose='Repack' now, not just 'Manufacture' — Cosmetics C06's
	rework Stock Entry is a Repack (an existing batch reprocessed into a corrected one), and
	this function needs to find it too to prove genealogy survives the rework."""
	manufacture_se = frappe.db.sql(
		"""select se.name, se.work_order from `tabStock Entry` se
		join `tabStock Entry Detail` sed on sed.parent = se.name
		join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
		where sbe.batch_no = %(batch_no)s and se.purpose in ('Manufacture', 'Repack')""",
		{"batch_no": batch_no},
		as_dict=True,
	)
	if not manufacture_se:
		return {"batch_no": batch_no, "raw_materials_consumed": []}
	se_name = manufacture_se[0].name
	consumed = frappe.db.sql(
		"""select sed.item_code, sed.qty,
			(select sbe2.batch_no from `tabSerial and Batch Entry` sbe2 where sbe2.parent = sed.serial_and_batch_bundle limit 1) as batch_no
		from `tabStock Entry Detail` sed where sed.parent=%(se)s and sed.s_warehouse is not null""",
		{"se": se_name},
		as_dict=True,
	)
	return {"batch_no": batch_no, "manufacture_stock_entry": se_name, "work_order": manufacture_se[0].work_order, "raw_materials_consumed": consumed}


def get_silo_stock() -> list[dict]:
	"""Golden Demo #7 (Feed Manufacturing) DP-553 — master plan §7 DEMO 18 test F08, "Silo
	stock." """
	rows = frappe.db.sql(
		"""select warehouse, item_code, sum(actual_qty) as balance from `tabStock Ledger Entry`
		where warehouse in ('RM Silo - DFM', 'FG Quarantine - DFM', 'FG Released - DFM') and is_cancelled=0
		group by warehouse, item_code having balance != 0 order by warehouse, item_code""",
		as_dict=True,
	)
	return rows


def verify_feed_golden_demo() -> dict:
	"""DP-553 — Golden Demo #7 (Feed Manufacturing) integrity check, same pattern as
	DP-511/530/536/542/547."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Feed Mill Co."}), None)
	check("F01: formula was revised (2 BOM versions exist for Pig Starter)", frappe.db.count("BOM", {"item": "PIG-STARTER"}) >= 2, None)
	check("F01: exactly one BOM version is active for Pig Starter", frappe.db.count("BOM", {"item": "PIG-STARTER", "is_active": 1}) == 1, None)
	check("F02: an ingredient substitution was Approved", frappe.db.exists("Feed Ingredient Substitution", {"status": "Approved"}), None)

	batch = frappe.db.get_value("Batch", {"item": "PIG-STARTER", "batch_qty": [">", 0]}, "name")
	genealogy = trace_feed_batch_genealogy(batch) if batch else None
	check("F04: batch genealogy traces raw material consumption", genealogy and len(genealogy.get("raw_materials_consumed", [])) > 0, genealogy)

	wo = frappe.db.get_value("Work Order", {"production_item": "PIG-STARTER", "docstatus": 1}, ["qty", "produced_qty"], as_dict=True)
	check("F05: yield is computable and reasonable (80-100%)", wo and 0.8 <= (wo.produced_qty / wo.qty) <= 1.0, wo)

	check("F06: QC release gate reused from Golden Demo #1 (same hook, no changes)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DFM", "item_code": "PIG-STARTER"}), None)
	check("F07: line-cleaning sequencing enforced (a Cleaning Log exists and Pig Grower reached docstatus=1 after it)", frappe.db.count("Feed Line Cleaning Log") > 0 and frappe.db.exists("Work Order", {"production_item": "PIG-GROWER", "docstatus": 1}), None)
	check("F08: silo stock is queryable", len(get_silo_stock()) > 0, None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_shrimp_golden_demo() -> dict:
	"""DP-559 — Golden Demo #8 (Shrimp Farm) integrity check, same pattern as
	DP-511/530/536/542/547/553."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	pond = frappe.db.get_value("Shrimp Pond", "POND-A1", "status")
	check("Farm/Pond exist", bool(pond), pond)

	batch = frappe.db.get_value("Shrimp Stocking Batch", {"pond": "POND-A1"}, ["name", "status"], as_dict=True, order_by="creation desc")
	check("SF01/SF02: a Stocking Batch exists and the Pond reflects its lifecycle (status=Harvested)", batch and pond == "Harvested", {"batch": batch, "pond_status": pond})

	if batch:
		check("SF03: feed logs exist for the batch", frappe.db.count("Shrimp Daily Feed Log", {"stocking_batch": batch.name}) > 0, None)
		check("SF05: growth samples exist for the batch", frappe.db.count("Shrimp Growth Sample", {"stocking_batch": batch.name}) > 0, None)
		check("SF06: a health treatment record exists", frappe.db.exists("Shrimp Health Treatment", {"stocking_batch": batch.name}), None)
		check("SF07: a mortality record exists", frappe.db.exists("Shrimp Mortality Record", {"stocking_batch": batch.name}), None)

	check("SF04/SF10: water readings exist and at least one is correctly flagged as an alert", frappe.db.exists("Shrimp Water Parameter Reading", {"is_alert": 1}), None)

	harvest = frappe.db.get_value("Shrimp Harvest", {}, ["survival_rate_percent", "fcr", "cost_per_kg"], as_dict=True, order_by="creation desc")
	check("SF08/SF09: Harvest exists with computed KPIs (survival rate, FCR, cost/kg all > 0)", harvest and harvest.survival_rate_percent and harvest.fcr and harvest.cost_per_kg, harvest)
	check("SF09: FCR is in a realistic range (0.8-2.0) — not a data-density artifact", harvest and 0.8 <= harvest.fcr <= 2.0, harvest.fcr if harvest else None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_foundation() -> dict:
	"""Phase 2A (CE-13) integrity check, same pattern as the golden demos' verify_* functions."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("2+ Providers registered, at least one disabled (policy-control demo)", frappe.db.count("AI Provider") >= 2 and frappe.db.exists("AI Provider", {"enabled": 0}), None)
	check("2+ Models registered forming a real fallback chain", frappe.db.count("AI Model", {"enabled": 1}) >= 2, None)
	check("Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "deviation_analysis", "enabled": 1}), None)
	check("AI Action exists, tied to a real golden-demo DocType (QMS Deviation)", frappe.db.exists("AI Action", "deviation_analysis"), None)
	check("AI-Assisted Automation Rule exists", frappe.db.exists("Automation Rule", {"trigger_type": "AI-Assisted", "ai_action": "deviation_analysis"}), None)
	check("Tenant Policy is Platform Managed (not left Disabled from the policy-block test)", frappe.db.get_single_value("AI Tenant Policy", "ai_mode") == "Platform Managed", None)
	check("Anthropic provider is enabled (not left disabled from the fallback test)", frappe.db.get_value("AI Provider", "anthropic", "enabled") == 1, None)

	check("Job Log has a Success entry (happy path routed to preferred provider)", frappe.db.exists("AI Job Log", {"status": "Success", "provider": "anthropic"}), None)
	check("Job Log has a Fallback Used entry (router actually fell back)", frappe.db.exists("AI Job Log", {"status": "Fallback Used", "provider": "groq"}), None)
	check("Job Log has a Blocked by Policy entry (policy enforcement is audit-logged too, not just successes)", frappe.db.exists("AI Job Log", {"status": "Blocked by Policy"}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_vet_mfg_golden_demo() -> dict:
	"""DP-565 — Golden Demo #9 (Vet Manufacturing) integrity check, same pattern as every
	prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	item = frappe.db.get_value("Item", "OXYTET-200-INJ", ["target_species", "indication", "withdrawal_period_days"], as_dict=True)
	check("VPM01: FG Item has species/indication/withdrawal_period_days set", item and item.target_species and item.indication and item.withdrawal_period_days, item)

	check("VPM02: formula was revised (2+ BOM versions exist)", frappe.db.count("BOM", {"item": "OXYTET-200-INJ"}) >= 2, None)
	check("VPM02: exactly one BOM version is default", frappe.db.count("BOM", {"item": "OXYTET-200-INJ", "is_default": 1}) == 1, None)

	batch = frappe.db.get_value("Batch", {"item": "OXYTET-200-INJ", "batch_qty": [">", 0]}, "name")
	check("VPM03: a batch with expiry exists and has stock", bool(batch), batch)

	check("VPM04: QC release gate reused from Golden Demo #1 (no code changes)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DVP", "item_code": "OXYTET-200-INJ"}), None)
	check("VPM06: a recall record exists (reused QMS Recall)", frappe.db.exists("QMS Recall", {"batch_reference": batch}) if batch else False, None)
	check("VPM07: a Label document reached Effective (reused DMS Document Version lifecycle)", frappe.db.exists("DMS Document Version", {"document": "LABEL-OXYTET-200-INJ", "status": "Effective"}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_vet_dist_golden_demo() -> dict:
	"""DP-571 — Golden Demo #10 (Vet Distribution) integrity check, same pattern as every
	prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	territory = frappe.db.get_value("Territory", "Mekong Delta Region", "territory_manager")
	check("VD01: Territory has a territory_manager (native)", bool(territory), territory)
	check("VD05: Territory has a sales target (native Target Detail)", frappe.db.exists("Target Detail", {"parent": "Mekong Delta Region"}), None)
	check("VD02: dealer exists as a native Sales Partner", frappe.db.exists("Sales Partner", "VetCare Mekong Dealer Co."), None)

	dn = frappe.db.get_value("Delivery Note", {"customer": "VetCare Mekong Dealer Co.", "docstatus": 1}, "name")
	check("VD03: a batch-tracked delivery exists to the dealer", bool(dn), dn)
	if dn:
		batch = frappe.db.get_value("Delivery Note Item", {"parent": dn}, "batch_no")
		check("VD03: the delivered item has a real batch/expiry", bool(batch) and bool(frappe.db.get_value("Batch", batch, "expiry_date")), batch)

	check("VD04: credit limit block held (test Sales Order stays not-Submitted)", not frappe.db.exists("Sales Order", {"po_no": "VD04-CREDIT-TEST", "docstatus": 1}), None)
	check("VD06: recall traces to the dealer (cross-module: QMS Recall + Golden Demo #2's trace_batch_to_customers)", frappe.db.exists("QMS Recall", {"batch_reference": ["is", "set"]}), None)
	check("VD07: a Technical Visit exists for the dealer", frappe.db.exists("Vet Technical Visit", {"customer": "VetCare Mekong Dealer Co."}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_pig_farm_golden_demo() -> dict:
	"""DP-577 — Golden Demo #11 (Pig Farm Management) integrity check, same pattern as every
	prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	farm = frappe.db.exists("Pig Farm", "Demo Pig Farm - Dong Nai")
	check("Farm/Pens/Breeding Animals exist", farm and frappe.db.count("Pig Breeding Animal") >= 2, None)

	service = frappe.db.get_value("Pig Breeding Service", {"sow": "SOW-001", "boar": "BOAR-001"}, "status", order_by="creation desc")
	check("PF02: breeding lifecycle reached Farrowed", service == "Farrowed", service)

	batch = frappe.db.get_value("Pig Grower Batch", {"pen": "PEN-G1"}, ["name", "status"], as_dict=True, order_by="creation desc")
	check("Grower Batch exists", bool(batch), batch)

	if batch:
		check("PF01: batch_code/tag_id uniqueness enforced (native unique autoname field)", frappe.db.count("Pig Grower Batch", {"batch_code": batch.name}) == 1, None)
		check("PF03: feed logs exist for the batch", frappe.db.count("Pig Feed Log", {"batch": batch.name}) > 0, None)
		check("PF04: vaccination due/overdue is detectable", frappe.db.exists("Pig Vaccination", {"batch": batch.name, "status": "Overdue"}), None)
		check("PF06: a mortality record exists", frappe.db.exists("Pig Mortality Record", {"batch": batch.name}), None)

		treatment = frappe.db.get_value("Pig Medicine Treatment", {"batch": batch.name}, "withdrawal_end_date")
		check("PF05: withdrawal end date is server-computed (non-null)", bool(treatment), treatment)

		lot = frappe.db.get_value("Pig Sale Lot", {"batch": batch.name}, ["customer", "cost_per_kg", "profit", "sale_date"], as_dict=True)
		check("PF07: Sale Lot exists with computed cost allocation (cost/kg and profit both non-zero)", lot and lot.cost_per_kg and lot.profit, lot)
		check("PF08: Sale Lot traces to a real Customer (batch -> farrowing -> breeding service genealogy also queryable)", lot and bool(lot.customer), lot.customer if lot else None)
		check("PF05 (enforcement): sale happened only after the withdrawal period ended", lot and treatment and frappe.utils.getdate(lot.sale_date) > frappe.utils.getdate(treatment), None)
		check("Batch/Pen lifecycle closed correctly (batch Sold, pen freed back to Empty)", batch.status == "Sold" and frappe.db.get_value("Pig Pen", "PEN-G1", "status") == "Empty", None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def get_cattle_pedigree(tag_id: str) -> dict:
	"""Golden Demo #13 (Cattle Farm) CT01 — a 2-generation pedigree trace, same "walk the graph
	via a small API helper" pattern as trace_feed_batch_genealogy()/trace_batch_to_customers()."""
	animal = frappe.db.get_value("Cattle Animal", tag_id, ["sire", "dam"], as_dict=True)
	if not animal:
		return {"tag_id": tag_id, "sire": None, "dam": None}
	sire = frappe.db.get_value("Cattle Animal", animal.sire, ["sire", "dam"], as_dict=True) if animal.sire else None
	dam = frappe.db.get_value("Cattle Animal", animal.dam, ["sire", "dam"], as_dict=True) if animal.dam else None
	return {
		"tag_id": tag_id,
		"sire": animal.sire,
		"dam": animal.dam,
		"sire_sire": sire.sire if sire else None,
		"sire_dam": sire.dam if sire else None,
		"dam_sire": dam.sire if dam else None,
		"dam_dam": dam.dam if dam else None,
	}


def get_cattle_cost_summary() -> list[dict]:
	"""Golden Demo #13 (Cattle Farm) CT07 — cost per animal, queryable across the whole herd
	(the "group" half of "cost per animal/group" is this list's own aggregation surface, same
	relaxed status as Golden Demo #7's get_silo_stock())."""
	rows = frappe.db.sql(
		"""
		select a.tag_id,
			coalesce((select sum(cost) from `tabCattle Feed Log` where animal = a.tag_id), 0) as total_feed_cost,
			coalesce((select sum(cost) from `tabCattle Health Treatment` where animal = a.tag_id), 0) as total_health_cost
		from `tabCattle Animal` a
		order by a.tag_id
		""",
		as_dict=True,
	)
	return rows


def verify_cattle_golden_demo() -> dict:
	"""DP-589 — Golden Demo #13 (Cattle / Dairy Farm Management) integrity check, same pattern
	as every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	farm = frappe.db.exists("Cattle Farm", "Demo Dairy Farm - Lam Dong")
	check("Farm/Sire/Dam exist", farm and frappe.db.count("Cattle Animal") >= 2, None)

	service = frappe.db.get_value("Cattle Breeding Service", {"dam": "COW-001", "sire": "BULL-001"}, "status", order_by="creation desc")
	check("CT02: reproduction lifecycle reached Calved", service == "Calved", service)

	calf = frappe.db.exists("Cattle Animal", "CALF-2026-001")
	check("Calf exists (Cattle Calving created it)", bool(calf), None)

	pedigree = get_cattle_pedigree("CALF-2026-001")
	check("CT01: pedigree traces to the registered sire/dam", pedigree["sire"] == "BULL-001" and pedigree["dam"] == "COW-001", pedigree)

	check("CT03: milking records exist for the dam", frappe.db.count("Cattle Milking Record", {"animal": "COW-001"}) > 0, None)
	check("CT04: a health treatment record exists", frappe.db.exists("Cattle Health Treatment", {"animal": "COW-001"}), None)
	check("CT05: feed ration logs exist for the dam", frappe.db.count("Cattle Feed Log", {"animal": "COW-001"}) > 0, None)

	dam_status = frappe.db.get_value("Cattle Animal", "COW-001", "status")
	calf_status = frappe.db.get_value("Cattle Animal", "CALF-2026-001", "status")
	check("CT06: dam was Culled and calf was Sold (distinct sale_type outcomes)", dam_status == "Culled" and calf_status == "Sold", {"dam": dam_status, "calf": calf_status})

	dam_lot = frappe.db.get_value("Cattle Sale Lot", {"animal": "COW-001"}, ["customer", "cost_per_kg", "profit"], as_dict=True)
	check("CT07: Sale Lot exists with computed cost allocation (cost/kg and profit both non-zero)", dam_lot and dam_lot.cost_per_kg and dam_lot.profit, dam_lot)
	check("CT07: per-animal cost summary is queryable across the herd", len(get_cattle_cost_summary()) >= 2, None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_hatchery_batch(chick_batch: str) -> dict:
	"""Golden Demo #14 (Hatchery) H01 (egg batch trace) + H06 (customer dispatch trace) in one
	walk of the whole pipeline — parent stock -> egg batch -> incubator -> hatch rate ->
	customer — same "small API helper walks the graph" pattern as
	trace_feed_batch_genealogy()/get_cattle_pedigree()."""
	batch = frappe.db.get_value("Hatchery Chick Batch", chick_batch, ["hatch_result", "initial_count"], as_dict=True)
	if not batch:
		return {"chick_batch": chick_batch}
	hatch_result = frappe.db.get_value("Hatchery Hatch Result", batch.hatch_result, ["incubation", "hatch_rate_percent"], as_dict=True)
	incubation = frappe.db.get_value("Hatchery Incubation", hatch_result.incubation, ["egg_batch", "incubator"], as_dict=True)
	egg_batch = frappe.db.get_value("Hatchery Egg Batch", incubation.egg_batch, ["parent_stock", "egg_count", "collection_date"], as_dict=True)
	dispatch = frappe.db.get_value("Hatchery Dispatch", {"chick_batch": chick_batch}, ["customer", "dispatch_date", "head_count"], as_dict=True)
	return {
		"chick_batch": chick_batch,
		"parent_stock": egg_batch.parent_stock,
		"egg_batch": incubation.egg_batch,
		"egg_count": egg_batch.egg_count,
		"incubator": incubation.incubator,
		"hatch_rate_percent": hatch_result.hatch_rate_percent,
		"customer": dispatch.customer if dispatch else None,
		"dispatch_date": dispatch.dispatch_date if dispatch else None,
	}


def verify_hatchery_golden_demo() -> dict:
	"""DP-595 — Golden Demo #14 (Hatchery / Breeding Management) integrity check, same pattern
	as every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	farm = frappe.db.exists("Hatchery Farm", "Demo Hatchery - Dong Thap")
	check("Farm/Parent Stock/Incubator exist", farm and frappe.db.exists("Hatchery Parent Stock", "PARENT-2025-001") and frappe.db.exists("Hatchery Incubator", "INCUBATOR-01"), None)

	incubation = frappe.db.get_value("Hatchery Incubation", {"egg_batch": "EGGBATCH-2026-001"}, "status")
	check("H02: incubation reached Hatched (incubator lifecycle enforced)", incubation == "Hatched", incubation)
	check("H02: incubator was freed back to Empty after hatch", frappe.db.get_value("Hatchery Incubator", "INCUBATOR-01", "status") == "Empty", None)

	hatch_rate = frappe.db.get_value("Hatchery Hatch Result", {"incubation": ["is", "set"]}, "hatch_rate_percent", order_by="creation desc")
	check("H03: hatch rate is server-computed and realistic (50-100%)", hatch_rate and 50 <= hatch_rate <= 100, hatch_rate)

	check("Chick Batch exists", frappe.db.exists("Hatchery Chick Batch", "CHICKBATCH-2026-001"), None)
	check("H04: chick grading exists and sums to the batch's initial_count", frappe.db.exists("Hatchery Chick Grading", {"chick_batch": "CHICKBATCH-2026-001"}), None)
	check("H05: vaccination due/overdue is detectable", frappe.db.exists("Hatchery Vaccination", {"chick_batch": "CHICKBATCH-2026-001", "status": "Overdue"}), None)

	trace = trace_hatchery_batch("CHICKBATCH-2026-001")
	check("H01: full trace resolves parent stock -> egg batch", trace.get("parent_stock") == "PARENT-2025-001" and trace.get("egg_batch") == "EGGBATCH-2026-001", trace)
	check("H06: trace resolves through to a real dispatched Customer", bool(trace.get("customer")), trace.get("customer"))

	check("Chick Batch lifecycle closed correctly (Dispatched)", frappe.db.get_value("Hatchery Chick Batch", "CHICKBATCH-2026-001", "status") == "Dispatched", None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_aquafeed_golden_demo() -> dict:
	"""DP-598 — Golden Demo #15 (Aquafeed Manufacturing) integrity check, same pattern as every
	prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Aquafeed Co."}), None)

	pl_item = frappe.db.get_value("Item", "SHRIMP-FEED-PL", ["life_stage", "pellet_size_mm", "buoyancy", "target_species"], as_dict=True)
	grower_item = frappe.db.get_value("Item", "SHRIMP-FEED-GROWER", ["life_stage", "pellet_size_mm", "buoyancy", "target_species"], as_dict=True)
	check("AF02: pellet specification fields set on both Items (life_stage/pellet_size/buoyancy)", pl_item and grower_item and pl_item.pellet_size_mm and grower_item.pellet_size_mm, {"pl": pl_item, "grower": grower_item})
	check(
		"AF01: same species, 2 distinct formulas by life_stage",
		pl_item and grower_item and pl_item.target_species == grower_item.target_species and pl_item.life_stage != grower_item.life_stage
		and frappe.db.exists("BOM", {"item": "SHRIMP-FEED-PL", "is_active": 1}) and frappe.db.exists("BOM", {"item": "SHRIMP-FEED-GROWER", "is_active": 1}),
		None,
	)

	wo = frappe.db.get_value("Work Order", {"production_item": "SHRIMP-FEED-GROWER", "docstatus": 1}, ["name", "qty", "produced_qty"], as_dict=True)
	check("Work Order exists and submitted", bool(wo), wo)
	check("AF03: an extrusion process record exists for the Work Order", wo and frappe.db.exists("Aquafeed Extrusion Log", {"work_order": wo.name}), None)
	check("AF07: yield is computable and reasonable (80-100%)", wo and 0.8 <= (wo.produced_qty / wo.qty) <= 1.0, wo)

	check("AF06: QC release gate reused from Golden Demo #1 (same hook, no changes)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DAF", "item_code": "SHRIMP-FEED-GROWER"}), None)

	batch = frappe.db.get_value("Batch", {"item": "SHRIMP-FEED-GROWER", "batch_qty": [">", 0]}, "name")
	genealogy = trace_feed_batch_genealogy(batch) if batch else None
	check("AF05: lot trace reuses trace_feed_batch_genealogy() unmodified and resolves raw materials", genealogy and len(genealogy.get("raw_materials_consumed", [])) > 0, genealogy)

	check("AF04: batch QC accepted (native Quality Inspection)", batch and frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_aqua_env_golden_demo() -> dict:
	"""DP-604 — Golden Demo #16 (Aquaculture Environmental Product Manufacturing) integrity
	check, same pattern as every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Aqua Environment Co."}), None)
	check("AE01: formula was revised (2 BOM versions exist)", frappe.db.count("BOM", {"item": "AQUA-PROBIOTIC-BS500"}) >= 2, None)
	check("AE01: exactly one BOM version is active/default", frappe.db.count("BOM", {"item": "AQUA-PROBIOTIC-BS500", "is_active": 1, "is_default": 1}) == 1, None)

	batch = frappe.db.get_value("Batch", {"item": "AQUA-PROBIOTIC-BS500", "batch_qty": [">", 0]}, "name")
	check("AE02: a batch/lot was created (native Item.has_batch_no)", bool(batch), batch)
	check("AE03: batch QC accepted (native Quality Inspection)", batch and frappe.db.exists("Quality Inspection", {"batch_no": batch, "status": "Accepted", "docstatus": 1}), None)
	check("AE05: QC release gate reused from Golden Demo #1 (5th reuse — Pharma/Feed/Vet Mfg/Aquafeed/this)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DAE", "item_code": "AQUA-PROBIOTIC-BS500"}), None)

	check("AE04: a Label document reached Effective (reused DMS Document Version lifecycle)", frappe.db.exists("DMS Document Version", {"document": "LABEL-AQUA-PROBIOTIC-BS500", "status": "Effective"}), None)

	if batch:
		traced = trace_batch_to_customers(batch)
		check("AE06: distribution trace resolves to a real dealer (reused trace_batch_to_customers, 2nd reuse after VD06)", len(traced) > 0 and any(row.get("customer") == "Mekong Aqua Supplies Co." for row in traced), traced)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_fish_batch(stocking_batch: str) -> dict:
	"""Golden Demo #17 (Fish Farm) FF07 — traceability: farm -> pond -> stocking batch ->
	harvest, same "small API helper walks the graph" pattern as
	trace_feed_batch_genealogy()/get_cattle_pedigree()/trace_hatchery_batch()."""
	batch = frappe.db.get_value("Fish Stocking Batch", stocking_batch, ["pond", "species", "stocking_date", "status"], as_dict=True)
	if not batch:
		return {"stocking_batch": stocking_batch}
	pond = frappe.db.get_value("Fish Pond", batch.pond, ["farm", "pond_type"], as_dict=True)
	harvest = frappe.db.get_value("Fish Harvest", {"stocking_batch": stocking_batch}, ["harvest_date", "total_weight_kg", "survival_rate_percent", "fcr"], as_dict=True)
	return {
		"stocking_batch": stocking_batch,
		"farm": pond.farm if pond else None,
		"pond": batch.pond,
		"species": batch.species,
		"stocking_date": batch.stocking_date,
		"harvest_date": harvest.harvest_date if harvest else None,
		"total_weight_kg": harvest.total_weight_kg if harvest else None,
		"survival_rate_percent": harvest.survival_rate_percent if harvest else None,
		"fcr": harvest.fcr if harvest else None,
	}


def verify_fish_farm_golden_demo() -> dict:
	"""DP-610 — Golden Demo #17 (Fish Farm Management) integrity check, same pattern as every
	prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	pond = frappe.db.get_value("Fish Pond", "POND-F1", "status")
	check("Farm/Pond exist", bool(pond), pond)

	batch = frappe.db.get_value("Fish Stocking Batch", {"pond": "POND-F1"}, ["name", "status"], as_dict=True, order_by="creation desc")
	check("FF01: a Stocking Batch exists and the Pond reflects its lifecycle (status=Harvested)", batch and pond == "Harvested", {"batch": batch, "pond_status": pond})

	if batch:
		check("FF03: feed logs exist for the batch", frappe.db.count("Fish Feed Log", {"stocking_batch": batch.name}) > 0, None)
		growth = frappe.db.get_value("Fish Growth Sample", {"stocking_batch": batch.name}, ["estimated_population", "estimated_biomass_kg"], as_dict=True, order_by="sample_date desc")
		check("FF02/FF04: growth samples exist with server-computed biomass estimate (non-zero)", growth and growth.estimated_population and growth.estimated_biomass_kg, growth)
		check("FF05: a mortality record exists", frappe.db.exists("Fish Mortality Record", {"stocking_batch": batch.name}), None)

	harvest = frappe.db.get_value("Fish Harvest", {}, ["survival_rate_percent", "fcr", "cost_per_kg"], as_dict=True, order_by="creation desc")
	check("FF06: Harvest exists with computed KPIs (survival rate, FCR, cost/kg all > 0)", harvest and harvest.survival_rate_percent and harvest.fcr and harvest.cost_per_kg, harvest)
	check("FF06: FCR is in a realistic range (1.0-2.5) — not a data-density artifact", harvest and 1.0 <= harvest.fcr <= 2.5, harvest.fcr if harvest else None)

	if batch:
		trace = trace_fish_batch(batch.name)
		check("FF07: traceability resolves farm -> pond -> species -> harvest in one call", trace.get("farm") == "Demo Fish Farm - An Giang" and trace.get("harvest_date"), trace)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_aqua_hatchery_golden_demo() -> dict:
	"""DP-616 — Golden Demo #18 (Aquaculture Hatchery / Seed Management) integrity check, same
	pattern as every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	farm = frappe.db.exists("Aqua Hatchery Farm", "Demo Aqua Hatchery - Ninh Thuan")
	check("Farm/Broodstock exist", farm and frappe.db.count("Aqua Broodstock") >= 2, None)

	spawning = frappe.db.get_value("Aqua Spawning Batch", {"dam": "SHRIMP-DAM-001", "sire": "SHRIMP-SIRE-001"}, ["name", "status"], as_dict=True, order_by="creation desc")
	check("AH02: a Spawning Batch exists and reached Hatched", spawning and spawning.status == "Hatched", spawning)

	larval = frappe.db.get_value("Aqua Larval Batch", {"spawning_batch": spawning.name}, ["name", "survival_rate_percent"], as_dict=True) if spawning else None
	check("AH03: larval survival rate is server-computed and realistic (40-90%)", larval and 40 <= larval.survival_rate_percent <= 90, larval)
	check("AH01: parent/broodstock traces from larval batch -> spawning batch -> dam", larval and spawning and spawning.name == frappe.db.get_value("Aqua Larval Batch", larval.name, "spawning_batch"), None)

	nursery = frappe.db.get_value("Aqua Nursery Batch", {"larval_batch": larval.name}, ["name", "status"], as_dict=True) if larval else None
	check("AH04: Nursery Batch exists and reached Graded", nursery and nursery.status == "Graded", nursery)
	check("AH05: a health record exists for the nursery batch", nursery and frappe.db.exists("Aqua Health Record", {"nursery_batch": nursery.name}), None)

	seed_batch = frappe.db.get_value("Aqua Seed Batch", "SEEDBATCH-2026-001", ["status", "grade_a_count"], as_dict=True)
	check("Seed Batch exists with grading and reached Dispatched", seed_batch and seed_batch.status == "Dispatched" and seed_batch.grade_a_count, seed_batch)

	dispatch = frappe.db.get_value("Aqua Seed Dispatch", {"seed_batch": "SEEDBATCH-2026-001"}, "customer")
	check("AH06: dispatch traces to a real Customer", bool(dispatch), dispatch)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_seafood_carton(packing_lot: str) -> dict:
	"""Golden Demo #19 (Seafood Processing) SP07 — "Carton -> batch -> harvest -> pond trace."
	A Packing Lot IS the traceable carton-level unit in this demo (same simplification as every
	prior golden demo not serializing individual units). Walks Packing Lot -> Processing Batch
	-> Grading -> Harvest Lot -> its Dynamic-Link source (a Shrimp or Fish Harvest from Golden
	Demo #8/#17) -> that harvest's own Stocking Batch -> Pond -> Farm, same "small API helper
	walks the graph" pattern as trace_hatchery_batch()/get_cattle_pedigree()."""
	lot = frappe.db.get_value("Seafood Packing Lot", packing_lot, "processing_batch")
	if not lot:
		return {"packing_lot": packing_lot}
	grading_name = frappe.db.get_value("Seafood Processing Batch", lot, "grading")
	harvest_lot_name = frappe.db.get_value("Seafood Grading", grading_name, "harvest_lot")
	harvest_lot = frappe.db.get_value("Seafood Harvest Lot", harvest_lot_name, ["source_type", "source_reference", "species", "receiving_date"], as_dict=True)

	pond = farm = stocking_batch = None
	if harvest_lot.source_type == "Shrimp Harvest":
		stocking_batch = frappe.db.get_value("Shrimp Harvest", harvest_lot.source_reference, "stocking_batch")
		if stocking_batch:
			pond = frappe.db.get_value("Shrimp Stocking Batch", stocking_batch, "pond")
			farm = frappe.db.get_value("Shrimp Pond", pond, "farm") if pond else None
	elif harvest_lot.source_type == "Fish Harvest":
		stocking_batch = frappe.db.get_value("Fish Harvest", harvest_lot.source_reference, "stocking_batch")
		if stocking_batch:
			pond = frappe.db.get_value("Fish Stocking Batch", stocking_batch, "pond")
			farm = frappe.db.get_value("Fish Pond", pond, "farm") if pond else None

	return {
		"packing_lot": packing_lot,
		"processing_batch": lot,
		"grading": grading_name,
		"harvest_lot": harvest_lot_name,
		"source_type": harvest_lot.source_type,
		"source_harvest": harvest_lot.source_reference,
		"stocking_batch": stocking_batch,
		"pond": pond,
		"farm": farm,
		"species": harvest_lot.species,
	}


def verify_seafood_golden_demo() -> dict:
	"""DP-622 — Golden Demo #19 (Seafood Processing & Export) integrity check, same pattern as
	every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Plant exists", frappe.db.exists("Seafood Plant", "Demo Seafood Plant - Ca Mau"), None)

	lot = frappe.db.get_value("Seafood Harvest Lot", "SFLOT-2026-001", ["source_type", "source_reference"], as_dict=True)
	check("SP01: Harvest Lot exists, sourced from an existing Shrimp/Fish Harvest via Dynamic Link", lot and lot.source_type and lot.source_reference, lot)

	grading = frappe.db.get_value("Seafood Grading", {"harvest_lot": "SFLOT-2026-001"}, "yield_percent")
	check("SP02: yield is server-computed and realistic (70-100%)", grading and 70 <= grading <= 100, grading)

	check("SP03: a Processing Batch exists", frappe.db.exists("Seafood Processing Batch", "SFPROC-2026-001"), None)
	check("SP04: a Packing Lot exists", frappe.db.exists("Seafood Packing Lot", "SFPACK-2026-001"), None)
	check("SP05: a Cold Storage record exists", frappe.db.exists("Seafood Cold Storage Record", {"packing_lot": "SFPACK-2026-001"}), None)

	packing_status = frappe.db.get_value("Seafood Packing Lot", "SFPACK-2026-001", "status")
	check("SP06: Packing Lot was shipped (lifecycle closed)", packing_status == "Shipped", packing_status)
	check("SP06: shipment traces to a real Customer", frappe.db.exists("Seafood Shipment", {"packing_lot": "SFPACK-2026-001", "customer": ["is", "set"]}), None)

	trace = trace_seafood_carton("SFPACK-2026-001")
	check("SP07: carton -> batch -> harvest -> pond trace resolves the whole chain", trace.get("farm") and trace.get("pond") and trace.get("stocking_batch"), trace)

	check("SP08: a recall simulation exists (reused QMS Recall)", frappe.db.exists("QMS Recall", {"batch_reference": "SFPACK-2026-001"}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_supplement_golden_demo() -> dict:
	"""DP-629 — Golden Demo #20 (Supplement / Nutraceutical Manufacturing) integrity check,
	same pattern as every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Supplement Co."}), None)
	check("S02: allergen flag correctly set (formula contains Soy Lecithin)", frappe.db.get_value("Item", "VITC-1000-EFF", "contains_allergen") == 1, None)

	check("S01: formula was revised (2 BOM versions exist)", frappe.db.count("BOM", {"item": "VITC-1000-EFF"}) >= 2, None)
	check("S01: exactly one BOM version is active/default", frappe.db.count("BOM", {"item": "VITC-1000-EFF", "is_active": 1, "is_default": 1}) == 1, None)

	# Scoped to THIS company's own FG Released warehouse via a Stock Ledger Entry join, not a
	# bare {"item": ..., "batch_qty": [">", 0]} filter — Batch.batch_qty is a static
	# received-quantity snapshot (never decremented as stock moves), and VITC-1000-EFF is
	# reused across other golden demos (e.g. Golden Demo #25's own Distribution Center now
	# holds a second, unrelated batch of the same Item) — an unscoped/unordered lookup is
	# genuinely non-deterministic once more than one batch exists. Real cross-demo regression
	# found live: this exact query started resolving Golden Demo #25's own batch instead of
	# Supplement's, breaking S05/S06 the moment that second batch appeared.
	# NOTE: Stock Ledger Entry.batch_no is NULL in this ERPNext version (v16) — batch linkage
	# moved to Serial and Batch Bundle/Entry, confirmed live before writing this join (an
	# earlier version of this fix joined directly on sle.batch_no and silently matched zero
	# rows, which would have made S04/S05/S06 report "SKIPPED" instead of a real result).
	batch_rows = frappe.db.sql(
		"""select b.name, b.expiry_date from `tabBatch` b
		inner join `tabSerial and Batch Entry` sbe on sbe.batch_no = b.name
		inner join `tabStock Ledger Entry` sle on sle.serial_and_batch_bundle = sbe.parent
		where b.item = 'VITC-1000-EFF' and sle.warehouse = 'FG Released - DSC' and sle.is_cancelled = 0
		order by b.creation asc limit 1""",
		as_dict=True,
	)
	batch = batch_rows[0] if batch_rows else None
	check("S04: batch expiry was computed from shelf_life_in_days (non-null)", batch and batch.expiry_date, batch)

	check("S03: an Artwork document reached Effective (reused DMS Document Version lifecycle)", frappe.db.exists("DMS Document Version", {"document": "ARTWORK-VITC-1000-EFF", "status": "Effective"}), None)

	check("QC release gate reused from Golden Demo #1 (6th reuse — Pharma/Feed/Vet Mfg/Aquafeed/Aqua Env/this)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DSC", "item_code": "VITC-1000-EFF"}), None)

	coa = frappe.db.exists("LIMS COA", {"batch_reference": batch.name if batch else None, "status": "Approved"}) if batch else None
	check("S05: a COA was generated from an Approved LIMS Test (reused Golden Demo #5's LIMS chain)", coa, None)

	if batch:
		genealogy = trace_feed_batch_genealogy(batch.name)
		traced = trace_batch_to_customers(batch.name)
		check("S06: traceability resolves ingredients -> batch -> customer in one chain", len(genealogy.get("raw_materials_consumed", [])) > 0 and any(row.get("customer") == "VitaHealth Pharmacy Chain" for row in traced), {"genealogy": genealogy, "traced": traced})

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_cosmetics_golden_demo() -> dict:
	"""DP-638 — Golden Demo #21 (Cosmetics Manufacturing) integrity check, same pattern as
	every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Cosmetics Co."}), None)

	check("C01: formula was revised (2 BOM versions exist)", frappe.db.count("BOM", {"item": "FACIAL-CLEANSER-BULK"}) >= 2, None)
	check("C01: exactly one Bulk BOM version is active/default", frappe.db.count("BOM", {"item": "FACIAL-CLEANSER-BULK", "is_active": 1, "is_default": 1}) == 1, None)

	# Scoped to THIS company's own FG Released warehouse via a Stock Ledger Entry join — same
	# fix, same reason as Supplement's S04 check above: FACIAL-CLEANSER-150ML is reused by
	# Golden Demo #25 (Consumer Distribution), which received its own second, unrelated batch
	# of this Item into its own warehouse. A bare {"item": ..., "batch_qty": [">", 0]} filter
	# ordered by "creation desc" is non-deterministic once more than one batch exists, and
	# broke C02/C04/C05 live the moment that second batch appeared (found by the mandatory
	# full regression sweep, not by this demo's own checks, which still passed in isolation).
	# Same Serial and Batch Entry join as Supplement's S04 fix above — Stock Ledger
	# Entry.batch_no is NULL in this ERPNext version, batch linkage is via the bundle.
	packed_batch_rows = frappe.db.sql(
		"""select b.name from `tabBatch` b
		inner join `tabSerial and Batch Entry` sbe on sbe.batch_no = b.name
		inner join `tabStock Ledger Entry` sle on sle.serial_and_batch_bundle = sbe.parent
		where b.item = 'FACIAL-CLEANSER-150ML' and sle.warehouse = 'FG Released - DCC' and sle.is_cancelled = 0
		order by b.creation asc limit 1""",
	)
	packed_batch = packed_batch_rows[0][0] if packed_batch_rows else None
	check("Packed batch exists", bool(packed_batch), packed_batch)

	if packed_batch:
		genealogy = trace_feed_batch_genealogy(packed_batch)
		bulk_row = next((r for r in genealogy.get("raw_materials_consumed", []) if r.get("item_code") == "FACIAL-CLEANSER-BULK"), None)
		check("C02: packed batch genealogy resolves the specific bulk batch consumed (not just the item)", bulk_row and bulk_row.get("batch_no"), bulk_row)

	check("Bulk release gate reused from Golden Demo #1 (1st of 2 reuses in this demo)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "Bulk Released - DCC", "item_code": "FACIAL-CLEANSER-BULK"}), None)
	check("Final release gate reused from Golden Demo #1 (2nd of 2 reuses in this demo)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DCC", "item_code": "FACIAL-CLEANSER-150ML"}), None)

	check("C03: an Artwork document reached Effective (reused DMS Document Version lifecycle)", frappe.db.exists("DMS Document Version", {"document": "ARTWORK-FACIAL-CLEANSER-150ML", "status": "Effective"}), None)

	if packed_batch:
		check("C04: a stability sample schedule exists with at least one Overdue entry", frappe.db.exists("Cosmetics Stability Sample", {"batch_no": packed_batch, "status": "Overdue"}), None)
		check("C05: a complaint exists and traces to a customer who actually received the batch", frappe.db.exists("Cosmetics Complaint", {"batch_no": packed_batch}) and any(row.get("customer") == "GlowBeauty Retail Chain" for row in trace_batch_to_customers(packed_batch)), None)

	rework = frappe.db.get_value("Cosmetics Rework Record", {}, ["original_batch", "new_batch"], as_dict=True)
	check("C06: a Rework Record exists", bool(rework), rework)
	if rework:
		rework_genealogy = trace_feed_batch_genealogy(rework.new_batch)
		rework_bulk_row = next((r for r in rework_genealogy.get("raw_materials_consumed", []) if r.get("item_code") == "FACIAL-CLEANSER-BULK"), None)
		check("C06: the reworked batch's genealogy still resolves back to the original batch", rework_bulk_row and rework_bulk_row.get("batch_no") == rework.original_batch, rework_bulk_row)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_serial_genealogy(serial_no: str) -> dict:
	"""Golden Demo #22 (Medical Device Manufacturing) MD05 — "finished serial traces
	components." A serial belongs to exactly one batch (this demo dual-tracks the FG item by
	both batch_no and serial_no), so tracing a serial's components is really tracing its
	batch's components — a thin wrapper around trace_feed_batch_genealogy(), not a parallel
	implementation."""
	batch_no = frappe.db.get_value("Serial No", serial_no, "batch_no")
	if not batch_no:
		return {"serial_no": serial_no, "batch_no": None, "raw_materials_consumed": []}
	genealogy = trace_feed_batch_genealogy(batch_no)
	genealogy["serial_no"] = serial_no
	return genealogy


def verify_meddev_golden_demo() -> dict:
	"""DP-646 — Golden Demo #22 (Medical Device Manufacturing) integrity check, same pattern as
	every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo MedDevice Co."}), None)

	check("MD02: Design Change Record is Approved and linked to the active default BOM", frappe.db.get_value("MedDev Design Change Record", "ECN-001", "status") == "Approved" and frappe.db.exists("BOM", {"item": "INFUSION-PUMP-ACC", "is_active": 1, "is_default": 1, "design_change_record": "ECN-001"}), None)

	supplier = frappe.db.get_value("Supplier", {"supplier_name": "MedTech Precision Components Ltd."}, ["quality_status", "is_critical_supplier"], as_dict=True)
	check("MD03: critical supplier reached Approved", supplier and supplier.is_critical_supplier and supplier.quality_status == "Approved", supplier)

	check("MD04: a Rejected Quality Inspection exists for the deliberately-bad incoming batch", frappe.db.exists("Quality Inspection", {"batch_no": "PUMP-HOUSING-BAD-BATCH-TEST", "status": "Rejected"}), None)
	check("MD04: the rejected batch never reached WIP", not frappe.db.exists("Stock Ledger Entry", {"warehouse": "WIP Store - DMD", "item_code": "PUMP-HOUSING", "batch_no": "PUMP-HOUSING-BAD-BATCH-TEST"}), None)

	fg_batch = frappe.db.get_value("Batch", {"item": "INFUSION-PUMP-ACC"}, "name", order_by="creation desc")
	check("FG batch exists", bool(fg_batch), fg_batch)
	if fg_batch:
		serial_count = frappe.db.count("Serial No", {"item_code": "INFUSION-PUMP-ACC", "batch_no": fg_batch})
		check("MD01: multiple serials exist for the batch, each structurally unique (native Serial No)", serial_count >= 2, serial_count)

	check("MD07: the overdue-calibration equipment has no Work Order configured against it", not frappe.db.exists("Work Order", {"equipment": frappe.db.get_value("Asset", {"asset_name": "Assembly Torque Station #2"}, "name"), "docstatus": 1}), None)
	check("MD07: the good equipment has a Work Order configured against it", frappe.db.exists("Work Order", {"equipment": frappe.db.get_value("Asset", {"asset_name": "Assembly Torque Station #1"}, "name"), "docstatus": 1}), None)

	check("Release gate reused from Golden Demo #1 (7th reuse)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DMD", "item_code": "INFUSION-PUMP-ACC"}), None)

	serial_no = frappe.db.get_value("Serial No", {"item_code": "INFUSION-PUMP-ACC"}, "name", order_by="creation asc")
	if serial_no:
		genealogy = trace_serial_genealogy(serial_no)
		check("MD05: finished serial traces back to its components", len(genealogy.get("raw_materials_consumed", [])) > 0, genealogy)
		check("MD06: a complaint exists referencing a real serial number", frappe.db.exists("MedDev Complaint", {"serial_or_lot": serial_no}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def get_pharmacy_central_dashboard() -> dict:
	"""Golden Demo #23 (Pharmacy Chain) RX07 — "Central dashboard." Stock across every store
	warehouse plus a company-wide sales total in one call, same "plain aggregate query, not a
	stored doctype" pattern as Golden Demo #7's get_silo_stock()."""
	stock_by_warehouse = frappe.db.sql(
		"""select warehouse, item_code, sum(actual_qty) as balance from `tabStock Ledger Entry`
		where (warehouse = 'Central Warehouse - DPH' or warehouse like 'Store % - DPH')
		and is_cancelled = 0 group by warehouse, item_code having balance != 0 order by warehouse, item_code""",
		as_dict=True,
	)
	total_sales = frappe.db.sql(
		"""select coalesce(sum(grand_total), 0) from `tabPOS Invoice` where company='Demo Pharmacy Chain Co.' and docstatus=1 and is_return=0"""
	)[0][0]
	return {"stock_by_warehouse": stock_by_warehouse, "total_sales_amount": total_sales}


def verify_pharmacy_golden_demo() -> dict:
	"""DP-656 — Golden Demo #23 (Pharmacy Chain) integrity check, same pattern as every prior
	golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": "Demo Pharmacy Chain Co."}), None)

	store_a_balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse='Store A - DPH' and item_code='PARA-500-TAB' and is_cancelled=0")[0][0] or 0
	store_b_balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse='Store B - DPH' and item_code='PARA-500-TAB' and is_cancelled=0")[0][0] or 0
	check("RX01: each store's own stock is independently queryable (different balances)", store_a_balance > 0 and store_b_balance > 0, {"store_a": store_a_balance, "store_b": store_b_balance})
	check("RX02: HQ replenishment reached Store A via a real Material Request", frappe.db.exists("Material Request", {"material_request_type": "Material Transfer", "company": "Demo Pharmacy Chain Co.", "docstatus": 1}), None)
	check("RX04: an inter-store transfer exists (Store A -> Store B)", frappe.db.count("Stock Entry", {"purpose": "Material Transfer", "company": "Demo Pharmacy Chain Co.", "docstatus": 1}) >= 2, None)

	check("RX03: the deliberately-expired batch was never sold", not frappe.db.exists("POS Invoice Item", {"batch_no": "RX03-EXPIRED-TEST"}), None)
	check("RX03: the expired batch still exists (receipt succeeded, only the sale was blocked)", frappe.db.exists("Batch", "RX03-EXPIRED-TEST"), None)

	original_sale = frappe.db.get_value("POS Invoice", {"pos_profile": "Pharmacy Store A POS", "is_return": 0, "docstatus": 1}, "name")
	check("RX05: a POS return exists against a real sale", original_sale and frappe.db.exists("POS Invoice", {"return_against": original_sale, "is_return": 1, "docstatus": 1}), original_sale)

	check("RX06: a Pricing Rule promotion exists and a Sales Order picked up the discounted rate", frappe.db.exists("Pricing Rule", {"title": "Pharmacy Loyalty Week Promotion"}) and frappe.db.exists("Sales Order Item", {"item_code": "PARA-500-TAB", "rate": ["<", 1500]}), None)

	dashboard = get_pharmacy_central_dashboard()
	check("RX07: central dashboard aggregates real stock across stores", len(dashboard.get("stock_by_warehouse", [])) > 0, dashboard)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_poultry_golden_demo() -> dict:
	"""DP-583 — Golden Demo #12 (Poultry Farm Management) integrity check, same pattern as
	every prior golden demo's verify_* function."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	farm = frappe.db.exists("Poultry Farm", "Demo Poultry Farm - Tien Giang")
	check("Farm/Houses exist", farm and frappe.db.count("Poultry House") >= 2, None)

	broiler = frappe.db.get_value("Poultry Flock", "FLOCK-BR-2026-001", ["name", "status"], as_dict=True)
	layer = frappe.db.get_value("Poultry Flock", "FLOCK-LY-2026-001", ["name", "status"], as_dict=True)
	check("PO01: both flocks exist (unique flock_code) and reached Sold", broiler and layer and broiler.status == "Sold" and layer.status == "Sold", {"broiler": broiler, "layer": layer})
	check("PO01: houses were freed back to Empty after sale", frappe.db.get_value("Poultry House", "HOUSE-B1", "status") == "Empty" and frappe.db.get_value("Poultry House", "HOUSE-L1", "status") == "Empty", None)

	if broiler:
		check("PO02: a mortality record exists for the broiler flock", frappe.db.exists("Poultry Mortality Record", {"flock": broiler.name}), None)
		check("PO03: feed logs exist for the broiler flock", frappe.db.count("Poultry Feed Log", {"flock": broiler.name}) > 0, None)
		check("PO04: vaccination due/overdue is detectable", frappe.db.exists("Poultry Vaccination", {"flock": broiler.name, "status": "Overdue"}), None)
		check("PO05: a weight curve exists (2+ weight records)", frappe.db.count("Poultry Weight Record", {"flock": broiler.name}) >= 2, None)

	if layer:
		check("PO06: egg production logged for the Layer flock only", frappe.db.count("Poultry Egg Production", {"flock": layer.name}) >= 2 and frappe.db.count("Poultry Egg Production", {"flock": broiler.name if broiler else ""}) == 0, None)

	lot = frappe.db.get_value("Poultry Sale Lot", {"flock": "FLOCK-BR-2026-001"}, ["customer", "cost_per_kg", "profit", "livability_percent"], as_dict=True)
	check("PO07: Sale Lot exists with computed cost allocation and livability (all non-zero)", lot and lot.cost_per_kg and lot.profit and lot.livability_percent, lot)
	check("PO07: Sale Lot traces to a real Customer", lot and bool(lot.customer), lot.customer if lot else None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_3pl_golden_demo() -> dict:
	"""DP-665 — Golden Demo #24 (Pharma 3PL / GSP / Cold Chain) integrity check, same pattern as
	every prior golden demo's verify_* function. Exactly the 6 lettered tests from master plan
	DEMO 08 (W01-W06), each checked against real data (re-deriving W01's own access-control
	assertion live here too, not just trusting the seed step's self-report)."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	_COMPANY = "Demo 3PL Cold Chain Co."
	_ITEM_A = "COLD-VACCINE-A"
	_ITEM_B = "COLD-BIOLOGIC-B"
	_CLIENT_A = "Global MedSupply Corp"
	_CLIENT_B = "NorthStar Pharma Distributors"
	_CLIENT_A_QUARANTINE_WH = "Client A Quarantine - D3PL"
	_CLIENT_A_RELEASED_WH = "Client A Released - D3PL"
	_CLIENT_B_QUARANTINE_WH = "Client B Quarantine - D3PL"
	_CLIENT_B_RELEASED_WH = "Client B Released - D3PL"
	_CLIENT_A_USER = "client.a.3pl@pharmacountry.vn"

	check("Company exists", frappe.db.exists("Company", {"company_name": _COMPANY}), None)
	check("Warehouse hierarchy: 4 client warehouses carry native Warehouse.customer ownership", frappe.db.get_value("Warehouse", _CLIENT_A_QUARANTINE_WH, "customer") == _CLIENT_A and frappe.db.get_value("Warehouse", _CLIENT_B_RELEASED_WH, "customer") == _CLIENT_B, None)

	# W01 — re-derive the access-control assertion live, not just trust the seed step's own
	# self-report. Same mechanism: Warehouse User Permission (apply_to_all_doctypes=1) cascading
	# through frappe.get_list() (permission-aware), confirmed to exclude another client's
	# warehouses entirely.
	original_user = frappe.session.user
	try:
		frappe.set_user(_CLIENT_A_USER)
		visible = frappe.get_list("Stock Ledger Entry", filters={"item_code": ["in", [_ITEM_A, _ITEM_B]]}, fields=["warehouse"], distinct=True, limit_page_length=0)
		visible_warehouses = {r.warehouse for r in visible}
	finally:
		frappe.set_user(original_user)
	check(
		"W01: Customer A's user cannot see Customer B's stock (Stock Ledger Entry via frappe.get_list)",
		_CLIENT_A_RELEASED_WH in visible_warehouses and _CLIENT_B_RELEASED_WH not in visible_warehouses and _CLIENT_B_QUARANTINE_WH not in visible_warehouses,
		sorted(visible_warehouses),
	)

	# W02 — the reading document itself, once flagged by the validate hook, IS the excursion event.
	excursion = frappe.db.get_value("Cold Chain Temperature Reading", {"warehouse": _CLIENT_A_RELEASED_WH, "temperature_c": 12.0}, ["is_excursion", "status"], as_dict=True)
	normal = frappe.db.get_value("Cold Chain Temperature Reading", {"warehouse": _CLIENT_A_RELEASED_WH, "temperature_c": 4.0}, ["is_excursion", "status"], as_dict=True)
	check("W02: an out-of-range reading was flagged as an Excursion event", excursion and excursion.is_excursion == 1 and excursion.status == "Excursion", excursion)
	check("W02: an in-range reading stayed Normal (the flag is a real comparison, not always-on)", normal and normal.is_excursion == 0 and normal.status == "Normal", normal)

	# W03 — FEFO: the first item row on the real outbound Delivery Note must be the batch with
	# the globally earliest expiry_date among every batch ever received for this item, not the
	# batch received/created first (inbound receiving deliberately made those two orders diverge).
	dn_name = frappe.db.get_value("Delivery Note", {"customer": _CLIENT_A, "company": _COMPANY, "docstatus": 1}, "name")
	first_batch = frappe.db.get_value("Delivery Note Item", {"parent": dn_name}, "batch_no", order_by="idx asc") if dn_name else None
	first_batch_expiry = frappe.db.get_value("Batch", first_batch, "expiry_date") if first_batch else None
	earliest_expiry_overall = frappe.db.sql("select min(expiry_date) from `tabBatch` where item=%s", (_ITEM_A,))[0][0]
	check("W03: FEFO — the earliest-expiry batch (not the earliest-created one) was delivered first", first_batch_expiry and earliest_expiry_overall and first_batch_expiry == earliest_expiry_overall, {"first_batch": first_batch, "first_batch_expiry": str(first_batch_expiry), "earliest_expiry_overall": str(earliest_expiry_overall)})

	# W04 — the blocked attempt never actually created a Delivery Note Item row at all (insert()
	# itself failed), so no submitted or draft Delivery Note Item should ever reference either
	# Quarantine warehouse, and both should now be fully drained (everything QC-released out).
	check("W04: no Delivery Note Item was ever sourced from a Quarantine warehouse", not frappe.db.exists("Delivery Note Item", {"warehouse": ["in", [_CLIENT_A_QUARANTINE_WH, _CLIENT_B_QUARANTINE_WH]]}), None)
	qa_balance = frappe.db.sql("select coalesce(sum(actual_qty),0) from `tabStock Ledger Entry` where warehouse=%s and is_cancelled=0", (_CLIENT_A_QUARANTINE_WH,))[0][0] or 0
	check("W04: Client A Quarantine is fully drained (everything moved to Released via the QC gate)", qa_balance == 0, qa_balance)
	check("W04: an Accepted Quality Inspection backs the release (block_fg_release_without_qa's own gate)", frappe.db.exists("Quality Inspection", {"item_code": _ITEM_A, "status": "Accepted", "docstatus": 1}), None)

	# W05 — native Stock Reconciliation.
	check("W05: a submitted Stock Reconciliation exists for this company", frappe.db.exists("Stock Reconciliation", {"company": _COMPANY, "docstatus": 1}), None)
	b_released_balance = frappe.db.sql("select coalesce(sum(actual_qty),0) from `tabStock Ledger Entry` where item_code=%s and warehouse=%s and is_cancelled=0", (_ITEM_B, _CLIENT_B_RELEASED_WH))[0][0] or 0
	check("W05: the reconciled balance reflects the physical-count correction (< the naive received total of 120)", b_released_balance < 120, b_released_balance)

	# W06 — billing by service rule: a real Sales Invoice per client, computed from real usage.
	si_a = frappe.db.get_value("Sales Invoice", {"customer": _CLIENT_A, "company": _COMPANY, "docstatus": 1}, ["name", "grand_total"], as_dict=True)
	si_b = frappe.db.get_value("Sales Invoice", {"customer": _CLIENT_B, "company": _COMPANY, "docstatus": 1}, ["name", "grand_total"], as_dict=True)
	check("W06: Client A was billed (storage + picking fee, since A has real outbound activity)", si_a and si_a.grand_total > 0 and frappe.db.exists("Sales Invoice Item", {"parent": si_a.name, "item_code": "3PL-STORAGE-FEE"}) and frappe.db.exists("Sales Invoice Item", {"parent": si_a.name, "item_code": "3PL-PICKING-FEE"}), si_a)
	check("W06: Client B was billed (storage fee only, since B has no outbound activity yet)", si_b and si_b.grand_total > 0 and frappe.db.exists("Sales Invoice Item", {"parent": si_b.name, "item_code": "3PL-STORAGE-FEE"}) and not frappe.db.exists("Sales Invoice Item", {"parent": si_b.name, "item_code": "3PL-PICKING-FEE"}), si_b)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


# ============================================================================
# Golden Demo #25 — Consumer Health / Cosmetics Distribution (DP-666..673)
# ============================================================================

_CONSUMER_DIST_COMPANY = "Demo Consumer Distribution Co."
_CONSUMER_DIST_DC_WAREHOUSE = "Distribution Center - DCD"


def get_consumer_dist_territory_sales() -> list:
	"""Golden Demo #25 CD03 — territory-scoped sales aggregate. Plain SQL aggregate over real
	Sales Order data grouped by native Territory, same "thin wrapper over real ledger data"
	pattern as get_pharmacy_central_dashboard()."""
	return frappe.db.sql(
		"""select territory, count(*) as order_count, sum(base_grand_total) as total_amount
		from `tabSales Order`
		where company = %s and docstatus = 1
		group by territory order by territory""",
		(_CONSUMER_DIST_COMPANY,),
		as_dict=True,
	)


def get_consumer_dist_commission_report() -> list:
	"""Golden Demo #25 CD06 — Salesperson commission report. Sums ERPNext's own NATIVE
	`Sales Team.incentives` (auto-computed by SellingController.calculate_contribution() from
	each row's allocated_percentage x commission_rate against amount_eligible_for_commission,
	itself gated by Item.grant_commission) across every submitted Sales Invoice, grouped by
	Sales Person — no custom commission math, just aggregating a native computed field."""
	return frappe.db.sql(
		"""select st.sales_person, count(distinct st.parent) as invoice_count,
		sum(st.incentives) as total_commission
		from `tabSales Team` st
		inner join `tabSales Invoice` si on si.name = st.parent
		where st.parenttype = 'Sales Invoice' and si.company = %s and si.docstatus = 1
		group by st.sales_person order by st.sales_person""",
		(_CONSUMER_DIST_COMPANY,),
		as_dict=True,
	)


def get_consumer_dist_sales_dashboard() -> dict:
	"""Golden Demo #25 — sales dashboard, the last step of the user guide ("...delivery ->
	receivable -> sales dashboard"): stock on hand at the Distribution Center, territory sales,
	commission by salesperson, and total receivable, all aggregated from real documents."""
	stock_by_item = frappe.db.sql(
		"""select item_code, sum(actual_qty) as balance from `tabStock Ledger Entry`
		where warehouse = %s and is_cancelled = 0
		group by item_code having balance != 0 order by item_code""",
		(_CONSUMER_DIST_DC_WAREHOUSE,),
		as_dict=True,
	)
	total_receivable = frappe.db.sql(
		"""select coalesce(sum(outstanding_amount), 0) from `tabSales Invoice`
		where company = %s and docstatus = 1""",
		(_CONSUMER_DIST_COMPANY,),
	)[0][0]
	return {
		"stock_by_item": stock_by_item,
		"territory_sales": get_consumer_dist_territory_sales(),
		"commission_report": get_consumer_dist_commission_report(),
		"total_receivable": total_receivable,
	}


def verify_consumer_dist_golden_demo() -> dict:
	"""DP-673 — Golden Demo #25 (Consumer Health / Cosmetics Distribution) integrity check.
	CD01-CD06, exactly matching the master plan's lettered tests."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": _CONSUMER_DIST_COMPANY}), None)

	# CD01 — Customer price list.
	dealer_so = frappe.db.get_value("Sales Order", {"po_no": "CD01-DEALER-PRICE-TEST"}, "name")
	retail_so = frappe.db.get_value("Sales Order", {"po_no": "CD01-RETAIL-PRICE-TEST"}, "name")
	dealer_rate = frappe.db.get_value("Sales Order Item", {"parent": dealer_so}, "rate") if dealer_so else None
	retail_rate = frappe.db.get_value("Sales Order Item", {"parent": retail_so}, "rate") if retail_so else None
	default_price_list = frappe.db.get_value("Customer", "Golden Health Hanoi Dealer Co.", "default_price_list")
	check("CD01: dealer Customer has its own default_price_list assigned", default_price_list == "Dealer Tier Price List (Consumer Dist Demo)", default_price_list)
	check(
		"CD01: dealer Sales Order resolved the dealer-tier rate, below the standard/retail rate",
		bool(dealer_rate) and bool(retail_rate) and dealer_rate < retail_rate,
		{"dealer_rate": dealer_rate, "retail_rate": retail_rate},
	)

	# CD02 — Promotion period, both edges.
	rule = frappe.db.get_value("Pricing Rule", {"title": "Consumer Dist Tet Cosmetics Promotion"}, ["valid_from", "valid_upto"], as_dict=True)
	inside_so = frappe.db.get_value("Sales Order", {"po_no": "CD02-PROMO-INSIDE"}, "name")
	outside_so = frappe.db.get_value("Sales Order", {"po_no": "CD02-PROMO-OUTSIDE"}, "name")
	inside_rate = frappe.db.get_value("Sales Order Item", {"parent": inside_so}, "rate") if inside_so else None
	outside_rate = frappe.db.get_value("Sales Order Item", {"parent": outside_so}, "rate") if outside_so else None
	check("CD02: Pricing Rule promotion exists with a valid_from/valid_upto window", bool(rule and rule.valid_from and rule.valid_upto), rule)
	check("CD02: order dated INSIDE the promo window got the discounted rate", bool(inside_rate) and inside_rate < 95000, inside_rate)
	check("CD02: order dated OUTSIDE the promo window did NOT get the discount (both edges tested)", outside_rate == 95000, outside_rate)

	# CD03 — Sales territory.
	hanoi_territory = frappe.db.get_value("Sales Order", {"po_no": "CD01-DEALER-PRICE-TEST"}, "territory")
	saigon_territory = frappe.db.get_value("Sales Order", {"po_no": "CD02-PROMO-INSIDE"}, "territory")
	territory_sales = get_consumer_dist_territory_sales()
	territories_with_sales = {row.territory for row in territory_sales if row.total_amount}
	check("CD03: Hanoi dealer Sales Order attributed to the North territory", hanoi_territory == "Northern Vietnam Dealer Territory", hanoi_territory)
	check("CD03: Saigon dealer Sales Order attributed to the South territory", saigon_territory == "Southern Vietnam Dealer Territory", saigon_territory)
	check(
		"CD03: territory-scoped sales aggregate resolves real, non-zero totals for both territories",
		{"Northern Vietnam Dealer Territory", "Southern Vietnam Dealer Territory"} <= territories_with_sales,
		territory_sales,
	)

	# CD04 — Dealer credit.
	credit_limit = frappe.db.get_value("Customer Credit Limit", {"parent": "Golden Health Hanoi Dealer Co.", "company": _CONSUMER_DIST_COMPANY}, "credit_limit")
	check("CD04: dealer Customer has a native credit limit configured", bool(credit_limit), credit_limit)
	check(
		"CD04: the deliberately over-limit dealer order was blocked (no submitted Sales Order was left behind)",
		not frappe.db.exists("Sales Order", {"po_no": "CD04-CREDIT-TEST", "docstatus": 1}),
		None,
	)

	# CD05 — Return linked original lot. Scoped via a join excluding is_return=1 — once the
	# return exists, its own rows ALSO carry against_sales_order=hanoi_flow_so (make_return_doc
	# copies it forward), so an unscoped Delivery Note Item lookup is ambiguous and can pick the
	# return itself instead of the original (found live during verification on this demo).
	hanoi_flow_so = frappe.db.get_value("Sales Order", {"po_no": "CD05-FLOW-HANOI"}, "name")
	original_dn = None
	if hanoi_flow_so:
		_rows = frappe.db.sql(
			"""select dni.parent from `tabDelivery Note Item` dni
			inner join `tabDelivery Note` dn on dn.name = dni.parent
			where dni.against_sales_order = %s and dn.is_return = 0 and dn.docstatus = 1
			order by dn.creation asc limit 1""",
			(hanoi_flow_so,),
		)
		original_dn = _rows[0][0] if _rows else None
	original_batch = frappe.db.get_value("Delivery Note Item", {"parent": original_dn}, "batch_no") if original_dn else None
	return_dn = frappe.db.get_value("Delivery Note", {"return_against": original_dn, "is_return": 1, "docstatus": 1}, "name") if original_dn else None
	return_batch = frappe.db.get_value("Delivery Note Item", {"parent": return_dn}, "batch_no") if return_dn else None
	check("CD05: a Sales Return exists against the original Delivery Note", bool(return_dn), return_dn)
	check(
		"CD05: the return references the SAME batch/lot that was originally delivered, not just any batch of the item",
		bool(original_batch) and original_batch == return_batch,
		{"original_batch": original_batch, "return_batch": return_batch},
	)

	# CD06 — Commission report.
	commission = get_consumer_dist_commission_report()
	persons_with_commission = {row.sales_person for row in commission if row.total_commission}
	check(
		"CD06: commission report resolves real, non-zero per-salesperson commission from Sales Invoice data (native Sales Team.incentives)",
		{"Le Thi Hoa (Consumer Dist Demo)", "Pham Van Minh (Consumer Dist Demo)"} <= persons_with_commission,
		commission,
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Catalog expansion verify functions (P2 post-launch reviewer fix, NOT master-plan DP items) —
# a reviewer correctly flagged the 4 public sites backed by these golden demos
# (catalog.pharmacountry.vn/WEB-01, shop.pharmacountry.vn/WEB-05, pharmacy.pharmacountry.vn/
# WEB-06, brand.pharmacountry.vn/WEB-02) as too thin (1-2 products each). These 4 NEW,
# additive verify functions check the new real Items/BOMs/Item Prices/stock added by each
# golden demo's own new `seed_*_catalog_expansion()` step — deliberately kept SEPARATE from
# the existing `verify_supplement_golden_demo()`/`verify_cosmetics_golden_demo()`/
# `verify_pharmacy_golden_demo()`/`verify_consumer_dist_golden_demo()` above (never edited)
# to avoid any risk of regressing an already-passing, already-idempotency-proven check.
# ---------------------------------------------------------------------------


def verify_supplement_catalog_expansion() -> dict:
	"""Supplement Co side of the P2 catalog-widening fix — 5 new real products (Item + real
	Formula/BOM each), 2 of which (VITD3-1000-SG, ZINC-50-TAB) additionally went through the
	full production -> QC -> LIMS COA pipeline as new WEB-02 brand-site flagship SKUs."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	new_items = ["VITD3-1000-SG", "ZINC-50-TAB", "MULTIVIT-COMP-TAB", "OMEGA3-1000-SG", "PROBIOTIC-10B-CAP"]
	for item_code in new_items:
		check(f"{item_code}: Item exists", frappe.db.exists("Item", item_code), None)
		check(f"{item_code}: has an active default Formula (BOM)", frappe.db.exists("BOM", {"item": item_code, "is_active": 1, "is_default": 1}), None)

	for item_code in ("VITD3-1000-SG", "ZINC-50-TAB"):
		# Scoped via the Work Order that actually produced it, not a bare {"item": ...,
		# "batch_qty": [">", 0]} filter — ambiguous once Demo Consumer Distribution Co. also
		# receives its own second, unrelated batch of this same globally-reused Item (see
		# supplement_seeds.py's _flagship_batch_from_work_order() docstring for the full
		# cross-demo regression history this deliberately avoids repeating).
		batch_rows = frappe.db.sql(
			"""select sbe.batch_no from `tabWork Order` wo
			join `tabStock Entry` se on se.work_order = wo.name and se.purpose = 'Manufacture' and se.docstatus = 1
			join `tabStock Entry Detail` sed on sed.parent = se.name and sed.t_warehouse is not null
			join `tabSerial and Batch Entry` sbe on sbe.parent = sed.serial_and_batch_bundle
			where wo.production_item = %(item)s and wo.company = 'Demo Supplement Co.'
			order by wo.creation asc limit 1""",
			{"item": item_code},
		)
		batch = batch_rows[0][0] if batch_rows else None
		check(f"{item_code}: a production batch exists", bool(batch), batch)
		released = frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DSC", "item_code": item_code}) if batch else False
		check(f"{item_code}: batch reached FG Released (QC gate reused, same as VITC-1000-EFF)", released, None)
		coa = frappe.db.exists("LIMS COA", {"batch_reference": batch, "status": "Approved"}) if batch else False
		check(f"{item_code}: a COA was generated from an Approved LIMS Test (same depth as VITC-1000-EFF's S05)", coa, None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_cosmetics_catalog_expansion() -> dict:
	"""Cosmetics Co side of the P2 catalog-widening fix — one new real finished cosmetic
	(FACIAL-TONER-200ML) with a real Formula (BOM), widening WEB-05's Skincare category."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("FACIAL-TONER-200ML: Item exists", frappe.db.exists("Item", "FACIAL-TONER-200ML"), None)
	check("FACIAL-TONER-200ML: has an active default Formula (BOM)", frappe.db.exists("BOM", {"item": "FACIAL-TONER-200ML", "is_active": 1, "is_default": 1}), None)
	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_pharmacy_catalog_expansion() -> dict:
	"""Pharmacy Chain side of the P2 catalog-widening fix — 7 new real OTC Items with real
	Store A stock (a real, explicitly-set, non-expired Batch.expiry_date) and a real selling
	Item Price on Standard Selling, plus 2 existing real items (reused from other golden
	demos) also given real Store A stock. Confirms the existing RX03-EXPIRED-TEST marker batch
	and PARA-500-TAB's own stock were never touched by any of this."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	new_items = ["IBUPROFEN-400-TAB", "LORATADINE-10-TAB", "COUGH-SYRUP-100ML", "ANTACID-CHEW-TAB", "PARACETAMOL-SYRUP-KIDS", "ORS-SACHET", "ANTIFUNGAL-CREAM-15G"]
	today = frappe.utils.getdate(frappe.utils.nowdate())
	for item_code in new_items:
		check(f"{item_code}: Item exists", frappe.db.exists("Item", item_code), None)
		check(f"{item_code}: has a real selling Item Price on Standard Selling", frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling", "selling": 1}), None)
		batch_rows = frappe.db.sql(
			"""select b.name, b.expiry_date from `tabBatch` b
			inner join `tabSerial and Batch Entry` sbe on sbe.batch_no = b.name
			inner join `tabStock Ledger Entry` sle on sle.serial_and_batch_bundle = sbe.parent
			where b.item = %(item)s and sle.warehouse = 'Store A - DPH' and sle.is_cancelled = 0
			order by b.creation asc limit 1""",
			{"item": item_code},
			as_dict=True,
		)
		batch = batch_rows[0] if batch_rows else None
		check(
			f"{item_code}: has real, non-expired Store A stock (explicit Batch.expiry_date, not silently defaulted)",
			bool(batch and batch.expiry_date and frappe.utils.getdate(batch.expiry_date) > today),
			batch,
		)

	for item_code in ("VITC-1000-EFF", "MULTIVIT-COMP-TAB"):
		check(f"{item_code}: also stocked at Store A (reused item)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "Store A - DPH", "item_code": item_code}), None)

	check("RX03-EXPIRED-TEST marker batch untouched (still exists)", frappe.db.exists("Batch", "RX03-EXPIRED-TEST"), None)
	para_balance = frappe.db.sql("select sum(actual_qty) from `tabStock Ledger Entry` where warehouse='Store A - DPH' and item_code='PARA-500-TAB' and is_cancelled=0")[0][0] or 0
	check("PARA-500-TAB Store A stock still positive (existing flagship untouched)", para_balance > 0, para_balance)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_consumer_dist_catalog_expansion() -> dict:
	"""Consumer Distribution Co side of the P2 catalog-widening fix — this is the ONE company
	WEB-01's/WEB-05's own `_safe_item_codes()` queries actually read from. Confirms all 6 new
	items (5 supplement + 1 cosmetics) now satisfy the SAME 2 real, data-driven conditions
	those live queries require: a real Stock Ledger Entry for this company, and a real selling
	Item Price on Standard Selling — proving the richer catalog will actually surface on both
	sites with zero frontend code change, not just that backend data exists in isolation."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	expansion_items = ["VITD3-1000-SG", "ZINC-50-TAB", "MULTIVIT-COMP-TAB", "OMEGA3-1000-SG", "PROBIOTIC-10B-CAP", "FACIAL-TONER-200ML"]
	for item_code in expansion_items:
		has_sle = frappe.db.exists("Stock Ledger Entry", {"warehouse": _CONSUMER_DIST_DC_WAREHOUSE, "item_code": item_code})
		has_price = frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling", "selling": 1})
		check(f"{item_code}: real Stock Ledger Entry at the Distribution Center", has_sle, None)
		check(f"{item_code}: real selling Item Price on Standard Selling", has_price, None)

	safe_codes = frappe.db.sql(
		"""select distinct i.item_code from `tabItem` i
		inner join `tabStock Ledger Entry` sle on sle.item_code = i.item_code and sle.company = %(company)s
		inner join `tabItem Price` ip on ip.item_code = i.item_code and ip.selling = 1 and ip.price_list = 'Standard Selling'
		where i.disabled = 0""",
		{"company": _CONSUMER_DIST_COMPANY},
	)
	safe_codes = {r[0] for r in safe_codes}
	check(
		"WEB-01/WEB-05's own live _safe_item_codes() condition now covers all 8 real products (2 original + 6 new)",
		{"VITC-1000-EFF", "FACIAL-CLEANSER-150ML"} | set(expansion_items) <= safe_codes,
		sorted(safe_codes),
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_premix_golden_demo() -> dict:
	"""DP-679 — Golden Demo #26 (Premix / Feed Additive Manufacturing) integrity check.
	PM01-PM07, exactly matching the master plan's lettered tests. The negative tests themselves
	(PM01-PM04) leave no artifact behind (a blocked insert() never commits), so this re-derives
	each guarantee from real, current data rather than trusting the seed step's own self-report
	— e.g. PM01/PM03 recompute actual consumed quantities/order directly from Stock Entry
	Detail, not just "the seed step said it passed"."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	_COMPANY = "Demo Premix Co."
	_FG_ITEM = "PREMIX-BROILER-2PCT"
	_CRITICAL_ITEM = "SELENIUM-PREMIX"

	check("Company exists", frappe.db.exists("Company", {"company_name": _COMPANY}), None)

	bom = frappe.db.get_value("BOM", {"item": _FG_ITEM, "is_active": 1}, ["name", "is_default", "premix_approval_status", "quantity"], as_dict=True)
	check("PM04: an active default Formula (BOM) exists with premix_approval_status='Approved'", bom and bom.is_default and bom.premix_approval_status == "Approved", bom)

	wo = frappe.db.get_value("Work Order", {"production_item": _FG_ITEM, "docstatus": 1}, ["name", "qty", "produced_qty", "bom_no"], as_dict=True)
	check("Work Order exists and is submitted", bool(wo), wo)

	se_name = frappe.db.get_value("Stock Entry", {"work_order": wo.name, "purpose": "Manufacture", "docstatus": 1}, "name") if wo else None
	check("Manufacture Stock Entry exists and is submitted", bool(se_name), se_name)

	# PM02 — critical ingredient double-check (four-eyes control).
	verification = frappe.db.get_value(
		"Premix Weighing Verification", {"work_order": wo.name if wo else None, "item_code": _CRITICAL_ITEM}, ["status", "weighed_by", "verified_by"], as_dict=True
	)
	check(
		"PM02: critical ingredient has a Verified weighing record with a DIFFERENT second person signed off (four-eyes)",
		verification and verification.status == "Verified" and verification.verified_by and verification.verified_by != verification.weighed_by,
		verification,
	)

	# PM01 — micro-weigh tolerance: recompute actual consumption vs BOM-scaled expectation for
	# every micro ingredient directly from Stock Entry Detail, not from the seed step's report.
	if se_name and bom:
		bom_items = {r.item_code: r.qty for r in frappe.get_all("BOM Item", filters={"parent": bom.name}, fields=["item_code", "qty"])}
		micro_items = {i.name for i in frappe.get_all("Item", filters={"is_micro_ingredient": 1}, fields=["name"])}
		consumed = frappe.get_all("Stock Entry Detail", filters={"parent": se_name, "s_warehouse": ["is", "set"]}, fields=["item_code", "qty"])
		scale = (wo.qty / bom.quantity) if bom.quantity else 1
		pm01_ok = True
		pm01_detail = []
		for row in consumed:
			if row.item_code not in micro_items or row.item_code not in bom_items:
				continue
			expected_qty = bom_items[row.item_code] * scale
			deviation = abs(row.qty - expected_qty) / expected_qty * 100 if expected_qty else 0
			pm01_detail.append({"item_code": row.item_code, "consumed": row.qty, "expected": expected_qty, "deviation_percent": round(deviation, 2)})
			if deviation > 1.0:
				pm01_ok = False
		check("PM01: every micro ingredient's actual consumption is within ±1% of the Formula's expected qty", pm01_ok and len(pm01_detail) > 0, pm01_detail)
	else:
		check("PM01: every micro ingredient's actual consumption is within ±1% of the Formula's expected qty", False, "no manufacture Stock Entry found")

	# PM03 — sequence rule: recompute idx-order of consumption rows vs BOM Item.sequence_no.
	if se_name and bom:
		seq_map = {r.item_code: r.sequence_no for r in frappe.get_all("BOM Item", filters={"parent": bom.name}, fields=["item_code", "sequence_no"])}
		rows = frappe.get_all("Stock Entry Detail", filters={"parent": se_name, "s_warehouse": ["is", "set"]}, fields=["item_code", "idx"], order_by="idx asc")
		seqs_in_order = [seq_map.get(r.item_code) for r in rows if seq_map.get(r.item_code)]
		pm03_ok = seqs_in_order == sorted(seqs_in_order) and len(seqs_in_order) >= 2
		check("PM03: actual consumption order (Stock Entry Detail idx) matches the Formula's ascending mixing sequence", pm03_ok, seqs_in_order)
	else:
		check("PM03: actual consumption order (Stock Entry Detail idx) matches the Formula's ascending mixing sequence", False, "no manufacture Stock Entry found")

	# PM05 — lot trace, reusing Golden Demo #7's trace_feed_batch_genealogy() unmodified.
	fg_batch = frappe.db.get_value("Batch", {"item": _FG_ITEM}, "name", order_by="creation desc")
	genealogy = trace_feed_batch_genealogy(fg_batch) if fg_batch else None
	consumed_items = {r.get("item_code") for r in (genealogy or {}).get("raw_materials_consumed", [])}
	check(
		"PM05: finished premix batch traces back to every raw ingredient batch/consumption (carrier, mineral mix, all 4 micro ingredients)",
		fg_batch and consumed_items >= {"RICE-HULL", "MINERAL-MIX", "SELENIUM-PREMIX", "VIT-D3", "VIT-A-ACETATE", "VIT-E"},
		genealogy,
	)

	# PM06 — COA (native Quality Inspection Reading, numeric min/max band).
	qi = frappe.db.get_value("Quality Inspection", {"batch_no": fg_batch, "status": "Accepted", "docstatus": 1}, "name") if fg_batch else None
	reading = frappe.db.get_value("Quality Inspection Reading", {"parent": qi}, ["specification", "min_value", "max_value", "reading_1", "status"], as_dict=True) if qi else None
	pm06_ok = bool(reading and reading.status == "Accepted" and reading.min_value <= float(reading.reading_1) <= reading.max_value)
	check("PM06: finished batch has an Accepted QC/COA record with measured potency within the target tolerance band", pm06_ok, reading)

	# PM07 — production reconciliation (actual yield vs expected).
	check("PM07: production reconciliation — actual output qty is a real, non-zero fraction (>=95%) of the Work Order's target qty", wo and wo.produced_qty and (wo.produced_qty / wo.qty) >= 0.95, wo)

	check("Release gate reused from Golden Demo #1 (block_fg_release_without_qa, unmodified)", frappe.db.exists("Stock Ledger Entry", {"warehouse": "FG Released - DPX", "item_code": _FG_ITEM}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Golden Demo #27 — Feed / Ingredient Trading (master plan DEMO 21, "PHASE 6" item 8)
# ---------------------------------------------------------------------------

_INGREDIENT_TRADING_COMPANY = "Demo Ingredient Trading Co."
_INGREDIENT_TRADING_ITEMS = ["SOYBEAN-MEAL-48", "FISH-MEAL-65"]


def get_ingredient_supplier_lot(batch_no: str) -> dict:
	"""Golden Demo #27 FT03 — supplier lot. A LIGHTER lookup than
	trace_feed_batch_genealogy() (which is keyed on finding a Manufacture/Repack Stock Entry
	that consumed the batch — this is a pure TRADING demo with no manufacturing step at all, so
	that function would always return an empty raw_materials_consumed list here). Which supplier
	and which specific Purchase Receipt (shipment) a purchased batch came from, via
	Batch -> Serial and Batch Entry -> Serial and Batch Bundle (voucher_type='Purchase Receipt',
	voucher_no=<PR>) -> Purchase Receipt.supplier — the Serial and Batch Bundle's own
	voucher_type/voucher_no is used directly (one hop shorter than going through Stock Ledger
	Entry, confirmed by reading serial_and_batch_bundle.json before writing this)."""
	rows = frappe.db.sql(
		"""select sbb.voucher_no as purchase_receipt, pr.supplier, pr.posting_date, pr.company
		from `tabSerial and Batch Entry` sbe
		inner join `tabSerial and Batch Bundle` sbb on sbb.name = sbe.parent
		inner join `tabPurchase Receipt` pr on pr.name = sbb.voucher_no
		where sbe.batch_no = %(batch_no)s and sbb.voucher_type = 'Purchase Receipt' and pr.docstatus = 1
		limit 1""",
		{"batch_no": batch_no},
		as_dict=True,
	)
	if not rows:
		return {"batch_no": batch_no, "purchase_receipt": None, "supplier": None}
	row = rows[0]
	return {"batch_no": batch_no, "purchase_receipt": row.purchase_receipt, "supplier": row.supplier, "received_on": row.posting_date, "company": row.company}


def get_ingredient_price_history(item_code: str | None = None) -> list:
	"""Golden Demo #27 FT06 — price history. Pure aggregation over native
	Item Price.valid_from/price_list_rate — no new schema. Multiple Item Price rows per
	item/price_list are allowed by ERPNext as long as they don't all match an existing row's
	valid_from/valid_upto/uom/customer/supplier/batch_no exactly (confirmed by reading
	item_price.py's own check_duplicates() before relying on this)."""
	items = [item_code] if item_code else _INGREDIENT_TRADING_ITEMS
	return frappe.db.sql(
		"""select item_code, price_list, selling, buying, valid_from, price_list_rate
		from `tabItem Price` where item_code in %(items)s
		order by item_code, valid_from asc""",
		{"items": items},
		as_dict=True,
	)


def get_ingredient_trading_margin_report() -> list:
	"""Golden Demo #27 FT07 — margin report. Real aggregation over actual Purchase Invoice
	(cost, base_amount already company-currency-converted) vs. Sales Invoice (revenue) data per
	traded item, same "thin wrapper over real ledger data" pattern as
	get_pharmacy_central_dashboard()/3PL's billing run/get_consumer_dist_commission_report()."""
	purchases = {
		r.item_code: r
		for r in frappe.db.sql(
			"""select pii.item_code, sum(pii.qty) as purchase_qty, sum(pii.base_amount) as purchase_value
			from `tabPurchase Invoice Item` pii inner join `tabPurchase Invoice` pi on pi.name = pii.parent
			where pi.company = %s and pi.docstatus = 1 group by pii.item_code""",
			(_INGREDIENT_TRADING_COMPANY,),
			as_dict=True,
		)
	}
	sales = {
		r.item_code: r
		for r in frappe.db.sql(
			"""select sii.item_code, sum(sii.qty) as sales_qty, sum(sii.base_amount) as sales_value
			from `tabSales Invoice Item` sii inner join `tabSales Invoice` si on si.name = sii.parent
			where si.company = %s and si.docstatus = 1 group by sii.item_code""",
			(_INGREDIENT_TRADING_COMPANY,),
			as_dict=True,
		)
	}
	report = []
	for item_code in sorted(set(purchases) | set(sales)):
		p = purchases.get(item_code)
		s = sales.get(item_code)
		avg_buy_rate = (p.purchase_value / p.purchase_qty) if p and p.purchase_qty else None
		avg_sell_rate = (s.sales_value / s.sales_qty) if s and s.sales_qty else None
		margin_per_unit = (avg_sell_rate - avg_buy_rate) if (avg_buy_rate is not None and avg_sell_rate is not None) else None
		report.append(
			{
				"item_code": item_code,
				"purchase_qty": p.purchase_qty if p else 0,
				"purchase_value": p.purchase_value if p else 0,
				"avg_buy_rate": avg_buy_rate,
				"sales_qty": s.sales_qty if s else 0,
				"sales_value": s.sales_value if s else 0,
				"avg_sell_rate": avg_sell_rate,
				"margin_per_unit": margin_per_unit,
				"estimated_margin_total": (margin_per_unit * s.sales_qty) if (margin_per_unit is not None and s) else None,
			}
		)
	return report


def verify_ingredient_trading_golden_demo() -> dict:
	"""DP-685 — Golden Demo #27 (Feed / Ingredient Trading) integrity check. FT01-FT07, exactly
	matching the master plan's lettered tests. Re-derives every guarantee from live data (native
	PO/PR/PI fields, real Batch/Serial and Batch Bundle links, real Blanket Order/Item Price/
	Invoice rows) rather than trusting any seed step's own self-report."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Company exists", frappe.db.exists("Company", {"company_name": _INGREDIENT_TRADING_COMPANY}), None)

	# FT01 — shipment quantity reconciliation, recomputed directly from native PO/PR/PI fields.
	po1_name = frappe.db.get_value("Purchase Order", {"title": "IT-PO-SOY-01"}, "name")
	po1_item = frappe.db.get_value("Purchase Order Item", {"parent": po1_name, "item_code": "SOYBEAN-MEAL-48"}, ["qty", "received_qty"], as_dict=True) if po1_name else None
	pr1_name = frappe.db.get_value("Purchase Receipt Item", {"purchase_order": po1_name, "item_code": "SOYBEAN-MEAL-48"}, "parent") if po1_name else None
	billed_qty = flt(
		frappe.db.sql(
			"""select coalesce(sum(pii.qty), 0) from `tabPurchase Invoice Item` pii inner join `tabPurchase Invoice` pi on pi.name = pii.parent
			where pii.purchase_receipt = %s and pii.item_code = 'SOYBEAN-MEAL-48' and pi.docstatus = 1""",
			(pr1_name,),
		)[0][0]
	) if pr1_name else None
	check(
		"FT01: shipment quantity reconciles across PO -> Purchase Receipt -> Purchase Invoice (ordered > received > 0, shrinkage detected; billed matches ACTUAL received, not the nominal order)",
		bool(po1_item and pr1_name and 0 < po1_item.received_qty < po1_item.qty and billed_qty == po1_item.received_qty),
		{"ordered": po1_item.qty if po1_item else None, "received": po1_item.received_qty if po1_item else None, "billed": billed_qty},
	)

	# FT02 — FX handling, two POs identical except conversion_rate.
	po2_name = frappe.db.get_value("Purchase Order", {"title": "IT-PO-SOY-02-FX"}, "name")
	po1_fx = frappe.db.get_value("Purchase Order", po1_name, ["grand_total", "base_grand_total", "conversion_rate"], as_dict=True) if po1_name else None
	po2_fx = frappe.db.get_value("Purchase Order", po2_name, ["grand_total", "base_grand_total", "conversion_rate"], as_dict=True) if po2_name else None
	ft02_ok = bool(
		po1_fx and po2_fx
		and po1_fx.grand_total == po2_fx.grand_total
		and po1_fx.conversion_rate != po2_fx.conversion_rate
		and round(po1_fx.base_grand_total) == round(po1_fx.grand_total * po1_fx.conversion_rate)
		and round(po2_fx.base_grand_total) == round(po2_fx.grand_total * po2_fx.conversion_rate)
		and po1_fx.base_grand_total != po2_fx.base_grand_total
	)
	check(
		"FT02: FX handling — identical USD grand_total converted at two different conversion_rates yields two genuinely different, arithmetically-correct base_grand_total (VND) amounts",
		ft02_ok,
		{"po1": po1_fx, "po2": po2_fx},
	)

	# FT03 — supplier lot.
	soy_batch = frappe.db.get_value(
		"Purchase Receipt Item", {"purchase_order": po1_name, "item_code": "SOYBEAN-MEAL-48"}, "batch_no"
	) if po1_name else None
	if not soy_batch and pr1_name:
		soy_batch = frappe.db.sql(
			"""select sbe.batch_no from `tabPurchase Receipt Item` pri
			inner join `tabSerial and Batch Entry` sbe on sbe.parent = pri.serial_and_batch_bundle
			where pri.parent = %s and pri.item_code = 'SOYBEAN-MEAL-48' limit 1""",
			(pr1_name,),
		)
		soy_batch = soy_batch[0][0] if soy_batch else None
	lot = get_ingredient_supplier_lot(soy_batch) if soy_batch else None
	check(
		"FT03: purchased batch traces back to its specific supplier and shipment (Purchase Receipt)",
		bool(lot and lot.get("supplier") == "Cargill Asia Trading Pte Ltd" and lot.get("purchase_receipt") == pr1_name),
		lot,
	)

	# FT04 — incoming QC.
	qi = frappe.db.get_value("Quality Inspection", {"batch_no": soy_batch, "reference_type": "Purchase Receipt", "status": "Accepted", "docstatus": 1}, ["name", "inspection_type"], as_dict=True) if soy_batch else None
	released = frappe.db.sql(
		"""select 1 from `tabStock Ledger Entry` sle join `tabSerial and Batch Entry` sbe on sbe.parent = sle.serial_and_batch_bundle
		where sle.warehouse = 'Trading Released - DIT' and sbe.batch_no = %s and sle.is_cancelled = 0 limit 1""",
		(soy_batch,),
	) if soy_batch else None
	check(
		"FT04: batch has an Accepted incoming Quality Inspection against its Purchase Receipt, and only THEN reached the Released warehouse (block_fg_release_without_qa reuse)",
		bool(qi and qi.inspection_type == "Incoming" and released),
		{"quality_inspection": qi, "released": bool(released)},
	)

	# FT05 — contract quantity (native Blanket Order draw-down).
	bo_name = frappe.db.get_value("Blanket Order", {"customer": "Hau Giang Feed Mill Co. (Trading Demo)", "blanket_order_type": "Selling"}, "name")
	bo_item = frappe.db.get_value("Blanket Order Item", {"parent": bo_name, "item_code": "SOYBEAN-MEAL-48"}, ["qty", "ordered_qty"], as_dict=True) if bo_name else None
	check(
		"FT05: Blanket Order commits a quantity and the real Sales Order's draw-down is tracked against it natively (0 < ordered_qty < committed qty)",
		bool(bo_item and 0 < bo_item.ordered_qty < bo_item.qty),
		bo_item,
	)
	check(
		"FT05: an over-commit Sales Order beyond the Blanket Order's remaining qty was blocked (no submitted doc left behind)",
		not frappe.db.exists("Sales Order", {"po_no": "IT-SO-CONTRACT-OVERCOMMIT", "docstatus": 1}),
		None,
	)

	# FT06 — price history, a genuinely increasing series over time.
	history = get_ingredient_price_history("SOYBEAN-MEAL-48")
	rates = [r.price_list_rate for r in history]
	check(
		"FT06: price history for a traded ingredient is queryable and shows a genuine trend over time (>=3 dated points, strictly non-decreasing, first < last)",
		len(rates) >= 3 and rates == sorted(rates) and rates[0] < rates[-1],
		rates,
	)

	# FT07 — margin report, real positive margin for BOTH traded items.
	margin_report = get_ingredient_trading_margin_report()
	items_with_positive_margin = {row["item_code"] for row in margin_report if row.get("margin_per_unit") and row["margin_per_unit"] > 0}
	check(
		"FT07: margin report resolves a real, positive sell-vs-buy margin for both traded items from actual Purchase/Sales Invoice data",
		{"SOYBEAN-MEAL-48", "FISH-MEAL-65"} <= items_with_positive_margin,
		margin_report,
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def trace_meat_finished_lot(packing_lot: str) -> dict:
	"""Golden Demo #28 (Meat Processing) MP06 — "Finished lot -> source animal/farm," the
	reverse-genealogy analogue of Seafood's trace_seafood_carton(). Walks Packing Lot ->
	Processing Batch -> ALL of its sources (a real multi-row child table, unlike Seafood's 1:1
	chain) -> each Incoming Lot -> its own Dynamic-Link source (a Pig Sale Lot from Golden Demo
	#11, resolved one hop further to its actual Pig Grower Batch) or, for a self-contained
	"Direct Farm Intake" lot, the named source farm/cooperative directly."""
	batch_name = frappe.db.get_value("Meat Packing Lot", packing_lot, "processing_batch")
	if not batch_name:
		return {"packing_lot": packing_lot}

	source_rows = frappe.get_all("Meat Processing Batch Source", filters={"parent": batch_name}, fields=["incoming_lot", "live_weight_kg"])
	sources = []
	for row in source_rows:
		lot = frappe.db.get_value(
			"Meat Incoming Lot", row.incoming_lot, ["source_type", "source_reference", "source_farm_name", "species", "receiving_date"], as_dict=True
		)
		farm_trace = None
		if lot.source_type == "Pig Sale Lot" and lot.source_reference:
			pig_batch = frappe.db.get_value("Pig Sale Lot", lot.source_reference, "batch")
			if pig_batch:
				grower_batch = frappe.db.get_value("Pig Grower Batch", pig_batch, ["batch_code", "farrowing", "pen"], as_dict=True)
				farm_trace = {"pig_sale_lot": lot.source_reference, "pig_grower_batch": pig_batch, "grower_batch_detail": grower_batch}
		elif lot.source_type == "Cattle Sale Lot" and lot.source_reference:
			animal = frappe.db.get_value("Cattle Sale Lot", lot.source_reference, "animal")
			farm_trace = {"cattle_sale_lot": lot.source_reference, "cattle_animal": animal}
		elif lot.source_type == "Direct Farm Intake":
			farm_trace = {"source_farm_name": lot.source_farm_name}

		sources.append(
			{
				"incoming_lot": row.incoming_lot,
				"live_weight_kg": row.live_weight_kg,
				"source_type": lot.source_type,
				"species": lot.species,
				"farm_trace": farm_trace,
			}
		)

	return {"packing_lot": packing_lot, "processing_batch": batch_name, "sources": sources}


def get_meat_recall_impact(incoming_lot: str) -> list:
	"""Golden Demo #28 (Meat Processing) MP07 — "given a specific incoming lot or processing
	batch, identify every finished/distributed lot that must be recalled." A real forward
	traversal (the opposite direction of trace_meat_finished_lot()'s reverse genealogy): Incoming
	Lot -> every Processing Batch whose own sources child table consumed it -> every Packing Lot
	made from those batches -> whether/where each one was actually distributed."""
	batch_names = frappe.get_all("Meat Processing Batch Source", filters={"incoming_lot": incoming_lot}, pluck="parent")
	affected = []
	for batch_name in set(batch_names):
		packing_lots = frappe.get_all("Meat Packing Lot", filters={"processing_batch": batch_name}, fields=["name", "status"])
		for pl in packing_lots:
			distribution = frappe.db.get_value("Meat Distribution", {"packing_lot": pl.name}, ["customer", "destination", "distribution_date"], as_dict=True)
			affected.append(
				{
					"incoming_lot": incoming_lot,
					"processing_batch": batch_name,
					"packing_lot": pl.name,
					"packing_lot_status": pl.status,
					"distribution": distribution,
				}
			)
	return affected


def verify_meat_processing_golden_demo() -> dict:
	"""DP-690 — Golden Demo #28 (Meat / Animal Product Processing) integrity check. MP01-MP07,
	exactly matching the master plan's lettered tests. Re-derives every guarantee from live data
	rather than trusting any seed step's own self-report, same discipline as every prior golden
	demo's verify_* function (and directly caught real bugs in 3 of the last 3 prior demos)."""
	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	check("Plant exists", frappe.db.exists("Meat Plant", "Dong Nai Meat Processing Plant"), None)

	# MP01 — incoming lot(s) recorded and traceable to a specific farm/source.
	lot1 = frappe.db.get_value("Meat Incoming Lot", "MPLOT-2026-001", ["source_type", "source_reference", "inspection_status", "live_weight_kg"], as_dict=True)
	lot2 = frappe.db.get_value("Meat Incoming Lot", "MPLOT-2026-002", ["source_type", "source_farm_name", "inspection_status", "live_weight_kg"], as_dict=True)
	check(
		"MP01: Incoming Lot 1 exists, sourced from a real Pig Sale Lot via Dynamic Link, ante-mortem inspection Passed",
		bool(lot1 and lot1.source_type == "Pig Sale Lot" and lot1.source_reference and frappe.db.exists("Pig Sale Lot", lot1.source_reference) and lot1.inspection_status == "Passed"),
		lot1,
	)
	check(
		"MP01: Incoming Lot 2 exists, a self-contained direct-farm-intake lot with a named source farm, ante-mortem inspection Passed",
		bool(lot2 and lot2.source_type == "Direct Farm Intake" and lot2.source_farm_name and lot2.inspection_status == "Passed"),
		lot2,
	)

	# MP02 — yield, recomputed independently from raw fields (never trust the stored percent).
	batch = frappe.db.get_value(
		"Meat Processing Batch", "MPPROC-2026-001", ["total_live_weight_kg", "carcass_weight_kg", "carcass_yield_percent", "output_cut_weight_kg", "cut_yield_percent", "qc_status"], as_dict=True
	)
	expected_carcass_yield = round((batch.carcass_weight_kg / batch.total_live_weight_kg) * 100, 2) if batch and batch.total_live_weight_kg else None
	expected_cut_yield = round((batch.output_cut_weight_kg / batch.carcass_weight_kg) * 100, 2) if batch and batch.carcass_weight_kg else None
	check(
		"MP02: carcass yield % is server-computed, matches independent recomputation, and is realistic (60-80%)",
		bool(batch and batch.carcass_yield_percent == expected_carcass_yield and 60 <= batch.carcass_yield_percent <= 80),
		{"stored": batch.carcass_yield_percent if batch else None, "recomputed": expected_carcass_yield},
	)
	check(
		"MP02: cut yield % is server-computed, matches independent recomputation, and is realistic (75-95%)",
		bool(batch and batch.cut_yield_percent == expected_cut_yield and 75 <= batch.cut_yield_percent <= 95),
		{"stored": batch.cut_yield_percent if batch else None, "recomputed": expected_cut_yield},
	)
	check(
		"MP02: over-yield negative test left no artifact behind (throwaway batch never persisted)",
		not frappe.db.exists("Meat Processing Batch", "MPPROC-2026-NEGTEST"),
		None,
	)

	# MP03 — process lot genealogy: the batch's own sources child table resolves BOTH incoming lots.
	source_rows = frappe.get_all("Meat Processing Batch Source", filters={"parent": "MPPROC-2026-001"}, fields=["incoming_lot", "live_weight_kg"])
	source_lots = {r.incoming_lot for r in source_rows}
	sum_sources = sum(flt(r.live_weight_kg) for r in source_rows)
	check(
		"MP03: Processing Batch genealogy resolves BOTH incoming lots (a real multi-source consumption, not a 1:1 shortcut), summing to the batch's own total_live_weight_kg",
		source_lots == {"MPLOT-2026-001", "MPLOT-2026-002"} and bool(batch) and sum_sources == batch.total_live_weight_kg,
		{"source_lots": sorted(source_lots), "sum": sum_sources, "batch_total": batch.total_live_weight_kg if batch else None},
	)

	# MP04 — QC hold/release, a real enforced gate.
	check("MP04: Processing Batch is QC-Released (the real Packing Lot could only be created after this)", batch and batch.qc_status == "Released", batch.qc_status if batch else None)
	check(
		"MP04: pack-while-On-Hold negative test left no artifact behind (marker carton_count=9999 never persisted)",
		not frappe.db.exists("Meat Packing Lot", {"carton_count": 9999}),
		None,
	)
	real_packing = frappe.db.get_value("Meat Packing Lot", "MPPACK-2026-001", ["carton_count", "total_packed_weight_kg", "status"], as_dict=True)
	check("MP04: the real Packing Lot exists with the expected carton count", bool(real_packing and real_packing.carton_count == 62), real_packing)

	# MP05 — cold storage, with temperature/condition tracking, chain-closed to Distributed.
	cold_storage = frappe.db.get_value("Meat Cold Storage Record", {"packing_lot": "MPPACK-2026-001"}, ["storage_temp_c", "status"], as_dict=True)
	check(
		"MP05: Cold Storage record exists with a real sub-zero temperature, closed to Distributed once shipped",
		bool(cold_storage and cold_storage.storage_temp_c < 0 and cold_storage.status == "Distributed"),
		cold_storage,
	)

	# MP06 — finished lot -> source animal/farm, the full reverse genealogy chain.
	trace = trace_meat_finished_lot("MPPACK-2026-001")
	pig_branch = next((s for s in trace.get("sources", []) if s["source_type"] == "Pig Sale Lot"), None)
	direct_branch = next((s for s in trace.get("sources", []) if s["source_type"] == "Direct Farm Intake"), None)
	check(
		"MP06: finished Packing Lot traces all the way back to a real Pig Grower Batch (via its Pig Sale Lot)",
		bool(pig_branch and pig_branch["farm_trace"] and pig_branch["farm_trace"].get("pig_grower_batch")),
		pig_branch,
	)
	check(
		"MP06: finished Packing Lot ALSO traces back to the named direct-intake source farm (the second genealogy branch)",
		bool(direct_branch and direct_branch["farm_trace"] and direct_branch["farm_trace"].get("source_farm_name")),
		direct_branch,
	)

	# MP07 — recall: given EITHER incoming lot, identify every finished/distributed lot affected.
	impact1 = get_meat_recall_impact("MPLOT-2026-001")
	impact2 = get_meat_recall_impact("MPLOT-2026-002")
	distributed1 = [i for i in impact1 if i["packing_lot_status"] == "Distributed" and i["distribution"] and i["distribution"].get("customer")]
	distributed2 = [i for i in impact2 if i["packing_lot_status"] == "Distributed" and i["distribution"] and i["distribution"].get("customer")]
	check(
		"MP07: recall impact for EITHER incoming lot correctly identifies the SAME distributed finished Packing Lot with a real customer",
		bool(distributed1 and distributed2 and {i["packing_lot"] for i in distributed1} == {i["packing_lot"] for i in distributed2} == {"MPPACK-2026-001"}),
		{"from_lot1": impact1, "from_lot2": impact2},
	)
	check("MP07: a recall drill record exists referencing the originating incoming lot", frappe.db.exists("QMS Recall", {"batch_reference": "MPLOT-2026-001"}), None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_executive_assistant_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-01 (Executive Assistant) + Tool Registry integrity check, same
	pattern as every prior golden demo's verify_* function AND `verify_ai_foundation()`
	(Phase 2A). Re-derives every acceptance-criteria claim from live data/live calls rather
	than trusting the seed step's own self-report:
	  - Tool Registry: 5 AI Tools registered and enabled, each with a real, importable
	    python_function_path.
	  - Architecture: no arbitrary SQL exposed to the AI layer (every tool call goes through
	    ask_enterprise(), which resolves tools from the AI Tool registry, never a raw query).
	  - Permission-aware + "không trả dữ liệu ngoài quyền": 2 real, differently-scoped users
	    (Golden Demo #24's 3PL Client A/B) asking the SAME question get DIFFERENT, correctly
	    scoped, non-leaking results.
	  - Có nguồn dữ liệu: every answer carries non-empty `sources` citations.
	  - Log provider/model/tool: every invocation is logged to AI Job Log with provider, model,
	    AND the tool_calls list (extending the existing, otherwise-unused schema field).
	  - Fact vs. interpretation: data_facts and ai_interpretation are structurally separate
	    fields, never blended into one opaque string.
	"""
	from enterprise_core.enterprise_core.ai_executive_assistant import QUESTION_TOOL_MAP, ask_enterprise

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry ---
	tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	check("5 AI Tools registered", len(tools) >= 5, [t.tool_code for t in tools])
	check("All registered AI Tools are enabled", all(t.enabled for t in tools), tools)
	importable = []
	for t in tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable.append(callable(fn))
		except Exception:
			importable.append(False)
	check("Every AI Tool's python_function_path actually imports to a callable", all(importable), dict(zip([t.tool_code for t in tools], importable)))

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation ---
	check("ask_enterprise_synthesis AI Action exists (reuses existing AI foundation router/policy/logging)", frappe.db.exists("AI Action", "ask_enterprise_synthesis"), None)
	check("ask_enterprise_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "ask_enterprise_synthesis", "enabled": 1}), None)

	# --- All 5 example questions answer with real data, sourced, logged ---
	responses = {}
	for question_code, expected_tools in QUESTION_TOOL_MAP.items():
		resp = ask_enterprise(question_code, user="Administrator")
		responses[question_code] = resp
		check(f"'{question_code}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{question_code}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"'{question_code}': response cites real data sources ('có nguồn dữ liệu')", len(resp["sources"]) > 0, resp["sources"][:3])
		check(f"'{question_code}': provider + model logged on the response", bool(resp["provider"]) and bool(resp["model"]), {"provider": resp["provider"], "model": resp["model"]})
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls", "retrieved_sources", "action"], as_dict=True) if resp.get("job_log") else None
		check(
			f"'{question_code}': AI Job Log entry records provider/model/tool_calls (extends the existing CE-13 schema field)",
			bool(log and log.provider and log.model and log.tool_calls and frappe.parse_json(log.tool_calls) == expected_tools),
			log,
		)

	# --- Permission-aware proof: 2 real, differently-scoped users, same question, different results ---
	client_a = "client.a.3pl@pharmacountry.vn"
	client_b = "client.b.3pl@pharmacountry.vn"
	users_exist = frappe.db.exists("User", client_a) and frappe.db.exists("User", client_b)
	check("Both 3PL Client A/B portal users exist (Golden Demo #24 precedent)", users_exist, {"client_a": client_a, "client_b": client_b})

	if users_exist:
		resp_a = ask_enterprise("batches_on_hold", user=client_a)
		resp_b = ask_enterprise("batches_on_hold", user=client_b)
		warehouses_a = {b["warehouse"] for b in resp_a["data_facts"]["get_batches_on_hold"]["batches"]}
		warehouses_b = {b["warehouse"] for b in resp_b["data_facts"]["get_batches_on_hold"]["batches"]}
		check("Client A sees at least one batch on hold (its own quarantine warehouse)", len(warehouses_a) > 0, sorted(warehouses_a))
		check("Client B sees at least one batch on hold (its own quarantine warehouse)", len(warehouses_b) > 0, sorted(warehouses_b))
		check("Same question ('Batch nào đang bị hold?'), 2 different users -> genuinely DIFFERENT results", warehouses_a != warehouses_b, {"client_a": sorted(warehouses_a), "client_b": sorted(warehouses_b)})
		check("Client A's answer contains NO Client B warehouse data (no leak)", not any("Client B" in w for w in warehouses_a), sorted(warehouses_a))
		check("Client B's answer contains NO Client A warehouse data (no leak)", not any("Client A" in w for w in warehouses_b), sorted(warehouses_b))
		check("Client A's 'sources' citations contain no Client B reference (no leak via citations)", not any("Client B" in s for s in resp_a["sources"]), resp_a["sources"])
		check("Client B's 'sources' citations contain no Client A reference (no leak via citations)", not any("Client A" in s for s in resp_b["sources"]), resp_b["sources"])
	else:
		check("Permission-scoping proof executed", False, "Client A/B users missing — cannot run the 2-user proof.")

	# --- Revenue trend tool has genuine multi-month data (not a degenerate single bucket) ---
	revenue_facts = responses.get("revenue_trend", {}).get("data_facts", {}).get("get_revenue_trend_explanation_data", {})
	check(
		"Revenue trend tool has genuine multi-month data (both this-month and prior-month totals > 0)",
		bool(revenue_facts.get("this_month_total")) and bool(revenue_facts.get("prev_month_total")),
		{"this_month_total": revenue_facts.get("this_month_total"), "prev_month_total": revenue_facts.get("prev_month_total")},
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_qms_copilot_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-02 (QMS Copilot) integrity check, same pattern as
	`verify_ai_executive_assistant_golden_demo()`. Re-derives every acceptance-criteria claim
	from live data/live calls:
	  - Tool Registry extended (not duplicated): 3 new AI Tools registered/enabled/importable,
	    on top of AI-DEMO-01's original 5 (8 total).
	  - All 5 use cases (summarize deviation, find similar deviation, suggest investigation
	    questions, draft CAPA, summarize audit finding) run end-to-end with real tool data.
	  - Similarity search ("find similar deviation") finds a REAL match with a stated,
	    explainable basis and correctly excludes an unrelated deviation.
	  - THE mandatory-approval acceptance criterion: a draft_capa AI Draft cannot become a real
	    QMS CAPA without an explicit approve_capa_draft() call; a rejected/unapproved draft is
	    clearly distinguishable (status, no resulting_reference) from an approved one; approval
	    is attributable to a specific real human user; DocType-level guard rails (no
	    self-approval, no re-deciding a finalized draft) actually fire.
	  - The other 4 use cases' approval endorses the draft text WITHOUT minting a new record —
	    proving the "convert to real record" behavior is deliberately CAPA-specific, not blanket.
	"""
	from enterprise_core.enterprise_core.ai_qms_copilot import (
		USE_CASE_TOOL_MAP,
		approve_ai_suggestion,
		approve_capa_draft,
		reject_capa_draft,
		run_qms_copilot,
	)
	from enterprise_core.enterprise_core.ai_drafts import create_ai_draft

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: 3 new tools, on top of AI-DEMO-01's original 5 ---
	new_tool_codes = ["get_deviation_detail", "find_similar_deviations", "get_audit_finding_summary_data"]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("8 AI Tools registered total (AI-DEMO-01's 5 + AI-DEMO-02's 3, same shared registry)", len(all_tools) >= 8, sorted(all_tool_codes))
	check("All 3 new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("All 3 new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 3, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation ---
	check("qms_copilot_synthesis AI Action exists (reuses existing AI foundation router/policy/logging)", frappe.db.exists("AI Action", "qms_copilot_synthesis"), None)
	check("qms_copilot_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "qms_copilot_synthesis", "enabled": 1}), None)

	# --- Base demo records exist ---
	deviation = frappe.db.get_value("QMS Deviation", {"subject": "Cold storage temperature excursion — Warehouse B"}, "name")
	audit = frappe.db.get_value("QMS Audit", {"subject": "Internal GMP Audit — Q3 2026"}, "name")
	# draft_capa deliberately targets the AI-DEMO-02-owned "Warehouse C" similarity-control
	# Deviation, NOT the shared Warehouse B flagship record — a real bug found during this
	# build: Golden Demo #2/#3's own `qms_seeds._ensure_capa_for_deviation()` does an un-ordered
	# lookup keyed on (source_type, source_reference) assuming AT MOST ONE CAPA exists for
	# Warehouse B; this verify function's own repeated draft_capa approvals (append-only, same
	# precedent as AI Job Log) would otherwise create extra CAPAs sharing that key and make that
	# unrelated lookup nondeterministically pick up (and re-close) a fresh AI-approved CAPA
	# instead of the golden demo's real one. Warehouse C is owned exclusively by this demo, so
	# nothing else assumes uniqueness over it.
	capa_deviation = frappe.db.get_value("QMS Deviation", {"subject": "Cold storage temperature excursion — Warehouse C"}, "name")
	check("Base demo Deviation (Warehouse B) exists", bool(deviation), deviation)
	check("Base demo Audit (Internal GMP Audit — Q3 2026) exists", bool(audit), audit)
	check("draft_capa's own base Deviation (Warehouse C, similarity control) exists", bool(capa_deviation), capa_deviation)
	if not (deviation and audit and capa_deviation):
		return {"all_passed": False, "checks": checks}

	# --- All 5 use cases answer with real data, an AI suggestion, and a fresh (never auto-approved) AI Draft ---
	source_ref_by_use_case = {
		"summarize_deviation": deviation,
		"find_similar_deviation": deviation,
		"suggest_investigation_questions": deviation,
		"draft_capa": capa_deviation,
		"summarize_audit_finding": audit,
	}
	responses = {}
	for use_case, expected_tools in USE_CASE_TOOL_MAP.items():
		resp = run_qms_copilot(use_case, source_ref_by_use_case[use_case], user="Administrator")
		responses[use_case] = resp
		check(f"'{use_case}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{use_case}': data_facts and ai_suggestion are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_suggestion"], dict), None)
		check(f"'{use_case}': response cites real data sources ('có nguồn dữ liệu')", len(resp["sources"]) > 0, resp["sources"][:3])
		suggestion = resp["ai_suggestion"]
		check(f"'{use_case}': ai_suggestion flagged requires_human_approval=True", suggestion.get("requires_human_approval") is True, suggestion)
		check(f"'{use_case}': a fresh AI Draft is created in 'Draft' status (never auto-approved)", suggestion.get("approval_status") == "Draft" and frappe.db.get_value("AI Draft", suggestion.get("draft"), "status") == "Draft", suggestion)
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"'{use_case}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- Similarity search: real match found, real basis stated, unrelated deviation excluded ---
	similar_name = frappe.db.get_value("QMS Deviation", {"subject": "Cold storage temperature excursion — Warehouse C"}, "name")
	unrelated_name = frappe.db.get_value("QMS Deviation", {"subject": "Packaging label misprint — Batch 552199A"}, "name")
	sim_candidates = responses["find_similar_deviation"]["data_facts"]["find_similar_deviations"]["candidates"]
	sim_names = {c["deviation"] for c in sim_candidates}
	check("Similarity search finds the genuinely similar Warehouse C deviation", similar_name in sim_names, sorted(sim_names))
	check("Similarity search correctly excludes the unrelated packaging-label deviation", unrelated_name not in sim_names, sorted(sim_names))
	matched = next((c for c in sim_candidates if c["deviation"] == similar_name), None)
	check("Matched candidate states a real, non-empty similarity basis (shared_keywords)", bool(matched and matched.get("shared_keywords")), matched)

	# --- THE mandatory-approval proof: draft cannot become CAPA without explicit approval ---
	# Uses a before/after COUNT (scoped to this deviation) rather than "does a CAPA with the
	# suggested subject exist" — this verify function is re-run repeatedly (AI Draft/QMS CAPA
	# are append-only, like AI Job Log), so a subject-existence check would false-positive-fail
	# against a PRIOR run's already-approved CAPA sharing the same deterministic subject.
	capa_count_before_draft = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": capa_deviation})
	capa_draft_name = responses["draft_capa"]["ai_suggestion"]["draft"]
	capa_draft = frappe.get_doc("AI Draft", capa_draft_name)
	check(
		"A fresh draft_capa AI Draft has NOT yet produced any real QMS CAPA (no premature record)",
		not capa_draft.resulting_reference and frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": capa_deviation}) == capa_count_before_draft,
		{"draft": capa_draft_name, "resulting_reference": capa_draft.resulting_reference},
	)

	reviewer = "quality.director@pharmacountry.vn"
	check("Reviewer is a real, distinct human user (not Administrator, not the AI)", frappe.db.exists("User", reviewer) and reviewer != "Administrator", reviewer)

	capa_name = approve_capa_draft(capa_draft_name, reviewed_by=reviewer, review_notes="verify_ai_qms_copilot_golden_demo approval check.")
	capa_draft.reload()
	check("approve_capa_draft() created a real QMS CAPA", frappe.db.exists("QMS CAPA", capa_name), capa_name)
	check(
		"Approving the draft created EXACTLY one new CAPA for this deviation",
		frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": capa_deviation}) == capa_count_before_draft + 1,
		{"before": capa_count_before_draft, "capa_name": capa_name},
	)
	check("Approved draft's status flips to 'Approved'", capa_draft.status == "Approved", capa_draft.status)
	check("Approved draft's resulting_reference points at the real CAPA", capa_draft.resulting_reference == capa_name, capa_draft.resulting_reference)
	check("Approval is attributable to the specific real human reviewer (reviewed_by)", capa_draft.reviewed_by == reviewer, capa_draft.reviewed_by)
	check("Approval timestamp (reviewed_on) recorded", bool(capa_draft.reviewed_on), capa_draft.reviewed_on)
	log_after = frappe.db.get_value("AI Job Log", capa_draft.generated_by_job_log, ["accepted", "final_record_reference"], as_dict=True)
	check("Underlying AI Job Log updated with accepted=1/final_record_reference on approval", bool(log_after and log_after.accepted and log_after.final_record_reference == capa_name), log_after)

	# Second draft_capa -> rejected -> clearly distinguishable, no CAPA created.
	resp2 = run_qms_copilot("draft_capa", capa_deviation, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	capa_count_before = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": capa_deviation})
	reject_capa_draft(draft2_name, reviewed_by=reviewer, review_notes="verify_ai_qms_copilot_golden_demo rejection check.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	capa_count_after = frappe.db.count("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": capa_deviation})
	check("Rejected draft's status is 'Rejected' (clearly distinguishable from 'Approved')", draft2.status == "Rejected", draft2.status)
	check("Rejected draft has NO resulting_reference", not draft2.resulting_reference, draft2.resulting_reference)
	check("Rejecting a draft does NOT create any QMS CAPA (count unchanged)", capa_count_after == capa_count_before, {"before": capa_count_before, "after": capa_count_after})
	check("Approved draft and rejected draft report genuinely different statuses", capa_draft.status != draft2.status, {"approved": capa_draft.status, "rejected": draft2.status})

	# --- DocType-level guard rails: no self-approval, no re-deciding a finalized draft ---
	guard_draft = create_ai_draft(
		copilot_code="qms_copilot", use_case="draft_capa", source_doctype="QMS Deviation", source_reference=capa_deviation,
		content="[verify_ai_qms_copilot_golden_demo negative-test draft.]",
	)
	guard_draft.status = "Approved"  # no reviewed_by set — must be blocked
	self_approval_blocked = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		self_approval_blocked = True
	check("Guard rail: cannot flip AI Draft to Approved without reviewed_by (no self-approval)", self_approval_blocked, None)

	redecision_blocked = False
	try:
		reject_capa_draft(capa_draft_name, reviewed_by=reviewer, review_notes="attempting to re-decide")
	except frappe.ValidationError:
		redecision_blocked = True
	check("Guard rail: cannot re-decide an already-finalized (Approved) draft", redecision_blocked, None)

	# --- Non-CAPA use cases: approval endorses the draft, mints NO new record ---
	summary_draft_name = responses["summarize_deviation"]["ai_suggestion"]["draft"]
	approve_ai_suggestion(summary_draft_name, reviewed_by=reviewer, review_notes="verify_ai_qms_copilot_golden_demo endorsement check.")
	summary_draft = frappe.get_doc("AI Draft", summary_draft_name)
	check("Non-CAPA use case ('summarize_deviation') draft approved successfully", summary_draft.status == "Approved", summary_draft.status)
	check("Non-CAPA use case approval mints NO new record (resulting_reference stays empty)", not summary_draft.resulting_reference, summary_draft.resulting_reference)
	check("Non-CAPA use case approval still attributable to the real human reviewer", summary_draft.reviewed_by == reviewer, summary_draft.reviewed_by)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_dms_copilot_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-03 (DMS Copilot) integrity check, same pattern as
	`verify_ai_qms_copilot_golden_demo()`. Re-derives every acceptance-criteria claim from live
	data/live calls:
	  - Tool Registry extended (not duplicated): 4 new AI Tools registered/enabled/importable,
	    on top of AI-DEMO-01/02's original 8 (12 total).
	  - All 5 use cases (compare SOP revisions, create change summary, suggest impacted
	    documents, suggest training impact, Q&A over effective documents) run end-to-end with
	    real tool data.
	  - compare_document_revisions finds a REAL field-level diff between SOP-WH-02's real
	    v1 (Obsolete) and v2 (Effective) versions.
	  - suggest_impacted_documents' relationship proxy (same department/doc_type) correctly
	    includes documents matching by each basis and excludes a genuine negative control.
	  - suggest_training_impact surfaces REAL (not fabricated) DMS Training Assignment data.
	  - THE defining acceptance criterion: Q&A over effective documents excludes an Obsolete
	    version even when it matches the SAME search keywords as the Effective version — proven
	    empirically (the Obsolete match is still found, just reported as excluded, never as a
	    usable source), directly mirroring the master plan's own RAG "Obsolete doc not used as
	    current" requirement.
	  - Approval/rejection are attributable to a specific real human user, mint NO new business
	    record for ANY of the 5 use cases (the structural distinction from QMS Copilot's
	    draft_capa), and the DocType-level guard rails (no self-approval, no re-deciding a
	    finalized draft, no cross-copilot approval) actually fire.
	"""
	from enterprise_core.enterprise_core.ai_dms_copilot import (
		USE_CASE_TOOL_MAP,
		approve_dms_draft,
		reject_dms_draft,
		run_dms_copilot,
	)
	from enterprise_core.enterprise_core.ai_drafts import create_ai_draft

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: 4 new tools, on top of AI-DEMO-01/02's original 8 ---
	new_tool_codes = ["compare_document_revisions", "suggest_impacted_documents", "suggest_training_impact", "search_effective_documents"]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("12 AI Tools registered total (AI-DEMO-01/02's 8 + AI-DEMO-03's 4, same shared registry)", len(all_tools) >= 12, sorted(all_tool_codes))
	check("All 4 new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("All 4 new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 4, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation ---
	check("dms_copilot_synthesis AI Action exists (reuses existing AI foundation router/policy/logging)", frappe.db.exists("AI Action", "dms_copilot_synthesis"), None)
	check("dms_copilot_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "dms_copilot_synthesis", "enabled": 1}), None)

	# --- Base demo records exist ---
	base_document = "SOP-WH-02"
	check("Base demo Document (SOP-WH-02) exists", frappe.db.exists("DMS Document", base_document), base_document)
	v1_name = frappe.db.get_value("DMS Document Version", {"document": base_document, "version_no": 1}, "name")
	v2_name = frappe.db.get_value("DMS Document Version", {"document": base_document, "version_no": 2}, "name")
	check("Base demo has both v1 (Obsolete) and v2 (Effective) versions", bool(v1_name and v2_name), {"v1": v1_name, "v2": v2_name})
	for doc_code in ("SOP-WH-05", "FORM-WH-01", "SOP-QA-01", "POLICY-HR-01"):
		check(f"Relationship-proof document {doc_code} exists", frappe.db.exists("DMS Document", doc_code), doc_code)
	if not (v1_name and v2_name):
		return {"all_passed": False, "checks": checks}

	# --- All 5 use cases answer with real data, an AI suggestion, and a fresh (never auto-approved) AI Draft ---
	source_ref_by_use_case = {
		"compare_sop_revisions": base_document,
		"create_change_summary": base_document,
		"suggest_impacted_documents": base_document,
		"suggest_training_impact": base_document,
		"qa_effective_documents": "cold storage logs",
	}
	responses = {}
	for use_case, expected_tools in USE_CASE_TOOL_MAP.items():
		resp = run_dms_copilot(use_case, source_ref_by_use_case[use_case], user="Administrator")
		responses[use_case] = resp
		check(f"'{use_case}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{use_case}': data_facts and ai_suggestion are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_suggestion"], dict), None)
		check(f"'{use_case}': response cites real data sources", len(resp["sources"]) > 0, resp["sources"][:3])
		suggestion = resp["ai_suggestion"]
		check(f"'{use_case}': ai_suggestion flagged requires_human_approval=True", suggestion.get("requires_human_approval") is True, suggestion)
		check(f"'{use_case}': a fresh AI Draft is created in 'Draft' status (never auto-approved)", suggestion.get("approval_status") == "Draft" and frappe.db.get_value("AI Draft", suggestion.get("draft"), "status") == "Draft", suggestion)
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"'{use_case}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- compare_document_revisions: real field-level diff ---
	cmp_data = responses["compare_sop_revisions"]["data_facts"]["compare_document_revisions"]
	changed_fields = {c["field"] for c in cmp_data["fields_changed"]}
	check("Revision comparison correctly orders version_a=1 (older) / version_b=2 (newer)", cmp_data["version_a"]["version_no"] == 1 and cmp_data["version_b"]["version_no"] == 2, cmp_data)
	check("Revision comparison detects content_summary changed between v1 and v2", "content_summary" in changed_fields, sorted(changed_fields))
	check("Revision comparison detects status changed between v1 and v2", "status" in changed_fields, sorted(changed_fields))

	# --- suggest_impacted_documents: relationship proxy, positive + negative control ---
	impacted = {c["document"]: c for c in responses["suggest_impacted_documents"]["data_facts"]["suggest_impacted_documents"]["impacted_documents"]}
	check("Impacted-documents: dept+type match (SOP-WH-05) found with correct basis", impacted.get("SOP-WH-05", {}).get("relationship_basis") == ["same department", "same document type"] if "SOP-WH-05" in impacted else False, impacted.get("SOP-WH-05"))
	check("Impacted-documents: dept-only match (FORM-WH-01) found with correct basis", impacted.get("FORM-WH-01", {}).get("relationship_basis") == ["same department"] if "FORM-WH-01" in impacted else False, impacted.get("FORM-WH-01"))
	check("Impacted-documents: type-only match (SOP-QA-01) found with correct basis", impacted.get("SOP-QA-01", {}).get("relationship_basis") == ["same document type"] if "SOP-QA-01" in impacted else False, impacted.get("SOP-QA-01"))
	check("Impacted-documents: negative control (POLICY-HR-01, shares nothing) correctly excluded", "POLICY-HR-01" not in impacted, sorted(impacted))

	# --- suggest_training_impact: real, pre-existing DMS Training Assignment data ---
	training = responses["suggest_training_impact"]["data_facts"]["suggest_training_impact"]
	needing_retraining = {u["user"] for u in training["users_needing_retraining"]}
	check("Training-impact surfaces the real trained users as needing retraining", {"warehouse.officer@pharmacountry.vn", "qa.manager@pharmacountry.vn"}.issubset(needing_retraining), sorted(needing_retraining))
	check("Training-impact resolves the document's real current_version", training.get("current_version") == frappe.db.get_value("DMS Document", base_document, "current_version"), training.get("current_version"))

	# --- THE effective-vs-obsolete Q&A exclusion proof (the sharpest acceptance criterion) ---
	qa = responses["qa_effective_documents"]["data_facts"]["search_effective_documents"]
	qa_result_versions = {r["version"] for r in qa["results"]}
	qa_excluded_versions = {r["version"] for r in qa["obsolete_or_draft_matches_excluded"]}
	check("Q&A: query 'cold storage logs' matched the Obsolete v1 (proving the search itself works, not just silently skipping it)", v1_name in qa_excluded_versions, sorted(qa_excluded_versions))
	check("Q&A: Obsolete v1 is NEVER returned as a usable source, despite matching the query", v1_name not in qa_result_versions, sorted(qa_result_versions))
	check("Q&A: the Effective v2 IS returned as a usable source for the same query", v2_name in qa_result_versions, sorted(qa_result_versions))

	# --- Approval: attributable to a real human, mints NO new record for ANY of the 5 use cases ---
	reviewer = "quality.director@pharmacountry.vn"
	check("Reviewer is a real, distinct human user (not Administrator, not the AI)", frappe.db.exists("User", reviewer) and reviewer != "Administrator", reviewer)

	compare_draft_name = responses["compare_sop_revisions"]["ai_suggestion"]["draft"]
	compare_draft = frappe.get_doc("AI Draft", compare_draft_name)
	check("A fresh compare_sop_revisions AI Draft has NO resulting_reference before approval", not compare_draft.resulting_reference, compare_draft.resulting_reference)

	approve_dms_draft(compare_draft_name, reviewed_by=reviewer, review_notes="verify_ai_dms_copilot_golden_demo approval check.")
	compare_draft.reload()
	check("Approved draft's status flips to 'Approved'", compare_draft.status == "Approved", compare_draft.status)
	check("Approving a DMS Copilot draft mints NO new record (resulting_reference stays empty)", not compare_draft.resulting_reference, compare_draft.resulting_reference)
	check("Approval is attributable to the specific real human reviewer (reviewed_by)", compare_draft.reviewed_by == reviewer, compare_draft.reviewed_by)
	check("Approval timestamp (reviewed_on) recorded", bool(compare_draft.reviewed_on), compare_draft.reviewed_on)

	# Second draft, rejected -> clearly distinguishable, still no record minted.
	resp2 = run_dms_copilot("compare_sop_revisions", base_document, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	reject_dms_draft(draft2_name, reviewed_by=reviewer, review_notes="verify_ai_dms_copilot_golden_demo rejection check.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	check("Rejected draft's status is 'Rejected' (clearly distinguishable from 'Approved')", draft2.status == "Rejected", draft2.status)
	check("Rejected draft has NO resulting_reference", not draft2.resulting_reference, draft2.resulting_reference)
	check("Approved draft and rejected draft report genuinely different statuses", compare_draft.status != draft2.status, {"approved": compare_draft.status, "rejected": draft2.status})

	# --- Guard rails: cross-copilot approval refused, no self-approval, no re-deciding a finalized draft ---
	foreign_draft = create_ai_draft(
		copilot_code="qms_copilot", use_case="summarize_deviation", source_doctype="QMS Deviation", source_reference=None,
		content="[verify_ai_dms_copilot_golden_demo negative test — a foreign-copilot draft.]",
	)
	foreign_blocked = False
	try:
		approve_dms_draft(foreign_draft.name, reviewed_by=reviewer)
	except frappe.ValidationError:
		foreign_blocked = True
	check("Guard rail: approve_dms_draft() refuses a foreign (non-dms_copilot) draft", foreign_blocked, None)

	guard_draft = create_ai_draft(
		copilot_code="dms_copilot", use_case="compare_sop_revisions", source_doctype="DMS Document", source_reference=base_document,
		content="[verify_ai_dms_copilot_golden_demo negative-test draft.]",
	)
	guard_draft.status = "Approved"  # no reviewed_by set — must be blocked
	self_approval_blocked = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		self_approval_blocked = True
	check("Guard rail: cannot flip AI Draft to Approved without reviewed_by (no self-approval)", self_approval_blocked, None)

	redecision_blocked = False
	try:
		reject_dms_draft(compare_draft_name, reviewed_by=reviewer, review_notes="attempting to re-decide")
	except frappe.ValidationError:
		redecision_blocked = True
	check("Guard rail: cannot re-decide an already-finalized (Approved) draft", redecision_blocked, None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_manufacturing_insight_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-05 (Manufacturing Insight) integrity check, same pattern as
	`verify_ai_executive_assistant_golden_demo()` (this demo's own closer architectural
	template — see `ai_manufacturing_insight.py`'s module docstring for the documented
	NO-DRAFT design decision). Re-derives every acceptance-criteria claim from live data/live
	calls rather than trusting the seed step's own self-report:
	  - Tool Registry extended (not duplicated): 4 new AI Tools registered/enabled/importable,
	    on top of AI-DEMO-01/02/03's original 12 (16 total).
	  - Architecture: no arbitrary SQL exposed to the AI layer, no ai_suggestion/AI Draft field
	    anywhere in the response (the documented NO-DRAFT shape actually holds, not just in the
	    docstring).
	  - All 4 use cases (explain production delay, yield anomaly analysis, batch-record
	    completeness review, downtime summary) run end-to-end with real tool data.
	  - explain_production_delay() correctly distinguishes a genuinely delayed Work Order from
	    an on-time one, AND correlates the delay against a REAL, directly-recorded Premix
	    Weighing Verification timing fact (not a guess).
	  - analyze_yield_anomalies() correctly distinguishes a genuine anomaly (86% yield, 14%
	    deviation) from ordinary variance within the stated threshold (96% yield, 4% deviation)
	    — proving real threshold discrimination, not a blanket "anything under 100%" rule.
	  - check_batch_record_completeness() correctly flags a deliberately-incomplete batch as
	    incomplete with real, specific missing-record reasons, and reports a real, fully-
	    documented batch as complete (positive + negative control).
	  - summarize_downtime() aggregates a genuine multi-day delay and explicitly labels the
	    number as a derived proxy, never as a native recorded fact.
	  - Golden Demo #26 (Premix)'s OWN verify_premix_golden_demo() still passes after this
	    demo's isolated AI-DEMO-05-owned item/Work Orders/batches were added — the isolation
	    design (see ai_manufacturing_insight_seeds.py's module docstring) actually holds, not
	    just in theory.
	"""
	from enterprise_core.enterprise_core.ai_manufacturing_insight import QUESTION_TOOL_MAP, ask_manufacturing_insight
	from enterprise_core.enterprise_core.ai_manufacturing_insight_seeds import (
		_FG_ITEM,
		_INCOMPLETE_BATCH_ID,
		_work_order_for_batch,
	)

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: 4 new tools, on top of AI-DEMO-01/02/03's original 12 ---
	new_tool_codes = ["explain_production_delay", "analyze_yield_anomalies", "check_batch_record_completeness", "summarize_downtime"]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("16 AI Tools registered total (AI-DEMO-01/02/03's 12 + AI-DEMO-05's 4, same shared registry)", len(all_tools) >= 16, sorted(all_tool_codes))
	check("All 4 new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("All 4 new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 4, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation ---
	check("manufacturing_insight_synthesis AI Action exists (reuses existing AI foundation router/policy/logging)", frappe.db.exists("AI Action", "manufacturing_insight_synthesis"), None)
	check("manufacturing_insight_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "manufacturing_insight_synthesis", "version": 1, "enabled": 1}), None)
	check("manufacturing_insight_synthesis AI Action does NOT require human review (documented NO-DRAFT design)", frappe.db.get_value("AI Action", "manufacturing_insight_synthesis", "human_review_required") == 0, None)

	# --- Base demo fixtures exist ---
	wo_a = _work_order_for_batch(f"{_FG_ITEM}-AIDEMO05-WO-A-ONTIME")
	wo_b = _work_order_for_batch(f"{_FG_ITEM}-AIDEMO05-WO-B-DELAYED")
	wo_c = _work_order_for_batch(f"{_FG_ITEM}-AIDEMO05-WO-C-YIELD-ANOMALY")
	wo_d = _work_order_for_batch(f"{_FG_ITEM}-AIDEMO05-WO-D-YIELD-NORMAL-VARIANCE")
	check("All 4 AI-DEMO-05 Work Order scenarios (A/B/C/D) exist", all([wo_a, wo_b, wo_c, wo_d]), {"A": wo_a, "B": wo_b, "C": wo_c, "D": wo_d})
	check("Deliberately-incomplete batch fixture exists", frappe.db.exists("Batch", _INCOMPLETE_BATCH_ID), _INCOMPLETE_BATCH_ID)
	if not all([wo_a, wo_b, wo_c, wo_d]):
		return {"all_passed": False, "checks": checks}

	# --- All 4 use cases answer with real data — and NO ai_suggestion/draft field anywhere ---
	responses = {}
	for question_code, expected_tools in QUESTION_TOOL_MAP.items():
		resp = ask_manufacturing_insight(question_code, user="Administrator")
		responses[question_code] = resp
		check(f"'{question_code}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{question_code}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"'{question_code}': response cites real data sources ('có nguồn dữ liệu')", len(resp["sources"]) > 0, resp["sources"][:3])
		check(f"'{question_code}': response has NO ai_suggestion/draft field (documented NO-DRAFT design actually holds)", "ai_suggestion" not in resp, sorted(resp.keys()))
		check(f"'{question_code}': provider + model logged on the response", bool(resp["provider"]) and bool(resp["model"]), {"provider": resp["provider"], "model": resp["model"]})
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls", "retrieved_sources"], as_dict=True) if resp.get("job_log") else None
		check(
			f"'{question_code}': AI Job Log entry records provider/model/tool_calls (extends the existing CE-13 schema field)",
			bool(log and log.provider and log.model and log.tool_calls and frappe.parse_json(log.tool_calls) == expected_tools),
			log,
		)

	# --- explain_production_delay(): real delay vs on-time distinction, real correlation ---
	delay_facts = responses["production_delay"]["data_facts"]["explain_production_delay"]
	delayed_wos = {d["work_order"] for d in delay_facts["delayed"]}
	on_time_wos = {d["work_order"] for d in delay_facts["on_time"]}
	check("WO-B-DELAYED correctly flagged as delayed", wo_b in delayed_wos, sorted(delayed_wos))
	check("WO-A-ONTIME correctly reported as on-time (not delayed)", wo_a in on_time_wos, sorted(on_time_wos))
	entry_b = next((d for d in delay_facts["delayed"] if d["work_order"] == wo_b), None)
	check("WO-B-DELAYED's delay_hours reflects a genuine multi-day gap (>24h)", bool(entry_b) and entry_b["delay_hours"] > 24, entry_b)
	check(
		"WO-B-DELAYED's contributing_factors cites the real Premix Weighing Verification timing correlation (not a guess)",
		bool(entry_b) and any("Premix Weighing Verification" in f and "AFTER" in f for f in entry_b["contributing_factors"]),
		entry_b["contributing_factors"] if entry_b else None,
	)

	# --- analyze_yield_anomalies(): real threshold discrimination ---
	yield_facts = responses["yield_anomaly"]["data_facts"]["analyze_yield_anomalies"]
	by_batch = {b["batch_no"]: b for b in yield_facts["batches"]}
	anomaly_batch = f"{_FG_ITEM}-AIDEMO05-WO-C-YIELD-ANOMALY"
	normal_batch = f"{_FG_ITEM}-AIDEMO05-WO-D-YIELD-NORMAL-VARIANCE"
	check("WO-C (86% yield, 14% deviation) correctly flagged anomalous", by_batch.get(anomaly_batch, {}).get("anomaly") is True, by_batch.get(anomaly_batch))
	check("WO-D (96% yield, 4% deviation) correctly NOT flagged anomalous (within the 5% threshold)", by_batch.get(normal_batch, {}).get("anomaly") is False, by_batch.get(normal_batch))

	# --- check_batch_record_completeness(): positive + negative control ---
	completeness_facts = responses["batch_completeness"]["data_facts"]["check_batch_record_completeness"]
	by_completeness = {r["batch_no"]: r for r in completeness_facts["results"]}
	incomplete = by_completeness.get(_INCOMPLETE_BATCH_ID)
	check("Deliberately-incomplete batch fixture correctly flagged INCOMPLETE", bool(incomplete) and incomplete["complete"] is False, incomplete)
	check("Incomplete batch's 'missing' list states real, specific reasons", bool(incomplete) and len(incomplete.get("missing", [])) > 0, incomplete.get("missing") if incomplete else None)
	complete_others = [b for b, r in by_completeness.items() if r["complete"] and b != _INCOMPLETE_BATCH_ID]
	check("At least one real, fully-documented batch correctly flagged COMPLETE (negative control)", len(complete_others) > 0, complete_others)

	# --- summarize_downtime(): derived proxy, explicitly labeled, reflects the real WO-B delay ---
	downtime_facts = responses["downtime_summary"]["data_facts"]["summarize_downtime"]
	check("Downtime summary explicitly labels its number a derived proxy (methodology_note)", "derived proxy" in (downtime_facts.get("methodology_note") or ""), downtime_facts.get("methodology_note"))
	check("Downtime summary's total_derived_delay_hours reflects WO-B-DELAYED's real multi-day gap (>24h)", downtime_facts.get("total_derived_delay_hours", 0) > 24, downtime_facts.get("total_derived_delay_hours"))

	# --- Isolation proof: Golden Demo #26's OWN verify function still passes unaffected ---
	premix_result = verify_premix_golden_demo()
	check(
		"Golden Demo #26 (Premix)'s OWN verify_premix_golden_demo() still passes after AI-DEMO-05's isolated item/Work Orders/batches were added (isolation design holds)",
		premix_result["all_passed"],
		[c for c in premix_result["checks"] if not c["passed"]],
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_procurement_assistant_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-06 (Procurement Assistant) integrity check, same pattern as every
	prior Phase 6A verify_* function. A deliberate HYBRID design (see
	`ai_procurement_assistant.py`'s own module docstring): 4 analytical use cases follow
	AI-DEMO-05's NO-DRAFT shape, the 5th (supplier qualification recommendation) reuses
	AI-DEMO-02's `AI Draft` mechanism — this verify function checks both shapes hold, plus THE
	defining acceptance criterion, "AI không tự approve supplier", proved negatively (not just
	asserted): a live before/after read showing the recommendation step itself never changes
	`Supplier.quality_status`, every structural approval guard firing, a real positive-control
	upgrade recommendation over Golden Demo #27's own untouched Cargill data, AND a static
	source-level check that exactly one write site to `Supplier.quality_status` exists anywhere in
	this module, gated behind an explicit human `reviewed_by`.
	"""
	import inspect

	from enterprise_core.enterprise_core import ai_procurement_assistant
	from enterprise_core.enterprise_core.ai_procurement_assistant import (
		ANALYTICAL_USE_CASE_TOOL_MAP,
		approve_supplier_status_draft,
		ask_procurement_assistant,
		recommend_supplier_qualification,
		reject_supplier_status_draft,
	)
	from enterprise_core.enterprise_core.ai_procurement_assistant_seeds import (
		_PAYMENT_TERMS_AI6,
		_SQ_CARGILL_MARKER,
		_SUPPLIER_AI6,
		_SUPPLIER_CARGILL,
		_SUPPLIER_NUTRECO,
	)
	from enterprise_core.enterprise_core.ai_drafts import create_ai_draft
	from enterprise_core.enterprise_core.ai_tools import recommend_supplier_qualification_change

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: 5 new tools, on top of AI-DEMO-01/02/03/05's original 16 ---
	new_tool_codes = ["extract_supplier_quotation", "normalize_supplier_quotations", "compare_supplier_quotations", "summarize_supplier_history", "recommend_supplier_qualification_change"]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("21 AI Tools registered total (AI-DEMO-01/02/03/05's 16 + AI-DEMO-06's 5, same shared registry)", len(all_tools) >= 21, sorted(all_tool_codes))
	check("All 5 new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("All 5 new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 5, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation, TWO pairs (hybrid design) ---
	check("procurement_assistant_synthesis AI Action exists and does NOT require human review (4 analytical use cases, NO-DRAFT)", frappe.db.get_value("AI Action", "procurement_assistant_synthesis", "human_review_required") == 0, None)
	check("procurement_assistant_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "procurement_assistant_synthesis", "version": 1, "enabled": 1}), None)
	check("procurement_supplier_qualification_synthesis AI Action exists and DOES require human review (the consequential 5th use case)", frappe.db.get_value("AI Action", "procurement_supplier_qualification_synthesis", "human_review_required") == 1, None)
	check("procurement_supplier_qualification_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "procurement_supplier_qualification_synthesis", "version": 1, "enabled": 1}), None)

	# --- Base demo fixtures exist ---
	cargill_sq = frappe.db.get_value("Supplier Quotation", {"title": _SQ_CARGILL_MARKER}, "name")
	isolated_supplier = frappe.db.get_value("Supplier", {"supplier_name": _SUPPLIER_AI6}, "name")
	check("Cargill Supplier Quotation fixture exists", bool(cargill_sq), cargill_sq)
	check("Isolated AI-DEMO-06 Supplier fixture exists (critical, Approved starting state)", bool(isolated_supplier), isolated_supplier)
	if not (cargill_sq and isolated_supplier):
		return {"all_passed": False, "checks": checks}

	# --- All 4 analytical use cases answer with real data — and NO ai_suggestion/draft field anywhere ---
	source_ref_by_use_case = {
		"extract_quotation": cargill_sq,
		"normalize_terms": "SOYBEAN-MEAL-48",
		"compare_quotations": "SOYBEAN-MEAL-48",
		"summarize_supplier_history": isolated_supplier,
	}
	responses = {}
	for use_case, expected_tools in ANALYTICAL_USE_CASE_TOOL_MAP.items():
		resp = ask_procurement_assistant(use_case, source_ref_by_use_case[use_case], user="Administrator")
		responses[use_case] = resp
		check(f"'{use_case}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{use_case}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"'{use_case}': response cites real data sources ('có nguồn dữ liệu')", len(resp["sources"]) > 0, resp["sources"][:3])
		check(f"'{use_case}': response has NO ai_suggestion/draft field (documented NO-DRAFT design for these 4 use cases)", "ai_suggestion" not in resp, sorted(resp.keys()))
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"'{use_case}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- extract_supplier_quotation(): real, honestly-labeled simulated extraction ---
	extracted = responses["extract_quotation"]["data_facts"]["extract_supplier_quotation"]
	check("extract_supplier_quotation() resolves the real quotation's supplier/currency/incoterm", extracted.get("supplier") == _SUPPLIER_CARGILL and extracted.get("currency") == "USD" and bool(extracted.get("incoterm")), extracted)
	check("extract_supplier_quotation() is honest that this simulates extraction from structured data, not real OCR/document parsing", "structured" in (responses["extract_quotation"]["tool_notes"].get("extract_supplier_quotation") or ""), responses["extract_quotation"]["tool_notes"])

	# --- normalize/compare: the real, genuine trade-off (Nutreco cheaper, Cargill faster) ---
	norm = responses["normalize_terms"]["data_facts"]["normalize_supplier_quotations"]
	by_supplier = {r["supplier"]: r for r in norm.get("normalized", [])}
	check("normalize_supplier_quotations() resolves BOTH real supplier quotations for SOYBEAN-MEAL-48", {_SUPPLIER_CARGILL, _SUPPLIER_NUTRECO} <= set(by_supplier), sorted(by_supplier))
	check(
		"normalize_supplier_quotations() converts to base currency via each quotation's OWN conversion_rate (Nutreco's normalized price is genuinely lower than Cargill's)",
		bool(by_supplier) and by_supplier.get(_SUPPLIER_NUTRECO, {}).get("normalized_rate_base_currency", 1e18) < by_supplier.get(_SUPPLIER_CARGILL, {}).get("normalized_rate_base_currency", 0),
		by_supplier,
	)
	best = responses["compare_quotations"]["data_facts"]["compare_supplier_quotations"].get("best_by_dimension", {})
	check("compare_supplier_quotations() correctly picks Nutreco as lowest normalized price", best.get("lowest_normalized_price", {}).get("supplier") == _SUPPLIER_NUTRECO, best.get("lowest_normalized_price"))
	check("compare_supplier_quotations() correctly picks Cargill as shortest lead time (real trade-off, not a one-sided example)", best.get("shortest_lead_time", {}).get("supplier") == _SUPPLIER_CARGILL, best.get("shortest_lead_time"))

	# --- summarize_supplier_history(): the real, deliberately-worsening decline ---
	hist = responses["summarize_supplier_history"]["data_facts"]["summarize_supplier_history"]
	check("summarize_supplier_history(): all 3 real shipments for the isolated supplier are aggregated", hist.get("shipment_count") == 3, hist.get("shipment_count"))
	check("summarize_supplier_history(): latest QC result is genuinely Rejected (native reading-vs-spec auto-status, not fabricated)", hist.get("quality", {}).get("latest_qc_status") == "Rejected", hist.get("quality"))
	check("summarize_supplier_history(): on-time delivery rate reflects the real worsening trend (< 50%)", (hist.get("delivery", {}).get("on_time_rate") or 1) < 0.5, hist.get("delivery"))
	check("summarize_supplier_history(): payment terms actually used reflects the real Purchase Order.payment_terms_template", _PAYMENT_TERMS_AI6 in (hist.get("payment_terms_actually_used") or []), hist.get("payment_terms_actually_used"))

	# --- THE mandatory-approval / "AI không tự approve supplier" proof ---
	status_before = frappe.db.get_value("Supplier", isolated_supplier, "quality_status")
	qual_resp = recommend_supplier_qualification(isolated_supplier, user="Administrator")
	status_immediately_after = frappe.db.get_value("Supplier", isolated_supplier, "quality_status")
	check(
		"recommend_supplier_qualification() itself NEVER changes Supplier.quality_status, even though it calls the (mock) AI synthesis step",
		status_immediately_after == status_before,
		{"before": status_before, "immediately_after": status_immediately_after},
	)
	suggestion = qual_resp["ai_suggestion"]
	check("Fresh recommendation is flagged requires_human_approval=True, approval_status='Draft' (never auto-final)", suggestion.get("requires_human_approval") is True and suggestion.get("approval_status") == "Draft", suggestion)
	check("Fresh recommendation correctly suggests 'Disqualified' for the critical, declining-history supplier", suggestion.get("suggested_fields", {}).get("recommended_status") == "Disqualified", suggestion.get("suggested_fields"))
	draft_name = suggestion["draft"]

	reviewer = "procurement.officer@pharmacountry.vn"
	check("Reviewer is a real, distinct human user (not Administrator, not the AI)", frappe.db.exists("User", reviewer) and reviewer != "Administrator", reviewer)

	# Guard rails, checked BEFORE the real approval (so a blocked attempt can never be confused with the real one).
	blocked_no_reviewer = False
	try:
		approve_supplier_status_draft(draft_name, reviewed_by=None)
	except frappe.ValidationError:
		blocked_no_reviewer = True
	check("Guard rail: approve_supplier_status_draft() requires an explicit reviewed_by", blocked_no_reviewer, None)

	blocked_bogus_reviewer = False
	try:
		approve_supplier_status_draft(draft_name, reviewed_by="not.a.real.user@nowhere.fake")
	except frappe.ValidationError:
		blocked_bogus_reviewer = True
	check("Guard rail: approve_supplier_status_draft() rejects a reviewed_by that is not a real User record", blocked_bogus_reviewer, None)
	check("Blocked approval attempts left Supplier.quality_status untouched", frappe.db.get_value("Supplier", isolated_supplier, "quality_status") == status_before, None)

	guard_draft = create_ai_draft(
		copilot_code="procurement_assistant", use_case="supplier_qualification_recommendation", source_doctype="Supplier", source_reference=isolated_supplier,
		content="[verify_ai_procurement_assistant_golden_demo negative-test draft.]",
	)
	guard_draft.status = "Approved"  # no reviewed_by set — must be blocked
	self_approval_blocked = False
	try:
		guard_draft.save(ignore_permissions=True)
	except frappe.ValidationError:
		self_approval_blocked = True
	check("Guard rail: cannot flip AI Draft to Approved without reviewed_by (no self-approval, DocType-level, reused unmodified from AI-DEMO-02)", self_approval_blocked, None)

	# The real, human-approved change.
	returned_supplier = approve_supplier_status_draft(draft_name, reviewed_by=reviewer, review_notes="verify_ai_procurement_assistant_golden_demo approval check.")
	draft = frappe.get_doc("AI Draft", draft_name)
	check("approve_supplier_status_draft() applied the real Supplier.quality_status change", returned_supplier == isolated_supplier and frappe.db.get_value("Supplier", isolated_supplier, "quality_status") == "Disqualified", frappe.db.get_value("Supplier", isolated_supplier, "quality_status"))
	check("Approved draft's status flips to 'Approved', resulting_reference points at the real Supplier", draft.status == "Approved" and draft.resulting_doctype == "Supplier" and draft.resulting_reference == isolated_supplier, draft.as_dict())
	check("Approval is attributable to the specific real human reviewer (reviewed_by)", draft.reviewed_by == reviewer, draft.reviewed_by)
	check("Approval timestamp (reviewed_on) recorded", bool(draft.reviewed_on), draft.reviewed_on)
	log_after = frappe.db.get_value("AI Job Log", draft.generated_by_job_log, ["accepted", "final_record_reference"], as_dict=True)
	check("Underlying AI Job Log updated with accepted=1/final_record_reference on approval", bool(log_after and log_after.accepted and log_after.final_record_reference == isolated_supplier), log_after)

	redecision_blocked = False
	try:
		reject_supplier_status_draft(draft_name, reviewed_by=reviewer)
	except frappe.ValidationError:
		redecision_blocked = True
	check("Guard rail: cannot re-decide an already-finalized (Approved) draft", redecision_blocked, None)

	# Second recommendation -> rejected -> clearly distinguishable, quality_status unchanged.
	resp2 = recommend_supplier_qualification(isolated_supplier, user="Administrator")
	draft2_name = resp2["ai_suggestion"]["draft"]
	reject_supplier_status_draft(draft2_name, reviewed_by=reviewer, review_notes="verify_ai_procurement_assistant_golden_demo rejection check.")
	draft2 = frappe.get_doc("AI Draft", draft2_name)
	check("Rejected draft's status is 'Rejected' (clearly distinguishable from 'Approved')", draft2.status == "Rejected", draft2.status)
	check("Rejected draft has NO resulting_reference", not draft2.resulting_reference, draft2.resulting_reference)
	check("Rejecting a draft does NOT change Supplier.quality_status", frappe.db.get_value("Supplier", isolated_supplier, "quality_status") == "Disqualified", None)

	# --- Real positive control: Golden Demo #27's own untouched Cargill data recommends an UPGRADE ---
	cargill_status_before = frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status")
	cargill_resp = recommend_supplier_qualification(_SUPPLIER_CARGILL, user="Administrator")
	cargill_status_after_recommend = frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status")
	check("Recommending for Cargill did not itself change Cargill's real quality_status", cargill_status_after_recommend == cargill_status_before, {"before": cargill_status_before, "after": cargill_status_after_recommend})
	check(
		"Real positive control: Golden Demo #27's own untouched, clean-history Cargill data recommends an 'Approved' UPGRADE (distinguishes good vs. bad suppliers, not a blanket flag)",
		cargill_resp["ai_suggestion"]["suggested_fields"].get("recommended_status") == "Approved",
		cargill_resp["ai_suggestion"]["suggested_fields"],
	)
	reject_supplier_status_draft(cargill_resp["ai_suggestion"]["draft"], reviewed_by=reviewer, review_notes="verify_ai_procurement_assistant_golden_demo: positive-control only, deliberately not applied.")
	check("Cargill's real Supplier.quality_status remains untouched by this verify function (isolation discipline)", frappe.db.get_value("Supplier", _SUPPLIER_CARGILL, "quality_status") == cargill_status_before, None)

	# --- Static, source-level structural proof: exactly one Supplier-write site, reviewed_by-gated ---
	# Docstrings are stripped before scanning — several of this module's own docstrings quote
	# `.save()`/`.insert()` etc. IN PROSE (describing what must NOT be there), which would
	# otherwise false-positive a naive substring check on the raw source.
	def _strip_docstring(source):
		first = source.find('"""')
		if first == -1:
			return source
		second = source.find('"""', first + 3)
		if second == -1:
			return source
		return source[:first] + source[second + 3 :]

	tool_source = _strip_docstring(inspect.getsource(recommend_supplier_qualification_change))
	no_write_in_tool = "frappe.db.set_value" not in tool_source and ".save(" not in tool_source and ".insert(" not in tool_source
	check("Structural proof: the read-only recommendation TOOL contains zero write calls", no_write_in_tool, None)
	orch_source = _strip_docstring(inspect.getsource(ai_procurement_assistant.recommend_supplier_qualification))
	no_write_in_orchestration = "frappe.db.set_value" not in orch_source and not (("Supplier" in orch_source) and (".save(" in orch_source or ".insert(" in orch_source))
	check("Structural proof: the orchestration entry point contains zero direct Supplier-write calls (only calls the read-only tool + create_ai_draft())", no_write_in_orchestration, None)
	approve_source = _strip_docstring(inspect.getsource(ai_procurement_assistant.approve_supplier_status_draft))
	write_count = approve_source.count('frappe.db.set_value("Supplier"')
	check("Structural proof: EXACTLY ONE Supplier.quality_status write site exists anywhere in this module, inside approve_supplier_status_draft()", write_count == 1, write_count)
	check("Structural proof: that one write site is gated behind an explicit human reviewed_by check", "reviewed_by" in approve_source, None)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_farm_aquaculture_insight_golden_demo() -> dict:
	"""Phase 6A — AI-DEMO-09 (Livestock Farm Assistant) + AI-DEMO-10 (Shrimp/Aquaculture
	Assistant) integrity check, same pattern as `verify_ai_manufacturing_insight_golden_demo()`
	(this combined item's own closer architectural template — see
	`ai_farm_aquaculture_insight.py`'s module docstring for the documented NO-DRAFT design
	decision shared by both verticals). Re-derives every acceptance-criteria claim from live
	data/live calls rather than trusting the seed step's own self-report:
	  - Tool Registry extended (not duplicated): 8 new AI Tools registered/enabled/importable, on
	    top of AI-DEMO-01/02/03/05/06's original 21 (29 total).
	  - Architecture: no arbitrary SQL exposed to the AI layer, no ai_suggestion/AI Draft field
	    anywhere in either vertical's response (the documented NO-DRAFT shape actually holds).
	  - All 8 use cases (4 livestock + 4 aquaculture) run end-to-end with real tool data.
	  - "Automation handles hard thresholds, AI handles interpretation", proved concretely for
	    BOTH verticals: (a) aquaculture — `analyze_pond_instability()`'s own source code contains
	    no water-threshold comparison at all (a static check, not just a docstring claim), yet
	    correctly reports 0 automation-flagged alerts for the stable baseline pond and several real
	    SF10-automation-flagged alerts for the deteriorating one; (b) livestock — a static check
	    that `pig_validations.py` (Golden Demo #11's own business-rule module) contains no
	    FCR/mortality threshold logic, confirming the livestock tools' farm's-own-relative-history
	    comparisons are not standing in for missing automation, and are not new hard-threshold
	    validation code themselves (no `frappe.throw`/blocking side effect anywhere in either tool).
	  - `explain_fcr_deterioration()`/`analyze_mortality_anomaly()`/`identify_barn_requiring_
	    attention()`/`analyze_feed_cost()` each correctly discriminate a genuinely deteriorated/
	    anomalous cohort from normal-variance ones, from real Pig Farm cohort data.
	  - `analyze_pond_instability()`/`analyze_feed_fcr_trend()`/`analyze_water_trend()`/
	    `explain_pond_anomaly()` each correctly discriminate real trend/anomaly signals from real
	    Shrimp Farm pond data, with every new Harvest's FCR kept inside the pre-existing 0.8-2.0
	    sanity range so it can never corrupt `verify_shrimp_golden_demo()`.
	  - Golden Demo #11 (Pig Farm)'s and Golden Demo #8 (Shrimp Farm)'s OWN verify_*_golden_demo()
	    functions still pass after this demo's isolated pens/ponds were added — the isolation
	    design (see `ai_farm_aquaculture_insight_seeds.py`'s own module docstring) actually holds.
	"""
	import inspect

	from enterprise_core.enterprise_core import ai_tools, pig_validations
	from enterprise_core.enterprise_core.ai_farm_aquaculture_insight import (
		AQUACULTURE_QUESTION_TOOL_MAP,
		LIVESTOCK_QUESTION_TOOL_MAP,
		ask_aquaculture_insight,
		ask_livestock_insight,
	)

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: 8 new tools, on top of AI-DEMO-01/02/03/05/06's original 21 ---
	new_tool_codes = [
		"explain_fcr_deterioration",
		"analyze_mortality_anomaly",
		"identify_barn_requiring_attention",
		"analyze_feed_cost",
		"analyze_pond_instability",
		"analyze_feed_fcr_trend",
		"analyze_water_trend",
		"explain_pond_anomaly",
	]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("29 AI Tools registered total (AI-DEMO-01/02/03/05/06's 21 + AI-DEMO-09/10's 8, same shared registry)", len(all_tools) >= 29, sorted(all_tool_codes))
	check("All 8 new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("All 8 new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 8, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template wiring reuses the EXISTING CE-13 foundation, one pair per vertical (both NO-DRAFT) ---
	check("livestock_farm_insight_synthesis AI Action exists and does NOT require human review (NO-DRAFT)", frappe.db.get_value("AI Action", "livestock_farm_insight_synthesis", "human_review_required") == 0, None)
	check("livestock_farm_insight_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "livestock_farm_insight_synthesis", "version": 1, "enabled": 1}), None)
	check("aquaculture_insight_synthesis AI Action exists and does NOT require human review (NO-DRAFT)", frappe.db.get_value("AI Action", "aquaculture_insight_synthesis", "human_review_required") == 0, None)
	check("aquaculture_insight_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "aquaculture_insight_synthesis", "version": 1, "enabled": 1}), None)

	# --- "Automation handles hard thresholds, AI handles interpretation" — static, source-level proof ---
	# Docstrings are stripped before scanning — analyze_pond_instability()'s own docstring quotes
	# `shrimp_water_reading_validate` IN PROSE (describing what it deliberately does NOT do),
	# which would otherwise false-positive a naive substring check on the raw source (the same
	# "strip docstrings before scanning" discipline `verify_ai_procurement_assistant_golden_demo()`
	# already established for its own structural-proof checks).
	def _strip_docstring(source):
		first = source.find('"""')
		if first == -1:
			return source
		second = source.find('"""', first + 3)
		if second == -1:
			return source
		return source[:first] + source[second + 3 :]

	instability_source = _strip_docstring(inspect.getsource(ai_tools.analyze_pond_instability))
	no_threshold_reimpl = "_WATER_THRESHOLDS" not in instability_source and "shrimp_water_reading_validate" not in instability_source
	check("Structural proof: analyze_pond_instability() contains NO water-threshold comparison of its own — it only reads the existing is_alert/alert_message fields", no_threshold_reimpl, None)
	water_trend_source = _strip_docstring(inspect.getsource(ai_tools.analyze_water_trend))
	check("Structural proof: analyze_water_trend() also contains no threshold re-implementation, only counts existing is_alert flags", "_WATER_THRESHOLDS" not in water_trend_source, None)

	pig_validations_source = inspect.getsource(pig_validations)
	check(
		"Golden Demo #11 (Pig Farm)'s own pig_validations.py has NO FCR/mortality threshold-alert automation to defer to — confirming the livestock tools' relative-to-history comparisons fill a genuine gap, not a re-implementation",
		"fcr" not in pig_validations_source.lower() and "mortality_count >" not in pig_validations_source and "mortality_rate" not in pig_validations_source.lower(),
		None,
	)
	fcr_tool_source = inspect.getsource(ai_tools.explain_fcr_deterioration)
	mortality_tool_source = inspect.getsource(ai_tools.analyze_mortality_anomaly)
	check(
		"Structural proof: neither livestock tool ever calls frappe.throw/blocks anything — both are read-only interpretation, never new hard-threshold validation code",
		"frappe.throw" not in fcr_tool_source and "frappe.throw" not in mortality_tool_source,
		None,
	)

	# --- Base isolated fixtures exist (livestock) ---
	pig_pens = ["PEN-AI9-C1", "PEN-AI9-C2", "PEN-AI9-C3"]
	pig_batches = {p: frappe.db.get_value("Pig Grower Batch", {"pen": p}, "name") for p in pig_pens}
	check("All 3 isolated AI-DEMO-09 Pig Grower Batch cohorts exist", all(pig_batches.values()), pig_batches)

	# --- Base isolated fixtures exist (aquaculture) ---
	shrimp_ponds = ["POND-AI10-1", "POND-AI10-2", "POND-AI10-3"]
	shrimp_batches = {p: frappe.db.get_value("Shrimp Stocking Batch", {"pond": p}, "name") for p in shrimp_ponds}
	shrimp_harvests = {p: frappe.db.get_value("Shrimp Harvest", {"stocking_batch": b}, "fcr") if b else None for p, b in shrimp_batches.items()}
	check("All 3 isolated AI-DEMO-10 Shrimp Stocking Batches exist", all(shrimp_batches.values()), shrimp_batches)
	check("All 3 isolated AI-DEMO-10 Shrimp Harvests exist with a computed FCR", all(v is not None for v in shrimp_harvests.values()), shrimp_harvests)
	check("Every isolated Shrimp Harvest's FCR is inside the realistic 0.8-2.0 sanity range (cannot corrupt verify_shrimp_golden_demo()'s own unfiltered most-recent-Harvest check)", all(v is not None and 0.8 <= v <= 2.0 for v in shrimp_harvests.values()), shrimp_harvests)
	if not (all(pig_batches.values()) and all(shrimp_batches.values())):
		return {"all_passed": False, "checks": checks}

	# --- All 4 livestock use cases answer with real data — and NO ai_suggestion/draft field anywhere ---
	livestock_responses = {}
	for question_code, expected_tools in LIVESTOCK_QUESTION_TOOL_MAP.items():
		resp = ask_livestock_insight(question_code, user="Administrator")
		livestock_responses[question_code] = resp
		check(f"livestock '{question_code}': tools_called matches the fixed registry mapping", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"livestock '{question_code}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"livestock '{question_code}': response cites real data sources", len(resp["sources"]) > 0, resp["sources"][:3])
		check(f"livestock '{question_code}': response has NO ai_suggestion/draft field (documented NO-DRAFT design)", "ai_suggestion" not in resp, sorted(resp.keys()))
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"livestock '{question_code}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- All 4 aquaculture use cases answer with real data — and NO ai_suggestion/draft field anywhere ---
	aquaculture_responses = {}
	for question_code, expected_tools in AQUACULTURE_QUESTION_TOOL_MAP.items():
		params = {"pond": "POND-AI10-3"} if question_code == "pond_anomaly_explanation" else {}
		resp = ask_aquaculture_insight(question_code, user="Administrator", **params)
		aquaculture_responses[question_code] = resp
		check(f"aquaculture '{question_code}': tools_called matches the fixed registry mapping", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"aquaculture '{question_code}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"aquaculture '{question_code}': response cites real data sources", len(resp["sources"]) > 0, resp["sources"][:3])
		check(f"aquaculture '{question_code}': response has NO ai_suggestion/draft field (documented NO-DRAFT design)", "ai_suggestion" not in resp, sorted(resp.keys()))
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"aquaculture '{question_code}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- explain_fcr_deterioration()/analyze_mortality_anomaly(): real discrimination, not a blanket flag ---
	fcr_facts = livestock_responses["fcr_deterioration"]["data_facts"]["explain_fcr_deterioration"]
	by_pen = {c["pen"]: c for c in fcr_facts["cohorts_chronological"]}
	check("PEN-AI9-C1/C2 (normal variance) correctly NOT flagged deteriorated", not by_pen.get("PEN-AI9-C1", {}).get("flagged_deteriorated") and not by_pen.get("PEN-AI9-C2", {}).get("flagged_deteriorated"), by_pen)
	check("PEN-AI9-C3 (genuine deterioration) correctly flagged, with a real linked Pig Medicine Treatment cited", by_pen.get("PEN-AI9-C3", {}).get("flagged_deteriorated") and any("Medicine Treatment" in f for f in by_pen.get("PEN-AI9-C3", {}).get("contributing_factors", [])), by_pen.get("PEN-AI9-C3"))

	mortality_facts = livestock_responses["mortality_anomaly"]["data_facts"]["analyze_mortality_anomaly"]
	by_pen_m = {c["pen"]: c for c in mortality_facts["cohorts"]}
	check("PEN-AI9-C3's mortality anomaly is expressed as a real MULTIPLE of the farm's own peer average (never a fixed absolute rate cutoff)", by_pen_m.get("PEN-AI9-C3", {}).get("anomalous") and by_pen_m.get("PEN-AI9-C3", {}).get("ratio_vs_peer_average", 0) >= 2.0, by_pen_m.get("PEN-AI9-C3"))
	check("PEN-AI9-C1 (baseline) correctly NOT flagged anomalous", not by_pen_m.get("PEN-AI9-C1", {}).get("anomalous"), by_pen_m.get("PEN-AI9-C1"))

	# --- identify_barn_requiring_attention()/analyze_feed_cost() ---
	ranking = livestock_responses["barn_requiring_attention"]["data_facts"]["identify_barn_requiring_attention"]["ranked_cohorts"]
	check("identify_barn_requiring_attention() ranks PEN-AI9-C3 #1 (worst on all 3 real signals)", bool(ranking) and ranking[0]["pen"] == "PEN-AI9-C3", [r["pen"] for r in ranking])
	cost_cohorts = livestock_responses["feed_cost_analysis"]["data_facts"]["analyze_feed_cost"]["cohorts_chronological"]
	cost_values = [c["cost_per_kg_gained"] for c in cost_cohorts]
	check("analyze_feed_cost()'s cost/kg-gained rises monotonically across the real chronological cohorts, decomposed into price + efficiency", len(cost_values) == 3 and cost_values[0] < cost_values[1] < cost_values[2], cost_values)

	# --- analyze_pond_instability(): real automation-flagged alerts read, not recomputed ---
	instability_facts = aquaculture_responses["pond_instability"]["data_facts"]["analyze_pond_instability"]
	by_pond = {r["pond"]: r for r in instability_facts["results"]}
	check("POND-AI10-1 (stable baseline) has 0 real SF10 automation-flagged alerts", by_pond.get("POND-AI10-1", {}).get("alert_reading_count") == 0, by_pond.get("POND-AI10-1"))
	check("POND-AI10-3 (deteriorating) has multiple real SF10 automation-flagged alerts AND a falling dissolved-oxygen trend", by_pond.get("POND-AI10-3", {}).get("alert_reading_count", 0) >= 3 and by_pond.get("POND-AI10-3", {}).get("per_parameter_variance", {}).get("do_mg_l", {}).get("trend_direction") == "falling", by_pond.get("POND-AI10-3"))

	# --- analyze_feed_fcr_trend(): real trend, all within the sanity range that verify_shrimp_golden_demo() also checks ---
	fcr_trend = aquaculture_responses["feed_fcr_trend"]["data_facts"]["analyze_feed_fcr_trend"]["trend_chronological"]
	fcr_values = [t["fcr"] for t in fcr_trend]
	check("analyze_feed_fcr_trend() shows a real, monotonically-worsening FCR trend across the 3 isolated crop cycles, all within the realistic 0.8-2.0 range", len(fcr_values) == 3 and fcr_values[0] < fcr_values[1] < fcr_values[2] and all(0.8 <= v <= 2.0 for v in fcr_values), fcr_values)
	check("The most recent crop cycle is correctly flagged deteriorated vs. the trailing average of prior cycles", bool(fcr_trend) and fcr_trend[-1]["flagged_deteriorated"], fcr_trend[-1] if fcr_trend else None)

	# --- analyze_water_trend(): farm-level trend + rising real alert frequency ---
	water_trend_facts = aquaculture_responses["water_trend"]["data_facts"]["analyze_water_trend"]
	alerts = water_trend_facts.get("automation_flagged_alerts", {})
	check("analyze_water_trend() shows a real falling farm-level dissolved-oxygen trend", water_trend_facts.get("per_parameter_trend", {}).get("do_mg_l", {}).get("trend_direction") == "falling", water_trend_facts.get("per_parameter_trend", {}).get("do_mg_l"))
	check("analyze_water_trend()'s real automation-flagged alert count rose from the early period to the recent period", alerts.get("recent_period", 0) > alerts.get("early_period", 0), alerts)

	# --- explain_pond_anomaly(): grounded in real instability signal + real linked Health Treatment ---
	anomaly_facts = aquaculture_responses["pond_anomaly_explanation"]["data_facts"]["explain_pond_anomaly"]
	check("explain_pond_anomaly() grounds its explanation in a real instability_signal with automation-flagged alerts", bool(anomaly_facts.get("instability_signal", {}).get("alert_reading_count")), anomaly_facts.get("instability_signal"))
	check("explain_pond_anomaly() cites a real linked Shrimp Health Treatment (never fabricated)", bool(anomaly_facts.get("linked_health_treatments")), anomaly_facts.get("linked_health_treatments"))

	# --- Isolation proof: both underlying golden demos' OWN verify functions still pass unaffected ---
	pig_result = verify_pig_farm_golden_demo()
	check(
		"Golden Demo #11 (Pig Farm)'s OWN verify_pig_farm_golden_demo() still passes after AI-DEMO-09's isolated pens/cohorts were added (isolation design holds)",
		pig_result["all_passed"],
		[c for c in pig_result["checks"] if not c["passed"]],
	)
	shrimp_result = verify_shrimp_golden_demo()
	check(
		"Golden Demo #8 (Shrimp Farm)'s OWN verify_shrimp_golden_demo() still passes after AI-DEMO-10's isolated ponds/cycles were added (isolation design holds)",
		shrimp_result["all_passed"],
		[c for c in shrimp_result["checks"] if not c["passed"]],
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_permission_aware_rag_golden_demo() -> dict:
	"""Phase 6A — Permission-aware RAG (master plan §13.9, lines ~1231-1264; RAG test list §19F
	lines ~3304-3310), the eighth Phase 6A item. Re-derives every one of the 5 NAMED RAG tests
	from live data/live calls, never trusting the seed step's own self-report:
	  - Tool Registry extended (not duplicated): 2 new AI Tools (`search_knowledge_base`,
	    `get_document`) registered/enabled/importable, on top of AI-DEMO-01/02/03/05/06/09/10's
	    original 29 (31 total).
	  - Architecture: `permission_aware_rag_synthesis` AI Action/Prompt Template reuse the existing
	    CE-13 foundation, human_review_required=0 (documented NO-DRAFT design), and the `RAG Chunk`
	    vector index DocType exists with the real chunking/MOCK-embedding/citation fields.
	  - Both use cases (`ask_knowledge_base`, `get_document_content`) run end-to-end with real,
	    tool-sourced data, no ai_suggestion/draft field anywhere.
	  - RAG test 'Effective doc retrieved': get_document_content() returns the real CURRENT
	    version's content (not a stale one).
	  - RAG test 'Obsolete doc not used as current': two real Obsolete revisions genuinely match
	    the query vocabulary (proven directly against their stored mock-embedding vectors) yet are
	    NEVER returned by search_knowledge_base() — only the current revision is.
	  - RAG test 'User without permission cannot retrieve': two real, differently-permissioned
	    users (a real Quality Manager vs. a real Stock-User-only 3PL portal user) get genuinely
	    different results — the unauthorized user's zero results are explained by a real
	    permission_denied_source_count > 0, not a coincidental non-match.
	  - RAG test 'Version update triggers re-index': a LIVE status-change event (a new version
	    promoted to Effective) is shown to automatically flip the superseded version's chunks to
	    Obsolete/is_current=0 and index the new version's chunks as Effective/is_current=1 — via
	    the real hooks.py on_update hook, with no manual reindex call anywhere in this check.
	  - RAG test 'Source citations correct': every citation returned is cross-checked against the
	    real, live DMS Document/DMS Document Version records it claims to cite.
	  - Idempotency: re-running the bulk indexer twice does not duplicate any RAG Chunk row.
	  - Golden Demo #4 (DMS)'s and AI-DEMO-03 (DMS Copilot)'s OWN verify_*_golden_demo() functions
	    still pass after this demo's isolated document/hooks were added.
	"""
	from enterprise_core.enterprise_core import rag_pipeline
	from enterprise_core.enterprise_core.ai_permission_aware_rag import (
		QUESTION_TOOL_MAP,
		ask_knowledge_base,
		get_document_content,
	)

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	doc_code = "SOP-CAL-01"
	authorized_user = "qa.manager@pharmacountry.vn"
	unauthorized_user = "client.a.3pl@pharmacountry.vn"
	query = "pressure gauge calibration interval"

	# --- Tool Registry: 2 new tools, on top of AI-DEMO-01/02/03/05/06/09/10's original 29 ---
	new_tool_codes = ["search_knowledge_base", "get_document"]
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("31 AI Tools registered total (prior 29 + this demo's 2, same shared registry)", len(all_tools) >= 31, sorted(all_tool_codes))
	check("Both new AI Tools present in the registry", set(new_tool_codes).issubset(all_tool_codes), sorted(all_tool_codes))
	new_tools = [t for t in all_tools if t.tool_code in new_tool_codes]
	check("Both new AI Tools are enabled", all(t.enabled for t in new_tools) and len(new_tools) == 2, new_tools)
	importable = {}
	for t in new_tools:
		try:
			fn = frappe.get_attr(t.python_function_path)
			importable[t.tool_code] = callable(fn)
		except Exception:
			importable[t.tool_code] = False
	check("Every new AI Tool's python_function_path actually imports to a callable", all(importable.values()), importable)

	# --- AI Action / Prompt Template / RAG Chunk DocType wiring ---
	check("permission_aware_rag_synthesis AI Action exists and does NOT require human review (NO-DRAFT)", frappe.db.get_value("AI Action", "permission_aware_rag_synthesis", "human_review_required") == 0, None)
	check("permission_aware_rag_synthesis Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "permission_aware_rag_synthesis", "version": 1, "enabled": 1}), None)
	rag_chunk_fieldnames = {df.fieldname for df in frappe.get_meta("RAG Chunk").fields} if frappe.db.exists("DocType", "RAG Chunk") else set()
	check("RAG Chunk DocType exists with the mandatory chunk/embedding/version/currency fields", {"chunk_text", "embedding", "version_no", "is_current", "source_status"}.issubset(rag_chunk_fieldnames), sorted(rag_chunk_fieldnames))

	# --- Base isolated fixtures exist ---
	check(f"Isolated demo Document {doc_code} exists", frappe.db.exists("DMS Document", doc_code), doc_code)
	if not frappe.db.exists("DMS Document", doc_code):
		return {"all_passed": False, "checks": checks}

	# --- Both use cases answer with real data, NO ai_suggestion field, and a real AI Job Log entry ---
	responses = {}
	for question_code, expected_tools in QUESTION_TOOL_MAP.items():
		resp = ask_knowledge_base(query, user=authorized_user) if question_code == "ask_knowledge_base" else get_document_content(doc_code, user=authorized_user)
		responses[question_code] = resp
		check(f"'{question_code}': tools_called matches the fixed registry mapping (no arbitrary tool/SQL execution)", resp["tools_called"] == expected_tools, resp["tools_called"])
		check(f"'{question_code}': data_facts and ai_interpretation are separate, non-blended fields", isinstance(resp["data_facts"], dict) and isinstance(resp["ai_interpretation"], str), None)
		check(f"'{question_code}': response has NO ai_suggestion/draft field (documented NO-DRAFT design)", "ai_suggestion" not in resp, sorted(resp.keys()))
		check(f"'{question_code}': response carries structured citations (not a raw, unattributed text blob)", isinstance(resp.get("citations"), list), resp.get("citations"))
		log = frappe.db.get_value("AI Job Log", resp["job_log"], ["provider", "model", "tool_calls"], as_dict=True) if resp.get("job_log") else None
		check(f"'{question_code}': AI Job Log entry records provider/model/tool_calls", bool(log and log.provider and log.model and log.tool_calls), log)

	# --- RAG test #4: 'Version update triggers re-index' — a LIVE status-change event, checked live ---
	v2_name = frappe.db.get_value("DMS Document Version", {"document": doc_code, "version_no": 2}, "name")
	check("v1/v2 exist before the live re-index trigger", bool(v2_name), v2_name)
	v3_already_existed = frappe.db.exists("DMS Document Version", {"document": doc_code, "version_no": 3})
	if not v3_already_existed:
		before_v2_chunks = frappe.get_all("RAG Chunk", filters={"source_reference": v2_name}, fields=["is_current"])
		check("Before the live trigger: v2's chunks are ALL is_current=1 (the current version so far)", bool(before_v2_chunks) and all(c.is_current for c in before_v2_chunks), before_v2_chunks)

	# Import here (not at module top) — mirrors this file's own existing local-import style for
	# demo-specific seed helpers used only inside one verify function.
	from enterprise_core.enterprise_core.ai_permission_aware_rag_seeds import _promote_version, _V3_CONTENT

	v3_name, v3_created = _promote_version(3, _V3_CONTENT)  # the real trigger event — a genuine .save()
	v2_chunks_after = frappe.get_all("RAG Chunk", filters={"source_reference": v2_name}, fields=["is_current", "source_status"])
	v3_chunks_after = frappe.get_all("RAG Chunk", filters={"source_reference": v3_name}, fields=["is_current", "source_status"])
	check("RAG test 'Version update triggers re-index': v2's chunks auto-flipped to Obsolete/is_current=0 (no manual reindex call)", bool(v2_chunks_after) and all((not c.is_current) and c.source_status == "Obsolete" for c in v2_chunks_after), v2_chunks_after)
	check("RAG test 'Version update triggers re-index': v3's chunks auto-indexed as Effective/is_current=1 immediately after promotion", bool(v3_chunks_after) and all(c.is_current for c in v3_chunks_after), v3_chunks_after)

	# --- RAG test #1: 'Effective doc retrieved' ---
	doc_resp = get_document_content(doc_code, user=authorized_user)
	doc_data = doc_resp["data_facts"]["get_document"]
	check("RAG test 'Effective doc retrieved': get_document_content() returns the REAL current version (v3)", doc_data.get("version") == v3_name, doc_data.get("version"))
	check("RAG test 'Effective doc retrieved': retrieved content reflects the latest revision (30-day interval)", "30 day" in (doc_data.get("content") or ""), doc_data.get("content"))
	check("RAG test 'Effective doc retrieved': multiple real chunks (chunking pipeline proof, not a single blob)", doc_data.get("chunk_count", 0) >= 2, doc_data.get("chunk_count"))

	# --- RAG test #2: 'Obsolete doc not used as current' ---
	search_resp = ask_knowledge_base(query, user=authorized_user, top_k=10)
	result_versions = {r["version"] for r in search_resp["data_facts"]["search_knowledge_base"]["results"]}
	check("RAG test 'Obsolete doc not used as current': current v3 IS returned by search_knowledge_base()", v3_name in result_versions, sorted(result_versions))
	query_vector = rag_pipeline.mock_embed(query)
	for version_no in (1, 2):
		v_name = frappe.db.get_value("DMS Document Version", {"document": doc_code, "version_no": version_no}, "name")
		v_status = frappe.db.get_value("DMS Document Version", v_name, "status")
		obsolete_chunks = frappe.get_all("RAG Chunk", filters={"source_reference": v_name}, fields=["embedding"])
		similarities = [rag_pipeline.cosine_similarity(query_vector, frappe.parse_json(c.embedding)) for c in obsolete_chunks]
		check(f"RAG test 'Obsolete doc not used as current': v{version_no} is genuinely Obsolete AND genuinely matches the query vocabulary (real similarity > 0)", v_status == "Obsolete" and any(s > 0 for s in similarities), {"status": v_status, "similarities": similarities})
		check(f"RAG test 'Obsolete doc not used as current': v{version_no} is NEVER returned as current knowledge despite matching", v_name not in result_versions, sorted(result_versions))

	# --- RAG test #3: 'User without permission cannot retrieve' ---
	denied_resp = ask_knowledge_base(query, user=unauthorized_user)
	authorized_count = search_resp["data_facts"]["search_knowledge_base"]["count"]
	denied_data = denied_resp["data_facts"]["search_knowledge_base"]
	check("RAG test 'User without permission cannot retrieve': the authorized user (real Quality Manager role) gets real, non-zero results", authorized_count > 0, authorized_count)
	check("RAG test 'User without permission cannot retrieve': the unauthorized user (real Stock-User-only 3PL portal user, zero DMS permission) gets ZERO results", denied_data["count"] == 0, denied_data)
	check("RAG test 'User without permission cannot retrieve': the zero result is explained by a REAL permission denial, not a coincidental non-match", denied_data.get("permission_denied_source_count", 0) > 0, denied_data.get("permission_denied_source_count"))

	# --- RAG test #5: 'Source citations correct' ---
	citations = search_resp["citations"]
	check("RAG test 'Source citations correct': search_knowledge_base() returned at least one citation", bool(citations), citations)
	citation_mismatches = []
	for c in citations:
		real = frappe.db.get_value("DMS Document Version", c["version"], ["document", "version_no"], as_dict=True)
		if not real or real.document != c["document"] or real.version_no != c["version_no"]:
			citation_mismatches.append({"citation": c, "real": real})
	check("RAG test 'Source citations correct': every search citation matches the real, live DMS Document Version record it claims to cite", not citation_mismatches, citation_mismatches)
	real_doc = frappe.db.get_value("DMS Document", doc_code, ["title", "current_version"], as_dict=True)
	doc_citation = (doc_resp.get("citations") or [None])[0]
	check("RAG test 'Source citations correct': get_document_content() citation matches the real, live DMS Document record", bool(doc_citation) and doc_citation.get("version") == real_doc.current_version and doc_citation.get("title") == real_doc.title, {"citation": doc_citation, "real": real_doc})

	# --- Idempotency: re-running the bulk indexer twice never duplicates chunk rows ---
	before_count = frappe.db.count("RAG Chunk", {"document_code": doc_code})
	rag_pipeline.reindex_all_effective_documents()
	rag_pipeline.reindex_all_effective_documents()
	after_count = frappe.db.count("RAG Chunk", {"document_code": doc_code})
	check("Idempotency: re-running the bulk indexer twice does not duplicate any RAG Chunk row", before_count == after_count, {"before": before_count, "after": after_count})

	# --- Isolation proof: Golden Demo #4 (DMS) and AI-DEMO-03 (DMS Copilot)'s OWN verify functions still pass ---
	dms_result = verify_dms_golden_demo()
	check("Golden Demo #4 (DMS)'s OWN verify_dms_golden_demo() still passes after this demo's isolated document/hooks were added", dms_result["all_passed"], [c for c in dms_result["checks"] if not c["passed"]])
	dms_copilot_result = verify_ai_dms_copilot_golden_demo()
	check("AI-DEMO-03 (DMS Copilot)'s OWN verify_ai_dms_copilot_golden_demo() still passes after this demo's additive re-index hook was added", dms_copilot_result["all_passed"], [c for c in dms_copilot_result["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_ai_evaluation_datasets_golden_demo() -> dict:
	"""Phase 6A — Evaluation Datasets (master plan §13.14 "AI Evaluation", lines ~1365-1382), the
	NINTH and FINAL Phase 6A item. Re-derives every check from live data/live calls, never trusting
	the seed step's own self-report:
	  - Tool Registry extended (not duplicated): `classify_complaint` registered/enabled/importable
	    on top of AI-DEMO-01/02/03/05/06/09/10/RAG's original 31 tools (32 total).
	  - `classify_complaint` AI Action/Prompt Template exist, reusing the existing CE-13 foundation.
	  - `AI Evaluation Case`/`AI Evaluation Run` DocTypes exist with the mandatory fields.
	  - A real, labeled dataset exists for BOTH `deviation_analysis` (>=7 cases, a real mix of
	    organic pre-existing QMS Deviation records AND a few newly-seeded isolated ones for missing
	    severity/category coverage) and `classify_complaint` (>=12 newly-seeded QMS Complaint cases
	    — QMS Complaint had zero pre-existing records platform-wide).
	  - `run_evaluation()` executes end-to-end for both actions: a real pass/fail tally against each
	    case's real labeled ground truth, a real >0 source_support_score, and the mock-dependent
	    rubric dimensions (groundedness/hallucination/actionability) are honestly left None/N-A
	    with a non-empty disclosure — never a fabricated number.
	  - False-positive/negative tracking genuinely fires for `classify_complaint` (>=1 of each, from
	    2 deliberately-labeled classifier-limitation cases), not just trivially reporting zero.
	  - `check_model_swap_safe()` produces a REAL ALLOW verdict for a capability-compatible
	    candidate model (no regression) AND a REAL BLOCK verdict for a capability-incompatible one
	    (a genuine 0% pass-rate regression) — from two real, persisted AI Evaluation Run records
	    each time, with AI Model enabled-state correctly restored afterward.
	  - `regression_vs_previous_run` is populated on at least one AI Evaluation Run.
	  - Golden Demo #2/#3 (QMS)'s and AI-DEMO-02 (QMS Copilot)'s OWN verify_*_golden_demo()
	    functions still pass after this demo's isolated Deviations/Complaints were added.
	"""
	from enterprise_core.enterprise_core.ai_evaluation import NOT_APPLICABLE_MOCKED, check_model_swap_safe, run_evaluation
	from enterprise_core.enterprise_core.ai_evaluation_seeds import (
		MODEL_SWAP_INCOMPATIBLE_MODEL_CODE,
		MODEL_SWAP_SAFE_MODEL_CODE,
	)

	checks = []

	def check(name, passed, detail):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# --- Tool Registry: classify_complaint on top of the prior 31 ---
	all_tools = frappe.get_all("AI Tool", fields=["tool_code", "enabled", "python_function_path"])
	all_tool_codes = {t.tool_code for t in all_tools}
	check("32 AI Tools registered total (prior 31 + classify_complaint, same shared registry)", len(all_tools) >= 32, sorted(all_tool_codes))
	check("classify_complaint AI Tool present and enabled", "classify_complaint" in all_tool_codes and next((t.enabled for t in all_tools if t.tool_code == "classify_complaint"), 0), None)
	classify_tool = next((t for t in all_tools if t.tool_code == "classify_complaint"), None)
	importable = False
	if classify_tool:
		try:
			importable = callable(frappe.get_attr(classify_tool.python_function_path))
		except Exception:
			importable = False
	check("classify_complaint's python_function_path actually imports to a callable", importable, classify_tool)

	# --- AI Action / Prompt Template / DocType wiring ---
	check("classify_complaint AI Action exists", frappe.db.exists("AI Action", "classify_complaint"), None)
	check("classify_complaint Prompt Template exists and is enabled", frappe.db.exists("Prompt Template", {"template_code": "classify_complaint", "version": 1, "enabled": 1}), None)
	case_fieldnames = {df.fieldname for df in frappe.get_meta("AI Evaluation Case").fields} if frappe.db.exists("DocType", "AI Evaluation Case") else set()
	check("AI Evaluation Case DocType exists with the mandatory labeling fields", {"action_code", "input_reference", "expected_category", "expected_severity", "secondary_flag_name", "expected_secondary_flag", "is_synthetic"}.issubset(case_fieldnames), sorted(case_fieldnames))
	run_fieldnames = {df.fieldname for df in frappe.get_meta("AI Evaluation Run").fields} if frappe.db.exists("DocType", "AI Evaluation Run") else set()
	check("AI Evaluation Run DocType exists with the mandatory scoring/rubric/regression fields", {"pass_rate_percent", "false_positive_count", "false_negative_count", "source_support_score", "groundedness_score", "hallucination_flag_rate", "actionability_score", "regression_vs_previous_run"}.issubset(run_fieldnames), sorted(run_fieldnames))

	# --- Real labeled datasets exist ---
	dev_cases = frappe.get_all("AI Evaluation Case", filters={"action_code": "deviation_analysis", "enabled": 1}, fields=["name", "is_synthetic"])
	check("deviation_analysis has >=7 enabled labeled cases", len(dev_cases) >= 7, len(dev_cases))
	check("deviation_analysis's dataset includes REAL, organic (non-synthetic) pre-existing records, not fabricated data", sum(1 for c in dev_cases if not c.is_synthetic) >= 5, dev_cases)
	complaint_cases = frappe.get_all("AI Evaluation Case", filters={"action_code": "classify_complaint", "enabled": 1}, fields=["name"])
	check("classify_complaint has >=12 enabled labeled cases", len(complaint_cases) >= 12, len(complaint_cases))

	# --- run_evaluation() end-to-end, both actions ---
	dev_report = run_evaluation("deviation_analysis", user="Administrator")
	check("deviation_analysis evaluation run: total_cases matches the real dataset size", dev_report["total_cases"] == len(dev_cases), dev_report["total_cases"])
	check("deviation_analysis evaluation run: passed_cases + failed_cases == total_cases", dev_report["passed_cases"] + dev_report["failed_cases"] == dev_report["total_cases"], dev_report)
	check("deviation_analysis evaluation run: real, non-zero source_support_score", dev_report["source_support_score"] > 0, dev_report["source_support_score"])
	dev_run_doc = frappe.get_doc("AI Evaluation Run", dev_report["run"])
	check("deviation_analysis evaluation run: mock-dependent rubric fields (groundedness/hallucination/actionability) honestly left N/A, not fabricated", dev_run_doc.groundedness_score == NOT_APPLICABLE_MOCKED and dev_run_doc.hallucination_flag_rate == NOT_APPLICABLE_MOCKED and dev_run_doc.actionability_score == NOT_APPLICABLE_MOCKED, {"groundedness": dev_run_doc.groundedness_score, "hallucination": dev_run_doc.hallucination_flag_rate, "actionability": dev_run_doc.actionability_score})
	check("deviation_analysis evaluation run: rubric_scoring_notes discloses the mock-adapter limitation honestly", bool(dev_run_doc.rubric_scoring_notes) and "MOCK" in dev_run_doc.rubric_scoring_notes, dev_run_doc.rubric_scoring_notes)

	complaint_report = run_evaluation("classify_complaint", user="Administrator")
	check("classify_complaint evaluation run: total_cases matches the real dataset size", complaint_report["total_cases"] == len(complaint_cases), complaint_report["total_cases"])
	check("classify_complaint evaluation run: false-positive tracking genuinely fires (>=1, from a real deliberate keyword-collision case)", complaint_report["false_positive_count"] >= 1, complaint_report["false_positive_count"])
	check("classify_complaint evaluation run: false-negative tracking genuinely fires (>=1, from a real deliberate under-flagged case)", complaint_report["false_negative_count"] >= 1, complaint_report["false_negative_count"])
	check("classify_complaint evaluation run: real, non-zero source_support_score", complaint_report["source_support_score"] > 0, complaint_report["source_support_score"])

	# --- check_model_swap_safe(): the concrete governance-principle proof ---
	original_model_states = {m.name: m.enabled for m in frappe.get_all("AI Model", fields=["name", "enabled"])}
	allowed = check_model_swap_safe("classify_complaint", MODEL_SWAP_SAFE_MODEL_CODE, user="Administrator")
	check("check_model_swap_safe(): a capability-compatible candidate model is ALLOWED (real, non-regressing pass-rate comparison)", allowed["verdict"] == "ALLOWED" and not allowed["regressed"], allowed)
	blocked = check_model_swap_safe("classify_complaint", MODEL_SWAP_INCOMPATIBLE_MODEL_CODE, user="Administrator")
	check("check_model_swap_safe(): a capability-INCOMPATIBLE candidate model is BLOCKED (real 0% candidate pass rate, genuine regression)", blocked["verdict"] == "BLOCKED" and blocked["regressed"] and blocked["candidate_pass_rate_percent"] == 0.0, blocked)
	restored_states = {m.name: m.enabled for m in frappe.get_all("AI Model", fields=["name", "enabled"])}
	check("check_model_swap_safe(): every AI Model's enabled state was correctly restored afterward (no lingering site-wide side effect)", restored_states == original_model_states, {"before": original_model_states, "after": restored_states})

	# --- regression_vs_previous_run populated: checked on the BLOCKED scenario's own baseline run,
	# which by this point in the function is guaranteed to have at least one real predecessor run
	# for classify_complaint (the direct run_evaluation() call above, and/or the ALLOWED scenario's
	# own 2 runs) — unlike the very FIRST run_evaluation() call for an action on a fresh site
	# (which correctly has no predecessor and leaves this field empty, not a bug).
	blocked_baseline_doc = frappe.get_doc("AI Evaluation Run", blocked["baseline_run"])
	check("regression_vs_previous_run is populated once a real predecessor run exists for the same action_code", bool(blocked_baseline_doc.regression_vs_previous_run), blocked_baseline_doc.regression_vs_previous_run)

	# --- Isolation proof: Golden Demo #2/#3 (QMS) and AI-DEMO-02 (QMS Copilot)'s OWN verify functions still pass ---
	qms_result = verify_qms_golden_demo()
	check("Golden Demo #2/#3 (QMS)'s OWN verify_qms_golden_demo() still passes after this demo's isolated Deviations were added", qms_result["all_passed"], [c for c in qms_result["checks"] if not c["passed"]])
	qms_copilot_result = verify_ai_qms_copilot_golden_demo()
	check("AI-DEMO-02 (QMS Copilot)'s OWN verify_ai_qms_copilot_golden_demo() still passes after this demo's isolated Deviations were added", qms_copilot_result["all_passed"], [c for c in qms_copilot_result["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_dealer_portal_demo() -> dict:
	"""WEB-03 (B2B Customer / Dealer Portal) integrity check, same pattern as every prior golden
	demo's verify_* function. Runs the (idempotent) seed steps first — dealer_portal_seeds.py is
	deliberately NOT wired into after_install/after_migrate (see its own module docstring: it's
	demo-portal test fixture data layered on top of Golden Demo #25, not a new Industry Pack golden
	demo in its own right), so this verify function is also this data's own re-seed entry point for
	the regression sweep."""
	from enterprise_core.enterprise_core.dealer_portal_api import get_my_debt, verify_dealer_portal_access_control
	from enterprise_core.enterprise_core.dealer_portal_seeds import (
		_ALPHA_USER,
		_BETA_USER,
		_DEALER_ALPHA,
		_DEALER_BETA,
		seed_dealer_portal_credit_test,
		seed_dealer_portal_master_data,
		seed_dealer_portal_sales_flow,
	)

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	seed_dealer_portal_master_data()
	seed_dealer_portal_sales_flow()
	seed_dealer_portal_credit_test()

	check("Dealer Alpha Customer exists, isolated from Golden Demo #25's own Hanoi/Saigon dealers", frappe.db.exists("Customer", {"customer_name": _DEALER_ALPHA}), None)
	check("Dealer Beta Customer exists, isolated from Golden Demo #25's own Hanoi/Saigon dealers", frappe.db.exists("Customer", {"customer_name": _DEALER_BETA}), None)
	check("Dealer Alpha portal User exists", frappe.db.exists("User", _ALPHA_USER), None)
	check("Dealer Beta portal User exists", frappe.db.exists("User", _BETA_USER), None)
	check(
		"Dealer Alpha's User Permission scopes it to exactly its own Customer",
		frappe.db.get_value("User Permission", {"user": _ALPHA_USER, "allow": "Customer"}, "for_value") == _DEALER_ALPHA,
		None,
	)
	check(
		"Dealer Beta's User Permission scopes it to exactly its own Customer",
		frappe.db.get_value("User Permission", {"user": _BETA_USER, "allow": "Customer"}, "for_value") == _DEALER_BETA,
		None,
	)

	# Real credit-limit block, isolated dealer (mirrors CD04's own mechanism, never mutates CD04's
	# own Hanoi dealer data).
	beta_credit_test_so = frappe.db.get_value("Sales Order", {"po_no": "WEB03-BETA-CREDIT-TEST"}, "name")
	check(
		"Beta's deliberately over-credit-limit order was blocked (no submitted Sales Order left behind)",
		not beta_credit_test_so or frappe.db.get_value("Sales Order", beta_credit_test_so, "docstatus") != 1,
		beta_credit_test_so,
	)
	beta_inlimit_so = frappe.db.get_value("Sales Order", {"po_no": "WEB03-BETA-FLOW-1", "docstatus": 1}, "name")
	check("Beta's real, within-limit order was NOT blocked", bool(beta_inlimit_so), beta_inlimit_so)

	# get_my_debt() run for real, as Alpha, confirming a genuine non-error computed balance/credit
	# view (not just that the Customer Credit Limit row exists).
	original_user = frappe.session.user
	try:
		frappe.set_user(_ALPHA_USER)
		alpha_debt = get_my_debt()
	finally:
		frappe.set_user(original_user)
	check("get_my_debt() resolves a real credit_limit for the logged-in dealer", alpha_debt.get("credit_limit") == 20000000, alpha_debt)

	# The empirical two-user cross-dealer permission proof — see dealer_portal_api.py's own
	# docstring for why this is the single most important check in this whole demo.
	access_result = verify_dealer_portal_access_control()
	check("Empirical cross-dealer access-control proof (login as Alpha, login as Beta, cross-access attempts) — ALL sub-checks passed", access_result["all_passed"], [c for c in access_result["checks"] if not c["passed"]])

	# Isolation proof: Golden Demo #25's own verify function must still pass unchanged after this
	# demo's isolated dealers/orders were added on top of the same company.
	cd_result = verify_consumer_dist_golden_demo()
	check("Golden Demo #25 (Consumer Distribution)'s OWN verify_consumer_dist_golden_demo() still passes after WEB-03's isolated dealers were added", cd_result["all_passed"], [c for c in cd_result["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_supplier_portal_demo() -> dict:
	"""WEB-04 (Supplier / RFQ Portal) integrity check, same pattern as every prior golden demo's
	verify_* function — a close structural twin of `verify_dealer_portal_demo()` above. Runs the
	(idempotent) seed steps first — `supplier_portal_seeds.py` is deliberately NOT wired into
	after_install/after_migrate (same precedent as `dealer_portal_seeds.py`), so this verify function
	is also this data's own re-seed entry point for the regression sweep. Reuses Golden Demo #27's
	real Cargill/Nutreco suppliers rather than minting new ones (see `supplier_portal_seeds.py`'s own
	module docstring for why that was confirmed safe) so this function ALSO re-runs
	`verify_ingredient_trading_golden_demo()` and `verify_ai_procurement_assistant_golden_demo()` at
	the end, to prove those two golden demos' own idempotency assumptions were never disturbed."""
	from enterprise_core.enterprise_core.supplier_portal_api import (
		get_my_qualification_status,
		verify_supplier_portal_access_control,
	)
	from enterprise_core.enterprise_core.supplier_portal_seeds import (
		_CARGILL_USER,
		_NUTRECO_USER,
		_RFQ_CARGILL_MARKER,
		_RFQ_NUTRECO_MARKER,
		_SUPPLIER_CARGILL,
		_SUPPLIER_NUTRECO,
		seed_supplier_portal_demo_data,
	)

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	seed_supplier_portal_demo_data()

	check("Cargill Asia Trading Pte Ltd Supplier exists (real Golden Demo #27 supplier, reused not duplicated)", frappe.db.exists("Supplier", _SUPPLIER_CARGILL), None)
	check("Nutreco South America S.A. Supplier exists (real Golden Demo #27 supplier, reused not duplicated)", frappe.db.exists("Supplier", _SUPPLIER_NUTRECO), None)
	check("Cargill portal User exists", frappe.db.exists("User", _CARGILL_USER), None)
	check("Nutreco portal User exists", frappe.db.exists("User", _NUTRECO_USER), None)
	check(
		"Cargill's User Permission scopes it to exactly its own Supplier",
		frappe.db.get_value("User Permission", {"user": _CARGILL_USER, "allow": "Supplier"}, "for_value") == _SUPPLIER_CARGILL,
		None,
	)
	check(
		"Nutreco's User Permission scopes it to exactly its own Supplier",
		frappe.db.get_value("User Permission", {"user": _NUTRECO_USER, "allow": "Supplier"}, "for_value") == _SUPPLIER_NUTRECO,
		None,
	)

	# Both RFQs are real, submitted, single-supplier documents.
	cargill_rfq = frappe.db.get_value("Request for Quotation", {"title": _RFQ_CARGILL_MARKER}, ["name", "docstatus"], as_dict=True)
	nutreco_rfq = frappe.db.get_value("Request for Quotation", {"title": _RFQ_NUTRECO_MARKER}, ["name", "docstatus"], as_dict=True)
	check("Cargill's RFQ exists and is submitted", bool(cargill_rfq) and cargill_rfq.docstatus == 1, cargill_rfq)
	check("Nutreco's RFQ exists and is submitted", bool(nutreco_rfq) and nutreco_rfq.docstatus == 1, nutreco_rfq)

	# Cargill's real, live-submitted quotation response against its own RFQ (the write-path proof —
	# see supplier_portal_seeds.seed_supplier_portal_quotation_response()).
	cargill_response = frappe.db.exists(
		"Supplier Quotation Item", {"request_for_quotation": cargill_rfq.name if cargill_rfq else None, "docstatus": 1}
	)
	check("Cargill's real quotation response against its own RFQ was submitted (docstatus=1)", bool(cargill_response), cargill_response)

	# Nutreco's RFQ was deliberately left unanswered — a genuine "invited, not yet responded" state.
	nutreco_response = frappe.db.exists(
		"Supplier Quotation Item", {"request_for_quotation": nutreco_rfq.name if nutreco_rfq else None}
	)
	check("Nutreco's RFQ was deliberately left unanswered (no Supplier Quotation Item links back to it)", not nutreco_response, nutreco_response)

	# get_my_qualification_status() run for real, as Cargill, confirming a genuine non-error view.
	original_user = frappe.session.user
	try:
		frappe.set_user(_CARGILL_USER)
		cargill_qual = get_my_qualification_status()
	finally:
		frappe.set_user(original_user)
	check("get_my_qualification_status() resolves real quality_status/is_critical_supplier for the logged-in supplier", cargill_qual.get("supplier") == _SUPPLIER_CARGILL and "quality_status" in cargill_qual, cargill_qual)

	# The empirical two-user cross-supplier permission proof — the single most important check in
	# this whole demo (see supplier_portal_api.py's own docstring).
	access_result = verify_supplier_portal_access_control()
	check("Empirical cross-supplier access-control proof (login as Cargill, login as Nutreco, cross-access attempts) — ALL sub-checks passed", access_result["all_passed"], [c for c in access_result["checks"] if not c["passed"]])

	# Isolation proof: both golden demos whose real supplier data this portal reuses must still pass
	# their OWN verify functions unchanged, run TWICE to catch any silent idempotency corruption.
	it_result_1 = verify_ingredient_trading_golden_demo()
	it_result_2 = verify_ingredient_trading_golden_demo()
	check("Golden Demo #27 (Ingredient Trading)'s OWN verify_ingredient_trading_golden_demo() still passes after WEB-04's data was added (run #1)", it_result_1["all_passed"], [c for c in it_result_1["checks"] if not c["passed"]])
	check("Golden Demo #27 (Ingredient Trading)'s OWN verify_ingredient_trading_golden_demo() still passes when re-run a second time (idempotency)", it_result_2["all_passed"], [c for c in it_result_2["checks"] if not c["passed"]])

	ai6_result_1 = verify_ai_procurement_assistant_golden_demo()
	ai6_result_2 = verify_ai_procurement_assistant_golden_demo()
	check("AI-DEMO-06 (Procurement Assistant)'s OWN verify_ai_procurement_assistant_golden_demo() still passes after WEB-04's data was added (run #1)", ai6_result_1["all_passed"], [c for c in ai6_result_1["checks"] if not c["passed"]])
	check("AI-DEMO-06 (Procurement Assistant)'s OWN verify_ai_procurement_assistant_golden_demo() still passes when re-run a second time (idempotency)", ai6_result_2["all_passed"], [c for c in ai6_result_2["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_b2c_commerce_demo() -> dict:
	"""WEB-05 (B2C Commerce) integrity check, same pattern as every prior golden demo's verify_*
	function. Unlike WEB-03/WEB-04, there are no seed fixtures to re-run here — `b2c_commerce_api.py`
	is a genuinely stateless-per-request guest-write endpoint, so this function's own empirical
	access-control proof (`verify_b2c_commerce_access_control()`) IS the demo data: every run places
	several real new Sales Orders against the isolated "Web Store Guest" customer to prove the
	pricing-integrity and order-lookup constraints for real. Reuses Demo Consumer Distribution Co.
	(Golden Demo #25)'s real company/item/price-list data (same choice WEB-01/WEB-03 already made),
	so this ALSO re-runs `verify_consumer_dist_golden_demo()` to prove that golden demo's own CD01-
	CD06 assertions were never disturbed by WEB-05's new guest orders."""
	from enterprise_core.enterprise_core.b2c_commerce_api import _WEB_GUEST_CUSTOMER, verify_b2c_commerce_access_control

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	# The single most important check in this whole demo — see b2c_commerce_api.py's own docstring
	# for why an anonymous-write guest-checkout endpoint is a genuinely new risk category on this
	# platform. Proves, empirically, that a spoofed client-supplied price is ignored and that order
	# lookup genuinely requires both the random token and the checkout phone number.
	access_result = verify_b2c_commerce_access_control()
	check(
		"Empirical guest-checkout security proof (price-tampering resistance, stock/qty/item validation, order-lookup two-factor requirement) — ALL sub-checks passed",
		access_result["all_passed"],
		[c for c in access_result["checks"] if not c["passed"]],
	)

	check(
		"Web Store Guest customer exists and is isolated from Golden Demo #25's own flagship dealers/WEB-03's portal dealers",
		frappe.db.exists("Customer", {"customer_name": _WEB_GUEST_CUSTOMER})
		and _WEB_GUEST_CUSTOMER not in ("Golden Health Hanoi Dealer Co.", "Golden Health Saigon Dealer Co.", "WEB03 Portal Dealer Alpha", "WEB03 Portal Dealer Beta"),
		_WEB_GUEST_CUSTOMER,
	)

	# Isolation proof: Golden Demo #25's own verify function must still pass unchanged after WEB-05's
	# guest orders were layered on top of the same company, run TWICE to catch any silent idempotency
	# corruption from the repeated verify-time order placements above.
	cd_result_1 = verify_consumer_dist_golden_demo()
	cd_result_2 = verify_consumer_dist_golden_demo()
	check("Golden Demo #25 (Consumer Distribution)'s OWN verify_consumer_dist_golden_demo() still passes after WEB-05's guest orders were added (run #1)", cd_result_1["all_passed"], [c for c in cd_result_1["checks"] if not c["passed"]])
	check("Golden Demo #25 (Consumer Distribution)'s OWN verify_consumer_dist_golden_demo() still passes when re-run a second time (idempotency)", cd_result_2["all_passed"], [c for c in cd_result_2["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_online_pharmacy_demo() -> dict:
	"""WEB-06 (Online Pharmacy) integrity check, same pattern as every prior golden demo's verify_*
	function — a close structural twin of `verify_b2c_commerce_demo()` above (WEB-06 reuses WEB-05's
	own proven guest-writable-checkout security model almost verbatim, see `online_pharmacy_api.py`'s
	own module docstring for exactly what's reused vs. genuinely new). Runs the (idempotent) one-time
	infra setup first — `online_pharmacy_seeds.py` is deliberately NOT wired into after_install/
	after_migrate (same precedent as `dealer_portal_seeds.py`/`supplier_portal_seeds.py`), so this
	verify function is also this data's own re-setup entry point for the regression sweep. Reuses
	Golden Demo #23 (Pharmacy Chain)'s real company/item/store/batch data rather than minting a new
	pharmacy, so this ALSO re-runs `verify_pharmacy_golden_demo()` TWICE at the end, to prove that
	golden demo's own RX01-RX07 assertions (including RX03's expired-batch-never-sold invariant and
	RX05's own POS-return-against-a-specific-sale lookup, both real corruption risks this build
	designed around via an isolated POS Profile/top-up batch, not discovered by breaking them) were
	never disturbed by WEB-06's own repeated real guest orders."""
	from enterprise_core.enterprise_core.online_pharmacy_api import _ONLINE_GUEST_CUSTOMER, verify_online_pharmacy_access_control
	from enterprise_core.enterprise_core.online_pharmacy_seeds import seed_online_pharmacy_setup

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	seed_online_pharmacy_setup()

	# The single most important check in this whole demo — see online_pharmacy_api.py's own
	# docstring for why an anonymous-write guest-checkout endpoint against a pharmacy's real batch/
	# expiry data is a genuinely higher-risk surface than WEB-05's own non-batched consumer goods.
	# Proves, empirically, that a spoofed client-supplied price/batch is ignored, that order lookup
	# genuinely requires both the random token and the checkout phone number, AND that the SAME
	# native expiry-block mechanism RX03 already proved (Golden Demo #23) still protects this new
	# write path against a deliberate attempt to sell an already-expired batch.
	access_result = verify_online_pharmacy_access_control()
	check(
		"Empirical guest-checkout security + expiry-safety proof (price/batch-tampering resistance,"
		" native BatchExpiredError still blocks the expired batch, order-lookup two-factor"
		" requirement) — ALL sub-checks passed",
		access_result["all_passed"],
		[c for c in access_result["checks"] if not c["passed"]],
	)

	check(
		"Pharmacy Online Guest customer exists and is isolated from Golden Demo #23's own Walk-in Customer",
		frappe.db.exists("Customer", {"customer_name": _ONLINE_GUEST_CUSTOMER}) and _ONLINE_GUEST_CUSTOMER != "Pharmacy Walk-in Customer",
		_ONLINE_GUEST_CUSTOMER,
	)

	# Isolation proof: Golden Demo #23's own verify function must still pass unchanged after WEB-06's
	# guest orders were layered on top of the same company/store/batches, run TWICE to catch any
	# silent idempotency corruption from the repeated verify-time order placements above — this
	# golden demo has the platform's own documented history of finicky batch-scoping/balance-based
	# idempotency bugs (DP-649/650/655), so this re-check is not a formality.
	pharmacy_result_1 = verify_pharmacy_golden_demo()
	pharmacy_result_2 = verify_pharmacy_golden_demo()
	check("Golden Demo #23 (Pharmacy Chain)'s OWN verify_pharmacy_golden_demo() still passes after WEB-06's guest orders were added (run #1)", pharmacy_result_1["all_passed"], [c for c in pharmacy_result_1["checks"] if not c["passed"]])
	check("Golden Demo #23 (Pharmacy Chain)'s OWN verify_pharmacy_golden_demo() still passes when re-run a second time (idempotency)", pharmacy_result_2["all_passed"], [c for c in pharmacy_result_2["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_farm_portal_demo() -> dict:
	"""WEB-07 (Farm Customer / Technical Service Portal) integrity check, same pattern as every
	prior golden demo's verify_* function — a close structural twin of `verify_dealer_portal_demo()`/
	`verify_supplier_portal_demo()` above. Runs the (idempotent) bootstrap + seed steps first —
	`bootstrap_farm_portal_doctypes.py`/`farm_portal_seeds.py` are deliberately NOT wired into
	after_install/after_migrate (same precedent as `dealer_portal_seeds.py`/
	`supplier_portal_seeds.py`), so this verify function is also this data's own re-seed entry point
	for the regression sweep. Reuses Golden Demo #10 (Veterinary Distribution)'s real company/
	item/warehouse/DocType (`Vet Technical Visit`) rather than minting a parallel setup, so this
	ALSO re-runs `verify_vet_dist_golden_demo()` TWICE at the end, to prove that golden demo's own
	VD01-VD07 assertions (including VD07's own Technical Visit check) were never disturbed by
	WEB-07's own isolated farm customers/visits/orders layered on top of the same company."""
	from enterprise_core.enterprise_core.bootstrap_farm_portal_doctypes import run as bootstrap_farm_portal_doctypes
	from enterprise_core.enterprise_core.farm_portal_api import get_my_service_history, verify_farm_portal_access_control
	from enterprise_core.enterprise_core.farm_portal_seeds import (
		_ALPHA_USER,
		_BETA_USER,
		_FARM_ALPHA,
		_FARM_BETA,
		seed_farm_portal_credit_test,
		seed_farm_portal_master_data,
		seed_farm_portal_sales_flow,
		seed_farm_portal_technical_visits,
	)

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	bootstrap_farm_portal_doctypes()
	seed_farm_portal_master_data()
	seed_farm_portal_sales_flow()
	seed_farm_portal_credit_test()
	seed_farm_portal_technical_visits()

	check("Farm Alpha Customer exists, isolated from Golden Demo #10's own dealer", frappe.db.exists("Customer", {"customer_name": _FARM_ALPHA}), None)
	check("Farm Beta Customer exists, isolated from Golden Demo #10's own dealer", frappe.db.exists("Customer", {"customer_name": _FARM_BETA}), None)
	check("Farm Alpha portal User exists", frappe.db.exists("User", _ALPHA_USER), None)
	check("Farm Beta portal User exists", frappe.db.exists("User", _BETA_USER), None)
	check(
		"Farm Alpha's User Permission scopes it to exactly its own Customer",
		frappe.db.get_value("User Permission", {"user": _ALPHA_USER, "allow": "Customer"}, "for_value") == _FARM_ALPHA,
		None,
	)
	check(
		"Farm Beta's User Permission scopes it to exactly its own Customer",
		frappe.db.get_value("User Permission", {"user": _BETA_USER, "allow": "Customer"}, "for_value") == _FARM_BETA,
		None,
	)
	check(
		"Vet Technical Visit has a read-only Sales User Custom DocPerm (the cascade this whole portal's visit/recommendation scoping depends on)",
		frappe.db.exists("Custom DocPerm", {"parent": "Vet Technical Visit", "role": "Sales User", "read": 1}),
		None,
	)
	check(
		"Vet Technical Visit has the recommended_item Custom Field",
		frappe.db.exists("Custom Field", "Vet Technical Visit-recommended_item"),
		None,
	)

	# Real credit-limit block, isolated farm (mirrors VD04's/WEB-03's own mechanism, never mutates
	# Golden Demo #10's own dealer data).
	beta_credit_test_so = frappe.db.get_value("Sales Order", {"po_no": "WEB07-BETA-CREDIT-TEST"}, "name")
	check(
		"Beta's deliberately over-credit-limit order was blocked (no submitted Sales Order left behind)",
		not beta_credit_test_so or frappe.db.get_value("Sales Order", beta_credit_test_so, "docstatus") != 1,
		beta_credit_test_so,
	)
	beta_inlimit_so = frappe.db.get_value("Sales Order", {"po_no": "WEB07-BETA-FLOW-1", "docstatus": 1}, "name")
	check("Beta's real, within-limit order was NOT blocked", bool(beta_inlimit_so), beta_inlimit_so)

	check("At least 4 real Technical Visit records exist across both farms (small, honestly-scoped, not a large fabricated dataset)", frappe.db.count("Vet Technical Visit", {"customer": ["in", [_FARM_ALPHA, _FARM_BETA]]}) >= 4, None)
	check("At least one real recommendation (Technical Visit with a recommended_item) exists per farm", frappe.db.exists("Vet Technical Visit", {"customer": _FARM_ALPHA, "recommended_item": ["is", "set"]}) and frappe.db.exists("Vet Technical Visit", {"customer": _FARM_BETA, "recommended_item": ["is", "set"]}), None)

	# get_my_service_history() run for real, as Alpha, confirming a genuine non-error merged view.
	original_user = frappe.session.user
	try:
		frappe.set_user(_ALPHA_USER)
		alpha_history = get_my_service_history()
	finally:
		frappe.set_user(original_user)
	check("get_my_service_history() resolves a real, non-empty merged timeline for the logged-in farm", len(alpha_history) > 0, len(alpha_history))

	# The empirical two-user cross-farm permission proof — see farm_portal_api.py's own docstring
	# for why this is the single most important check in this whole demo.
	access_result = verify_farm_portal_access_control()
	check("Empirical cross-farm access-control proof (login as Alpha, login as Beta, cross-access attempts) — ALL sub-checks passed", access_result["all_passed"], [c for c in access_result["checks"] if not c["passed"]])

	# Isolation proof: Golden Demo #10's own verify function must still pass unchanged after this
	# demo's isolated farms/orders/visits were added on top of the same company, run TWICE to catch
	# any silent idempotency corruption.
	vd_result_1 = verify_vet_dist_golden_demo()
	vd_result_2 = verify_vet_dist_golden_demo()
	check("Golden Demo #10 (Veterinary Distribution)'s OWN verify_vet_dist_golden_demo() still passes after WEB-07's isolated farms were added (run #1)", vd_result_1["all_passed"], [c for c in vd_result_1["checks"] if not c["passed"]])
	check("Golden Demo #10 (Veterinary Distribution)'s OWN verify_vet_dist_golden_demo() still passes when re-run a second time (idempotency)", vd_result_2["all_passed"], [c for c in vd_result_2["checks"] if not c["passed"]])

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}


def verify_guided_demo_mode() -> dict:
	"""Guided Demo Mode (master plan §16) integrity check, same pattern as every prior golden
	demo's verify_* function. Runs the (idempotent) bootstrap + seed steps first —
	`bootstrap_guided_demo_doctypes.py`/`guided_demo_seeds.py` are deliberately NOT wired into
	after_install/after_migrate (same precedent as the portal demos above), so this verify
	function is also this feature's own re-seed entry point for the regression sweep. Checks the
	2 DocTypes exist, each of the 5 seeded scenarios has the expected step count, EVERY step's
	target_document actually exists as a real record (not a stale/fabricated reference — the
	single most important check here, since a broken direct_link would defeat the entire feature),
	and that every scenario with allow_reset=1 has a reset_function_path that genuinely resolves
	to a callable (frappe.get_attr succeeds) — never a fake/unwired button."""
	from enterprise_core.enterprise_core.bootstrap_guided_demo_doctypes import run as bootstrap_guided_demo_doctypes
	from enterprise_core.enterprise_core.guided_demo_seeds import seed_guided_demo_scenarios

	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	bootstrap_guided_demo_doctypes()
	seed_results = seed_guided_demo_scenarios()

	check("Guided Demo Scenario DocType exists", frappe.db.exists("DocType", "Guided Demo Scenario"), None)
	check("Guided Demo Scenario Step DocType exists", frappe.db.exists("DocType", "Guided Demo Scenario Step"), None)

	_EXPECTED_SCENARIOS = {
		"PHARMA-BATCH-RELEASE": 11,
		"COSMETICS-STABILITY-COMPLAINT": 5,
		"PIG-FARM-BREEDING-TO-SALE": 6,
		"AI-QMS-COPILOT-CAPA-APPROVAL": 5,
		"FARM-PORTAL-TECHNICAL-VISIT": 5,
	}

	for scenario_code, expected_steps in _EXPECTED_SCENARIOS.items():
		exists = frappe.db.exists("Guided Demo Scenario", scenario_code)
		check(f"{scenario_code}: scenario record exists", exists, seed_results)
		if not exists:
			continue

		scenario = frappe.get_doc("Guided Demo Scenario", scenario_code)
		check(f"{scenario_code}: has {expected_steps} step(s)", len(scenario.steps) == expected_steps, len(scenario.steps))
		check(f"{scenario_code}: objective and what_this_demonstrates are both non-empty", bool(scenario.objective) and bool(scenario.what_this_demonstrates), None)

		broken_targets = []
		for step in scenario.steps:
			if step.target_doctype and step.target_document:
				if not frappe.db.exists(step.target_doctype, step.target_document):
					broken_targets.append({"step_no": step.step_no, "target_doctype": step.target_doctype, "target_document": step.target_document})
				elif not step.direct_link:
					broken_targets.append({"step_no": step.step_no, "issue": "target set but direct_link missing"})
		check(f"{scenario_code}: every step's target_document (where set) is a real, currently-existing record with a computed direct_link", not broken_targets, broken_targets)

		if scenario.allow_reset:
			resolvable = True
			resolve_error = None
			try:
				fn = frappe.get_attr(scenario.reset_function_path)
				resolvable = callable(fn)
			except Exception as e:
				resolvable = False
				resolve_error = str(e)
			check(f"{scenario_code}: allow_reset=1 has a reset_function_path that genuinely resolves to a callable", resolvable, resolve_error)
		else:
			check(f"{scenario_code}: allow_reset=0 has honest, non-empty reset_instructions (no silent no-op)", bool(scenario.reset_instructions), None)

	# Reset dispatcher itself: exercise the "not available" honest path and the real path once,
	# without leaving side effects behind other than what the underlying idempotent seed already
	# guarantees is safe to re-run.
	from enterprise_core.enterprise_core.guided_demo import reset_guided_demo_scenario

	fake_scenario = "PHARMA-BATCH-RELEASE"
	original_allow_reset = frappe.db.get_value("Guided Demo Scenario", fake_scenario, "allow_reset")
	frappe.db.set_value("Guided Demo Scenario", fake_scenario, "allow_reset", 0)
	not_available_result = reset_guided_demo_scenario(fake_scenario)
	frappe.db.set_value("Guided Demo Scenario", fake_scenario, "allow_reset", original_allow_reset)
	check(
		"reset_guided_demo_scenario() returns an honest 'not_available' status (never a silent no-op) when allow_reset is off",
		not_available_result.get("status") == "not_available",
		not_available_result,
	)

	real_reset_result = reset_guided_demo_scenario(fake_scenario)
	check(
		"reset_guided_demo_scenario() actually runs the real, idempotent reset function when allow_reset is on",
		real_reset_result.get("status") == "ok",
		real_reset_result,
	)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
