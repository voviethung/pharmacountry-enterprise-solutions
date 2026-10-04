import { NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

const intlMiddleware = createIntlMiddleware(routing);

// Real locale detection, run once per request BEFORE next-intl's own middleware ever sees an
// un-prefixed path — mirrors hub-landing's own middleware.ts exactly (same detection order:
// Cloudflare's CF-IPCountry header first, then Accept-Language, then default to Vietnamese).
//
// PRIMARY SIGNAL: Cloudflare's own edge adds a real `CF-IPCountry` request header to every
// request that passes through Cloudflare, including traffic proxied via a Tunnel.
//
// FALLBACK: standard Accept-Language header, for the case CF-IPCountry is ever missing (e.g. a
// direct localhost/dev request that never went through Cloudflare at all).
//
// GENUINELY AMBIGUOUS: default to Vietnamese rather than English.
function detectLocale(request: NextRequest): "vi" | "en" {
  const cfCountry = request.headers.get("cf-ipcountry");
  if (cfCountry && cfCountry.trim()) {
    return cfCountry.trim().toUpperCase() === "VN" ? "vi" : "en";
  }
  const acceptLanguage = request.headers.get("accept-language") || "";
  const primary = (acceptLanguage.split(",")[0] || "").trim().toLowerCase();
  if (primary.startsWith("vi")) return "vi";
  if (primary.startsWith("en")) return "en";
  return "vi";
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasLocalePrefix = routing.locales.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`)
  );

  if (!hasLocalePrefix) {
    const locale = detectLocale(request);
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}${pathname === "/" ? "" : pathname}`;
    return NextResponse.redirect(url);
  }

  return intlMiddleware(request);
}

export const config = {
  // Skip Next.js internals, any file with an extension, and — critically for this app — every
  // Route Handler under /api (session login/logout, orders, returns): those must never get a
  // locale prefix and must keep working exactly as before.
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
