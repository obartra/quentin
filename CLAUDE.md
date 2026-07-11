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

- Walmart is named only as a biographical fact. No Walmart imagery, internal work,
  confidential detail, or implied endorsement; keep case-study specifics generic
  ("a Fortune 1 retailer"). A comms review of that language is wanted before launch.
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

## Keep things in sync

- Run `python3 tools/validate_site.py` before committing. It verifies internal links
  and anchors resolve, gallery keys match their JSON, and no template junk slipped in.
  It intentionally does not fail on missing `assets/img/` files (the slot system
  handles those) but reports unfilled slots as INFO.
- CI (`.github/workflows/ci.yml`) runs that same validator on every push and PR.
- The README hero (`docs/preview.jpg`) is a rendered screenshot of the home page.
  Regenerate it when the hero changes: serve the site, set
  `sessionStorage.setItem("qf-access","1")` to pass the gate, screenshot the top of
  `index.html`, then re-optimize (JPEG, ~2400px wide).

## Run & deploy

- Preview locally: `python3 -m http.server 8000`, then open http://localhost:8000.
  The site is access-gated via `sessionStorage["qf-access"]`; `gate.js` handles it.
- Deploy: pushing to `main` publishes to GitHub Pages via
  `.github/workflows/deploy.yml`. Live (gated, pre-launch) at
  https://obartra.github.io/quentin/.
