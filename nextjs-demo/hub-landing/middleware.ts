import { NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

const intlMiddleware = createIntlMiddleware(routing);

// Real locale detection, run once per request BEFORE next-intl's own middleware ever sees an
// un-prefixed path — this is what makes "/" resolve to /vi for a Vietnam-based visitor and
// /en for everyone else, per the user's explicit "mac dinh tieng Viet" requirement.
//
// PRIMARY SIGNAL: Cloudflare's own edge adds a real `CF-IPCountry` request header to every
// request that passes through Cloudflare, INCLUDING traffic proxied via cloudflared/Cloudflare
// Tunnel (confirmed against Cloudflare's own documentation: "HTTP request headers" — CF-Ray,
// CF-Connecting-IP, CF-IPCountry, CF-Visitor are added at the edge regardless of whether the
// origin is reached via a direct proxy or a Tunnel; the Tunnel daemon does not strip them, it
// just carries the already-decorated request through to this container). This is far more
// reliable than Accept-Language for "is this visitor geographically in Vietnam" — many VN
// users run browsers/OSes configured in en-US.
//
// FALLBACK: standard Accept-Language header, for the case CF-IPCountry is ever missing (e.g.
// a direct localhost/dev request that never went through Cloudflare at all).
//
// GENUINELY AMBIGUOUS: default to Vietnamese, matching the user's own explicit stated
// preference, rather than defaulting to English.
//
// CRAWLER OVERRIDE (checked first, before CF-IPCountry): a link-preview bot (Zalo, Facebook,
// etc.) fetching the bare `pharmacountry.vn` for its OG card is not "a visitor" in the
// geo-detection sense at all — it typically runs from infrastructure outside Vietnam and/or
// sends a generic `Accept-Language: en-US` regardless of who the link was actually shared with,
// so the normal CF-IPCountry/Accept-Language logic below can't be trusted for it (confirmed
// live: a link shared in Zalo to a VN contact rendered an English OG card). Since the real
// audience is VN-default by explicit requirement, every known preview/search crawler is forced
// to the default locale directly, rather than running through geo detection at all.
const CRAWLER_USER_AGENT_PATTERN =
  /facebookexternalhit|Facebot|Twitterbot|LinkedInBot|WhatsApp|TelegramBot|Slackbot|Discordbot|SkypeUriPreview|Pinterest|redditbot|vkShare|Zalo|Googlebot|bingbot|Applebot|YandexBot|DuckDuckBot/i;

function detectLocale(request: NextRequest): "vi" | "en" {
  const userAgent = request.headers.get("user-agent") || "";
  if (CRAWLER_USER_AGENT_PATTERN.test(userAgent)) {
    return routing.defaultLocale;
  }

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

  // Already has a real locale prefix (either the visitor followed a link with one, or used the
  // manual VI/EN switcher in the header) — next-intl just needs to set up its own request
  // context here, no further auto-detection (the prefix itself is authoritative once present).
  return intlMiddleware(request);
}

export const config = {
  // Skip the Next.js internals, any file with an extension (images, favicon, etc.), and the
  // Frappe API isn't proxied through this app anyway — but explicitly excluding /api/ here too
  // in case a future route handler is ever added under this app's own /api.
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
