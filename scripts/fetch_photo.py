#!/usr/bin/env python3
"""Fetch one license-safe stock photo for a deck (stdlib only, Tier 3).

Usage:
  fetch_photo.py "QUERY" OUT_DIR

Searches Openverse restricted to CC0/Public-Domain marks, downloads the best
match into OUT_DIR, and prints a JSON manifest on stdout:
  {"path": ..., "attribution": ..., "license": ..., "url": ...}

Never called by build_pptx.py — the skill runs this BEFORE building and puts
the returned path into a "photo" element; if this exits non-zero the skill
simply omits the path and the deck degrades to the gradient field (SL-23).
Openverse license metadata is community-sourced and not warranted; the
attribution line must be kept on the slide.

Exit codes: 0 ok · 1 usage · 4 unavailable (no network / no results /
download failed) — 4 is the "fall back silently" signal.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("VIBE_OPENVERSE_API",
                     "https://api.openverse.org/v1/images/")
TIMEOUT = 15
UA = {"User-Agent": "vibe-plugin-fetch-photo/1.0"}


def unavailable(msg):
    print(f"fetch_photo: {msg}", file=sys.stderr)
    sys.exit(4)


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    query, out_dir = argv
    params = urllib.parse.urlencode({
        "q": query, "license": "cc0,pdm", "page_size": 10,
        "fields": "id,title,creator,license,license_version,url,"
                  "foreign_landing_url,filetype"})
    try:
        req = urllib.request.Request(f"{API}?{params}", headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            results = json.load(resp).get("results") or []
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        unavailable(f"Openverse unreachable: {exc}")

    for r in results:
        url = r.get("url")
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
        except (urllib.error.URLError, OSError, TimeoutError):
            continue  # try the next result
        if data[:8] != b"\x89PNG\r\n\x1a\n" and data[:3] != b"\xff\xd8\xff":
            continue  # only formats the builder embeds
        ext = "png" if data[:4] == b"\x89PNG"[:4] else "jpeg"
        slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-") or "photo"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{slug}-{r.get('id', 'x')[:8]}.{ext}")
        with open(path, "wb") as fh:
            fh.write(data)
        licence = f"{r.get('license', '?').upper()} {r.get('license_version', '')}".strip()
        attribution = (f"{r.get('title') or 'Photo'} — "
                       f"{r.get('creator') or 'unknown'} ({licence}, "
                       "via Openverse)")
        print(json.dumps({"path": path, "attribution": attribution,
                          "license": licence,
                          "url": r.get("foreign_landing_url") or url}))
        return 0
    unavailable("no usable CC0/PD result")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
