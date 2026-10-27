# Codex 多 Agent 环境（Live2D）

2026-10-27 维护时未改动模型路由、Profile、Effort、Provider 或认证；本页只补充当前项目文档关系。项目角色规范见 [../AGENTS.md](../AGENTS.md)，项目进度见 [../docs/PROGRESS.md](../docs/PROGRESS.md)。

## 当前配置

- 主 Agent：在 Codex 界面用 `/model` 选择，Profile 不锁定主模型。
- 子 Agent：默认 `gpt-6-astra` / `medium`；Reviewer 角色固定同一组值。
- Provider：由 CC Switch 当前线路决定；主/子 Agent 不得跨 Provider。
- 两条线路共用同一个 `live2d` Profile；CC Switch 只切 Provider，不切 Agent 配置。

## 为什么源文件在 `codex/`，而不是 `.codex/`

当前 Codex CLI 0.164.0 只加载以下位置：

- `$CODEX_HOME/config.toml`
- `$CODEX_HOME/<profile>.config.toml`（通过 `codex -p <profile>`）
- `$CODEX_HOME/agents/*.toml`（原生子 Agent 角色）

项目内的 `.codex/config.toml` 不会被加载（已实测：`codex doctor` 仍只报告 `~/.codex/config.toml`）。因此源文件保留在项目 `codex/`，由安装脚本创建符号链接到 `~/.codex/`。

安装脚本不会修改 CC Switch 管理的 `config.toml`、`auth.json` 或 `[model_providers.*]`。

## 文件

| 文件 | 作用 |
|---|---|
| `codex/profiles/live2d.config.toml` | 只设置子 Agent 默认值；主模型由 Codex 界面选择 |
| `codex/agents/live2d-reviewer.toml` | 只读 Reviewer 角色，固定 `gpt-6-astra` / `medium` |
| `scripts/install-codex-live2d.sh` | 创建/校验 `~/.codex` 下的符号链接 |
| `scripts/codex-live2d` | 自动识别 CC Switch 线路并启动 Codex |
| `AGENTS.md` | 项目内 Executor / Reviewer 职责与工作流 |

## 安装

```sh
cd /Users/Link/code/Character
./scripts/install-codex-live2d.sh
```

脚本是幂等的；如果目标位置已有不同文件或指向别处的符号链接，会拒绝覆盖。旧版按线路拆分的两个 Profile 会被自动清理。

## 启动

先在 CC Switch 切到官方 Plus 或 BeefAPI，然后：

```sh
./scripts/codex-live2d
```

脚本会自动识别当前线路并打印，例如：

```text
[codex-live2d] provider=official reviewer=gpt-6-astra/medium; main model is chosen in Codex UI
```

也可以显式校验线路：

```sh
./scripts/codex-live2d official
./scripts/codex-live2d beefapi
```

线路不匹配时脚本会拒绝启动，避免主/子 Agent 跨 Provider。

进入 Codex 后，用界面的 `/model` 选择主 Agent 的模型和 Effort；本项目 Profile 不锁定主模型。

### 启动入口差异

- 通过 `./scripts/codex-live2d` 启动：`live2d` Profile 会注入 `[agents]` 默认值，普通子 Agent 自动使用 `gpt-6-astra` / `medium`。
- 直接从 Codex 桌面或 VS Code 界面启动：Profile 不会加载。此时 Reviewer 角色仍固定 `gpt-6-astra` / `medium`；普通子 Agent 需要主 Agent 按项目 `AGENTS.md` 显式传 `model="gpt-6-astra"`、`reasoning_effort="medium"`，否则可能继承主 Agent 的选择。

如果不希望依赖提示词约束，请始终用 `./scripts/codex-live2d` 启动。

本项目假定 CC Switch 处于直连模式。聚合/路由模式可能改写模型路由，不建议用于本项目。

## 模型

| 模式 | Executor（主） | Reviewer（子） |
|---|---|---|
| 官方 Plus | Codex 界面 `/model` 选择 | `gpt-6-astra` / `medium` |
| BeefAPI | Codex 界面 `/model` 选择 | `gpt-6-astra` / `medium` |

子 Agent 的默认值由两层保证：

- `[agents]`：`default_subagent_model = "gpt-6-astra"`，`default_subagent_reasoning_effort = "medium"`
- `live2d-reviewer.toml`：Reviewer 角色固定 `gpt-6-astra` / `medium`，且提示中说明这些值不可更改

因此主 Agent 无论选择什么模型/Effort，子 Agent 都不会继承主 Agent 的选择。

## Reviewer 调用

```text
spawn_agent(
  agent_type="live2d-reviewer",
  task_name="review_<scope>",
  message="<文件/图层范围；明确只读>"
)
```

Reviewer 关注代码、架构、Live2D 图层顺序与遮挡、alpha/裁切/遮罩、PSD/MOC3/纹理/绘制顺序、命中区域、参数边界、物理，以及测试声明是否有证据。

只读是角色指令约束；原生子 Agent 继承工具权限，不是独立沙箱。Executor 必须在任务描述中明确禁止写入，只派发只读检查。

## 验证记录（2026-10-27）

本次维护只更新说明和目录，没有重新验证在线模型调用。以下为此前已验证的配置事实：

已通过：

- 合并后的 `live2d` Profile 可加载；主模型不再被 Profile 固定（实测解析为 Codex 默认 `gpt-6.1-sol`，Effort 未由 Profile 设置，可在界面 `/model` 修改）。
- `live2d-reviewer` 已出现在原生 `spawn_agent` 的可用角色中，固定为 `gpt-6-astra` / `medium`。
- 项目 `AGENTS.md` 已进入 Codex 提示词。
- 启动脚本自动识别当前官方线路；`./scripts/codex-live2d official` 通过，`./scripts/codex-live2d beefapi` 在当前官方线路下按预期拒绝。
- `[agents]` 配置被 Codex 接受，没有新增 unrecognized 警告；现有警告仅来自全局 `mcp_servers.computer-use.type`。

尚未验证：

- 官方 Plus 实际模型调用：当前账号触发用量限制，Codex 返回 “You've hit your usage limit”，预计 18:30 后恢复。
- 主 Agent 实际调用 `live2d-reviewer` 的在线闭环：依赖上面的模型调用，当前无法执行。
- BeefAPI 实际调用：需要先在 CC Switch 手动切到 BeefAPI。

恢复额度或切到 BeefAPI 后，可运行：

```sh
./scripts/codex-live2d exec --skip-git-repo-check -s read-only \
  '调用 spawn_agent(agent_type="live2d-reviewer", task_name="review_smoke", message="只读检查 README.md 的结构，不要修改文件。")，然后返回 Reviewer 的结论。'
```

然后检查会话 JSONL 中是否出现 `spawn_agent`、`live2d-reviewer`，以及子 Agent 的 `turn_context` 是否为 `gpt-6-astra` / `medium`。
