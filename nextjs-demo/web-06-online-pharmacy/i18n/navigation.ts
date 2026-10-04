import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware wrappers around Next.js's own Link/useRouter/redirect/usePathname — every
// internal navigation in this app should import from here, not from "next/link" or
// "next/navigation" directly, so the current locale prefix is preserved automatically.
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
