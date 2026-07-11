# CLAUDE.md

Working notes for this repo. Human-facing overview is in [README.md](README.md); the
repositioning rationale is in [PROPOSAL.md](PROPOSAL.md); the image/media manifest is
in [ASSETS.md](ASSETS.md).

## What this is

A static marketing site for Quentin Fears that keeps a dark, editorial visual style
while repositioning him from "celebrity & personal stylist" to fashion creative
leader, visual strategist, speaker, and host. Six hand-authored HTML pages
(`index`, `work`, `ideas`, `speak`, `about`, `contact`) plus a shared CSS/JS layer.
No framework, no build step, no package manager.

## Stack & conventions

- Plain HTML + CSS + JS, dependency-free and self-contained (no external fonts,
  scripts, or CDNs) so it works offline and under a strict CSP. Do not add a build
  step, framework, or npm dependency without a strong reason.
- Design system lives in `assets/css/style.css`. Behavior lives in
  `assets/js/main.js` (mobile nav, scroll-reveal, gallery lightbox, contact-form
  mailto fallback, footer year) and `assets/js/gate.js` (the access gate). Keep it
  progressive: pages must stay legible with JavaScript disabled.
- House voice uses em dashes and all-caps letter-spaced labels. Match the existing
  editorial tone; do not strip em dashes in this repo.
- Keep metadata honest and present-day (page titles, `og:` tags; the footer year is
  set dynamically). No Wix boilerplate ("Mysite", "Cordan", lorem ipsum) — CI fails
  on it.

## Content guardrails (from the brief)

- This is Quentin's **personal** site; it does not speak for any employer. Walmart is
  named only as a biographical fact. No Walmart imagery, internal work, confidential
  detail, or implied endorsement; keep case-study specifics generic ("a Fortune 1
  retailer"). Do not present him as an official representative in metadata or
  structured data: machine-readable employer claims (`worksFor`, an employer name
  inside `<head>`) are out, and `tools/seo_check.py` fails if a flagged company name
  appears in any page `<head>`. A comms review of that language is wanted before launch.
- "Don't just wear clothes, wear confidence" survives only as a secondary tagline,
  not the headline.

## Images: the slot system

Every photo is a real `<img src="assets/img/…">`. If the file is missing, the tag
falls back to a labeled placeholder (`onerror` + CSS), so the layout never breaks.
When you add or rename a slot, update both the page and [ASSETS.md](ASSETS.md) so the
manifest stays in sync. Bulk-download originals with
`python3 tools/fetch_site_images.py` (pushes to the `site-images` branch by default);
the large `assets/img/site-dump/` output is gitignored.

Work-page galleries are data-driven: `data-gallery="key"` buttons open the lightbox
using the `<script id="gallery-data">` JSON in `work.html`. Keep the button keys and
the JSON keys in sync (CI checks this).

## SEO layer

The site ships a complete, self-contained technical-SEO layer. Any change that touches
a page, an asset, the domain, or the page set must keep it intact.

- **Per page:** unique `<title>` + meta description, `<link rel="canonical">`, the full
  Open Graph + Twitter Card set, a `robots` directive, `theme-color`, and favicon /
  apple-touch-icon / manifest links.
- **Structured data:** a JSON-LD `<script type="application/ld+json">` block per page,
  all keyed to one shared Person entity `@id` `https://quentinfears.com/#person`
  (`WebSite` + `Person` on home; `ProfilePage`, `ContactPage`, `CollectionPage`, and
  `BreadcrumbList` on the others).
- **Assets & crawl:** a branded `assets/img/og-cover.jpg` (1200×630), `favicon.svg` /
  `favicon.ico` / `apple-touch-icon.png` / PWA icons via `site.webmanifest`, and
  `robots.txt` pointing at `sitemap.xml` (which lists all six pages).

Everything is keyed to `https://quentinfears.com` as the single source of truth.

### When you add a new page

1. Copy the entire `<head>` from an existing page and adjust the per-page values.
2. Give it a unique `<title>` and `<meta name="description">` (aim: title ~60 chars,
   description ~160; longer only warns).
3. Set `<link rel="canonical">` and `og:url` to `https://quentinfears.com/<file>.html`.
4. Keep the full tag set: `og:*`, `twitter:card` (`summary_large_image`) + image,
   `robots`, `theme-color`, and the favicon / apple-touch-icon / manifest / stylesheet
   `<link>`s.
5. Add a JSON-LD block referencing the shared Person `@id`, plus a `BreadcrumbList`.
6. Add the page's URL to [sitemap.xml](sitemap.xml).
7. Use exactly one `<h1>` and give every `<img>` an `alt`.
8. Run `python3 tools/seo_check.py` and fix anything it reports.

### When the domain changes

`https://quentinfears.com` is the single source of truth. Find-and-replace it across all
`*.html`, `robots.txt`, and `sitemap.xml`, and update `BASE` in
[tools/seo_check.py](tools/seo_check.py). The check confirms consistency. Note the site
is currently *served* from GitHub Pages at `https://obartra.github.io/quentin/`; the
canonical/`og:` URLs intentionally point at the launch domain `quentinfears.com`.

### Private preview vs launch (indexing)

The site sits behind the client-side password gate (`assets/js/gate.js`), so it is a
**private preview**. While the gate is up, every page is `robots: noindex, nofollow`
so search engines do not index a password wall. The exact directive to restore is in an
HTML comment beside each `robots` tag. **At launch:** remove the gate and flip all six
pages back to `index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`,
then submit the sitemap. `tools/seo_check.py` warns if a gated page is left indexable, or
if an ungated page is left `noindex`, so the two stay coupled.

## Keep things in sync

Two dependency-free validators guard the repo; run both before committing, and CI
(`.github/workflows/ci.yml`) runs both on every push and PR:

- `python3 tools/validate_site.py` — internal links and anchors resolve, gallery keys
  match their JSON, and no template junk slipped in. It does not fail on missing
  `assets/img/` files (the slot system handles those) but reports unfilled slots as INFO.
- `python3 tools/seo_check.py` — the SEO invariants: one non-empty `<title>`, a meta
  description, canonical == expected URL, `og:url` match, required `og:*`/`name` meta,
  `og:image` resolves to a real file, favicon/manifest/stylesheet links, one `<h1>`,
  `alt` on every `<img>`, valid JSON-LD keyed to the canonical origin, sitemap
  membership, the gate↔indexing coupling, and no employer name in `<head>`. Site-wide
  it checks `robots.txt` → sitemap, sitemap/page-set sync, and manifest/asset existence.

The README hero (`docs/preview.jpg`) is a rendered screenshot of the home page.
Regenerate it when the hero changes: serve the site, set
`sessionStorage.setItem("qf-access","1")` to pass the gate, screenshot the top of
`index.html`, then re-optimize (JPEG, ~2400px wide).

## Run & deploy

- Preview locally: `python3 -m http.server 8000`, then open http://localhost:8000.
  The site is access-gated via `sessionStorage["qf-access"]`; `gate.js` handles it.
- Deploy: pushing to `main` publishes to GitHub Pages via
  `.github/workflows/deploy.yml`. Live (gated, pre-launch) at
  https://obartra.github.io/quentin/.

## What not to do

- Do not add external fonts, scripts, or CDNs. It breaks the offline / CSP-safe guarantee.
- Do not strip em dashes; they are the house voice here.
- Do not remove or desync canonical, Open Graph, JSON-LD, or sitemap entries when editing pages.
- Do not present Quentin as speaking for an employer in metadata or structured data.
- Do not introduce a build step, or rename/move the crawl files or validators, without
  updating `tools/seo_check.py`, `tools/validate_site.py`, and `.github/workflows/`.
