// WEB-01 — thin server-side client for the Frappe `public_api.py` guest-whitelisted
// endpoints (enterprise_core app). Every call here hits a real, unauthenticated Frappe HTTP
// endpoint — there is no API key/session token anywhere in this file, matching the backend's
// own guest-only security design (see public_api.py's module docstring).
//
// Frappe is multi-tenant and routes purely on the HTTP Host header (there's no per-site
// port/path), and this dev machine has no DNS/hosts-file entry for test.demo.local or
// pharmacountry.vn — so the Host header has to be overridden per request. The WHATWG Fetch
// spec (enforced by Node's built-in `fetch`/undici) forbids scripts from setting the `Host`
// header, so this uses Node's lower-level `http` module instead, which has no such
// restriction, to connect to FRAPPE_BASE_URL while asking for the FRAPPE_SITE_HOST site.

import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export interface CompanyProfile {
  company_name: string;
  country: string;
  currency: string;
  about: string;
}

export interface CatalogItem {
  item_code: string;
  item_name: string;
  uom: string;
  category: string;
  description: string;
  price: number | null;
  currency: string | null;
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

export function getCompanyProfile(): Promise<CompanyProfile> {
  return callFrappeApi<CompanyProfile>(
    "enterprise_core.enterprise_core.public_api.get_company_profile"
  );
}

export function getCatalogItems(): Promise<CatalogItem[]> {
  return callFrappeApi<CatalogItem[]>(
    "enterprise_core.enterprise_core.public_api.get_catalog_items"
  );
}

export function getItemDetail(itemCode: string): Promise<CatalogItem> {
  return callFrappeApi<CatalogItem>(
    "enterprise_core.enterprise_core.public_api.get_item_detail",
    { item_code: itemCode }
  );
}

export function formatPrice(price: number | null, currency: string | null): string {
  if (price === null || currency === null) return "Price on request";
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency }).format(price);
}
