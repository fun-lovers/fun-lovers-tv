#!/usr/bin/env python3
"""Parse every tracked-project JSON file and reject duplicate object keys."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "__pycache__", "node_modules", "dist"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def main() -> int:
    files = sorted(
        path for path in ROOT.rglob("*.json")
        if not any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts)
    )
    failures = []
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        except Exception as exc:
            failures.append((path.relative_to(ROOT).as_posix(), str(exc)))
    if failures:
        for path, error in failures:
            print(f"ERROR {path}: {error}", file=sys.stderr)
        raise SystemExit(f"{len(failures)} invalid JSON file(s) out of {len(files)}")
    print(f"PASS: {len(files)} JSON file(s) parsed; no duplicate keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
