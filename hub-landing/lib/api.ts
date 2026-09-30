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

// See .env.local's own comment: these are the sibling apps' OWN deployment URLs (a frontend
// deployment fact), not something the Frappe backend describes. Deliberately NO localhost
// fallback — a "http://localhost:3001" link is meaningless to a real visitor (it points at
// their own device, not this server), so until an app is actually deployed somewhere publicly
// reachable and its real URL is set via env var, these stay undefined and liveDemoUrlFor()
// reports it as not yet live rather than rendering a dead link.
export const WEB01_URL = process.env.HUB_WEB01_URL || undefined;
export const WEB02_URL = process.env.HUB_WEB02_URL || undefined;
export const WEB03_URL = process.env.HUB_WEB03_URL || undefined;
export const WEB04_URL = process.env.HUB_WEB04_URL || undefined;
export const WEB05_URL = process.env.HUB_WEB05_URL || undefined;
export const WEB06_URL = process.env.HUB_WEB06_URL || undefined;
export const WEB07_URL = process.env.HUB_WEB07_URL || undefined;

// Maps the backend's real, stable demo `key` (NOT pack_code — a pack_code can now have more
// than one demo, e.g. IP-CONSUMER-DIST has both WEB-01 and WEB-03) -> the matching sibling
// app's real URL. Deliberately a small, hardcoded map here in the frontend (mirroring the
// backend's own hardcoded `_LIVE_DEMO_PACKS` allow-list) rather than trying to derive a URL
// from any request input.
const LIVE_DEMO_URLS: Record<string, string | undefined> = {
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

export class FrappeApiError extends Error {
  status: number;
  constructor(message: string, status = 0) {
    super(message);
    this.status = status;
  }
}

function extractErrorMessage(parsed: unknown, status: number, method: string): string {
  if (parsed && typeof parsed === "object") {
    const obj = parsed as Record<string, unknown>;
    if (typeof obj._server_messages === "string") {
      try {
        const messages = JSON.parse(obj._server_messages) as string[];
        const first = messages[0] ? JSON.parse(messages[0]) : null;
        if (first?.message) return String(first.message);
      } catch {
        // fall through to generic message below
      }
    }
    if (typeof obj.exc_type === "string" && typeof obj.exception === "string") {
      return String(obj.exception);
    }
  }
  return `Frappe API "${method}" returned HTTP ${status}`;
}

interface CallOptions {
  method?: "GET" | "POST";
  params?: Record<string, string>;
  body?: unknown;
}

// Same Node raw-`http`-module Host-header workaround as WEB-01..07's own `lib/api.ts` files
// (see this file's top-of-file comment) — now extended to also support a real POST + JSON body,
// the same way WEB-05's `b2c_commerce_api.ts` client does for `placeWebOrder`, for the Hub's own
// new Contact-form -> Lead write.
function callFrappeApi<T>(method: string, options: CallOptions = {}): Promise<T> {
  const { method: httpMethod = "GET", params, body } = options;
  const url = new URL(`/api/method/${method}`, FRAPPE_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  const payload = httpMethod === "POST" && body !== undefined ? JSON.stringify(body) : undefined;
  const headers: Record<string, string> = { Host: FRAPPE_SITE_HOST, Accept: "application/json" };
  if (payload) {
    headers["Content-Type"] = "application/json; charset=utf-8";
    headers["Content-Length"] = Buffer.byteLength(payload).toString();
  }

  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: `${url.pathname}${url.search}`,
        method: httpMethod,
        headers,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode || 0;
          let parsed: unknown = null;
          try {
            parsed = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
          } catch {
            // non-JSON body — parsed stays null, generic message used below
          }
          if (status < 200 || status >= 300) {
            reject(new FrappeApiError(extractErrorMessage(parsed, status, method), status));
            return;
          }
          resolve((parsed as { message: T } | null)?.message as T);
        });
      }
    );
    req.on("error", (err) => reject(new FrappeApiError(err.message, 0)));
    if (payload) req.write(payload);
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

// One real seed step that ran to build this pack's golden demo (Industry Pack Seed -> Seed
// Template, resolved server-side). `label` is the real Seed Template's human name (frequently
// carrying its own real internal ticket reference, e.g. "(DP-529)") — never the raw
// `seed_function` dotted path or `template_code` enum. See public_api.py's own
// `get_industry_pack_detail()` docstring for why this endpoint (unlike the list endpoint) is
// allowed to expose this.
export interface IndustryPackSeedStep {
  sequence: number;
  label: string;
  seed_type: "Master Data" | "Transaction" | "Demo Scenario" | string;
}

// One real Capability Engine this pack's Edition actually wires up. Only ever non-empty when
// the pack's own `default_edition` is genuinely set in the backend (true today for exactly 1
// of 27 packs, IP-PHARMA) — never a guessed/typical set for the other packs.
export interface IndustryPackCapabilityEngine {
  engine_code: string;
  engine_name: string;
  category: string;
}

export interface IndustryPackDetail extends IndustrySolution {
  seed_steps: IndustryPackSeedStep[];
  capability_engines: IndustryPackCapabilityEngine[];
}

export function getIndustryPackDetail(packCode: string): Promise<IndustryPackDetail> {
  return callFrappeApi<IndustryPackDetail>(
    "enterprise_core.enterprise_core.public_api.get_industry_pack_detail",
    { params: { pack_code: packCode } }
  );
}

export interface ContactLeadInput {
  fullName: string;
  email: string;
  company?: string;
  message: string;
}

// The Hub's own guest-write call, backing the new /contact page. Mirrors WEB-05's
// `placeWebOrder()` client-side shape: only ever sends the 4 fields the real backend
// (`public_api.py`'s `submit_contact_lead()`) explicitly validates and accepts — see that
// function's own docstring for the full narrow-elevation security model it enforces server-side.
export function submitContactLead(input: ContactLeadInput): Promise<{ success: boolean }> {
  return callFrappeApi<{ success: boolean }>(
    "enterprise_core.enterprise_core.public_api.submit_contact_lead",
    {
      method: "POST",
      body: {
        full_name: input.fullName,
        email: input.email,
        company: input.company || "",
        message: input.message,
      },
    }
  );
}
