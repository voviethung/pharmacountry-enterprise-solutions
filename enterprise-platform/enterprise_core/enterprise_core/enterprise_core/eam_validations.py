"""Golden Demo #6 (EAM/CMMS/Calibration/Validation standalone, master plan DEMO 13)
business rule — E06, "Equipment status prevents unauthorized use." Interpreted concretely as:
equipment can't be qualified (put back into authorized use) while its calibration is
overdue — ties E02/E05/E06 together into one real rule rather than three disconnected ones.
"""

import frappe
from frappe import _


def eam_qualification_validate(doc, method):
	if doc.status != "Qualified":
		return
	# ordered by calibration_date (when it was actually performed), not due_date — the most
	# RECENT calibration event supersedes an older one regardless of which has the
	# further-future due_date value; getting recalibrated always resets the clock.
	latest_due = frappe.db.get_value(
		"EAM Calibration Record", {"asset": doc.asset, "result": "Pass"}, "due_date", order_by="calibration_date desc, creation desc"
	)
	if not latest_due:
		frappe.throw(
			_("Cannot qualify Asset {0} — no passing calibration record exists.").format(doc.asset),
			title=_("E06: Calibration Required"),
		)
	if frappe.utils.getdate(latest_due) < frappe.utils.getdate():
		frappe.throw(
			_("Cannot qualify Asset {0} — its calibration was due {1} and is overdue. Equipment status prevents unauthorized use until recalibrated.").format(
				doc.asset, latest_due
			),
			title=_("E06: Calibration Overdue"),
		)
