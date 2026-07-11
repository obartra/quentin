#!/usr/bin/env python3
"""
Fetch every image from quentinfears.com into this repo.

Run it on YOUR machine (it needs to reach the live site — the build sandbox
can't). No third-party packages required; Python 3.8+ standard library only.

    # download only:
    python3 tools/fetch_site_images.py --no-push

    # download AND push to a branch so Claude can pull it in and analyze (default):
    python3 tools/fetch_site_images.py            # pushes to branch "site-images"
    python3 tools/fetch_site_images.py --branch site-images --remote origin

What it does
------------
1. Crawls the site (same-origin links, breadth-first) starting from the home
   page, plus a fallback list of the known section routes.
2. Extracts image URLs from: <img src/srcset>, <source srcset>, og:image, and
   every Wix media reference embedded in the page HTML/JSON
   (static.wixstatic.com/media/... and wix:image://v1/... forms).
3. Rewrites Wix URLs to the ORIGINAL full-resolution file (strips the
   /v1/fill/w_.../ display transform), so you get the best quality available.
4. Downloads everything into assets/img/site-dump/ (deduped by content hash)
   and writes manifest.json mapping each file to its source URL and the pages
   it appeared on.
5. (Default) commits the dump to a dedicated branch ("site-images") and pushes
   it to origin WITHOUT disturbing your current branch — so Claude can fetch
   that branch, view the images, and place the good ones for you. Then just tell
   Claude: "the images are on branch site-images".

After it runs, review assets/img/site-dump/, then rename the ones you want into
the documented slots in ASSETS.md (hero-portrait.jpg, archive-macygray.jpg, ...).

Note: Instagram (@mrqfears) is login-walled and is NOT covered here — see the
note at the bottom of this file.
"""

import argparse
import hashlib
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import deque

DEFAULT_BASE = "https://www.quentinfears.com"

# Fallback seeds in case navigation links aren't in the server-rendered HTML.
KNOWN_ROUTES = [
    "/", "/celebrity", "/celebrity-men", "/red-carpet",
    "/editorial", "/editorial-men", "/commercial", "/production",
    "/services", "/tv-correspondent", "/about-me", "/press-testimonials",
    "/press", "/testimonials",
]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

IMG_EXT = r"(?:jpg|jpeg|png|webp|gif|avif|svg)"

# static.wixstatic.com/media/<file>.<ext>  (optionally scheme-relative)
RE_WIX_MEDIA = re.compile(
    r"(?:https?:)?//static\.wixstatic\.com/media/[^\s\"'<>()\\]+?\." + IMG_EXT,
    re.I,
)
# wix:image://v1/<file>~mv2.<ext>/...   ->  reconstruct the media URL
RE_WIX_IMAGE = re.compile(r"wix:image://v1/([^/\"'\s]+?\." + IMG_EXT + r")", re.I)
# generic src / srcset / og:image / background-image url(...)
RE_SRC = re.compile(r"(?:src|data-src|content)\s*=\s*[\"']([^\"']+?\." + IMG_EXT + r"[^\"']*)[\"']", re.I)
RE_SRCSET = re.compile(r"srcset\s*=\s*[\"']([^\"']+)[\"']", re.I)
RE_CSS_URL = re.compile(r"url\(\s*[\"']?([^\"')]+?\." + IMG_EXT + r"[^\"')]*)", re.I)
RE_HREF = re.compile(r"href\s*=\s*[\"']([^\"'#?]+)[\"']", re.I)


def make_opener(insecure=False):
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    handler = urllib.request.HTTPSHandler(context=ctx)
    opener = urllib.request.build_opener(handler)
    return opener


def fetch(opener, url, referer=None, binary=False, timeout=30):
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=timeout) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8", "replace")


def to_original(url):
    """Rewrite a Wix display URL to the original full-res upload."""
    if url.startswith("//"):
        url = "https:" + url
    if "static.wixstatic.com/media/" in url and "/v1/" in url:
        url = url.split("/v1/")[0]
    return url


def collect_images(html, page_url):
    found = set()
    for m in RE_WIX_MEDIA.findall(html):
        found.add(to_original(m if m.startswith("http") else "https:" + m))
    for f in RE_WIX_IMAGE.findall(html):
        found.add("https://static.wixstatic.com/media/" + f)
    for s in RE_SRC.findall(html):
        found.add(to_original(urllib.parse.urljoin(page_url, s)))
    for ss in RE_SRCSET.findall(html):
        # NB: Wix transform URLs contain commas (w_1000,h_1400), so we cannot
        # naively split srcset on ",". Only accept candidates that begin like a
        # real URL — this rejects the comma-fragment tails of Wix URLs (the Wix
        # media URLs themselves are already captured by RE_WIX_MEDIA above).
        for part in ss.split(","):
            u = part.strip().split(" ")[0]
            if u.startswith(("http://", "https://", "//", "/")):
                found.add(to_original(urllib.parse.urljoin(page_url, u)))
    for c in RE_CSS_URL.findall(html):
        found.add(to_original(urllib.parse.urljoin(page_url, c)))
    # drop obvious non-content sprites / icons
    return {u for u in found if u and not u.lower().endswith(".svg")}


def same_origin_links(html, base_host, page_url):
    links = set()
    for href in RE_HREF.findall(html):
        absu = urllib.parse.urljoin(page_url, href)
        p = urllib.parse.urlparse(absu)
        if p.scheme in ("http", "https") and p.netloc == base_host:
            # only crawl page-like paths, skip files/assets
            if not re.search(r"\.(jpg|jpeg|png|webp|gif|avif|svg|pdf|zip|css|js|ico|mp4|mov)$", p.path, re.I):
                links.add(p._replace(query="", fragment="").geturl())
    return links


def safe_filename(url):
    name = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] or "image"
    name = urllib.parse.unquote(name)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not re.search(r"\.(jpg|jpeg|png|webp|gif|avif)$", name, re.I):
        name += ".jpg"
    return name


def git(args, check=True, capture=False):
    r = subprocess.run(["git"] + args, text=True, capture_output=capture)
    if check and r.returncode != 0:
        raise RuntimeError((getattr(r, "stderr", "") or getattr(r, "stdout", "") or "").strip())
    return (r.stdout or "").strip() if capture else r.returncode


def push_dump(out_dir, branch, remote):
    """Commit the image dump to `branch` and push, then return to the current
    branch. Does not disturb the working branch's history."""
    try:
        git(["rev-parse", "--is-inside-work-tree"], capture=True)
    except Exception:
        print("\n(not a git repo — skipping push; commit the images yourself)")
        return
    if remote not in (git(["remote"], capture=True) or "").split():
        print(f"\n(no '{remote}' remote — skipping push)")
        return

    original = git(["rev-parse", "--abbrev-ref", "HEAD"], capture=True)
    email = git(["config", "user.email"], check=False, capture=True)
    idcfg = [] if email else ["-c", "user.email=fetch@local", "-c", "user.name=Image Fetcher"]

    print(f"\nPushing dump to '{branch}' on '{remote}' (current branch: {original})...")
    git(["checkout", "-B", branch])
    try:
        git(["add", "-f", out_dir])
        has_staged = git(["diff", "--cached", "--quiet"], check=False)  # 1 = changes staged
        if has_staged == 0:
            print("  nothing new to commit")
        else:
            git(idcfg + ["commit", "-m", f"Image dump from live site ({out_dir})"])
        git(["push", "-u", "--force", remote, branch])
        print(f"\n  Pushed to '{branch}'. Now tell Claude:")
        print(f"    \"the images are on branch {branch}\"")
    finally:
        if original and original != "HEAD":
            git(["checkout", original])


def main():
    ap = argparse.ArgumentParser(description="Download all images from quentinfears.com")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--out", default="assets/img/site-dump")
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--insecure", action="store_true", help="skip TLS verification")
    ap.add_argument("--branch", default="site-images",
                    help="branch to push the dump to (default: site-images)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--push", dest="push", action="store_true", default=True,
                    help="push the dump to --branch (default: on)")
    ap.add_argument("--no-push", dest="push", action="store_false",
                    help="only download; do not touch git")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    base_host = urllib.parse.urlparse(base).netloc
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    opener = make_opener(insecure=args.insecure)

    # --- crawl pages ---
    seeds = [base + r for r in KNOWN_ROUTES]
    queue = deque(dict.fromkeys([base + "/"] + seeds))
    seen_pages, visited = set(), []
    img_pages = {}  # image url -> set(page urls)

    while queue and len(visited) < args.max_pages:
        page = queue.popleft()
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(opener, page, referer=base)
        except Exception as e:
            print(f"  skip page {page}  ({e.__class__.__name__})")
            continue
        visited.append(page)
        for img in collect_images(html, page):
            img_pages.setdefault(img, set()).add(page)
        for link in same_origin_links(html, base_host, page):
            if link not in seen_pages:
                queue.append(link)
        print(f"crawled {page}  (+{len(collect_images(html, page))} imgs)")
        time.sleep(0.25)

    print(f"\n{len(img_pages)} unique image URLs across {len(visited)} pages. Downloading...\n")

    # --- download images (dedupe by content hash) ---
    manifest, by_hash = [], {}
    ok = fail = 0
    for i, (url, pages) in enumerate(sorted(img_pages.items()), 1):
        try:
            data = fetch(opener, url, referer=base, binary=True)
        except Exception as e:
            print(f"  [{i}] FAIL {url}  ({e.__class__.__name__})")
            fail += 1
            continue
        h = hashlib.sha1(data).hexdigest()[:12]
        if h in by_hash:
            manifest.append({"file": by_hash[h], "url": url,
                             "pages": sorted(pages), "duplicate_of_hash": h})
            continue
        fname = safe_filename(url)
        path = os.path.join(out_dir, fname)
        n = 1
        while os.path.exists(path) and hashlib.sha1(open(path, "rb").read()).hexdigest()[:12] != h:
            root, ext = os.path.splitext(fname)
            path = os.path.join(out_dir, f"{root}-{n}{ext}")
            n += 1
        with open(path, "wb") as f:
            f.write(data)
        by_hash[h] = os.path.basename(path)
        manifest.append({"file": os.path.basename(path), "url": url,
                         "pages": sorted(pages), "bytes": len(data)})
        ok += 1
        print(f"  [{i}] {len(data)//1024:>5} KB  {os.path.basename(path)}")
        time.sleep(0.15)

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump({"base": base, "pages": visited, "images": manifest}, f, indent=2)

    print(f"\nDone. {ok} downloaded, {fail} failed, "
          f"{len(manifest)-ok} duplicates skipped.")
    print(f"Files in: {out_dir}/   (see manifest.json)")

    if args.push and ok > 0:
        push_dump(out_dir, args.branch, args.remote)
    else:
        print("Next: rename the keepers into the slots documented in ASSETS.md.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

# ---------------------------------------------------------------------------
# Instagram (@mrqfears): not fetched here. Instagram requires login and blocks
# scraping, so a standalone script is unreliable and risks your account. Easiest
# path: open the profile, use "Save"/download tools you're comfortable with, or
# from the app request your data export, then drop chosen images into
# assets/img/ and I'll analyze + place them.
# ---------------------------------------------------------------------------
