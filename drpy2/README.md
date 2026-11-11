# drpy2 静态 TVBox 配置

此目录由根目录 GitHub Actions 工作流发布到 GitHub Pages 的 `/drpy2/` 路径。Python 只在 Actions 构建阶段生成 JSON；线上不运行 FastAPI。

## 导入地址

`https://fun-lovers.github.io/fun-lovers-tv/drpy2/tvbox.json`

## 发布

1. 合并包含本目录和 `.github/workflows/deploy-drpy2-pages.yml` 的 PR 到 main。
2. 仓库 Settings → Pages → Source 选择 GitHub Actions。
3. Actions 中运行 Deploy drpy2 to GitHub Pages。
4. 成功后导入上面的 URL。

## 文件

- `config/sources.json`：已审核并启用的源目录。
- `public/js/`：drpy2 JavaScript 规则。
- `public/libs/drpy2.min.js`：由 Actions 构建时下载，不提交运行时二进制。
- `scripts/build_static.py`：生成 Pages 路径正确的 TVBox JSON 并执行结构校验。

## 边界

当前只包含 Bilibili 官方公开元数据示例，播放跳转官方网页，不提取媒体直链，不绕过登录、会员或 DRM。TVBox 对网页播放的支持因客户端而异，尚需在目标客户端实测。GitHub Pages 不提供 Python 在线 API、数据库、私有 Cookie 或后台任务。
