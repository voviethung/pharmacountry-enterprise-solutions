// WEB-03 — authenticated server-side client for `dealer_portal_api.py`'s session-validated
// endpoints. Every call here presents a REAL Frappe session cookie (`sid`) held server-side by
// this app (see lib/session.ts) — there is no `allow_guest` endpoint anywhere in this file, and no
// function accepts a "which dealer" parameter: the backend always resolves that from the session
// cookie itself (see dealer_portal_api.py's own module docstring).
//
// Reuses WEB-01/02/Hub's own Node `http`-module Host-header workaround (Frappe routes purely on
// the HTTP `Host` header; this machine has no DNS entry for test.demo.local/pharmacountry.vn, and
// plain `fetch()` forbids scripts from setting a custom `Host` header).
import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export class DealerApiError extends Error {
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
  csrfToken?: string;
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
  return `Dealer API "${method}" returned HTTP ${status}`;
}

function callDealerApi<T>(method: string, sid: string, options: CallOptions = {}): Promise<T> {
  const { method: httpMethod = "GET", params, body, csrfToken } = options;
  const url = new URL(`/api/method/${method}`, FRAPPE_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  }

  const payload = httpMethod === "POST" && body !== undefined ? JSON.stringify(body) : undefined;
  const headers: Record<string, string> = {
    Host: FRAPPE_SITE_HOST,
    Accept: "application/json",
    Cookie: `sid=${sid}`,
  };
  if (payload) {
    headers["Content-Type"] = "application/json; charset=utf-8";
    headers["Content-Length"] = Buffer.byteLength(payload).toString();
  }
  if (csrfToken) headers["X-Frappe-CSRF-Token"] = csrfToken;

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
            reject(new DealerApiError(extractErrorMessage(parsed, status, method), status));
            return;
          }
          resolve((parsed as { message: T } | null)?.message as T);
        });
      }
    );
    req.on("error", (err) => reject(new DealerApiError(err.message, 0)));
    if (payload) req.write(payload);
    req.end();
  });
}

const NS = "enterprise_core.enterprise_core.dealer_portal_api";

export interface DealerProfile {
  user: string;
  customer: string;
  customer_name: string;
  territory: string;
  price_list: string;
  csrf_token: string;
}

export interface CatalogItem {
  item_code: string;
  item_name: string;
  uom: string;
  my_price: number | null;
  price_list: string;
  currency: string;
}

export interface StockAvailability {
  item_code: string;
  warehouse: string;
  available_qty: number;
}

export interface OrderSummary {
  name: string;
  customer: string;
  transaction_date: string;
  delivery_date: string;
  grand_total: number;
  status: string;
  docstatus: number;
  po_no: string | null;
}

export interface OrderDetail {
  name: string;
  customer: string;
  transaction_date: string;
  delivery_date: string;
  status: string;
  grand_total: number;
  po_no: string | null;
  items: { item_code: string; item_name: string; qty: number; rate: number; amount: number }[];
}

export interface InvoiceSummary {
  name: string;
  customer: string;
  posting_date: string;
  due_date: string;
  grand_total: number;
  outstanding_amount: number;
  status: string;
  docstatus: number;
}

export interface DebtPosition {
  customer: string;
  outstanding_balance: number;
  credit_limit: number | null;
  available_credit: number | null;
}

export interface ReturnSummary {
  name: string;
  customer: string;
  posting_date: string;
  grand_total: number;
  docstatus: number;
  return_against: string;
}

export interface DeliverySummary {
  name: string;
  customer: string;
  posting_date: string;
  grand_total: number;
}

export function getMyProfile(sid: string) {
  return callDealerApi<DealerProfile>(`${NS}.get_my_profile`, sid);
}

export function getCatalogWithMyPricing(sid: string) {
  return callDealerApi<CatalogItem[]>(`${NS}.get_catalog_with_my_pricing`, sid);
}

export function getStockAvailability(sid: string) {
  return callDealerApi<StockAvailability[]>(`${NS}.get_stock_availability`, sid);
}

export function getMyOrders(sid: string) {
  return callDealerApi<OrderSummary[]>(`${NS}.get_my_orders`, sid);
}

export function getMyOrderDetail(sid: string, salesOrder: string) {
  return callDealerApi<OrderDetail>(`${NS}.get_my_order_detail`, sid, {
    params: { sales_order: salesOrder },
  });
}

export function placeOrder(
  sid: string,
  csrfToken: string,
  items: { item_code: string; qty: number }[]
) {
  return callDealerApi<{ name: string; grand_total: number; status: string }>(
    `${NS}.place_order`,
    sid,
    { method: "POST", body: { items }, csrfToken }
  );
}

export function getMyInvoices(sid: string) {
  return callDealerApi<InvoiceSummary[]>(`${NS}.get_my_invoices`, sid);
}

export function getMyDebt(sid: string) {
  return callDealerApi<DebtPosition>(`${NS}.get_my_debt`, sid);
}

export function getMyReturns(sid: string) {
  return callDealerApi<ReturnSummary[]>(`${NS}.get_my_returns`, sid);
}

export function getMyDeliveriesEligibleForReturn(sid: string) {
  return callDealerApi<DeliverySummary[]>(`${NS}.get_my_deliveries_eligible_for_return`, sid);
}

export function requestReturn(
  sid: string,
  csrfToken: string,
  deliveryNote: string,
  qty?: number
) {
  return callDealerApi<{ name: string; grand_total: number }>(`${NS}.request_return`, sid, {
    method: "POST",
    body: { delivery_note: deliveryNote, qty },
    csrfToken,
  });
}

export function formatVnd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}
