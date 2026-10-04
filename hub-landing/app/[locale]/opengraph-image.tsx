import { ImageResponse } from "next/og";

// Next.js file-convention OG image — automatically applies to every page under app/[locale]/
// (home, about, contact, solutions, solutions/[packCode]) unless a more specific route defines
// its own opengraph-image file. Generated from code (real brand gradient/colors, same diamond
// mark shape as components/PharmaCountryLogo.tsx) rather than a static asset, so there's nothing
// to keep in sync by hand — one file, locale-aware, always matches the live brand.

export const alt = "PharmaCountry Enterprise Solutions";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

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
          <div
            style={{
              display: "flex",
              width: 120,
              height: 120,
              alignItems: "center",
              justifyContent: "center",
              marginRight: 36,
            }}
          >
            <div
              style={{
                display: "flex",
                width: 84,
                height: 84,
                transform: "rotate(45deg)",
                background:
                  "linear-gradient(135deg, #3DBB89 0%, #158A57 45%, #0A4A2D 100%)",
                borderRadius: 14,
                border: "3px solid #1FA76B",
              }}
            />
          </div>
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
