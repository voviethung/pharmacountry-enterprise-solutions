// Real PharmaCountry brand mark, ported (not reinvented) from the sibling Quantri-pharmacountry
// project's own design work, copied into `brand-assets/` for this rebrand:
//   - `brand-assets/bimi-logo.svg` — the real compact icon mark (rotated rounded-square outline
//     + filled hexagon "PMCT" badge), used as this project's real BIMI/favicon brand logo.
//   - `brand-assets/CustomLogoFooter.jsx` — the real full wordmark lockup (gradient diamond +
//     "PharmaCountry" text), with the REAL brand gradient stops (#3DBB89 -> #158A57 -> #0A4A2D,
//     accent #1FA76B) that this whole rebrand's color palette is built from.
//   - `brand-assets/CustomLogo.jsx` / `CustomLogo2.jsx` — earlier/alternate colorways of the
//     same two shapes (a teal/cyan diamond variant, and an outline-only PMCT badge) kept only
//     for reference; NOT used here since CustomLogoFooter.jsx's gradient is the most recent/
//     refined real version (its own file header comments and the darker, more legible palette
//     confirm it's the latest iteration).
//
// Two variants are exported, matching the two real shapes above:
//   - `PharmaCountryMark`  — icon-only (the rotated-square + "PMCT" badge), for compact spaces
//     (mobile header, favicon-adjacent contexts).
//   - `PharmaCountryWordmark` — the full diamond + "PharmaCountry" text lockup, for the main
//     header/footer. The original's small ".com" sub-label is deliberately dropped here (this
//     Hub is PharmaCountry's enterprise-software/ERP division, not the pharmacountry.vn B2B
//     marketplace itself) — callers add their own sub-brand label as real, translatable text
//     next to the SVG rather than baking English text into the graphic.

import { useId } from "react";

interface MarkProps {
  size?: number;
  className?: string;
}

interface WordmarkProps {
  width?: number;
  height?: number;
  className?: string;
}

/** Compact icon-only mark — ported from brand-assets/bimi-logo.svg. */
export function PharmaCountryMark({ size = 36, className = "" }: MarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="PharmaCountry"
      className={className}
    >
      <rect x="0" y="0" width="64" height="64" rx="14" fill="#ffffff" />
      <g transform="translate(32, 32)">
        <rect
          x="-22"
          y="-22"
          width="44"
          height="44"
          rx="3"
          ry="3"
          fill="#ffffff"
          stroke="#158A57"
          strokeWidth="4"
          transform="rotate(45)"
        />
        <polygon points="-31,0 -22,-9 22,-9 31,0 22,9 -22,9" fill="#158A57" />
        <text
          x="0"
          y="1"
          fontFamily="Arial, Helvetica, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill="#ffffff"
          textAnchor="middle"
          dominantBaseline="middle"
          letterSpacing="0.5"
        >
          PMCT
        </text>
      </g>
    </svg>
  );
}

/** Full diamond + "PharmaCountry" wordmark lockup — ported from brand-assets/CustomLogoFooter.jsx. */
export function PharmaCountryWordmark({
  width = 168,
  height = 44,
  className = "",
}: WordmarkProps) {
  // Unique per render — this component is mounted more than once on the same page (header +
  // footer), and a hidden instance (e.g. the header's `hidden sm:block` copy on mobile) still
  // leaves its <defs> in the DOM even though it isn't visually shown. A fixed id here would
  // collide across instances, breaking SVG gradient resolution for whichever instance the
  // browser resolves second (the diamond mark rendering hollow/unfilled, hiding "PMCT" — this
  // was observed live on the footer wordmark on mobile, where only the footer instance is
  // visible but the header's still-mounted-but-hidden instance shared its gradient id).
  const uid = useId();
  const gradId = `pmctWordmarkGradient-${uid}`;
  const shineId = `pmctWordmarkShine-${uid}`;
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 168 44"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="PharmaCountry"
      className={className}
    >
      <defs>
        <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3DBB89" />
          <stop offset="45%" stopColor="#158A57" />
          <stop offset="100%" stopColor="#0A4A2D" />
        </linearGradient>
        <radialGradient id={shineId} cx="35%" cy="30%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.42" />
          <stop offset="50%" stopColor="#3DBB89" stopOpacity="0.16" />
          <stop offset="100%" stopColor="#0A4A2D" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Diamond mark */}
      <path d="M 22 4 L 40 22 L 22 40 L 4 22 Z" fill={`url(#${gradId})`} />
      <path d="M 22 4 L 40 22 L 22 40 L 4 22 Z" fill={`url(#${shineId})`} opacity="0.96" />
      <path
        d="M 22 4 L 40 22 L 22 40 L 4 22 Z"
        stroke="#1FA76B"
        strokeWidth="1.6"
        fill="none"
        opacity="0.85"
      />
      <path
        d="M 22 4 L 22 22 M 4 22 L 22 22 L 40 22"
        stroke="#ffffff"
        strokeWidth="0.9"
        opacity="0.18"
      />
      <text
        x="22"
        y="26"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="11"
        fontWeight="700"
        fill="#ffffff"
        textAnchor="middle"
        letterSpacing="-0.2"
      >
        PMCT
      </text>

      {/* Wordmark text */}
      <text
        x="50"
        y="27"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="18"
        fontWeight="700"
        fill="#0A4A2D"
        letterSpacing="-0.4"
      >
        PharmaCountry
      </text>
    </svg>
  );
}
