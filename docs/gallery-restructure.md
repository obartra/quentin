# Portfolio gallery restructure: categories, shoots, and what was recoverable

Date: 2026-07-12. Companion note to the gallery data-model change in
`content/galleries.yaml`, `keystatic.config.ts`, `src/pages/work.astro`,
`public/assets/js/main.js`, and `public/assets/css/style.css`.

## The cause of the issue

The old Wix site organized the portfolio as **category pages** (`/celebrity`,
`/celebrity-men`, `/editorial`, `/editorial-men`, `/commercial`), each a gallery of
**photo shoots**, each shoot with its own image set. The 2026 migration flattened
this twice:

1. **Categories were merged.** The rework commit (`e11c0b0`) pooled the downloaded
   site images into four flat sets (`editorial`, `menswear`, `celebrity`,
   `commercial`). Celebrity men and Celebrity women were combined into one
   `celebrity` set, and tiles were pointed at whichever set looked closest, not at
   the old site's category for that tile.
2. **Shoot grouping was dropped.** Each set was a single flat image list, so a tile
   like "Norman Reedus" opened a mixed slideshow of every image in the set, and
   prev/next walked into unrelated shoots.

## What changed

- **Data model** (`content/galleries.yaml`, schema in `keystatic.config.ts`):
  `sets` are now categories `{ key, title, shoots }`; each shoot is
  `{ slug, title, images: [{ src, cap }] }`. The first image of a shoot is its
  thumbnail. Work-page cases reference a category (`gallery`); archive tiles also
  carry a `shoot` slug and deep-link to that shoot.
- **Category assignments** were restored from the pre-rework `work.html` in git
  history, which preserved each tile's old-site link:
  `archive-01` (Menswear styling) and `archive-05` (Norman Reedus) →
  `/celebrity-men`; `archive-02` (Glamour) and `archive-07` (Event dressing) →
  `/celebrity`; `archive-03` / `archive-08` → `/editorial`; `archive-04` →
  `/editorial-men`; `archive-06` → `/commercial`. The TIME case tile linked the old
  home page, not a gallery, so it no longer opens one.
- **Shoot grouping** within each category was reconstructed by visual audit (same
  model, wardrobe, location, session) because no per-image record survived (see
  below). Duplicate frames were removed: `archive-01/03/05/06/07`,
  `work-enterprise`, and `work-editorial` are crops of frames already in
  `assets/img/gallery/`; only `work-celebrity.jpg` is a distinct frame and joined
  its shoot's set.
- **Lightbox** (`main.js`): two levels. A category opens a grid of shoot thumbnails
  (title + photo count); a shoot opens its own image list, and prev/next wrap
  **within that shoot only**. Back returns to the category grid with the
  just-viewed shoot focused. Nav arrows hide for single-image shoots. Esc closes.
- Gallery image filenames keep their historical prefixes (`g-celebrity-5.jpg` now
  sits in `celebrity-men`); the YAML is the source of truth, so files were not
  renamed.

## Original-site content that could not be recovered

The authoritative old-site image dump (88 images plus a `manifest.json` mapping
each file to the old page it appeared on, on the `site-images` branch) **no longer
exists**: the branch was deleted from the remote. The live Wix site and the Wayback
Machine were both unreachable from the sandbox (network policy denies
`www.quentinfears.com` and `web.archive.org`), and the Instagram dump
(2024 onward) has no overlap with the old portfolio, so:

- **Missing shoot images could not be restored.** Several shoots survive as a
  single frame (Norman Reedus, Event dressing, Print & commercial, Evening wear,
  Studio lookbook) although the old site very likely showed more.
- **Per-image category records are gone** for the 32 pooled gallery images, so
  shoot grouping and the split of the pooled images between Celebrity men and
  Celebrity women rest on visual identification plus the tile mapping recovered
  from git history.
- **Old shoot titles are unknown** beyond the eight tile captions; the two menswear
  shoots ("In the studio", "On location") carry descriptive stand-in titles.

To recover the rest: re-run `python3 tools/fetch_site_images.py` from a machine
that can reach quentinfears.com (it re-pushes the `site-images` branch with the
manifest), then extend the affected shoots' `images` lists in
`content/galleries.yaml`.
