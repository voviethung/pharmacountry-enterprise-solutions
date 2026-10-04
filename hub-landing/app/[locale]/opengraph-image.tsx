import { ImageResponse } from "next/og";

// Next.js file-convention OG image — automatically applies to every page under app/[locale]/
// (home, about, contact, solutions, solutions/[packCode]) unless a more specific route defines
// its own opengraph-image file. Generated from code (real brand gradient/colors, same diamond
// mark shape as components/PharmaCountryLogo.tsx) rather than a static asset, so there's nothing
// to keep in sync by hand — one file, locale-aware, always matches the live brand.

export const alt = "PharmaCountry Enterprise Solutions";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// The exact shape markup from PharmaCountryMark in components/PharmaCountryLogo.tsx, as inline
// SVG JSX — not a nested <img src="data:image/svg+xml;..."> like the first attempt (that
// rasterized through a path with no font data, so its text came out as tofu boxes), and not a
// hand-redrawn div approximation either (that got the badge shape wrong: a rounded rect instead
// of the real hexagon). Satori DOES render SVG primitives (rect/g/polygon) natively and
// pixel-faithfully — but it explicitly does NOT support <text> inside <svg> at all ("<text> nodes
// are not currently supported, please convert them to <path>" — confirmed from the live build
// error). So the SVG below draws ONLY the real hexagon/diamond geometry; "PMCT" is a separate
// plain Satori text <div>, absolutely centered on top of it — the one combination that gets both
// the exact shape AND correctly rendered text.
function LogoMark() {
  return (
    <div
      style={{
        display: "flex",
        position: "relative",
        width: 120,
        height: 120,
        marginRight: 36,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg width={120} height={120} viewBox="0 0 64 64">
        <rect x={0} y={0} width={64} height={64} rx={14} fill="#ffffff" />
        <g transform="translate(32, 32)">
          <rect
            x={-22}
            y={-22}
            width={44}
            height={44}
            rx={3}
            ry={3}
            fill="#ffffff"
            stroke="#158A57"
            strokeWidth={4}
            transform="rotate(45)"
          />
          <polygon points="-31,0 -22,-9 22,-9 31,0 22,9 -22,9" fill="#158A57" />
        </g>
      </svg>
      <div
        style={{
          display: "flex",
          position: "absolute",
          fontSize: 24,
          fontWeight: 700,
          color: "#ffffff",
          letterSpacing: "1px",
        }}
      >
        PMCT
      </div>
    </div>
  );
}

const COPY = {
  vi: {
    eyebrow: "PHARMACOUNTRY ENTERPRISE SOLUTIONS",
    tagline:
      "Phần mềm cho doanh nghiệp sản xuất, phân phối, vận hành chuỗi bán lẻ và trang trại trong các ngành quản lý chặt chẽ.",
  },
  en: {
    eyebrow: "PHARMACOUNTRY ENTERPRISE SOLUTIONS",
    tagline:
      "Software for businesses in regulated manufacturing, distribution, retail chain operations, and farming.",
  },
} as const;

export default async function Image({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const copy = locale === "vi" ? COPY.vi : COPY.en;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px 90px",
          backgroundColor: "#0f172a",
          backgroundImage:
            "radial-gradient(circle at 12% 15%, rgba(61,187,137,0.30) 0%, rgba(61,187,137,0) 42%), radial-gradient(circle at 92% 85%, rgba(21,138,87,0.28) 0%, rgba(21,138,87,0) 45%)",
          fontFamily: "Arial, Helvetica, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <LogoMark />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div
              style={{
                display: "flex",
                fontSize: 72,
                fontWeight: 700,
                color: "#ffffff",
                letterSpacing: "-1px",
              }}
            >
              PharmaCountry
            </div>
            <div
              style={{
                display: "flex",
                fontSize: 34,
                fontWeight: 600,
                color: "#3DBB89",
                marginTop: 2,
              }}
            >
              Enterprise Solutions
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            marginTop: 56,
            fontSize: 30,
            lineHeight: 1.45,
            color: "#cbd5e1",
            maxWidth: 980,
          }}
        >
          {copy.tagline}
        </div>

        <div
          style={{
            display: "flex",
            marginTop: 56,
            fontSize: 24,
            fontWeight: 600,
            color: "#64748b",
            letterSpacing: "2px",
          }}
        >
          PHARMACOUNTRY.VN
        </div>
      </div>
    ),
    { ...size }
  );
}
