#!/usr/bin/env python3
"""Safely unpack the unified TVBox bundle, accepting a variable top-level ZIP folder."""
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

archive = Path(sys.argv[1] if len(sys.argv) > 1 else "unified-tvbox-bundle.zip")
target = Path(sys.argv[2] if len(sys.argv) > 2 else "dist/unified")
if not archive.is_file():
    raise SystemExit(f"Bundle not found: {archive}")

with tempfile.TemporaryDirectory() as td:
    temp = Path(td).resolve()
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"Corrupt ZIP member: {bad}")
        for member in zf.infolist():
            destination = (temp / member.filename).resolve()
            if destination != temp and temp not in destination.parents:
                raise SystemExit(f"Unsafe archive path: {member.filename}")
        zf.extractall(temp)

    # Do not assume the ZIP has a fixed wrapper directory. Locate the main
    # config and publish its containing directory as the Pages /unified root.
    candidates = [p for p in temp.rglob("tvbox-unified.json") if p.is_file()]
    if len(candidates) != 1:
        shown = [str(p.relative_to(temp)) for p in candidates[:10]]
        raise SystemExit(
            "Expected exactly one tvbox-unified.json in bundle; "
            f"found {len(candidates)}: {shown}"
        )
    source = candidates[0].parent
    if not (source / "jar-configs").is_dir():
        print("WARNING: jar-configs/ directory not found beside the main config.")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)

print(f"Unpacked unified TVBox bundle from {source} into {target}")
