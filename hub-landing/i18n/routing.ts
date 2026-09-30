import { defineRouting } from "next-intl/routing";

// Two locales: Vietnamese (default) and English. Vietnamese is the default because the real
// traffic for pharmacountry.vn is expected to be predominantly Vietnam-based, and the user
// explicitly asked for "mac dinh tieng Viet" (default Vietnamese) as the fallback whenever
// locale detection is genuinely ambiguous (see middleware.ts for the actual Vietnam-vs-not
// detection logic that runs BEFORE this default ever applies).
export const routing = defineRouting({
  locales: ["vi", "en"],
  defaultLocale: "vi",
  localePrefix: "always",
});

export type Locale = (typeof routing.locales)[number];
