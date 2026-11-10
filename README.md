# fun-lovers-tv

## TVBox 配置（最近 15 天活跃仓库筛选）

配置文件仅使用位于频道运营方官方域名的 CGTN HLS 地址。没有将第三方聚合仓库的直播列表整份导入。

### 导入 TVBox

配置地址：

`https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/refresh-tvbox-active-15d/tvbox-selfhost-config.json`

独立 M3U：

`https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/refresh-tvbox-active-15d/live.m3u`

### 最近 15 天仓库筛选

筛选区间：2026-10-26 至 2026-11-10（按 GitHub 最新提交时间）。

共检出 7 个近期活跃仓库，其中 5 个为 TVBox 配置候选。逐一读取候选配置后，发现其直播区包含第三方聚合源、版权状态不明的流、付费频道分组或内网地址，因此未整仓导入。仓库活跃不等于直播授权。

- iptv-org/iptv：仅作开源索引参考，不批量导入。
- fanmingming/live：仅作台标/EPG辅助资源。
- 其余近期活跃候选仓库：列入审核记录，未自动导入。

### 播放验证说明

JSON 语法、M3U 结构及 HTTPS URL 格式已检查。当前执行环境未完成外部 HLS 拉流及 TVBox 设备解码测试，因此不宣称所有频道已实播验证。频道可能受地区、网络及官方排期影响。

审核详情见 `live-source-audit.json`。
