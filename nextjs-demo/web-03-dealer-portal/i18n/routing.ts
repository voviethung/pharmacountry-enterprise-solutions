import { defineRouting } from "next-intl/routing";

// Two locales: Vietnamese (default) and English — matching the Hub's own bilingual setup
// (hub-landing). Vietnamese is the default because the real traffic for pharmacountry.vn is
// expected to be predominantly Vietnam-based; see middleware.ts for the actual Vietnam-vs-not
// detection logic that runs before this default ever applies.
export const routing = defineRouting({
  locales: ["vi", "en"],
  defaultLocale: "vi",
  localePrefix: "always",
});

export type Locale = (typeof routing.locales)[number];
