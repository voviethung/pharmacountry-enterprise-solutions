import { redirect } from "next/navigation";

// Fallback stub — see app/page.tsx's own comment. The real Solutions page lives at
// app/[locale]/solutions/page.tsx.
export default function SolutionsRedirectPage() {
  redirect("/vi/solutions");
}
