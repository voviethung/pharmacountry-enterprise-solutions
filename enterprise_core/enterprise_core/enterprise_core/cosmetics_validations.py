"""Golden Demo #21 (Cosmetics Manufacturing, master plan DEMO 03) business rules — C04.
"""

import frappe


def cosmetics_stability_sample_validate(doc, method):
	"""C04 — stability sample status (Scheduled/Tested/Overdue) is always server-computed,
	never manually set, same pattern as every prior golden demo's vaccination-style due/overdue
	field."""
	if doc.test_date:
		doc.status = "Tested"
	elif doc.scheduled_date and frappe.utils.getdate(doc.scheduled_date) < frappe.utils.getdate(frappe.utils.nowdate()):
		doc.status = "Overdue"
	else:
		doc.status = "Scheduled"
