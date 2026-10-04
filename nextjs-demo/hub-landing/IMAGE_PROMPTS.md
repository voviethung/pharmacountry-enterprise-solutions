# PharmaCountry Enterprise Solutions — Hub Image Prompts

No image-generation tool exists in this environment, so real photography/illustration could not
be produced directly. This file is the deliverable in its place: ready-to-paste prompts for a
tool like Midjourney, DALL·E, or Stable Diffusion. Once you generate images from these prompts,
send the resulting files back for a follow-up pass to embed them (replacing the CSS-only
placeholder blocks currently marked with `{/* TODO: replace with real ... image ... */}` in the
code — see `app/[locale]/page.tsx` for the homepage hero and `app/[locale]/about/page.tsx` for
the About-page image).

Brand palette to reference in any prompt: primary green gradient `#3DBB89` → `#158A57` →
`#0A4A2D`, accent `#1FA76B`. Avoid generic "stock-photo businesspeople shaking hands" clichés,
and avoid anything with obviously wrong/garbled text, extra fingers, or other uncanny AI-image
tells — if the tool supports a "no text" or "no logos" negative prompt, use it (any real
wordmark/logo will be added separately in code, not baked into the photo).

---

## 1. Homepage hero banner

**Placement:** Full-width dark hero section background, homepage, behind the headline text (text
overlays on the left/top of the image, so keep the right two-thirds visually calmer).

**Aspect ratio:** 16:9 (or wider, e.g. 21:9, since it spans the full page width behind text).

**Prompt:**
> A modern, dimly lit enterprise software control room at night, wide-angle view: large curved
> monitors displaying abstract dashboards, data charts, and manufacturing-line schematics in
> shades of emerald and teal green (#158A57, #3DBB89), reflecting softly off a dark glass desk.
> In the background, softly blurred glimpses of a pharmaceutical manufacturing line and
> laboratory glassware suggest the software connects to real industrial operations, without
> being the main subject. Moody, cinematic lighting, shallow depth of field, high-end tech/
> editorial photography style (think a modern enterprise SaaS company's website hero, not a
> generic stock photo). No visible logos, no readable text on any screen, no people in frame.
> Photorealistic, 16:9, dark background suitable for white text overlay on the left side.
> --ar 16:9

**Negative/avoid:** stock-photo businesspeople shaking hands, generic laptop-on-desk cliché,
visible brand logos or legible on-screen text, cartoonish or overly saturated colors, distorted
hands/faces.

---

## 2. About-page image

**Placement:** A rounded image block near the top of the About page, above the company copy.

**Aspect ratio:** 4:3 or 1:1 (fits a contained card, not full-bleed).

**Prompt:**
> A clean, bright, modern software engineering team workspace: a small group of professionals
> (diverse in age and gender, business-casual attire) collaborating around a large monitor
> showing abstract green-toned dashboard UI mockups, in a well-lit open-plan office with plants
> and warm wood accents. Soft natural daylight from large windows, shallow depth of field on the
> monitor and hands, faces slightly turned away or out of sharp focus to keep it generic and
> professional rather than depicting specific real individuals. Warm, optimistic, trustworthy
> corporate photography style with a subtle emerald-green (#158A57) color grade in the shadows.
> No visible logos, no legible text on any screen. Photorealistic, 4:3.
> --ar 4:3

**Negative/avoid:** stiff posed stock-photo smiles, obviously fake diversity casting, visible
brand logos, legible on-screen text, uncanny/distorted faces or hands.

---

## 3. (Optional) Multi-industry breadth illustration

**Placement:** Could accompany the "How our platform is built" section on the homepage, or a
future expanded Solutions overview page — illustrating the platform's breadth across pharma,
livestock, aquaculture, cosmetics, etc. Optional; only use if a natural section needs a visual
anchor.

**Aspect ratio:** 3:2.

**Prompt:**
> A modern, flat-design editorial illustration (not photorealistic) representing interconnected
> industries: subtle line-art icons of a pharmaceutical tablet/capsule, a fish, a cow/livestock
> silhouette, a cosmetics bottle, and a medical device, all connected by thin glowing emerald-
> green (#158A57) network lines converging into a single abstract hexagonal "hub" node in the
> center. Minimal, clean background in white or very light grey, generous negative space,
> corporate/editorial infographic style similar to a modern SaaS platform's "how it works"
> section. No text, no logos.
> --ar 3:2

**Negative/avoid:** cluttered composition, more than 5-6 distinct icon elements, photorealistic
rendering (this one should read as a clean vector-style illustration, not a photo), clip-art
look.

---

## Where these plug in (code references)

- Homepage hero: `app/[locale]/page.tsx`, the `<section className="relative overflow-hidden ...">`
  block — currently a CSS gradient placeholder tinted with the real brand green.
- About page: `app/[locale]/about/page.tsx`, the rounded gradient block near the top of the page.
- Multi-industry illustration (optional): would go in the "How our platform is built" section of
  `app/[locale]/page.tsx` if added later.
