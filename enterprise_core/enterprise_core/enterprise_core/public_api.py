"""WEB-01 — Corporate + Product Catalog public API (Phase 7 "Specialized UX/Portal/Web",
master plan §8 lines ~2557-2558: "WEB-01 Corporate + Product Catalog — Cho nha may/nha phan
phoi" — for a factory/distributor). Backs the standalone Next.js site in
`nextjs-demo/web-01-corporate-catalog/`.

SECURITY MODEL — read this before touching this file:
  Every function here is `@frappe.whitelist(allow_guest=True, methods=["GET"])`: reachable
  over HTTP with ZERO authentication, exactly like a real public corporate website. There is
  no logged-in user to scope permissions to, so this module does NOT rely on ambient
  `get_list()` permission filtering at all — every query below is an EXPLICIT, hand-picked
  `fields`/`fieldname` allow-list (never `"*"`, never a raw doctype dump, never `get_all()`).
  It reads ONLY:
    - Company: company_name, country, default_currency (nothing financial/internal).
    - Item: item_code, item_name, stock_uom, restricted to a SAFE SET computed by
      `_safe_item_codes()` below (see its docstring) — never cost/valuation rate, stock qty,
      warehouse, batch/lot, supplier, or any manufacturing/QC field.
    - Item Price: price_list_rate + currency on the public "Standard Selling" list only —
      never the internal dealer-tier price list, never a purchase/buying price.
  No customer, dealer, territory, commission, supplier, or financial-account data is ever
  touched by this module. The showcased company/price-list names are hardcoded module
  constants, NOT accepted as request parameters — a guest can never ask this API to describe
  a different company or a different (e.g. internal dealer-tier) price list.

DATA SOURCE CHOICE — why "Demo Consumer Distribution Co." (Golden Demo #25):
  Checked 3 candidates before picking one (grepped every `*_seeds.py` for `description`,
  `image`, `standard_rate`/`Item Price` fields, then confirmed the actual live field values
  via `bench execute` against `test.demo.local`):
    - Golden Demo #1 (Demo Pharma Co, the flagship manufacturer) — real Items, but a
      manufacturer's raw-material/tablet SKUs (Paracetamol API, MCC, PVC/Alu blister foil)
      with NO Item Price data anywhere (it never sells to an end customer) — poor fit for a
      public "product catalog with pricing".
    - Golden Demo #21 (Cosmetics manufacturer) — consumer-facing finished goods (facial
      cleanser) but likewise NO Item Price data — it manufactures for a distributor, doesn't
      sell direct.
    - Golden Demo #25 (Demo Consumer Distribution Co., IP-CONSUMER-DIST) — a genuine
      DISTRIBUTOR (matches WEB-01's own spec text) that receives and resells 2 real,
      consumer-facing finished goods reused from Golden Demo #20 (Supplement,
      VITC-1000-EFF) and Golden Demo #21 (Cosmetics, FACIAL-CLEANSER-150ML), and — uniquely
      among every golden demo — has REAL `Item Price` rows on the public "Standard Selling"
      price list (260,000 VND / 95,000 VND, confirmed live) because its own CD01 test
      (consumer_dist_seeds.py) depends on that exact price data existing. This is the only
      golden demo company with presentable, real SELLING price data — picked for that reason.

  `Item.description` and `Item.image` are empty on every single Item in every golden demo
  seed module (grep-confirmed across the whole app, then confirmed live via `bench execute`
  for these 2 items specifically) — no seed module ever populated them. Rather than mutate
  existing shared Item records (VITC-1000-EFF/FACIAL-CLEANSER-150ML are reused across 3
  golden demos; editing their `description` field would be a shared-data change outside this
  module's own scope), `_CATALOG_COPY` below supplies short, clearly-labeled PRESENTATION
  copy (tagline/category/blurb) for the public site, keyed by the real `item_code` — it is
  marketing text authored for this demo, not a claim of real ERP data, and it only ever
  renders for an item_code that ALSO independently passes `_safe_item_codes()`'s real,
  data-driven filter below (so it can never be attached to a company/item this API wasn't
  meant to describe).
"""

import frappe

_PUBLIC_COMPANY = "Demo Consumer Distribution Co."
_PUBLIC_PRICE_LIST = "Standard Selling"

_COMPANY_COPY = {
	"about": (
		"Demo Consumer Distribution Co. is a nationwide distributor of consumer health and "
		"personal care products, supplying a dealer network across Northern and Southern "
		"Vietnam. This corporate site showcases a live product catalog drawn from the "
		"company's real ERP data."
	),
}

# Presentation-only copy for the public catalog — see module docstring. Keyed by the real
# item_code; only ever surfaced for an item_code that independently passes
# _safe_item_codes()'s real SQL filter.
_CATALOG_COPY = {
	"VITC-1000-EFF": {
		"category": "Nutraceutical / Supplement",
		"blurb": (
			"Fast-dissolving effervescent tablet delivering 1000mg of Vitamin C per serving, "
			"distributed nationwide through our dealer network."
		),
	},
	"FACIAL-CLEANSER-150ML": {
		"category": "Personal Care / Cosmetics",
		"blurb": (
			"Gentle daily facial cleanser in a 150ml bottle, formulated for everyday use and "
			"distributed through our dealer and retail network."
		),
	},
}


def _safe_item_codes():
	"""The ONLY items this public API will ever describe: real, non-disabled Items that (a)
	have at least one real Stock Ledger Entry for `_PUBLIC_COMPANY` — i.e. genuinely received/
	distributed by this company, not just any Item in the shared Item master — AND (b) have a
	real, selling Item Price on the public `_PUBLIC_PRICE_LIST` — i.e. genuinely priced for
	public sale (excludes the internal dealer-tier price list entirely). Both conditions are
	real, data-driven checks against actual transactional/pricing records, not a hardcoded
	item_code allow-list, so this stays correct if the demo data ever changes."""
	rows = frappe.db.sql(
		"""
		select distinct i.item_code
		from `tabItem` i
		inner join `tabStock Ledger Entry` sle
			on sle.item_code = i.item_code and sle.company = %(company)s
		inner join `tabItem Price` ip
			on ip.item_code = i.item_code and ip.selling = 1 and ip.price_list = %(price_list)s
		where i.disabled = 0
		order by i.item_code
		""",
		{"company": _PUBLIC_COMPANY, "price_list": _PUBLIC_PRICE_LIST},
		as_dict=True,
	)
	return [r.item_code for r in rows]


def _serialize_item(item_code):
	item = frappe.db.get_value(
		"Item",
		item_code,
		["item_code", "item_name", "stock_uom", "sales_uom"],
		as_dict=True,
	)
	if not item:
		return None
	price = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "selling": 1, "price_list": _PUBLIC_PRICE_LIST},
		["price_list_rate", "currency"],
		as_dict=True,
	)
	copy = _CATALOG_COPY.get(item_code, {})
	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		# `sales_uom` (e.g. "Tube") is the customer-facing selling unit when an Item defines
		# one — falling back to `stock_uom` only for items with no sales-side override. Fixes
		# a real bug where VITC-1000-EFF displayed "/ Kg" (its internal manufacturing/stock
		# tracking unit) next to a per-tube retail price, which read as nonsensical to a
		# visitor even after the price itself was corrected.
		"uom": item.sales_uom or item.stock_uom,
		"category": copy.get("category", "Consumer Product"),
		"description": copy.get("blurb", ""),
		"price": price.price_list_rate if price else None,
		"currency": price.currency if price else None,
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_company_profile():
	"""Public, guest-accessible corporate profile for the home/about page. Returns ONLY
	company_name/country/currency (real) plus static about-copy — no financial/internal
	Company field is ever read or returned."""
	company = frappe.db.get_value(
		"Company",
		_PUBLIC_COMPANY,
		["company_name", "country", "default_currency"],
		as_dict=True,
	)
	if not company:
		frappe.throw("Company profile is not available.", frappe.DoesNotExistError)
	return {
		"company_name": company.company_name,
		"country": company.country,
		"currency": company.default_currency,
		"about": _COMPANY_COPY["about"],
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_catalog_items():
	"""Public, guest-accessible product catalog listing — every item in `_safe_item_codes()`,
	each serialized through `_serialize_item()`'s explicit field allow-list."""
	return [item for item in (_serialize_item(code) for code in _safe_item_codes()) if item]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_item_detail(item_code: str = ""):
	"""Public, guest-accessible single-product detail. Deliberately re-checks `item_code`
	against `_safe_item_codes()` (not just "does this Item exist") so a guest can never probe
	an arbitrary Item code outside the public catalog's real, data-driven safe set."""
	item_code = (item_code or "").strip()
	if not item_code or item_code not in _safe_item_codes():
		frappe.throw("Product not found.", frappe.DoesNotExistError)
	return _serialize_item(item_code)


# ============================================================================
# WEB-02 — Brand / Consumer Product Website (Phase 7, master plan §8 lines ~2560-2561:
# "WEB-02 Brand / Consumer Product Website — Cho supplement/cosmetics/veterinary brand.").
# Backs a SEPARATE Next.js app, `nextjs-demo/web-02-brand-website/`. Added to this SAME file
# rather than a new one — it is the exact same security pattern as WEB-01 above, just a
# different company/item/shape of data, so it belongs next to it, not duplicated.
#
# DATA SOURCE CHOICE — why Demo Supplement Co. (Golden Demo #19/#20, IP-SUPPLEMENT),
# VITC-1000-EFF, over Cosmetics (#21) or Veterinary (#9/#10):
#   Checked all 3 candidates the master plan names (grepped `supplement_seeds.py`,
#   `cosmetics_seeds.py`, `vet_mfg_seeds.py`/`vet_dist_seeds.py` for `description`/`image`/
#   vertical custom fields/Item Price, then confirmed live values via `bench execute` against
#   test.demo.local):
#     - Demo Cosmetics Co. (`FACIAL-CLEANSER-150ML`) — 1 sellable finished good, but NO
#       vertical-specific descriptive field beyond generic has_batch_no/shelf_life_in_days —
#       nothing to build a real "why this brand" story on besides invented copy.
#     - Demo Vet Pharma Co. (`OXYTET-200-INJ`) — the richest CUSTOM fields (target_species,
#       indication, withdrawal_period_days), but those are clinical/regulatory label fields
#       for a prescription veterinary injectable sold to dealers/vets, not a genuine
#       consumer-brand product — a "brand site" for it would ring false (nobody browses a
#       lifestyle website for antibiotic withdrawal periods).
#     - **Demo Supplement Co. (`VITC-1000-EFF`, Vitamin C 1000mg Effervescent Tablet) — the
#       one picked.** A real, everyday consumer wellness product (exactly the kind of single-
#       hero-product brand site real vitamin brands run), AND it has the richest REAL,
#       verifiable data of the three once the full manufacturing chain is included, not just
#       the Item record: a real active Formula (BOM) with real ingredient proportions, a real
#       `contains_allergen` flag (Soy Lecithin), and a real LIMS Specification + Approved LIMS
#       COA test result (Vitamin C Content, spec 950-1050 mg/tablet, latest verified batch
#       tested at 1002 mg/tablet, live-confirmed) — a genuine, data-backed "lab verified
#       quality" claim, not invented copy. This is also deliberately the ORIGINAL MANUFACTURER
#       of one of WEB-01's own 2 showcased items, told from the brand's own point of view
#       (story/formula/quality) rather than WEB-01's distributor point of view (price list) —
#       so this reads as a different site, not a re-skin.
#
# SECURITY MODEL — identical discipline to WEB-01 above, same guest-only justification (no
# logged-in user to scope permissions to, so every field below is an explicit, hand-picked
# allow-list, never `"*"`/a whole-doctype dump/`get_all(fields=["*"])`):
#   - Company: company_name, country, default_currency only (same 3 fields as WEB-01).
#   - Item: item_code, item_name, shelf_life_in_days, contains_allergen only — genuinely
#     label-appropriate consumer facts. `stock_uom` ("Kg", a manufacturing batch unit) and
#     `item_group` ("Finished Goods") are deliberately NOT exposed — real fields, but not
#     consumer-meaningful, so they're left out rather than exposed "because they're not
#     forbidden" (the site's real needs drive the allow-list, not just the ban-list).
#   - BOM ("Formula"): item_code/qty of the CURRENT default+active BOM ONLY, from which only a
#     computed formula-weight PERCENTAGE is returned — never a BOM cost/rate/amount field,
#     never the raw materials' own supplier/valuation data.
#   - LIMS Specification + LIMS COA/Test: parameter_name/unit/min_value/max_value from the one
#     Effective spec for this item, plus the latest Approved test's result_value for that same
#     parameter and the COA's issued_date. Never batch_no, analyst, reviewer, instrument, or
#     any Stock Entry/Sales Order reference — the query scopes to this item via
#     `LIMS Sample.item_name` specifically (this platform's shared LIMS module runs the exact
#     same chain for multiple golden demos/items, so scoping by item_name, not "any Approved
#     COA", is required for correctness as well as safety).
#   No customer, dealer, warehouse, batch/lot, supplier, or financial-account data is read
#   anywhere here. `_BRAND_COMPANY`/`_BRAND_FG_ITEM` are hardcoded module constants, never
#   accepted as request parameters — a guest can never redirect this API to describe a
#   different company or item.
#
# `Item.description`/`Item.image` are empty here too (same platform-wide gap WEB-01 found) —
# `_BRAND_COPY`/`_INGREDIENT_NOTES` below are clearly-labeled PRESENTATION copy authored for
# this demo, not a claim of real ERP data; they only ever decorate the real item/ingredient
# codes returned by the real, data-driven queries above.
# ============================================================================

_BRAND_COMPANY = "Demo Supplement Co."
_BRAND_FG_ITEM = "VITC-1000-EFF"
_BRAND_FG_NAME = "Vitamin C 1000mg Effervescent Tablet"

_BRAND_COPY = {
	"tagline": "Daily immune support, fast-dissolving, made with care.",
	"mission": (
		"Demo Supplement Co. formulates everyday wellness products for people who want a "
		"simple, transparent daily ritual — real ingredients, a published formula, and every "
		"batch lab-verified before it reaches a shelf. This brand site shows our flagship "
		"product's real formula and real quality-testing data, drawn live from our own "
		"manufacturing and lab systems."
	),
	"philosophy": (
		"We publish our formula's real ingredient proportions and our lab's real, verified "
		"test results rather than asking you to take a label on faith. If an ingredient can "
		"cause a reaction — like the soy lecithin in our Vitamin C tablet — we flag it clearly, "
		"not in fine print."
	),
}

# Presentation-only copy for the hero product page — see module docstring. Keyed by the real
# item_code; only ever surfaced for `_BRAND_FG_ITEM` itself.
_PRODUCT_COPY = {
	"VITC-1000-EFF": {
		"category": "Immune Support / Effervescent Supplement",
		"tagline": "1000mg of Vitamin C, dissolved in seconds, verified in the lab.",
		"story": (
			"Our effervescent tablet dissolves in a glass of water in under a minute, delivering "
			"a full 1000mg dose of Vitamin C with a light orange flavor and no tablet to swallow. "
			"It's formulated, manufactured, and lab-tested end-to-end by Demo Supplement Co."
		),
		"benefits": [
			"1000mg Vitamin C per serving to support normal immune function.",
			"Fast-dissolving effervescent format — no swallowing a tablet.",
			"Light orange flavor, no artificial dyes in the formula.",
			"Every batch lab-tested against a published potency specification before release.",
		],
	}
}

# Presentation-only short notes for real formula ingredients — purely descriptive flavor text,
# never used to decide which ingredients are returned (that's `_brand_formula()`'s real BOM
# query below).
_INGREDIENT_NOTES = {
	"ASCORBIC-ACID": "The active ingredient — pharmaceutical-grade Vitamin C.",
	"CITRIC-ACID": "Food-grade acid that helps create the effervescent fizz.",
	"SODIUM-BICARB": "Reacts with the citric acid to produce the tablet's fizz on contact with water.",
	"SORBITOL": "A gentle sweetener and tablet binder.",
	"SOY-LECITHIN": "A binding agent derived from soy — the tablet's one common allergen.",
	"ORANGE-FLAVOR": "Natural-style orange flavoring, no artificial dyes.",
}


def _brand_default_bom():
	"""The product's real, current manufacturing Formula (BOM) — active AND default only, i.e.
	the version actually used for the most recent production, never a superseded/historical
	BOM version (those stay on record for traceability but aren't "the current formula")."""
	return frappe.db.get_value(
		"BOM", {"item": _BRAND_FG_ITEM, "is_active": 1, "is_default": 1}, "name"
	)


def _brand_formula():
	"""Real BOM ingredient list, reduced to item_code/name/percent-of-formula-weight only —
	never a BOM cost/rate/amount field. Percentage is computed here (qty / total qty), never
	stored or asserted by any hardcoded lookup, so it stays correct if the formula changes."""
	bom_name = _brand_default_bom()
	if not bom_name:
		return []
	rows = frappe.db.get_all(
		"BOM Item", filters={"parent": bom_name}, fields=["item_code", "qty"], order_by="qty desc"
	)
	total_qty = sum(r.qty for r in rows) or 1
	formula = []
	for row in rows:
		item_name = frappe.db.get_value("Item", row.item_code, "item_name")
		formula.append(
			{
				"item_code": row.item_code,
				"name": item_name,
				"percent_of_formula": round((row.qty / total_qty) * 100, 1),
				"note": _INGREDIENT_NOTES.get(row.item_code, ""),
			}
		)
	return formula


def _brand_quality():
	"""Real LIMS Specification (the published potency range) + the latest Approved LIMS
	COA/Test result for THIS item specifically, scoped via `LIMS Sample.item_name` (this
	platform's shared LIMS chain serves multiple golden demos/items on the same doctypes, so
	scoping by item_name — not "any Approved COA in the system" — is required for correctness,
	not just security). Returns None if no Effective spec exists yet rather than guessing."""
	spec_name = frappe.db.get_value(
		"LIMS Specification", {"item_name": _BRAND_FG_NAME, "status": "Effective"}, "name"
	)
	if not spec_name:
		return None
	params = frappe.db.get_all(
		"LIMS Specification Parameter",
		filters={"parent": spec_name},
		fields=["parameter_name", "unit", "min_value", "max_value"],
	)

	sample_names = [
		row.name
		for row in frappe.db.get_all(
			"LIMS Sample", filters={"item_name": _BRAND_FG_NAME}, fields=["name"]
		)
	]
	latest_result = None
	verified_on = None
	if sample_names:
		test_names = [
			row.name
			for row in frappe.db.get_all(
				"LIMS Test",
				filters={"sample": ["in", sample_names], "status": "Approved"},
				fields=["name"],
			)
		]
		if test_names:
			coa_rows = frappe.db.get_all(
				"LIMS COA",
				filters={"test": ["in", test_names], "status": "Approved"},
				fields=["test", "issued_date"],
				order_by="issued_date desc",
				limit=1,
			)
			if coa_rows:
				verified_on = coa_rows[0].issued_date
				latest_result = frappe.db.get_all(
					"LIMS Test Result",
					filters={"parent": coa_rows[0].test},
					fields=["parameter_name", "result_value", "unit"],
				)

	results_by_param = {r.parameter_name: r for r in (latest_result or [])}
	return {
		"specification": [dict(p) for p in params],
		"verified_on": str(verified_on) if verified_on else None,
		"latest_tested_values": {
			p.parameter_name: results_by_param[p.parameter_name].result_value
			for p in params
			if p.parameter_name in results_by_param
		},
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_brand_profile():
	"""Public, guest-accessible brand profile for the home/about/our-story pages. Returns ONLY
	company_name/country/currency (real) plus static brand copy — no financial/internal
	Company field is ever read or returned."""
	company = frappe.db.get_value(
		"Company",
		_BRAND_COMPANY,
		["company_name", "country", "default_currency"],
		as_dict=True,
	)
	if not company:
		frappe.throw("Brand profile is not available.", frappe.DoesNotExistError)
	return {
		"company_name": company.company_name,
		"country": company.country,
		"currency": company.default_currency,
		"tagline": _BRAND_COPY["tagline"],
		"mission": _BRAND_COPY["mission"],
		"philosophy": _BRAND_COPY["philosophy"],
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_brand_product():
	"""Public, guest-accessible hero-product page: real Item facts (shelf life, allergen flag),
	real Formula (BOM) ingredient proportions, and real lab-verified quality data — plus
	presentation copy for the narrative fields Item.description/image leave empty. There is
	only one hero product in this demo (`_BRAND_FG_ITEM`), so unlike WEB-01's catalog this is
	not parameterized by item_code at all — nothing here is guest-controllable."""
	item = frappe.db.get_value(
		"Item",
		_BRAND_FG_ITEM,
		["item_code", "item_name", "shelf_life_in_days", "contains_allergen"],
		as_dict=True,
	)
	if not item:
		frappe.throw("Product is not available.", frappe.DoesNotExistError)
	copy = _PRODUCT_COPY.get(_BRAND_FG_ITEM, {})
	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		"shelf_life_days": item.shelf_life_in_days,
		"contains_allergen": bool(item.contains_allergen),
		"category": copy.get("category", "Supplement"),
		"tagline": copy.get("tagline", ""),
		"story": copy.get("story", ""),
		"benefits": copy.get("benefits", []),
		"ingredients": _brand_formula(),
		"quality": _brand_quality(),
	}


# ============================================================================
# Platform Hub — Master Landing Site (USER-REQUESTED, NOT in the master plan's WEB-01..07
# list — see documents/project_status.md's Phase 7 section for the full rationale). Backs a
# THIRD, separate Next.js app, `nextjs-demo/hub-landing/`. Added to this SAME file for the
# exact same reason WEB-02 was added next to WEB-01 rather than in a new module: identical
# guest-only security pattern, just different (and here, much less sensitive) data.
#
# WHY THIS EXISTS: direct user feedback, not a master-plan line item — "ca website demo nay
# cung phai la 1 website dang cty... may cuc demo chi la khi nguoi dung chon vao thoi" (the
# whole demo platform should itself present as one company/product website, with the
# individual industry demos being things a visitor selects into). WEB-01 and WEB-02 are real,
# but each is its own disconnected site with no shared entry point describing what
# ENTERPRISE_PLATFORM itself is. This hub is that shared entry point.
#
# DATA SOURCE: the real `Industry Pack` DocType (DP-303, seeded by
# `enterprise_core/setup.py`'s `_INDUSTRY_PACKS` — 27 real registered packs, not a list
# invented for this hub). This is the platform's own canonical industry registry, already
# built for exactly this kind of purpose (pairing an industry vertical with its Edition/
# roles/workspaces/seed data) — reusing it here rather than hardcoding a parallel list in the
# frontend is both more honest and stays correct if a pack is ever added/renamed/disabled.
#
# SECURITY MODEL — same discipline as WEB-01/WEB-02 above (explicit, hand-picked field
# allow-list; hardcoded module constants, never request params; no `"*"`/raw doctype dump):
#   - Industry Pack: pack_code, pack_name, industry_category only — genuinely descriptive,
#     non-sensitive registry metadata (what industry packs this platform has built). Never
#     `default_edition`/`terminology_overrides`/`roles`/`workspaces`/`seeds` (those are
#     internal wiring, not public-facing facts) — `roles`/`workspaces`/`seeds` are child
#     tables that could reveal internal template naming/sequencing, so only a computed
#     BOOLEAN (`has_golden_demo`, does this pack have at least one Seed Template attached at
#     all) is derived from `Industry Pack Seed`, never the child rows themselves.
#   - Capability Engine: only a single COUNT of enabled rows (`capability_engine_count`) —
#     not even engine_code/engine_name are returned, just "how many exist" as one integer,
#     for a homepage stat tile. This is the least amount of real data that still lets the
#     home page state a true platform-scale fact instead of a hardcoded/guessed number.
#   No Company, Item, Customer, Sales, financial, or any transactional data is read anywhere
#   in this section — Industry Pack/Capability Engine are pure platform CONFIGURATION/
#   REGISTRY doctypes, not business data, which is why this is lower-stakes than WEB-01/
#   WEB-02's own item-price/LIMS data even before the field allow-list is applied.
#
# WHY `frappe.db.get_all()`, not `frappe.db.get_list()`, for the Industry Pack/Capability
# Engine queries below: `Industry Pack`'s and `Capability Engine`'s own DocType permissions
# (see their .json) grant read/write only to `System Manager` — there is no Guest/All read
# permission on either doctype. `get_list()` ENFORCES those permissions and would return an
# empty result (or raise) for the guest user this endpoint runs as; `get_all()` deliberately
# skips permission enforcement, which is exactly why WEB-01/WEB-02 above also use
# `get_all()`/`get_value()`/raw `frappe.db.sql()` throughout instead of `get_list()` — a
# guest-whitelisted function has no ambient user permission scope to preserve in the first
# place (the function body itself, with its explicit field allow-list and hardcoded filters,
# IS the entire security boundary). Every filter passed to `get_all()` below is a hardcoded
# constant (`enabled=1`), never a request parameter.
#
# PRESENTATION COPY: `Industry Pack.description` (a real field) is never populated by
# `setup.py`'s seed function (grep-confirmed — `seed_industry_packs()` never sets it), so
# — same discipline as WEB-01's `_CATALOG_COPY`/WEB-02's `_PRODUCT_COPY` — `_PACK_SUMMARIES`
# below supplies a short, factual one-line summary per pack_code, authored from this
# project's own real build records (`setup.py`'s own Golden-Demo-number code comments and
# `documents/project_status.md`'s Phase 1-6 entries), not invented marketing copy. It only
# ever decorates a pack_code that independently, really exists and is enabled in the DB.
#
# LIVE DEMO LINKAGE: `_LIVE_DEMO_PACKS` is a hardcoded, small allow-list of the Industry Packs (of
# 27) that this project has actually built a dedicated public/authenticated Next.js site for so
# far — a fact about this project's own build history, not something a request could ever
# influence. Each pack_code now maps to a LIST of demos (changed from a single label when WEB-03
# shipped as a SECOND site on the SAME IP-CONSUMER-DIST pack — WEB-01 is a guest-only public
# catalog, WEB-03 is a separately-authenticated dealer portal against the same company's real
# data; one pack_code can genuinely have more than one dedicated site). Each entry carries a
# stable `key` (matched against `hub-landing`'s own `LIVE_DEMO_URLS` map, see that app's
# `lib/api.ts`) and `requires_login` (WEB-01/WEB-02 are guest-only; WEB-03/WEB-04 each require a
# real login (dealer/supplier respectively) — the Hub must disclose this distinction rather than
# link to it exactly like a public site). The ACTUAL WEB-01/02/03/04 URLs are deliberately NOT
# hardcoded here — they are dev-server ports (currently 3001/3002/3004/3005) that belong to those
# apps' own deployment, not to this backend's business data; `hub-landing`'s own `.env.local`
# carries those URLs (same "frontend owns its own deployment config" precedent
# `FRAPPE_BASE_URL`/`FRAPPE_SITE_HOST` already established), keyed by the SAME `key` this API
# returns.
_LIVE_DEMO_PACKS = {
	"IP-CONSUMER-DIST": [
		{
			"key": "WEB-01",
			"label": "WEB-01 — Corporate + Product Catalog (Demo Consumer Distribution Co., Golden Demo #25)",
			"requires_login": False,
		},
		{
			"key": "WEB-03",
			"label": "WEB-03 — B2B Customer / Dealer Portal (Demo Consumer Distribution Co., Golden Demo #25)",
			"requires_login": True,
		},
		{
			"key": "WEB-05",
			"label": "WEB-05 — B2C Commerce (Demo Consumer Distribution Co., Golden Demo #25)",
			"requires_login": False,
		},
	],
	"IP-SUPPLEMENT": [
		{
			"key": "WEB-02",
			"label": "WEB-02 — Brand / Consumer Product Website (Demo Supplement Co., Golden Demo #20)",
			"requires_login": False,
		},
	],
	"IP-INGREDIENT-TRADING": [
		{
			"key": "WEB-04",
			"label": "WEB-04 — Supplier / RFQ Portal (Demo Ingredient Trading Co., Golden Demo #27)",
			"requires_login": True,
		},
	],
	"IP-PHARMACY": [
		{
			"key": "WEB-06",
			"label": "WEB-06 — Online Pharmacy (Demo Pharmacy Chain Co., Store A, Golden Demo #23)",
			"requires_login": False,
		},
	],
	"IP-VETERINARY": [
		{
			"key": "WEB-07",
			"label": "WEB-07 — Farm Customer / Technical Service Portal (Demo Vet Pharma Co., Golden Demo #10)",
			"requires_login": True,
		},
	],
}

# One factual, one-line summary per real, enabled Industry Pack — see module docstring above
# for sourcing (setup.py's own Golden-Demo-number comments / project_status.md), never
# invented capability claims. Golden Demo numbers quoted here match setup.py's own inline
# comments exactly (the ground-truth source), not guessed.
_PACK_SUMMARIES = {
	"IP-PHARMA": "Full GMP pharmaceutical manufacturing — batch production, QA/QC release, deviation/CAPA, document control, and equipment calibration (Golden Demo #1, the platform's flagship demo).",
	"IP-SUPPLEMENT": "Nutraceutical/TPBVSK manufacturing — formula revisions, artwork versioning, and COA-backed batch release (Golden Demo #20).",
	"IP-COSMETICS": "Cosmetics manufacturing — bulk and packed production, formula/artwork revisions, stability studies, distribution complaints, and rework (Golden Demo #21).",
	"IP-MEDICAL-DEVICE": "Medical device manufacturing — supplier qualification, incoming inspection, assembly, release, and complaint/trace handling (Golden Demo #22).",
	"IP-VETERINARY": "Veterinary pharmaceutical manufacturing and distribution — production, formula revision, recall, label versioning, and dealer/vet technical visits (Golden Demo #9).",
	"IP-VETERINARY-BIOLOGICAL": "Veterinary biological / vaccine manufacturing — registered as an Industry Pack, no golden demo seed data built yet (reserved for a future demo).",
	"IP-FEED": "Compound animal feed manufacturing — formula revision, ingredient substitution, manufacturing, and production-line sequencing (Golden Demo #7).",
	"IP-PREMIX": "Premix / feed additive manufacturing — micro-weigh tolerance control, weighing verification, sequencing, and manufacturing (Golden Demo #26).",
	"IP-LIVESTOCK-PIG": "Pig farm management — breeding flow, farm operations, and sale, with full data-quality validations (Golden Demo #11).",
	"IP-LIVESTOCK-POULTRY": "Poultry farm management — placement, operations, and sale flow (Golden Demo #12).",
	"IP-LIVESTOCK-CATTLE": "Cattle/dairy farm management — breeding, operations, and sale flow (Golden Demo #13).",
	"IP-HATCHERY": "Hatchery / breeding management — egg batch, incubation, hatch/grading, vaccination, and dispatch (Golden Demo #14).",
	"IP-AQUAFEED": "Aquafeed manufacturing — master data and full production flow for aquaculture feed (Golden Demo #15).",
	"IP-AQUA-ENVIRONMENT": "Aquaculture environment treatment manufacturing — formula revision, production, label versioning, and distribution trace (Golden Demo #16).",
	"IP-SHRIMP": "Shrimp farm management — stocking, farm operations, and harvest (Golden Demo #8).",
	"IP-FISH": "Fish farm management — stocking, operations, and harvest (Golden Demo #17).",
	"IP-AQUA-HATCHERY": "Aqua hatchery / seed management — spawning, larval/nursery rearing, and dispatch (Golden Demo #18).",
	"IP-MEAT-PROCESSING": "Meat/animal product processing — receiving, batch processing, QC/packing, and distribution/recall trace (Golden Demo #28).",
	"IP-SEAFOOD-PROCESSING": "Seafood processing and export — receiving/grading, processing/packing, shipment, and recall (Golden Demo #19).",
	"IP-QMS": "Quality Management System (standalone) — deviation/CAPA, change control, OOS/OOT, audit, and recall/risk/supplier quality (Golden Demo #3).",
	"IP-DMS": "Document Management System & Training (standalone) — document lifecycle, revision control, and training assignment (Golden Demo #4).",
	"IP-LIMS": "Laboratory Information Management System (standalone) — specifications, sample/test golden flow, OOS flow, and COA issuance (Golden Demo #5).",
	"IP-EAM": "EAM / CMMS / calibration / validation (standalone) — equipment calibration, qualification, and breakdown/repair tracking (Golden Demo #6).",
	"IP-PHARMACY": "Pharmacy chain retail/POS — replenishment, inter-store transfer, POS sale/return, expiry blocking, and a central dashboard (Golden Demo #23).",
	"IP-3PL-COLDCHAIN": "Pharma 3PL / GSP / cold chain warehousing — inbound receiving, quarantine/release, FEFO outbound, temperature monitoring, and billing (Golden Demo #24).",
	"IP-CONSUMER-DIST": "Consumer health/cosmetics distribution — price policy, promotions, territory and dealer credit control, sales flow, and returns (Golden Demo #25).",
	"IP-INGREDIENT-TRADING": "Feed/ingredient trading — import shipments, supplier lot QC, contracts and sales, price history, and margin reporting (Golden Demo #27).",
}


def _pack_has_golden_demo(pack_code):
	"""Real, computed signal (never a hardcoded guess): does this Industry Pack have at least
	one Seed Template actually attached to it (`Industry Pack Seed` child rows)? That's the
	platform's own real mechanism for "this pack has real, buildable demo data" (DP-303/
	_sync_industry_pack_seeds in setup.py) — so this stays correct if a future pack is wired
	up, without editing this API. Returns a plain boolean; the child rows' own content
	(seed_template/sequence) is never returned."""
	return bool(frappe.db.exists("Industry Pack Seed", {"parent": pack_code}))


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_industry_solutions():
	"""Public, guest-accessible list of every real, enabled Industry Pack — the hub's
	Industries/Solutions page. Each entry is the real DB row's pack_code/pack_name/
	industry_category plus a real computed `has_golden_demo` boolean and (for the packs this
	project has actually built a dedicated site for) a `live_demos` LIST — plural since
	IP-CONSUMER-DIST now has 2 (WEB-01 guest-only, WEB-03 login-required), see this section's
	module docstring for the full security/sourcing design."""
	packs = frappe.db.get_all(
		"Industry Pack",
		filters={"enabled": 1},
		fields=["pack_code", "pack_name", "industry_category"],
		order_by="pack_code asc",
	)
	solutions = []
	for pack in packs:
		live_demos = _LIVE_DEMO_PACKS.get(pack.pack_code, [])
		solutions.append(
			{
				"pack_code": pack.pack_code,
				"pack_name": pack.pack_name,
				"industry_category": pack.industry_category,
				"summary": _PACK_SUMMARIES.get(pack.pack_code, ""),
				"has_golden_demo": _pack_has_golden_demo(pack.pack_code),
				"has_live_demo": bool(live_demos),
				"live_demos": live_demos,
			}
		)
	return solutions


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_platform_stats():
	"""Public, guest-accessible platform-scale stat tile data for the hub's home page — real
	counts only, never a list of records. `capability_engine_count` is the ONLY Capability
	Engine data ever returned by this module (not even engine_code/engine_name) — seeing
	"how many exist" is true and useful for a homepage stat without exposing the registry
	itself. `live_demo_count` counts individual DEMOS (7: WEB-01/02/03/04/05/06/07), not packs (5),
	since IP-CONSUMER-DIST alone now has 3 dedicated sites (WEB-01/03/05)."""
	return {
		"industry_pack_count": frappe.db.count("Industry Pack", {"enabled": 1}),
		"capability_engine_count": frappe.db.count("Capability Engine", {"enabled": 1}),
		"golden_demo_pack_count": len(
			[
				p
				for p in frappe.db.get_all("Industry Pack", filters={"enabled": 1}, fields=["pack_code"])
				if _pack_has_golden_demo(p.pack_code)
			]
		),
		"live_demo_count": sum(len(v) for v in _LIVE_DEMO_PACKS.values()),
	}


# ----------------------------------------------------------------------------
# Industry Pack DETAIL (USER-REQUESTED — "make the ~26 non-live-demo Industry Packs feel
# genuinely complete instead of a one-line ERP System Demo card"). Backs a new per-pack page
# in the Hub, `hub-landing`'s `/solutions/[packCode]`.
#
# WHY THIS REVISITS THE ABOVE MODULE DOCSTRING'S "never the child rows themselves" RULE:
# `get_industry_solutions()`'s own module docstring (above) deliberately withheld
# `Industry Pack.seeds` child-row CONTENT from the LIST endpoint, reasoning that
# "roles/workspaces/seeds are child tables that could reveal internal template
# naming/sequencing" — true, and that reasoning still holds for the bulk LIST endpoint (no
# reason a homepage-scale listing needs 27 packs' worth of internal step names). This new
# function is a DIFFERENT, narrower thing: a single pack's own detail page, requested
# explicitly by pack_code, whose entire purpose is to show a genuine visitor "what actually
# ran to build this specific demo" — the real `Seed Template` names (e.g. "QMS Deviation ->
# CAPA -> Closure (DP-529)") ARE exactly that fact, and they are already visible to anyone
# reading this platform's own public engineering documentation
# (`documents/project_status.md`) — this just surfaces the same honest fact through the UI
# instead of only through source comments. Still never returns `seed_function` (the literal
# Python dotted path) or `is_required`/raw `template_code` — only a human label, its
# `seed_type`, and its sequence position, which is what an interested visitor actually wants
# ("how many real steps, in what order, does this reference build have").
#
# CAPABILITY ENGINES: only returned when `Industry Pack.default_edition` is ACTUALLY set —
# confirmed live (2026-09-30 investigation) that only 1 of 27 packs (IP-PHARMA ->
# PHARMA_MFG_STARTER) has this populated; every other pack's `default_edition` is blank. This
# function does NOT fabricate a plausible-looking engine list for the other 26 — it returns an
# empty list for them, and the frontend is expected to simply omit that section rather than
# show a fake or guessed set of engines. Honesty about a data-model gap beats a confident-
# looking but invented answer.
def _resolve_seed_steps(pack_code):
	"""Real `Industry Pack Seed` child rows for one pack, resolved to their `Seed Template`'s
	human-readable name/type, in sequence order. See this section's own comment above for why
	this — unlike `get_industry_solutions()` — is allowed to expose child-row content."""
	seed_rows = frappe.db.get_all(
		"Industry Pack Seed",
		filters={"parenttype": "Industry Pack", "parent": pack_code},
		fields=["seed_template", "sequence"],
		order_by="sequence asc",
	)
	if not seed_rows:
		return []
	template_codes = list({row.seed_template for row in seed_rows})
	templates = {
		t.template_code: t
		for t in frappe.db.get_all(
			"Seed Template",
			filters={"template_code": ["in", template_codes]},
			fields=["template_code", "template_name", "seed_type"],
		)
	}
	steps = []
	for row in seed_rows:
		template = templates.get(row.seed_template)
		if not template:
			continue
		steps.append(
			{
				"sequence": row.sequence,
				"label": template.template_name,
				"seed_type": template.seed_type,
			}
		)
	return steps


def _resolve_capability_engines(default_edition):
	"""Real `Edition.capability_engines` -> `Capability Engine` lookup for one Edition code, or
	an empty list if there's no Edition to resolve (see this section's own comment above — this
	is currently true for 26 of 27 packs, and that's reported as an empty list, never guessed)."""
	if not default_edition:
		return []
	engine_rows = frappe.db.get_all(
		"Edition Capability Engine",
		filters={"parenttype": "Edition", "parent": default_edition, "enabled": 1},
		fields=["capability_engine"],
	)
	if not engine_rows:
		return []
	engine_codes = list({row.capability_engine for row in engine_rows})
	engines = frappe.db.get_all(
		"Capability Engine",
		filters={"engine_code": ["in", engine_codes], "enabled": 1},
		fields=["engine_code", "engine_name", "category"],
		order_by="engine_code asc",
	)
	return [{"engine_code": e.engine_code, "engine_name": e.engine_name, "category": e.category} for e in engines]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_industry_pack_detail(pack_code):
	"""Public, guest-accessible detail for ONE real, enabled Industry Pack — backs the Hub's
	`/solutions/[packCode]` page. `pack_code` is a request parameter (unlike every other
	function in this module), but it only ever SELECTS which already-public pack_code's real
	registry data to return — never an arbitrary doctype/fieldname, and the underlying query is
	still `frappe.db.get_all()` with a hardcoded field allow-list, exactly like
	`get_industry_solutions()`. An unknown/disabled pack_code raises `DoesNotExistError` rather
	than silently returning an empty/blank record."""
	pack = frappe.db.get_value(
		"Industry Pack",
		{"pack_code": pack_code, "enabled": 1},
		["pack_code", "pack_name", "industry_category", "default_edition"],
		as_dict=True,
	)
	if not pack:
		frappe.throw("Industry pack not found.", frappe.DoesNotExistError)

	live_demos = _LIVE_DEMO_PACKS.get(pack.pack_code, [])
	return {
		"pack_code": pack.pack_code,
		"pack_name": pack.pack_name,
		"industry_category": pack.industry_category,
		"summary": _PACK_SUMMARIES.get(pack.pack_code, ""),
		"has_golden_demo": _pack_has_golden_demo(pack.pack_code),
		"has_live_demo": bool(live_demos),
		"live_demos": live_demos,
		"seed_steps": _resolve_seed_steps(pack.pack_code),
		"capability_engines": _resolve_capability_engines(pack.default_edition),
	}


# ============================================================================
# Hub Contact Form — REAL BUSINESS-CRM WRITE (user-requested rebrand, not in the master plan's
# WEB-01..07 list — see documents/project_status.md's rebrand entry for the full rationale).
# Backs the Hub's new `/contact` page (`nextjs-demo/hub-landing/app/[locale]/contact/`).
#
# THIS IS A NEW RISK CATEGORY FOR *THIS FILE* (though not for the platform overall) — read
# before touching this section:
#   Every other function in this module (WEB-01/WEB-02/the Hub's own read-only endpoints above)
#   is `allow_guest=True` + READ-ONLY. This is `allow_guest=True` + a REAL WRITE — an anonymous
#   caller creates a real `Lead` document in ERPNext's native CRM module. That combination
#   (guest + write) was already solved once in this platform, in `b2c_commerce_api.py`'s
#   `place_web_order()` (WEB-05) — this function reuses the EXACT SAME narrow-elevation pattern
#   rather than inventing a new one:
#     1. EXPLICIT, VALIDATED INPUT ONLY. Exactly 4 fields are ever read from the request —
#        `full_name`, `email`, `company`, `message` — each length- and shape-checked BEFORE
#        anything is written (see `_validate_contact_lead()`). No other key in the request body
#        is ever read, so a caller cannot inject an arbitrary Lead field (e.g. `status`,
#        `lead_owner`, `source`, or any other DocField) — the Lead document this function builds
#        has a hardcoded field set, not a pass-through of the request body.
#     2. NARROW, RESTORED-ON-EXIT ELEVATION, NOT AMBIENT PRIVILEGE. `Guest` has no create
#        permission on `Lead` (CRM module, System-Manager/Sales-user scoped by default) — exactly
#        the same real permissions gap `place_web_order()`'s own docstring documents for
#        `Sales Order`/`Address`. The fix is identical: `frappe.set_user("Administrator")`
#        scoped to ONLY the `lead.insert()` call, restored in a `finally` clause even on failure.
#        Every value written in that one-line block was already fully validated above it, before
#        the elevation — nothing request-controlled is interpreted while elevated.
#     3. SANE INPUT BOUNDS, HONESTLY NOT REAL ANTI-ABUSE. Same disclosure as WEB-05's own
#        docstring point 5 — length caps on every field are real validation, not rate limiting,
#        a CAPTCHA, or spam/fraud detection. A real production deployment of a public contact
#        form would need those too; not pretended here.
#     4. NO ENUMERABLE RESPONSE. The created Lead's own (sequential, guessable) `name`
#        (`CRM-LEAD-2026-NNNNN`) is never returned to the caller — same "never leak a sequential
#        internal id to a guest" discipline as WEB-05's `order_token` design, even though a Lead
#        is lower-stakes than a Sales Order. The response is just a boolean confirmation.
#
# LEAD FIELD CHOICE — checked live against the real `Lead` DocType (CRM module) via
# `bench execute frappe.get_meta` against `pharmacountry.vn` before writing this, not guessed:
#   - `status` is the ONLY field the DocType itself marks `reqd=1`; set to the real, valid
#     select option `"Lead"` (the first/default status for a brand-new, uncontacted lead — the
#     DocType's own `status` field options are `Lead, Open, Replied, Opportunity, Quotation,
#     Lost Quotation, Interested, Converted, Do Not Contact`).
#   - `lead_name`, `company_name`, `email_id` are real, standard Data fields on Lead — the
#     submitter's name, company, and email map directly onto them.
#   - There is no simple "message" text field on Lead itself; the real, standard way ERPNext
#     models free-text notes on a Lead is the `notes` CHILD TABLE (`CRM Note`, fields
#     `note`/`added_by`/`added_on`, confirmed live via the same `get_meta` call) — the visitor's
#     message is appended there as one `CRM Note` row, not stuffed into an unrelated field.
_MAX_CONTACT_NAME_LEN = 120
_MAX_CONTACT_COMPANY_LEN = 120
_MAX_CONTACT_EMAIL_LEN = 180
_MAX_CONTACT_MESSAGE_LEN = 2000


def _validate_contact_lead(full_name, email, company, message):
	full_name = (full_name or "").strip()
	email = (email or "").strip()
	company = (company or "").strip()
	message = (message or "").strip()

	if not full_name or len(full_name) > _MAX_CONTACT_NAME_LEN:
		frappe.throw(f"A valid name (1-{_MAX_CONTACT_NAME_LEN} characters) is required.")
	if not email or "@" not in email or len(email) > _MAX_CONTACT_EMAIL_LEN:
		frappe.throw("A valid email address is required.")
	if len(company) > _MAX_CONTACT_COMPANY_LEN:
		frappe.throw(f"Company name must be {_MAX_CONTACT_COMPANY_LEN} characters or fewer.")
	if not message or len(message) > _MAX_CONTACT_MESSAGE_LEN:
		frappe.throw(f"A message (1-{_MAX_CONTACT_MESSAGE_LEN} characters) is required.")

	return {
		"full_name": full_name,
		"email": email,
		"company": company,
		"message": message,
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_contact_lead(full_name: str = "", email: str = "", company: str = "", message: str = ""):
	"""Creates a REAL `Lead` document (ERPNext CRM module) from the Hub's public `/contact` form.
	See this section's module docstring for the full threat model. Exactly 4 request fields are
	ever read (all re-validated here, never trusted from the frontend alone even though the
	Next.js route handler in front of this also validates); nothing else in the request is
	interpreted, and the one real write is scoped to a single narrow, restored-on-exit
	`Administrator` elevation."""
	contact = _validate_contact_lead(full_name, email, company, message)

	lead = frappe.get_doc(
		{
			"doctype": "Lead",
			"lead_name": contact["full_name"],
			"company_name": contact["company"] or contact["full_name"],
			"email_id": contact["email"],
			"status": "Lead",
			"notes": [
				{
					"note": (
						f"Submitted via PharmaCountry Enterprise Solutions Hub contact form "
						f"(pharmacountry.vn/contact).\n\n{contact['message']}"
					),
				}
			],
		}
	)

	# Narrow, documented, restored-on-exit "service account" elevation — identical pattern to
	# b2c_commerce_api.py's place_web_order(), see this section's module docstring point 2.
	# Scoped to exactly this one statement; every value it writes was already validated above,
	# before this block, and the original session user is restored even on failure.
	_original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		lead.insert()
	finally:
		frappe.set_user(_original_user)

	# Deliberately no Lead `name`/id in the response — see module docstring point 4.
	return {"success": True}


def verify_hub_contact_lead_access_control():
	"""Real, empirical proof for the Hub contact form's guest-write security model — part of the
	platform's standard verify_* regression sweep. Always runs as Guest (this endpoint never
	requires a session)."""
	original_user = frappe.session.user
	checks = []

	def check(name, passed, detail=None):
		checks.append({"check": name, "passed": bool(passed), "detail": detail})

	try:
		frappe.set_user("Guest")

		before_count = frappe.db.count("Lead")
		probe_email = f"verify.hub.contact.{frappe.generate_hash(length=8)}@example.com"
		result = submit_contact_lead(
			full_name="Hub Contact Verify Test",
			email=probe_email,
			company="Verify Co.",
			message="Automated regression-sweep probe for the Hub contact form.",
		)
		check("submit_contact_lead() returns a plain success confirmation, no internal id", result == {"success": True}, result)

		after_count = frappe.db.count("Lead")
		check("Exactly one real Lead document was created", after_count == before_count + 1, {"before": before_count, "after": after_count})

		created = frappe.db.get_value(
			"Lead", {"email_id": probe_email}, ["lead_name", "company_name", "email_id", "status"], as_dict=True
		)
		check(
			"The created Lead contains exactly the submitted fields (name/company/email) and the expected status",
			bool(created)
			and created.lead_name == "Hub Contact Verify Test"
			and created.company_name == "Verify Co."
			and created.email_id == probe_email
			and created.status == "Lead",
			created,
		)

		# --- Field-injection resistance: an unexpected key in the payload must have ZERO effect. ---
		# submit_contact_lead()'s own signature only accepts full_name/email/company/message — any
		# extra kwarg would raise a TypeError before ever reaching frappe.get_doc(), proving there is
		# no pass-through of arbitrary request fields into the Lead document.
		injection_blocked = False
		try:
			submit_contact_lead(
				full_name="Injection Test",
				email="injection@example.com",
				company="X",
				message="test",
				status="Converted",  # type: ignore[call-arg]  # deliberately invalid extra kwarg
			)
		except TypeError:
			injection_blocked = True
		except Exception:
			injection_blocked = False
		check("An unexpected extra field in the request is rejected, never silently applied", injection_blocked, None)

		# --- Validation rejects bad input, never silently creates a malformed Lead. ---
		bad_email_rejected = False
		try:
			submit_contact_lead(full_name="X", email="not-an-email", company="", message="test")
		except frappe.ValidationError:
			bad_email_rejected = True
		except Exception:
			bad_email_rejected = False
		check("An email address without '@' is rejected", bad_email_rejected, None)

		empty_message_rejected = False
		try:
			submit_contact_lead(full_name="X", email="valid@example.com", company="", message="")
		except frappe.ValidationError:
			empty_message_rejected = True
		except Exception:
			empty_message_rejected = False
		check("An empty message is rejected", empty_message_rejected, None)

		oversized_message_rejected = False
		try:
			submit_contact_lead(
				full_name="X",
				email="valid@example.com",
				company="",
				message="x" * (_MAX_CONTACT_MESSAGE_LEN + 1),
			)
		except frappe.ValidationError:
			oversized_message_rejected = True
		except Exception:
			oversized_message_rejected = False
		check(f"A message beyond {_MAX_CONTACT_MESSAGE_LEN} characters is rejected", oversized_message_rejected, None)
	finally:
		frappe.set_user(original_user)

	return {"all_passed": all(c["passed"] for c in checks), "checks": checks}
