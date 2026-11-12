#!/usr/bin/env python3
"""Create a credential-safe structural map of cloud-drive JavaScript in a bundle."""
import json, re, sys, zipfile
from pathlib import PurePosixPath

WANTED = re.compile(r"(quark|baidu|uc|pans|wanpan|盘搜)\.js$", re.I)
IMPORTS = re.compile(r"""(?:import\s+.*?from\s*|require\s*\()\s*['"]([^'"]+)['"]""")
FUNCTIONS = re.compile(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>")
CREDENTIALS = re.compile(r"quark_cookie|baidu_cookie|uc_cookie|uc_token|quarkCookie|baiduCookie|ucCookie|access_token|refresh_token|accessToken|refreshToken|Cookie|token|Authorization", re.I)
URLS = re.compile(r"https?://[A-Za-z0-9._:-]+(?:/[^\s'\"<>]*)?")

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_netdisk_js.py bundle.zip report.json")
    rows = []
    with zipfile.ZipFile(sys.argv[1]) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit("corrupt member: " + bad)
        for info in z.infolist():
            if info.is_dir() or not WANTED.search(PurePosixPath(info.filename).name) or info.file_size > 2_000_000:
                continue
            src = z.read(info).decode("utf-8", "replace")
            funcs = set()
            for m in FUNCTIONS.finditer(src):
                funcs.add(m.group(1) or m.group(2))
            urls = set()
            for m in URLS.finditer(src):
                value = m.group(0).split("?", 1)[0].split("#", 1)[0].rstrip(".,);")
                urls.add(value[:240])
            rows.append({
                "file": info.filename,
                "size_bytes": info.file_size,
                "imports": sorted(set(IMPORTS.findall(src)))[:80],
                "function_names": sorted(funcs)[:120],
                "credential_identifiers": sorted(set(m.group(0) for m in CREDENTIALS.finditer(src)), key=str.casefold)[:80],
                "http_endpoints": sorted(urls)[:80]
            })
    out = {"source_count": len(rows), "sources": rows,
           "security_note": "No source lines or credential values are included."}
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if re.search(r"(cookie-value-must-not-leak|access-token-must-not-leak|secret-value-must-not-leak)", text):
        raise SystemExit("credential redaction self-test failed")
    open(sys.argv[2], "w", encoding="utf-8").write(text + "\n")
    print("Scanned", len(rows), "JavaScript source files; no credential values exported.")
if __name__ == "__main__":
    main()
