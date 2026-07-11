#!/usr/bin/env python3
"""
Transcode a downloaded Instagram reel into a compact, self-hostable web video +
poster still for the site's vertical reel player (see the "Weekly routine"
section of CLAUDE.md).

Input is a source `.mp4` (e.g. from `tools/fetch_instagram_authed.py --videos`
or `gallery-dl -o videos=true`). Output is a small H.264 MP4 under
`public/assets/video/` plus a JPEG poster under `public/assets/img/`, and a YAML
snippet to paste into the `reels.items` list in `content/ideas.yaml`.

Requires ffmpeg on PATH.

    python3 tools/prepare_reel.py path/to/source.mp4 \
        --name reel-closet-cleanse \
        --caption "Making room in your closet is making room in your life." \
        --permalink https://www.instagram.com/p/XXXX/

Defaults: scales to <=1280 px tall (keeps the 9:16 vertical shape), H.264 + AAC,
CRF 27, faststart (streams before fully downloaded). Aim is < ~3 MB per reel; if
one comes out heavier, raise --crf (e.g. 30) or lower --max-height (e.g. 960).
"""

import argparse
import os
import shutil
import subprocess
import sys


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def main():
    ap = argparse.ArgumentParser(description="Transcode a reel for self-hosting.")
    ap.add_argument("source", help="source .mp4")
    ap.add_argument("--name", required=True, help="output basename, e.g. reel-closet-cleanse")
    ap.add_argument("--caption", default="")
    ap.add_argument("--permalink", default="")
    ap.add_argument("--video-dir", default="public/assets/video")
    ap.add_argument("--poster-dir", default="public/assets/img")
    ap.add_argument("--max-height", type=int, default=1280)
    ap.add_argument("--crf", type=int, default=27)
    ap.add_argument("--poster-at", default="0.8", help="timestamp (s) for the poster frame")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH. Install it (brew install ffmpeg).")
    if not os.path.exists(args.source):
        sys.exit(f"source not found: {args.source}")

    os.makedirs(args.video_dir, exist_ok=True)
    os.makedirs(args.poster_dir, exist_ok=True)
    out_video = os.path.join(args.video_dir, args.name + ".mp4")
    out_poster = os.path.join(args.poster_dir, args.name + ".jpg")

    # even dimensions required by H.264; scale by height, keep aspect.
    vf = f"scale=-2:'min({args.max_height},ih)':flags=lanczos"
    ffmpeg("-i", args.source, "-vf", vf, "-c:v", "libx264", "-profile:v", "high",
           "-crf", str(args.crf), "-preset", "slow", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_video)
    ffmpeg("-ss", args.poster_at, "-i", args.source, "-frames:v", "1",
           "-vf", vf, "-q:v", "3", out_poster)

    vbytes = os.path.getsize(out_video)
    print(f"\nvideo:  {out_video}  ({vbytes // 1024} KB)")
    print(f"poster: {out_poster}  ({os.path.getsize(out_poster) // 1024} KB)")
    if vbytes > 3_500_000:
        print("  note: > ~3.5 MB. Consider --crf 30 or --max-height 960.")

    pub_video = out_video.replace("public/", "", 1)
    pub_poster = out_poster.replace("public/", "", 1)
    print("\nPaste into content/ideas.yaml under reels.items:")
    print(f"""    - poster:
        src: "{pub_poster}"
        alt: "{(args.caption or 'Instagram reel')[:80]}"
        tag: "Reel"
        label: "Instagram reel"
      caption: "{args.caption}"
      permalink: "{args.permalink}"
      videoSrc: "{pub_video}\"""")


if __name__ == "__main__":
    main()
