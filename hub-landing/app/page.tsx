import { redirect } from "next/navigation";

// Dead-code-in-practice fallback: middleware.ts's matcher covers "/" and redirects every
// visitor to /vi or /en (via real CF-IPCountry/Accept-Language detection) before Next.js
// routing ever reaches this file. This stub exists only so the route isn't a 404 if middleware
// is ever bypassed (e.g. a raw internal health check). The real home page lives at
// app/[locale]/page.tsx.
export default function RootPage() {
  redirect("/vi");
}
