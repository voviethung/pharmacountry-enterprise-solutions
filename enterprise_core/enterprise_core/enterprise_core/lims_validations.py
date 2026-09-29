"""Golden Demo #5 (LIMS / QC Laboratory standalone, master plan DEMO 12) business rules —
L01/L02/L03/L04/L06/L07/L08.
"""

import frappe
from frappe import _


def lims_sample_validate(doc, method):
	"""L01 — sample uniqueness: not Frappe's own primary-key uniqueness (trivial, always
	true), but a real business rule — no two samples for the same batch+type on the same
	received_date (prevents accidental double-logging of the same physical sample)."""
	duplicate = frappe.db.exists(
		"LIMS Sample",
		{
			"batch_reference": doc.batch_reference,
			"sample_type": doc.sample_type,
			"received_date": doc.received_date,
			"name": ["!=", doc.name or ""],
		},
	)
	if duplicate:
		frappe.throw(
			_("A sample for batch {0}, type {1}, received {2} already exists ({3}).").format(
				doc.batch_reference, doc.sample_type, doc.received_date, duplicate
			),
			title=_("L01: Duplicate Sample"),
		)


def lims_test_validate(doc, method):
	"""L02 — only Effective spec/method usable. L03 — analyst segregation: reviewer/approver
	can't be the same person as the analyst who ran the test. L04 — pass/fail is always
	recomputed from the spec bounds, never trusted as manually entered (reproducible).
	L06 — once Reviewed or later, result values become immutable. L08 — the instrument's
	calibration must not be overdue."""
	if doc.status in ("Assigned", "In Progress"):
		spec_status = frappe.db.get_value("LIMS Specification", doc.specification, "status")
		if spec_status != "Effective":
			frappe.throw(
				_("Cannot use Specification {0} — status is '{1}', must be Effective.").format(doc.specification, spec_status),
				title=_("L02: Specification Not Effective"),
			)
		method_status = frappe.db.get_value("LIMS Test Method", doc.method, "status")
		if method_status != "Effective":
			frappe.throw(
				_("Cannot use Test Method {0} — status is '{1}', must be Effective.").format(doc.method, method_status),
				title=_("L02: Method Not Effective"),
			)

	if doc.instrument:
		calibration_due = frappe.db.get_value("LIMS Instrument", doc.instrument, "calibration_due_date")
		if calibration_due and frappe.utils.getdate(calibration_due) < frappe.utils.getdate():
			frappe.throw(
				_("Cannot use Instrument {0} — calibration was due {1} and is overdue.").format(doc.instrument, calibration_due),
				title=_("L08: Instrument Calibration Overdue"),
			)

	if doc.results:
		spec_params = {
			row.parameter_name: (row.min_value, row.max_value)
			for row in frappe.get_doc("LIMS Specification", doc.specification).parameters
		}
		for row in doc.results:
			bounds = spec_params.get(row.parameter_name)
			if bounds and row.result_value is not None:
				min_value, max_value = bounds
				row.pass_fail = "Pass" if min_value <= row.result_value <= max_value else "Fail"

	if not doc.is_new():
		before_status = frappe.db.get_value("LIMS Test", doc.name, "status")
		if before_status in ("Reviewed", "Approved"):
			before_results = {r.parameter_name: r.result_value for r in frappe.get_doc("LIMS Test", doc.name).results}
			for row in doc.results:
				if row.parameter_name in before_results and before_results[row.parameter_name] != row.result_value:
					frappe.throw(
						_("Cannot edit result for {0} — this Test has already been Reviewed. Result values are locked.").format(row.parameter_name),
						title=_("L06: Reviewed Result Locked"),
					)

	if doc.status in ("Reviewed", "Approved") and doc.reviewed_by and doc.reviewed_by == doc.analyst:
		frappe.throw(
			_("Cannot review Test {0} — the reviewer ({1}) cannot also be the analyst who ran the test.").format(doc.name, doc.analyst),
			title=_("L03: Analyst Segregation"),
		)


def lims_test_on_update(doc, method):
	"""L05 — OOS trigger: any Fail result creates a real QMS OOS OOT record (Golden Demo #3's
	module — one shared OOS/OOT concept, not a parallel LIMS-only one)."""
	if doc.oos_triggered:
		return
	has_fail = any(row.pass_fail == "Fail" for row in doc.results)
	if not has_fail:
		return

	oos = frappe.get_doc(
		{
			"doctype": "QMS OOS OOT",
			"subject": f"OOS triggered by LIMS Test {doc.name} (sample {doc.sample})",
			"result_type": "OOS",
			"test_reference": doc.name,
			"status": "Open",
		}
	)
	oos.insert(ignore_permissions=True)
	# doc.db_set(), not frappe.db.set_value() — the latter updates the DB row's `modified`
	# timestamp but not the in-memory `doc` still held by whatever code called save() (this
	# hook runs from inside save()'s own on_update step), so a subsequent operation on that
	# same in-memory doc within the same request sees a stale timestamp and gets rejected
	# with TimestampMismatchError. db_set() keeps both in sync.
	doc.db_set({"oos_triggered": 1, "linked_oos": oos.name}, update_modified=False)


def lims_coa_validate(doc, method):
	"""L07 — a COA can only reference an Approved LIMS Test."""
	test_status = frappe.db.get_value("LIMS Test", doc.test, "status")
	if doc.status == "Approved" and test_status != "Approved":
		frappe.throw(
			_("Cannot approve COA {0} — the underlying LIMS Test {1} is '{2}', must be Approved first.").format(
				doc.name, doc.test, test_status
			),
			title=_("L07: COA Requires Approved Test"),
		)
