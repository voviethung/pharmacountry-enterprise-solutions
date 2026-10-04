"""Golden Demo #3 — QMS standalone (master plan DEMO 10), IP-QMS. Unlike Golden Demo #1/#2
(mostly composing existing ERPNext doctypes), this is fresh CE-06 QMS DocTypes
(bootstrap_qms_doctypes.py) + fresh business rules (qms_validations.py). Reuses the DP-405
demo users (qa.manager@/quality.director@pharmacountry.vn etc.) so CAPA owner vs. closer
segregation (Q02) is a real, different person — not a role-play of the same account.
"""

import frappe

_CAPA_OWNER = "qa.manager@pharmacountry.vn"
_CAPA_CLOSER = "quality.director@pharmacountry.vn"


def _ensure_deviation():
	marker = "Cold storage temperature excursion — Warehouse B"
	existing = frappe.db.get_value("QMS Deviation", {"subject": marker}, "name")
	if existing:
		return existing, False
	dev = frappe.get_doc(
		{
			"doctype": "QMS Deviation",
			"subject": marker,
			"description": "Cold storage unit B-02 recorded a 2-hour excursion above the validated temperature range.",
			"severity": "Major",
			"status": "Under Investigation",
			"reported_by": _CAPA_OWNER,
			"investigation_notes": "Maintenance log shows a compressor fault during the excursion window.",
			"root_cause": "Compressor thermostat drift beyond calibration tolerance.",
		}
	)
	dev.insert(ignore_permissions=True)
	return dev.name, True


def _ensure_capa_for_deviation(deviation_name):
	existing = frappe.db.get_value("QMS CAPA", {"source_type": "QMS Deviation", "source_reference": deviation_name}, "name")
	if existing:
		return existing, False
	capa = frappe.get_doc(
		{
			"doctype": "QMS CAPA",
			"subject": "Recalibrate and add redundant monitoring — Cold storage B-02",
			"capa_type": "Both",
			"source_type": "QMS Deviation",
			"source_reference": deviation_name,
			"owner_user": _CAPA_OWNER,
			"due_date": frappe.utils.add_days(frappe.utils.nowdate(), -2),
			"status": "In Progress",
			"action_plan": "Recalibrate compressor thermostat; install a redundant temperature logger with SMS alert.",
		}
	)
	capa.insert(ignore_permissions=True)
	frappe.db.set_value("QMS Deviation", deviation_name, "status", "CAPA Initiated")
	frappe.db.set_value("QMS Deviation", deviation_name, "linked_capa", capa.name)
	return capa.name, True


def _close_capa(capa_name):
	capa = frappe.get_doc("QMS CAPA", capa_name)
	if capa.status == "Closed":
		return False
	capa.status = "Pending Effectiveness Check"
	capa.save(ignore_permissions=True)
	capa.reload()
	capa.effectiveness_check_date = frappe.utils.add_days(capa.due_date, 5)
	capa.effectiveness_evidence = "7 days of post-recalibration logger data show temperature within range; no further excursions."
	capa.closed_by = _CAPA_CLOSER
	capa.status = "Closed"
	capa.save(ignore_permissions=True)
	return True


def seed_deviation_capa_flow():
	"""DP-523 — the master plan's own "Flow mẫu": Deviation -> Investigation -> Root Cause ->
	CAPA -> Effectiveness -> Closure. CAPA owner (qa.manager) and closer (quality.director)
	are deliberately different demo users, satisfying Q02 on the happy path too, not just in
	the negative test (DP-524)."""
	deviation_name, deviation_created = _ensure_deviation()
	capa_name, capa_created = _ensure_capa_for_deviation(deviation_name)
	closed = _close_capa(capa_name)
	if closed:
		frappe.db.set_value("QMS Deviation", deviation_name, "status", "Closed")
	return (
		f"seed_deviation_capa_flow: Deviation {'created' if deviation_created else 'already existed'} ({deviation_name}). "
		f"CAPA {'created' if capa_created else 'already existed'} ({capa_name}). "
		f"Closure {'completed' if closed else 'already done'}."
	)


def _test_q01_deviation_requires_root_cause():
	marker = "Q01-TEST-DEVIATION"
	if frappe.db.exists("QMS Deviation", {"subject": marker}):
		return True
	dev = frappe.get_doc(
		{
			"doctype": "QMS Deviation",
			"subject": marker,
			"severity": "Minor",
			"status": "Open",
			"reported_by": _CAPA_OWNER,
		}
	)
	dev.insert(ignore_permissions=True)
	dev.status = "Closed"
	blocked = False
	try:
		dev.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("Q01 negative test FAILED: Deviation closed without root_cause was not blocked!")
	return True


def _test_q02_owner_cannot_close_own_capa():
	marker = "Q02-TEST-CAPA"
	if frappe.db.exists("QMS CAPA", {"subject": marker}):
		return True
	capa = frappe.get_doc(
		{
			"doctype": "QMS CAPA",
			"subject": marker,
			"capa_type": "Corrective",
			"owner_user": _CAPA_OWNER,
			"due_date": frappe.utils.add_days(frappe.utils.nowdate(), -1),
			"status": "Pending Effectiveness Check",
			"effectiveness_check_date": frappe.utils.nowdate(),
			"effectiveness_evidence": "n/a — negative test",
		}
	)
	capa.insert(ignore_permissions=True)
	capa.status = "Closed"
	capa.closed_by = _CAPA_OWNER  # same as owner_user — should be blocked
	blocked = False
	try:
		capa.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("Q02 negative test FAILED: CAPA closed by its own owner was not blocked!")
	return True


def _test_q04_effectiveness_required():
	marker = "Q04-TEST-CAPA"
	if frappe.db.exists("QMS CAPA", {"subject": marker}):
		return True
	capa = frappe.get_doc(
		{
			"doctype": "QMS CAPA",
			"subject": marker,
			"capa_type": "Corrective",
			"owner_user": _CAPA_OWNER,
			"due_date": frappe.utils.nowdate(),
			"status": "In Progress",
		}
	)
	capa.insert(ignore_permissions=True)
	capa.status = "Closed"  # no effectiveness_check_date / evidence set — should be blocked
	blocked = False
	try:
		capa.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("Q04 negative test FAILED: CAPA closed without effectiveness evidence was not blocked!")
	return True


def seed_qms_validations():
	"""DP-524 — proves Q01 (Deviation needs root_cause to close), Q02 (CAPA owner can't
	close their own CAPA) and Q04 (CAPA needs effectiveness evidence, checked on/after due
	date, to close) actually fire."""
	q01 = _test_q01_deviation_requires_root_cause()
	q02 = _test_q02_owner_cannot_close_own_capa()
	q04 = _test_q04_effectiveness_required()
	return f"seed_qms_validations: Q01 CONFIRMED ({q01}). Q02 CONFIRMED ({q02}). Q04 CONFIRMED ({q04})."


def seed_qms_escalation():
	"""DP-525 — Q03, CAPA due date escalation. Creates one deliberately overdue, still-open
	CAPA, then runs the escalation check (api.escalate_overdue_capas) and verifies it actually
	flips this CAPA's status to Overdue, not just that a query could theoretically find it."""
	marker = "Q03-TEST-OVERDUE-CAPA"
	existing = frappe.db.get_value("QMS CAPA", {"subject": marker}, "name")
	if not existing:
		capa = frappe.get_doc(
			{
				"doctype": "QMS CAPA",
				"subject": marker,
				"capa_type": "Corrective",
				"owner_user": _CAPA_OWNER,
				"due_date": frappe.utils.add_days(frappe.utils.nowdate(), -30),
				"status": "In Progress",
			}
		)
		capa.insert(ignore_permissions=True)
		existing = capa.name

	from enterprise_core.enterprise_core.api import escalate_overdue_capas

	escalated = escalate_overdue_capas()
	current_status = frappe.db.get_value("QMS CAPA", existing, "status")
	if current_status != "Overdue":
		frappe.throw(f"Q03 negative test FAILED: CAPA {existing} due 30 days ago was not escalated (status={current_status}).")
	return f"seed_qms_escalation: overdue CAPA {existing} escalated to 'Overdue'. Total escalated this run: {escalated}."


def seed_qms_change_control():
	"""DP-526 — Q05, "Change impacts documents/training/equipment." One Change Control
	record with all three impact flags set, moved Draft -> Under Review -> Approved."""
	marker = "Replace cold storage compressor thermostat — Warehouse B"
	existing = frappe.db.get_value("QMS Change Control", {"subject": marker}, "name")
	if existing:
		return f"seed_qms_change_control: already existed ({existing})."
	cc = frappe.get_doc(
		{
			"doctype": "QMS Change Control",
			"subject": marker,
			"change_type": "Equipment",
			"reason": "Root cause of the cold storage deviation (DP-523) — thermostat drift beyond calibration tolerance.",
			"status": "Under Review",
			"impacts_documents": 1,
			"impacts_training": 1,
			"impacts_equipment": 1,
			"impact_notes": "SOP-WH-02 (cold chain monitoring) needs revision; warehouse staff need refresher training; new logger hardware needs qualification.",
		}
	)
	cc.insert(ignore_permissions=True)
	cc.status = "Approved"
	cc.approved_by = _CAPA_CLOSER
	cc.save(ignore_permissions=True)
	return f"seed_qms_change_control: created and approved ({cc.name})."


def seed_qms_oos_oot():
	"""DP-527 — Q06, "OOS can create CAPA/deviation." An OOS result linked to both a fresh
	CAPA and a fresh Deviation, proving the cross-module creation the master plan calls for.
	Each sub-step is checked independently (not just "does the OOS record exist") so a
	partial prior failure can resume instead of silently reporting "already existed" while
	permanently missing its CAPA/Deviation links — found via a real partial failure during
	development (the source_type bug below left an OOS record with no links)."""
	marker = "PARA-500-TAB potency assay — Batch QC-2026-EXT"
	oos_name = frappe.db.get_value("QMS OOS OOT", {"subject": marker}, "name")
	if not oos_name:
		oos = frappe.get_doc(
			{
				"doctype": "QMS OOS OOT",
				"subject": marker,
				"result_type": "OOS",
				"test_reference": "Potency Assay",
				"result_value": "94.2%",
				"specification": "95.0% - 105.0%",
				"status": "Investigated",
			}
		)
		oos.insert(ignore_permissions=True)
		oos_name = oos.name

	dev_name = frappe.db.get_value("QMS Deviation", {"subject": f"Deviation raised from OOS — {marker}"}, "name")
	if not dev_name:
		dev = frappe.get_doc(
			{
				"doctype": "QMS Deviation",
				"subject": f"Deviation raised from OOS — {marker}",
				"severity": "Major",
				"status": "Under Investigation",
				"reported_by": _CAPA_OWNER,
				"investigation_notes": "Raised automatically from OOS result outside potency specification.",
			}
		)
		dev.insert(ignore_permissions=True)
		dev_name = dev.name

	capa_name = frappe.db.get_value("QMS CAPA", {"source_type": "QMS OOS OOT", "source_reference": oos_name}, "name")
	if not capa_name:
		capa = frappe.get_doc(
			{
				"doctype": "QMS CAPA",
				"subject": f"Investigate potency OOS — {marker}",
				"capa_type": "Corrective",
				"source_type": "QMS OOS OOT",
				"source_reference": oos_name,
				"owner_user": _CAPA_OWNER,
				"due_date": frappe.utils.add_days(frappe.utils.nowdate(), 14),
				"status": "Open",
			}
		)
		capa.insert(ignore_permissions=True)
		capa_name = capa.name

	if not frappe.db.get_value("QMS OOS OOT", oos_name, "linked_capa"):
		frappe.db.set_value("QMS OOS OOT", oos_name, {"linked_capa": capa_name, "linked_deviation": dev_name, "status": "CAPA Created"})

	return f"seed_qms_oos_oot: OOS {oos_name}, Deviation {dev_name}, CAPA {capa_name} — all linked."


def seed_qms_audit():
	"""DP-528 — Q07, "Audit finding → CAPA." An Audit with one Major finding, linked to a
	fresh CAPA. Findings are child rows of Audit (not independently addressable doctype
	records), so the CAPA's source_reference points at the parent Audit, documented as such."""
	marker = "Internal GMP Audit — Q3 2026"
	audit_name = frappe.db.get_value("QMS Audit", {"subject": marker}, "name")
	if not audit_name:
		audit = frappe.get_doc(
			{
				"doctype": "QMS Audit",
				"subject": marker,
				"audit_type": "Internal",
				"auditor": "Nguyen Van A (Internal QA)",
				"status": "Completed",
				"findings": [
					{
						"finding": "Cold storage temperature logs for Warehouse B were not reviewed within the SOP-mandated 24-hour window on 3 occasions.",
						"severity": "Major",
					}
				],
			}
		)
		audit.insert(ignore_permissions=True)
		audit_name = audit.name

	capa_name = frappe.db.get_value("QMS CAPA", {"source_type": "QMS Audit", "source_reference": audit_name}, "name")
	if not capa_name:
		capa = frappe.get_doc(
			{
				"doctype": "QMS CAPA",
				"subject": f"Enforce 24h cold storage log review — {marker}",
				"capa_type": "Preventive",
				"source_type": "QMS Audit",
				"source_reference": audit_name,
				"owner_user": _CAPA_OWNER,
				"due_date": frappe.utils.add_days(frappe.utils.nowdate(), 21),
				"status": "Open",
			}
		)
		capa.insert(ignore_permissions=True)
		capa_name = capa.name

	audit = frappe.get_doc("QMS Audit", audit_name)
	if not audit.findings[0].linked_capa:
		audit.findings[0].linked_capa = capa_name
		audit.save(ignore_permissions=True)

	return f"seed_qms_audit: Audit {audit_name} with 1 finding, linked to CAPA {capa_name}."


def seed_qms_recall_risk_supplier():
	"""DP-529 — master data completeness for the remaining 3 of the 9 QMS modules (Recall,
	Risk, Supplier Quality) that don't have their own numbered Q0x test."""
	created = []

	if not frappe.db.exists("QMS Recall", {"subject": "Voluntary recall — Batch 552242D (demo)"}):
		frappe.get_doc(
			{
				"doctype": "QMS Recall",
				"subject": "Voluntary recall — Batch 552242D (demo)",
				"batch_reference": "552242D",
				"reason": "Illustrative recall record for the QMS standalone demo — not a real product issue.",
				"status": "Completed",
				"customers_notified": 1,
			}
		).insert(ignore_permissions=True)
		created.append("Recall")

	if not frappe.db.exists("QMS Risk", {"subject": "Single cold storage unit — no redundancy"}):
		risk = frappe.get_doc(
			{
				"doctype": "QMS Risk",
				"subject": "Single cold storage unit — no redundancy",
				"risk_category": "Equipment",
				"likelihood": "Medium",
				"impact": "High",
				"mitigation": "DP-526 change control adds a redundant temperature logger with SMS alert.",
				"status": "Mitigated",
			}
		)
		_LEVEL = {"Low": 1, "Medium": 2, "High": 3}
		risk.risk_score = _LEVEL[risk.likelihood] * _LEVEL[risk.impact]
		risk.insert(ignore_permissions=True)
		created.append("Risk")

	if not frappe.db.exists("QMS Supplier Quality", "ABC Pharma Chemicals Co."):
		frappe.get_doc(
			{
				"doctype": "QMS Supplier Quality",
				"supplier_name": "ABC Pharma Chemicals Co.",
				"quality_score": 92,
				"last_audit_date": frappe.utils.add_months(frappe.utils.nowdate(), -6),
				"status": "Approved",
			}
		).insert(ignore_permissions=True)
		created.append("Supplier Quality")

	return f"seed_qms_recall_risk_supplier: created {created or 'nothing new (all already existed)'}."
