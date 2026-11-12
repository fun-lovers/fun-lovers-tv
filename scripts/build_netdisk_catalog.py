#!/usr/bin/env python3
"""Build a safe catalog of bundled TVBox cloud-drive search sites."""
import json
import re
import sys
from pathlib import Path

MATCH = re.compile(r"net.?disk|cloud.?drive|pan|quark|baidu|aliyun|alipan|uc|网盘|云盘|夸克|百度", re.I)
CLOUD = re.compile(r"网盘|云盘|夸克|百度|UC", re.I)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_netdisk_catalog.py tvbox-unified.json output.json")
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sites = []
    for index, site in enumerate(config.get("sites", [])):
        if site.get("type") != 3:
            continue
        searchable = " ".join(str(site.get(k, "")) for k in ("key", "name", "api", "类型"))
        if not MATCH.search(searchable):
            continue
        sites.append({
            "index": index,
            "key": str(site.get("key", "")),
            "name": str(site.get("name", "")),
            "type": site.get("type"),
            "searchable": site.get("searchable"),
            "quickSearch": site.get("quickSearch"),
            "api": str(site.get("api", "")),
            "cloudDrive": bool(CLOUD.search(str(site.get("name", ""))))
        })
    payload = {
        "version": 1,
        "source": "tvbox-unified.json",
        "total": len(sites),
        "cloudDriveTotal": sum(1 for item in sites if item["cloudDrive"]),
        "sites": sites,
        "note": "Metadata only. ext credentials and secret values are deliberately excluded."
    }
    Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
    Path(sys.argv[2]).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(sites)} TVBox type-3 netdisk-related sites ({payload['cloudDriveTotal']} cloud-drive named entries).")

if __name__ == "__main__":
    main()
