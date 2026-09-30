"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// Real, working seeded demo accounts — see this app's README ("Test farm credentials").
// Non-production, demo-only accounts with no real business data at stake.
const DEMO_ACCOUNTS = [
  {
    key: "alpha",
    label: "Demo Alpha (cattle farm, generous credit)",
    email: "farm.alpha.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
  {
    key: "beta",
    label: "Demo Beta (swine farm, tight credit limit)",
    email: "farm.beta.portal@pharmacountry.vn",
    password: "Demo@1234",
  },
];

export default function LoginForm() {
  const router = useRouter();
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
        setError(data.error || "Login failed.");
        setLoading(false);
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Could not reach the portal. Please try again.");
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
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          Demo Access
        </p>
        <p className="mt-1 text-xs text-emerald-800">
          Try it now with real seeded demo accounts — no real business data at stake.
        </p>
        <ul className="mt-2 space-y-1 text-xs text-emerald-900">
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
              className="flex-1 rounded-md border border-emerald-300 bg-white px-2 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
            >
              Log in as Demo {account.key === "alpha" ? "Alpha" : "Beta"}
            </button>
          ))}
        </div>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-slate-700">
          Email
        </label>
        <input
          id="username"
          type="email"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          placeholder="farm.alpha.portal@pharmacountry.vn"
          autoComplete="username"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-700">
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
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
        className="w-full rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-60"
      >
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </form>
    </div>
  );
}
