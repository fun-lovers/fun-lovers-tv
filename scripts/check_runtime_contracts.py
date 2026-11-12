#!/usr/bin/env python3
"""Static syntax and dependency-contract checks for the TVBox repository."""
from __future__ import annotations

import ast
import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "refactor/runtime-matrix.json"
CATALOG = ROOT / "drpy2/config/sources.json"
PYTHON_SPIDERS = [
    ROOT / "single-tvbox/py/douban.py",
    ROOT / "single-tvbox/py/hongguo.py",
    ROOT / "single-tvbox/py/ruyishipin.py",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    declared = matrix.get("spiders", {})
    if not isinstance(declared, dict):
        fail("runtime-matrix.json: spiders must be an object")

    for path in PYTHON_SPIDERS:
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            fail(f"missing Python spider: {rel}")
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=rel)
            py_compile.compile(str(path), doraise=True, cfile="/tmp/tvbox-check.pyc")
        except (SyntaxError, py_compile.PyCompileError) as exc:
            fail(f"Python syntax error in {rel}: {exc}")

        if rel not in declared:
            fail(f"{rel} is missing from runtime-matrix.json")
        entry = declared[rel]
        third_party = set(entry.get("thirdParty", []))
        optional = set(entry.get("optionalThirdParty", [])) | set(entry.get("optionalImportRoots", []))
        known_host_roots = {"base", "com"}
        imported = set()
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])

        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        external = imported - stdlib - known_host_roots
        undeclared = external - third_party - optional
        if undeclared:
            fail(f"{rel} has undeclared external imports: {', '.join(sorted(undeclared))}")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(catalog, list) or not catalog:
        fail("drpy2/config/sources.json must be a non-empty array")
    seen = set()
    for item in catalog:
        key = item.get("key")
        rule_file = item.get("rule_file")
        if not key or key in seen:
            fail(f"missing or duplicate drpy2 source key: {key!r}")
        seen.add(key)
        js_path = ROOT / "drpy2/public/js" / str(rule_file)
        if not js_path.is_file():
            fail(f"missing drpy2 JS rule for {key}: {rule_file}")

    print(f"PASS: {len(PYTHON_SPIDERS)} Python spiders, {len(catalog)} drpy2 rules, dependency matrix consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
