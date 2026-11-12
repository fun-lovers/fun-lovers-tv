#!/usr/bin/env python3
"""Audit JAR inventory, manifests and Java class-file targets in a unified bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import PurePosixPath
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



def read_uleb128(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data) and shift <= 35:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("invalid DEX ULEB128")


def inspect_dex(data: bytes) -> dict:
    if len(data) < 112 or data[:4] != b"dex\x5cn":
        raise ValueError("invalid DEX header")
    u32 = lambda offset: int.from_bytes(data[offset:offset + 4], "little")
    string_count, string_off = u32(56), u32(60)
    type_count, type_off = u32(64), u32(68)
    class_count = u32(96)
    if string_count > 2_000_000 or type_count > 2_000_000:
        raise ValueError("unreasonable DEX table size")
    if string_off + string_count * 4 > len(data) or type_off + type_count * 4 > len(data):
        raise ValueError("DEX string/type table outside file")

    strings = []
    for index in range(string_count):
        item_off = u32(string_off + index * 4)
        _, start = read_uleb128(data, item_off)
        end = data.find(b"\x5c0", start)
        if end < 0:
            raise ValueError("unterminated DEX string")
        strings.append(data[start:end].decode("utf-8", errors="replace"))

    package_counts = Counter()
    for index in range(type_count):
        string_index = u32(type_off + index * 4)
        if string_index >= len(strings):
            continue
        descriptor = strings[string_index]
        if descriptor.startswith("L") and "/" in descriptor:
            parts = descriptor[1:].split("/")
            package_counts[".".join(parts[:2])] += 1
    return {
        "version": data[4:7].decode("ascii", errors="replace"),
        "fileSizeHeader": u32(32),
        "headerSize": u32(36),
        "classDefinitionCount": class_count,
        "typeCount": type_count,
        "packagePrefixes": dict(package_counts.most_common(20))
    }

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
        "entryCount": 0,
        "entryExtensions": {},
        "dexFiles": [],
        "nativeLibraries": [],
        "sampleEntries": [],
        "error": None,
    }
    try:
        with zipfile.ZipFile(path) as jar:
            bad = jar.testzip()
            if bad:
                item["error"] = f"corrupt entry: {bad}"
                return item
            item["validZip"] = True
            names = jar.namelist()
            item["entryCount"] = len(names)
            extensions = Counter(PurePosixPath(name).suffix.lower() or "[no extension]" for name in names)
            item["entryExtensions"] = dict(sorted(extensions.items()))
            item["sampleEntries"] = names[:20]
            classes = Counter()
            for name in names:
                if name.lower().endswith(".dex"):
                    raw_dex = jar.read(name)
                    dex = {"path": name, "sizeBytes": len(raw_dex)}
                    try:
                        dex.update(inspect_dex(raw_dex))
                    except Exception as exc:
                        dex["headerError"] = str(exc)
                    item["dexFiles"].append(dex)
                elif name.lower().endswith(".so"):
                    parts = name.split("/")
                    known_abis = {"armeabi-v7a", "arm64-v8a", "x86", "x86_64", "riscv64"}
                    abi = next((part for part in parts if part in known_abis), "unknown")
                    item["nativeLibraries"].append({
                        "path": name,
                        "abi": abi,
                        "sizeBytes": jar.getinfo(name).file_size
                    })
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
        "totalJarBytes": sum(item["sizeBytes"] for item in jars),
        "dexVersions": dict(sorted(Counter(
            dex.get("version", "unknown")
            for item in jars for dex in item["dexFiles"]
        ).items())),
        "nativeLibraryCount": sum(len(item["nativeLibraries"]) for item in jars),
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
            f"entries={item['entryCount']} extensions={item['entryExtensions']} "
            f"classes={item['classCount']} dex={item['dexFiles']} "
            f"native={item['nativeLibraries']} "
            f"valid={item['validZip']} sha256={item['sha256']}"
        )
        if item["error"]:
            print(f"  ERROR: {item['error']}")
        if item["sampleEntries"]:
            print(f"  entries sample: {item['sampleEntries']}")
        if item["manifest"]:
            print(f"  manifest: {item['manifest']}")
    for reference in references[:50]:
        print(f"JAR REF {reference['where']}: {reference['value']}")
    if len(references) > 50:
        print(f"... {len(references) - 50} additional JAR references in JSON report")
    if args.output:
        print(f"JAR audit report written to {args.output}")
    if report["invalidJars"]:
        raise SystemExit(f"Invalid JAR file(s): {report['invalidJars']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
