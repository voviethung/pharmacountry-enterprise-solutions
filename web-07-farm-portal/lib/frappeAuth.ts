// WEB-07 — real login against Frappe's own NATIVE session endpoint (`/api/method/login`), never
// a hand-rolled password check. Reuses WEB-01/02/03/04's own Node `http`-module Host-header
// workaround (see lib/api.ts for the full explanation) since Frappe routes purely on the HTTP
// `Host` header and this machine has no DNS entry for test.demo.local/pharmacountry.vn.
//
// This runs SERVER-SIDE ONLY (called from app/api/auth/login/route.ts) — the real Frappe `sid`
// this returns is handed to lib/session.ts's in-memory store and never reaches the browser. See
// farm_portal_api.py's module docstring and this app's README for the full authentication design
// (reused verbatim from WEB-03/04, not redesigned).
import http from "node:http";

const FRAPPE_BASE_URL = process.env.FRAPPE_BASE_URL || "http://localhost:8082";
const FRAPPE_SITE_HOST = process.env.FRAPPE_SITE_HOST || "test.demo.local";

export class FrappeLoginError extends Error {}

export interface FrappeLoginResult {
  sid: string;
  fullName?: string;
}

export function loginToFrappe(usr: string, pwd: string): Promise<FrappeLoginResult> {
  const url = new URL("/api/method/login", FRAPPE_BASE_URL);
  const body = new URLSearchParams({ usr, pwd }).toString();

  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: url.pathname,
        method: "POST",
        headers: {
          Host: FRAPPE_SITE_HOST,
          "Content-Type": "application/x-www-form-urlencoded",
          "Content-Length": Buffer.byteLength(body),
          Accept: "application/json",
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode || 0;
          const setCookie = res.headers["set-cookie"] || [];
          const sidCookie = setCookie.find((c) => c.startsWith("sid="));
          const sid = sidCookie ? sidCookie.split(";")[0].slice("sid=".length) : null;
          if (status !== 200 || !sid || sid === "Guest") {
            reject(new FrappeLoginError("Invalid username or password."));
            return;
          }
          try {
            const parsed = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
            resolve({ sid, fullName: parsed.full_name });
          } catch {
            resolve({ sid });
          }
        });
      }
    );
    req.on("error", () => reject(new FrappeLoginError("Could not reach the backend.")));
    req.write(body);
    req.end();
  });
}

export function logoutFromFrappe(sid: string): Promise<void> {
  const url = new URL("/api/method/logout", FRAPPE_BASE_URL);
  return new Promise((resolve) => {
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: url.pathname,
        method: "POST",
        headers: { Host: FRAPPE_SITE_HOST, Cookie: `sid=${sid}`, Accept: "application/json" },
      },
      (res) => {
        res.on("data", () => {});
        res.on("end", () => resolve());
      }
    );
    // Logout is best-effort — the Next.js side always destroys its own session regardless.
    req.on("error", () => resolve());
    req.end();
  });
}
