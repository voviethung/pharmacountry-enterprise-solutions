import React from "react";

export default function CustomLogo() {
  return (
    <svg
      width="100"
      height="40"
      viewBox="0 0 120 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Define gradient for diamond shine effect */}
      <defs>
        <linearGradient id="diamondGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#2ab5c4" stopOpacity="1" />
          <stop offset="25%" stopColor="#1e8f9a" stopOpacity="1" />
          <stop offset="50%" stopColor="#0a3d42" stopOpacity="1" />
          <stop offset="75%" stopColor="#166f7a" stopOpacity="1" />
          <stop offset="100%" stopColor="#40d4e0" stopOpacity="0.9" />
        </linearGradient>

        {/* Shine highlight gradient */}
        <radialGradient id="diamondShine" cx="40%" cy="30%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.3" />
          <stop offset="50%" stopColor="#2ab5c4" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#0a3d42" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Diamond shape with gradient background */}
      <path
        d="M 60 2 L 115 20 L 60 38 L 5 20 Z"
        fill="url(#diamondGradient)"
      />

      {/* Shine overlay */}
      <path
        d="M 60 2 L 115 20 L 60 38 L 5 20 Z"
        fill="url(#diamondShine)"
      />

      {/* Diamond border for definition */}
      <path
        d="M 60 2 L 115 20 L 60 38 L 5 20 Z"
        stroke="#40d4e0"
        strokeWidth="1.5"
        fill="none"
        opacity="0.5"
      />

      {/* Inner facets for gem effect */}
      <path
        d="M 60 2 L 60 20 M 5 20 L 60 20 L 115 20"
        stroke="#ffffff"
        strokeWidth="0.8"
        opacity="0.15"
      />

      {/* Main text: PharmaCountry - white, italic */}
      <text
        x="60"
        y="22.5"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="10"
        fontWeight="700"
        fontStyle="normal"
        fill="#ffffff"
        letterSpacing="-0.3"
        textAnchor="middle"
      >
        PharmaCountry
      </text>

      {/* Small ".com" positioned below */}
      <text
        x="60"
        y="29"
        fontFamily="Arial, Helvetica, sans-serif"
        fontSize="7"
        fontWeight="600"
        fontStyle="normal"
        fill="#ffffff"
        textAnchor="middle"
        opacity="0.95"
      >
        .com
      </text>
    </svg>
  );
}
// import React from "react";

// export default function PharmaCountryLogo({ width = 300, height = 40 }) {
//   return (
//     <svg
//       width={width}
//       height={height}
//       viewBox="0 0 300 40"
//       xmlns="http://www.w3.org/2000/svg"
//     >
//       <text
//         x="0"
//         y="30"
//         fontFamily="Arial, sans-serif"
//         fontSize="18"
//         fill="#1dbf73"
//       >
//         Pharma
//       </text>
//       <text
//         x="65"
//         y="30"
//         fontFamily="Arial, sans-serif"
//         fontSize="18"
//         fill="#404145"
//       >
//         Country
//       </text>
//     </svg>
//   );
// }