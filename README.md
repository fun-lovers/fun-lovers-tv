# fun-lovers-tv

TVBox / 影视仓公开配置与源索引。

## TVBox 导入地址

- **多仓索引：** https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/main/ysc-doc-source.json
- **点播源（已实测版，26 个唯一 API）：** https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/main/addons/tvbox-vod-verified.json

## 点播接口健康检查

- 检查程序：`scripts/check_vod_sources.py`
- 自动任务：`.github/workflows/vod-health-check.yml`
- 执行频率：每天 UTC 02:17；修改点播索引或检测程序时也会触发；支持 Actions 手动运行。
- 检查项目：配置 JSON、站点字段、CMS 目录接口（`ac=list`）、详情接口（`ac=detail`）及详情样例中的 HTTP(S) 播放地址字段。
- 报告：GitHub Actions 运行摘要及 JSON/Markdown 工件，保留 30 天；任一目录、详情或样例播放地址检查失败时任务标红，但仍上传报告。

**验证边界：** “样例播放地址存在”仅代表详情响应中含 HTTP(S) 地址，不代表媒体流已下载或已在 TVBox 播放成功。检测结果会受到服务商限流、地区限制和临时网络状况影响。
