# CLAUDE.md

## Project

`quentinfears.com` is a static personal site for **Quentin Fears** (fashion creative
leader, visual strategist, speaker, and host). It is plain HTML/CSS/JS with **no build
step** and **no external fonts, scripts, or CDNs**, so it works offline and under a
strict Content Security Policy. It deploys to any static host (GitHub Pages, Netlify,
Vercel, Cloudflare Pages, Wix Studio).

See [README.md](README.md) for structure, [PROPOSAL.md](PROPOSAL.md) for positioning,
and [ASSETS.md](ASSETS.md) for the image manifest.

### Positioning guard (read before touching copy or metadata)

This is Quentin's **personal** site. It does **not** speak for any employer. Do not
present him as an official representative or spokesperson of a company (for example,
Walmart) in metadata, structured data, or new marketing copy. First-person mentions of
his own experience in the visible body copy are his to make; machine-readable employer
claims (`worksFor`, employer schema, an employer name inside `<head>`) are not. The SEO
check enforces this by failing if a flagged company name appears in any page `<head>`.

## Structure

```
index.html work.html ideas.html speak.html about.html contact.html   the six pages
assets/css/style.css   design system (self-contained)
assets/js/main.js      nav, scroll reveal, form fallback, footer year
assets/img/            photos (see ASSETS.md) + generated SEO/social assets
favicon.svg favicon.ico apple-touch-icon.png site.webmanifest        icons + PWA manifest
robots.txt sitemap.xml                                               crawl files
tools/seo_check.py     SEO invariant checker (stdlib only)
tools/fetch_site_images.py   crawl/download images from the live site
.github/workflows/seo.yml    CI that runs the SEO check
```

## Golden rule: never let the SEO layer regress

The site ships a complete technical-SEO layer (per-page canonical, Open Graph, Twitter
Card, robots meta, favicon/manifest, JSON-LD structured data, sitemap, robots.txt).
**Any change that touches a page, an asset, the domain, or the page set must keep it
intact.** Before committing, run:

```bash
python3 tools/seo_check.py
```

CI ([.github/workflows/seo.yml](.github/workflows/seo.yml)) runs the same check on every
push and pull request and fails the build if an invariant breaks. Keep it green.

### When you add a new page

1. Copy the entire `<head>` from an existing page and adjust the per-page values.
2. Give it a unique `<title>` and `<meta name="description">` (aim: title under ~60
   chars, description under ~160; longer only warns).
3. Set `<link rel="canonical">` and `og:url` to `https://quentinfears.com/<file>.html`.
4. Keep the full tag set: `og:title/description/type/image/url/site_name/locale`,
   `twitter:card` (`summary_large_image`) + image, `robots`, `theme-color`, and the
   favicon / apple-touch-icon / manifest / stylesheet `<link>`s.
5. Add a JSON-LD `<script type="application/ld+json">` block that references the shared
   Person entity `@id` `https://quentinfears.com/#person`, plus a `BreadcrumbList`.
6. Add the page's URL to [sitemap.xml](sitemap.xml).
7. Use exactly one `<h1>` and give every `<img>` an `alt`.
8. Run `python3 tools/seo_check.py` and fix anything it reports.

### When you change a page

Keep `<title>`, description, canonical, `og:url`, JSON-LD `name`/`url`, and the sitemap
entry in sync. Editing the visible copy is fine; do not desync the metadata from it.

### When the domain changes

`https://quentinfears.com` is the single source of truth. Find-and-replace it across all
`*.html`, `robots.txt`, and `sitemap.xml`, and update `BASE` in
[tools/seo_check.py](tools/seo_check.py). The check will confirm consistency.

### Private preview vs launch (indexing)

The site currently sits behind the client-side password gate (`assets/js/gate.js`), so it
is a **private preview**. While the gate is up, every page is `robots: noindex, nofollow`
so search engines do not index a password wall. The exact directive to restore is in an
HTML comment beside each `robots` tag. **At launch:** remove the gate and flip all six
pages back to `index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`,
then submit the sitemap. The checker warns if a gated page is left indexable, or if an
ungated page is left `noindex`, so the two stay coupled.

### What tools/seo_check.py enforces

Per page: exactly one non-empty `<title>`; a meta description; canonical present and
equal to the expected URL; `og:url` matching canonical; all required `og:*` and
`name` meta present; `og:image` absolute and pointing at a file that exists; favicon /
manifest / stylesheet links present; exactly one `<h1>`; `alt` on every `<img>`; at
least one JSON-LD block, each valid JSON and keyed to the canonical origin; the page is
listed in the sitemap; and no flagged employer name in `<head>`. Site-wide: `robots.txt`
points at the sitemap, the sitemap lists exactly the repo's pages, `site.webmanifest` is
valid JSON with icons that exist, and every referenced asset is present.

## Commands

| Command                          | Description                                  |
| -------------------------------- | -------------------------------------------- |
| `python3 tools/seo_check.py`     | Validate all SEO invariants (run before commit) |
| `python3 -m http.server 8000`    | Preview the site at `http://localhost:8000`  |
| `python3 tools/fetch_site_images.py` | Crawl/download images from the live site |

## What not to do

- Do not add external fonts, scripts, or CDNs. It breaks the offline / CSP-safe guarantee.
- Do not remove or desync canonical, Open Graph, JSON-LD, or sitemap entries when editing pages.
- Do not present Quentin as speaking for an employer in metadata or structured data.
- Do not introduce a build step or rename/move the crawl files without updating
  `tools/seo_check.py` and `.github/workflows/seo.yml`.
- Do not commit real photos to `assets/img/` that you were not given rights to use.
