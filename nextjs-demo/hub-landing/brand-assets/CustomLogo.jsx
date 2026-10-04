import React from "react";

/**
 * CustomLogoOption4 - Square rotated 45° with PMCT text
 * 
 * Design specs:
 * - Square shape rotated 45 degrees
 * - Border radius: 4px
 * - Outline style (no fill)
 * - Border: 3px solid, color $primary-darker (#156b44)
 * - Diagonal length: 30px (side = 30/√2 ≈ 21.21px)
 * - Text "PMCT" centered, watermark style, color $primary-darker
 */
export default function CustomLogo({ size = 30, className = "", fontSize = 8 }) {
  // Diagonal = 30px, so side = diagonal / √2 ≈ 21.21px
  const diagonal = size;
  const side = diagonal / Math.SQRT2;
  const primaryDarker = "#2ebd85";
  
  // SVG viewBox needs to accommodate the rotated square plus border
  // Center at (half of viewBox, half of viewBox)
  const viewBoxSize = diagonal + 4; // extra space for border
  const center = viewBoxSize / 2;
  
  return (
    <svg
      width={viewBoxSize}
      height={viewBoxSize}
      viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="PharmaCountry PMCT logo"
      className={className}
    >
      <defs>
        {/* Watermark/embossed effect for text */}
        <filter id="watermarkEffect" x="-20%" y="-20%" width="140%" height="140%">
          <feOffset dx="0.3" dy="0.3" result="offsetOut" in="SourceAlpha" />
          <feGaussianBlur stdDeviation="0.2" result="blurOut" in="offsetOut" />
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
        </filter>
      </defs>

      {/* Rotated square with rounded corners */}
      <g transform={`rotate(45 ${center} ${center})`}>
        <rect
          x={center - side / 2}
          y={center - side / 2}
          width={side}
          height={side}
          rx="4"
          ry="4"
          fill="none"
          stroke={primaryDarker}
          strokeWidth="3"
        />
      </g>

      {/* PMCT text - horizontal, centered, watermark style */}
      <text
        x={center}
        y={center}
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize={fontSize}
        fontWeight="600"
        fill={primaryDarker}
        textAnchor="middle"
        dominantBaseline="central"
        letterSpacing="0.3"
        filter="url(#watermarkEffect)"
        opacity="1.0"
      >
        PMCT
      </text>
    </svg>
  );
}

/**
 * Variant with custom colors
 */
export function CustomLogoColored({ 
  size = 30, 
  borderColor = "#156b44", 
  textColor = "#156b44",
  className = "" 
}) {
  const diagonal = size;
  const side = diagonal / Math.SQRT2;
  const viewBoxSize = diagonal + 8;
  const center = viewBoxSize / 2;
  const fontSize = Math.max(5, size * 0.2);
  
  return (
    <svg
      width={viewBoxSize}
      height={viewBoxSize}
      viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="PharmaCountry PMCT logo"
      className={className}
    >
      <defs>
        <filter id="watermarkEffectColored" x="-20%" y="-20%" width="140%" height="140%">
          <feOffset dx="0.3" dy="0.3" result="offsetOut" in="SourceAlpha" />
          <feGaussianBlur stdDeviation="0.2" result="blurOut" in="offsetOut" />
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
        </filter>
      </defs>

      <g transform={`rotate(45 ${center} ${center})`}>
        <rect
          x={center - side / 2}
          y={center - side / 2}
          width={side}
          height={side}
          rx="4"
          ry="4"
          fill="none"
          stroke={borderColor}
          strokeWidth="3"
        />
      </g>

      <text
        x={center}
        y={center}
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize={fontSize}
        fontWeight="700"
        fill={textColor}
        textAnchor="middle"
        dominantBaseline="central"
        letterSpacing="0.3"
        filter="url(#watermarkEffectColored)"
        opacity="1.0"
      >
        PMCT
      </text>
    </svg>
  );
}
