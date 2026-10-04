"use client";

import { useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

// Real, working seeded demo accounts — see this app's README ("Test dealer credentials").
// Non-production, demo-only accounts with no real business data at stake. The email/password
// values themselves are real demo credentials and are never translated.
const DEMO_ACCOUNTS = [
  {
    key: "alpha",
    email: "dealer.alpha.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
  {
    key: "beta",
    email: "dealer.beta.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
] as const;

// Route Handlers run outside next-intl's locale context, so app/api/auth/login/route.ts returns
// a stable machine-readable `error_code` instead of English prose. Only codes present in
// messages/*.json's "errors" namespace are translated directly; anything else (or a future code
// this client doesn't know about yet) falls back to "errors.unknown".
const KNOWN_ERROR_CODES = new Set([
  "invalid_credentials",
  "invalid_request_body",
  "missing_credentials",
  "not_provisioned",
  "server_error",
]);

export default function LoginForm() {
  const router = useRouter();
  const t = useTranslations("login");
  const tErrors = useTranslations("errors");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
        const code = typeof data.error_code === "string" ? data.error_code : null;
        setError(tErrors(code && KNOWN_ERROR_CODES.has(code) ? code : "unknown"));
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
      <div className="rounded-md border border-indigo-200 bg-indigo-50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
          {t("demoAccessLabel")}
        </p>
        <p className="mt-1 text-xs text-indigo-800">{t("demoAccessIntro")}</p>
        <ul className="mt-2 space-y-1 text-xs text-indigo-900">
          {DEMO_ACCOUNTS.map((account) => (
            <li key={account.key}>
              <span className="font-medium">
                {account.key === "alpha" ? t("demoAccountAlphaLabel") : t("demoAccountBetaLabel")}:
              </span>{" "}
              {account.email} · {account.password}
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
              className="flex-1 rounded-md border border-indigo-300 bg-white px-2 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 disabled:opacity-60"
            >
              {account.key === "alpha" ? t("demoLoginButtonAlpha") : t("demoLoginButtonBeta")}
            </button>
          ))}
        </div>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-slate-700">
          {t("emailLabel")}
        </label>
        <input
          id="username"
          type="email"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder="dealer.alpha.portal@pharmacountry.vn"
          autoComplete="username"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-700">
          {t("passwordLabel")}
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-60"
      >
        {loading ? t("signingIn") : t("signInButton")}
      </button>
    </form>
    </div>
  );
}
