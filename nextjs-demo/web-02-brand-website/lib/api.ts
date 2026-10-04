// WEB-02 — thin server-side client for the Frappe `public_api.py` guest-whitelisted
// endpoints (enterprise_core app). Every call here hits a real, unauthenticated Frappe HTTP
// endpoint — there is no API key/session token anywhere in this file, matching the backend's
// own guest-only security design (see public_api.py's module docstring, WEB-02 section).
//
// This file is a direct reuse of WEB-01's own `lib/api.ts` pattern (nextjs-demo/
// web-01-corporate-catalog/lib/api.ts) — same Host-header workaround, same shape. Frappe is
// multi-tenant and routes purely on the HTTP Host header (there's no per-site port/path), and
// this dev machine has no DNS/hosts-file entry for test.demo.local or pharmacountry.vn — so
// the Host header has to be overridden per request. The WHATWG Fetch spec (enforced by Node's
// built-in `fetch`/undici) forbids scripts from setting the `Host` header, so this uses Node's
// lower-level `http` module instead, which has no such restriction, to connect to
// FRAPPE_BASE_URL while asking for the FRAPPE_SITE_HOST site.

import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export interface BrandProfile {
  company_name: string;
  country: string;
  currency: string;
  tagline: string;
  mission: string;
  philosophy: string;
}

export interface BrandIngredient {
  item_code: string;
  name: string;
  percent_of_formula: number;
  note: string;
}

export interface BrandQuality {
  specification: {
    parameter_name: string;
    unit: string;
    min_value: number;
    max_value: number;
  }[];
  verified_on: string | null;
  latest_tested_values: Record<string, number>;
}

export interface BrandProduct {
  item_code: string;
  item_name: string;
  shelf_life_days: number;
  contains_allergen: boolean;
  category: string;
  tagline: string;
  story: string;
  benefits: string[];
  ingredients: BrandIngredient[];
  quality: BrandQuality | null;
}

// P2 post-launch reviewer fix: the lightweight lineup shape get_brand_products() returns —
// enough to render a product grid/nav without pulling full formula/quality detail for every
// SKU up front (that's what getBrandProduct(item_code) is for, on the detail page).
export interface BrandProductSummary {
  item_code: string;
  item_name: string;
  shelf_life_days: number;
  category: string;
  tagline: string;
}

class FrappeApiError extends Error {}

function callFrappeApi<T>(
  method: string,
  params?: Record<string, string>
): Promise<T> {
  const url = new URL(`/api/method/${method}`, FRAPPE_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: `${url.pathname}${url.search}`,
        method: "GET",
        headers: { Host: FRAPPE_SITE_HOST, Accept: "application/json" },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode || 0;
          if (status < 200 || status >= 300) {
            reject(new FrappeApiError(`Frappe API "${method}" returned HTTP ${status}`));
            return;
          }
          try {
            const body = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
            resolve(body.message as T);
          } catch (err) {
            reject(err);
          }
        });
      }
    );
    req.on("error", reject);
    req.end();
  });
}

export function getBrandProfile(): Promise<BrandProfile> {
  return callFrappeApi<BrandProfile>(
    "enterprise_core.enterprise_core.public_api.get_brand_profile"
  );
}

// P2 post-launch reviewer fix: get_brand_product now accepts an optional item_code (still
// defaults to the flagship when omitted, so every existing call site — the homepage, the
// original /product page — keeps working unchanged).
export function getBrandProduct(itemCode?: string): Promise<BrandProduct> {
  return callFrappeApi<BrandProduct>(
    "enterprise_core.enterprise_core.public_api.get_brand_product",
    itemCode ? { item_code: itemCode } : undefined
  );
}

// P2 post-launch reviewer fix: new, additive — the real product lineup (now 3 real SKUs
// instead of 1), for the /products listing page.
export function getBrandProducts(): Promise<BrandProductSummary[]> {
  return callFrappeApi<BrandProductSummary[]>(
    "enterprise_core.enterprise_core.public_api.get_brand_products"
  );
}
