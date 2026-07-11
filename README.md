# quentinfears.com — repositioned site

![Stack: HTML · CSS · JS](https://img.shields.io/badge/stack-HTML%20%C2%B7%20CSS%20%C2%B7%20JS-0b0b0c?style=flat-square&labelColor=0b0b0c)
![Build: none](https://img.shields.io/badge/build-none-f72c9c?style=flat-square&labelColor=0b0b0c)
![Deploy: any static host](https://img.shields.io/badge/deploy-any%20static%20host-0b0b0c?style=flat-square&labelColor=0b0b0c)
![Dependencies: zero](https://img.shields.io/badge/dependencies-0-0b0b0c?style=flat-square&labelColor=0b0b0c)

A rebuild of Quentin Fears' website that keeps the **visual style** of the current
site (dark, editorial, image-forward, premium) while repositioning the **content**
from "celebrity & personal stylist" to **fashion creative leader, visual strategist,
speaker, and host**, per the repositioning brief.

![The repositioned quentinfears.com home page — dark editorial hero: display-serif wordmark, positioning line, portrait, and three proof points](docs/preview.jpg)

> The home page as it renders today. Photography and video are placed through a simple
> image-slot system (see [ASSETS.md](ASSETS.md)); any slot still without a file falls
> back to a labeled placeholder, so the layout stays intact at every stage of asset
> collection.

See **[PROPOSAL.md](PROPOSAL.md)** for the proposal (what stays, what changes, and why)
and **[ASSETS.md](ASSETS.md)** for the image/media manifest.

## Structure

```
index.html      Home — positioning, proof points, teasers, testimonials, CTA
work.html       Work — case studies + selected styling archive
ideas.html      Ideas — philosophy, TIME feature, closet-cleanse thesis, signature formats
speak.html      Speak & Host — talk topics, reel, media credits, booking
about.html      About — full arc to present, the story-first method, timeline
contact.html    Contact — one form, four inquiry types
assets/css/style.css   Design system (self-contained, no external fonts)
assets/js/main.js      Mobile nav, scroll reveal, form fallback, footer year
assets/img/            Drop real photos here (see ASSETS.md)
```

## Design

- **Style continuity:** near-black canvas, warm off-white ink, high-contrast fashion
  serif for display (Didone/Bodoni register via a resilient system stack), clean
  grotesque sans for UI, all-caps letter-spaced labels, and a restrained champagne accent.
- **Self-contained:** no external fonts, scripts, or CDNs — works offline and inside a
  strict CSP. Fonts degrade gracefully (Didot → Bodoni → Playfair → Georgia).
- **Responsive & accessible:** mobile nav, skip link, reduced-motion support, keyboard-
  friendly forms, semantic landmarks.
- **Image slots:** each `<img>` reveals a labeled placeholder until the real file is
  added, so the site looks designed at every stage of asset collection.

## Preview locally

It's static HTML — open `index.html` directly, or serve the folder:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Validate

A dependency-free consistency check keeps the pages, links, and galleries in sync:

```bash
python3 tools/validate_site.py
```

It verifies internal links and anchors resolve, gallery keys match their JSON, and no
template boilerplate slipped in. It does not fail on unfilled image slots (the
placeholder system handles those) and reports them as `INFO`. CI runs the same check
on every push and pull request (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Deploy

Any static host works: GitHub Pages, Netlify, Vercel, Cloudflare Pages, or Wix Studio.
No build step required.

This repo is wired for **GitHub Pages**: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
publishes the site on every push to `main` (currently at `https://obartra.github.io/quentin/`,
behind a lightweight access gate while it's pre-launch).

## Before launch — checklist

- [ ] Add real images to `assets/img/` (see `ASSETS.md`), especially the leader-mode hero portrait.
- [ ] Embed the two-minute speaking reel on `speak.html`.
- [ ] Replace testimonial quotes with verbatim wording from the existing site.
- [ ] Have Quentin's manager/comms review the Walmart bio language.
- [ ] Set the contact form endpoint and update the contact email.
- [x] Set the real domain in the `og:` / canonical / sitemap tags (`https://quentinfears.com`). If the
      site launches on a different domain, find-and-replace `quentinfears.com` across the HTML,
      `robots.txt`, and `sitemap.xml`.
- [ ] **Flip indexing on at launch.** While the password gate is up the pages are
      `robots: noindex, nofollow` (a private preview should not be indexed). When the gate
      comes off, restore `index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`
      on all six pages (the exact string is in an HTML comment next to each `robots` tag).
- [ ] Submit `sitemap.xml` in Google Search Console and Bing Webmaster Tools after launch.
- [ ] Optional: replace the generated `assets/img/og-cover.jpg` share card and the JSON-LD
      `Person.image` with a real photo of Quentin once the leader-mode portrait exists.

## SEO

Technical SEO is built in and self-contained (no external calls):

- **Per page:** unique `<title>` + meta description, canonical URL, Open Graph + Twitter Card
  tags, and a `robots` directive. While the site is behind the password gate this is
  `noindex, nofollow`; flip it to `index, follow, max-image-preview:large` at launch.
- **Structured data:** JSON-LD on every page — a shared `Person` entity (`#person`) plus
  `WebSite`, `ProfilePage` (about), `ContactPage` (contact), `CollectionPage` (work), and
  `BreadcrumbList` on subpages.
- **Social share card:** `assets/img/og-cover.jpg` (1200×630), generated from the brand palette.
- **Icons:** `favicon.svg` (scalable), `favicon.ico`, `apple-touch-icon.png`, and PWA icons via
  `site.webmanifest`.
- **Crawl:** `robots.txt` points at `sitemap.xml`, which lists all six pages.

Everything is keyed to `https://quentinfears.com`; change that string if the domain differs.
