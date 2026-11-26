#!/usr/bin/env python3
"""TVBox / 影视仓 Spider 配置校验、合并、更新与接口检测工具."""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, ipaddress, json, re, socket, sys
import urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

UA = "fun-lovers-tv-spider-manager/1.0"
TIMEOUT = 10
MAX_BYTES = 5 * 1024 * 1024
URL_RE = re.compile(r"https?://[^\s\"'<>|$]+", re.I)

def safe_url(value: Any) -> tuple[bool, str]:
    if not isinstance(value, str) or not value.strip(): return False, "URL 为空"
    try:
        p = urllib.parse.urlsplit(value.strip())
        if p.scheme not in ("http", "https") or not p.hostname: return False, "只允许 HTTP(S) URL"
        if p.username or p.password: return False, "URL 不允许内嵌账号密码"
        host = p.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")): return False, "禁止访问本地主机名"
        try: addresses = [ipaddress.ip_address(host)]
        except ValueError:
            try:
                infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
                addresses = [ipaddress.ip_address(x[4][0]) for x in infos]
            except OSError as exc: return False, f"DNS 解析失败：{type(exc).__name__}"
        if not addresses or any(not x.is_global for x in addresses): return False, "主机解析到非公网 IP，已阻止请求"
        return True, ""
    except ValueError as exc: return False, f"URL 格式错误：{exc}"

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        ok, why = safe_url(newurl)
        if not ok: raise urllib.error.HTTPError(newurl, code, "重定向被阻止：" + why, headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

OPENER = urllib.request.build_opener(SafeRedirect)

def request(url: str, method: str = "GET", timeout: int = TIMEOUT, limit: int = 4096):
    ok, why = safe_url(url)
    if not ok: return None, None, why, url
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "application/json, text/plain, */*", "Range": f"bytes=0-{max(0, limit - 1)}"})
    try:
        with OPENER.open(req, timeout=timeout) as response:
            body = response.read(limit + 1) if method != "HEAD" else b""
            return getattr(response, "status", 200), body, "", response.geturl()
    except urllib.error.HTTPError as exc: return exc.code, b"", f"HTTP {exc.code}", exc.geturl()
    except (TimeoutError, socket.timeout): return None, None, "timeout", url
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (TimeoutError, socket.timeout)): return None, None, "timeout", url
        return None, None, f"network_error:{type(reason).__name__}", url
    except Exception as exc: return None, None, f"request_error:{type(exc).__name__}", url

def load_json(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict): raise ValueError(f"{path}: JSON 顶层必须是对象")
    return data

def detect_format(cfg: dict) -> str:
    if isinstance(cfg.get("sites"), list): return "tvbox_config"
    if isinstance(cfg.get("urls"), list): return "multi_repository_index"
    if isinstance(cfg.get("lives"), list): return "tvbox_live_config"
    return "unknown_json"

def validate(cfg: dict, source: str = "") -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if detect_format(cfg) == "unknown_json": warnings.append(f"{source}: 未识别到常见 TVBox 字段")
    for key in ("sites", "parses", "lives", "urls", "rules", "flags"):
        if key in cfg and not isinstance(cfg[key], list): errors.append(f"{source}: {key} 必须是数组")
    for i, site in enumerate(cfg.get("sites", [])):
        if not isinstance(site, dict):
            errors.append(f"{source}: sites[{i}] 必须是对象"); continue
        if not site.get("key"): warnings.append(f"{source}: sites[{i}] 缺少 key")
        api = site.get("api")
        if not isinstance(api, str) or not api.strip(): errors.append(f"{source}: sites[{i}] 缺少 api")
        if site.get("type") == 3 and isinstance(api, str):
            p = urllib.parse.urlsplit(api)
            if p.scheme not in ("http", "https") and not (Path(source).parent / api).resolve().is_file():
                warnings.append(f"{source}: Python Spider 文件不存在：{api}")
    if "spider" in cfg and cfg["spider"] not in ("", None) and not isinstance(cfg["spider"], str):
        errors.append(f"{source}: spider 必须是字符串 URL")
    for field in ("parses", "lives"):
        for i, item in enumerate(cfg.get(field, [])):
            if not isinstance(item, dict): errors.append(f"{source}: {field}[{i}] 必须是对象"); continue
            if item.get("url") and not isinstance(item.get("url"), str): errors.append(f"{source}: {field}[{i}].url 必须是字符串")
    return errors, warnings

def identity(item: Any, fields: tuple[str, ...]):
    if isinstance(item, dict):
        for field in fields:
            value = item.get(field)
            if value not in (None, ""): return field, str(value).strip()
        return "json", json.dumps(item, ensure_ascii=False, sort_keys=True)
    return "value", str(item).strip()

def merge(configs: list[dict]) -> tuple[dict, dict]:
    if not configs: raise ValueError("至少需要一个配置文件")
    result = dict(configs[0])
    policies = {"sites": ("key", "api"), "parses": ("name", "url"), "lives": ("name", "url"), "rules": ("name", "host"), "urls": (), "flags": ()}
    stats = {}
    for field, keys in policies.items():
        items, seen = [], set()
        for cfg in configs:
            value = cfg.get(field, [])
            if not isinstance(value, list): continue
            for item in value:
                ident = identity(item, keys)
                if ident not in seen: seen.add(ident); items.append(item)
        if items or any(field in cfg for cfg in configs): result[field] = items
        stats[field] = len(items)
    for cfg in configs[1:]:
        for key, value in cfg.items():
            if key not in result: result[key] = value
    return result, stats

def append_url(out: dict, value: Any, label: str):
    if not isinstance(value, str): return
    for url in URL_RE.findall(value):
        url = url.rstrip("),.;]}")
        p = urllib.parse.urlsplit(url)
        if p.scheme in ("http", "https") and p.hostname: out.setdefault(url, label)

def collect_urls(cfg: dict) -> dict[str, str]:
    found = {}
    append_url(found, cfg.get("spider"), "spider JAR")
    for i, site in enumerate(cfg.get("sites", [])):
        if isinstance(site, dict):
            append_url(found, site.get("api"), f"sites[{i}].api")
            append_url(found, site.get("ext"), f"sites[{i}].ext")
    for field in ("parses", "lives"):
        for i, item in enumerate(cfg.get(field, [])):
            if isinstance(item, dict):
                append_url(found, item.get("url"), f"{field}[{i}].url")
                append_url(found, item.get("epg"), f"{field}[{i}].epg")
    for i, item in enumerate(cfg.get("urls", [])):
        append_url(found, item.get("url") if isinstance(item, dict) else item, f"urls[{i}]")
    def walk(obj, path="$"):
        if isinstance(obj, dict):
            for key, value in obj.items():
                child = f"{path}.{key}"
                if key.lower() in {"playurl", "play_url", "vod_play_url"}: append_url(found, value, child)
                walk(value, child)
        elif isinstance(obj, list):
            for i, value in enumerate(obj): walk(value, f"{path}[{i}]")
    walk(cfg)
    return found

def check_one(url: str, source: str, timeout: int):
    status, body, error, final = request(url, "HEAD", timeout)
    method = "HEAD"
    if status in (405, 501) or status is None:
        status, body, error, final = request(url, "GET", timeout, 1024); method = "GET"
    state = "ok" if status is not None and 200 <= status < 400 else ("timeout" if error == "timeout" else "failed")
    return {"url": url, "source": source, "status": status, "state": state, "method": method, "final_url": final, "error": error}

def check_config(cfg: dict, timeout: int, limit: int):
    pairs = list(collect_urls(cfg).items())[:limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda pair: check_one(pair[0], pair[1], timeout), pairs))
    summary = {"total": len(results), "ok": sum(x["state"] == "ok" for x in results), "failed": sum(x["state"] == "failed" for x in results), "timeout": sum(x["state"] == "timeout" for x in results), "skipped": max(0, len(collect_urls(cfg)) - len(results))}
    return {"summary": summary, "results": results, "note": "HTTP 可达不代表 API 协议正确或媒体一定能播放；需在 TVBox/影视仓实测。"}

def update_remote(url: str, output: str, timeout: int):
    status, body, error, final = request(url, "GET", timeout, MAX_BYTES)
    if status is None or not 200 <= status < 400: raise RuntimeError(f"远程配置下载失败：{error or status}")
    if len(body) > MAX_BYTES: raise RuntimeError("远程配置超过 5 MiB 限制")
    data = json.loads(body.decode("utf-8-sig"))
    if not isinstance(data, dict): raise RuntimeError("远程 JSON 顶层必须是对象")
    errors, _ = validate(data, url)
    if errors: raise RuntimeError("远程配置校验失败：" + "; ".join(errors))
    target = Path(output); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return final

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate"); p.add_argument("configs", nargs="+")
    p = sub.add_parser("merge"); p.add_argument("configs", nargs="+"); p.add_argument("-o", "--output", required=True)
    p = sub.add_parser("check"); p.add_argument("configs", nargs="+"); p.add_argument("--json-out", default="reports/spider-health.json"); p.add_argument("--timeout", type=int, default=TIMEOUT); p.add_argument("--limit", type=int, default=200)
    p = sub.add_parser("update"); p.add_argument("url"); p.add_argument("-o", "--output", required=True); p.add_argument("--timeout", type=int, default=TIMEOUT)
    args = parser.parse_args()
    try:
        if args.cmd == "update":
            final = update_remote(args.url, args.output, args.timeout); print(f"远程配置已下载并校验：{final} -> {args.output}"); return 0
        configs = [load_json(x) for x in args.configs]
        if args.cmd == "validate":
            failed = False
            for path, cfg in zip(args.configs, configs):
                errors, warnings = validate(cfg, path); print(f"[{detect_format(cfg)}] {path}")
                for msg in warnings: print("提示:", msg)
                for msg in errors: print("错误:", msg)
                failed |= bool(errors)
            return 1 if failed else 0
        if args.cmd == "merge":
            result, stats = merge(configs); errors, warnings = validate(result, args.output)
            if errors: raise RuntimeError("; ".join(errors))
            out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"合并完成：{out}；" + ", ".join(f"{k}={v}" for k, v in stats.items()))
            for msg in warnings: print("提示:", msg)
            return 0
        reports = []
        for path, cfg in zip(args.configs, configs):
            errors, warnings = validate(cfg, path)
            reports.append({"config": path, "format": detect_format(cfg), "validation_errors": errors, "warnings": warnings, **check_config(cfg, args.timeout, args.limit)})
        report = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "configs": reports,
                  "summary": {"configs": len(reports), "urls": sum(x["summary"]["total"] for x in reports), "ok": sum(x["summary"]["ok"] for x in reports), "failed": sum(x["summary"]["failed"] for x in reports), "timeout": sum(x["summary"]["timeout"] for x in reports)}}
        out = Path(args.json_out); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report["summary"], ensure_ascii=False))
        # 超时只记录、不令工作流失败；格式错误和明确 HTTP 失败仍返回非零。
        return 1 if any(x["validation_errors"] or x["summary"]["failed"] for x in reports) else 0
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
