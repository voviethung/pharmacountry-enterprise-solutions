// WEB-05 — server-side client for `b2c_commerce_api.py`'s guest-whitelisted endpoints
// (enterprise_core app). Every call here hits a real, unauthenticated Frappe HTTP endpoint — there
// is no API key/session cookie anywhere in this file, matching the backend's own guest-only
// security design (see b2c_commerce_api.py's module docstring). Unlike WEB-01/02's read-only
// client, this file also POSTs a real write (`placeWebOrder`) — the request body is exactly what
// the browser's cart/checkout form collected (item_code/qty/contact fields), and the REAL price is
// always computed server-side by Frappe, never trusted from this app's own request either.
//
// Reuses WEB-01/02/03/04's own Node `http`-module Host-header workaround verbatim: Frappe routes
// purely on the HTTP `Host` header, this machine has no DNS entry for
// test.demo.local/pharmacountry.vn, and plain `fetch()` (Node's built-in, backed by undici) forbids
// scripts from setting the `Host` header at all.
import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export class B2cApiError extends Error {
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
  return `B2C API "${method}" returned HTTP ${status}`;
}

function callB2cApi<T>(method: string, options: CallOptions = {}): Promise<T> {
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
            reject(new B2cApiError(extractErrorMessage(parsed, status, method), status));
            return;
          }
          resolve((parsed as { message: T } | null)?.message as T);
        });
      }
    );
    req.on("error", (err) => reject(new B2cApiError(err.message, 0)));
    if (payload) req.write(payload);
    req.end();
  });
}

const NS = "enterprise_core.enterprise_core.b2c_commerce_api";

export interface StorefrontItem {
  item_code: string;
  item_name: string;
  uom: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  available_qty: number;
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
}

export interface OrderConfirmation {
  order_token: string;
  payment_method: string;
  status: string;
  grand_total: number;
  currency: string;
  delivery_date: string;
  items: OrderLine[];
}

export interface OrderStatus extends OrderConfirmation {
  transaction_date: string;
  contact_display: string;
  address_display: string;
}

export function getStorefrontCatalog(): Promise<StorefrontItem[]> {
  return callB2cApi<StorefrontItem[]>(`${NS}.get_storefront_catalog`);
}

// The ONLY write in this whole app. `items` only ever carries item_code/qty — there is
// deliberately no `rate`/`price`/`amount` field in this TypeScript shape at all, because the real
// backend ignores any such field even if present (see b2c_commerce_api.py's own docstring); this
// type just keeps that same discipline on the frontend side.
export function placeWebOrder(items: CheckoutLine[], contact: CheckoutContact): Promise<OrderConfirmation> {
  return callB2cApi<OrderConfirmation>(`${NS}.place_web_order`, {
    method: "POST",
    body: { items, contact, payment_method: "Cash on Delivery" },
  });
}

export function getOrderStatus(orderToken: string, phone: string): Promise<OrderStatus> {
  return callB2cApi<OrderStatus>(`${NS}.get_order_status`, {
    params: { order_token: orderToken, phone },
  });
}

export function formatVnd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}
