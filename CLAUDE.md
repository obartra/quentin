# CLAUDE.md

Working notes for this repo. Human-facing overview is in [README.md](README.md); the
repositioning rationale is in [PROPOSAL.md](PROPOSAL.md); the image/media manifest is
in [ASSETS.md](ASSETS.md); the build architecture is in
[docs/astro-keystatic-migration.md](docs/astro-keystatic-migration.md).

## What this is

A marketing site for Quentin Fears that keeps a dark, editorial visual style while
repositioning him from "celebrity & personal stylist" to fashion creative leader,
visual strategist, speaker, and host. Six pages (`index`, `work`, `ideas`, `speak`,
`about`, `contact`).

It is built with **Astro**, and all copy lives in editable content files managed by a
**Keystatic** admin, so the site is maintainable with no code. Astro renders the
content into the same markup the site shipped by hand and reuses the same
self-contained CSS/JS, so the output, the SEO layer, the gate, and the galleries are
unchanged. The build is a static export deployed to GitHub Pages.

## Stack & conventions

- **Astro** (static output, `build.format: 'file'` → flat `about.html`, `work.html`,
  …). `npm run build` emits `dist/`; that is what deploys and what the validators
  check.
- **Content is data.** Editable text and image paths live in `content/*.yaml`, one
  singleton per page plus a `galleries` singleton. The schema and the `/keystatic`
  admin are defined in [keystatic.config.ts](keystatic.config.ts). Pages read it at
  build time via `@keystatic/core/reader` (see [src/lib/content.ts](src/lib/content.ts));
  no server or database.
- **The design system and behavior are unchanged and self-contained.** CSS in
  `public/assets/css/style.css`; behavior in `public/assets/js/main.js` (mobile nav,
  scroll-reveal, gallery lightbox, contact-form mailto fallback, footer year) and
  `public/assets/js/gate.js` (the access gate). No external fonts, scripts, or CDNs —
  it must keep working offline and under a strict CSP. Pages stay legible with
  JavaScript disabled. Everything in `public/` ships verbatim into `dist/`.
- **Keep links relative.** Every internal link and asset reference is relative
  (`work.html`, `assets/css/style.css`, `favicon.svg`) so the site works under both
  the GitHub Pages subpath and the apex domain. `base` stays `/`; do not switch to
  root-absolute asset paths.
- **House voice uses em dashes** and all-caps letter-spaced labels. Match the existing
  editorial tone; do not strip em dashes in this repo (content or code).
- Keep metadata honest and present-day. No Wix boilerplate ("Mysite", "Cordan", lorem
  ipsum) — CI fails on it.

## The Keystatic admin

Three build shapes from one project (see the header comment in
[astro.config.mjs](astro.config.mjs)):

- **Local editing:** `npm run dev` → `/keystatic`. Local file storage; editing writes
  the `content/*.yaml` files; commit + push to publish. Free, no server.
- **Public site:** `npm run build` sets `KEYSTATIC_ADMIN=0`, so the Keystatic + React
  integrations and the SSR `/keystatic` routes are skipped. The deployed site is a
  pure static export (GitHub Pages). Keep it that way.
- **Hosted admin:** `npm run build:admin` (`ADMIN_HOST=netlify`,
  `KEYSTATIC_STORAGE=github`) builds the same app with the admin as SSR routes behind
  the Netlify adapter and GitHub storage, so a non-technical editor edits from a
  browser and Save commits to the repo. Storage is env-driven in
  [keystatic.config.ts](keystatic.config.ts). Setup:
  [docs/hosted-admin.md](docs/hosted-admin.md). The adapter belongs to this build
  only; never let it leak into the public `npm run build`.

## Content guardrails (from the brief)

- This is Quentin's **personal** site; it does not speak for any employer. Walmart is
  named only as a biographical fact in body copy. No Walmart imagery, internal work,
  confidential detail, or implied endorsement; keep case-study specifics generic
  ("a Fortune 1 retailer"). Do not present him as an official representative in
  metadata or structured data: machine-readable employer claims (`worksFor`, an
  employer name inside `<head>`) are out. `tools/seo_check.py` fails if a flagged
  company name appears in any page `<head>`, so keep such terms in body content only
  (never in a `seo.*` field, since those render into `<head>`).
- "Don't just wear clothes, wear confidence" survives only as a secondary tagline
  (the footer), not the headline.

## Images: the slot system

Photos are `<img src="assets/img/…">` whose paths are edited as content fields. If a
file is missing, the tag falls back to a labeled placeholder (`onerror` + CSS), so the
layout never breaks. Real files live in `public/assets/img/`. When you add or rename a
slot, update [ASSETS.md](ASSETS.md) so the manifest stays in sync. Bulk-download
originals with `python3 tools/fetch_site_images.py`.

Work-page galleries are data-driven from the `galleries` singleton
(`content/galleries.yaml`). Each set has a `key`; Work cases and archive items
reference a key via their `gallery` field, and `work.astro` emits the
`<script id="gallery-data">` JSON the lightbox reads. Keep the referenced keys and the
gallery keys in sync (CI checks this).

## SEO layer

The full technical-SEO layer is generated in code, not authored per page, so it stays
consistent. Editable per page: `seo.title`, `seo.description`, `seo.ogTitle`,
`seo.ogDescription`, `seo.ogType`. Generated by
[src/layouts/BaseLayout.astro](src/layouts/BaseLayout.astro) and
[src/lib/jsonld.ts](src/lib/jsonld.ts):

- **Per page:** canonical + `og:url` (from the page path), the full Open Graph +
  Twitter Card set, `robots`, `theme-color`, and favicon / apple-touch-icon / manifest
  / stylesheet links.
- **Structured data:** a JSON-LD block per page, all keyed to one shared Person entity
  `@id` `https://quentinfears.com/#person` (`WebSite` + `Person` + `WebPage` on home;
  `ProfilePage`, `ContactPage`, `CollectionPage`, or `WebPage`, plus a `BreadcrumbList`,
  on the others).
- **Assets & crawl:** `public/assets/img/og-cover.jpg` (1200×630), favicons / PWA
  icons via `public/site.webmanifest`, and `public/robots.txt` → `public/sitemap.xml`.

Everything is keyed to `https://quentinfears.com` as the single source of truth.

### When you add a new page

1. Add a singleton to `keystatic.config.ts` (reuse the `seo()` helper) and a
   `content/<page>.yaml` with its copy.
2. Add `src/pages/<page>.astro`: read the singleton and render its sections, wrapped
   in `BaseLayout` with `pagePath="<page>.html"`, the `seo.*` props, a `navCurrent`,
   and a `jsonLd` graph (use `personMinimal` + `breadcrumb` from `src/lib/jsonld.ts`).
   `BaseLayout` supplies the rest of the `<head>` — do not hand-write it.
3. Use exactly one `<h1>` and give every `<img>` an `alt`.
4. Add the page's URL to [public/sitemap.xml](public/sitemap.xml).
5. Run `npm run build && npm run validate` and fix anything reported.

### When the domain changes

`https://quentinfears.com` is the single source of truth. Update `SITE_ORIGIN` in
[src/lib/content.ts](src/lib/content.ts), `BASE` in
[tools/seo_check.py](tools/seo_check.py), and find-and-replace the domain in
`public/robots.txt` and `public/sitemap.xml`. The site is *served* pre-launch from
GitHub Pages at `https://obartra.github.io/quentin/`; the canonical/`og:` URLs
intentionally point at the launch domain `quentinfears.com`.

### Private preview vs launch (indexing)

The site sits behind the client-side password gate (`public/assets/js/gate.js`), so it
is a private preview. While the gate is up, `BaseLayout` emits `robots: noindex,
nofollow` on every page (the exact launch directive is in the comment beside the
`robots` tag). **At launch:** remove the gate and flip the `robots` content in
`BaseLayout.astro` back to
`index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`, then
submit the sitemap. `tools/seo_check.py` warns if a gated page is left indexable, or an
ungated page is left `noindex`, so the two stay coupled.

## Keep things in sync

Two dependency-free validators guard the repo; they read the build output. Run
`npm run build` first (or `npm run check`, which does both), and CI
(`.github/workflows/ci.yml`) builds then runs both on every push and PR:

- `python3 tools/validate_site.py [dir]` — internal links and anchors resolve, gallery
  keys match their JSON, no template junk. Reports unfilled `assets/img/` slots as INFO.
- `python3 tools/seo_check.py [dir]` — the SEO invariants (one `<title>`, meta
  description, canonical, required `og:*`/`name` meta, `og:image` resolves, favicon /
  manifest / stylesheet links, one `<h1>`, `alt` on every `<img>`, valid JSON-LD keyed
  to the canonical origin, sitemap membership, gate ↔ indexing coupling, and no employer
  name in `<head>`), plus `robots.txt` → sitemap and manifest/asset existence.

Both default to `dist/` when it exists (else the repo root). CI passes `dist`
explicitly.

The README hero (`docs/preview.jpg`) is a rendered screenshot of the home page.
Regenerate it when the hero changes: serve the build, set
`sessionStorage.setItem("qf-access","1")` to pass the gate, screenshot the top of the
home page, then re-optimize (JPEG, ~2400px wide).

## Run & deploy

- Preview locally: `npm run dev` (site at http://localhost:4321, admin at
  `/keystatic`). Or `npm run build && npm run preview` for the production build. The
  site is access-gated via `sessionStorage["qf-access"]`; `gate.js` handles it.
- Deploy: pushing to `main` builds and publishes `dist/` to GitHub Pages via
  `.github/workflows/deploy.yml`. Live (gated, pre-launch) at
  https://obartra.github.io/quentin/.

## What not to do

- Do not add external fonts, scripts, or CDNs to the site. It breaks the offline /
  CSP-safe guarantee. (Astro/Keystatic build-time dependencies are fine; they do not
  ship to the browser.)
- Do not switch internal links/assets to root-absolute paths; keep them relative so
  the subpath and apex domain both work.
- Do not strip em dashes; they are the house voice here.
- Do not hand-write or desync the `<head>`, JSON-LD, or sitemap when adding pages; the
  head is generated by `BaseLayout` and keyed to the canonical origin.
- Do not present Quentin as speaking for an employer in metadata or structured data,
  or put an employer name in any `seo.*` field.
- Keep the **public** build (`npm run build`) static and adapter-free — that is what
  ships to GitHub Pages. The Netlify adapter is intentional but belongs only to the
  separate hosted-admin build (`npm run build:admin`); do not merge the two.
- Rename/move the crawl files or validators only alongside updates to
  `tools/seo_check.py`, `tools/validate_site.py`, and `.github/workflows/`.
