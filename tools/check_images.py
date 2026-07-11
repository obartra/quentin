#!/usr/bin/env python3
"""
Image budget gate for quentinfears.com (Astro build).

Fails CI when images regress on optimization, so a heavy or un-processed photo
can never sneak in. Runs with the standard library only.

Enforces, over public/assets/img/:
  1. Every photo referenced by the CMS content ships AVIF + WebP responsive
     variants (run tools/optimize_images.py after adding one).
  2. No shipped raster exceeds its per-format byte budget.

Usage: python3 tools/check_images.py
Exit 0 = within budget, exit 1 = at least one violation.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "public", "assets", "img")
CONTENT = os.path.join(ROOT, "content")

# Per-format ceiling in KB for any single shipped file.
BUDGET_KB = {"avif": 180, "webp": 250, "jpg": 380, "jpeg": 380, "png": 64}

# Social card + PWA icons are not part of the responsive-photo pipeline.
EXEMPT_FROM_VARIANTS = {"og-cover.jpg", "icon-192.png", "icon-512.png"}


def referenced_photos():
    srcs = set()
    for f in glob.glob(os.path.join(CONTENT, "*.yaml")):
        text = open(f, encoding="utf-8").read()
        for m in re.findall(r"assets/img/([a-z0-9-]+\.jpg)", text):
            srcs.add(m)
    return sorted(srcs)


def main():
    errors = []

    for f in sorted(glob.glob(os.path.join(IMGDIR, "*.*"))):
        ext = f.rsplit(".", 1)[-1].lower()
        cap = BUDGET_KB.get(ext)
        if cap is None:
            continue
        kb = os.path.getsize(f) / 1024
        if kb > cap:
            errors.append(
                f"{os.path.relpath(f, ROOT)} is {kb:.0f}KB (budget {cap}KB for .{ext}) "
                f"- run tools/optimize_images.py"
            )

    photos = referenced_photos()
    for name in photos:
        if name in EXEMPT_FROM_VARIANTS:
            continue
        base = name[:-4]
        for fmt in ("avif", "webp"):
            if not glob.glob(os.path.join(IMGDIR, f"{base}-*.{fmt}")):
                errors.append(
                    f"{name} is referenced by content but has no {fmt.upper()} variants "
                    f"- run tools/optimize_images.py"
                )

    n_variants = len(glob.glob(os.path.join(IMGDIR, "*-*.avif"))) + len(
        glob.glob(os.path.join(IMGDIR, "*-*.webp"))
    )
    if errors:
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nImage budget check failed: {len(errors)} violation(s).")
        return 1

    print(
        f"Image budget check passed: {len(photos)} photos, "
        f"{n_variants} AVIF/WebP variants, all within budget."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
