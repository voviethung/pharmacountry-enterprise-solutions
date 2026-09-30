import { redirect } from "next/navigation";

// Fallback stub — see app/page.tsx's own comment. The real About page lives at
// app/[locale]/about/page.tsx.
export default function AboutRedirectPage() {
  redirect("/vi/about");
}
