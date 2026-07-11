# Instagram @mrqfears image dump

Photography pulled from the **@mrqfears** Instagram grid (Quentin Fears), as a
selection pool for the portfolio site. `manifest.json` maps every file to its
post permalink, shortcode, dimensions, date, and caption.

## Contents

- **187 photos** (images only; reels/videos were excluded).
- Mostly **carousel photos** at original resolution plus a few single photos.
- **Date range:** 2024-02-26 → 2026-06-19 (the most recent ~13 pages of posts;
  the deep back-catalogue was intentionally not pulled).

Files are named by Instagram media id (e.g. `3923101934693768506_....jpg`);
carousel children share a post id prefix. Use `manifest.json` to look up the
human-facing shortcode, permalink, caption, and shot date for any file.

## How this was produced

Authenticated pull via `gallery-dl` reading the local Chrome cookie jar:

```sh
python3 -m gallery_dl --cookies-from-browser chrome -o videos=false \
  --range 1-160 --write-metadata -D assets/img/instagram-dump \
  "https://www.instagram.com/mrqfears/"
```

(`--range` counts posts; raise it to reach further back. The first run needs a
one-time macOS Keychain approval for "Chrome Safe Storage".)

Sidecar metadata was consolidated into `manifest.json` and the per-file `.json`
sidecars removed. `tools/fetch_instagram_images.py` (also on this branch) is a
dependency-free fallback that pulls the most-recent posts without any login.

## For the agent placing these

Good candidates for the portfolio's archive/case slots are the carousel photos
with styling captions (search `manifest.json` captions for names/brands, e.g.
"Speedo", editorial credits). Filenames carry no meaning on their own; always
resolve through `manifest.json`.
