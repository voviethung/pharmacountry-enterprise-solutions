"use client";

import { useEffect } from "react";

// The true root <html> tag lives in app/layout.tsx (one level above this [locale] segment) and
// can't know the locale at render time, so it defaults to lang="vi". This tiny client component
// corrects `document.documentElement.lang` once the real locale is known, for correctness
// (screen readers / browser language tooling) without duplicating <html> in a nested layout.
export default function HtmlLangSync({ locale }: { locale: string }) {
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return null;
}
