#!/usr/bin/env python3
"""Audit JAR inventory, manifests and Java class-file targets in a unified bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_attributes(raw: bytes) -> dict[str, str]:
    text = raw.decode("utf-8", errors="replace").replace("\r\n ", "")
    attrs = {}
    for line in text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            attrs[key] = value
    return attrs


def inspect_jar(path: Path, root: Path) -> dict:
    item = {
        "path": path.relative_to(root).as_posix(),
        "sizeBytes": path.stat().st_size,
        "sha256": sha256(path),
        "validZip": False,
        "classCount": 0,
        "classMajorVersions": {},
        "manifest": {},
        "nestedJars": [],
        "error": None,
    }
    try:
        with zipfile.ZipFile(path) as jar:
            bad = jar.testzip()
            if bad:
                item["error"] = f"corrupt entry: {bad}"
                return item
            item["validZip"] = True
            classes = Counter()
            for name in jar.namelist():
                if name.endswith(".class"):
                    try:
                        header = jar.read(name)[:8]
                        if len(header) == 8 and header[:4] == b"\xca\xfe\xba\xbe":
                            classes[int.from_bytes(header[6:8], "big")] += 1
                    except Exception:
                        continue
                elif name.lower().endswith(".jar"):
                    item["nestedJars"].append(name)
                elif name.upper() == "META-INF/MANIFEST.MF":
                    item["manifest"] = manifest_attributes(jar.read(name))
            item["classMajorVersions"] = {str(k): v for k, v in sorted(classes.items())}
            item["classCount"] = sum(classes.values())
    except Exception as exc:
        item["error"] = str(exc)
    return item


def collect_jar_references(value, where="root"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(collect_jar_references(child, f"{where}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(collect_jar_references(child, f"{where}[{index}]"))
    elif isinstance(value, str) and ".jar" in value.lower():
        found.append({"where": where, "value": value})
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Extracted unified bundle directory")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = root / "tvbox-unified.json"
    if not config_path.is_file():
        raise SystemExit(f"Missing unified config: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    jar_configs = sorted((root / "jar-configs").rglob("*.json")) if (root / "jar-configs").is_dir() else []
    configs = [config_path, *jar_configs]
    references = []
    for path in configs:
        doc = config if path == config_path else json.loads(path.read_text(encoding="utf-8"))
        references.extend(collect_jar_references(doc, path.relative_to(root).as_posix()))

    jars = [inspect_jar(path, root) for path in sorted(root.rglob("*.jar")) if path.is_file()]
    report = {
        "bundleRoot": root.name,
        "mainConfig": config_path.relative_to(root).as_posix(),
        "siteCount": len(config.get("sites", [])) if isinstance(config.get("sites"), list) else None,
        "jarConfigCount": len(jar_configs),
        "jarCount": len(jars),
        "jarReferences": references,
        "jars": jars,
        "invalidJars": [item["path"] for item in jars if not item["validZip"]],
        "javaClassMajorVersionGuide": {
            "52": "Java 8",
            "55": "Java 11",
            "61": "Java 17",
            "65": "Java 21"
        }
    }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(f"JAR audit: {report['jarCount']} JAR(s), {report['jarConfigCount']} JAR config(s), {len(references)} config reference(s)")
    for item in jars:
        print(
            f"JAR {item['path']} size={item['sizeBytes']} "
            f"classes={item['classCount']} majors={item['classMajorVersions']} "
            f"valid={item['validZip']} sha256={item['sha256']}"
        )
        if item["error"]:
            print(f"  ERROR: {item['error']}")
        for key in ("Main-Class", "Implementation-Version", "Build-Jdk", "Build-Jdk-Spec"):
            if key in item["manifest"]:
                print(f"  {key}: {item['manifest'][key]}")
    if args.output:
        print(f"JAR audit report written to {args.output}")
    if report["invalidJars"]:
        raise SystemExit(f"Invalid JAR file(s): {report['invalidJars']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
