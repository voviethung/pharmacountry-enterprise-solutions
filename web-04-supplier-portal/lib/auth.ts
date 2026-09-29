import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getSession, SESSION_COOKIE_NAME, type SupplierSession } from "./session";

export async function getCurrentSession(): Promise<SupplierSession | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  return getSession(token);
}

export async function requireSession(): Promise<SupplierSession> {
  const session = await getCurrentSession();
  if (!session) redirect("/login");
  return session;
}

export { SESSION_COOKIE_NAME };
