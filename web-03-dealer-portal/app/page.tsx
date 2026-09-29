import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/auth";

// Force dynamic rendering — this reads the session cookie and redirects based on live
// login state. Without this, Next.js would prerender it once at Docker build time (no cookie
// present, no backend reachable) and bake that snapshot in for every visitor forever.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const session = await getCurrentSession();
  redirect(session ? "/dashboard" : "/login");
}
