#!/usr/bin/env python3
"""
Fetch images from an Instagram profile (default @mrqfears, Quentin Fears) into
this repo, then push them to a dedicated branch so another agent can pull the
branch, view the images, and place the good ones into the portfolio.

Run it on a machine with network access (Instagram must be reachable). No
third-party packages required; Python 3.8+ standard library only.

    # download only (into assets/img/instagram-dump/):
    python3 tools/fetch_instagram_images.py --no-push

    # download AND push to branch "instagram-images" (default):
    python3 tools/fetch_instagram_images.py

How it works
------------
Uses Instagram's public, un-authenticated web endpoints, i.e. the same ones the
website itself calls from a logged-out browser:
  * /api/v1/users/web_profile_info/  ->  profile + numeric user id
  * /api/v1/feed/user/<id>/          ->  paginated timeline (next_max_id cursor)
Both are called with the public web app-id header. No login, no cookies, and no
third-party downloader site (tools like toolzu only grab the avatar and are
captcha/ad-walled). Works for PUBLIC profiles only; a private profile yields
nothing.

For each post it downloads the highest-resolution still available:
  * photos and carousel photo children  ->  full-res image_versions2 candidate
  * reels / videos                      ->  the poster frame (largest still).
    The video file itself is not downloaded; this grabs images only.
Everything is deduped by content hash. A manifest.json records, per file:
shortcode, permalink, kind (photo | carousel_photo | video_poster), dimensions,
caption, and taken_at.

Then, by default, it commits the dump to a dedicated branch ("instagram-images")
and pushes it to origin WITHOUT disturbing your current branch, so another agent
can fetch that branch, view the images, and place the good ones. Then just say:
"the Instagram images are on branch instagram-images".
"""

import argparse
import hashlib
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# Public web app-id that the logged-out instagram.com site sends with its API
# calls. Not a secret; it is visible in every browser request to Instagram.
APP_ID = "936619743392459"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

API = "https://i.instagram.com/api/v1"


def make_opener(insecure=False):
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))


def fetch(opener, url, binary=False, timeout=30, api=False):
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if api:
        headers["X-IG-App-ID"] = APP_ID
        headers["Referer"] = "https://www.instagram.com/"
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=timeout) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8", "replace")


def get_json(opener, url, retries=5, backoff=45):
    """GET a JSON API url, backing off on Instagram's anonymous rate limit
    (HTTP 401/429 with a "wait a few minutes" body)."""
    for attempt in range(retries + 1):
        try:
            return json.loads(fetch(opener, url, api=True))
        except urllib.error.HTTPError as e:
            if e.code in (401, 429) and attempt < retries:
                wait = backoff * (attempt + 1)
                print(f"    rate-limited ({e.code}); waiting {wait}s "
                      f"[retry {attempt + 1}/{retries}]")
                time.sleep(wait)
                continue
            raise


def user_id_for(opener, username):
    url = (API + "/users/web_profile_info/?username="
           + urllib.parse.quote(username))
    u = get_json(opener, url)["data"]["user"]
    if u.get("is_private"):
        raise SystemExit(f"@{username} is private; nothing to fetch.")
    return u["id"], u


def best_candidate(cands):
    """Return the url of the largest image_versions2 candidate."""
    if not cands:
        return None, 0, 0
    c = max(cands, key=lambda x: x.get("width", 0) * x.get("height", 0))
    return c.get("url"), c.get("width", 0), c.get("height", 0)


def caption_of(item):
    cap = item.get("caption")
    return cap.get("text") if cap else None


def stills_from_item(item):
    """Yield (kind, url, width, height, child_index) for every still in a post.
    media_type: 1 = photo, 2 = video, 8 = carousel."""
    mt = item.get("media_type")
    if mt == 8:
        for i, child in enumerate(item.get("carousel_media", []), 1):
            url, w, h = best_candidate(
                child.get("image_versions2", {}).get("candidates", []))
            if url:
                kind = ("video_poster" if child.get("media_type") == 2
                        else "carousel_photo")
                yield kind, url, w, h, i
    else:
        url, w, h = best_candidate(
            item.get("image_versions2", {}).get("candidates", []))
        if url:
            kind = "video_poster" if mt == 2 else "photo"
            yield kind, url, w, h, 0


def iter_items(opener, user_id, max_pages, count, sleep):
    """Yield timeline items newest-first, following the next_max_id cursor."""
    max_id = None
    for page in range(1, max_pages + 1):
        url = f"{API}/feed/user/{user_id}/?count={count}"
        if max_id:
            url += "&max_id=" + urllib.parse.quote(max_id)
        data = get_json(opener, url)
        items = data.get("items", [])
        print(f"  page {page}: {len(items)} posts")
        for it in items:
            yield it
        if not data.get("more_available") or not data.get("next_max_id"):
            break
        max_id = data["next_max_id"]
        time.sleep(sleep)


def filename_for(shortcode, kind, idx, ext):
    base = shortcode or "post"
    if kind == "video_poster" and idx == 0:
        return f"{base}_poster.{ext}"
    if idx:
        return f"{base}_{idx}.{ext}"
    return f"{base}.{ext}"


def ext_from_url(url, default="jpg"):
    path = urllib.parse.urlparse(url).path
    e = os.path.splitext(path)[1].lstrip(".").lower()
    return e if e in ("jpg", "jpeg", "png", "webp") else default


def git(args, check=True, capture=False):
    r = subprocess.run(["git"] + args, text=True, capture_output=capture)
    if check and r.returncode != 0:
        raise RuntimeError((getattr(r, "stderr", "") or getattr(r, "stdout", "")
                            or "").strip())
    return (r.stdout or "").strip() if capture else r.returncode


def push_dump(out_dir, branch, remote):
    """Commit the dump to `branch` and push, then return to the current branch."""
    try:
        git(["rev-parse", "--is-inside-work-tree"], capture=True)
    except Exception:
        print("\n(not a git repo; skipping push, commit the images yourself)")
        return
    if remote not in (git(["remote"], capture=True) or "").split():
        print(f"\n(no '{remote}' remote; skipping push)")
        return

    original = git(["rev-parse", "--abbrev-ref", "HEAD"], capture=True)
    email = git(["config", "user.email"], check=False, capture=True)
    idcfg = [] if email else ["-c", "user.email=fetch@local",
                              "-c", "user.name=Image Fetcher"]

    print(f"\nPushing dump to '{branch}' on '{remote}' (current: {original})...")
    git(["checkout", "-B", branch])
    try:
        git(["add", "-f", out_dir])
        if git(["diff", "--cached", "--quiet"], check=False) == 0:
            print("  nothing new to commit")
        else:
            git(idcfg + ["commit", "-m",
                         f"Instagram image dump ({out_dir})"])
        git(["push", "-u", "--force", remote, branch])
        print(f"\n  Pushed to '{branch}'. Now tell the other agent:")
        print(f"    \"the Instagram images are on branch {branch}\"")
    finally:
        if original and original != "HEAD":
            git(["checkout", original])


def main():
    ap = argparse.ArgumentParser(
        description="Download images from an Instagram profile.")
    ap.add_argument("--user", default="mrqfears")
    ap.add_argument("--out", default="assets/img/instagram-dump")
    ap.add_argument("--max-pages", type=int, default=15,
                    help="timeline pages to walk (count posts each)")
    ap.add_argument("--max-images", type=int, default=300,
                    help="stop after downloading this many images")
    ap.add_argument("--count", type=int, default=33, help="posts per page")
    ap.add_argument("--sleep", type=float, default=1.2,
                    help="seconds between API pages")
    ap.add_argument("--img-sleep", type=float, default=0.1,
                    help="seconds between image downloads")
    ap.add_argument("--insecure", action="store_true",
                    help="skip TLS verification")
    ap.add_argument("--branch", default="instagram-images")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--push", dest="push", action="store_true", default=True)
    ap.add_argument("--no-push", dest="push", action="store_false",
                    help="only download; do not touch git")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    opener = make_opener(insecure=args.insecure)

    print(f"Resolving @{args.user}...")
    user_id, profile = user_id_for(opener, args.user)
    print(f"  id={user_id}  posts={profile.get('edge_owner_to_timeline_media',{}).get('count')}")

    manifest = []
    by_hash = {}
    ok = skipped = fail = 0
    kinds = {"photo": 0, "carousel_photo": 0, "video_poster": 0}

    # profile picture (highest available)
    avatar = profile.get("profile_pic_url_hd") or profile.get("profile_pic_url")
    stills = []
    if avatar:
        stills.append(("avatar", avatar, 0, 0, 0, args.user, None))

    print("Walking timeline...")
    for item in iter_items(opener, user_id, args.max_pages, args.count,
                           args.sleep):
        code = item.get("code")
        cap = caption_of(item)
        taken = item.get("taken_at")
        for kind, url, w, h, idx in stills_from_item(item):
            stills.append((kind, url, w, h, idx, code, cap, taken))

    print(f"\n{len(stills)} stills found. Downloading (cap {args.max_images})...\n")
    for still in stills:
        if ok >= args.max_images:
            print(f"  reached --max-images ({args.max_images}); stopping.")
            break
        kind, url = still[0], still[1]
        w, h, idx, code = still[2], still[3], still[4], still[5]
        cap = still[6] if len(still) > 6 else None
        taken = still[7] if len(still) > 7 else None
        try:
            data = fetch(opener, url, binary=True)
        except Exception as e:
            print(f"  FAIL {code}/{idx} ({e.__class__.__name__})")
            fail += 1
            continue
        h12 = hashlib.sha1(data).hexdigest()[:12]
        if h12 in by_hash:
            skipped += 1
            continue
        ext = ext_from_url(url)
        fname = (f"avatar.{ext}" if kind == "avatar"
                 else filename_for(code, kind, idx, ext))
        path = os.path.join(args.out, fname)
        with open(path, "wb") as f:
            f.write(data)
        by_hash[h12] = fname
        if kind in kinds:
            kinds[kind] += 1
        permalink = (f"https://www.instagram.com/p/{code}/" if code and
                     kind != "avatar" else None)
        manifest.append({
            "file": fname, "kind": kind, "shortcode": code,
            "permalink": permalink, "width": w, "height": h,
            "bytes": len(data), "caption": cap, "taken_at": taken,
        })
        ok += 1
        print(f"  [{ok}] {len(data)//1024:>5} KB  {fname}  ({w}x{h}, {kind})")
        time.sleep(args.img_sleep)

    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump({"user": args.user, "user_id": user_id,
                   "count": kinds, "images": manifest}, f, indent=2)

    print(f"\nDone. {ok} downloaded, {skipped} dup-skipped, {fail} failed.")
    print(f"  photos={kinds['photo']}  carousel_photos={kinds['carousel_photo']}"
          f"  video_posters={kinds['video_poster']}")
    print(f"Files in: {args.out}/   (see manifest.json)")

    if args.push and ok > 0:
        push_dump(args.out, args.branch, args.remote)
    else:
        print("\nNext: another agent can select from these and place them.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
