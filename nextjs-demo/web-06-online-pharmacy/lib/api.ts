// WEB-06 — server-side client for `online_pharmacy_api.py`'s guest-whitelisted endpoints
// (enterprise_core app). Every call here hits a real, unauthenticated Frappe HTTP endpoint — there
// is no API key/session cookie anywhere in this file, matching the backend's own guest-only
// security design (see online_pharmacy_api.py's module docstring, which reuses WEB-05's proven
// b2c_commerce_api.py security model almost verbatim). This file also POSTs a real write
// (`placePharmacyOrder`) — the request body is exactly what the browser's cart/checkout form
// collected (item_code/qty/contact fields); the REAL price AND the REAL, non-expired batch
// allocation are always computed server-side by Frappe, never trusted from this app either.
//
// Reuses WEB-01/02/03/04/05's own Node `http`-module Host-header workaround verbatim: Frappe routes
// purely on the HTTP `Host` header, this machine has no DNS entry for
// test.demo.local/pharmacountry.vn, and plain `fetch()` (Node's built-in, backed by undici) forbids
// scripts from setting the `Host` header at all.
import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export class PharmacyApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

interface CallOptions {
  method?: "GET" | "POST";
  params?: Record<string, string>;
  body?: unknown;
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
  return `Pharmacy API "${method}" returned HTTP ${status}`;
}

function callPharmacyApi<T>(method: string, options: CallOptions = {}): Promise<T> {
  const { method: httpMethod = "GET", params, body } = options;
  const url = new URL(`/api/method/${method}`, FRAPPE_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  }

  const payload = httpMethod === "POST" && body !== undefined ? JSON.stringify(body) : undefined;
  const headers: Record<string, string> = {
    Host: FRAPPE_SITE_HOST,
    Accept: "application/json",
  };
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
            reject(new PharmacyApiError(extractErrorMessage(parsed, status, method), status));
            return;
          }
          resolve((parsed as { message: T } | null)?.message as T);
        });
      }
    );
    req.on("error", (err) => reject(new PharmacyApiError(err.message, 0)));
    if (payload) req.write(payload);
    req.end();
  });
}

const NS = "enterprise_core.enterprise_core.online_pharmacy_api";

export interface PharmacyCatalogItem {
  item_code: string;
  item_name: string;
  uom: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  available_qty: number;
  store: string;
  requires_prescription: boolean;
}

export interface CheckoutContact {
  full_name: string;
  phone: string;
  address_line1: string;
  city: string;
  email?: string;
}

export interface CheckoutLine {
  item_code: string;
  qty: number;
}

export interface OrderLine {
  item_code: string;
  item_name: string;
  qty: number;
  rate: number;
  amount: number;
  batch_no: string;
  batch_expiry_date: string | null;
}

export interface OrderConfirmation {
  order_token: string;
  payment_method: string;
  status: string;
  grand_total: number;
  currency: string;
  store: string;
  address_display: string;
  items: OrderLine[];
}

export interface OrderStatus extends OrderConfirmation {
  transaction_date: string;
  contact_display: string;
}

export function getPharmacyCatalog(): Promise<PharmacyCatalogItem[]> {
  return callPharmacyApi<PharmacyCatalogItem[]>(`${NS}.get_pharmacy_catalog`);
}

// The ONLY write in this whole app. `items` only ever carries item_code/qty — there is
// deliberately no `rate`/`price`/`amount`/`batch_no` field in this TypeScript shape at all, because
// the real backend ignores any such field even if present (see online_pharmacy_api.py's own
// docstring — batch allocation is ALWAYS server-computed, earliest-expiry-first, from real
// non-expired stock); this type just keeps that same discipline on the frontend side.
export function placePharmacyOrder(items: CheckoutLine[], contact: CheckoutContact): Promise<OrderConfirmation> {
  return callPharmacyApi<OrderConfirmation>(`${NS}.place_pharmacy_order`, {
    method: "POST",
    body: { items, contact, payment_method: "Cash on Delivery" },
  });
}

export function getPharmacyOrderStatus(orderToken: string, phone: string): Promise<OrderStatus> {
  return callPharmacyApi<OrderStatus>(`${NS}.get_pharmacy_order_status`, {
    params: { order_token: orderToken, phone },
  });
}

export function formatVnd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}
