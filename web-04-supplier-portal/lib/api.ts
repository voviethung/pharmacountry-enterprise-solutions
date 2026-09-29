// WEB-04 — the Node raw-http-module Host-header workaround is reused VERBATIM from
// nextjs-demo/web-03-dealer-portal/lib/api.ts (same reasoning: Frappe routes on the Host header,
// fetch()/undici forbids setting it). Only the typed interfaces and the `NS` module path below are
// new, pointing at `enterprise_core.enterprise_core.supplier_portal_api` instead of
// `dealer_portal_api`.
import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export class SupplierApiError extends Error {
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
      } catch {}
    }
    if (typeof obj.exc_type === "string" && typeof obj.exception === "string") {
      return String(obj.exception);
    }
  }
  return `Supplier API "${method}" returned HTTP ${status}`;
}

function callSupplierApi<T>(method: string, sid: string, options: CallOptions = {}): Promise<T> {
  const { method: httpMethod = "GET", params, body, csrfToken } = options;
  const url = new URL(`/api/method/${method}`, FRAPPE_BASE_URL);
  if (params) for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);

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
      { hostname: url.hostname, port: url.port || 80, path: `${url.pathname}${url.search}`, method: httpMethod, headers },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode || 0;
          let parsed: unknown = null;
          try {
            parsed = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
          } catch {}
          if (status < 200 || status >= 300) {
            reject(new SupplierApiError(extractErrorMessage(parsed, status, method), status));
            return;
          }
          resolve((parsed as { message: T } | null)?.message as T);
        });
      }
    );
    req.on("error", (err) => reject(new SupplierApiError(err.message, 0)));
    if (payload) req.write(payload);
    req.end();
  });
}

const NS = "enterprise_core.enterprise_core.supplier_portal_api";

export interface SupplierProfile {
  user: string;
  supplier: string;
  supplier_name: string;
  supplier_group: string;
  country: string;
  default_currency: string;
  csrf_token: string;
}

export interface RfqSummary {
  name: string;
  title: string;
  transaction_date: string;
  schedule_date: string;
  status: string;
  quote_status: string;
}

export interface RfqDetail extends RfqSummary {
  company: string;
  message_for_supplier: string;
  items: { item_code: string; item_name: string; qty: number; uom: string; warehouse: string; schedule_date: string }[];
}

export interface QuotationSummary {
  name: string;
  supplier: string;
  transaction_date: string;
  valid_till: string;
  status: string;
  docstatus: number;
  currency: string;
  grand_total: number;
}

export interface QuotationDetail extends QuotationSummary {
  conversion_rate: number;
  incoterm: string;
  terms: string;
  items: {
    item_code: string;
    item_name: string;
    qty: number;
    rate: number;
    amount: number;
    lead_time_days: number | null;
    request_for_quotation: string | null;
  }[];
}

export interface PurchaseOrderSummary {
  name: string;
  supplier: string;
  transaction_date: string;
  schedule_date: string;
  currency: string;
  grand_total: number;
  status: string;
  docstatus: number;
}

export interface PurchaseOrderDetail extends PurchaseOrderSummary {
  conversion_rate: number;
  items: { item_code: string; item_name: string; qty: number; received_qty: number; rate: number; amount: number }[];
}

export interface QualityInspectionRef {
  name: string;
  status: string;
  item_code: string;
}

export interface DeliverySummary {
  name: string;
  supplier: string;
  posting_date: string;
  status: string;
  docstatus: number;
  grand_total: number;
  quality_inspections: QualityInspectionRef[];
}

export interface QualificationStatus {
  supplier: string;
  supplier_name: string;
  quality_status: string;
  is_critical_supplier: boolean;
  quality_inspections_total: number;
  quality_inspections_accepted: number;
  qc_pass_rate: number | null;
}

export interface DocumentRef {
  type: string;
  reference_doctype: string;
  reference_name: string;
  title: string;
  date: string;
}

export function getMyProfile(sid: string) {
  return callSupplierApi<SupplierProfile>(`${NS}.get_my_profile`, sid);
}

export function getMyRfqs(sid: string) {
  return callSupplierApi<RfqSummary[]>(`${NS}.get_my_rfqs`, sid);
}

export function getMyRfqDetail(sid: string, rfq: string) {
  return callSupplierApi<RfqDetail>(`${NS}.get_my_rfq_detail`, sid, { params: { rfq } });
}

export function getMyQuotations(sid: string) {
  return callSupplierApi<QuotationSummary[]>(`${NS}.get_my_quotations`, sid);
}

export function getMyQuotationDetail(sid: string, supplierQuotation: string) {
  return callSupplierApi<QuotationDetail>(`${NS}.get_my_quotation_detail`, sid, {
    params: { supplier_quotation: supplierQuotation },
  });
}

export function submitQuotation(
  sid: string,
  csrfToken: string,
  input: {
    rfq: string;
    rate: number;
    currency: string;
    conversion_rate: number;
    incoterm?: string;
    valid_till_days?: number;
    lead_time_days?: number;
    terms?: string;
  }
) {
  return callSupplierApi<{ name: string; grand_total: number; status: string; already_submitted: boolean }>(
    `${NS}.submit_quotation`,
    sid,
    { method: "POST", body: input, csrfToken }
  );
}

export function getMyPurchaseOrders(sid: string) {
  return callSupplierApi<PurchaseOrderSummary[]>(`${NS}.get_my_purchase_orders`, sid);
}

export function getMyPurchaseOrderDetail(sid: string, purchaseOrder: string) {
  return callSupplierApi<PurchaseOrderDetail>(`${NS}.get_my_purchase_order_detail`, sid, {
    params: { purchase_order: purchaseOrder },
  });
}

export function getMyDeliveries(sid: string) {
  return callSupplierApi<DeliverySummary[]>(`${NS}.get_my_deliveries`, sid);
}

export function getMyQualificationStatus(sid: string) {
  return callSupplierApi<QualificationStatus>(`${NS}.get_my_qualification_status`, sid);
}

export function getMyDocuments(sid: string) {
  return callSupplierApi<DocumentRef[]>(`${NS}.get_my_documents`, sid);
}

export function formatMoney(value: number | null | undefined, currency = "USD"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(value);
}
