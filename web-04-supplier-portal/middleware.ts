import { NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

const intlMiddleware = createIntlMiddleware(routing);

// Real locale detection, run once per request BEFORE next-intl's own middleware ever sees an
// un-prefixed path — mirrors hub-landing/middleware.ts exactly (same reasoning: CF-IPCountry is
// the primary signal, Accept-Language is the fallback, Vietnamese is the ambiguous default).
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
  // Skip Next.js internals, any file with an extension, and /api — this app's Route Handlers
  // (session cookie login/logout, quotations) must never get a locale prefix.
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
