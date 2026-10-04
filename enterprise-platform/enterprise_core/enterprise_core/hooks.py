app_name = "enterprise_core"
app_title = "Enterprise Core"
app_publisher = "Enterprise Platform"
app_description = "Cross-industry ERP capability platform (Edition/Feature/Industry Pack config layer)"
app_email = "noreply@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "enterprise_core",
# 		"logo": "/assets/enterprise_core/logo.png",
# 		"title": "Enterprise Core",
# 		"route": "/enterprise_core",
# 		"has_permission": "enterprise_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/enterprise_core/css/enterprise_core.css"
# app_include_js = "/assets/enterprise_core/js/enterprise_core.js"

# include js, css files in header of web template
# web_include_css = "/assets/enterprise_core/css/enterprise_core.css"
# web_include_js = "/assets/enterprise_core/js/enterprise_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "enterprise_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "enterprise_core/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "enterprise_core.utils.jinja_methods",
# 	"filters": "enterprise_core.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "enterprise_core.install.before_install"
after_install = "enterprise_core.setup.after_install"
after_migrate = "enterprise_core.setup.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "enterprise_core.uninstall.before_uninstall"
# after_uninstall = "enterprise_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "enterprise_core.utils.before_app_install"
# after_app_install = "enterprise_core.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "enterprise_core.utils.before_app_uninstall"
# after_app_uninstall = "enterprise_core.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "enterprise_core.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "enterprise_core.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["enterprise_core.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Stock Entry": {
		"validate": [
			"enterprise_core.enterprise_core.validations.block_quarantine_issue_to_production",
			"enterprise_core.enterprise_core.validations.block_fg_release_without_qa",
			"enterprise_core.enterprise_core.feed_validations.block_weighing_tolerance_exceeded",
			"enterprise_core.enterprise_core.meddev_validations.meddev_block_rejected_material_use",
			"enterprise_core.enterprise_core.premix_validations.block_micro_weigh_tolerance_exceeded",
			"enterprise_core.enterprise_core.premix_validations.block_manufacture_without_second_check",
			"enterprise_core.enterprise_core.premix_validations.block_sequence_violation",
		],
	},
	"Work Order": {
		"validate": [
			"enterprise_core.enterprise_core.feed_validations.block_line_not_cleaned_after_allergen",
			"enterprise_core.enterprise_core.meddev_validations.meddev_block_overdue_equipment_operation",
		],
	},
	"BOM": {
		"validate": [
			"enterprise_core.enterprise_core.meddev_validations.meddev_bom_validate",
			"enterprise_core.enterprise_core.premix_validations.block_bom_default_without_approval",
		],
	},
	"Purchase Order": {
		"validate": "enterprise_core.enterprise_core.meddev_validations.meddev_block_critical_supplier_not_approved",
	},
	"Delivery Note": {
		"validate": [
			"enterprise_core.enterprise_core.validations.block_recalled_batch_delivery",
			"enterprise_core.enterprise_core.threepl_validations.block_quarantine_delivery",
		],
	},
	"QMS Deviation": {
		"validate": "enterprise_core.enterprise_core.qms_validations.qms_deviation_validate",
	},
	"QMS CAPA": {
		"validate": "enterprise_core.enterprise_core.qms_validations.qms_capa_validate",
	},
	"AI Draft": {
		"validate": "enterprise_core.enterprise_core.ai_drafts.ai_draft_validate",
	},
	"DMS Document Version": {
		"validate": "enterprise_core.enterprise_core.dms_validations.dms_document_version_validate",
		# Phase 6A — Permission-aware RAG: an ADDITIVE second on_update handler (hooks.py doc_events
		# supports a list per event), never a replacement for dms_validations' own D02/D04 handler.
		# Runs unconditionally on every version save (not just status=="Effective" transitions) so
		# ANY revision/status change keeps the RAG Chunk vector index honest — master plan §13.9's
		# own "Re-index khi document revision/effective status thay đổi" requirement, wired as a
		# real event. Order matters: dms_validations' own handler must run FIRST so DMS Document's
		# current_version/status are already updated before rag_pipeline re-derives is_current — see
		# rag_pipeline.py's module docstring for the full re-index design (including how this SAME
		# hook automatically re-indexes a superseded sibling version too, via its own nested .save()).
		"on_update": [
			"enterprise_core.enterprise_core.dms_validations.dms_document_version_on_update",
			"enterprise_core.enterprise_core.rag_pipeline.reindex_document_version_on_update",
		],
	},
	"LIMS Sample": {
		"validate": "enterprise_core.enterprise_core.lims_validations.lims_sample_validate",
	},
	"LIMS Test": {
		"validate": "enterprise_core.enterprise_core.lims_validations.lims_test_validate",
		"on_update": "enterprise_core.enterprise_core.lims_validations.lims_test_on_update",
	},
	"LIMS COA": {
		"validate": "enterprise_core.enterprise_core.lims_validations.lims_coa_validate",
	},
	"EAM Qualification": {
		"validate": "enterprise_core.enterprise_core.eam_validations.eam_qualification_validate",
	},
	"Shrimp Pond": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations.shrimp_pond_validate",
	},
	"Shrimp Stocking Batch": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations.shrimp_stocking_batch_validate",
		"on_update": "enterprise_core.enterprise_core.shrimp_validations.shrimp_stocking_batch_on_update",
	},
	"Shrimp Daily Feed Log": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations._block_if_batch_not_active",
	},
	"Shrimp Growth Sample": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations._block_if_batch_not_active",
	},
	"Shrimp Health Treatment": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations._block_if_batch_not_active",
	},
	"Shrimp Mortality Record": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations._block_if_batch_not_active",
	},
	"Shrimp Water Parameter Reading": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations.shrimp_water_reading_validate",
	},
	"Shrimp Harvest": {
		"validate": "enterprise_core.enterprise_core.shrimp_validations.shrimp_harvest_validate",
		"on_update": "enterprise_core.enterprise_core.shrimp_validations.shrimp_harvest_on_update",
	},
	"Pig Breeding Service": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_breeding_service_validate",
	},
	"Pig Farrowing": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_farrowing_validate",
		"on_update": "enterprise_core.enterprise_core.pig_validations.pig_farrowing_on_update",
	},
	"Pig Grower Batch": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_grower_batch_validate",
		"on_update": "enterprise_core.enterprise_core.pig_validations.pig_grower_batch_on_update",
	},
	"Pig Feed Log": {
		"validate": "enterprise_core.enterprise_core.pig_validations._block_if_batch_not_active",
	},
	"Pig Vaccination": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_vaccination_validate",
	},
	"Pig Medicine Treatment": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_medicine_treatment_validate",
	},
	"Pig Weight Record": {
		"validate": "enterprise_core.enterprise_core.pig_validations._block_if_batch_not_active",
	},
	"Pig Mortality Record": {
		"validate": "enterprise_core.enterprise_core.pig_validations._block_if_batch_not_active",
	},
	"Pig Sale Lot": {
		"validate": "enterprise_core.enterprise_core.pig_validations.pig_sale_lot_validate",
		"on_update": "enterprise_core.enterprise_core.pig_validations.pig_sale_lot_on_update",
	},
	"Poultry Flock": {
		"validate": "enterprise_core.enterprise_core.poultry_validations.poultry_flock_validate",
		"on_update": "enterprise_core.enterprise_core.poultry_validations.poultry_flock_on_update",
	},
	"Poultry Feed Log": {
		"validate": "enterprise_core.enterprise_core.poultry_validations._block_if_flock_not_active",
	},
	"Poultry Vaccination": {
		"validate": "enterprise_core.enterprise_core.poultry_validations.poultry_vaccination_validate",
	},
	"Poultry Weight Record": {
		"validate": "enterprise_core.enterprise_core.poultry_validations._block_if_flock_not_active",
	},
	"Poultry Mortality Record": {
		"validate": "enterprise_core.enterprise_core.poultry_validations._block_if_flock_not_active",
	},
	"Poultry Egg Production": {
		"validate": "enterprise_core.enterprise_core.poultry_validations.poultry_egg_production_validate",
	},
	"Poultry Sale Lot": {
		"validate": "enterprise_core.enterprise_core.poultry_validations.poultry_sale_lot_validate",
		"on_update": "enterprise_core.enterprise_core.poultry_validations.poultry_sale_lot_on_update",
	},
	"Cattle Animal": {
		"validate": "enterprise_core.enterprise_core.cattle_validations.cattle_animal_validate",
	},
	"Cattle Breeding Service": {
		"validate": "enterprise_core.enterprise_core.cattle_validations.cattle_breeding_service_validate",
	},
	"Cattle Calving": {
		"validate": "enterprise_core.enterprise_core.cattle_validations.cattle_calving_validate",
		"on_update": "enterprise_core.enterprise_core.cattle_validations.cattle_calving_on_update",
	},
	"Cattle Milking Record": {
		"validate": "enterprise_core.enterprise_core.cattle_validations.cattle_milking_record_validate",
	},
	"Cattle Health Treatment": {
		"validate": "enterprise_core.enterprise_core.cattle_validations._block_if_animal_not_active",
	},
	"Cattle Feed Log": {
		"validate": "enterprise_core.enterprise_core.cattle_validations._block_if_animal_not_active",
	},
	"Cattle Sale Lot": {
		"validate": "enterprise_core.enterprise_core.cattle_validations.cattle_sale_lot_validate",
		"on_update": "enterprise_core.enterprise_core.cattle_validations.cattle_sale_lot_on_update",
	},
	"Hatchery Incubation": {
		"validate": "enterprise_core.enterprise_core.hatchery_validations.hatchery_incubation_validate",
		"on_update": "enterprise_core.enterprise_core.hatchery_validations.hatchery_incubation_on_update",
	},
	"Hatchery Hatch Result": {
		"validate": "enterprise_core.enterprise_core.hatchery_validations.hatchery_hatch_result_validate",
		"on_update": "enterprise_core.enterprise_core.hatchery_validations.hatchery_hatch_result_on_update",
	},
	"Hatchery Chick Grading": {
		"validate": "enterprise_core.enterprise_core.hatchery_validations.hatchery_chick_grading_validate",
	},
	"Hatchery Vaccination": {
		"validate": "enterprise_core.enterprise_core.hatchery_validations.hatchery_vaccination_validate",
	},
	"Hatchery Dispatch": {
		"validate": "enterprise_core.enterprise_core.hatchery_validations.hatchery_dispatch_validate",
		"on_update": "enterprise_core.enterprise_core.hatchery_validations.hatchery_dispatch_on_update",
	},
	"Meat Processing Batch": {
		"validate": "enterprise_core.enterprise_core.meat_processing_validations.meat_processing_batch_validate",
	},
	"Meat Packing Lot": {
		"validate": "enterprise_core.enterprise_core.meat_processing_validations.meat_packing_lot_validate",
	},
	"Meat Distribution": {
		"validate": "enterprise_core.enterprise_core.meat_processing_validations.meat_distribution_validate",
		"on_update": "enterprise_core.enterprise_core.meat_processing_validations.meat_distribution_on_update",
	},
	"Fish Pond": {
		"validate": "enterprise_core.enterprise_core.fish_validations.fish_pond_validate",
	},
	"Fish Stocking Batch": {
		"validate": "enterprise_core.enterprise_core.fish_validations.fish_stocking_batch_validate",
		"on_update": "enterprise_core.enterprise_core.fish_validations.fish_stocking_batch_on_update",
	},
	"Fish Feed Log": {
		"validate": "enterprise_core.enterprise_core.fish_validations._block_if_batch_not_active",
	},
	"Fish Growth Sample": {
		"validate": "enterprise_core.enterprise_core.fish_validations.fish_growth_sample_validate",
	},
	"Fish Mortality Record": {
		"validate": "enterprise_core.enterprise_core.fish_validations._block_if_batch_not_active",
	},
	"Fish Harvest": {
		"validate": "enterprise_core.enterprise_core.fish_validations.fish_harvest_validate",
		"on_update": "enterprise_core.enterprise_core.fish_validations.fish_harvest_on_update",
	},
	"Aqua Spawning Batch": {
		"validate": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_spawning_batch_validate",
	},
	"Aqua Larval Batch": {
		"validate": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_larval_batch_validate",
		"on_update": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_larval_batch_on_update",
	},
	"Aqua Health Record": {
		"validate": "enterprise_core.enterprise_core.aqua_hatchery_validations._block_if_nursery_not_active",
	},
	"Aqua Seed Batch": {
		"validate": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_seed_batch_validate",
		"on_update": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_seed_batch_on_update",
	},
	"Aqua Seed Dispatch": {
		"validate": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_seed_dispatch_validate",
		"on_update": "enterprise_core.enterprise_core.aqua_hatchery_validations.aqua_seed_dispatch_on_update",
	},
	"Seafood Grading": {
		"validate": "enterprise_core.enterprise_core.seafood_validations.seafood_grading_validate",
	},
	"Seafood Shipment": {
		"validate": "enterprise_core.enterprise_core.seafood_validations.seafood_shipment_validate",
		"on_update": "enterprise_core.enterprise_core.seafood_validations.seafood_shipment_on_update",
	},
	"Cosmetics Stability Sample": {
		"validate": "enterprise_core.enterprise_core.cosmetics_validations.cosmetics_stability_sample_validate",
	},
	"Cold Chain Temperature Reading": {
		"validate": "enterprise_core.enterprise_core.threepl_validations.threepl_temperature_reading_validate",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"enterprise_core.tasks.all"
# 	],
# 	"daily": [
# 		"enterprise_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"enterprise_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"enterprise_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"enterprise_core.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "enterprise_core.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "enterprise_core.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "enterprise_core.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "enterprise_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["enterprise_core.utils.before_request"]
# after_request = ["enterprise_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["enterprise_core.utils.before_job"]
# after_job = ["enterprise_core.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"enterprise_core.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

