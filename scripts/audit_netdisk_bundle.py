#!/usr/bin/env python3
"""Inventory existing netdisk/cloud-drive assets without exposing credential values."""
import json, re, sys, zipfile
from pathlib import Path

archive = Path(sys.argv[1])
out = Path(sys.argv[2])
keywords = re.compile(r"net.?disk|cloud.?drive|pan|quark|aliyun|alipan|baidu|uc.?drive|夸克|网盘|云盘|阿里云盘|百度网盘|UC网盘|迅雷", re.I)
credential_names = re.compile(r"(cookie|token|auth|authorization|refresh.?token|access.?token|密码|凭据)", re.I)
sensitive_values = re.compile(r"(?i)(cookie|token|authorization|password|secret)\s*[:=]\s*['"][^'"]{8,}['"]")
MAX_TEXT = 2_000_000
MAX_MATCHES = 400
report = {"archive": archive.name, "members_scanned": 0, "matched_files": [], "json_entries": [], "credential_key_names": [], "notes": [
    "This report records credential field names only; it never records credential values.",
    "A matching filename or keyword is not proof that the source works or that the account flow is supported."
]}
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        if info.is_dir(): continue
        report["members_scanned"] += 1
        name = info.filename
        if keywords.search(name):
            report["matched_files"].append(name)
        if info.file_size > MAX_TEXT or not name.lower().endswith((".json",".js",".py",".txt",".md",".xml")):
            continue
        try: raw = z.read(info).decode("utf-8", "ignore")
        except Exception: continue
        if keywords.search(raw) and len(report["matched_files"]) < MAX_MATCHES:
            if name not in report["matched_files"]: report["matched_files"].append(name)
        for m in credential_names.finditer(raw):
            key = m.group(0)
            if key.lower() not in [x.lower() for x in report["credential_key_names"]]:
                report["credential_key_names"].append(key[:80])
        if name.lower().endswith(".json"):
            try: doc = json.loads(raw)
            except Exception: continue
            def walk(v, p="$"):
                if isinstance(v, dict):
                    flat = " ".join(str(k)+":"+str(x)[:180] for k,x in v.items() if isinstance(x,(str,int,float,bool)))
                    if keywords.search(flat) and len(report["json_entries"]) < MAX_MATCHES:
                        safe = {}
                        for k,x in v.items():
                            if credential_names.search(str(k)):
                                safe[k] = "<redacted: field name only>"
                            elif isinstance(x,(str,int,float,bool)) or x is None:
                                s=str(x)
                                safe[k] = s[:240]
                        report["json_entries"].append({"file":name,"path":p,"entry":safe})
                    for k,x in v.items(): walk(x,p+"."+str(k))
                elif isinstance(v,list):
                    for i,x in enumerate(v): walk(x,p+f"[{i}]")
            walk(doc)
report["matched_files"] = report["matched_files"][:MAX_MATCHES]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Scanned {report['members_scanned']} archive members")
print("Matched files:")
for p in report["matched_files"]: print(" - "+p)
print("Credential field names (values never printed): "+", ".join(report["credential_key_names"]))
print("JSON source entries: "+str(len(report["json_entries"])))
print("Report written to "+str(out))
