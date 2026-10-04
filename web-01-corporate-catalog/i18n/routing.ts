import { defineRouting } from "next-intl/routing";

// Two locales: Vietnamese (default) and English. Vietnamese is the default because the real
// traffic for pharmacountry.vn (and its catalog.pharmacountry.vn sub-site) is expected to be
// predominantly Vietnam-based, matching the same default already used by the sibling
// hub-landing app (see middleware.ts for the actual Vietnam-vs-not detection logic that runs
// BEFORE this default ever applies).
export const routing = defineRouting({
  locales: ["vi", "en"],
  defaultLocale: "vi",
  localePrefix: "always",
});

export type Locale = (typeof routing.locales)[number];
