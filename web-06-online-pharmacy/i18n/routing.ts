import { defineRouting } from "next-intl/routing";

// Two locales: Vietnamese (default) and English. Vietnamese is the default because this is a
// real consumer-facing pharmacy storefront aimed at a Vietnamese audience — see middleware.ts
// for the actual Vietnam-vs-not detection logic that runs before this default ever applies.
export const routing = defineRouting({
  locales: ["vi", "en"],
  defaultLocale: "vi",
  localePrefix: "always",
});

export type Locale = (typeof routing.locales)[number];
