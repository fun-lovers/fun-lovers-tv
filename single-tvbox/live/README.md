# 直播资源目录

本目录的直播入口统一写入上级 `box.json` 的 `lives` 数组。资源按以下维度组织：

- 国家：CN、JP、HK、TW、KR、US、UK、CA、AU、SG、DE、FR、IT、ES
- 分类：新闻、教育、纪录片、文化、儿童、音乐、体育、电影
- 语言：英语、日语、中文、韩语
- 地区：亚洲、亚太、欧洲
- 精选：Free-TV/IPTV

## EPG

XMLTV：`https://iptv-org.github.io/epg/guides/all.xml`

EPG 匹配依赖 M3U 的 `tvg-id` 与 XMLTV 中的 channel id。并非每个频道都有节目单。

## 维护原则

- 优先保留上游项目持续维护的 M3U URL，不把动态流地址复制进仓库。
- 上游 playlist 能下载不代表其中每个频道都能播放。
- 遇到版权方投诉、明显未经授权的转播或失效链接，应及时移除。
- 不把付费频道、加密频道或需要绕过 DRM 的资源作为免费源。
