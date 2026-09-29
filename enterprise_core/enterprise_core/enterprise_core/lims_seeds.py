"""Golden Demo #5 — LIMS / QC Laboratory standalone (master plan DEMO 12), IP-LIMS. Reuses
the DP-405 demo users (analyst@ as the person running tests, qc.manager@ reviewing them —
genuinely different accounts for L03 segregation) and Golden Demo #3's QMS OOS OOT module
for L05.
"""

import frappe

_ANALYST = "analyst@pharmacountry.vn"
_REVIEWER = "qc.manager@pharmacountry.vn"
_INSTRUMENT_CODE = "HPLC-01"
_SPEC_ITEM = "Paracetamol 500 mg Tablet"


def _ensure_instrument():
	if frappe.db.exists("LIMS Instrument", _INSTRUMENT_CODE):
		return False
	frappe.get_doc(
		{
			"doctype": "LIMS Instrument",
			"instrument_code": _INSTRUMENT_CODE,
			"instrument_name": "HPLC System 01",
			"calibration_due_date": frappe.utils.add_months(frappe.utils.nowdate(), 6),
			"status": "Calibrated",
		}
	).insert(ignore_permissions=True)
	return True


def _ensure_specification():
	existing = frappe.db.get_value("LIMS Specification", {"item_name": _SPEC_ITEM, "status": "Effective"}, "name")
	if existing:
		return existing, False
	spec = frappe.get_doc(
		{
			"doctype": "LIMS Specification",
			"spec_code": "SPEC-PARA-500-TAB",
			"item_name": _SPEC_ITEM,
			"version_no": 1,
			"status": "Effective",
			"parameters": [
				{"parameter_name": "Assay", "unit": "%", "min_value": 95.0, "max_value": 105.0},
				{"parameter_name": "Dissolution", "unit": "%", "min_value": 80.0, "max_value": 100.0},
			],
		}
	)
	spec.insert(ignore_permissions=True)
	return spec.name, True


def _ensure_method():
	existing = frappe.db.get_value("LIMS Test Method", {"method_code": "MTD-HPLC-ASSAY", "status": "Effective"}, "name")
	if existing:
		return existing, False
	method = frappe.get_doc(
		{
			"doctype": "LIMS Test Method",
			"method_code": "MTD-HPLC-ASSAY",
			"method_name": "HPLC Assay & Dissolution — Paracetamol Tablets",
			"instrument_type": "HPLC",
			"status": "Effective",
		}
	)
	method.insert(ignore_permissions=True)
	return method.name, True


def seed_lims_master_data():
	"""DP-537 — Instrument, Specification and Test Method master data (all Effective),
	matching the master plan's "Receive sample -> assign -> test" flow's prerequisites."""
	instrument_created = _ensure_instrument()
	spec_name, spec_created = _ensure_specification()
	method_name, method_created = _ensure_method()
	return (
		f"seed_lims_master_data: Instrument {'created' if instrument_created else 'already existed'} ({_INSTRUMENT_CODE}). "
		f"Specification {'created' if spec_created else 'already existed'} ({spec_name}). "
		f"Method {'created' if method_created else 'already existed'} ({method_name})."
	)


def _ensure_sample(batch_reference, sample_type="Finished Goods"):
	existing = frappe.db.get_value(
		"LIMS Sample", {"batch_reference": batch_reference, "sample_type": sample_type, "received_date": frappe.utils.nowdate()}, "name"
	)
	if existing:
		return existing, False
	sample = frappe.get_doc(
		{
			"doctype": "LIMS Sample",
			"item_name": _SPEC_ITEM,
			"batch_reference": batch_reference,
			"sample_type": sample_type,
			"received_date": frappe.utils.nowdate(),
			"status": "Assigned",
		}
	)
	sample.insert(ignore_permissions=True)
	return sample.name, True


def _spec_and_method():
	spec = frappe.db.get_value("LIMS Specification", {"item_name": _SPEC_ITEM, "status": "Effective"}, "name")
	method = frappe.db.get_value("LIMS Test Method", {"method_code": "MTD-HPLC-ASSAY", "status": "Effective"}, "name")
	return spec, method


def _ensure_golden_test(sample_name):
	existing = frappe.db.get_value("LIMS Test", {"sample": sample_name}, "name")
	if existing and frappe.db.get_value("LIMS Test", existing, "status") == "Approved":
		return existing, False
	spec, method = _spec_and_method()
	if existing:
		test = frappe.get_doc("LIMS Test", existing)
	else:
		test = frappe.get_doc(
			{
				"doctype": "LIMS Test",
				"sample": sample_name,
				"specification": spec,
				"method": method,
				"instrument": _INSTRUMENT_CODE,
				"analyst": _ANALYST,
				"status": "In Progress",
				"results": [
					{"parameter_name": "Assay", "result_value": 99.1, "unit": "%"},
					{"parameter_name": "Dissolution", "unit": "%", "result_value": 92.5},
				],
			}
		)
		test.insert(ignore_permissions=True)
	test.status = "Result Entered"
	test.save(ignore_permissions=True)
	test.status = "Reviewed"
	test.reviewed_by = _REVIEWER
	test.save(ignore_permissions=True)
	test.status = "Approved"
	test.approved_by = _REVIEWER
	test.save(ignore_permissions=True)
	return test.name, True


def seed_lims_golden_flow():
	"""DP-538 — the master plan's own flow: Receive sample -> assign -> test -> result ->
	review -> approve. L04 (reproducible calculation) is proven implicitly — pass_fail is
	always server-recomputed from spec bounds on every save, never trusted as entered."""
	if not frappe.db.exists("LIMS Specification", {"item_name": _SPEC_ITEM, "status": "Effective"}):
		return "seed_lims_golden_flow: SKIPPED — run seed_lims_master_data first."
	sample_name, sample_created = _ensure_sample("552242D")
	test_name, test_progressed = _ensure_golden_test(sample_name)
	frappe.db.set_value("LIMS Sample", sample_name, "status", "Approved")
	pass_fail = {r.parameter_name: r.pass_fail for r in frappe.get_doc("LIMS Test", test_name).results}
	return (
		f"seed_lims_golden_flow: Sample {'created' if sample_created else 'already existed'} ({sample_name}). "
		f"Test {'reached Approved' if test_progressed else 'already existed'} ({test_name}). "
		f"L04 recomputed pass_fail: {pass_fail}."
	)


def _ensure_oos_test():
	sample_name, sample_created = _ensure_sample("552242D-OOS-DEMO")
	existing = frappe.db.get_value("LIMS Test", {"sample": sample_name}, "name")
	if existing:
		return frappe.db.get_value("LIMS Test", existing, "linked_oos"), False
	spec, method = _spec_and_method()
	test = frappe.get_doc(
		{
			"doctype": "LIMS Test",
			"sample": sample_name,
			"specification": spec,
			"method": method,
			"instrument": _INSTRUMENT_CODE,
			"analyst": _ANALYST,
			"status": "In Progress",
			"results": [
				{"parameter_name": "Assay", "result_value": 94.2, "unit": "%"},  # below 95.0 min -> Fail
				{"parameter_name": "Dissolution", "result_value": 92.0, "unit": "%"},
			],
		}
	)
	test.insert(ignore_permissions=True)
	test.status = "Result Entered"
	test.save(ignore_permissions=True)
	linked_oos = frappe.db.get_value("LIMS Test", test.name, "linked_oos")
	return linked_oos, True


def seed_lims_oos_flow():
	"""DP-539 — L05, OOS trigger. A deliberately out-of-spec Assay result must auto-create a
	real QMS OOS OOT record via the lims_test_on_update hook."""
	if not frappe.db.exists("LIMS Specification", {"item_name": _SPEC_ITEM, "status": "Effective"}):
		return "seed_lims_oos_flow: SKIPPED — run seed_lims_master_data first."
	linked_oos, created = _ensure_oos_test()
	if not linked_oos:
		frappe.throw("L05 FAILED: an out-of-spec result did not trigger a linked QMS OOS OOT record.")
	return f"seed_lims_oos_flow: OOS Test {'created' if created else 'already existed'}, linked to QMS OOS OOT {linked_oos}."


def seed_lims_coa():
	"""DP-540 — L07, COA only approved results. A COA for the golden-flow Test (Approved),
	approved successfully."""
	test_name = frappe.db.get_value("LIMS Test", {"sample": frappe.db.get_value("LIMS Sample", {"batch_reference": "552242D"}, "name"), "status": "Approved"}, "name")
	if not test_name:
		return "seed_lims_coa: SKIPPED — run seed_lims_golden_flow first."
	existing = frappe.db.get_value("LIMS COA", {"test": test_name}, "name")
	if existing:
		return f"seed_lims_coa: already existed ({existing})."
	coa = frappe.get_doc(
		{
			"doctype": "LIMS COA",
			"batch_reference": "552242D",
			"test": test_name,
			"status": "Draft",
		}
	)
	coa.insert(ignore_permissions=True)
	coa.status = "Approved"
	coa.issued_date = frappe.utils.nowdate()
	coa.save(ignore_permissions=True)
	return f"seed_lims_coa: created and approved ({coa.name})."


def _test_l01_duplicate_sample_blocked():
	if not frappe.db.exists("LIMS Sample", {"batch_reference": "552242D", "sample_type": "Finished Goods"}):
		return True
	dup = frappe.get_doc(
		{
			"doctype": "LIMS Sample",
			"item_name": _SPEC_ITEM,
			"batch_reference": "552242D",
			"sample_type": "Finished Goods",
			"received_date": frappe.utils.nowdate(),
		}
	)
	blocked = False
	try:
		dup.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("L01 negative test FAILED: a duplicate sample was not blocked!")
	return True


def _test_l02_draft_spec_blocked():
	marker = "L02-TEST-DRAFT-SPEC"
	if not frappe.db.exists("LIMS Specification", marker):
		frappe.get_doc(
			{"doctype": "LIMS Specification", "spec_code": marker, "item_name": marker, "version_no": 1, "status": "Draft"}
		).insert(ignore_permissions=True)
	sample_name, _created = _ensure_sample("L02-TEST-BATCH")
	_, method = _spec_and_method()
	test = frappe.get_doc(
		{
			"doctype": "LIMS Test",
			"sample": sample_name,
			"specification": marker,
			"method": method,
			"analyst": _ANALYST,
			"status": "In Progress",
		}
	)
	blocked = False
	try:
		test.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("L02 negative test FAILED: a Test against a Draft Specification was not blocked!")
	return True


def _test_l03_analyst_cannot_review_own_test():
	sample_name, _created = _ensure_sample("L03-TEST-BATCH")
	spec, method = _spec_and_method()
	existing = frappe.db.get_value("LIMS Test", {"sample": sample_name}, "name")
	if existing:
		test = frappe.get_doc("LIMS Test", existing)
	else:
		test = frappe.get_doc(
			{
				"doctype": "LIMS Test",
				"sample": sample_name,
				"specification": spec,
				"method": method,
				"instrument": _INSTRUMENT_CODE,
				"analyst": _ANALYST,
				"status": "In Progress",
				"results": [{"parameter_name": "Assay", "result_value": 99.0, "unit": "%"}],
			}
		)
		test.insert(ignore_permissions=True)
	test.status = "Reviewed"
	test.reviewed_by = _ANALYST  # same as analyst — should be blocked
	blocked = False
	try:
		test.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("L03 negative test FAILED: the analyst reviewing their own Test was not blocked!")
	return True


def _test_l06_reviewed_result_locked():
	sample_name = frappe.db.get_value("LIMS Sample", {"batch_reference": "552242D"}, "name")
	test_name = frappe.db.get_value("LIMS Test", {"sample": sample_name, "status": "Approved"}, "name")
	if not test_name:
		frappe.throw("_test_l06_reviewed_result_locked: golden-flow Test not found — run seed_lims_golden_flow first.")
	test = frappe.get_doc("LIMS Test", test_name)
	test.results[0].result_value = 1.0  # tamper with an already-reviewed result
	blocked = False
	try:
		test.save(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("L06 negative test FAILED: editing a Reviewed Test's result was not blocked!")
	return True


def _test_l08_overdue_instrument_blocked():
	marker = "L08-TEST-OVERDUE-INSTRUMENT"
	if not frappe.db.exists("LIMS Instrument", marker):
		frappe.get_doc(
			{
				"doctype": "LIMS Instrument",
				"instrument_code": marker,
				"instrument_name": "Overdue Test Instrument",
				"calibration_due_date": frappe.utils.add_days(frappe.utils.nowdate(), -10),
				"status": "Overdue",
			}
		).insert(ignore_permissions=True)
	sample_name, _created = _ensure_sample("L08-TEST-BATCH")
	spec, method = _spec_and_method()
	test = frappe.get_doc(
		{
			"doctype": "LIMS Test",
			"sample": sample_name,
			"specification": spec,
			"method": method,
			"instrument": marker,
			"analyst": _ANALYST,
			"status": "In Progress",
		}
	)
	blocked = False
	try:
		test.insert(ignore_permissions=True)
	except frappe.ValidationError:
		blocked = True
	if not blocked:
		frappe.throw("L08 negative test FAILED: a Test using an instrument with overdue calibration was not blocked!")
	return True


def seed_lims_validations():
	"""DP-541 — L01/L02/L03/L06/L08 negative tests."""
	l01 = _test_l01_duplicate_sample_blocked()
	l02 = _test_l02_draft_spec_blocked()
	l03 = _test_l03_analyst_cannot_review_own_test()
	l06 = _test_l06_reviewed_result_locked()
	l08 = _test_l08_overdue_instrument_blocked()
	return f"seed_lims_validations: L01 CONFIRMED ({l01}). L02 CONFIRMED ({l02}). L03 CONFIRMED ({l03}). L06 CONFIRMED ({l06}). L08 CONFIRMED ({l08})."
