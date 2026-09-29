import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/auth";

// Force dynamic rendering — this reads the session cookie on every request to decide where to
// redirect. Without this, Next.js could prerender it once at Docker build time and bake in a
// single redirect destination for every visitor forever.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const session = await getCurrentSession();
  redirect(session ? "/dashboard" : "/login");
}
