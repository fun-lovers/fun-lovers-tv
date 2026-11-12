#!/usr/bin/env python3
"""Safely unpack the unified TVBox bundle with traversal and resource limits."""
from __future__ import annotations

import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

MAX_ENTRIES = 50_000
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000


def validate_archive(zf: zipfile.ZipFile, temp_root: Path) -> None:
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        raise SystemExit(f"Archive has too many entries: {len(infos)} > {MAX_ENTRIES}")

    total_size = 0
    seen = set()
    for member in infos:
        name = member.filename
        if not name or "\\" in name:
            raise SystemExit(f"Unsafe archive member name: {name!r}")
        if name in seen:
            raise SystemExit(f"Duplicate archive member: {name}")
        seen.add(name)

        destination = (temp_root / name).resolve()
        if destination != temp_root and temp_root not in destination.parents:
            raise SystemExit(f"Unsafe archive path: {name}")
        if stat.S_ISLNK(member.external_attr >> 16):
            raise SystemExit(f"Symbolic links are not allowed in bundle: {name}")

        if member.file_size > MAX_MEMBER_BYTES:
            raise SystemExit(
                f"Archive member too large: {name} ({member.file_size} bytes)"
            )
        total_size += member.file_size
        if total_size > MAX_TOTAL_BYTES:
            raise SystemExit(
                f"Archive expands beyond limit: {total_size} > {MAX_TOTAL_BYTES} bytes"
            )
        if member.file_size and not member.compress_size:
            raise SystemExit(f"Invalid compressed size for archive member: {name}")
        if member.compress_size:
            ratio = member.file_size / member.compress_size
            if ratio > MAX_COMPRESSION_RATIO:
                raise SystemExit(
                    f"Suspicious compression ratio for {name}: {ratio:.1f}"
                )


def main() -> int:
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
            validate_archive(zf, temp)
            zf.extractall(temp)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
