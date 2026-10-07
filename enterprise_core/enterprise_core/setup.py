"""Idempotent setup logic (DP-307) — runs on every site via after_install/after_migrate.
Only inserts records that are missing; never overwrites a record a user has edited.
Pattern follows the audit finding on ERP ENLIE's own setup.py (see
enterprise-platform/documents/productization/01_productization_audit.md §4-§6): this is the
one place ENLIE got right (generic mechanism seeding generic data) — the master plan's 15
Capability Engines (§3) are the platform's own registry, not any one customer's data, so
seeding them unconditionally on every site is correct here (unlike ENLIE's department/
warehouse seeds, which were misclassified this way).
"""

import frappe

# A fresh ERPNext site created HEADLESSLY (bench new-site, never the interactive Setup Wizard)
# is missing a whole set of standard root/default records the Setup Wizard normally creates —
# "All Customer Groups", "All Supplier Groups", "All Territories", "All Item Groups", the
# "Transit" Warehouse Type, default UOMs, etc. (see erpnext/setup/setup_wizard/operations/
# install_fixtures.py's own install()/get_preset_records()). This app's own AI/golden-demo seed
# functions create real master/transactional data (e.g. threepl_seeds._ensure_company(), which
# creates a Customer Group explicitly parented under "All Customer Groups") and assume these
# roots already exist, the same assumption the Setup Wizard flow always satisfies — a real
# multi-tenant provisioning flow never runs that wizard, so fresh sites hard-failed with
# "Could not find Warehouse Type: Transit" and then "Could not find Parent Customer Group: All
# Customer Groups" in succession (confirmed live via scripts/provision-tenant.sh against a real
# new site, frappe_docker_demo) — never hit before because the platform's own 2 real sites
# happened to already have these from however they were first bootstrapped.
#
# Fix: call ERPNext's own install_fixtures.install() directly — the exact function the Setup
# Wizard itself calls — rather than hand-reimplementing one missing record at a time as each
# seed function happens to trip over the next one. Confirmed safe to call unconditionally (every
# insert in frappe.desk.page.setup_wizard.setup_wizard.make_records() uses
# ignore_if_duplicate=True and swallows+logs any other exception, never raising), so it's a
# correct no-op on the 2 existing real sites that already have these records.
def seed_erpnext_fixtures():
	from erpnext.setup.setup_wizard.operations.install_fixtures import install as install_erpnext_fixtures
	from erpnext.setup.setup_wizard.setup_wizard import setup_company, setup_defaults

	# install_fixtures.install() is always called with a real country string in the interactive
	# Setup Wizard (it comes straight from the wizard form, never None) — some of its preset
	# records (default Territory) are built directly from it, so it can't be left out. "Vietnam"
	# matches this platform's own real target market (see pharmacountry.vn's own "mặc định tiếng
	# Việt" requirement elsewhere in this codebase), not a hardcoded assumption about any one
	# tenant's real country — a tenant can still add/rename territories after provisioning.
	country = "Vietnam"
	install_erpnext_fixtures(country=country)

	# install_fixtures.install() alone still isn't enough: ERPNext's "Standard Selling"/"Standard
	# Buying" Price Lists (needed by threepl_seeds._ensure_item_prices() and every other seed
	# function that prices an Item) are created by a DIFFERENT Setup Wizard stage —
	# setup_defaults() — which itself needs setup_company()'s own default Company (for its
	# currency/fiscal-year/global-defaults) to already exist first. Both are "Only for
	# programmatical use" per setup_wizard.py's own comment on setup_complete(), the function this
	# reproduces headlessly (stage_fixtures + setup_company + setup_defaults, skipping only the
	# telemetry-capture stage, which is meaningless outside the real interactive wizard).
	#
	# Skipped entirely if a Company already exists on this site (the platform's own 2 real sites,
	# or a second after_migrate run) — this block exists purely to bootstrap the master data a
	# BRAND NEW site otherwise lacks, never to create a second company on top of one that's
	# already there. The placeholder name/abbreviation below is deliberately generic (not any
	# tenant's real company) — renaming/replacing it with the tenant's actual company is a
	# separate onboarding step, out of scope for "make fresh-site provisioning not crash."
	if frappe.db.exists("Company"):
		return

	today = frappe.utils.getdate()
	args = frappe._dict(
		{
			"company_name": "Tenant Company",
			"company_abbr": "TC",
			"currency": "VND",
			"country": country,
			"chart_of_accounts": "Standard",
			"domain": "Manufacturing",
			"fy_start_date": f"{today.year}-01-01",
			"fy_end_date": f"{today.year}-12-31",
		}
	)
	setup_company(args)
	setup_defaults(args)


# (engine_code, engine_name, category) — master plan §3, 15 Capability Engines.
_CAPABILITY_ENGINES = [
	("CE-01", "ERP Core", "Core"),
	("CE-02", "CRM & Sales", "Core"),
	("CE-03", "Procurement", "Core"),
	("CE-04", "WMS & Logistics", "Core"),
	("CE-05", "Manufacturing / MRP", "Core"),
	("CE-06", "QMS", "Industry"),
	("CE-07", "DMS & Training", "Industry"),
	("CE-08", "LIMS / Laboratory", "Industry"),
	("CE-09", "EAM / CMMS / Validation", "Industry"),
	("CE-10", "Farm Management", "Industry"),
	("CE-11", "Traceability", "Industry"),
	("CE-12", "Commerce / Portal", "Core"),
	("CE-13", "AI & Automation Platform", "AI"),
	("CE-14", "HR Performance & Competency", "Industry"),
	("CE-15", "R&D & Regulatory Affairs (RA)", "Industry"),
]


def seed_capability_engines():
	for engine_code, engine_name, category in _CAPABILITY_ENGINES:
		if frappe.db.exists("Capability Engine", engine_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Capability Engine",
				"engine_code": engine_code,
				"engine_name": engine_name,
				"category": category,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


# DP-302 — illustrative Feature Flags only, NOT a canonical/exhaustive list. Real feature
# flags get added by whichever capability-engine app actually implements that behavior
# (Phase 3+); these five exist to prove the Edition -> Feature Flag -> is_feature_enabled()
# mechanism works end-to-end before any real business app depends on it.
# (feature_code, feature_name, capability_engine, default_enabled)
_FEATURE_FLAGS = [
	("multi_currency", "Multi-Currency Accounting", "CE-01", 0),
	("advanced_bom_versioning", "Advanced BOM Versioning", "CE-05", 0),
	("capa_effectiveness_check", "CAPA Effectiveness Check", "CE-06", 1),
	("stability_study_tracking", "Stability Study Tracking", "CE-08", 1),
	("ai_deviation_summarization", "AI-Assisted Deviation Summarization", "CE-13", 0),
]

# DP-302 — one illustrative Edition proving the mechanism, matching master plan DEMO 01
# (Pharmaceutical Manufacturing ERP)'s capability list: CE-01,03,04,05,06,07,08,09,11.
_SAMPLE_EDITION_CODE = "PHARMA_MFG_STARTER"
_SAMPLE_EDITION_ENGINES = ["CE-01", "CE-03", "CE-04", "CE-05", "CE-06", "CE-07", "CE-08", "CE-09", "CE-11"]
_SAMPLE_EDITION_FEATURES = ["capa_effectiveness_check", "stability_study_tracking"]


def seed_feature_flags():
	for feature_code, feature_name, engine_code, default_enabled in _FEATURE_FLAGS:
		if frappe.db.exists("Feature Flag", feature_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Feature Flag",
				"feature_code": feature_code,
				"feature_name": feature_name,
				"capability_engine": engine_code,
				"default_enabled": default_enabled,
			}
		).insert(ignore_permissions=True)


def seed_sample_edition():
	if frappe.db.exists("Edition", _SAMPLE_EDITION_CODE):
		return
	edition = frappe.get_doc(
		{
			"doctype": "Edition",
			"edition_code": _SAMPLE_EDITION_CODE,
			"edition_name": "Pharma Manufacturing Starter",
			"description": "Illustrative Edition for DEMO 01 (Pharmaceutical Manufacturing ERP) — proves the Edition/Feature Flag mechanism, not a finished product offering.",
			"is_default": 1,
		}
	)
	for engine_code in _SAMPLE_EDITION_ENGINES:
		edition.append("capability_engines", {"capability_engine": engine_code, "enabled": 1})
	for feature_code in _SAMPLE_EDITION_FEATURES:
		edition.append("feature_flags", {"feature_flag": feature_code, "enabled": 1})
	edition.insert(ignore_permissions=True)

	settings = frappe.get_single("Enterprise Core Settings")
	if not settings.active_edition:
		settings.active_edition = _SAMPLE_EDITION_CODE
		settings.save(ignore_permissions=True)


# DP-303 — 19 Industry Packs, master plan §4 (canonical/exhaustive list, unlike the Feature
# Flags above). (pack_code, pack_name, industry_category)
_INDUSTRY_PACKS = [
	("IP-PHARMA", "Pharmaceutical", "Pharmaceutical"),
	("IP-SUPPLEMENT", "Nutraceutical / TPBVSK", "Nutraceutical"),
	("IP-COSMETICS", "Cosmetics", "Cosmetics"),
	("IP-MEDICAL-DEVICE", "Medical Device", "Medical Device"),
	("IP-VETERINARY", "Veterinary", "Veterinary"),
	("IP-VETERINARY-BIOLOGICAL", "Veterinary Biological / Vaccine", "Veterinary"),
	("IP-FEED", "Animal Feed", "Animal Feed"),
	("IP-PREMIX", "Premix / Feed Additive", "Animal Feed"),
	("IP-LIVESTOCK-PIG", "Livestock — Pig", "Livestock"),
	("IP-LIVESTOCK-POULTRY", "Livestock — Poultry", "Livestock"),
	("IP-LIVESTOCK-CATTLE", "Livestock — Cattle", "Livestock"),
	("IP-HATCHERY", "Hatchery (Livestock)", "Livestock"),
	("IP-AQUAFEED", "Aquafeed", "Aquaculture"),
	("IP-AQUA-ENVIRONMENT", "Aquaculture Environment Treatment", "Aquaculture"),
	("IP-SHRIMP", "Shrimp Farming", "Aquaculture"),
	("IP-FISH", "Fish Farming", "Aquaculture"),
	("IP-AQUA-HATCHERY", "Aqua Hatchery", "Aquaculture"),
	("IP-MEAT-PROCESSING", "Meat Processing", "Processing"),
	("IP-SEAFOOD-PROCESSING", "Seafood Processing", "Processing"),
	("IP-QMS", "Quality Management System (standalone)", "Horizontal / Cross-Industry"),
	("IP-DMS", "Document Management System & Training (standalone)", "Horizontal / Cross-Industry"),
	("IP-LIMS", "Laboratory Information Management System (standalone)", "Horizontal / Cross-Industry"),
	("IP-EAM", "EAM / CMMS / Calibration / Validation (standalone)", "Horizontal / Cross-Industry"),
	("IP-PHARMACY", "Pharmacy Chain (retail/POS)", "Pharmaceutical"),
	("IP-3PL-COLDCHAIN", "Pharma 3PL / GSP / Cold Chain", "Pharmaceutical"),
	("IP-CONSUMER-DIST", "Consumer Health / Cosmetics Distribution", "Cosmetics"),  # fixed Select
	# option list has no "Consumer Products"/"Distribution" value (checked
	# industry_pack.json's options before picking — same lesson 3PL/Pharmacy already hit);
	# "Cosmetics" is the closest fit since one of the two distributed item lines is cosmetics.
	("IP-INGREDIENT-TRADING", "Feed / Ingredient Trading", "Animal Feed"),  # new — a pure-trading
	# (no manufacturing) vertical wasn't in DP-303's original 19-pack list, registered directly
	# alongside IP-PHARMACY/IP-3PL-COLDCHAIN/IP-CONSUMER-DIST's own precedent for post-hoc pack
	# additions; "Animal Feed" fits directly within the fixed Select option list (same category
	# as IP-FEED/IP-PREMIX) since the traded goods are feed ingredients/additives.
]

# The only pack with a real Edition to pair with so far (DP-302's sample Edition). Superseded
# below by _PACK_DEFAULT_EDITIONS once the real product Editions exist — kept here unchanged so
# the sample Edition itself (already referenced by Enterprise Core Settings.active_edition) never
# loses its own original pairing in the history of this dict.
_SAMPLE_PACK_DEFAULT_EDITIONS = {"IP-PHARMA": _SAMPLE_EDITION_CODE}


# ---------------------------------------------------------------------------------------------
# Product Editions (SaaS packaging, "chuẩn hóa Product Core") — real tiered product offerings
# built on the same Edition/Capability Engine mechanism the sample Edition above proved out.
# Two axes, matching how real multi-industry ERP SaaS products (NetSuite, Odoo) package
# themselves: which INDUSTRY GROUP a customer operates in (groups the 27 Industry Packs into the
# ~8 verticals a real buyer actually shops for — nobody buys "Hatchery" alone), and which SERVICE
# TIER they're on (Starter/Professional/Enterprise, controlling which Capability Engines are
# enabled). 8 groups x 3 tiers = 24 real Editions. The 4 "Horizontal / Cross-Industry" standalone
# packs (IP-QMS/IP-DMS/IP-LIMS/IP-EAM) are deliberately NOT part of any group — they're
# cross-cutting add-on products in their own right, not an industry vertical, so they keep no
# default_edition here (same as today).
# (group_code, group_name, [pack_codes])
_EDITION_GROUPS = [
	("PHARMA", "Pharmaceutical", ["IP-PHARMA", "IP-PHARMACY", "IP-3PL-COLDCHAIN"]),
	("SUPPLEMENT_COSMETICS", "Nutraceutical & Cosmetics", ["IP-SUPPLEMENT", "IP-COSMETICS", "IP-CONSUMER-DIST"]),
	("MEDICAL_DEVICE", "Medical Device", ["IP-MEDICAL-DEVICE"]),
	("VETERINARY", "Veterinary", ["IP-VETERINARY", "IP-VETERINARY-BIOLOGICAL"]),
	("ANIMAL_FEED", "Animal Feed", ["IP-FEED", "IP-PREMIX", "IP-INGREDIENT-TRADING"]),
	("LIVESTOCK", "Livestock", ["IP-LIVESTOCK-PIG", "IP-LIVESTOCK-POULTRY", "IP-LIVESTOCK-CATTLE", "IP-HATCHERY"]),
	("AQUACULTURE", "Aquaculture", ["IP-AQUAFEED", "IP-AQUA-ENVIRONMENT", "IP-SHRIMP", "IP-FISH", "IP-AQUA-HATCHERY"]),
	("PROCESSING", "Meat & Seafood Processing", ["IP-MEAT-PROCESSING", "IP-SEAFOOD-PROCESSING"]),
]

# Engines every tier shares, before a group's own industry engines are added.
_TIER_STARTER_ENGINES = ["CE-01", "CE-04", "CE-05"]
_TIER_PROFESSIONAL_ADDS = ["CE-02", "CE-03", "CE-11", "CE-12"]
_TIER_ENTERPRISE_ADDS = ["CE-13", "CE-14", "CE-15"]

# Per-group industry engines, added at Professional (and inherited by Enterprise) — derived from
# what each group's own packs' real doctypes actually exercise (manufacturing/QC-heavy packs get
# QMS/DMS/LIMS/EAM; farm-operation packs get Farm Management instead, not the manufacturing QC
# stack their doctypes never touch; see DP-307's own per-pack seed function list above for which
# doctypes each pack really uses).
_GROUP_INDUSTRY_ENGINES = {
	"PHARMA": ["CE-06", "CE-07", "CE-08", "CE-09"],
	"SUPPLEMENT_COSMETICS": ["CE-06", "CE-07", "CE-08", "CE-09"],
	"MEDICAL_DEVICE": ["CE-06", "CE-07", "CE-08", "CE-09"],
	"VETERINARY": ["CE-06", "CE-07", "CE-10"],
	"ANIMAL_FEED": ["CE-06", "CE-08", "CE-09"],
	"LIVESTOCK": ["CE-10"],
	"AQUACULTURE": ["CE-10"],
	"PROCESSING": ["CE-06", "CE-08"],
}

_TIER_SUFFIXES = ["STARTER", "PROFESSIONAL", "ENTERPRISE"]


def _build_product_editions():
	"""Returns [(edition_code, edition_name, description, [engine_codes])] for all 24 real
	Editions — computed from the registries above rather than hand-listed, so the Starter <
	Professional < Enterprise engine progression can never drift out of sync across the 8 groups."""
	editions = []
	for group_code, group_name, _packs in _EDITION_GROUPS:
		industry_engines = _GROUP_INDUSTRY_ENGINES[group_code]
		starter = list(_TIER_STARTER_ENGINES)
		professional = starter + _TIER_PROFESSIONAL_ADDS + industry_engines
		enterprise = professional + _TIER_ENTERPRISE_ADDS
		tiers = [("STARTER", starter), ("PROFESSIONAL", professional), ("ENTERPRISE", enterprise)]
		for tier_suffix, engines in tiers:
			edition_code = f"{group_code}_{tier_suffix}"
			edition_name = f"{group_name} — {tier_suffix.title()}"
			description = (
				f"Real product Edition (chuẩn hóa Product Core) for the {group_name} industry "
				f"group, {tier_suffix.title()} tier."
			)
			# De-duplicate while preserving order (a group/tier combination can list the same
			# engine twice across the Starter/Professional/Enterprise/industry lists above).
			seen = set()
			ordered_engines = [e for e in engines if not (e in seen or seen.add(e))]
			editions.append((edition_code, edition_name, description, ordered_engines))
	return editions


_PRODUCT_EDITIONS = _build_product_editions()

# Every pack's real default Edition: its group's Professional tier (the sensible middle default —
# Starter/Enterprise remain available for a future subscription/signup flow to let the customer
# pick). IP-PHARMA intentionally moves OFF the old illustrative PHARMA_MFG_STARTER sample onto
# the real PHARMA_PROFESSIONAL Edition; the sample Edition record itself is left in place
# unchanged (still referenced by _SAMPLE_PACK_DEFAULT_EDITIONS above and by whatever Enterprise
# Core Settings.active_edition already points to) rather than deleted, so no existing Link field
# is ever left dangling.
_PACK_DEFAULT_EDITIONS = {
	pack_code: f"{group_code}_PROFESSIONAL"
	for group_code, _group_name, pack_codes in _EDITION_GROUPS
	for pack_code in pack_codes
}


def seed_product_editions():
	for edition_code, edition_name, description, engine_codes in _PRODUCT_EDITIONS:
		if frappe.db.exists("Edition", edition_code):
			continue
		edition = frappe.get_doc(
			{
				"doctype": "Edition",
				"edition_code": edition_code,
				"edition_name": edition_name,
				"description": description,
				"is_default": 0,
			}
		)
		for engine_code in engine_codes:
			edition.append("capability_engines", {"capability_engine": engine_code, "enabled": 1})
		edition.insert(ignore_permissions=True)


def sync_industry_pack_default_editions():
	for pack_code, edition_code in _PACK_DEFAULT_EDITIONS.items():
		current = frappe.db.get_value("Industry Pack", pack_code, "default_edition")
		if current == edition_code:
			continue
		frappe.db.set_value("Industry Pack", pack_code, "default_edition", edition_code)


def activate_edition(edition_code: str) -> None:
	"""Pins THIS SITE's Enterprise Core Settings.active_edition to a real product Edition — the
	one step a tenant-provisioning flow calls (via `bench execute`) right after `bench new-site
	... --install-app enterprise_core` finishes seeding the Edition/Capability Engine/Industry
	Pack registry (after_install, above), to turn a freshly-provisioned site into "this tenant is
	on the Veterinary Professional plan" without any manual Desk clicking. Called from
	frappe_docker_demo's scripts/provision-tenant.sh."""
	if not frappe.db.exists("Edition", edition_code):
		frappe.throw(f"Edition '{edition_code}' does not exist on this site.")
	settings = frappe.get_single("Enterprise Core Settings")
	settings.active_edition = edition_code
	settings.save(ignore_permissions=True)
	frappe.db.commit()


def seed_industry_packs():
	for pack_code, pack_name, category in _INDUSTRY_PACKS:
		if frappe.db.exists("Industry Pack", pack_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Industry Pack",
				"pack_code": pack_code,
				"pack_name": pack_name,
				"industry_category": category,
				"default_edition": _PACK_DEFAULT_EDITIONS.get(pack_code),
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


# DP-304 — 11 Role Templates matching master plan DEMO 01 (Pharmaceutical Manufacturing
# ERP)'s exact role list (canonical for that one pack, same status as the Feature Flags:
# illustrative for the platform as a whole, real for this specific demo). `frappe_role`
# left blank deliberately — mapping to an actual Frappe Role/permission set is a DP-400
# Demo Factory decision, not forced here.
# (template_code, template_name, description)
_ROLE_TEMPLATES = [
	("GENERAL_DIRECTOR", "General Director", "Overall business oversight; views cross-functional dashboards."),
	("QUALITY_DIRECTOR", "Quality Director", "Owns quality strategy across QA/QC/RA; final escalation for quality decisions."),
	("QA_MANAGER", "QA Manager", "Batch release, deviation/CAPA ownership, document approval."),
	("QC_MANAGER", "QC Manager", "Lab testing oversight, result review/approval, instrument/method management."),
	("PRODUCTION_MANAGER", "Production Manager", "Work order execution, batch record review, production scheduling."),
	("PLANNING_OFFICER", "Planning Officer", "Production planning, material requirement planning."),
	("WAREHOUSE_OFFICER", "Warehouse Officer", "Receipt, storage, quarantine/release movement, picking/delivery."),
	("PROCUREMENT_OFFICER", "Procurement Officer", "RFQ, purchase order, supplier evaluation."),
	("MAINTENANCE", "Maintenance", "Equipment calibration/preventive maintenance, breakdown handling."),
	("ANALYST", "Analyst", "Executes lab tests, records results for QC Manager review."),
	("OPERATOR", "Operator", "Executes production/packaging steps on the shop floor."),
]

_IP_PHARMA_ROLES = [code for code, _, _ in _ROLE_TEMPLATES]


def seed_role_templates():
	for template_code, template_name, description in _ROLE_TEMPLATES:
		if frappe.db.exists("Role Template", template_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Role Template",
				"template_code": template_code,
				"template_name": template_name,
				"description": description,
			}
		).insert(ignore_permissions=True)


def seed_industry_pack_roles():
	pack = frappe.get_doc("Industry Pack", "IP-PHARMA")
	existing = {row.role_template for row in pack.roles}
	changed = False
	for template_code in _IP_PHARMA_ROLES:
		if template_code in existing:
			continue
		pack.append("roles", {"role_template": template_code, "is_required": 1})
		changed = True
	if changed:
		pack.save(ignore_permissions=True)


# DP-305 — 7 Workspace Templates covering DEMO 01 (Pharma)'s 11 roles (several roles share
# a workspace, e.g. Analyst+QC Manager both use the QA/QC workspace). Grouping inspired by
# the 20 real role-scoped workspaces catalogued on ERP ENLIE during the audit (qa_qms_dms,
# production_planner, stock_user, purchase_user, maintenance_qualification, ... — see
# 01_productization_audit.md §3 DP-103) but not copied verbatim; genericized for this pack.
# `frappe_workspace` left blank — building the actual Frappe Workspace is later work.
# (template_code, template_name, description)
_WORKSPACE_TEMPLATES = [
	("EXECUTIVE_WORKSPACE", "Executive Dashboard", "Cross-functional KPIs for General/Quality Director."),
	("QA_QC_WORKSPACE", "QA/QC Workspace", "Deviation, CAPA, batch release, document control, lab results."),
	("PRODUCTION_WORKSPACE", "Production Workspace", "Work orders, job cards, batch execution."),
	("PLANNING_WORKSPACE", "Planning Workspace", "Production plan, material requirement planning."),
	("WAREHOUSE_WORKSPACE", "Warehouse Workspace", "Receipt, quarantine/release, stock movement, picking."),
	("PROCUREMENT_WORKSPACE", "Procurement Workspace", "RFQ, purchase order, supplier evaluation."),
	("MAINTENANCE_WORKSPACE", "Maintenance Workspace", "Equipment calibration, preventive maintenance, breakdowns."),
]

_IP_PHARMA_WORKSPACES = [code for code, _, _ in _WORKSPACE_TEMPLATES]


def seed_workspace_templates():
	for template_code, template_name, description in _WORKSPACE_TEMPLATES:
		if frappe.db.exists("Workspace Template", template_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Workspace Template",
				"template_code": template_code,
				"template_name": template_name,
				"description": description,
			}
		).insert(ignore_permissions=True)


def seed_industry_pack_workspaces():
	pack = frappe.get_doc("Industry Pack", "IP-PHARMA")
	existing = {row.workspace_template for row in pack.workspaces}
	changed = False
	for template_code in _IP_PHARMA_WORKSPACES:
		if template_code in existing:
			continue
		pack.append("workspaces", {"workspace_template": template_code, "is_required": 1})
		changed = True
	if changed:
		pack.save(ignore_permissions=True)


# DP-306 — 4 illustrative Seed Templates for IP-PHARMA. Real implementations are stubs
# (enterprise_core/seeds.py) until a real capability-engine app exists to seed into
# (Phase 3+) — this proves the registry->runner mechanism, not real demo data.
# (template_code, template_name, seed_type, seed_function, sequence)
_SEED_TEMPLATES = [
	("SEED_DEMO_COMPANY", "Demo Company Setup", "Master Data", "enterprise_core.enterprise_core.seeds.seed_demo_company", 10),
	("SEED_PHARMA_MASTER_DATA", "Pharma Master Data", "Master Data", "enterprise_core.enterprise_core.seeds.seed_pharma_master_data", 20),
	("SEED_PURCHASE_FLOW", "Purchase Flow (DP-502)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_purchase_flow", 25),
	("SEED_WAREHOUSE_FLOW", "Warehouse Flow (DP-503)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_warehouse_flow", 27),
	("SEED_MANUFACTURING_FLOW", "Manufacturing Flow (DP-504)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_manufacturing_flow", 29),
	("SEED_QC_FLOW", "QC Flow (DP-505)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_qc_flow", 30),
	("SEED_QA_RELEASE", "QA Release (DP-506)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_qa_release", 32),
	("SEED_QMS_INTEGRATION", "QMS Integration (DP-507)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_qms_integration", 34),
	("SEED_DMS_INTEGRATION", "DMS Integration (DP-508)", "Master Data", "enterprise_core.enterprise_core.seeds.seed_dms_integration", 35),
	("SEED_EAM_FLOW", "EAM Flow (DP-509)", "Master Data", "enterprise_core.enterprise_core.seeds.seed_eam_flow", 36),
	("SEED_DASHBOARD", "Dashboard (DP-510)", "Master Data", "enterprise_core.enterprise_core.seeds.seed_dashboard", 38),
	("SEED_DEMO_USERS", "Demo Users", "Master Data", "enterprise_core.enterprise_core.seeds.seed_demo_users", 39),
	("SEED_PHARMA_DIST_MASTER_DATA", "Pharma Distribution Master Data (DP-513)", "Master Data", "enterprise_core.enterprise_core.seeds.seed_pharma_distribution_master_data", 41),
	("SEED_DISTRIBUTION_SALES_FLOW", "Distribution Sales Flow (DP-514)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_distribution_sales_flow", 42),
	("SEED_DISTRIBUTION_VALIDATIONS", "Distribution Validations PD02/PD03/PD04 (DP-515/516/517)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_distribution_validations", 43),
	("SEED_DISTRIBUTION_RETURN", "Distribution Customer Return (DP-518)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_distribution_return", 44),
	("SEED_MANUFACTURING_BATCH_2", "Manufacturing Batch 2 for FEFO (DP-520/521)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_manufacturing_batch_2", 45),
	("SEED_DISTRIBUTION_FEFO_PROOF", "Distribution FEFO Proof PD01 (DP-522)", "Transaction", "enterprise_core.enterprise_core.seeds.seed_distribution_fefo_proof", 46),
	("SEED_DEMO_SCENARIO", "End-to-End Batch Scenario", "Demo Scenario", "enterprise_core.enterprise_core.seeds.seed_demo_scenario", 40),
]


# Golden Demo #3 — QMS standalone (master plan DEMO 10), attached to IP-QMS, not IP-PHARMA —
# a genuinely separate, cross-industry product, not part of the Pharma demo's own seed chain.
_QMS_SEED_TEMPLATES = [
	("SEED_QMS_DEVIATION_CAPA_FLOW", "QMS Deviation -> CAPA -> Closure (DP-523)", "Transaction", "enterprise_core.enterprise_core.qms_seeds.seed_deviation_capa_flow", 10),
	("SEED_QMS_VALIDATIONS", "QMS Validations Q01/Q02/Q04 (DP-524)", "Transaction", "enterprise_core.enterprise_core.qms_seeds.seed_qms_validations", 20),
	("SEED_QMS_ESCALATION", "QMS CAPA Escalation Q03 (DP-525)", "Transaction", "enterprise_core.enterprise_core.qms_seeds.seed_qms_escalation", 30),
	("SEED_QMS_CHANGE_CONTROL", "QMS Change Control Q05 (DP-526)", "Master Data", "enterprise_core.enterprise_core.qms_seeds.seed_qms_change_control", 40),
	("SEED_QMS_OOS_OOT", "QMS OOS/OOT Q06 (DP-527)", "Transaction", "enterprise_core.enterprise_core.qms_seeds.seed_qms_oos_oot", 50),
	("SEED_QMS_AUDIT", "QMS Audit Q07 (DP-528)", "Transaction", "enterprise_core.enterprise_core.qms_seeds.seed_qms_audit", 60),
	("SEED_QMS_RECALL_RISK_SUPPLIER", "QMS Recall/Risk/Supplier Quality (DP-529)", "Master Data", "enterprise_core.enterprise_core.qms_seeds.seed_qms_recall_risk_supplier", 70),
]

# Golden Demo #4 — DMS & Training standalone (master plan DEMO 11), attached to IP-DMS.
_DMS_SEED_TEMPLATES = [
	("SEED_DMS_DOCUMENT_LIFECYCLE", "DMS Document Lifecycle (DP-531/532)", "Transaction", "enterprise_core.enterprise_core.dms_seeds.seed_dms_document_lifecycle", 10),
	("SEED_DMS_REVISION", "DMS Revision D02/D04/D06 (DP-533)", "Transaction", "enterprise_core.enterprise_core.dms_seeds.seed_dms_revision", 20),
	("SEED_DMS_VALIDATIONS", "DMS Validations D01/D05 (DP-534)", "Transaction", "enterprise_core.enterprise_core.dms_seeds.seed_dms_validations", 30),
]

# Golden Demo #5 — LIMS / QC Laboratory standalone (master plan DEMO 12), attached to IP-LIMS.
_LIMS_SEED_TEMPLATES = [
	("SEED_LIMS_MASTER_DATA", "LIMS Master Data (DP-537)", "Master Data", "enterprise_core.enterprise_core.lims_seeds.seed_lims_master_data", 10),
	("SEED_LIMS_GOLDEN_FLOW", "LIMS Golden Flow L04 (DP-538)", "Transaction", "enterprise_core.enterprise_core.lims_seeds.seed_lims_golden_flow", 20),
	("SEED_LIMS_OOS_FLOW", "LIMS OOS Flow L05 (DP-539)", "Transaction", "enterprise_core.enterprise_core.lims_seeds.seed_lims_oos_flow", 30),
	("SEED_LIMS_COA", "LIMS COA L07 (DP-540)", "Transaction", "enterprise_core.enterprise_core.lims_seeds.seed_lims_coa", 40),
	("SEED_LIMS_VALIDATIONS", "LIMS Validations L01/L02/L03/L06/L08 (DP-541)", "Transaction", "enterprise_core.enterprise_core.lims_seeds.seed_lims_validations", 50),
]

# Golden Demo #6 — EAM/CMMS/Calibration/Validation standalone (master plan DEMO 13), IP-EAM.
_EAM_SEED_TEMPLATES = [
	("SEED_EAM_CALIBRATION", "EAM Calibration E02 (DP-543)", "Master Data", "enterprise_core.enterprise_core.eam_seeds.seed_eam_calibration", 10),
	("SEED_EAM_QUALIFICATION", "EAM Qualification E05/E06 (DP-544)", "Transaction", "enterprise_core.enterprise_core.eam_seeds.seed_eam_qualification", 20),
	("SEED_EAM_BREAKDOWN_REPAIR", "EAM Breakdown Repair E03/E04 (DP-545)", "Transaction", "enterprise_core.enterprise_core.eam_seeds.seed_eam_breakdown_repair", 30),
	("SEED_EAM_VALIDATIONS", "EAM Validations E06 (DP-546)", "Transaction", "enterprise_core.enterprise_core.eam_seeds.seed_eam_validations", 40),
]

# Golden Demo #7 — Compound Feed Manufacturing (master plan DEMO 18), attached to IP-FEED
# (already reserved in _INDUSTRY_PACKS above from DP-303).
_FEED_SEED_TEMPLATES = [
	("SEED_FEED_MASTER_DATA", "Feed Master Data (DP-548)", "Master Data", "enterprise_core.enterprise_core.feed_seeds.seed_feed_master_data", 10),
	("SEED_FEED_FORMULA_REVISION", "Feed Formula Revision F01 (DP-549)", "Transaction", "enterprise_core.enterprise_core.feed_seeds.seed_feed_formula_revision", 20),
	("SEED_FEED_SUBSTITUTION", "Feed Ingredient Substitution F02 (DP-550)", "Transaction", "enterprise_core.enterprise_core.feed_seeds.seed_feed_substitution", 30),
	("SEED_FEED_MANUFACTURING", "Feed Manufacturing F03/F06 (DP-551)", "Transaction", "enterprise_core.enterprise_core.feed_seeds.seed_feed_manufacturing", 40),
	("SEED_FEED_SEQUENCING", "Feed Line Sequencing F07 (DP-552)", "Transaction", "enterprise_core.enterprise_core.feed_seeds.seed_feed_sequencing", 50),
]

# Golden Demo #8 — Shrimp Farm Management (master plan DEMO 28), attached to IP-SHRIMP
# (already reserved in _INDUSTRY_PACKS above from DP-303).
_SHRIMP_SEED_TEMPLATES = [
	("SEED_SHRIMP_MASTER_DATA", "Shrimp Farm Master Data (DP-554)", "Master Data", "enterprise_core.enterprise_core.shrimp_seeds.seed_shrimp_farm_master_data", 10),
	("SEED_SHRIMP_STOCKING", "Shrimp Stocking SF01/SF02 (DP-555)", "Transaction", "enterprise_core.enterprise_core.shrimp_seeds.seed_shrimp_stocking", 20),
	("SEED_SHRIMP_OPERATIONS", "Shrimp Operations SF03-SF07/SF10 (DP-556)", "Transaction", "enterprise_core.enterprise_core.shrimp_seeds.seed_shrimp_operations", 30),
	("SEED_SHRIMP_HARVEST", "Shrimp Harvest SF08/SF09 (DP-557)", "Transaction", "enterprise_core.enterprise_core.shrimp_seeds.seed_shrimp_harvest", 40),
	("SEED_SHRIMP_VALIDATIONS", "Shrimp Validations SF01/SF02/SF03 (DP-558)", "Transaction", "enterprise_core.enterprise_core.shrimp_seeds.seed_shrimp_validations", 50),
]

# Golden Demo #9 — Veterinary Pharmaceutical Manufacturing (master plan DEMO 14, "PHASE 4"
# item 1), attached to IP-VETERINARY (already reserved in _INDUSTRY_PACKS above from DP-303).
_VET_MFG_SEED_TEMPLATES = [
	("SEED_VET_MFG_MASTER_DATA", "Vet Mfg Master Data VPM01 (DP-560)", "Master Data", "enterprise_core.enterprise_core.vet_mfg_seeds.seed_vet_mfg_master_data", 10),
	("SEED_VET_MFG_PRODUCTION", "Vet Mfg Production VPM03/VPM04 (DP-561)", "Transaction", "enterprise_core.enterprise_core.vet_mfg_seeds.seed_vet_mfg_production", 20),
	("SEED_VET_MFG_FORMULA_REVISION", "Vet Mfg Formula Revision VPM02 (DP-562)", "Transaction", "enterprise_core.enterprise_core.vet_mfg_seeds.seed_vet_mfg_formula_revision", 30),
	("SEED_VET_MFG_RECALL", "Vet Mfg Recall VPM06 (DP-563)", "Transaction", "enterprise_core.enterprise_core.vet_mfg_seeds.seed_vet_mfg_recall", 40),
	("SEED_VET_MFG_LABEL", "Vet Mfg Label Version VPM07 (DP-564)", "Transaction", "enterprise_core.enterprise_core.vet_mfg_seeds.seed_vet_mfg_label", 50),
	("SEED_VET_DIST_MASTER_DATA", "Vet Dist Master Data VD01/VD02/VD05 (DP-566)", "Master Data", "enterprise_core.enterprise_core.vet_dist_seeds.seed_vet_dist_master_data", 60),
	("SEED_VET_DIST_SALES_FLOW", "Vet Dist Sales Flow VD03 (DP-567)", "Transaction", "enterprise_core.enterprise_core.vet_dist_seeds.seed_vet_dist_sales_flow", 70),
	("SEED_VET_DIST_VALIDATIONS", "Vet Dist Validations VD04 (DP-568)", "Transaction", "enterprise_core.enterprise_core.vet_dist_seeds.seed_vet_dist_validations", 80),
	("SEED_VET_DIST_RECALL_TRACE", "Vet Dist Recall Trace VD06 (DP-569)", "Transaction", "enterprise_core.enterprise_core.vet_dist_seeds.seed_vet_dist_recall_trace", 90),
	("SEED_VET_DIST_TECHNICAL_VISIT", "Vet Dist Technical Visit VD07 (DP-570)", "Transaction", "enterprise_core.enterprise_core.vet_dist_seeds.seed_vet_dist_technical_visit", 100),
]

# Golden Demo #11 — Pig Farm Management (master plan DEMO 22, "PHASE 4" item 3), attached to
# IP-LIVESTOCK-PIG (already reserved in _INDUSTRY_PACKS above from DP-303).
_PIG_SEED_TEMPLATES = [
	("SEED_PIG_MASTER_DATA", "Pig Farm Master Data PF01 (DP-573)", "Master Data", "enterprise_core.enterprise_core.pig_seeds.seed_pig_farm_master_data", 10),
	("SEED_PIG_BREEDING_FLOW", "Pig Breeding Flow PF02 (DP-574)", "Transaction", "enterprise_core.enterprise_core.pig_seeds.seed_pig_breeding_flow", 20),
	("SEED_PIG_OPERATIONS", "Pig Operations PF03/PF04/PF05/PF06 (DP-575)", "Transaction", "enterprise_core.enterprise_core.pig_seeds.seed_pig_operations", 30),
	("SEED_PIG_SALE", "Pig Sale PF07/PF08 (DP-576)", "Transaction", "enterprise_core.enterprise_core.pig_seeds.seed_pig_sale", 40),
	("SEED_PIG_VALIDATIONS", "Pig Validations PF01/PF02/PF05 (DP-577)", "Transaction", "enterprise_core.enterprise_core.pig_seeds.seed_pig_validations", 50),
]

# Golden Demo #12 — Poultry Farm Management (master plan DEMO 23, "PHASE 4" item 4), attached to
# IP-LIVESTOCK-POULTRY (already reserved in _INDUSTRY_PACKS above from DP-303).
_POULTRY_SEED_TEMPLATES = [
	("SEED_POULTRY_MASTER_DATA", "Poultry Farm Master Data (DP-579)", "Master Data", "enterprise_core.enterprise_core.poultry_seeds.seed_poultry_farm_master_data", 10),
	("SEED_POULTRY_PLACEMENT", "Poultry Placement PO01 (DP-580)", "Transaction", "enterprise_core.enterprise_core.poultry_seeds.seed_poultry_placement", 20),
	("SEED_POULTRY_OPERATIONS", "Poultry Operations PO02/PO03/PO04/PO05/PO06 (DP-581)", "Transaction", "enterprise_core.enterprise_core.poultry_seeds.seed_poultry_operations", 30),
	("SEED_POULTRY_SALE", "Poultry Sale PO07 (DP-582)", "Transaction", "enterprise_core.enterprise_core.poultry_seeds.seed_poultry_sale", 40),
	("SEED_POULTRY_VALIDATIONS", "Poultry Validations PO01/PO06/PO07 (DP-583)", "Transaction", "enterprise_core.enterprise_core.poultry_seeds.seed_poultry_validations", 50),
]

# Golden Demo #13 — Cattle / Dairy Farm Management (master plan DEMO 24, "PHASE 4" item 5),
# attached to IP-LIVESTOCK-CATTLE (already reserved in _INDUSTRY_PACKS above from DP-303).
_CATTLE_SEED_TEMPLATES = [
	("SEED_CATTLE_MASTER_DATA", "Cattle Farm Master Data CT01 (DP-585)", "Master Data", "enterprise_core.enterprise_core.cattle_seeds.seed_cattle_farm_master_data", 10),
	("SEED_CATTLE_BREEDING_FLOW", "Cattle Breeding Flow CT02 (DP-586)", "Transaction", "enterprise_core.enterprise_core.cattle_seeds.seed_cattle_breeding_flow", 20),
	("SEED_CATTLE_OPERATIONS", "Cattle Operations CT03/CT04/CT05 (DP-587)", "Transaction", "enterprise_core.enterprise_core.cattle_seeds.seed_cattle_operations", 30),
	("SEED_CATTLE_SALE", "Cattle Sale CT06/CT07 (DP-588)", "Transaction", "enterprise_core.enterprise_core.cattle_seeds.seed_cattle_sale", 40),
	("SEED_CATTLE_VALIDATIONS", "Cattle Validations CT01/CT02/CT06 (DP-589)", "Transaction", "enterprise_core.enterprise_core.cattle_seeds.seed_cattle_validations", 50),
]

# Golden Demo #14 — Hatchery / Breeding Management (master plan DEMO 25, "PHASE 4" item 6, the
# last Phase 4 item), attached to IP-HATCHERY (already reserved in _INDUSTRY_PACKS above from
# DP-303).
_HATCHERY_SEED_TEMPLATES = [
	("SEED_HATCHERY_MASTER_DATA", "Hatchery Master Data (DP-591)", "Master Data", "enterprise_core.enterprise_core.hatchery_seeds.seed_hatchery_master_data", 10),
	("SEED_HATCHERY_EGG_INCUBATION", "Hatchery Egg Batch/Incubation H01/H02 (DP-592)", "Transaction", "enterprise_core.enterprise_core.hatchery_seeds.seed_hatchery_egg_and_incubation", 20),
	("SEED_HATCHERY_HATCH_GRADING", "Hatchery Hatch/Grading H03/H04 (DP-593)", "Transaction", "enterprise_core.enterprise_core.hatchery_seeds.seed_hatchery_hatch_and_grading", 30),
	("SEED_HATCHERY_VACCINATION_DISPATCH", "Hatchery Vaccination/Dispatch H05/H06 (DP-594)", "Transaction", "enterprise_core.enterprise_core.hatchery_seeds.seed_hatchery_vaccination_and_dispatch", 40),
	("SEED_HATCHERY_VALIDATIONS", "Hatchery Validations H01/H04/H06 (DP-595)", "Transaction", "enterprise_core.enterprise_core.hatchery_seeds.seed_hatchery_validations", 50),
]

# Golden Demo #15 — Aquafeed Manufacturing (master plan DEMO 26, "PHASE 5" item 1), attached to
# IP-AQUAFEED (already reserved in _INDUSTRY_PACKS above from DP-303).
_AQUAFEED_SEED_TEMPLATES = [
	("SEED_AQUAFEED_MASTER_DATA", "Aquafeed Master Data AF01/AF02 (DP-597)", "Master Data", "enterprise_core.enterprise_core.aquafeed_seeds.seed_aquafeed_master_data", 10),
	("SEED_AQUAFEED_PRODUCTION", "Aquafeed Production AF03-AF07 (DP-598)", "Transaction", "enterprise_core.enterprise_core.aquafeed_seeds.seed_aquafeed_production", 20),
]

# Golden Demo #16 — Aquaculture Environmental Product Manufacturing (master plan DEMO 27,
# "PHASE 5" item 2, the last Phase 5 item), attached to IP-AQUA-ENVIRONMENT (already reserved
# in _INDUSTRY_PACKS above from DP-303).
_AQUA_ENV_SEED_TEMPLATES = [
	("SEED_AQUA_ENV_MASTER_DATA", "Aqua Environment Master Data (DP-600)", "Master Data", "enterprise_core.enterprise_core.aqua_env_seeds.seed_aqua_env_master_data", 10),
	("SEED_AQUA_ENV_PRODUCTION", "Aqua Environment Production AE02/AE03/AE05 (DP-601)", "Transaction", "enterprise_core.enterprise_core.aqua_env_seeds.seed_aqua_env_production", 20),
	("SEED_AQUA_ENV_FORMULA_REVISION", "Aqua Environment Formula Revision AE01 (DP-602)", "Transaction", "enterprise_core.enterprise_core.aqua_env_seeds.seed_aqua_env_formula_revision", 30),
	("SEED_AQUA_ENV_LABEL", "Aqua Environment Label Version AE04 (DP-603)", "Transaction", "enterprise_core.enterprise_core.aqua_env_seeds.seed_aqua_env_label", 40),
	("SEED_AQUA_ENV_DISTRIBUTION", "Aqua Environment Distribution Trace AE06 (DP-604)", "Transaction", "enterprise_core.enterprise_core.aqua_env_seeds.seed_aqua_env_distribution", 50),
]

# Golden Demo #17 — Fish Farm Management (master plan DEMO 29, "PHASE 5" item 3), attached to
# IP-FISH (already reserved in _INDUSTRY_PACKS above from DP-303).
_FISH_SEED_TEMPLATES = [
	("SEED_FISH_MASTER_DATA", "Fish Farm Master Data (DP-606)", "Master Data", "enterprise_core.enterprise_core.fish_seeds.seed_fish_farm_master_data", 10),
	("SEED_FISH_STOCKING", "Fish Stocking FF01 (DP-607)", "Transaction", "enterprise_core.enterprise_core.fish_seeds.seed_fish_stocking", 20),
	("SEED_FISH_OPERATIONS", "Fish Operations FF02/FF03/FF04/FF05 (DP-608)", "Transaction", "enterprise_core.enterprise_core.fish_seeds.seed_fish_operations", 30),
	("SEED_FISH_HARVEST", "Fish Harvest FF06 (DP-609)", "Transaction", "enterprise_core.enterprise_core.fish_seeds.seed_fish_harvest", 40),
	("SEED_FISH_VALIDATIONS", "Fish Validations FF01 (DP-610)", "Transaction", "enterprise_core.enterprise_core.fish_seeds.seed_fish_validations", 50),
]

# Golden Demo #18 — Aquaculture Hatchery / Seed Management (master plan DEMO 30, "PHASE 5"
# item 4), attached to IP-AQUA-HATCHERY (already reserved in _INDUSTRY_PACKS above from DP-303).
_AQUA_HATCHERY_SEED_TEMPLATES = [
	("SEED_AQUA_HATCHERY_MASTER_DATA", "Aqua Hatchery Master Data AH01 (DP-612)", "Master Data", "enterprise_core.enterprise_core.aqua_hatchery_seeds.seed_aqua_hatchery_master_data", 10),
	("SEED_AQUA_HATCHERY_SPAWNING", "Aqua Hatchery Spawning AH02 (DP-613)", "Transaction", "enterprise_core.enterprise_core.aqua_hatchery_seeds.seed_aqua_hatchery_spawning", 20),
	("SEED_AQUA_HATCHERY_LARVAL_NURSERY", "Aqua Hatchery Larval/Nursery AH03/AH04/AH05 (DP-614)", "Transaction", "enterprise_core.enterprise_core.aqua_hatchery_seeds.seed_aqua_hatchery_larval_nursery", 30),
	("SEED_AQUA_HATCHERY_DISPATCH", "Aqua Hatchery Dispatch AH06 (DP-615)", "Transaction", "enterprise_core.enterprise_core.aqua_hatchery_seeds.seed_aqua_hatchery_dispatch", 40),
	("SEED_AQUA_HATCHERY_VALIDATIONS", "Aqua Hatchery Validations AH01/AH04/AH06 (DP-616)", "Transaction", "enterprise_core.enterprise_core.aqua_hatchery_seeds.seed_aqua_hatchery_validations", 50),
]

# Golden Demo #19 — Seafood Processing & Export (master plan DEMO 32, "PHASE 5" item 5, the
# last Phase 5 item), attached to IP-SEAFOOD-PROCESSING (already reserved in _INDUSTRY_PACKS
# above from DP-303).
_SEAFOOD_SEED_TEMPLATES = [
	("SEED_SEAFOOD_MASTER_DATA", "Seafood Plant Master Data (DP-618)", "Master Data", "enterprise_core.enterprise_core.seafood_seeds.seed_seafood_master_data", 10),
	("SEED_SEAFOOD_RECEIVING_GRADING", "Seafood Receiving/Grading SP01/SP02 (DP-619)", "Transaction", "enterprise_core.enterprise_core.seafood_seeds.seed_seafood_receiving_and_grading", 20),
	("SEED_SEAFOOD_PROCESSING_PACKING", "Seafood Processing/Packing SP03/SP04/SP05 (DP-620)", "Transaction", "enterprise_core.enterprise_core.seafood_seeds.seed_seafood_processing_and_packing", 30),
	("SEED_SEAFOOD_SHIPMENT_RECALL", "Seafood Shipment/Recall SP06/SP08 (DP-621)", "Transaction", "enterprise_core.enterprise_core.seafood_seeds.seed_seafood_shipment_and_recall", 40),
	("SEED_SEAFOOD_VALIDATIONS", "Seafood Validations SP02/SP06 (DP-622)", "Transaction", "enterprise_core.enterprise_core.seafood_seeds.seed_seafood_validations", 50),
]

# Golden Demo #20 — Supplement / Nutraceutical Manufacturing (master plan DEMO 02, "PHASE 6"
# item 1), attached to IP-SUPPLEMENT (already reserved in _INDUSTRY_PACKS above from DP-303).
_SUPPLEMENT_SEED_TEMPLATES = [
	("SEED_SUPPLEMENT_MASTER_DATA", "Supplement Master Data S02/S04 (DP-624)", "Master Data", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_master_data", 10),
	("SEED_SUPPLEMENT_PRODUCTION", "Supplement Production S04 (DP-625)", "Transaction", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_production", 20),
	("SEED_SUPPLEMENT_FORMULA_REVISION", "Supplement Formula Revision S01 (DP-626)", "Transaction", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_formula_revision", 30),
	("SEED_SUPPLEMENT_ARTWORK", "Supplement Artwork Version S03 (DP-627)", "Transaction", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_artwork", 40),
	("SEED_SUPPLEMENT_COA", "Supplement COA S05 (DP-628)", "Transaction", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_coa", 50),
	("SEED_SUPPLEMENT_DISTRIBUTION", "Supplement Distribution Trace S06 (DP-629)", "Transaction", "enterprise_core.enterprise_core.supplement_seeds.seed_supplement_distribution", 60),
]

# Golden Demo #21 — Cosmetics Manufacturing (master plan DEMO 03, "PHASE 6" item 2), attached to
# IP-COSMETICS (already reserved in _INDUSTRY_PACKS above from DP-303).
_COSMETICS_SEED_TEMPLATES = [
	("SEED_COSMETICS_MASTER_DATA", "Cosmetics Master Data (DP-631)", "Master Data", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_master_data", 10),
	("SEED_COSMETICS_BULK_PRODUCTION", "Cosmetics Bulk Production (DP-632)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_bulk_production", 20),
	("SEED_COSMETICS_PACKED_PRODUCTION", "Cosmetics Packed Production C02 (DP-633)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_packed_production", 30),
	("SEED_COSMETICS_FORMULA_REVISION", "Cosmetics Formula Revision C01 (DP-634)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_formula_revision", 40),
	("SEED_COSMETICS_ARTWORK", "Cosmetics Artwork Version C03 (DP-635)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_artwork", 50),
	("SEED_COSMETICS_STABILITY", "Cosmetics Stability Schedule C04 (DP-636)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_stability", 60),
	("SEED_COSMETICS_DISTRIBUTION_COMPLAINT", "Cosmetics Distribution/Complaint C05 (DP-637)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_distribution_and_complaint", 70),
	("SEED_COSMETICS_REWORK", "Cosmetics Rework C06 (DP-638)", "Transaction", "enterprise_core.enterprise_core.cosmetics_seeds.seed_cosmetics_rework", 80),
]

# Golden Demo #22 — Medical Device Manufacturing (master plan DEMO 04, "PHASE 6" item 3),
# attached to IP-MEDICAL-DEVICE (already reserved in _INDUSTRY_PACKS above from DP-303).
_MEDDEV_SEED_TEMPLATES = [
	("SEED_MEDDEV_MASTER_DATA", "MedDev Master Data (DP-640)", "Master Data", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_master_data", 10),
	("SEED_MEDDEV_SUPPLIER_QUALIFICATION", "MedDev Supplier Qualification MD03 (DP-641)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_supplier_qualification", 20),
	("SEED_MEDDEV_BOM", "MedDev BOM MD02 (DP-642)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_bom", 30),
	("SEED_MEDDEV_INCOMING_INSPECTION", "MedDev Incoming Inspection MD04 (DP-643)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_incoming_inspection", 40),
	("SEED_MEDDEV_ASSEMBLY", "MedDev Assembly MD01/MD07 (DP-644)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_assembly", 50),
	("SEED_MEDDEV_RELEASE", "MedDev Release (DP-645)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_release", 60),
	("SEED_MEDDEV_TRACE_COMPLAINT", "MedDev Trace/Complaint MD05/MD06 (DP-646)", "Transaction", "enterprise_core.enterprise_core.meddev_seeds.seed_meddev_trace_and_complaint", 70),
]

# Golden Demo #23 — Pharmacy Chain (master plan DEMO 09, "PHASE 6" item 4), attached to
# IP-PHARMACY (new — a Pharmacy Chain retail vertical wasn't in DP-303's original 19-pack
# list, so it's registered here directly).
_PHARMACY_SEED_TEMPLATES = [
	("SEED_PHARMACY_MASTER_DATA", "Pharmacy Master Data (DP-648)", "Master Data", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_master_data", 10),
	("SEED_PHARMACY_REPLENISHMENT", "Pharmacy Replenishment RX02 (DP-649)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_replenishment", 20),
	("SEED_PHARMACY_INTER_STORE_TRANSFER", "Pharmacy Inter-Store Transfer RX04 (DP-650)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_inter_store_transfer", 30),
	("SEED_PHARMACY_POS_SESSION", "Pharmacy POS Session (DP-651)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_pos_session", 40),
	("SEED_PHARMACY_EXPIRY_BLOCK", "Pharmacy Expiry Block RX03 (DP-652)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_expiry_block", 50),
	("SEED_PHARMACY_POS_SALE", "Pharmacy POS Sale (DP-653)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_pos_sale", 60),
	("SEED_PHARMACY_POS_RETURN", "Pharmacy POS Return RX05 (DP-654)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_pos_return", 70),
	("SEED_PHARMACY_PROMOTION", "Pharmacy Promotion RX06 (DP-655)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_promotion", 80),
	("SEED_PHARMACY_DASHBOARD", "Pharmacy Central Dashboard RX07 (DP-656)", "Transaction", "enterprise_core.enterprise_core.pharmacy_seeds.seed_pharmacy_dashboard", 90),
]

# Golden Demo #24 — Pharma 3PL / GSP / Cold Chain (master plan DEMO 08, "PHASE 6" item 5),
# attached to IP-3PL-COLDCHAIN (new — a 3PL warehouse-operator vertical wasn't in DP-303's
# original 19-pack list, registered directly the same way IP-PHARMACY was for Golden Demo #23).
_3PL_SEED_TEMPLATES = [
	("SEED_3PL_MASTER_DATA", "3PL Master Data (DP-658)", "Master Data", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_master_data", 10),
	("SEED_3PL_INBOUND_RECEIVING", "3PL Inbound Receiving (DP-659)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_inbound_receiving", 20),
	("SEED_3PL_QUARANTINE_RELEASE", "3PL Quarantine Block + Release W04 (DP-660)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_quarantine_release", 30),
	("SEED_3PL_FEFO_OUTBOUND", "3PL FEFO Outbound W03 (DP-661)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_fefo_outbound", 40),
	("SEED_3PL_TEMPERATURE_MONITORING", "3PL Temperature Monitoring W02 (DP-662)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_temperature_monitoring", 50),
	("SEED_3PL_STOCK_RECONCILIATION", "3PL Stock Reconciliation W05 (DP-663)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_stock_reconciliation", 60),
	("SEED_3PL_ACCESS_CONTROL_TEST", "3PL Access Control W01 (DP-664)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_access_control_test", 70),
	("SEED_3PL_BILLING_RUN", "3PL Billing Run W06 (DP-665)", "Transaction", "enterprise_core.enterprise_core.threepl_seeds.seed_3pl_billing_run", 80),
]

# Golden Demo #25 — Consumer Health / Cosmetics Distribution (master plan DEMO 06, "PHASE 6"
# item 6), attached to IP-CONSUMER-DIST (new — a distributor/wholesaler vertical wasn't in
# DP-303's original 19-pack list, registered directly the same way IP-PHARMACY/IP-3PL-COLDCHAIN
# were for Golden Demo #23/#24).
_CONSUMER_DIST_SEED_TEMPLATES = [
	("SEED_CONSUMER_DIST_MASTER_DATA", "Consumer Dist Master Data (DP-666)", "Master Data", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_master_data", 10),
	("SEED_CONSUMER_DIST_PRICE_POLICY", "Consumer Dist Price Policy CD01 (DP-667)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_price_policy", 20),
	("SEED_CONSUMER_DIST_PROMOTION", "Consumer Dist Promotion CD02 (DP-668)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_promotion", 30),
	("SEED_CONSUMER_DIST_TERRITORY_CHECK", "Consumer Dist Territory CD03 (DP-669)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_territory_check", 40),
	("SEED_CONSUMER_DIST_CREDIT", "Consumer Dist Dealer Credit CD04 (DP-670)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_credit", 50),
	("SEED_CONSUMER_DIST_SALES_FLOW", "Consumer Dist Sales Flow (DP-671)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_sales_flow", 60),
	("SEED_CONSUMER_DIST_RETURN", "Consumer Dist Return CD05 (DP-672)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_return", 70),
	("SEED_CONSUMER_DIST_DASHBOARD", "Consumer Dist Commission Report + Dashboard CD06 (DP-673)", "Transaction", "enterprise_core.enterprise_core.consumer_dist_seeds.seed_consumer_dist_dashboard", 80),
]

# Golden Demo #26 — Premix / Feed Additive Manufacturing (master plan DEMO 19, "PHASE 6" item
# 7), attached to IP-PREMIX (already reserved in _INDUSTRY_PACKS above from DP-303, category
# "Animal Feed" — not re-added here).
_PREMIX_SEED_TEMPLATES = [
	("SEED_PREMIX_MASTER_DATA", "Premix Master Data PM04 (DP-675)", "Master Data", "enterprise_core.enterprise_core.premix_seeds.seed_premix_master_data", 10),
	("SEED_PREMIX_WEIGHING_VERIFICATION", "Premix Weighing Verification PM02 (DP-676)", "Transaction", "enterprise_core.enterprise_core.premix_seeds.seed_premix_weighing_verification", 20),
	("SEED_PREMIX_SEQUENCING", "Premix Sequencing PM03 (DP-677)", "Transaction", "enterprise_core.enterprise_core.premix_seeds.seed_premix_sequencing", 30),
	("SEED_PREMIX_MICRO_TOLERANCE", "Premix Micro-Weigh Tolerance PM01 (DP-678)", "Transaction", "enterprise_core.enterprise_core.premix_seeds.seed_premix_micro_tolerance", 40),
	("SEED_PREMIX_MANUFACTURING", "Premix Manufacturing PM06/PM07 (DP-679)", "Transaction", "enterprise_core.enterprise_core.premix_seeds.seed_premix_manufacturing", 50),
]

# Golden Demo #27 — Feed / Ingredient Trading (master plan DEMO 21, "PHASE 6" item 8), attached
# to IP-INGREDIENT-TRADING (new — registered above alongside IP-PHARMACY/IP-3PL-COLDCHAIN/
# IP-CONSUMER-DIST's own precedent for post-hoc pack additions).
_INGREDIENT_TRADING_SEED_TEMPLATES = [
	("SEED_INGREDIENT_TRADING_MASTER_DATA", "Ingredient Trading Master Data (DP-680)", "Master Data", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_master_data", 10),
	("SEED_INGREDIENT_TRADING_IMPORT_SHIPMENT", "Ingredient Trading Import Shipment FT01/FT02 (DP-681)", "Transaction", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_import_shipment", 20),
	("SEED_INGREDIENT_TRADING_SUPPLIER_LOT_QC", "Ingredient Trading Supplier Lot + QC FT03/FT04 (DP-682)", "Transaction", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_supplier_lot_qc", 30),
	("SEED_INGREDIENT_TRADING_CONTRACT_AND_SALES", "Ingredient Trading Contract + Sales FT05 (DP-683)", "Transaction", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_contract_and_sales", 40),
	("SEED_INGREDIENT_TRADING_PRICE_HISTORY", "Ingredient Trading Price History FT06 (DP-684)", "Transaction", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_price_history", 50),
	("SEED_INGREDIENT_TRADING_MARGIN_REPORT", "Ingredient Trading Margin Report FT07 (DP-685)", "Transaction", "enterprise_core.enterprise_core.ingredient_trading_seeds.seed_ingredient_trading_margin_report", 60),
]


# Golden Demo #28 — Meat / Animal Product Processing (master plan DEMO 31, "PHASE 6" item 9,
# the last Phase 6 item), attached to IP-MEAT-PROCESSING (already reserved in _INDUSTRY_PACKS
# above from DP-303, category "Processing" — no new pack registration needed).
_MEAT_PROCESSING_SEED_TEMPLATES = [
	("SEED_MEAT_PROCESSING_MASTER_DATA", "Meat Processing Master Data (DP-686)", "Master Data", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_master_data", 10),
	("SEED_MEAT_PROCESSING_RECEIVING", "Meat Processing Receiving MP01 (DP-687)", "Transaction", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_receiving", 20),
	("SEED_MEAT_PROCESSING_BATCH", "Meat Processing Batch MP02/MP03 (DP-688)", "Transaction", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_batch", 30),
	("SEED_MEAT_PROCESSING_QC_PACKING", "Meat Processing QC/Packing MP04/MP05 (DP-689)", "Transaction", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_qc_and_packing", 40),
	("SEED_MEAT_PROCESSING_DISTRIBUTION_RECALL", "Meat Processing Distribution/Recall MP06/MP07 (DP-690)", "Transaction", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_distribution_and_recall", 50),
	("SEED_MEAT_PROCESSING_VALIDATIONS", "Meat Processing Validations MP02 (DP-690)", "Transaction", "enterprise_core.enterprise_core.meat_processing_seeds.seed_meat_processing_validations", 60),
]


def seed_seed_templates():
	for template_code, template_name, seed_type, seed_function, _sequence in (
		_SEED_TEMPLATES
		+ _QMS_SEED_TEMPLATES
		+ _DMS_SEED_TEMPLATES
		+ _LIMS_SEED_TEMPLATES
		+ _EAM_SEED_TEMPLATES
		+ _FEED_SEED_TEMPLATES
		+ _SHRIMP_SEED_TEMPLATES
		+ _VET_MFG_SEED_TEMPLATES
		+ _PIG_SEED_TEMPLATES
		+ _POULTRY_SEED_TEMPLATES
		+ _CATTLE_SEED_TEMPLATES
		+ _HATCHERY_SEED_TEMPLATES
		+ _AQUAFEED_SEED_TEMPLATES
		+ _AQUA_ENV_SEED_TEMPLATES
		+ _FISH_SEED_TEMPLATES
		+ _AQUA_HATCHERY_SEED_TEMPLATES
		+ _SEAFOOD_SEED_TEMPLATES
		+ _SUPPLEMENT_SEED_TEMPLATES
		+ _COSMETICS_SEED_TEMPLATES
		+ _MEDDEV_SEED_TEMPLATES
		+ _PHARMACY_SEED_TEMPLATES
		+ _3PL_SEED_TEMPLATES
		+ _CONSUMER_DIST_SEED_TEMPLATES
		+ _PREMIX_SEED_TEMPLATES
		+ _INGREDIENT_TRADING_SEED_TEMPLATES
		+ _MEAT_PROCESSING_SEED_TEMPLATES
	):
		if frappe.db.exists("Seed Template", template_code):
			continue
		frappe.get_doc(
			{
				"doctype": "Seed Template",
				"template_code": template_code,
				"template_name": template_name,
				"seed_type": seed_type,
				"seed_function": seed_function,
			}
		).insert(ignore_permissions=True)


def _sync_industry_pack_seeds(pack_code, seed_templates):
	pack = frappe.get_doc("Industry Pack", pack_code)
	existing = {row.seed_template: row for row in pack.seeds}
	changed = False
	for template_code, _name, _type, _fn, sequence in seed_templates:
		if template_code in existing:
			if existing[template_code].sequence != sequence:
				existing[template_code].sequence = sequence
				changed = True
			continue
		pack.append("seeds", {"seed_template": template_code, "sequence": sequence, "is_required": 1})
		changed = True
	if changed:
		pack.save(ignore_permissions=True)


def seed_industry_pack_seeds():
	_sync_industry_pack_seeds("IP-PHARMA", _SEED_TEMPLATES)


def seed_industry_pack_qms_seeds():
	_sync_industry_pack_seeds("IP-QMS", _QMS_SEED_TEMPLATES)


def seed_industry_pack_dms_seeds():
	_sync_industry_pack_seeds("IP-DMS", _DMS_SEED_TEMPLATES)


def seed_industry_pack_lims_seeds():
	_sync_industry_pack_seeds("IP-LIMS", _LIMS_SEED_TEMPLATES)


def seed_industry_pack_eam_seeds():
	_sync_industry_pack_seeds("IP-EAM", _EAM_SEED_TEMPLATES)


def seed_industry_pack_feed_seeds():
	_sync_industry_pack_seeds("IP-FEED", _FEED_SEED_TEMPLATES)


def seed_industry_pack_shrimp_seeds():
	_sync_industry_pack_seeds("IP-SHRIMP", _SHRIMP_SEED_TEMPLATES)


def seed_industry_pack_vet_mfg_seeds():
	_sync_industry_pack_seeds("IP-VETERINARY", _VET_MFG_SEED_TEMPLATES)


def seed_industry_pack_pig_seeds():
	_sync_industry_pack_seeds("IP-LIVESTOCK-PIG", _PIG_SEED_TEMPLATES)


def seed_industry_pack_poultry_seeds():
	_sync_industry_pack_seeds("IP-LIVESTOCK-POULTRY", _POULTRY_SEED_TEMPLATES)


def seed_industry_pack_cattle_seeds():
	_sync_industry_pack_seeds("IP-LIVESTOCK-CATTLE", _CATTLE_SEED_TEMPLATES)


def seed_industry_pack_hatchery_seeds():
	_sync_industry_pack_seeds("IP-HATCHERY", _HATCHERY_SEED_TEMPLATES)


def seed_industry_pack_aquafeed_seeds():
	_sync_industry_pack_seeds("IP-AQUAFEED", _AQUAFEED_SEED_TEMPLATES)


def seed_industry_pack_aqua_env_seeds():
	_sync_industry_pack_seeds("IP-AQUA-ENVIRONMENT", _AQUA_ENV_SEED_TEMPLATES)


def seed_industry_pack_fish_seeds():
	_sync_industry_pack_seeds("IP-FISH", _FISH_SEED_TEMPLATES)


def seed_industry_pack_aqua_hatchery_seeds():
	_sync_industry_pack_seeds("IP-AQUA-HATCHERY", _AQUA_HATCHERY_SEED_TEMPLATES)


def seed_industry_pack_seafood_seeds():
	_sync_industry_pack_seeds("IP-SEAFOOD-PROCESSING", _SEAFOOD_SEED_TEMPLATES)


def seed_industry_pack_supplement_seeds():
	_sync_industry_pack_seeds("IP-SUPPLEMENT", _SUPPLEMENT_SEED_TEMPLATES)


def seed_industry_pack_cosmetics_seeds():
	_sync_industry_pack_seeds("IP-COSMETICS", _COSMETICS_SEED_TEMPLATES)


def seed_industry_pack_meddev_seeds():
	_sync_industry_pack_seeds("IP-MEDICAL-DEVICE", _MEDDEV_SEED_TEMPLATES)


def seed_industry_pack_pharmacy_seeds():
	_sync_industry_pack_seeds("IP-PHARMACY", _PHARMACY_SEED_TEMPLATES)


def seed_industry_pack_3pl_seeds():
	_sync_industry_pack_seeds("IP-3PL-COLDCHAIN", _3PL_SEED_TEMPLATES)


def seed_industry_pack_consumer_dist_seeds():
	_sync_industry_pack_seeds("IP-CONSUMER-DIST", _CONSUMER_DIST_SEED_TEMPLATES)


def seed_industry_pack_premix_seeds():
	_sync_industry_pack_seeds("IP-PREMIX", _PREMIX_SEED_TEMPLATES)


def seed_industry_pack_ingredient_trading_seeds():
	_sync_industry_pack_seeds("IP-INGREDIENT-TRADING", _INGREDIENT_TRADING_SEED_TEMPLATES)


def seed_industry_pack_meat_processing_seeds():
	_sync_industry_pack_seeds("IP-MEAT-PROCESSING", _MEAT_PROCESSING_SEED_TEMPLATES)


def seed_ai_foundation_wrapper():
	# Phase 2A (CE-13) — cross-cutting platform infrastructure, not tied to any single
	# Industry Pack, so it runs unconditionally here rather than through the per-pack Seed
	# Template registry (same status as DP-301..307's own registries above).
	from enterprise_core.enterprise_core.ai_seeds import seed_ai_foundation

	seed_ai_foundation()


def seed_ai_executive_assistant_wrapper():
	# Phase 6A (AI-DEMO-01 — Executive Assistant + Tool Registry) — a direct extension of
	# CE-13's cross-cutting AI foundation, not an industry vertical, so it follows the exact
	# same unconditional-in-after_install/after_migrate precedent as
	# seed_ai_foundation_wrapper() above rather than going through the per-pack Seed Template
	# registry. Runs AFTER seed_ai_foundation_wrapper() (needs AI Provider/Model/Tenant Policy
	# already seeded) and after the industry pack seeds above (its revenue-history seed data
	# depends on Golden Demo #25's Consumer Distribution company already existing — it
	# self-skips gracefully if that company isn't there yet).
	from enterprise_core.enterprise_core.ai_executive_assistant_seeds import seed_ai_executive_assistant

	seed_ai_executive_assistant()


def seed_ai_qms_copilot_wrapper():
	# Phase 6A (AI-DEMO-02 — QMS Copilot) — same unconditional-in-after_install/after_migrate
	# precedent as seed_ai_executive_assistant_wrapper() above: cross-cutting AI infra, not an
	# industry vertical, extending the SAME shared AI Tool registry (not a parallel one). Runs
	# AFTER seed_ai_executive_assistant_wrapper() (needs AI Provider/Model/Tenant Policy already
	# seeded) and after seed_industry_pack_qms_seeds() above (its own tool data depends on
	# Golden Demo #2/#3's QMS Deviation/CAPA/Audit records already existing — it also calls the
	# base QMS seed functions defensively itself, so it self-heals if run first).
	from enterprise_core.enterprise_core.ai_qms_copilot_seeds import seed_ai_qms_copilot

	seed_ai_qms_copilot()


def seed_ai_dms_copilot_wrapper():
	# Phase 6A (AI-DEMO-03 — DMS Copilot) — same unconditional-in-after_install/after_migrate
	# precedent as seed_ai_qms_copilot_wrapper() above: cross-cutting AI infra, not an industry
	# vertical, extending the SAME shared AI Tool registry (not a parallel one). Runs AFTER
	# seed_ai_qms_copilot_wrapper() (needs AI Provider/Model/Tenant Policy already seeded) and
	# after seed_industry_pack_dms_seeds() above (its own tool data depends on Golden Demo #4's
	# DMS Document/Version/Training Assignment records already existing — it also calls the
	# base DMS seed functions defensively itself, so it self-heals if run first).
	from enterprise_core.enterprise_core.ai_dms_copilot_seeds import seed_ai_dms_copilot

	seed_ai_dms_copilot()


def seed_ai_manufacturing_insight_wrapper():
	# Phase 6A (AI-DEMO-05 — Manufacturing Insight) — same unconditional-in-after_install/
	# after_migrate precedent as seed_ai_dms_copilot_wrapper() above: cross-cutting AI infra,
	# not an industry vertical, extending the SAME shared AI Tool registry (not a parallel
	# one). Runs AFTER seed_ai_dms_copilot_wrapper() (needs AI Provider/Model/Tenant Policy
	# already seeded) and after seed_industry_pack_premix_seeds() above (its own isolated
	# item/Work Order data depends on Golden Demo #26's own flagship Work Order already
	# existing — it self-skips gracefully if that isn't there yet, and deliberately does NOT
	# call any of premix_seeds.py's own Work-Order-related functions itself, to avoid the
	# "at most one Work Order" ambiguity documented in ai_manufacturing_insight_seeds.py's own
	# module docstring).
	from enterprise_core.enterprise_core.ai_manufacturing_insight_seeds import seed_ai_manufacturing_insight

	seed_ai_manufacturing_insight()


def seed_ai_procurement_assistant_wrapper():
	# Phase 6A (AI-DEMO-06 — Procurement Assistant) — same unconditional-in-after_install/
	# after_migrate precedent as seed_ai_manufacturing_insight_wrapper() above: cross-cutting AI
	# infra, not an industry vertical, extending the SAME shared AI Tool registry (not a parallel
	# one). Runs AFTER seed_ai_manufacturing_insight_wrapper() (needs AI Provider/Model/Tenant
	# Policy already seeded) and after seed_industry_pack_ingredient_trading_seeds() above (its
	# own Supplier Quotation fixtures and isolated declining-supplier-history data depend on
	# Golden Demo #27's real suppliers/USD-payable-account already existing — it self-skips
	# gracefully if that isn't there yet). A deliberate HYBRID design (4 analytical use cases
	# NO-DRAFT like AI-DEMO-05, the 5th supplier-qualification-recommendation DRAFT-gated like
	# AI-DEMO-02) — see ai_procurement_assistant.py's own module docstring.
	from enterprise_core.enterprise_core.ai_procurement_assistant_seeds import seed_ai_procurement_assistant

	seed_ai_procurement_assistant()


def seed_ai_farm_aquaculture_insight_wrapper():
	# Phase 6A (AI-DEMO-09 Livestock Farm Assistant + AI-DEMO-10 Shrimp/Aquaculture Assistant,
	# the master plan's own curated Phase 6A summary list treats these as ONE combined item) —
	# same unconditional-in-after_install/after_migrate precedent as
	# seed_ai_procurement_assistant_wrapper() above: cross-cutting AI infra, not an industry
	# vertical, extending the SAME shared AI Tool registry (not a parallel one). Runs AFTER
	# seed_ai_procurement_assistant_wrapper() (needs AI Provider/Model/Tenant Policy already
	# seeded) and after seed_industry_pack_pig_seeds()/seed_industry_pack_shrimp_seeds() above
	# (its own isolated Pen/Pond cohort data depends on Golden Demo #11/#8's own flagship
	# Grower Batch/Pond already existing) — it also self-skips gracefully per vertical if that
	# flagship data isn't there yet, the same "at most one" pen/pond-collision-avoidance
	# discipline AI-DEMO-05/06 established (see ai_farm_aquaculture_insight_seeds.py's own
	# module docstring for the full isolation rationale — NO-DRAFT like AI-DEMO-05, both
	# verticals built together under one entry-point module per the task's own instruction).
	from enterprise_core.enterprise_core.ai_farm_aquaculture_insight_seeds import seed_ai_farm_aquaculture_insight

	seed_ai_farm_aquaculture_insight()


def seed_ai_permission_aware_rag_wrapper():
	# Phase 6A — Permission-aware RAG, the eighth Phase 6A item (master plan §13.9 "RAG /
	# Enterprise Knowledge"). Same unconditional-in-after_install/after_migrate precedent as
	# seed_ai_farm_aquaculture_insight_wrapper() above: cross-cutting AI infra, not an industry
	# vertical, extending the SAME shared AI Tool registry (not a parallel one). Runs AFTER
	# seed_ai_farm_aquaculture_insight_wrapper() (needs AI Provider/Model/Tenant Policy already
	# seeded) and after seed_industry_pack_dms_seeds() above (its own isolated SOP-CAL-01 document
	# is new/self-contained, but the corpus backfill step re-indexes Golden Demo #4's own
	# SOP-WH-02 versions too, so DMS must already exist). Also registers the additive `hooks.py`
	# doc_events entry (`rag_pipeline.reindex_document_version_on_update`) that keeps the RAG
	# Chunk vector index in sync with DMS Document Version's own revision/effective-status
	# lifecycle going forward — see rag_pipeline.py's own module docstring for the full design.
	from enterprise_core.enterprise_core.ai_permission_aware_rag_seeds import seed_ai_permission_aware_rag

	seed_ai_permission_aware_rag()


def seed_ai_evaluation_datasets_wrapper():
	# Phase 6A — Evaluation Datasets, the NINTH and FINAL curated Phase 6A item (master plan
	# §13.14 "AI Evaluation"). Same unconditional-in-after_install/after_migrate precedent as
	# seed_ai_permission_aware_rag_wrapper() above: cross-cutting AI infra, not an industry
	# vertical, extending the SAME shared AI Tool registry (not a parallel one). Runs AFTER
	# seed_ai_permission_aware_rag_wrapper() (needs AI Provider/Model/Tenant Policy already
	# seeded) and after seed_industry_pack_qms_seeds() above (depends on Golden Demo #2/#3's own
	# QMS Deviation flow/OOS/validations already having run — it calls them itself, defensively,
	# same precedent as ai_qms_copilot_seeds.seed_ai_qms_copilot()). Registers `classify_complaint`
	# (a new, minimal AI Action/Tool built specifically so this demo has a second real action to
	# evaluate, per master plan §13.14's own worked example), a small disabled-by-default
	# capability-incomplete AI Model fixture (used only by check_model_swap_safe()'s own negative
	# test), 2 new isolated QMS Deviation records (severity/category coverage the 5 real,
	# pre-existing Deviations don't have) and 12 new isolated QMS Complaint records (QMS Complaint
	# had zero pre-existing records platform-wide) — see ai_evaluation_seeds.py's own module
	# docstring for the full rationale.
	from enterprise_core.enterprise_core.ai_evaluation_seeds import seed_ai_evaluation_datasets

	seed_ai_evaluation_datasets()


# The platform's own 2 demo/sales sites (see frappe_docker_demo/scripts/_lib.sh's own
# REAL_SITES) — the only sites that should ever get real golden-demo SHOWCASE data (fake
# companies, hardcoded demo users like qa.manager@pharmacountry.vn, AI chat history, etc.). A
# real tenant site provisioned via scripts/provision-tenant.sh must start clean with just the
# platform's own catalog (Capability Engines/Editions/Industry Packs/Templates — seeded
# unconditionally below, harmless metadata, not demo data) — never pre-loaded with another
# company's fake data. Confirmed live: without this gate, a fresh tenant site hard-crashes
# partway through the AI wrapper functions, which hardcode assumptions (specific demo
# users/companies) that only the 2 real sites actually have.
_DEMO_SHOWCASE_SITES = {"test.demo.local", "pharmacountry.vn"}


def seed_demo_showcase_data():
	if frappe.local.site not in _DEMO_SHOWCASE_SITES:
		return
	seed_ai_foundation_wrapper()
	seed_ai_executive_assistant_wrapper()
	seed_ai_qms_copilot_wrapper()
	seed_ai_dms_copilot_wrapper()
	seed_ai_manufacturing_insight_wrapper()
	seed_ai_procurement_assistant_wrapper()
	seed_ai_farm_aquaculture_insight_wrapper()
	seed_ai_permission_aware_rag_wrapper()
	seed_ai_evaluation_datasets_wrapper()


def after_install():
	seed_erpnext_fixtures()
	seed_capability_engines()
	seed_feature_flags()
	seed_sample_edition()
	seed_product_editions()
	seed_industry_packs()
	sync_industry_pack_default_editions()
	seed_role_templates()
	seed_industry_pack_roles()
	seed_workspace_templates()
	seed_industry_pack_workspaces()
	seed_seed_templates()
	seed_industry_pack_seeds()
	seed_industry_pack_qms_seeds()
	seed_industry_pack_dms_seeds()
	seed_industry_pack_lims_seeds()
	seed_industry_pack_eam_seeds()
	seed_industry_pack_feed_seeds()
	seed_industry_pack_shrimp_seeds()
	seed_industry_pack_vet_mfg_seeds()
	seed_industry_pack_pig_seeds()
	seed_industry_pack_poultry_seeds()
	seed_industry_pack_cattle_seeds()
	seed_industry_pack_hatchery_seeds()
	seed_industry_pack_aquafeed_seeds()
	seed_industry_pack_aqua_env_seeds()
	seed_industry_pack_fish_seeds()
	seed_industry_pack_aqua_hatchery_seeds()
	seed_industry_pack_seafood_seeds()
	seed_industry_pack_supplement_seeds()
	seed_industry_pack_cosmetics_seeds()
	seed_industry_pack_meddev_seeds()
	seed_industry_pack_pharmacy_seeds()
	seed_industry_pack_3pl_seeds()
	seed_industry_pack_consumer_dist_seeds()
	seed_industry_pack_premix_seeds()
	seed_industry_pack_ingredient_trading_seeds()
	seed_industry_pack_meat_processing_seeds()
	seed_demo_showcase_data()


def after_migrate():
	seed_erpnext_fixtures()
	seed_capability_engines()
	seed_feature_flags()
	seed_sample_edition()
	seed_product_editions()
	seed_industry_packs()
	sync_industry_pack_default_editions()
	seed_role_templates()
	seed_industry_pack_roles()
	seed_workspace_templates()
	seed_industry_pack_workspaces()
	seed_seed_templates()
	seed_industry_pack_seeds()
	seed_industry_pack_qms_seeds()
	seed_industry_pack_dms_seeds()
	seed_industry_pack_lims_seeds()
	seed_industry_pack_eam_seeds()
	seed_industry_pack_feed_seeds()
	seed_industry_pack_shrimp_seeds()
	seed_industry_pack_vet_mfg_seeds()
	seed_industry_pack_pig_seeds()
	seed_industry_pack_poultry_seeds()
	seed_industry_pack_cattle_seeds()
	seed_industry_pack_hatchery_seeds()
	seed_industry_pack_aquafeed_seeds()
	seed_industry_pack_aqua_env_seeds()
	seed_industry_pack_fish_seeds()
	seed_industry_pack_aqua_hatchery_seeds()
	seed_industry_pack_seafood_seeds()
	seed_industry_pack_supplement_seeds()
	seed_industry_pack_cosmetics_seeds()
	seed_industry_pack_meddev_seeds()
	seed_industry_pack_pharmacy_seeds()
	seed_industry_pack_3pl_seeds()
	seed_industry_pack_consumer_dist_seeds()
	seed_industry_pack_premix_seeds()
	seed_industry_pack_ingredient_trading_seeds()
	seed_industry_pack_meat_processing_seeds()
	seed_demo_showcase_data()
