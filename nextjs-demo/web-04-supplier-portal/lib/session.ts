// WEB-04 — reused VERBATIM (structure + the globalThis fix) from
// nextjs-demo/web-03-dealer-portal/lib/session.ts, only renaming the global key and the exported
// cookie name so a browser can never confuse a WEB-03 dealer session cookie with a WEB-04 supplier
// session cookie if both apps somehow ran on the same origin/port during dev.
import crypto from "node:crypto";

export interface SupplierSession {
  token: string;
  frappeSid: string;
  csrfToken: string;
  user: string;
  supplier: string;
  supplierName: string;
  createdAt: number;
  expiresAt: number;
}

const SESSION_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours

// REAL BUG FOUND + FIXED BY WEB-03, REUSED HERE FROM THE START (not rediscovered): Next.js compiles
// Route Handlers (app/api/.../route.ts) and Server Components/layouts into SEPARATE bundles. A plain
// `const sessions = new Map()` at module scope gets duplicated across those bundles — each bundle
// holds its OWN, independent Map instance in the same Node process — so a session created by
// /api/auth/login's Route Handler bundle would be invisible to the (portal) layout's Server
// Component bundle, which would always see an empty Map and redirect straight back to /login even
// with a valid cookie. Fixed by pinning the Map onto `globalThis` — a true process-wide singleton
// unaffected by how many separate module instances of this file get bundled.
const globalForSessions = globalThis as unknown as {
  __web04SupplierSessions?: Map<string, SupplierSession>;
};
const sessions = globalForSessions.__web04SupplierSessions ?? new Map<string, SupplierSession>();
globalForSessions.__web04SupplierSessions = sessions;

export function createSession(
  data: Omit<SupplierSession, "token" | "createdAt" | "expiresAt">
): SupplierSession {
  const token = crypto.randomBytes(32).toString("hex");
  const now = Date.now();
  const session: SupplierSession = { ...data, token, createdAt: now, expiresAt: now + SESSION_TTL_MS };
  sessions.set(token, session);
  return session;
}

export function getSession(token: string | undefined | null): SupplierSession | null {
  if (!token) return null;
  const session = sessions.get(token);
  if (!session) return null;
  if (Date.now() > session.expiresAt) {
    sessions.delete(token);
    return null;
  }
  return session;
}

export function destroySession(token: string | undefined | null): void {
  if (!token) return;
  sessions.delete(token);
}

export const SESSION_COOKIE_NAME = "web04_supplier_session";

// Disclosed limitation, same as WEB-03: sessions live only in this Node process's memory — a
// restart logs everyone out. Accepted for this demo; documented here and in this app's README, not
// silently glossed over.
