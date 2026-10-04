import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware wrappers around Next.js's own Link/useRouter/redirect/usePathname — every
// internal navigation in this app should import from here, not from "next/navigation" or
// "next/link" directly, so the current locale prefix is preserved automatically. This also
// matters for the protected-route redirect in lib/auth.ts: this `redirect()` picks up the
// current request's locale automatically, so requireSession() lands on /vi/login or /en/login
// correctly instead of a bare /login that would need a second round-trip through the middleware.
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
