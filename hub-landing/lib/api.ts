// Platform Hub — thin server-side client for the Frappe `public_api.py` guest-whitelisted
// endpoints (enterprise_core app). This file is a direct reuse of WEB-01/WEB-02's own
// `lib/api.ts` (same `callFrappeApi()` implementation, same Host-header workaround) — every
// call here hits a real, unauthenticated Frappe HTTP endpoint, no API key/session anywhere.
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

// See .env.local's own comment: these are the sibling apps' OWN dev-server URLs (a frontend
// deployment fact), not something the Frappe backend describes.
export const WEB01_URL = process.env.HUB_WEB01_URL || "http://localhost:3001";
export const WEB02_URL = process.env.HUB_WEB02_URL || "http://localhost:3002";
export const WEB03_URL = process.env.HUB_WEB03_URL || "http://localhost:3004";
export const WEB04_URL = process.env.HUB_WEB04_URL || "http://localhost:3005";
export const WEB05_URL = process.env.HUB_WEB05_URL || "http://localhost:3006";
export const WEB06_URL = process.env.HUB_WEB06_URL || "http://localhost:3007";
export const WEB07_URL = process.env.HUB_WEB07_URL || "http://localhost:3008";

// Maps the backend's real, stable demo `key` (NOT pack_code — a pack_code can now have more
// than one demo, e.g. IP-CONSUMER-DIST has both WEB-01 and WEB-03) -> the matching sibling
// app's real URL. Deliberately a small, hardcoded map here in the frontend (mirroring the
// backend's own hardcoded `_LIVE_DEMO_PACKS` allow-list) rather than trying to derive a URL
// from any request input.
const LIVE_DEMO_URLS: Record<string, string> = {
  "WEB-01": WEB01_URL,
  "WEB-02": WEB02_URL,
  "WEB-03": WEB03_URL,
  "WEB-04": WEB04_URL,
  "WEB-05": WEB05_URL,
  "WEB-06": WEB06_URL,
  "WEB-07": WEB07_URL,
};

export function liveDemoUrlFor(key: string): string | null {
  return LIVE_DEMO_URLS[key] ?? null;
}

export interface PlatformStats {
  industry_pack_count: number;
  capability_engine_count: number;
  golden_demo_pack_count: number;
  live_demo_count: number;
}

export interface LiveDemo {
  key: string;
  label: string;
  requires_login: boolean;
}

export interface IndustrySolution {
  pack_code: string;
  pack_name: string;
  industry_category: string;
  summary: string;
  has_golden_demo: boolean;
  has_live_demo: boolean;
  live_demos: LiveDemo[];
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

export function getPlatformStats(): Promise<PlatformStats> {
  return callFrappeApi<PlatformStats>(
    "enterprise_core.enterprise_core.public_api.get_platform_stats"
  );
}

export function getIndustrySolutions(): Promise<IndustrySolution[]> {
  return callFrappeApi<IndustrySolution[]>(
    "enterprise_core.enterprise_core.public_api.get_industry_solutions"
  );
}
