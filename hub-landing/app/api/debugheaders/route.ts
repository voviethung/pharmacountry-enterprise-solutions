import { NextResponse } from "next/server";

// Decommissioned. This route was a temporary, one-time diagnostic used during the bilingual
// i18n rebrand to empirically confirm that Cloudflare Tunnel forwards a real `CF-IPCountry`
// header to this container (it does — confirmed live against https://pharmacountry.vn, see
// middleware.ts's own comment for how that real finding shaped the locale-detection logic).
// Left in place as an inert 404 (rather than deleted) since this environment has no git history
// to fall back on for this app; not part of the site's real routes.
export async function GET() {
  return NextResponse.json({ error: "Not found." }, { status: 404 });
}
