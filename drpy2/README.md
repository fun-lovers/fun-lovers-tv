# drpy2 静态 TVBox 配置

导入地址：

`https://fun-lovers.github.io/fun-lovers-tv/drpy2/tvbox.json`

## 当前独立平台入口

- 哔哩哔哩：官方公开搜索与详情元数据。
- PeerTube：联邦视频平台的公开 REST 搜索；当前使用公开演示实例，实例可能调整或限流。
- YouTube：YouTube Data API v3，需要自行申请并配置 API Key。
- Dailymotion：公开视频 API；若接口要求应用凭据，需要按官方开发者文档配置。
- Vimeo：Vimeo API，需要 public scope access token。

每个平台只有一个检索入口，不再为同一平台拆分电影、动漫等重复入口。

## 凭据说明

YouTube 的 API Key 在 `public/js/youtube.js` 中的 `rule.key` 配置；Vimeo 的 public-scope token 在 `public/js/vimeo.js` 中的 `rule.token` 配置。不要把真实凭据提交到公开仓库。当前仓库是公开 GitHub Pages 静态站点，配置文件和 JS 都是公开可下载的；如果需要长期安全使用密钥，应改用有密钥保护的后端代理。没有填写凭据的平台可能无法返回搜索结果。

## 播放说明

当前规则以官方页面作为播放入口，不提取受保护媒体直链，不绕过登录、地区、会员或 DRM 限制。TVBox 是否能在内置播放器播放取决于客户端对网页 URL 的支持；导入成功不代表每个源都能直接播放。

## 部署

提交到 main 后，GitHub Actions 自动构建并发布 `/drpy2/`。Python 仅在构建阶段运行，不需要在线 FastAPI。
