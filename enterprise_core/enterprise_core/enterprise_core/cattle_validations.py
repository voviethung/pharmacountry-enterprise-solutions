"""Golden Demo #13 (Cattle / Dairy Farm Management, master plan DEMO 24) business rules —
CT01/CT02/CT03/CT06/CT07.
"""

import frappe
from frappe import _

_GESTATION_DAYS = 283  # average cattle gestation length — illustrative, same status as the pig
# demo's placeholder gestation constant.


def cattle_animal_validate(doc, method):
	"""CT01 — pedigree integrity: an animal can't be its own sire/dam, and sire/dam must have
	the matching sex (same shape as Pig Farm's sow/boar sex check on Breeding Service)."""
	if doc.sire:
		if doc.sire == doc.name:
			frappe.throw(_("{0} cannot be its own sire.").format(doc.name), title=_("CT01: Invalid Pedigree"))
		sire_sex = frappe.db.get_value("Cattle Animal", doc.sire, "sex")
		if sire_sex != "Male":
			frappe.throw(_("{0} is not Male, cannot be a sire.").format(doc.sire), title=_("CT01: Invalid Pedigree"))
	if doc.dam:
		if doc.dam == doc.name:
			frappe.throw(_("{0} cannot be its own dam.").format(doc.name), title=_("CT01: Invalid Pedigree"))
		dam_sex = frappe.db.get_value("Cattle Animal", doc.dam, "sex")
		if dam_sex != "Female":
			frappe.throw(_("{0} is not Female, cannot be a dam.").format(doc.dam), title=_("CT01: Invalid Pedigree"))


def cattle_breeding_service_validate(doc, method):
	"""CT02 — reproduction lifecycle state machine: Served -> Confirmed Pregnant -> Calved, or
	Served/Confirmed Pregnant -> Failed. Never backwards, never skipping. Also computes the
	expected calving date server-side rather than trusting manual entry (same pattern as Pig
	Farm's Breeding Service)."""
	dam_sex = frappe.db.get_value("Cattle Animal", doc.dam, "sex")
	if dam_sex != "Female":
		frappe.throw(_("{0} is not Female.").format(doc.dam), title=_("CT02: Invalid Dam"))
	sire_sex = frappe.db.get_value("Cattle Animal", doc.sire, "sex")
	if sire_sex != "Male":
		frappe.throw(_("{0} is not Male.").format(doc.sire), title=_("CT02: Invalid Sire"))

	if not doc.expected_calving_date:
		doc.expected_calving_date = frappe.utils.add_days(doc.service_date, _GESTATION_DAYS)

	if doc.is_new():
		return
	before_status = frappe.db.get_value("Cattle Breeding Service", doc.name, "status")
	valid_transitions = {
		"Served": {"Confirmed Pregnant", "Failed"},
		"Confirmed Pregnant": {"Calved", "Failed"},
	}
	if before_status != doc.status and doc.status not in valid_transitions.get(before_status, set()):
		frappe.throw(
			_("Invalid reproduction lifecycle transition for {0}: {1} -> {2}.").format(doc.name, before_status, doc.status),
			title=_("CT02: Invalid Reproduction Lifecycle Transition"),
		)


def cattle_calving_validate(doc, method):
	"""CT02 (part 2) — a calving can only be recorded against a Breeding Service that reached
	Confirmed Pregnant."""
	service_status = frappe.db.get_value("Cattle Breeding Service", doc.breeding_service, "status")
	if service_status != "Confirmed Pregnant":
		frappe.throw(
			_("Cannot record Calving for Breeding Service {0} — status is '{1}', must be Confirmed Pregnant.").format(
				doc.breeding_service, service_status
			),
			title=_("CT02: Breeding Service Not Confirmed Pregnant"),
		)


def cattle_calving_on_update(doc, method):
	frappe.db.set_value("Cattle Breeding Service", doc.breeding_service, "status", "Calved")


def _block_if_animal_not_active(doc, method):
	"""CT03/CT04/CT05 — milking, treatment and feed can only be logged against an Active
	animal (same rule shape as every prior golden demo's batch/flock-active guard)."""
	animal_status = frappe.db.get_value("Cattle Animal", doc.animal, "status")
	if animal_status != "Active":
		frappe.throw(
			_("Cannot log {0} against Animal {1} — status is '{2}', must be Active.").format(doc.doctype, doc.animal, animal_status),
			title=_("CT-lifecycle: Animal Not Active"),
		)


def cattle_milking_record_validate(doc, method):
	"""CT03 — only a Female animal can have a milking record."""
	_block_if_animal_not_active(doc, method)
	sex = frappe.db.get_value("Cattle Animal", doc.animal, "sex")
	if sex != "Female":
		frappe.throw(_("Cannot log a milking record for Animal {0} — sex is '{1}', must be Female.").format(doc.animal, sex), title=_("CT03: Not a Female Animal"))


def cattle_sale_lot_validate(doc, method):
	"""CT06 — an animal already Sold/Culled cannot be sold/culled twice; cost allocation
	(feed + health + other), cost/kg and profit are always server-recomputed from the animal's
	own recorded history (CT07), same "server always recomputes" principle as every prior
	harvest/sale doctype in this platform."""
	animal = frappe.get_doc("Cattle Animal", doc.animal)
	if animal.status != "Active":
		frappe.throw(
			_("Cannot sell/cull Animal {0} — status is '{1}', must be Active.").format(doc.animal, animal.status),
			title=_("CT06: Animal Not Active"),
		)

	total_feed_cost = frappe.db.sql("select sum(cost) from `tabCattle Feed Log` where animal=%s", (doc.animal,))[0][0] or 0
	total_health_cost = frappe.db.sql("select sum(cost) from `tabCattle Health Treatment` where animal=%s", (doc.animal,))[0][0] or 0
	doc.total_feed_cost = total_feed_cost
	doc.total_health_cost = total_health_cost
	doc.total_cost = total_feed_cost + total_health_cost + (doc.other_cost or 0)
	doc.cost_per_kg = round(doc.total_cost / doc.weight_kg, 2) if doc.weight_kg else 0
	doc.profit = (doc.sale_price or 0) - doc.total_cost


def cattle_sale_lot_on_update(doc, method):
	frappe.db.set_value("Cattle Animal", doc.animal, "status", doc.sale_type)
