#!/usr/bin/env python3
"""Validate the static three-package TVBox bundle before GitHub Pages deployment."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/unified").resolve()
main = root / "tvbox-unified.json"
if not main.is_file():
    raise SystemExit(f"Missing unified config: {main}")

def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Invalid JSON {path.relative_to(root)}: {exc}")

def local_resource_path(value):
    """Return the filesystem portion of a TVBox local ext reference.

    TVBox ext values may append a runtime alias after '$', for example
    './config/env.json$闪电'. The alias is not part of the file name.
    """
    path = value[2:]
    path = path.split("$", 1)[0]
    path = path.split("?", 1)[0].split("#", 1)[0]
    return path

def check_paths(value, where):
    missing = []
    if isinstance(value, str) and value.startswith("./"):
        relative = local_resource_path(value)
        target = (root / relative).resolve()
        if root not in target.parents and target != root:
            missing.append((where, value, "path escapes bundle root"))
        elif not target.is_file():
            missing.append((where, value, f"resolved file not found: {relative}"))
    elif isinstance(value, dict):
        for key, child in value.items():
            missing.extend(check_paths(child, f"{where}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            missing.extend(check_paths(child, f"{where}[{index}]"))
    return missing

config = load(main)
sites = config.get("sites")
if not isinstance(sites, list) or not sites:
    raise SystemExit("Unified config has no sites array")
keys = [str(site.get("key", "")) for site in sites]
if len(keys) != len(set(keys)):
    raise SystemExit("Duplicate site keys in unified config")

files = [main, *sorted((root / "jar-configs").glob("*.json"))]
missing = []
for path in files:
    doc = config if path == main else load(path)
    missing.extend(check_paths(doc, path.relative_to(root).as_posix()))

if missing:
    for where, value, reason in missing:
        print(f"MISSING {where}: {value} ({reason})")
    raise SystemExit(f"Found {len(missing)} missing or unsafe local resource reference(s)")

print(
    f"PASS: {len(sites)} unified sites; {len(files)-1} single-JAR configs; "
    "all local references exist (TVBox '$alias' suffixes handled)."
)
