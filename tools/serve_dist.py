#!/usr/bin/env python3
"""Serve the build output the way GitHub Pages does.

The site's internal links are extensionless ("/work"); GitHub Pages and
Netlify serve work.html for that request. Plain `python3 -m http.server`
maps URLs straight to files and would 404, so this wrapper adds that one
fallback rule on top of the standard-library handler. No dependencies.

Usage: python3 tools/serve_dist.py [port] [dir]   (defaults: 4599, dist/)
"""
from __future__ import annotations

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4599
DIR = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(_REPO_ROOT, "dist")


class CleanUrlHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        full = super().translate_path(path)
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if not clean.endswith("/") and not os.path.exists(full) and os.path.isfile(full + ".html"):
            return full + ".html"
        return full


def main() -> None:
    handler = partial(CleanUrlHandler, directory=DIR)
    with ThreadingHTTPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Serving {DIR} at http://127.0.0.1:{PORT} (GitHub Pages-style clean URLs)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
