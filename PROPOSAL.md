# Website Repositioning — Proposal

**Project:** Rebuild of quentinfears.com
**Goal:** Keep the visual *style* of the current site (dark, editorial, image-forward, premium) while changing the *content and architecture* to reposition Quentin from "celebrity & personal stylist" to **fashion creative leader, visual strategist, speaker, and host.**

This document is the "propose" step. The build that ships alongside it is the "create" step.

---

## 1. What stays the same (style continuity)

The current site's strengths are its aesthetic register: black background, large imagery, high-contrast fashion typography, confident all-caps treatment, and the line *"Don't just wear clothes, wear confidence."* The rebuild keeps that DNA so it still feels like Quentin:

- **Dark editorial base** — near-black canvas, warm off-white ink, generous negative space.
- **High-contrast fashion serif** for display headlines (Didone / Bodoni register, the "Vogue" feel), paired with a clean grotesque sans for UI and body.
- **All-caps, letter-spaced labels and navigation** — carried over from the current header treatment.
- **Image-led layout** — full-bleed hero, editorial grids, portrait-forward.
- **"Wear confidence"** survives as a secondary consumer-facing line.

## 2. What changes (content & positioning)

| Current site | Repositioned site |
|---|---|
| Headline: "HOST \| CELEBRITY STYLIST" | "Fashion creative leader, visual strategist, speaker & host" |
| 11 nav items split by deliverable + gender | 5 sections: Work · Ideas · Speak · About · Contact |
| Services = Commercial / Red Carpet / Personal Styling | Creative direction, visual strategy, speaking, hosting, (optional) personal styling |
| Galleries of finished looks | Case studies: objective → story → decisions → constraints → outcome |
| Bio ends ~2021 | Bio extends to present: enterprise fashion leadership at Walmart |
| TV Correspondent = résumé of past gigs | Speak & Host = bookable service with topics + reel + CTA |
| TIME feature as static screenshots | Ideas section — the philosophy, made quotable |
| Footer "© 2020 … Celebrity Stylist … LA" | Correct, present-day, location-neutral footer |
| Wix placeholder text, "Cordan", "Mysite" | Clean, correct metadata throughout |

## 3. Information architecture

1. **Home** — who he is now, one philosophy line, three proof points (enterprise leadership · TIME/Glamour voice · a decade of execution), and three clear paths: *hire · book to speak · follow.*
2. **Work** — 3–5 case studies written as narratives; the celebrity / editorial / commercial galleries live beneath as a single **Selected styling archive**, explicitly framed as *proof of execution*, not the service menu. Gender/format splits removed.
3. **Ideas** — the TIME theme (dress, identity, race, perception) given real treatment with the verbatim quote; the *closet-cleanse-as-renewal* thesis; short notes; the signature content formats.
4. **Speak & Host** — reframed from "TV Correspondent" into a bookable service: six talk topics, formats, a two-minute reel slot (Hilfiger / Sheen Talk / BNC), media credits, and a booking CTA.
5. **About** — the full arc ending at the present: actor's training → Glitter (Nikki Fowler) → Ladygunn creative team → Sheen fashion editor & *The Journey* host → celebrity styling, TIME & Glamour → enterprise fashion leadership. The acting-derived method ("what story do the clothes tell?") is the narrative spine.
6. **Contact / Book** — one form, four distinct inquiry types: corporate, speaking, media, personal styling.

## 4. Handling the Walmart question

Named as a biographical fact — *"Currently leads visual merchandising and styling initiatives in enterprise fashion at Walmart"* — with case-study detail kept generic ("a Fortune 1 retailer," "national campaign," "cross-functional teams") and **no** Walmart imagery, internal work, or implied endorsement. One review of the bio language by his manager/comms partner is recommended before launch.

## 5. Reusing existing assets

Nothing is thrown away — it is **recut**:

- Celebrity roster (Macy Gray, Skai Jackson, Norman Reedus, Keesha Sharp, EJ Johnson, Garcelle Beauvais) → the styling archive as *proof of taste*.
- TIME + Glamour features → the Ideas section and Home proof strip.
- Editorial credits (Glitter, Ladygunn, Sheen) → the About arc and a Work case study.
- Media footage (Tommy Hilfiger, *The Journey* / Sheen Talk Live, Black News Channel) → the Speak reel and credits.
- Testimonials with leadership language (Santana Dempsey, Brian S., the Thumbtack "mentor role" / "language of how to dress" review) → recut as evidence of collaboration and leadership.
- "Don't just wear clothes, wear confidence" → secondary tagline.

Because the image binaries live on the current Wix CDN, this build ships a documented **image-slot system** (`ASSETS.md`): every slot has a filename and a caption describing exactly which existing asset belongs there. Drop the files into `assets/img/` and they replace the tasteful labeled placeholders automatically. New portraits of Quentin *in leader mode* (speaking, directing, on set) are the one net-new asset recommended.

## 6. Build & tech

Static, dependency-free HTML/CSS/JS — hostable on GitHub Pages, Netlify, Vercel, or Wix Studio. Self-contained (no external fonts or scripts required), responsive, and accessible. See `README.md` for structure and local preview.

## 7. Immediate craft fixes baked in

Correct copyright (2026), no placeholder text, no "Mysite" metadata, consistent location story, no stray "Log In" link, "James Corden" spelled correctly, and honest, present-day meta titles/descriptions on every page.
