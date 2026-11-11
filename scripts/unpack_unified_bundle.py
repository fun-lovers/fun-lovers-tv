#!/usr/bin/env python3
"""Safely unpack the generated unified TVBox bundle into the Pages artifact."""
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
        for member in zf.infolist():
            destination = (temp / member.filename).resolve()
            if destination != temp and temp not in destination.parents:
                raise SystemExit(f"Unsafe archive path: {member.filename}")
        zf.extractall(temp)
    source = temp / "unified-deliverable"
    if not (source / "tvbox-unified.json").is_file():
        raise SystemExit("Bundle must contain unified-deliverable/tvbox-unified.json")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
print(f"Unpacked unified TVBox bundle into {target}")
