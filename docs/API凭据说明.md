# BeefAPI 本地凭据记录（历史）

> 状态：历史记录。自 2026-10-27 起，项目默认改用 Codex 官方内置生图，暂停 API/BeefAPI 调用。只有用户明确说明使用 API 生图时，才允许重新启用本文的旧入口。

密钥正文仅存于 `references/*.credentials.json`，权限 600，已加入 `.gitignore`；本文不包含密钥。

## 历史请求结果（2026-10-26）

| 名称 | 本地凭据文件 | 当时结果 |
|---|---|---|
| 原有生图 key | `references/beefapi_primary.credentials.json` | `gpt-image-2.5-sunburst` 成功，1024×1024 RGBA PNG；此前 `gpt-image-2` 编辑也成功 |
| 截图备用 key | `references/beefapi_secondary.credentials.json` | 修正 1 个字符转录差异后，直接 POST `/v1/images/generations` 仍返回 401“无效的令牌” |
| 最新文字 key | `references/beefapi_latest.credentials.json` | `/models` 可认证；直接 POST `gpt-image-2.5-sunburst` 和 `gpt-image-2` 均返回 404“模型不存在，或没有访问权限” |

请求参数、哈希、错误 request id 和日志见 `archive/legacy_character_pipeline/phase1/api_validation/validation_results.json`。不能把 `/models` 的返回列表单独当成生图权限结论。

## 旧调用方式（已归档）

- 旧入口 `work/run_image.mjs` 已随旧管线移到 `archive/legacy_character_pipeline/work/run_image.mjs`，不再作为当前生图入口。
- 旧包装器通过子进程环境变量传递 key；不修改全局技能或全局凭据。
- 旧 CLI 不识别 2.5 系列，且会把未列于 `/models` 的模型提前阻断；项目副本曾增加显式模型支持。该行为仅作为历史记录。

## 当前约定

- 默认使用 Codex 官方内置生图，意向 `gpt-image-2.5-sunburst`；工具若不暴露模型参数，不能声称实际指定成功。
- 只有用户明确要求使用 API 时，才允许调用 API/BeefAPI；不得把旧 key 当作默认入口。
- 所有私钥文件不得嵌入 HTML、上传、提交或放进公开演示。
