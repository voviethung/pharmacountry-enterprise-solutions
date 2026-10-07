# Copyright (c) 2026, Enterprise Platform and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TenantSubscription(Document):
	def log_event(self, event_type: str, note: str = "") -> None:
		"""Appends one row to this Tenant Subscription's own Events table and saves — the audit
		trail paypal_billing.py's webhook handler relies on to show a human exactly what
		happened and when, without needing to cross-reference PayPal's own dashboard."""
		self.append("events", {"event_time": now_datetime(), "event_type": event_type, "note": note})
		self.save(ignore_permissions=True)
		frappe.db.commit()
