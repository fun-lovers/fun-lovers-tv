# TVBox Spider 配置管理工具

本目录是 TVBox / 影视仓的 Python 配套管理工具，不是客户端运行时 Spider。TVBox 的 spider 通常指向客户端兼容的 JAR；Python Spider 通常以 sites[].type=3 和 Python 脚本路径配置。本工具不会把 Python 文件伪装成 JAR，也不会执行下载的远程代码。

## 功能

- 自动识别常见 TVBox 配置和多仓索引 JSON。
- 校验 spider、sites、Python Spider 本地文件路径、parses、lives 等字段。
- 多配置合并：sites/parses/lives/rules/urls/flags 去重；第一个配置优先，避免意外替换 Spider 运行时。
- HTTP(S) 可达性检查，含 Spider JAR、站点 API、解析接口、直播/EPG URL，以及配置中显式写出的播放 URL。
- 远程 JSON 安全下载、校验后保存。
- 输出 JSON 报告。超时单独统计且不让 Actions 失败；明确格式错误或非超时 HTTP 错误会标红。

## 本地运行（Python 3.10+，仅标准库）

    python scripts/manage_tvbox.py validate single-tvbox/box.json addons/tvbox-vod-verified.json
    python scripts/manage_tvbox.py check single-tvbox/box.json addons/tvbox-vod-verified.json --json-out reports/spider-health.json
    python scripts/manage_tvbox.py merge single-tvbox/box.json another.json -o dist/merged-tvbox.json
    python scripts/manage_tvbox.py update https://example.org/tvbox.json -o reports/remote-preview.json

## 自动任务

.github/workflows/tvbox-spider-maintenance.yml 每天运行，也支持手动运行。默认只检测仓库中现有配置，不会自动导入未知第三方源、不替换生产配置、不执行 Spider JAR 或 Python Spider。报告作为 Actions Artifact 保存。

## 安全与兼容边界

- 只对 HTTP(S) 公网地址发起探测，阻止 localhost、内网 IP 和重定向到非公网 IP。
- 远程更新仅生成预览文件；需要人工审核后再合并到正式配置。
- HTTP 200 只代表 URL 可达，不代表 API 协议正确、内容有授权或媒体可播放。
- Python Spider 需目标 TVBox 分支支持相应 Python Spider API；不同客户端分支可能存在兼容差异。
- 仅添加你有权使用的官方或明确授权的接口。公开可访问不等于获得转播或内容分发授权。
