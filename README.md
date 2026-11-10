# fun-lovers-tv

## TVBox 官方公开直播配置

本仓库的直播配置只收录可公开访问、且播放地址位于频道运营方官方域名的 HLS 流。当前收录 CGTN 英语、纪录片、西语、阿语、法语、俄语共 6 路。

### TVBox 导入

在 TVBox 的“配置地址”中填入：

`https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/add-official-tvbox-live/tvbox-selfhost-config.json`

也可单独导入 M3U 直播列表：

`https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/add-official-tvbox-live/live.m3u`

### 合规与可用性说明

- 不收录未经授权的第三方转播、私人 IP 转播、付费频道破解或绕过地域限制的地址。
- iptv-org 等公开索引只作为发现线索；公开可访问不等于获得转播授权。未能逐条确认权利和播放状态的条目不进入播放列表。
- 频道可用性可能受地区、网络、节目排期及官方服务器策略影响。
- 当前环境无法对外部 HLS 完成真实解码测试；配置格式及 URL 形式已检查，但不能承诺每一路在所有网络和设备上都能播放。

审核详情见 `live-source-audit.json`。
