# Runtime and Dependency Map

## 1. drpy2 static deployment
`drpy2/config/sources.json` references JS rules under `drpy2/public/js/`. The Pages workflow installs/obtains the drpy2 runtime, then `drpy2/scripts/build_static.py` assembles static output. The JS rules call host-provided functions such as `request()` and use the TVBox/drpy2 rule contract. They are not standalone Node.js programs.

Observed rule-specific dependencies:
- YouTube: YouTube Data API v3; empty `key` currently makes search return an empty list.
- Vimeo: Vimeo API; empty `token` currently makes search return an empty list.
- PeerTube: configured PeerTube instance API.
- Dailymotion: Dailymotion API.
- Bilibili: inspect remaining implementation and host-specific calls in the next source review.

## 2. single-tvbox Python spiders
- `douban.py`: standard library plus host-provided `base.spider.Spider`; uses Douban Frodo API and existing embedded API/app configuration. The import path now resolves relative to `__file__`, not the process working directory. Preserve existing keys/configuration during refactor.
- `hongguo.py`: `requests`; optional AES backends `cryptography` or `pycryptodome`, with a pure-Python AES fallback; host Spider integration; HTTP fetching, range requests, and local helper server code. Its host import fallback now resolves the package root relative to `__file__`. Runtime support for threads, HTTP server, and crypto modules varies by client.
- `ruyishipin.py`: `requests`, `urllib3`, optional Brotli; has client-specific proxy integration and a loopback proxy URL at `127.0.0.1:9978`. That endpoint is not available on every client. TLS certificate verification is enabled in the refactor branch; verify client networking still works against the upstream site's certificate.

## 3. Source validation
- `scripts/check_vod_sources.py` reads included VOD records from `ysc-doc-source.json` audit data and probes CMS list/detail responses. It checks sample play URL fields but does not fetch media bytes or validate decoder compatibility.
- `scripts/unpack_unified_bundle.py` and `scripts/validate_unified_bundle.py` operate on the unified release archive and its generated output.
- `single-tvbox/scripts/validate.py` validates the single package; cross-check its coverage against the unified validator before relying on it.

## 4. Configuration relationships
- `ysc-doc-source.json`: source review/audit source of truth candidate.
- `ysc-doc.json`: companion published index; exact generation/synchronization contract requires further tracing.
- `addons/*.json`: modular live/VOD inputs.
- `drpy2/config/sources.json`: drpy2-specific rule catalogue.
- `single-tvbox/box.json` and `single-tvbox/config/source-catalog.json`: single-package config and catalogue.
- Unified Pages output is generated from a GitHub Release bundle, not a tracked `unified/` directory on main.

## Validation layers
1. Syntax/parse validation.
2. Dependency/import validation.
3. Host API compatibility validation.
4. Remote endpoint reachability.
5. Media URL/manifest reachability.
6. Actual client playback/decode test.

Passing a lower layer must not be reported as passing a higher layer.
