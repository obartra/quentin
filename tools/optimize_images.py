#!/usr/bin/env python3
"""
Responsive image pipeline for quentinfears.com (Astro build).

For every photo referenced by the Keystatic content (content/*.yaml), this
generates right-sized AVIF and WebP variants plus an optimized JPEG fallback in
public/assets/img/, and writes src/data/img-variants.json so the <Picture>
component knows each image's widths and intrinsic size. Pages ship modern,
appropriately-scaled images instead of one oversized JPEG.

Pristine sources are copied once into public/assets/img/.orig/ (gitignored) and
every encode reads from there, so the script is idempotent: re-running never
recompresses an already-compressed file.

Usage: python3 tools/optimize_images.py [--report]
Requires Pillow with AVIF + WebP write support (Pillow >= 11).
"""
import glob
import json
import os
import re
import shutil
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "public", "assets", "img")
ORIG = os.path.join(IMGDIR, ".orig")
CONTENT = os.path.join(ROOT, "content")
MANIFEST = os.path.join(ROOT, "src", "data", "img-variants.json")

WIDTHS = [400, 800]
MAXW = 1080
JPEG_Q = 80
WEBP_Q = 70
AVIF_Q = 42


def referenced_photos():
    """Every assets/img/*.jpg path the CMS content points at."""
    srcs = set()
    for f in glob.glob(os.path.join(CONTENT, "*.yaml")):
        text = open(f, encoding="utf-8").read()
        for m in re.findall(r"assets/img/([a-z0-9-]+\.jpg)", text):
            srcs.add(m)
    return sorted(srcs)


def widths_for(source_width):
    ws = [w for w in WIDTHS if w < source_width and w <= MAXW]
    ws.append(min(source_width, MAXW))
    return sorted(set(ws))


def encode(name, report=False):
    base = name[:-4]  # strip ".jpg"
    live = os.path.join(IMGDIR, name)
    orig = os.path.join(ORIG, name)

    if not os.path.exists(orig):
        os.makedirs(ORIG, exist_ok=True)
        shutil.copy2(live, orig)

    src = Image.open(orig).convert("RGB")
    W, H = src.size
    widths = widths_for(W)
    produced = []

    for w in widths:
        h = round(H * w / W)
        im = src.resize((w, h), Image.LANCZOS)
        for ext, kwargs in (
            ("avif", dict(format="AVIF", quality=AVIF_Q)),
            ("webp", dict(format="WEBP", quality=WEBP_Q, method=6)),
        ):
            out = os.path.join(IMGDIR, f"{base}-{w}.{ext}")
            if not report:
                im.save(out, **kwargs)
            produced.append(out)

    topw = widths[-1]
    toph = round(H * topw / W)
    if not report:
        src.resize((topw, toph), Image.LANCZOS).save(
            live, format="JPEG", quality=JPEG_Q, optimize=True, progressive=True
        )
    produced.append(live)
    # manifest uses the top (fallback) intrinsic size for width/height.
    return {"width": topw, "height": toph, "widths": widths}, produced


def main():
    report = "--report" in sys.argv
    photos = referenced_photos()
    if not photos:
        print("No content-referenced photos found.", file=sys.stderr)
        return 1

    manifest = {}
    total_before = total_after = 0
    for name in photos:
        before = os.path.getsize(os.path.join(IMGDIR, name))
        info, produced = encode(name, report=report)
        after = sum(os.path.getsize(p) for p in produced)
        manifest[f"assets/img/{name}"] = info
        total_before += before
        total_after += after
        print(
            f"  {name:26} {info['width']}x{info['height']}  widths={info['widths']}  "
            f"{before/1024:6.0f}KB jpg -> {after/1024:6.0f}KB set"
        )

    if not report:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")

    print(
        f"\n{len(photos)} photos. Wrote {os.path.relpath(MANIFEST, ROOT)}. "
        f"Fallback-JPEG payload {total_before/1024:.0f}KB; full variant set "
        f"{total_after/1024:.0f}KB (browser downloads ONE variant per image)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
