import React from "react";

export default function CustomLogoFooter({ width = 160, height = 50 }) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 160 50"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="PharmaCountry logo"
    >
      <defs>
        <linearGradient id="diamondGradientFooter" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3DBB89" />
          <stop offset="45%" stopColor="#158A57" />
          <stop offset="100%" stopColor="#0A4A2D" />
        </linearGradient>

        <radialGradient id="diamondShineFooter" cx="35%" cy="30%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.42" />
          <stop offset="50%" stopColor="#3DBB89" stopOpacity="0.16" />
          <stop offset="100%" stopColor="#0A4A2D" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Diamond shape */}
      <path d="M 80 5 L 152 25 L 80 45 L 8 25 Z" fill="url(#diamondGradientFooter)" />
      <path d="M 80 5 L 152 25 L 80 45 L 8 25 Z" fill="url(#diamondShineFooter)" opacity="0.96" />
      <path
        d="M 80 5 L 152 25 L 80 45 L 8 25 Z"
        stroke="#1FA76B"
        strokeWidth="1.8"
        fill="none"
        opacity="0.85"
      />

      {/* Inner facets for dimension */}
      <path
        d="M 80 5 L 80 25 M 8 25 L 80 25 L 152 25"
        stroke="#ffffff"
        strokeWidth="1"
        opacity="0.18"
      />

      {/* Text - PharmaCountry */}
      <text
        x="80"
        y="27"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="13"
        fontWeight="700"
        fill="#ffffff"
        letterSpacing="-0.4"
        textAnchor="middle"
      >
        PharmaCountry
      </text>

      {/* Text - B2B Marketplace */}
      <text
        x="80"
        y="36"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="10"
        fontWeight="600"
        fill="#ffffff"
        textAnchor="middle"
        opacity="0.85"
      >
        .com
      </text>
    </svg>
  );
}
