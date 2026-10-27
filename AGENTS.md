# Character / Live2D Agent Contract

本文件只作用于 `/Users/Link/code/Character`。当前交付是 `live2d_v5`；`live2d_v1`–`v4` 是历史基线（v4 仍被 v5 测试引用），`live2d_v5_1` 是未验收的头发边缘修补实验。旧 phase1–4 已归档到 `archive/legacy_character_pipeline/`，不作为当前模型。

本文件在模型路由上优先于全局 OMX/AGENTS.md 的通用建议；仅限本项目。模型与启动配置的完整说明见 `codex/README.md`。

## 角色与权限

| 角色 | 模型 / Effort | 权限 |
|---|---|---|
| Executor（主 Agent） | Codex 界面 `/model` 选择 | 可读、可写、可运行测试、整合结果 |
| Reviewer（子 Agent） | 固定 `gpt-6-astra` / `medium` | 只读；不改文件、不调用生图/API、不再派生子 Agent |

### Executor

- 输入：用户任务、当前版本资产、Manifest、测试/验收记录。
- 职责：理解范围、开发修改、运行测试、整合结果、最终验证。
- 输出：改动文件、验证命令与结果、未验证边界；不要只给计划就结束。
- 大范围代码改动或 Live2D 图层/遮挡调整后，必须调用 `live2d-reviewer` 做一次独立审查。
- 派发普通子 Agent 时显式传 `model="gpt-6-astra"`、`reasoning_effort="medium"`；Reviewer 用 `live2d-reviewer`，不要再覆盖其模型。

### Reviewer

调用：

```text
spawn_agent(
  agent_type="live2d-reviewer",
  task_name="review_<scope>",
  message="<文件/图层范围；明确只读>"
)
```

- 输入：要审查的文件/图层范围、Manifest 或 PSD 变更、已知验证证据。
- 审查重点：Live2D 图层顺序与遮挡、耳根/后发隐藏区、alpha 与裁切、PSD/Manifest/纹理一致性、v5 已验收素材是否被破坏、测试声明是否被证据支持。
- 输出：`CLEAR` / `WATCH` / `BLOCK`；问题给出 `file:line`、证据和最小修复建议；明确列出“已验证”和“无法只读验证”。
- 只读是角色指令约束，不是独立沙箱；Executor 必须只派发只读检查，并在任务描述中禁止写入。

## 启动与 Provider

| 启动方式 | 子 Agent 默认 |
|---|---|
| `./scripts/codex-live2d` | `live2d` Profile 注入 `gpt-6-astra` / `medium` |
| Codex 桌面/VS Code 直接启动 | Profile 不加载；普通子 Agent 由本文件要求显式传 Astra/medium |

- Provider 由 CC Switch 当前线路决定；主/子 Agent 必须同一 Provider，禁止混用。
- 不改 `~/.codex/config.toml`、`~/.codex/auth.json`、`[model_providers.*]`；这些由 CC Switch 管理。
- 当前按 CC Switch 直连模式使用；聚合/路由模式可能改变子 Agent 路由，不要用于本项目。
- 模型路由、Profile、Effort、Provider 和认证已由用户确认；维护任务不得“顺手优化”这些配置。

## 执行限制

- 不在未获明确要求时开始 v6 正式开发、批量生图或重做已验收素材。
- 不调用生图 API；默认只用 Codex 官方内置生图。只有用户明确说明使用 API 时才允许调用 API/BeefAPI。
- 不修改已验收的 v5 PSD、Manifest、关键 PNG 和报告；需要变更时先说明范围、风险和回滚方式。
- 不移动仍被代码、脚本、Manifest 或测试引用的文件；移动前先查引用并更新路径。
- 归档优先移动而不是删除；历史材料放入 `archive/` 对应分类，并在归档索引登记。
- 不创建重复的 README、PROGRESS、CHECKLIST 或计划文件；当前计划统一写在 `docs/PROGRESS.md`。

## 文档维护

- 项目入口：根 `README.md`。
- 当前进度与 v6 计划：`docs/PROGRESS.md`。
- Codex 配置与启动：`codex/README.md`。
- 归档说明：`archive/README.md` 和 `archive/move_manifest.json`。
- 版本说明：`live2d_v1`–`v5_1/README.md`；历史版本只加状态说明，不改写当时的验证事实。
- 任何移动/归档后，更新所有受影响的相对路径和文档链接；保留 v1–v5 的可追溯性。

## 当前已知边界

- 现有头发仍是三片结构，后发和固定前发不足以支持大幅度头部转动；耳朵在头发移动时可能露出或遮挡错误。
- v5.1 只修补了两层前发的耳根/脸颊边缘；29 项自动检查中 28 项通过、1 项眼睑重叠失败，视觉验收未完成，不能当作 v5 的替代交付。
- 尚未完成 Cubism 绑定、±30° 头部伪 3D 转动、运动状态下完整头发/耳朵遮挡验证，以及 CMO3 在 Cubism Editor 中的编辑验证。
