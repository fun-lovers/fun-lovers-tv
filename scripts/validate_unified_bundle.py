#!/usr/bin/env python3
"""Validate the unified TVBox bundle and its local resource references."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def local_resource_path(value: str) -> str:
    """Strip the TVBox ext alias and URL suffix from a relative local path.

    Examples:
      ./config/env.json$闪电 -> config/env.json
      ./config/env.json?x=1#fragment$至臻 -> config/env.json
    """
    path = value[2:]
    path = path.split("$", 1)[0]
    path = path.split("?", 1)[0].split("#", 1)[0]
    return path


def check_local_reference(root: Path, value: str) -> str | None:
    relative = local_resource_path(value)
    target = (root / relative).resolve()
    resolved_root = root.resolve()
    if target != resolved_root and resolved_root not in target.parents:
        return "path escapes bundle root"
    if not target.is_file():
        return f"resolved file not found: {relative}"
    return None


def check_paths(value: Any, where: str, root: Path) -> list[tuple[str, str, str]]:
    missing: list[tuple[str, str, str]] = []
    if isinstance(value, str) and value.startswith("./"):
        reason = check_local_reference(root, value)
        if reason:
            missing.append((where, value, reason))
    elif isinstance(value, dict):
        for key, child in value.items():
            missing.extend(check_paths(child, f"{where}.{key}", root))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            missing.extend(check_paths(child, f"{where}[{index}]", root))
    return missing


def load_json(path: Path, root: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        try:
            label = path.relative_to(root).as_posix()
        except ValueError:
            label = str(path)
        raise ValueError(f"Invalid JSON {label}: {exc}") from exc


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir).resolve()
        target = root / "sources" / "星微" / "config" / "env.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"ok":true}\n', encoding="utf-8")

        alias_refs = [
            "./sources/星微/config/env.json$闪电",
            "./sources/星微/config/env.json?from=tvbox#ext$至臻",
        ]
        for reference in alias_refs:
            reason = check_local_reference(root, reference)
            assert reason is None, (reference, reason)

        escaped = check_local_reference(root, "./../../outside.json$别名")
        assert escaped == "path escapes bundle root", escaped

        missing = check_local_reference(root, "./missing.json$别名")
        assert missing and missing.startswith("resolved file not found"), missing

    print("SELF-TEST PASS: TVBox '$alias' paths, query suffixes, missing files, and traversal.")


def validate(root: Path) -> None:
    root = root.resolve()
    main = root / "tvbox-unified.json"
    if not main.is_file():
        raise ValueError(f"Missing unified config: {main}")

    config = load_json(main, root)
    sites = config.get("sites") if isinstance(config, dict) else None
    if not isinstance(sites, list) or not sites:
        raise ValueError("Unified config has no non-empty sites array")

    keys = [str(site.get("key", "")) for site in sites if isinstance(site, dict)]
    if len(keys) != len(sites):
        raise ValueError("Every site entry must be a JSON object")
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate site keys in unified config")

    jar_dir = root / "jar-configs"
    files = [main]
    if jar_dir.exists():
        if not jar_dir.is_dir():
            raise ValueError("jar-configs exists but is not a directory")
        files.extend(sorted(jar_dir.glob("*.json")))

    missing: list[tuple[str, str, str]] = []
    for path in files:
        document = config if path == main else load_json(path, root)
        missing.extend(check_paths(document, path.relative_to(root).as_posix(), root))

    if missing:
        for where, value, reason in missing:
            print(f"MISSING {where}: {value} ({reason})")
        raise ValueError(f"Found {len(missing)} missing or unsafe local resource reference(s)")

    print(
        f"PASS: {len(sites)} unified sites; {len(files) - 1} single-JAR configs; "
        "all local references exist (TVBox '$alias' suffixes handled)."
    )


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0
    if len(sys.argv) > 2:
        print("Usage: python scripts/validate_unified_bundle.py [bundle-root|--self-test]", file=sys.stderr)
        return 2

    root = Path(sys.argv[1] if len(sys.argv) == 2 else "dist/unified")
    try:
        validate(root)
    except (OSError, ValueError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
