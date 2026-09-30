import { NextResponse } from "next/server";
import { submitContactLead, FrappeApiError } from "@/lib/api";

// Server-side Route Handler backing the Hub's public /contact form. Exists as a thin proxy in
// front of `lib/api.ts`'s `submitContactLead()` for one structural reason: the browser's own
// <form> can only ever talk to THIS Next.js server (same-origin fetch), never directly to the
// Frappe backend — `lib/api.ts` calls Frappe using Node's raw `http` module specifically to set
// a Host header (see that file's own top-of-file comment), and browsers cannot do that at all
// (the Fetch/XHR spec forbids client-side scripts from setting Host). So the real request path
// is: browser -> this route handler (Node server) -> Frappe's guest-whitelisted
// `submit_contact_lead()` (which does its own, independent, full re-validation — this route's
// own checks are a defense-in-depth/better-error-message layer, never the real security
// boundary, exactly like WEB-05's own checkout route treats its frontend validation).
//
// This route reads ONLY the same 4 fields the backend accepts — no pass-through of an arbitrary
// request body.
const MAX_NAME_LEN = 120;
const MAX_COMPANY_LEN = 120;
const MAX_EMAIL_LEN = 180;
const MAX_MESSAGE_LEN = 2000;

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

  const { fullName, email, company, message } = body as Record<string, unknown>;

  const name = typeof fullName === "string" ? fullName.trim() : "";
  const emailStr = typeof email === "string" ? email.trim() : "";
  const companyStr = typeof company === "string" ? company.trim() : "";
  const messageStr = typeof message === "string" ? message.trim() : "";

  if (!name || name.length > MAX_NAME_LEN) {
    return NextResponse.json({ error: "A valid name is required." }, { status: 400 });
  }
  if (!emailStr || !emailStr.includes("@") || emailStr.length > MAX_EMAIL_LEN) {
    return NextResponse.json({ error: "A valid email address is required." }, { status: 400 });
  }
  if (companyStr.length > MAX_COMPANY_LEN) {
    return NextResponse.json({ error: "Company name is too long." }, { status: 400 });
  }
  if (!messageStr || messageStr.length > MAX_MESSAGE_LEN) {
    return NextResponse.json({ error: "A message is required." }, { status: 400 });
  }

  try {
    const result = await submitContactLead({
      fullName: name,
      email: emailStr,
      company: companyStr,
      message: messageStr,
    });
    return NextResponse.json(result);
  } catch (err) {
    const message =
      err instanceof FrappeApiError
        ? err.message
        : "Could not submit your message right now. Please try again shortly.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
