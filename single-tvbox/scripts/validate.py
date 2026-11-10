#!/usr/bin/env python3
"""Static validation for the single-tvbox TVBox configuration."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "box.json"

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def valid_http_url(value: str) -> bool:
    try:
        p = urlsplit(value)
        return p.scheme in ("http", "https") and bool(p.hostname)
    except ValueError:
        return False

def main() -> int:
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {CONFIG}: {exc}")
    if not isinstance(data, dict):
        fail("root must be an object")
    for field in ("sites", "lives", "parses", "rules", "doh", "ijk"):
        if not isinstance(data.get(field), list):
            fail(f"{field} must be an array")
    keys = set()
    for i, site in enumerate(data["sites"]):
        if not isinstance(site, dict):
            fail(f"sites[{i}] must be an object")
        key = site.get("key")
        if not isinstance(key, str) or not key:
            fail(f"sites[{i}] missing key")
        if key in keys:
            fail(f"duplicate site key: {key}")
        keys.add(key)
        kind = site.get("type")
        if kind == 1 and not valid_http_url(site.get("api", "")):
            fail(f"sites[{i}] invalid MacCMS API URL")
        if kind == 3:
            api = site.get("api", "")
            if not isinstance(api, str) or not api.startswith("./"):
                fail(f"sites[{i}] script api must be a relative path")
            script = (ROOT / api[2:]).resolve()
            if ROOT.resolve() not in script.parents or not script.is_file():
                fail(f"sites[{i}] script file missing or escapes package: {api}")
    for i, live in enumerate(data["lives"]):
        if not valid_http_url(live.get("url", "")):
            fail(f"lives[{i}] invalid playlist URL")
    for i, item in enumerate(data["doh"]):
        if not valid_http_url(item.get("url", "")):
            fail(f"doh[{i}] invalid DoH URL")
    print(f"OK: {len(data['sites'])} sites, {len(data['lives'])} live playlists, {len(keys)} unique keys")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
