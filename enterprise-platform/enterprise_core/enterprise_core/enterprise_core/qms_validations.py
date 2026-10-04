"""Golden Demo #3 (QMS standalone, master plan DEMO 10) business rules — Q01/Q02/Q04.
Fresh logic for the standalone QMS product, not shared with Golden Demo #1's Pharma-scoped
DP-503/DP-506 hooks (validations.py) even though the shape (stage-gating, segregation of
duties) rhymes with those.
"""

import frappe
from frappe import _


def qms_deviation_validate(doc, method):
	"""Q01 — required fields by stage: a Deviation can't move to Closed without root_cause
	on record (you can't close what was never investigated)."""
	if doc.status == "Closed" and not doc.root_cause:
		frappe.throw(
			_("Cannot close Deviation {0} without a recorded Root Cause.").format(doc.name),
			title=_("Q01: Required Field Missing"),
		)


def qms_capa_validate(doc, method):
	"""Q02 — segregation of duties: the CAPA owner cannot also be the one who closes it.
	Q04 — effectiveness cannot close before due date, and not without recorded evidence."""
	if doc.status == "Closed":
		if not doc.effectiveness_check_date or not doc.effectiveness_evidence:
			frappe.throw(
				_("Cannot close CAPA {0} without an effectiveness check date and evidence.").format(doc.name),
				title=_("Q04: Effectiveness Required"),
			)
		if frappe.utils.getdate(doc.effectiveness_check_date) < frappe.utils.getdate(doc.due_date):
			frappe.throw(
				_("Cannot close CAPA {0} — effectiveness check date ({1}) is before the due date ({2}).").format(
					doc.name, doc.effectiveness_check_date, doc.due_date
				),
				title=_("Q04: Effectiveness Before Due Date"),
			)
		if doc.closed_by and doc.closed_by == doc.owner_user:
			frappe.throw(
				_("Cannot close CAPA {0} — the CAPA owner ({1}) cannot also close it. Segregation of duties requires a different approver.").format(
					doc.name, doc.owner_user
				),
				title=_("Q02: Segregation of Duties"),
			)
