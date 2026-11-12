# 网盘搜索与账号中心

部署入口：`/netdisk/`

## 页面功能
- 夸克、百度、阿里云盘、UC 的公开网页索引搜索。
- Cookie / Token 在浏览器本地填写、保存、导入和导出。
- 将凭据补丁合并到用户选定的原始 JSON，并下载合并文件；不上传文件、不覆盖原始文件。
- 从 Release 中的真实 `tvbox-unified.json` 自动生成 TVBox 网盘搜索源清单，页面显示实际集成的 type=3 搜索源及其 JS API 路径。

## 已核实的 TVBox 运行时资源

来自发布版 `unified-tvbox-bundle.zip` 的结构审计（743 个文件）：

| 文件 | 用途 / 识别到的调用 |
|---|---|
| `sources/星微/tvboxTW/本地【拾光线路】/lib/pans.js` | 网盘适配器聚合入口，导入 ali、baidu、baidu2、cloud、pan123、quark、uc、yun |
| `.../lib/pan/quark.js` | 夸克网盘适配器；包含 listFile、needRefresh 等函数 |
| `.../lib/pan/baidu.js` | 百度网盘适配器 |
| `.../lib/pan/uc.js` | UC 网盘适配器；包含 listFile、needRefresh |
| `.../open/wanpan.js` | type=3 网盘聚合源；包含 home、homeVod、search、category、detail、play |
| `sources/星微/tvboxTW/本地【九月线路】/js/盘搜.js` | 独立盘搜源；包含 buildSearchUrl、syncCookies、search、detail、play |

审计同时在 TVBox 主配置中识别到 21 条与网盘/云盘/夸克/百度相关的 type=3 站点记录；其中包括 12 条共用 `open/wanpan.js` 的云盘聚合站点，以及夸克短剧搜索、网盘资源搜索等独立入口。具体数量和名称以部署时自动生成的 `tvbox-sites.json` 为准。清单只包含站点索引、名称、type、搜索标记和 API 路径，不包含 ext、Cookie 或 Token。

页面上的“TVBox 内置网盘搜索源”会读取该清单。用户在 TVBox/影视仓中仍需导入主配置并使用客户端的搜索入口；网页公开索引搜索与 TVBox 内置爬虫搜索是两种不同功能。

## 已核实的字段结构

### 拾光 env.json
审计的原始文件路径：`sources/星微/tvboxTW/本地【拾光线路】/config/env.json`。
字段：`quark_cookie`、`baidu_cookie`、`uc_cookie`、`uc_token`，另含 `line_order`、`quark_original`、`quark_infinite`、`quark_transfer`、`enable_proxy`、`proxy_url`、`proxy_img`、`threads` 等运行参数。
页面的 env 合并只写入用户非空填写的凭据字段，原配置其他设置保持不变。

### 星微 JAR ext
审计文件：`jar-configs/xw-dlao-88d04426c4.json`。
已确认结构在 `sites[2].ext` 和 `sites[3].ext`，包括 `site_urls` 数组、`url_key` 字符串、`token`、`ucCookie`、`quarkCookie` 和 `threadinfo` 对象。
页面只更新满足该结构的 ext 对象；不会修改其他站点或 JAR ext。`token` 的真实服务归属尚未完全确认，因此页面要求单独填写“JAR ext 专用 token”，不会把夸克或 UC Token 自动猜测映射过去。

## 操作方法
1. 打开网盘中心，填写对应 Cookie / Token。
2. 选择原始 `env.json` 或对应 JAR 配置 JSON。
3. 点击“合并凭据并下载”。
4. 先备份原文件，再将合并后的文件放回原配置位置，或按 TVBox/影视仓支持的配置导入方式导入。
5. 在 TVBox 导入主配置后，进入“TVBox 内置网盘搜索源”列出的站点进行搜索、详情和播放测试。

## 尚未实现的运行时同步
GitHub Pages 是静态网站。浏览器 localStorage 不会自动同步到 TVBox、影视仓、drpy Python 进程或 JAR 进程。本页通过本地合并原配置并下载实现安全的手动配置更新，不声称具备远程实时注入或云端账号同步。

已审计到 JS 适配器、聚合源和配置字段，但仅凭静态文件扫描不能证明账号认证、刷新 Token、分享链接解析和播放在所有客户端上均成功。仍需在具体 TVBox/影视仓版本实测，尤其是 JAR ext 的 `token` 归属与使用方式。

## 安全
- 页面凭据仅存当前浏览器 localStorage；本地存储不是密码保险箱。
- 文件合并在浏览器本地完成，不上传到服务器。
- 不要把导出的账号备份或合并配置提交到公开仓库、Issue、PR 或聊天群。
- 凭据泄漏后请在对应网盘平台撤销或更新。
- 不提供密码登录代理、会员绕过或访问控制绕过。

## 搜索说明
搜索按钮通过外部搜索引擎查询公开索引。结果有效性及授权状态需自行核验；本页不抓取或代理第三方网盘内容。


## TVBox 夸克 Cookie 配置页

专用入口：`/netdisk/quark-cookie.html`

- 在浏览器本地填写、保存或清除夸克 Cookie。
- 页面从公开 Pages 主配置读取 `tvbox-unified.json`，仅在本机内存中修改目标站点 `xw_bad1f_cat_58`。
- 目标站点改用已存在的 `open/wanpan.js` 真实夸克网盘解析器；Cookie 通过该站点的对象型 `ext.quark_cookie` 传入运行时。
- 点击生成后下载 `tvbox-quark-cookie.local.json`，再通过 TVBox / 影视仓的本地文件导入功能导入。
- Cookie 不会写入公开仓库，也不会上传到 Pages。下载配置包含个人 Cookie，必须妥善保管。
- GitHub Pages 的公开主配置只包含空 Cookie 字段；不同客户端对本地文件导入和对象型 ext 的支持可能不同，需在目标客户端实测。

构建时由 `scripts/patch_quark_cookie_source.py` 对 Release 整合包执行幂等补丁：把目标站点切换到现有 Quark 解析器，并避免在播放地址后附加未经签名的线程查询参数。该操作不把个人 Cookie 写入 Release。
