"""Golden Demo #10 — Veterinary Distribution (master plan DEMO 16), IP-VETERINARY (same pack
as Golden Demo #9 — manufacturing and distribution share one industry pack, same as
Pharma's #1/#2). Sells Golden Demo #9's OXYTET-200-INJ from FG Released - DVP.
"""

import frappe

_COMPANY_NAME = "Demo Vet Pharma Co."
_FG_ITEM = "OXYTET-200-INJ"
_FG_RELEASED = "FG Released - DVP"
_TERRITORY = "Mekong Delta Region"
_SALES_PERSON = "Tran Van Rep (Vet Demo)"
_DEALER_NAME = "VetCare Mekong Dealer Co."


_MONTHLY_DISTRIBUTION = "Standard Distribution (Vet Demo)"


def _ensure_territory_and_sales_person():
	if not frappe.db.exists("Sales Person", _SALES_PERSON):
		frappe.get_doc({"doctype": "Sales Person", "sales_person_name": _SALES_PERSON, "is_group": 0, "parent_sales_person": "Sales Team"}).insert(
			ignore_permissions=True
		)
	if not frappe.db.exists("Monthly Distribution", _MONTHLY_DISTRIBUTION):
		months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
		frappe.get_doc(
			{
				"doctype": "Monthly Distribution",
				"distribution_id": _MONTHLY_DISTRIBUTION,
				"fiscal_year": "2026",
				"percentages": [{"month": m, "percentage_allocation": 100.0 / 12} for m in months],
			}
		).insert(ignore_permissions=True)
	territory_created = False
	if not frappe.db.exists("Territory", _TERRITORY):
		frappe.get_doc(
			{
				"doctype": "Territory",
				"territory_name": _TERRITORY,
				"parent_territory": "All Territories",
				"is_group": 0,
				"territory_manager": _SALES_PERSON,
				"targets": [{"item_group": "All Item Groups", "fiscal_year": "2026", "distribution_id": _MONTHLY_DISTRIBUTION, "target_qty": 5000, "target_amount": 500000000}],
			}
		).insert(ignore_permissions=True)
		territory_created = True
	return territory_created


_CUSTOMER_GROUP = "Veterinary Dealers"


def _ensure_dealer_and_customer():
	if not frappe.db.exists("Sales Partner", _DEALER_NAME):
		frappe.get_doc({"doctype": "Sales Partner", "partner_name": _DEALER_NAME, "territory": _TERRITORY, "commission_rate": 5}).insert(
			ignore_permissions=True
		)
	if not frappe.db.exists("Customer Group", _CUSTOMER_GROUP):
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": _CUSTOMER_GROUP, "parent_customer_group": "All Customer Groups", "is_group": 0}).insert(
			ignore_permissions=True
		)
	customer_created = False
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_NAME}):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": _DEALER_NAME,
				"customer_type": "Company",
				"customer_group": _CUSTOMER_GROUP,
				"territory": _TERRITORY,
				"default_sales_partner": _DEALER_NAME,
			}
		).insert(ignore_permissions=True)
		customer_created = True
	return customer_created


def seed_vet_dist_master_data():
	"""DP-566 — VD01 (territory ownership — native Territory.territory_manager) + VD05
	(sales target — native Territory.targets) + VD02 (dealer — native Sales Partner)."""
	if not frappe.db.exists("Item", _FG_ITEM):
		return "seed_vet_dist_master_data: SKIPPED — run Golden Demo #9's seed_vet_mfg_master_data first."
	territory_created = _ensure_territory_and_sales_person()
	customer_created = _ensure_dealer_and_customer()
	return f"seed_vet_dist_master_data: Territory {'created' if territory_created else 'already existed'}. Dealer/Customer {'created' if customer_created else 'already existed'}."


def _ensure_sales_order_and_delivery():
	existing_so = frappe.db.exists("Sales Order", {"customer": _DEALER_NAME, "docstatus": 1})
	if existing_so:
		so_name = existing_so
		so_created = False
	else:
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": _DEALER_NAME,
				"company": _COMPANY_NAME,
				"territory": _TERRITORY,
				"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
				"items": [{"item_code": _FG_ITEM, "qty": 100, "warehouse": _FG_RELEASED, "rate": 180000}],
			}
		)
		so.insert(ignore_permissions=True)
		so.submit()
		so_name = so.name
		so_created = True

	dn_created = False
	if not frappe.db.exists("Delivery Note", {"against_sales_order": so_name, "docstatus": 1}):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

		dn = make_delivery_note(so_name)
		dn.insert(ignore_permissions=True)
		dn.submit()
		dn_created = True
	return so_name, so_created, dn_created


def seed_vet_dist_sales_flow():
	"""DP-567 — VD03, batch/expiry on delivery (same has_batch_no mechanism proven in Golden
	Demo #2's PD01/PD02, no new code)."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_NAME}):
		return "seed_vet_dist_sales_flow: SKIPPED — run seed_vet_dist_master_data first."
	so_name, so_created, dn_created = _ensure_sales_order_and_delivery()
	return f"seed_vet_dist_sales_flow: Sales Order {'created' if so_created else 'already existed'} ({so_name}). Delivery Note {'created' if dn_created else 'already existed'}."


_CREDIT_LIMIT = 25000000  # above the 18,000,000 existing order (100 x 180,000)


def _ensure_credit_limit():
	existing = frappe.db.get_value("Customer Credit Limit", {"parent": _DEALER_NAME, "company": _COMPANY_NAME}, ["name", "credit_limit"], as_dict=True)
	if existing:
		if existing.credit_limit == _CREDIT_LIMIT:
			return False
		frappe.db.set_value("Customer Credit Limit", existing.name, "credit_limit", _CREDIT_LIMIT)
		return True
	customer = frappe.get_doc("Customer", _DEALER_NAME)
	customer.append("credit_limits", {"company": _COMPANY_NAME, "credit_limit": _CREDIT_LIMIT})
	customer.save(ignore_permissions=True)
	return True


def _test_vd04_credit_limit_block():
	"""VD04 — same mechanism as Golden Demo #2's PD04: native Sales Order.check_credit_limit()."""
	if frappe.db.exists("Sales Order", {"po_no": "VD04-CREDIT-TEST", "customer": _DEALER_NAME}):
		return True
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": _DEALER_NAME,
			"company": _COMPANY_NAME,
			"po_no": "VD04-CREDIT-TEST",
			"delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
			"items": [{"item_code": _FG_ITEM, "qty": 50, "warehouse": _FG_RELEASED, "rate": 180000}],  # 9,000,000 on top of 18,000,000 = 27,000,000 > 25,000,000 limit
		}
	)
	blocked = False
	try:
		so.insert(ignore_permissions=True)
		so.submit()
	except frappe.ValidationError:
		blocked = True
		if so.name and frappe.db.exists("Sales Order", so.name):
			if frappe.db.get_value("Sales Order", so.name, "docstatus") == 1:
				frappe.get_doc("Sales Order", so.name).cancel()
			else:
				frappe.delete_doc("Sales Order", so.name, force=1, ignore_permissions=True)
	if not blocked:
		frappe.throw("VD04 negative test FAILED: over-credit-limit dealer order was not blocked!")
	return True


def seed_vet_dist_validations():
	"""DP-568 — VD04 (credit limit)."""
	if not frappe.db.exists("Sales Order", {"customer": _DEALER_NAME, "docstatus": 1}):
		return "seed_vet_dist_validations: SKIPPED — run seed_vet_dist_sales_flow first."
	_ensure_credit_limit()
	vd04 = _test_vd04_credit_limit_block()
	return f"seed_vet_dist_validations: VD04 CONFIRMED ({vd04})."


def seed_vet_dist_recall_trace():
	"""DP-569 — VD06 (recall) traces to the customers who received the recalled batch.
	Reuses Golden Demo #3's QMS Recall (already created by Golden Demo #9's DP-563) and Golden
	Demo #2's trace_batch_to_customers() query — no new code, just proving the cross-module
	chain: manufactured batch -> recalled -> traced to the dealer who received it."""
	dn_batch = frappe.db.get_value(
		"Delivery Note Item", {"item_code": _FG_ITEM, "parent": ["in", frappe.get_all("Delivery Note", {"customer": _DEALER_NAME, "docstatus": 1}, pluck="name")]}, "batch_no"
	)
	if not dn_batch:
		return "seed_vet_dist_recall_trace: SKIPPED — run seed_vet_dist_sales_flow first."
	recall_exists = frappe.db.exists("QMS Recall", {"batch_reference": dn_batch})
	from enterprise_core.enterprise_core.api import trace_batch_to_customers

	traced = trace_batch_to_customers(dn_batch)
	dealer_found = any(row.get("customer") == _DEALER_NAME for row in traced)
	if not (recall_exists and dealer_found):
		frappe.throw(f"VD06 FAILED: recall for batch {dn_batch} exists={bool(recall_exists)}, dealer traced={dealer_found}.")
	return f"seed_vet_dist_recall_trace: VD06 CONFIRMED — batch {dn_batch}'s recall traces to dealer {_DEALER_NAME}."


def seed_vet_dist_technical_visit():
	"""DP-570 — VD07, technical visit linked to customer."""
	if not frappe.db.exists("Customer", {"customer_name": _DEALER_NAME}):
		return "seed_vet_dist_technical_visit: SKIPPED — run seed_vet_dist_master_data first."
	if frappe.db.exists("Vet Technical Visit", {"customer": _DEALER_NAME}):
		return "seed_vet_dist_technical_visit: already existed."
	frappe.get_doc(
		{
			"doctype": "Vet Technical Visit",
			"customer": _DEALER_NAME,
			"sales_person": _SALES_PERSON,
			"products_discussed": "Oxytetracycline 200mg/mL Injectable Solution — withdrawal period and dosing for cattle/swine.",
			"notes": "Dealer requested more point-of-sale materials on withdrawal period compliance.",
			"follow_up_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
		}
	).insert(ignore_permissions=True)
	return "seed_vet_dist_technical_visit: VD07 CONFIRMED — technical visit created."
