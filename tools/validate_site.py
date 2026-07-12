#!/usr/bin/env python3
"""Validate internal consistency of the static site.

This is the "keep things in sync" guard. It is intentionally lightweight and
dependency-free (Python standard library only) so it runs anywhere, including CI,
with no install step.

What it checks (hard failures):
  1. Structural links resolve. Every local href/src that is NOT a content image
     (assets/img/...) points at a file that exists: page-to-page nav, the
     stylesheet, and the scripts.
  2. In-page anchors resolve. href="page#frag" / href="#frag" targets an
     element that actually has id="frag". Page links are extensionless
     ("work" -> work.html, the clean URL the static host serves).
  3. Galleries are wired. Every data-gallery="key" has a matching key in that
     page's <script id="gallery-data"> JSON (and vice-versa the JSON is valid).
  4. No leftover template junk (Wix boilerplate like "Mysite" / "Cordan" /
     "lorem ipsum").
  5. No em dashes in anything that ships. Copy policy: restructure the sentence
     (comma, colon, period, or a pipe in titles) instead of an em dash. Checked
     across every text file in the output (HTML, CSS, JS, XML, JSON, MD, SVG,
     TXT, webmanifest), including the literal character and its HTML entities.

What it deliberately does NOT fail on:
  - Missing content images under assets/img/. The site uses an image-slot system:
    an <img> whose file is absent falls back to a labeled placeholder by design
    (see ASSETS.md). Empty slots are reported as INFO for visibility, never as an
    error.

Usage:  python3 tools/validate_site.py   (exit code 0 = clean, 1 = problems)
"""

from __future__ import annotations

import json
import os
import re
import sys

# Directory to validate. The site is built by Astro into `dist/`, so validate
# that by default when it exists. Pass an explicit path as the first argument to
# override (e.g. a different output dir); falls back to the repo root otherwise.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:
    ROOT = os.path.abspath(sys.argv[1])
else:
    _dist = os.path.join(_REPO_ROOT, "dist")
    ROOT = _dist if os.path.isdir(_dist) else _REPO_ROOT

ATTR_REF = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)
ID_ATTR = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
DATA_GALLERY = re.compile(r'data-gallery\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
GALLERY_DATA = re.compile(
    r'<script[^>]*id=["\']gallery-data["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

EXTERNAL_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")
JUNK_STRINGS = ("lorem ipsum", "mysite", "cordan")

EM_DASH = "—"
EM_DASH_ENTITIES = ("&mdash;", "&#8212;", "&#x2014;")
TEXT_EXTENSIONS = (
    ".html", ".css", ".js", ".mjs", ".xml", ".json", ".md", ".txt",
    ".webmanifest", ".svg",
)
SKIP_DIRS = {"node_modules", ".git", ".astro"}

errors: list[str] = []
info: list[str] = []


def html_files() -> list[str]:
    return sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))


def ids_in(text: str) -> set[str]:
    return set(ID_ATTR.findall(text))


def check_page(name: str, pages: dict[str, str]) -> None:
    text = pages[name]
    ids = ids_in(text)

    for raw in ATTR_REF.findall(text):
        ref = raw.strip()
        if not ref or ref.startswith(EXTERNAL_PREFIXES) or ref == "#":
            continue

        # Pure in-page anchor, e.g. href="#main".
        if ref.startswith("#"):
            frag = ref[1:]
            if frag and frag not in ids:
                errors.append(f'{name}: anchor "#{frag}" has no matching id on the page')
            continue

        path_part, _, frag = ref.partition("#")
        path_part = path_part.lstrip("./")
        if not path_part:
            continue

        if path_part.startswith("assets/img/"):
            # Content image: absence is allowed (placeholder fallback).
            if not os.path.exists(os.path.join(ROOT, path_part)):
                info.append(f"{name}: image slot not yet filled -> {path_part}")
            continue

        # Page link. Internal links are extensionless ("work"); the static hosts
        # (GitHub Pages, Netlify) serve work.html for /work. Accept the .html
        # form too so legacy links stay valid.
        page_target = path_part if path_part.endswith(".html") else path_part + ".html"
        if page_target in pages:
            if frag and frag not in ids_in(pages[page_target]):
                errors.append(f'{name}: anchor "{path_part}#{frag}" has no matching id')
            continue

        target = os.path.join(ROOT, path_part)
        if not os.path.exists(target):
            errors.append(f"{name}: broken link -> {path_part}")
            continue

    check_galleries(name, text)
    for junk in JUNK_STRINGS:
        if junk in text.lower():
            errors.append(f'{name}: leftover template text "{junk}"')


def check_galleries(name: str, text: str) -> None:
    used = set(DATA_GALLERY.findall(text))
    match = GALLERY_DATA.search(text)
    if not used and not match:
        return
    if used and not match:
        errors.append(f"{name}: data-gallery buttons but no <script id=\"gallery-data\"> found")
        return
    try:
        keys = set(json.loads(match.group(1)))
    except (json.JSONDecodeError, TypeError) as exc:
        errors.append(f"{name}: gallery-data is not valid JSON ({exc})")
        return
    missing = used - keys
    if missing:
        errors.append(f'{name}: data-gallery={sorted(missing)} has no entry in gallery-data')


def check_em_dashes() -> None:
    """No em dashes in any shipped text file: restructure the sentence instead."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in sorted(filenames):
            if not filename.lower().endswith(TEXT_EXTENSIONS):
                continue
            path = os.path.join(dirpath, filename)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, 1):
                    low = line.lower()
                    if EM_DASH in line or any(e in low for e in EM_DASH_ENTITIES):
                        errors.append(
                            f"{rel}:{lineno}: em dash in shipped copy (restructure the sentence instead)"
                        )


def main() -> int:
    pages = {name: open(os.path.join(ROOT, name), encoding="utf-8").read() for name in html_files()}
    if not pages:
        print("No HTML files found at repo root", file=sys.stderr)
        return 1

    for name in pages:
        check_page(name, pages)

    check_em_dashes()

    for line in info:
        print(f"INFO  {line}")
    for line in errors:
        print(f"ERROR {line}")

    n = len(pages)
    if errors:
        print(f"\nFAIL: {len(errors)} problem(s) across {n} page(s).")
        return 1
    print(f"\nOK: {n} page(s) validated, {len(info)} unfilled image slot(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
