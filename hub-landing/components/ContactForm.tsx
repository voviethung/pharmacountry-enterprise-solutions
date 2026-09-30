"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";

type Status = "idle" | "submitting" | "success" | "error";

export default function ContactForm() {
  const t = useTranslations("contact");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const fullName = String(formData.get("fullName") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const company = String(formData.get("company") || "").trim();
    const message = String(formData.get("message") || "").trim();

    if (!fullName || !email || !email.includes("@") || !message) {
      setStatus("error");
      setErrorMessage(t("errorValidation"));
      return;
    }

    setStatus("submitting");
    setErrorMessage(null);

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullName, email, company, message }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(data?.error || t("errorGeneric"));
      }
      setStatus("success");
      form.reset();
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : t("errorGeneric"));
    }
  }

  if (status === "success") {
    return (
      <div className="rounded-lg border border-[#158A57]/30 bg-[#158A57]/5 p-6 text-[#0A4A2D]">
        {t("success")}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="fullName" className="block text-sm font-medium text-slate-900">
          {t("labelName")}
        </label>
        <input
          id="fullName"
          name="fullName"
          type="text"
          required
          maxLength={120}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-900">
          {t("labelEmail")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          maxLength={180}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>
      <div>
        <label htmlFor="company" className="block text-sm font-medium text-slate-900">
          {t("labelCompany")}{" "}
          <span className="font-normal text-slate-400">{t("companyOptional")}</span>
        </label>
        <input
          id="company"
          name="company"
          type="text"
          maxLength={120}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>
      <div>
        <label htmlFor="message" className="block text-sm font-medium text-slate-900">
          {t("labelMessage")}
        </label>
        <textarea
          id="message"
          name="message"
          required
          rows={5}
          maxLength={2000}
          placeholder={t("placeholderMessage")}
          className="mt-1.5 block w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-[#158A57] focus:outline-none focus:ring-1 focus:ring-[#158A57]"
        />
      </div>

      {status === "error" && errorMessage && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <button
        type="submit"
        disabled={status === "submitting"}
        className="inline-flex items-center gap-2 rounded-md bg-[#158A57] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0A4A2D] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "submitting" ? t("submitting") : t("submit")}
      </button>
    </form>
  );
}
