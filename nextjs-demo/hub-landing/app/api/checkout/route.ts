import { NextResponse } from "next/server";
import { createSubscriptionCheckout, FrappeApiError } from "@/lib/api";

// Server-side Route Handler backing the Hub's public /signup form — same structural reason as
// app/api/contact/route.ts: the browser's own <form>/fetch can only ever talk to THIS Next.js
// server (same-origin), never directly to Frappe with a custom Host header (see lib/api.ts's
// own top-of-file comment on why callFrappeApi() needs Node's raw `http` module). Real request
// path: browser -> this route handler (Node server) -> Frappe's guest-whitelisted
// `paypal_billing.create_subscription_checkout()`, which does its own full, independent
// re-validation (edition must be real + priced, tenant_site must not already have a pending/
// active subscription, etc.) — this route's own checks are a defense-in-depth/better-error-
// message layer, never the real security boundary, exactly like the /api/contact route.
//
// This route reads ONLY the 7 fields the backend function accepts — no pass-through of an
// arbitrary request body.
const MAX_EDITION_CODE_LEN = 60;
const MAX_COMPANY_LEN = 120;
const MAX_EMAIL_LEN = 180;
const MAX_TENANT_SITE_LEN = 63; // a DNS label limit — tenant_site becomes "<this>.pharmacountry.vn".
const TENANT_SITE_PATTERN = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/;

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Malformed request body." }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "Malformed request body." }, { status: 400 });
  }

  const {
    editionCode,
    billingCycle,
    tenantSite,
    companyName,
    customerEmail,
    returnUrl,
    cancelUrl,
  } = body as Record<string, unknown>;

  const edition = typeof editionCode === "string" ? editionCode.trim() : "";
  const cycle = typeof billingCycle === "string" ? billingCycle.trim() : "";
  const site = typeof tenantSite === "string" ? tenantSite.trim().toLowerCase() : "";
  const company = typeof companyName === "string" ? companyName.trim() : "";
  const email = typeof customerEmail === "string" ? customerEmail.trim() : "";
  const retUrl = typeof returnUrl === "string" ? returnUrl.trim() : "";
  const cnclUrl = typeof cancelUrl === "string" ? cancelUrl.trim() : "";

  if (!edition || edition.length > MAX_EDITION_CODE_LEN) {
    return NextResponse.json({ error: "A valid plan is required." }, { status: 400 });
  }
  if (cycle !== "Monthly" && cycle !== "Yearly") {
    return NextResponse.json(
      { error: "Billing cycle must be Monthly or Yearly." },
      { status: 400 }
    );
  }
  if (!site || site.length > MAX_TENANT_SITE_LEN || !TENANT_SITE_PATTERN.test(site)) {
    return NextResponse.json(
      { error: "Subdomain must be lowercase letters, numbers, and hyphens only." },
      { status: 400 }
    );
  }
  if (!company || company.length > MAX_COMPANY_LEN) {
    return NextResponse.json({ error: "A valid company name is required." }, { status: 400 });
  }
  if (!email || !email.includes("@") || email.length > MAX_EMAIL_LEN) {
    return NextResponse.json({ error: "A valid email address is required." }, { status: 400 });
  }
  if (!retUrl || !cnclUrl) {
    return NextResponse.json({ error: "Malformed request body." }, { status: 400 });
  }

  try {
    const result = await createSubscriptionCheckout({
      editionCode: edition,
      billingCycle: cycle as "Monthly" | "Yearly",
      tenantSite: `${site}.pharmacountry.vn`,
      companyName: company,
      customerEmail: email,
      returnUrl: retUrl,
      cancelUrl: cnclUrl,
    });
    return NextResponse.json(result);
  } catch (err) {
    const message =
      err instanceof FrappeApiError
        ? err.message
        : "Could not start checkout right now. Please try again shortly.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
