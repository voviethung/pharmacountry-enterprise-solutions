// WEB-03 — server-only dealer session store.
//
// AUTHENTICATION DESIGN (see dealer_portal_api.py's module docstring for the full backend-side
// half of this design): a real Frappe session cookie (`sid`) is obtained server-side, by this
// app's own /api/auth/login Route Handler, by calling Frappe's NATIVE `/api/method/login`
// endpoint (lib/frappeAuth.ts). That real `sid` is NEVER sent to the browser — it is kept here,
// in a server-only in-memory store, keyed by an opaque, random, Next.js-owned token. The browser
// only ever receives THAT opaque token, as an `httpOnly` cookie scoped to this app's own origin
// (see app/api/auth/login/route.ts) — client-side JS can never read it, and even if it could, it
// is useless against Frappe directly (it is not a real Frappe `sid`).
//
// DISCLOSED LIMITATION: this Map lives in the Next.js server process's memory. A dev/prod restart
// clears every session (every dealer would need to log in again) — a real production deployment
// would back this with a shared store (Redis, an encrypted/signed cookie holding the Frappe sid
// itself, etc.) so sessions survive a restart / work across multiple server instances behind a
// load balancer. For a single-process demo this is an accepted, documented simplification, not an
// oversight — see this app's own README, "Authentication design" section.
import crypto from "node:crypto";

export interface DealerSession {
  token: string;
  frappeSid: string;
  csrfToken: string;
  user: string;
  customer: string;
  customerName: string;
  priceList: string;
  createdAt: number;
  expiresAt: number;
}

const SESSION_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours

// REAL BUG FOUND + FIXED: Next.js compiles Route Handlers (app/api/.../route.ts) and Server
// Components/layouts into SEPARATE bundles. A plain `const sessions = new Map()` at module scope
// got duplicated across those bundles — each bundle held its OWN, independent Map instance in
// the same Node process — so a session created by /api/auth/login's Route Handler bundle was
// invisible to the (portal) layout's Server Component bundle, which always saw an empty Map and
// redirected straight back to /login even with a valid cookie (empirically confirmed: curl'ing
// /dashboard right after a successful login, in BOTH `next dev` and a production `next
// build`+`next start`, still redirected). Fixed by pinning the Map onto `globalThis` — a true
// process-wide singleton unaffected by how many separate module instances of this file get
// bundled — the same well-known workaround used for "don't create multiple PrismaClient
// instances" in Next.js apps.
const globalForSessions = globalThis as unknown as {
  __web03DealerSessions?: Map<string, DealerSession>;
};
const sessions = globalForSessions.__web03DealerSessions ?? new Map<string, DealerSession>();
globalForSessions.__web03DealerSessions = sessions;

export function createSession(
  data: Omit<DealerSession, "token" | "createdAt" | "expiresAt">
): DealerSession {
  const token = crypto.randomBytes(32).toString("hex");
  const now = Date.now();
  const session: DealerSession = {
    ...data,
    token,
    createdAt: now,
    expiresAt: now + SESSION_TTL_MS,
  };
  sessions.set(token, session);
  return session;
}

export function getSession(token: string | undefined | null): DealerSession | null {
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

export const SESSION_COOKIE_NAME = "web03_dealer_session";
