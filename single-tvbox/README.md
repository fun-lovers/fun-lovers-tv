# single-tvbox

这是一个独立维护的 TVBox 单仓配置包。客户端只需导入本目录的 `box.json`；配套 Python 爬虫脚本与配置说明均随仓库保存。

## 导入地址

```text
https://raw.githubusercontent.com/fun-lovers/fun-lovers-tv/main/single-tvbox/box.json
```

## 目录

- `box.json`：唯一 TVBox 导入入口，包含点播站、直播列表、DNS、播放器参数。
- `py/`：与 `type: 3` 站点对应的 Python Spider 脚本。
- `config/source-catalog.json`：源清单、上游来源和验证说明。
- `scripts/validate.py`：检查 JSON 语法、站点 key、脚本路径和直播地址格式。
- `LICENSE.cluntop.txt`：随附上游 Python 脚本的 MIT 许可。

## 本地检查

在仓库根目录执行：

```bash
python single-tvbox/scripts/validate.py
```

## 说明

1. 主配置使用相对路径引用 `./py/*.py`，请通过上方 raw GitHub 地址导入，保证相对路径解析到本目录。
2. Python 脚本按 cluntop/tvbox 上游版本随仓库保存；脚本运行需要客户端内置的 TVBox Spider 运行时。不同 TVBox 分支对 Python 运行时和依赖的支持可能不同。
3. MacCMS 点播接口与 IPTV-org M3U 是外部上游服务。配置中收录不代表服务当前可用，也不保证某个频道在你的网络/地区可播放。
4. 本次提交只做配置结构与资源 URL 格式检查，没有伪称完成全部接口的端到端播放测试。
5. `parses`、`rules`、`headers` 保持为空，避免默认信任未经核验的第三方网页解析脚本；客户端可使用自身播放器的直连/解析能力。

## 上游与许可

Python 脚本来源： [cluntop/tvbox](https://github.com/cluntop/tvbox)（MIT License）。
直播列表来源： [iptv-org/iptv](https://github.com/iptv-org/iptv)。
点播 API 候选清单基于本仓库既有的 `addons/tvbox-vod-verified.json` 与 cluntop 配置中出现的 MacCMS 接口类型整理；可用性需定期复核。
