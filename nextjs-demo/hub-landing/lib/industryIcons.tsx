// Maps this platform's real `industry_category` values (from get_industry_solutions(),
// grepped live from the running backend — Animal Feed, Aquaculture, Cosmetics,
// Horizontal / Cross-Industry, Livestock, Medical Device, Nutraceutical, Pharmaceutical,
// Processing, Veterinary) to a real icon + a color accent, purely for visual identity on
// the industry cards. No product photography exists anywhere in this platform's real data
// (every golden demo's Item.image field is empty, confirmed during WEB-01/WEB-02's own
// builds) — icons are an honest substitute, not a claim of real product imagery.

import type { LucideIcon } from "lucide-react";
import {
  Pill,
  Wheat,
  Fish,
  Sparkles,
  Stethoscope,
  Beef,
  FlaskConical,
  Factory,
  PawPrint,
  Layers,
} from "lucide-react";

export interface CategoryVisual {
  icon: LucideIcon;
  bg: string;
  fg: string;
}

const DEFAULT_VISUAL: CategoryVisual = {
  icon: Layers,
  bg: "bg-slate-100",
  fg: "text-slate-600",
};

const CATEGORY_VISUALS: Record<string, CategoryVisual> = {
  Pharmaceutical: { icon: Pill, bg: "bg-sky-100", fg: "text-sky-700" },
  "Animal Feed": { icon: Wheat, bg: "bg-amber-100", fg: "text-amber-700" },
  Aquaculture: { icon: Fish, bg: "bg-cyan-100", fg: "text-cyan-700" },
  Cosmetics: { icon: Sparkles, bg: "bg-pink-100", fg: "text-pink-700" },
  "Medical Device": { icon: Stethoscope, bg: "bg-indigo-100", fg: "text-indigo-700" },
  Livestock: { icon: Beef, bg: "bg-orange-100", fg: "text-orange-700" },
  Nutraceutical: { icon: FlaskConical, bg: "bg-emerald-100", fg: "text-emerald-700" },
  Processing: { icon: Factory, bg: "bg-violet-100", fg: "text-violet-700" },
  Veterinary: { icon: PawPrint, bg: "bg-teal-100", fg: "text-teal-700" },
  "Horizontal / Cross-Industry": { icon: Layers, bg: "bg-slate-100", fg: "text-slate-600" },
};

export function visualForCategory(category: string): CategoryVisual {
  return CATEGORY_VISUALS[category] ?? DEFAULT_VISUAL;
}
