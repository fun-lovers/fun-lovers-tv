#!/usr/bin/env python3
"""Build and validate a GitHub Pages-hosted drpy2 TVBox config."""
import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", default="dist/drpy2")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    base = args.base_url.rstrip("/")
    catalog = json.loads((root / "config/sources.json").read_text(encoding="utf-8"))
    sites = []
    for item in catalog:
        if not item.get("enabled", True):
            continue
        rule_file = item["rule_file"]
        if not (root / "public/js" / rule_file).is_file():
            raise SystemExit(f"Missing JS rule: {rule_file}")
        sites.append({
            "key": item["key"],
            "name": item["name"],
            "type": 3,
            "api": f"{base}/libs/drpy2.min.js",
            "searchable": int(bool(item.get("searchable", True))),
            "quickSearch": int(bool(item.get("quickSearch", True))),
            "filterable": 0,
            "ext": f"{base}/js/{rule_file}",
        })
    if not sites:
        raise SystemExit("No enabled source in config/sources.json")

    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copytree(root / "public/js", output / "js")
    shutil.copytree(root / "public/libs", output / "libs")
    # Use the standard TVBox schema. Most TVBox clients read "sites", not
    # the non-standard localized key "网站".
    config = {
        "name": "fun-lovers-tv-drpy2",
        "version": 1,
        "description": "drpy2 static configuration hosted on GitHub Pages",
        "spider": "",
        "sites": sites,
        "lives": [],
        "parses": [],
        "rules": [],
    }
    config_path = output / "tvbox.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    runtime = output / "libs/drpy2.min.js"
    if not runtime.is_file() or runtime.stat().st_size < 1000:
        raise SystemExit("drpy2 runtime missing or suspiciously small")
    for site in sites:
        if not (output / "js" / Path(site["ext"]).name).is_file():
            raise SystemExit(f"Published ext missing: {site['ext']}")
        if not site["api"].startswith(base + "/") or not site["ext"].startswith(base + "/"):
            raise SystemExit("Invalid Pages resource URL")
    json.loads(config_path.read_text(encoding="utf-8"))
    print(f"Built {len(sites)} source(s): {base}/tvbox.json")


if __name__ == "__main__":
    main()
