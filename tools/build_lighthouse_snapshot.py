#!/usr/bin/env python3
"""
De-gate the built Astro site (dist/) so Lighthouse measures the real, indexable
page instead of the client-side password gate.

The live site ships behind a gate and robots=noindex during private preview, so
a naive Lighthouse run would score the gate screen and mark the page non-index-
able. This edits the built HTML in place to remove the gate and set robots=index,
representing the public-launch state. CI-only: dist/ is rebuilt every run and is
never deployed by this workflow.

Usage: python3 tools/build_lighthouse_snapshot.py [dist_dir]   (default: dist)
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "dist")

INLINE_GATE = re.compile(
    r"if\(sessionStorage\.getItem\('qf-access'\)!=='1'\)"
    r"document\.documentElement\.classList\.add\('locked'\);"
)
GATE_SCRIPT = re.compile(r'\s*<script src="assets/js/gate\.js"[^>]*></script>')
ROBOTS_META = re.compile(r'(<meta name="robots" content=")[^"]*(")')


def main():
    files = glob.glob(os.path.join(DIST, "*.html"))
    if not files:
        print(f"No HTML in {DIST}; run `npm run build` first.", file=sys.stderr)
        return 1
    for f in files:
        text = open(f, encoding="utf-8").read()
        text = INLINE_GATE.sub("", text)
        text = GATE_SCRIPT.sub("", text)
        text = ROBOTS_META.sub(r"\1index, follow\2", text)
        open(f, "w", encoding="utf-8").write(text)
    print(f"De-gated {len(files)} pages in {os.path.relpath(DIST, ROOT)} "
          f"(gate removed, robots=index).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
