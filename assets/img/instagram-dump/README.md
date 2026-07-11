# Instagram @mrqfears image dump

Images pulled from the **@mrqfears** Instagram grid (Quentin Fears), for use as a
selection pool for the portfolio site. Every file is named by its post shortcode;
`manifest.json` maps each file to its permalink, kind, dimensions, and caption.

## Status: ANONYMOUS STARTER SUBSET (not the full archive yet)

This branch currently holds only the **12 most-recent posts** (20 stills):

- **9 carousel photos** at full resolution (several 2000-4096 px) — the real,
  usable photography.
- **11 reel poster frames** (640-1206 px) — thumbnails of video posts.

Instagram blocks logged-out access past the first ~12 posts (it hard-requires a
login and rate-limits everything else), so an un-authenticated pull cannot reach
the deeper archive — including the celebrity-styling work (Macy Gray, Skai
Jackson, Norman Reedus, Garcelle, Keesha Sharp, EJ Johnson, Sheen covers) that
the portfolio's archive slots want.

## How to get the FULL ~1888-post archive (run on the Mac, ~2 min)

The full pull needs the logged-in session. `gallery-dl` reads Chrome's own
cookie jar; on macOS the first run shows a Keychain prompt ("allow access to
**Chrome Safe Storage**") that must be approved once — this is why it can't be
done headlessly or from a phone.

```sh
python3 -m pip install --user gallery-dl

# Approve the one-time Keychain "Chrome Safe Storage" prompt when it appears.
python3 -m gallery_dl \
  --cookies-from-browser chrome \
  -o videos=false \
  --range 1-400 \
  -D assets/img/instagram-dump \
  "https://www.instagram.com/mrqfears/"
```

Then re-commit this directory to the branch (it is git-ignored on other
branches; force-add it here):

```sh
git add -f assets/img/instagram-dump && git commit -m "Full @mrqfears archive" \
  && git push --force origin instagram-images
```

`--range 1-400` caps the pull at ~400 files; raise/remove it for everything.
`-o videos=false` keeps images only (skips video files). Drop it to also fetch
the reels themselves.

## The lighter, no-login tool

`tools/fetch_instagram_images.py` (on this branch) is a stdlib-only fetcher that
uses Instagram's public logged-out endpoints. It reliably retrieves the recent
subset without any cookies, dedupes by content hash, writes this manifest, and
can push to a branch. It is what produced the starter set above; it cannot pass
the login wall for the deep archive.
