import type { Metadata } from "next";
import { getBrandProfile } from "@/lib/api";

export const metadata: Metadata = {
  title: "Our Story",
};

export default async function OurStoryPage() {
  const profile = await getBrandProfile();

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
        {profile.company_name}
      </p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-stone-900">Our Story</h1>

      <div className="mt-8 space-y-6 text-lg leading-relaxed text-stone-700">
        <p>{profile.mission}</p>
        <p>{profile.philosophy}</p>
      </div>

      <section className="mt-12 rounded-xl border border-stone-200 bg-stone-50 p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          Our formulation philosophy
        </h2>
        <p className="mt-3 text-stone-600 leading-relaxed">
          We keep our formula short and legible: six ingredients, each doing one clear job —
          a real active ingredient, a fizz reaction, a gentle sweetener, and a natural-style
          flavor. Nothing is added to the formula that isn&apos;t on the label, and nothing on
          the label is rounded up or hidden. The full ingredient breakdown, with real
          proportions pulled from our own manufacturing formula, is on our{" "}
          <a href="/product" className="font-medium text-emerald-800 hover:underline">
            product page
          </a>
          .
        </p>
      </section>

      <section className="mt-8 rounded-xl border border-stone-200 bg-stone-50 p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          Made in {profile.country}
        </h2>
        <p className="mt-3 text-stone-600 leading-relaxed">
          {profile.company_name} formulates and manufactures every batch in-house, with our own
          in-house lab testing every release against a published potency specification before
          it&apos;s cleared to ship — see the real, latest verified result on our{" "}
          <a href="/product" className="font-medium text-emerald-800 hover:underline">
            product page
          </a>
          .
        </p>
      </section>
    </div>
  );
}
