import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/auth";

// Force dynamic rendering — this reads the session cookie and redirects based on live login
// state. Without this, Next.js could prerender it once at Docker build time and bake in a
// stale redirect for every visitor.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const session = await getCurrentSession();
  redirect(session ? "/dashboard" : "/login");
}
