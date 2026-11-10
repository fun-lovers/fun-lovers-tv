# 网盘支持（single-tvbox）

本模块为 single-tvbox 增加网盘内容接入能力。采用**独立网盘后端 + TVBox 订阅**的方式，不把网盘 Cookie、Token、账号密码或分享提取码写进公开仓库。

## 能力与边界

主配置 `../box.json` 是静态 TVBox 配置，不能仅靠添加一个 JSON 字段就直接登录并播放所有网盘。不同网盘的鉴权、分享解析、直链有效期和请求头要求不同，需要后端负责账号管理、解析和播放代理。

推荐使用开源项目 [AList-TvBox](https://github.com/power721/alist-tvbox) 作为可选后端。其项目文档列出阿里云盘、百度网盘、夸克、UC、115、123、天翼、移动、迅雷、PikPak、光鸭等账号/分享支持，并提供 TVBox 订阅接口。具体能力受后端版本、网盘驱动、账号权限和地区限制影响。

## 支持平台（后端文档列出的范围）

| 网盘 | 标识 | 接入说明 |
|---|---|---|
| 阿里云盘 | aliyun | 账号 Token / 分享 |
| 百度网盘 | baidu | 账号 / 分享 |
| 夸克网盘 | quark | Cookie / 分享 |
| UC 网盘 | uc | Cookie / 分享 |
| 115 网盘 | 115 | Cookie / 分享 |
| 123 网盘 | 123 | 账号 / 分享 |
| 天翼云盘 | tianyi | 账号 / 分享 |
| 中国移动云盘 | 139 | 账号 / 分享 |
| 迅雷云盘 | thunder | 账号 / 分享 |
| PikPak | pikpak | 账号 / 分享 |
| 光鸭云盘 | guangya | 账号 / 分享 |

以上为上游项目文档声明的支持范围，不代表每种网盘在所有地区、账号类型和客户端上均可用。不要将未授权的第三方转存或盗链作为默认资源源。

## 部署后端（Docker Compose）

在 NAS、家用服务器或受信任的 Linux 主机上部署。先复制 `docker-compose.yml`，确认数据目录持久化，再启动：

```bash
docker compose up -d
docker compose logs -f alist-tvbox
```

管理界面默认端口为 `4567`。首次启动后立即设置强密码；不要沿用示例/默认凭证。建议仅向局域网开放，或通过带 HTTPS、身份验证和访问控制的反向代理访问。不要将管理端口直接暴露到公网。

1. 打开 `http://服务器局域网IP:4567`。
2. 完成管理员初始化并修改默认密码。
3. 在网盘账号页面添加你本人有权使用的网盘账号。
4. 在资源页面添加你有权访问的分享链接，或挂载自己的存储。
5. 在订阅页面复制 TVBox 订阅地址。
6. 在 TVBox / 影视仓中将订阅地址作为**第二个配置/订阅源**添加。

上游项目 README 描述的订阅地址形式为 `http://服务器地址:4567/sub/0`；若开启安全订阅，应使用管理页面实际生成的带 Token 地址。不要把带 Token 的地址提交到 GitHub。

## Docker Compose

本目录的 `docker-compose.yml` 使用上游公开镜像及持久化数据卷。首次部署前检查镜像发布说明与主机架构：

```yaml
services:
  alist-tvbox:
    image: haroldli/alist-tvbox:latest
    container_name: alist-tvbox
    restart: unless-stopped
    ports:
      - "4567:4567"
    volumes:
      - ./data:/data
```

如需从公网访问，先配置 HTTPS 反向代理、强密码、订阅 Token 和防火墙白名单。不要在 compose 文件中写入网盘 Cookie、Token 或密码；不要把 `data/` 上传到 Git。

## 与 single-tvbox 主配置的关系

- 保留 `../box.json` 作为原有点播/直播配置入口。
- 网盘后端产生的是独立 TVBox 订阅，推荐在客户端作为第二个订阅源添加。
- 不在静态公开 `box.json` 中写入个人网盘凭证。
- 不直接伪造 `csp_Alist`、`csp_PanAli` 等未确认客户端内置的爬虫类名；不同 TVBox 分支的内置 Spider/JAR 并不一致。
- 如果后端订阅地址不能在你的 TVBox 分支导入，请先核对客户端版本与上游兼容说明，而不是将账号 Cookie 填进公开配置。

## 凭证安全

- GitHub 仓库只存放不含秘密的模板和说明。
- Cookie、Access Token、Refresh Token、密码、分享提取码均视为敏感数据。
- 若曾提交过凭证，删除当前文件并不足够；应先在网盘/服务商处撤销或轮换，再评估 Git 历史清理。
- 开启订阅 Token；避免将订阅 URL 截图或粘贴到公开 Issue。
- 定期检查后端访问日志、异常登录和陌生设备。

## 上游文档

- [AList-TvBox 项目与订阅说明](https://github.com/power721/alist-tvbox)
- [AList-TvBox 中文功能文档](https://github.com/power721/alist-tvbox/blob/master/doc/README_zh.md)
- [AList-TvBox API 文档](https://github.com/power721/alist-tvbox/blob/master/api.md)
- [OpenList 官方文档](https://oplist.org/guide/)

## 验证状态

本仓库已加入部署模板和接入文档；尚未替用户部署后端、登录网盘账号或进行真实网盘播放验证。请在自己的服务环境中完成账号授权与播放测试。
