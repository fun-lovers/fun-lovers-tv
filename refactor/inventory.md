# Repository File Inventory

Baseline: `main`, recursive Git tree checked during this audit. 35 tracked files across 16 directories.

| Path | Role |
|---|---|
| `.gitignore` | Root ignore rules |
| `.github/workflows/deploy-drpy2-pages.yml` | drpy2 static Pages build/deploy |
| `.github/workflows/vod-health-check.yml` | VOD endpoint health checks |
| `README.md` | Repository overview |
| `addons/tvbox-live-bestfan.json` | Best-Fan M3U live playlist entry |
| `addons/tvbox-live-iptvorg.json` | IPTV-org country/region M3U entries |
| `addons/tvbox-live-xiongjian.json` | Xiongjian M3U live playlist entry |
| `addons/tvbox-vod-verified.json` | VOD source configuration |
| `analysis/three-pack/README.md` | Three-package analysis notes |
| `analysis/three-pack/DEPLOYMENT.md` | Three-package deployment notes |
| `analysis/three-pack/report.md` | Analysis report |
| `analysis/three-pack/summary.json` | Machine-readable analysis summary |
| `drpy2/.gitignore` | drpy2 ignore rules |
| `drpy2/README.md` | drpy2 project notes |
| `drpy2/config/sources.json` | drpy2 source catalogue |
| `drpy2/scripts/build_static.py` | Static site/config builder |
| `drpy2/public/js/bilibili_open.js` | Bilibili JS rule |
| `drpy2/public/js/dailymotion.js` | Dailymotion JS rule |
| `drpy2/public/js/peertube.js` | PeerTube JS rule |
| `drpy2/public/js/vimeo.js` | Vimeo JS rule |
| `drpy2/public/js/youtube.js` | YouTube JS rule |
| `scripts/check_vod_sources.py` | VOD catalogue/detail endpoint checks |
| `scripts/unpack_unified_bundle.py` | Unified release bundle unpacking |
| `scripts/validate_unified_bundle.py` | Unified bundle structural validation |
| `single-tvbox/LICENSE.cluntop.txt` | Upstream license text |
| `single-tvbox/README.md` | Single TVBox package notes |
| `single-tvbox/box.json` | Single TVBox config entry |
| `single-tvbox/config/source-catalog.json` | Source catalogue |
| `single-tvbox/live/README.md` | Live-source notes |
| `single-tvbox/scripts/validate.py` | Single package validator |
| `single-tvbox/py/douban.py` | Douban Python spider |
| `single-tvbox/py/hongguo.py` | Hongguo short-drama Python spider |
| `single-tvbox/py/ruyishipin.py` | Ruyi video Python spider |
| `ysc-doc-source.json` | Source index and audit ledger |
| `ysc-doc.json` | Source index/config companion |

This is the complete tracked-file inventory observed on the audited main tree. Runtime-generated files and files contained only in release archives are not counted as tracked source files here.
