"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

// Real, working seeded demo accounts — see this app's README ("Test supplier credentials").
// Non-production, demo-only accounts with no real business data at stake. Proper nouns and
// literal credentials — never translated.
const DEMO_ACCOUNTS = [
  {
    key: "cargill",
    label: "Cargill Asia Trading Pte Ltd",
    email: "supplier.cargill.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
  {
    key: "nutreco",
    label: "Nutreco South America S.A.",
    email: "supplier.nutreco.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
];

// Stable machine-readable codes the API route may return (see app/api/auth/login/route.ts).
// Any code not in this set falls back to the generic translated message, rather than breaking.
const KNOWN_ERROR_CODES = new Set([
  "invalid_credentials",
  "not_provisioned",
  "server_error",
  "invalid_request",
  "network",
  "generic",
]);

export default function LoginForm() {
  const router = useRouter();
  const t = useTranslations("login");
  const tErrors = useTranslations("errors");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function translateErrorCode(code: unknown): string {
    const key = typeof code === "string" && KNOWN_ERROR_CODES.has(code) ? code : "generic";
    return tErrors(key);
  }

  async function doLogin(loginUsername: string, loginPassword: string) {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(translateErrorCode(data.error_code));
        setLoading(false);
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError(tErrors("network"));
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    doLogin(username, password);
  }

  function handleDemoLogin(demoEmail: string, demoPassword: string) {
    setUsername(demoEmail);
    setPassword(demoPassword);
    doLogin(demoEmail, demoPassword);
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-teal-200 bg-teal-50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
          {t("demoBox.heading")}
        </p>
        <p className="mt-1 text-xs text-teal-800">{t("demoBox.description")}</p>
        <ul className="mt-2 space-y-1 text-xs text-teal-900">
          {DEMO_ACCOUNTS.map((account) => (
            <li key={account.key}>
              <span className="font-medium">{account.label}:</span> {account.email} ·{" "}
              {account.password}
            </li>
          ))}
        </ul>
        <div className="mt-3 flex gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.key}
              type="button"
              onClick={() => handleDemoLogin(account.email, account.password)}
              disabled={loading}
              className="flex-1 rounded-md border border-teal-300 bg-white px-2 py-1.5 text-xs font-semibold text-teal-700 hover:bg-teal-100 disabled:opacity-60"
            >
              {account.key === "cargill" ? t("demoBox.loginAsCargill") : t("demoBox.loginAsNutreco")}
            </button>
          ))}
        </div>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-slate-700">
          {t("fields.email")}
        </label>
        <input
          id="username"
          type="email"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          placeholder="supplier.cargill.portal@pharmacountry.vn"
          autoComplete="username"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-700">
          {t("fields.password")}
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          autoComplete="current-password"
        />
      </div>
      {error && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-600 disabled:opacity-60"
      >
        {loading ? t("signingIn") : t("signIn")}
      </button>
    </form>
    </div>
  );
}
