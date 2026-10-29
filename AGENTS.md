# Character / Live2D Collaboration Contract

本文件仅适用于此仓库工作树；具体本地绝对路径由使用者环境决定。

当前主线：See-through 拆层后的正面头部与接眼/局部对称候选。用户于 2026-10-29 审核通过；独立 `eye_close_trial v2` 已通过 Anime2.5DRig 双眼/单眼闭合和小幅运动验证，并获用户视觉确认。根目录 `live2d_v1`–`v5_1` 在此公开快照中保留为历史代码与记录，不是当前模型；旧 phase1–4 位于 `archive/legacy_character_pipeline/`。

本项目保留执行与独立审核的分工，但**不指定主 Agent 或子 Agent 的模型、Effort、Provider 或专用 Profile**。模型与线路使用当前 Codex 会话和 CC Switch 的实际设置，项目文档不设置默认值。

## 分工与权限

| 角色 | 职责 | 权限 |
|---|---|---|
| Executor（执行方） | 明确参考与目标，制作修改、运行验证、整合结果、修复审核问题并负责交付 | 可读、可写、可运行测试；遵守当前授权范围 |
| Reviewer（审核方） | 对照原始角色参考、验收基线、本轮目标和实际证据做独立只读审核 | 只读；不改文件、不调用生图/API、不修改配置、不派生子 Agent |

### Executor

- 输入：用户任务、当前版本资产、Manifest、测试/验收记录。
- 执行前明确原始参考、当前验收基线、改动范围和验收目标；当前执行计划以 `docs/PROGRESS.md` 为准。
- 大范围代码改动或 Live2D 图层/遮挡调整后，应安排一次独立只读审核；审核不可用时不能把自评当作独立审核。
- 修复审核中的 `BLOCK` 问题；`WATCH` 必须明确剩余风险、证据缺口和是否影响当前验收目标。
- 自动检查通过不替代美术与运动视觉验收。

### Reviewer

优先使用当前会话可用的 `live2d-reviewer`；该角色不绑定模型/Effort，只提供只读职责和审核规范。角色不可用时，使用普通原生子 Agent，并在任务中完整传入相同的只读职责。

```text
spawn_agent(
  agent_type="live2d-reviewer",
  task_name="review_<scope>",
  message="<文件/图层范围；明确只读>"
)
```

- 输入：要审查的文件/图层范围、Manifest 或 PSD 变更、已知验证证据。
- 审查重点：Live2D 图层顺序与遮挡、耳根/后发隐藏区、alpha 与裁切、PSD/Manifest/纹理一致性、已验收素材是否被破坏、测试声明是否被证据支持。
- 输出：`CLEAR` / `WATCH` / `BLOCK`；问题给出 `file:line`、证据和最小修复建议；明确列出“已验证”和“无法只读验证”。
- 只读是角色指令约束，不是独立沙箱；执行方必须在任务描述中禁止写入，只派发只读检查。

## 启动与配置

- 直接使用 Codex 桌面、VS Code 或 CLI 启动，不依赖项目专用 Profile 或启动脚本。
- 项目不保存模型、Effort、Provider 的默认值，也不覆盖 Codex 的全局设置。
- Provider 由 CC Switch 当前线路决定；执行与审核应在同一线路下运行，不跨 Provider。
- 不改 `~/.codex/config.toml`、`~/.codex/auth.json`、`[model_providers.*]`；这些由 CC Switch 管理。
- 当前按 CC Switch 直连模式使用；聚合/路由模式可能改变子 Agent 路由，不要用于本项目。

## 执行限制

- 不在未获明确要求时开始新阶段、批量生图或重做已验收素材。
- 不调用生图 API；默认只用 Codex 官方内置生图。只有用户明确说明使用 API 时才允许调用 API/BeefAPI。
- 不修改已验收的 v5 PSD、Manifest、关键 PNG 和报告；需要变更时先说明范围、风险和回滚方式。
- 不移动仍被代码、脚本、Manifest 或测试引用的文件；移动前先查引用并更新路径。
- 归档优先移动而不是删除；历史材料放入 `archive/` 对应分类，并在归档索引登记。
- 不创建重复的 README、PROGRESS、CHECKLIST 或计划文件；当前计划统一写在 `docs/PROGRESS.md`。

## 文档维护

- 项目入口：根 `README.md`。
- 当前进度：`docs/PROGRESS.md`。
- 协作分工：`codex/README.md`。
- 归档说明：`archive/README.md` 和 `archive/move_manifest.json`。
- 版本说明：`archive/self_split_live2d/live2d_v*/README.md`；历史版本只加状态说明，不改写当时的验证事实。根目录同名软链接兼容旧引用。
- 任何移动/归档后，更新所有受影响的相对路径和文档链接；保留 v1–v5 的可追溯性。

## 当前已知边界

- See-through 接眼/对称候选仍是活动主线。独立 `eye_close_trial v2` 已加入左右原生闭眼层并通过 Anime2.5DRig 双眼/单眼闭合和小幅运动技术检查，用户已确认视觉效果良好。基础接眼候选和 Cubism 预检副本仍不含原生 `eye_close`，不要混淆这些 PSD。
- v5.1 与 v6 状态为历史实验；保留既有测试事实，不作为当前进度或主线素材。
- 尚未完成 Cubism 绑定、±30° 头部伪 3D 转动、运动状态完整遮挡验证，以及 CMO3 在 Cubism Editor 中的编辑验证。
- 当前状态与中断恢复顺序以根 `README.md`、`docs/PROGRESS.md`、`experiments/seethrough_anime25d/experiment.json` 为准；旧手工 PoC 仅为历史参考，不能覆盖主线进度。
