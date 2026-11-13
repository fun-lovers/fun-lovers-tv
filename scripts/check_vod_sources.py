#!/usr/bin/env python3
"""Check TVBox MacCMS-style VOD source APIs and produce JSON/Markdown reports.

This checker validates catalog/detail responses and the shape of one sample play
URL. It deliberately does not fetch media bytes or claim that playback succeeds.
Only HTTP(S) public hostnames are accepted for configured CMS API endpoints.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import ipaddress
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = "fun-lovers-tv-vod-health/1.0 (+https://github.com/fun-lovers/fun-lovers-tv)"
TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_WORKERS = 8


def safe_http_url(value: Any) -> tuple[bool, str]:
    if not isinstance(value, str) or not value.strip():
        return False, "missing URL"
    try:
        parsed = urllib.parse.urlsplit(value.strip())
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False, "URL must use http(s) and include a hostname"
        if parsed.username or parsed.password:
            return False, "embedded URL credentials are not allowed"
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return False, "local hostname is not allowed"
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                return False, "non-public IP address is not allowed"
        except ValueError:
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
            except OSError as exc:
                return False, f"DNS lookup failed: {exc.__class__.__name__}"
            if not addresses:
                return False, "hostname resolved to no addresses"
            for address in addresses:
                if not ipaddress.ip_address(address).is_global:
                    return False, "hostname resolves to a non-public IP address"
        return True, ""
    except ValueError as exc:
        return False, f"invalid URL: {exc}"


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed, why = safe_http_url(newurl)
        if not allowed:
            raise urllib.error.HTTPError(newurl, code, f"redirect blocked: {why}", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


SAFE_OPENER = urllib.request.build_opener(SafeRedirectHandler)


def request_json(url: str) -> tuple[dict[str, Any] | None, int | None, str | None]:
    allowed, why = safe_http_url(url)
    if not allowed:
        return None, None, why
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/plain;q=0.8, */*;q=0.5"})
    try:
        with SAFE_OPENER.open(req, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", 200)
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            return None, status, "response exceeded 2 MiB limit"
        text = body.decode("utf-8-sig", errors="strict")
        data = json.loads(text)
        if not isinstance(data, dict):
            return None, status, "JSON root is not an object"
        return data, status, None
    except urllib.error.HTTPError as exc:
        return None, exc.code, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return None, None, "request timed out"
        return None, None, f"network error: {reason.__class__.__name__}"
    except (TimeoutError, socket.timeout):
        return None, None, "request timed out"
    except UnicodeDecodeError:
        return None, None, "response is not UTF-8"
    except json.JSONDecodeError as exc:
        return None, None, f"invalid JSON at character {exc.pos}"
    except Exception as exc:
        return None, None, f"request error: {exc.__class__.__name__}"


def with_query(api: str, **params: Any) -> str:
    parsed = urllib.parse.urlsplit(api)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: str(value) for key, value in params.items()})
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment))


def extract_list(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    value: Any = payload.get("list")
    if value is None:
        value = payload.get("data")
        if isinstance(value, dict):
            value = value.get("list")
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    return None


def extract_play_url(item: dict[str, Any]) -> tuple[str | None, str]:
    for key in ("vod_play_url", "play_url", "url", "playUrl"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            match = re.search(r"https?://[^\s$#|]+", value.strip(), re.IGNORECASE)
            if match:
                candidate = match.group(0).rstrip("),;\"'")
                parsed = urllib.parse.urlsplit(candidate)
                if parsed.scheme in ("http", "https") and parsed.hostname:
                    return candidate, "http_url_found"
                return None, "play_field_present_but_url_invalid"
            return None, "play_field_present_but_no_http_url"
    return None, "play_field_missing"


def load_sources(index: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    audit = index.get("audit", [])
    if not isinstance(audit, list):
        raise ValueError("index.audit must be an array")
    vod_entries = [entry for entry in audit if isinstance(entry, dict) and entry.get("sourceType") == "vod" and entry.get("decision") == "included"]
    unique: dict[str, dict[str, Any]] = {}
    config_errors: list[dict[str, Any]] = []
    config_timeouts: list[dict[str, Any]] = []
    for entry in vod_entries:
        source_url = entry.get("url")
        ok, why = safe_http_url(source_url)
        if not ok:
            config_errors.append({"source": entry.get("name", "unknown"), "stage": "source_config_url", "error": why})
            continue
        config, http_status, error = request_json(source_url)
        if error:
            record = {"source": entry.get("name", "unknown"), "stage": "source_config_fetch", "http_status": http_status, "error": error}
            if error == "request timed out":
                config_timeouts.append(record)
            else:
                config_errors.append(record)
            continue
        sites = config.get("sites") if config else None
        if not isinstance(sites, list):
            config_errors.append({"source": entry.get("name", "unknown"), "stage": "source_config_schema", "error": "sites is not an array"})
            continue
        for site in sites:
            if not isinstance(site, dict):
                config_errors.append({"source": entry.get("name", "unknown"), "stage": "site_schema", "error": "site entry is not an object"})
                continue
            api = site.get("api")
            if not isinstance(api, str) or not api.strip():
                config_errors.append({"source": entry.get("name", "unknown"), "site": site.get("name"), "stage": "site_schema", "error": "api is missing"})
                continue
            key = api.strip()
            if key not in unique:
                unique[key] = {"api": key, "sites": [], "sources": []}
            unique[key]["sites"].append({"name": site.get("name", "unnamed"), "key": site.get("key"), "type": site.get("type")})
            if entry.get("name") not in unique[key]["sources"]:
                unique[key]["sources"].append(entry.get("name", "unknown"))
    return list(unique.values()), config_errors, config_timeouts


def check_api(item: dict[str, Any]) -> dict[str, Any]:
    api = item["api"]
    result: dict[str, Any] = {
        "api": api,
        "host": urllib.parse.urlsplit(api).hostname,
        "sites": item["sites"],
        "sources": item["sources"],
        "site_type_ok": all(site.get("type") == 1 for site in item["sites"]),
        "list_status": "not_checked",
        "detail_status": "not_checked",
        "play_url_status": "not_checked",
        "sample_play_url": None,
    }
    list_data, list_http_status, list_error = request_json(with_query(api, ac="list", pg=1))
    result["list_http_status"] = list_http_status
    if list_error:
        result["list_status"] = "timeout" if list_error == "request timed out" else "unreachable_or_invalid"
        result["detail_status"] = "not_checked_timeout" if list_error == "request timed out" else "not_checked"
        result["play_url_status"] = "not_checked_timeout" if list_error == "request timed out" else "not_checked"
        result["error"] = list_error
        return result
    rows = extract_list(list_data or {})
    if rows is None:
        result["list_status"] = "unexpected_schema"
        result["error"] = "response JSON has no list array"
        return result
    if not rows:
        result["list_status"] = "empty_catalog"
        result["list_count"] = 0
        result["detail_status"] = "not_tested_empty_catalog"
        result["play_url_status"] = "not_tested_empty_catalog"
        return result
    result["list_status"] = "ok"
    result["list_count"] = len(rows)
    first = rows[0]
    vod_id = first.get("vod_id", first.get("id"))
    if vod_id is None:
        result["detail_status"] = "missing_vod_id"
        play_url, play_status = extract_play_url(first)
        result["play_url_status"] = play_status
        result["sample_play_url"] = play_url
        return result
    detail_data, detail_http_status, detail_error = request_json(with_query(api, ac="detail", ids=vod_id))
    result["detail_http_status"] = detail_http_status
    if detail_error:
        result["detail_status"] = "timeout" if detail_error == "request timed out" else "unavailable_or_invalid"
        result["play_url_status"] = "not_checked_timeout" if detail_error == "request timed out" else "not_checked"
        result["detail_error"] = detail_error
        return result
    detail_rows = extract_list(detail_data or {})
    if detail_rows is None:
        result["detail_status"] = "unexpected_schema"
        result["detail_error"] = "detail response JSON has no list array"
        return result
    if not detail_rows:
        result["detail_status"] = "empty_detail"
        result["play_url_status"] = "not_tested_empty_detail"
        return result
    result["detail_status"] = "ok"
    result["detail_count"] = len(detail_rows)
    play_url, play_status = extract_play_url(detail_rows[0])
    result["play_url_status"] = play_status
    result["sample_play_url"] = play_url
    return result


def status_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        key = result.get("list_status", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# TVBox VOD API health check",
        "",
        f"- Checked at: {report['checked_at']} UTC",
        f"- Configured sites: {summary['site_entries']}",
        f"- Unique API endpoints: {summary['unique_api_endpoints']}",
        f"- Catalog APIs responding with a list: {summary['list_ok']}",
        f"- Detail APIs responding with data: {summary['detail_ok']}",
        f"- Detail samples containing an HTTP(S) play URL: {summary['play_url_present']}",
        f"- Config/schema errors: {summary['config_errors']}",
        f"- Timeouts (non-fatal): {summary.get('timeout_count', 0)}",
        "",
        "> Note: an HTTP(S) play URL being present is only a format check; this workflow does not fetch media bytes or guarantee playback in TVBox.",
        "",
        "| API host | Site(s) | Catalog | Detail | Play URL field | Notes |",
        "|---|---|---:|---:|---:|---|",
    ]
    for result in report["results"]:
        names = ", ".join(str(site.get("name", "")) for site in result.get("sites", []))
        note = result.get("error") or result.get("detail_error") or ""
        note = str(note).replace("|", "\\|")
        lines.append(f"| {result.get('host') or ''} | {names} | {result.get('list_status')} | {result.get('detail_status')} | {result.get('play_url_status')} | {note} |")
    if report.get("config_timeouts"):
        lines.extend(["", "## Timeouts (non-fatal)", ""])
        for timeout in report["config_timeouts"]:
            lines.append(f"- {timeout.get('source', '')} / {timeout.get('stage', '')}: {timeout.get('error', 'request timed out')}")
    api_timeouts = [item for item in report["results"] if item.get("list_status") == "timeout" or item.get("detail_status") == "timeout"]
    if api_timeouts:
        lines.extend(["", "## API timeouts (non-fatal)", ""])
        for item in api_timeouts:
            sites = ", ".join(str(site.get("name", "")) for site in item.get("sites", []))
            stage = "catalog" if item.get("list_status") == "timeout" else "detail"
            lines.append(f"- {sites} / {stage}: request timed out ({item.get('api', '')})")
    if report["config_errors"]:
        lines.extend(["", "## Configuration errors", ""])
        for error in report["config_errors"]:
            lines.append(f"- {error.get('source', '')} / {error.get('stage', '')}: {error.get('error', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="ysc-doc-source.json", help="repository source index JSON")
    parser.add_argument("--json-out", default="reports/vod-health.json")
    parser.add_argument("--markdown-out", default="reports/vod-health.md")
    parser.add_argument("--summary", default=None, help="optional GitHub Actions step summary file")
    parser.add_argument("--fail-on-unavailable", action="store_true", help="return a non-zero status if any configured API check fails")
    args = parser.parse_args()

    index = json.loads(Path(args.index).read_text(encoding="utf-8"))
    apis, config_errors, config_timeouts = load_sources(index)
    site_entries = sum(len(item["sites"]) for item in apis)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(check_api, apis))
    summary = {
        "source_configs": len([entry for entry in index.get("audit", []) if isinstance(entry, dict) and entry.get("sourceType") == "vod" and entry.get("decision") == "included"]),
        "site_entries": site_entries,
        "unique_api_endpoints": len(apis),
        "list_ok": sum(item.get("list_status") == "ok" for item in results),
        "detail_ok": sum(item.get("detail_status") == "ok" for item in results),
        "play_url_present": sum(item.get("play_url_status") == "http_url_found" for item in results),
        "config_errors": len(config_errors),
        "config_timeouts": len(config_timeouts),
        "api_timeouts": sum(item.get("list_status") == "timeout" or item.get("detail_status") == "timeout" for item in results),
        "timeout_count": len(config_timeouts) + sum(item.get("list_status") == "timeout" or item.get("detail_status") == "timeout" for item in results),
        "list_status_counts": status_counts(results),
    }
    report = {
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "checker_version": "1.0",
        "summary": summary,
        "config_errors": config_errors,
        "config_timeouts": config_timeouts,
        "results": results,
        "limitations": [
            "A sample HTTP(S) play URL is checked for presence and syntax only.",
            "Media bytes are not fetched; successful playback in TVBox is not guaranteed.",
            "Provider-side rate limits, geo restrictions, and temporary network errors may affect results.",
        ],
    }
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    md_text = markdown_report(report)
    for output_path, content in ((args.json_out, json_text), (args.markdown_out, md_text)):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if args.summary:
        Path(args.summary).write_text(md_text, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    has_failures = bool(config_errors) or any(
        item.get("list_status") not in ("ok", "timeout")
        or item.get("detail_status") not in ("ok", "timeout", "not_checked_timeout")
        or item.get("play_url_status") not in ("http_url_found", "not_checked_timeout")
        for item in results
    )
    return 2 if args.fail_on_unavailable and has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
