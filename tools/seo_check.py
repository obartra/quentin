#!/usr/bin/env python3
"""
SEO invariant checker for quentinfears.com.

Runs with the standard library only (no pip install) so it works anywhere
Python 3 is available. Validates that every page keeps the technical-SEO
layer intact and in sync with sitemap.xml and the shared asset set.

Usage:
    python3 tools/seo_check.py

Exit code 0 = all invariants hold. Exit code 1 = at least one hard failure.
Soft issues (e.g. an over-long title) print as warnings and do not fail CI.
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# ---- Config -----------------------------------------------------------------
# The single source of truth for the site's canonical origin. If the domain
# changes, update this and find-and-replace across the HTML / robots / sitemap.
BASE = "https://quentinfears.com"

# This is a personal site. It must not present Quentin as an official
# representative or spokesperson of an employer in machine-readable metadata.
# These terms are allowed in visible body copy (his own first-person words)
# but not inside <head> (meta tags + JSON-LD structured data).
DISALLOWED_IN_HEAD = ["walmart"]

# Assets the SEO layer references and that must exist in the repo.
REQUIRED_ASSETS = [
    "favicon.svg",
    "favicon.ico",
    "apple-touch-icon.png",
    "site.webmanifest",
    "robots.txt",
    "sitemap.xml",
    "assets/img/og-cover.jpg",
    "assets/img/icon-192.png",
    "assets/img/icon-512.png",
]

# Substrings that every page's <head> must link to.
REQUIRED_LINK_ASSETS = [
    "favicon.svg",
    "favicon.ico",
    "apple-touch-icon.png",
    "site.webmanifest",
    "assets/css/style.css",
]

# Required meta by <meta property="..."> (Open Graph) and <meta name="...">.
REQUIRED_OG = ["og:title", "og:description", "og:type", "og:url", "og:image", "og:site_name"]
REQUIRED_NAME_META = ["description", "robots", "twitter:card"]

# Directory to validate. The site is built by Astro into `dist/`, so validate
# that by default when it exists. Pass an explicit path as the first argument to
# override (e.g. a different output dir); falls back to the repo root otherwise.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:
    ROOT = os.path.abspath(sys.argv[1])
else:
    _dist = os.path.join(_REPO_ROOT, "dist")
    ROOT = _dist if os.path.isdir(_dist) else _REPO_ROOT

errors = []
warnings = []


def err(page, msg):
    errors.append(f"{page}: {msg}")


def warn(page, msg):
    warnings.append(f"{page}: {msg}")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')


def parse_attrs(tag):
    return {k.lower(): v for k, v in ATTR_RE.findall(tag)}


def find_tags(html, name):
    return re.findall(r"<%s\b[^>]*>" % name, html, re.IGNORECASE)


def head_of(html):
    m = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else ""


def expected_url(page):
    return BASE + "/" if page == "index.html" else BASE + "/" + page


# ---- Per-page checks --------------------------------------------------------
def check_page(page, html, sitemap_locs):
    head = head_of(html)
    if not head:
        err(page, "no <head> found")
        return

    metas = [parse_attrs(t) for t in find_tags(head, "meta")]
    by_prop = {m["property"]: m.get("content", "") for m in metas if "property" in m}
    by_name = {m["name"]: m.get("content", "") for m in metas if "name" in m}

    # <title>
    titles = re.findall(r"<title\b[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if len(titles) != 1 or not titles[0].strip():
        err(page, f"expected exactly one non-empty <title>, found {len(titles)}")
    elif len(titles[0].strip()) > 65:
        warn(page, f"<title> is {len(titles[0].strip())} chars (Google shows ~60)")

    # meta description
    desc = by_name.get("description", "").strip()
    if not desc:
        err(page, "missing meta description")
    elif len(desc) > 200:
        err(page, f"meta description is {len(desc)} chars (keep under ~200)")
    elif len(desc) > 160:
        warn(page, f"meta description is {len(desc)} chars (Google truncates ~160)")

    # Required meta tags
    for prop in REQUIRED_OG:
        if not by_prop.get(prop, "").strip():
            err(page, f"missing or empty <meta property=\"{prop}\">")
    for nm in REQUIRED_NAME_META:
        if not by_name.get(nm, "").strip():
            err(page, f"missing or empty <meta name=\"{nm}\">")

    if by_name.get("twitter:card") and by_name["twitter:card"] != "summary_large_image":
        warn(page, f"twitter:card is '{by_name['twitter:card']}' (expected summary_large_image)")

    # canonical + og:url agree and match the expected URL for this file
    exp = expected_url(page)
    canon = None
    for t in find_tags(head, "link"):
        a = parse_attrs(t)
        if a.get("rel", "").lower() == "canonical":
            canon = a.get("href", "")
    if canon is None:
        err(page, "missing <link rel=\"canonical\">")
    elif canon != exp:
        err(page, f"canonical is '{canon}', expected '{exp}'")
    if by_prop.get("og:url") and by_prop["og:url"] != exp:
        err(page, f"og:url is '{by_prop['og:url']}', expected '{exp}'")

    # og:image must be absolute and point at an asset that exists
    ogimg = by_prop.get("og:image", "")
    if ogimg:
        if not ogimg.startswith("http"):
            err(page, f"og:image must be an absolute URL, got '{ogimg}'")
        elif ogimg.startswith(BASE):
            local = ogimg[len(BASE):].lstrip("/")
            if not os.path.isfile(os.path.join(ROOT, local)):
                err(page, f"og:image points at missing file '{local}'")

    # Required linked assets (favicon, manifest, stylesheet)
    for asset in REQUIRED_LINK_ASSETS:
        if asset not in head:
            err(page, f"<head> does not link required asset '{asset}'")

    # theme-color is a nice-to-have signal
    if not by_name.get("theme-color"):
        warn(page, "missing <meta name=\"theme-color\">")

    # Gate <-> indexing coupling. A page behind the client-side password gate
    # is a private preview and should be noindex; a public (ungated) page
    # should be indexable. This auto-resolves at launch when the gate is
    # removed and robots is flipped back to index.
    gated = "gate.js" in html or "qf-access" in head
    robots_val = by_name.get("robots", "").lower()
    if gated and "noindex" not in robots_val:
        warn(page, "page is behind the password gate but robots is not noindex "
                   "(a private preview should not be indexed)")
    if not gated and "noindex" in robots_val:
        warn(page, "page is public (no gate) but robots is noindex "
                   "(it will not appear in search)")

    # Exactly one <h1>
    h1s = re.findall(r"<h1\b", html, re.IGNORECASE)
    if len(h1s) != 1:
        err(page, f"expected exactly one <h1>, found {len(h1s)}")

    # Images should have alt text
    for img in find_tags(html, "img"):
        a = parse_attrs(img)
        if "alt" not in a:
            err(page, f"<img> without alt attribute: {img[:70]}...")

    # JSON-LD: at least one block, each valid JSON, each keyed to BASE
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    )
    if not blocks:
        err(page, "no JSON-LD structured data")
    for i, b in enumerate(blocks):
        try:
            json.loads(b)
        except json.JSONDecodeError as e:
            err(page, f"JSON-LD block {i} is invalid JSON: {e}")
            continue
        if BASE not in b:
            err(page, f"JSON-LD block {i} does not reference {BASE}")

    # Personal-site guard: no employer claims in <head> metadata / structured data
    head_lc = head.lower()
    for term in DISALLOWED_IN_HEAD:
        if term in head_lc:
            err(
                page,
                f"'{term}' appears in <head> metadata/structured data; this is a "
                f"personal site and must not assert an employer in machine-readable "
                f"tags (body copy is fine)",
            )

    # Page must be listed in the sitemap
    if exp not in sitemap_locs:
        err(page, f"URL '{exp}' is not listed in sitemap.xml")


# ---- Site-wide checks -------------------------------------------------------
def check_sitemap(pages):
    try:
        tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    except (ET.ParseError, FileNotFoundError) as e:
        err("sitemap.xml", f"could not parse: {e}")
        return set()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = {el.text.strip() for el in tree.findall(".//s:loc", ns)}
    expected = {expected_url(p) for p in pages}
    for extra in locs - expected:
        err("sitemap.xml", f"lists '{extra}' which is not a page in the repo")
    for missing in expected - locs:
        err("sitemap.xml", f"does not list '{missing}'")
    return locs


def check_robots():
    try:
        robots = read("robots.txt")
    except FileNotFoundError:
        err("robots.txt", "missing")
        return
    if "user-agent:" not in robots.lower():
        err("robots.txt", "missing a User-agent line")
    if f"Sitemap: {BASE}/sitemap.xml" not in robots:
        err("robots.txt", f"must point to 'Sitemap: {BASE}/sitemap.xml'")


def check_manifest():
    try:
        data = json.loads(read("site.webmanifest"))
    except FileNotFoundError:
        err("site.webmanifest", "missing")
        return
    except json.JSONDecodeError as e:
        err("site.webmanifest", f"invalid JSON: {e}")
        return
    for icon in data.get("icons", []):
        src = icon.get("src", "").lstrip("/")
        if src and not os.path.isfile(os.path.join(ROOT, src)):
            err("site.webmanifest", f"icon references missing file '{src}'")


def check_assets():
    for asset in REQUIRED_ASSETS:
        if not os.path.isfile(os.path.join(ROOT, asset)):
            err("assets", f"required asset missing: '{asset}'")


# ---- Main -------------------------------------------------------------------
def main():
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.html")))
    if not pages:
        print("No HTML pages found; nothing to check.", file=sys.stderr)
        return 1

    check_assets()
    check_robots()
    check_manifest()
    sitemap_locs = check_sitemap(pages)

    for page in pages:
        check_page(page, read(page), sitemap_locs)

    for w in warnings:
        print(f"  warn  {w}")
    if warnings:
        print()

    if errors:
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nSEO check failed: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1

    print(
        f"SEO check passed: {len(pages)} pages, "
        f"{len(REQUIRED_ASSETS)} assets, {len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
