#!/usr/bin/env python3
"""
Authenticated Instagram pull for @mrqfears (or any profile), using gallery-dl
with the local Chrome session, then consolidate the result into a clean image
set + manifest.json.

This is the method that produced the 187-photo dump on the `instagram-images`
branch. Use it for a deeper / one-off backfill than the login-free
tools/fetch_instagram_images.py can reach. For the recent-posts-only case (e.g.
a weekly "what's new" check) prefer that login-free tool instead.

Requirements
------------
- gallery-dl:  python3 -m pip install --user gallery-dl   (or pipx install)
- A Chrome profile logged into Instagram.
- macOS: the FIRST run triggers a Keychain prompt to read "Chrome Safe Storage"
  (the key that decrypts Chrome's cookies). It must be approved once, on the
  Mac, by a human. After approving "Always Allow" it will not prompt again, so
  later runs can be non-interactive as long as the Instagram login stays valid.

Usage
-----
    python3 tools/fetch_instagram_authed.py                 # default: @mrqfears, posts 1-160, images only
    python3 tools/fetch_instagram_authed.py --range 1-400   # deeper
    python3 tools/fetch_instagram_authed.py --user someone --browser chrome

`--range` counts POSTS (each post may yield several image files). Videos are
excluded by default (`--no-videos`); the manifest records shortcode, permalink,
caption, date, and dimensions per image. Sidecar .json files are removed after
they are folded into manifest.json.

This script does NOT touch git. Review the dump, then commit/push it to the data
branch yourself (see tools/fetch_instagram_images.py's push helper or ASSETS.md).
"""

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter


def run_gallery_dl(user, out, rng, videos, browser):
    url = f"https://www.instagram.com/{user}/"
    cmd = [
        sys.executable, "-m", "gallery_dl",
        "--cookies-from-browser", browser,
        "-o", f"videos={'true' if videos else 'false'}",
        "--range", rng,
        "--write-metadata",
        "-D", out,
        url,
    ]
    print("running:", " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\ngallery-dl exited {r.returncode}. If it stalled with no files, "
              f"a macOS Keychain prompt for 'Chrome Safe Storage' is waiting for "
              f"approval on the Mac.", file=sys.stderr)
    return r.returncode


def consolidate(out):
    """Dedupe images by content hash and fold sidecars into manifest.json."""
    seen, dups = {}, 0
    for p in sorted(glob.glob(os.path.join(out, "*.jpg"))):
        h = hashlib.sha1(open(p, "rb").read()).hexdigest()[:12]
        if h in seen:
            os.remove(p)
            if os.path.exists(p + ".json"):
                os.remove(p + ".json")
            dups += 1
        else:
            seen[h] = p

    images = []
    for p in sorted(glob.glob(os.path.join(out, "*.jpg"))):
        m = json.load(open(p + ".json")) if os.path.exists(p + ".json") else {}
        images.append({
            "file": os.path.basename(p),
            "kind": "carousel_photo" if m.get("sidecar_media_id") else "photo",
            "shortcode": m.get("post_shortcode") or m.get("shortcode"),
            "permalink": m.get("post_url"),
            "width": m.get("width"),
            "height": m.get("height"),
            "date": m.get("date"),
            "num": m.get("num"),
            "count": m.get("count"),
            "caption": m.get("description") or None,
            "bytes": os.path.getsize(p),
        })

    for sc in glob.glob(os.path.join(out, "*.jpg.json")):
        os.remove(sc)

    images.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    dates = [i["date"] for i in images if i.get("date")]
    manifest = {
        "source": "gallery-dl authenticated pull",
        "image_count": len(images),
        "date_range": {"newest": dates[0] if dates else None,
                       "oldest": dates[-1] if dates else None},
        "kinds": dict(Counter(i["kind"] for i in images)),
        "images": images,
    }
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=2)
    print(f"\nconsolidated: {len(images)} images "
          f"({dict(manifest['kinds'])}), {dups} duplicates removed")
    if dates:
        print(f"date range: {dates[-1]}  ->  {dates[0]}")
    return len(images)


def main():
    ap = argparse.ArgumentParser(description="Authenticated Instagram image pull + manifest.")
    ap.add_argument("--user", default="mrqfears")
    ap.add_argument("--out", default="assets/img/instagram-dump")
    ap.add_argument("--range", dest="rng", default="1-160", help="POST range, e.g. 1-400")
    ap.add_argument("--browser", default="chrome", help="cookies-from-browser source")
    ap.add_argument("--videos", dest="videos", action="store_true",
                    help="also download video files (default: images only)")
    ap.add_argument("--no-download", action="store_true",
                    help="skip gallery-dl; only (re)consolidate an existing dump")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if not args.no_download:
        run_gallery_dl(args.user, args.out, args.rng, args.videos, args.browser)
    consolidate(args.out)
    print(f"\nFiles in: {args.out}/   (see manifest.json). Commit/push the dump yourself.")


if __name__ == "__main__":
    main()
