#!/usr/bin/env python3
"""Inventory netdisk/cloud-drive assets without exporting credential values."""
from __future__ import annotations

import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

KEYWORDS = re.compile(
    r"net.?disk|cloud.?drive|pan|quark|aliyun|alipan|baidu|uc.?drive|"
    r"夸克|网盘|云盘|阿里云盘|百度网盘|UC网盘|迅雷",
    re.IGNORECASE,
)
CREDENTIAL_NAMES = re.compile(
    r"cookie|token|auth|authorization|refresh.?token|access.?token|"
    r"password|passwd|secret|密码|凭据",
    re.IGNORECASE,
)
TEXT_SUFFIXES = {".json", ".js", ".py", ".txt", ".md", ".xml", ".yaml", ".yml"}
MAX_TEXT_BYTES = 2_000_000
MAX_MATCHES = 400


def add_unique(items: list[str], value: str) -> None:
    if value and value.casefold() not in {item.casefold() for item in items}:
        items.append(value[:120])


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def audit_archive(archive: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "archive": archive.name,
        "members_scanned": 0,
        "matched_files": [],
        "json_entries": [],
        "credential_key_names": [],
        "notes": [
            "Credential values are never included in this report.",
            "JSON entries contain field names and value types only.",
            "A keyword match is not proof that a source works or supports account login.",
        ],
    }

    with zipfile.ZipFile(archive) as bundle:
        damaged = bundle.testzip()
        if damaged:
            raise ValueError(f"Corrupt ZIP member: {damaged}")

        for member in bundle.infolist():
            if member.is_dir():
                continue

            report["members_scanned"] += 1
            name = member.filename
            matched_files: list[str] = report["matched_files"]
            if KEYWORDS.search(name):
                add_unique(matched_files, name)

            suffix = Path(name).suffix.lower()
            if member.file_size > MAX_TEXT_BYTES or suffix not in TEXT_SUFFIXES:
                continue

            try:
                raw = bundle.read(member).decode("utf-8", errors="replace")
            except (OSError, RuntimeError, zipfile.BadZipFile):
                continue

            if KEYWORDS.search(raw) and len(matched_files) < MAX_MATCHES:
                add_unique(matched_files, name)

            for match in CREDENTIAL_NAMES.finditer(raw):
                add_unique(report["credential_key_names"], match.group(0))

            if suffix != ".json":
                continue

            try:
                document = json.loads(raw)
            except json.JSONDecodeError:
                continue

            def walk(value: Any, location: str = "$") -> None:
                if isinstance(value, dict):
                    keys = [str(key)[:120] for key in value.keys()]
                    # Values are inspected only in memory to identify relevant entries.
                    searchable = " ".join(keys + [
                        str(item)[:180]
                        for item in value.values()
                        if isinstance(item, (str, int, float, bool))
                    ])
                    for key in keys:
                        if CREDENTIAL_NAMES.search(key):
                            add_unique(report["credential_key_names"], key)

                    if KEYWORDS.search(searchable) and len(report["json_entries"]) < MAX_MATCHES:
                        report["json_entries"].append({
                            "file": name,
                            "path": location,
                            "field_types": {
                                str(key)[:120]: type_name(item)
                                for key, item in value.items()
                            },
                        })

                    for key, child in value.items():
                        walk(child, location + "." + str(key)[:120])
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        walk(child, f"{location}[{index}]")

            walk(document)

    report["matched_files"] = report["matched_files"][:MAX_MATCHES]
    report["json_entries"] = report["json_entries"][:MAX_MATCHES]
    report["credential_key_names"] = report["credential_key_names"][:MAX_MATCHES]
    return report


def self_test() -> None:
    secret_markers = (
        "cookie-value-must-not-leak",
        "access-token-must-not-leak",
        "refresh-token-must-not-leak",
        "session-cookie-must-not-leak",
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        archive = Path(temp_dir) / "sample.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr(
                "sources/netdisk/quark.json",
                json.dumps({
                    "name": "夸克网盘",
                    "search_api": "/api/search",
                    "cookie": secret_markers[0],
                    "access_token": secret_markers[1],
                    "nested": {"refresh_token": secret_markers[2]},
                }, ensure_ascii=False),
            )
            bundle.writestr(
                "sources/cloud/alipan.js",
                "const Cookie = 'session-cookie-must-not-leak';",
            )

        result = audit_archive(archive)
        serialized = json.dumps(result, ensure_ascii=False)
        assert result["members_scanned"] == 2, result
        assert any("quark.json" in item for item in result["matched_files"]), result
        assert any("alipan.js" in item for item in result["matched_files"]), result
        assert any("cookie" in item.casefold() for item in result["credential_key_names"]), result
        assert any("token" in item.casefold() for item in result["credential_key_names"]), result
        assert not any(marker in serialized for marker in secret_markers), serialized

    print("SELF-TEST PASS: ZIP scan works and credential values are not exported.")


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/audit_netdisk_bundle.py <bundle.zip> <report.json>",
            file=sys.stderr,
        )
        return 2

    archive = Path(sys.argv[1])
    output = Path(sys.argv[2])
    if not archive.is_file():
        print(f"Bundle not found: {archive}", file=sys.stderr)
        return 2

    try:
        report = audit_archive(archive)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(f"Unable to audit bundle: {exc}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Scanned {report['members_scanned']} archive members.")
    print("Matched files:")
    for path in report["matched_files"]:
        print(f" - {path}")
    print("Credential field names only:")
    print(", ".join(report["credential_key_names"]) or "(none detected)")
    print(f"JSON entry count: {len(report['json_entries'])}")
    print(f"Report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
