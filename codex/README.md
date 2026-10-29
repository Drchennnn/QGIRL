# Codex 协作分工（Live2D）

2026-10-29 更新：See-through 拆层正面候选是活动主线；独立 `eye_close_trial v2` 已通过 Anime2.5DRig 技术验证，视觉确认仍待完成；旧自行拆分版本已归档。保留执行与独立审核分工，但不指定任何模型、Effort、Provider 或专用 Profile。当前恢复入口是根 `README.md` 与唯一计划 `docs/PROGRESS.md`。

## 分工

| 角色 | 职责 | 权限 |
|---|---|---|
| Executor（执行方） | 明确参考与目标，制作修改、运行验证、整合结果、修复审核问题并负责交付 | 可读、可写、可运行测试；遵守当前授权范围 |
| Reviewer（审核方） | 对照原始角色参考、验收基线、本轮目标和实际证据做独立只读审核 | 只读；不改文件、不调用生图/API、不修改配置、不派生子 Agent |

审核不绑定模型，也不以模型名称或角色是否注册作为审核完成依据。自动检查、独立审核和美术/运动视觉验收分别说明，不相互冒充。

## Reviewer 调用

优先使用当前会话可用的 `live2d-reviewer`：

```text
spawn_agent(
  agent_type="live2d-reviewer",
  task_name="review_<scope>",
  message="只读审核指定范围；对照原始参考、当前验收基线和本轮目标。禁止写文件、生图/API和派生子 Agent。返回结论与证据。"
)
```

角色不可用时，使用普通原生子 Agent，并在任务中完整传入相同的只读职责和输出要求。角色调用失败不能计为已审核。

只读是角色指令约束，不是独立沙箱；执行方必须在任务描述中明确禁止写入，只派发只读检查。

## 配置边界

- 项目不保存模型/Effort 默认值，不提供专用 Profile 或模型启动脚本。
- 直接使用 Codex 桌面、VS Code 或 CLI 启动；模型在当前会话中选择。
- Provider 由 CC Switch 当前线路决定；执行与审核在同一线路下运行，不跨 Provider。
- 不修改 `~/.codex/config.toml`、`~/.codex/auth.json`、`[model_providers.*]`；这些由 CC Switch 管理。
- `codex/agents/live2d-reviewer.toml` 只保存只读职责、权限、输入输出和审查标准，不包含模型/Effort 字段。

## 历史说明

2026-10-27 的专用 Profile、模型默认值和启动/安装脚本已在 2026-10-29 移除，不再作为当前入口。历史进度中的 Reviewer/子 Agent 记录属于当时流程，不代表当前存在模型绑定或专用 Profile。

## 当前审核重点

- See-through候选图层顺序、眼部/头发遮挡、耳根与后发隐藏区、alpha与裁切。
- PSD/Manifest/纹理/锚点及候选哈希一致性。
- Anime2.5DRig与Cubism验证声明是否有对应证据；区分独立PSD原生闭眼试验层与 Anime2.5DRig 运行时合成层，不可相互冒充。
- 已验收素材是否被破坏；历史v5/v6审核结论不得转移给See-through候选。
