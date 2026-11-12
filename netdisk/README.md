# 网盘搜索与账号中心

部署入口：`/netdisk/`

## 页面功能
- 夸克、百度、阿里云盘、UC 的公开网页索引搜索入口。
- Cookie / Token 在当前浏览器填写和本地保存。
- JSON 账号备份、导入、清除。
- 两种已从整合包实际配置结构核实的凭据补丁导出。

## 已核实的 TVBox 配置字段

### 拾光线路 env.json
整合包内 `sources/星微/tvboxTW/本地【拾光线路】/config/env.json` 的字段结构包含：
- `quark_cookie`
- `baidu_cookie`
- `uc_cookie`
- `uc_token`

页面的“导出拾光 env 凭据补丁”仅导出上述四个字段。请将其合并进原 env.json，保留原文件其他配置，不要直接用补丁覆盖整个 env.json。

### 星微 JAR ext
整合包内 `jar-configs/xw-dlao-88d04426c4.json` 的两个站点 ext 结构包含：
- `quarkCookie`
- `ucCookie`
- `token`
- `site_urls`
- `url_key`
- `threadinfo`

页面的“导出星微 JAR ext 凭据补丁”只导出已确认的 Cookie 字段和 token 字段，不覆盖站点 URL、线程或其他 ext 配置。token 的具体服务归属及各站点实际读取逻辑尚未由 JAR 字节码/运行测试完全确认，导出值需要按目标站点自行核对。

## 尚未实现的运行时注入
本项目通过 GitHub Pages 发布静态资源。浏览器 localStorage 不会自动同步到 TVBox、影视仓、drpy Python 进程或 JAR 进程。导出的 JSON 是可手动合并的凭据补丁，不是远程账号同步服务，也不会自动改写已发布的 Release ZIP。

完整自动注入还需要在 TVBox 客户端支持的配置导入流程、JAR ext 消费点或受保护的后端服务中实现，并在目标客户端实测。静态页面不能安全地把浏览器 Cookie 推送给公开 GitHub 仓库。

## 安全
- 凭据只存当前浏览器 localStorage；不会提交到仓库或上传到 Pages。
- 仅在可信设备使用；本地存储不是密码保险箱。
- 不要把导出的凭据补丁上传到公开仓库、Issue、PR 或群聊。
- 凭据泄漏后请在对应网盘平台撤销或更新。
- 不提供密码登录代理、会员绕过或访问控制绕过。

## 搜索范围
搜索入口通过外部搜索引擎查询公开索引页面。结果有效性和授权状态需自行核验；本页不抓取或代理第三方网盘内容。
