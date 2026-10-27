> **仓库说明**：本仓库只上传代码、文档、Manifest 和报告 JSON；角色素材、PSD、HTML 预览、参考仓库和凭据未上传。详见 [REPO_SCOPE.md](REPO_SCOPE.md)。

# Character：Live2D 上半身立绘

开发目录：`/Users/Link/code/Character`。当前只推进 Live2D 角色资产；旧 phase1–4 角色管线已归档，不代表当前模型状态。

## 当前状态

- **当前交付：v5**。33 层、1024×1536 PSD，两个离线预览入口；脸部第二组六个分件已完成，其余 27 层沿用 v4 的已验收内容。
- **v5.1 是未验收实验**：只修补 `hair_front_fixed` 与 `hair_fringe_center` 两层；29 项自动检查中 28 项通过，眼睑重叠检查失败，视觉审查也未完成，不能替代 v5。
- **尚未完成**：完整头发分件、耳朵/后发动态遮挡、Cubism 绑定、±30° 头部伪 3D 转动、运动状态下的完整遮挡回归。
- **下一阶段：v6 头发分层重构**。只重构头发，不重做已验收的眼、眉、脸、耳、鼻嘴和身体。计划见 [docs/PROGRESS.md](docs/PROGRESS.md)。

## 快速入口

| 内容 | 入口 |
|---|---|
| 当前版本说明 | [live2d_v5/README.md](live2d_v5/README.md) |
| 当前 PSD | [live2d_v5/packed/character_front_v5.psd](live2d_v5/packed/character_front_v5.psd) |
| 脸部六件检查页 | [live2d_v5/脸部第二组_独立分件检查.html](live2d_v5/脸部第二组_独立分件检查.html) |
| 视线/发片预览 | [live2d_v5/视线与发片精修预览.html](live2d_v5/视线与发片精修预览.html) |
| v5.1 头发修补实验 | [live2d_v5_1/README.md](live2d_v5_1/README.md) |
| 开发进度与 v6 计划 | [docs/PROGRESS.md](docs/PROGRESS.md) |
| Codex 多 Agent 环境 | [codex/README.md](codex/README.md) |
| 归档索引 | [archive/README.md](archive/README.md) |
| 原始角色参考 | [参考/原始参考图/README.md](参考/原始参考图/README.md) |

预览页可以直接用浏览器打开，不需要启动服务器。旧 phase4 播放器（`http://127.0.0.1:4176`）已归档，不再是当前入口。

## 版本

| 版本 | 状态 | 说明 |
|---|---|---|
| `live2d_v1` | 历史基线 | 新全身正面母版与初版拆层 |
| `live2d_v2` | 历史基线 | 精修母版、35 层 PSD、离线视线原型 |
| `live2d_v3` | 历史基线 | RGBA 视线裁切修复、透明头发分件 |
| `live2d_v4` | 历史基线，仍被 v5 测试引用 | 十个眼部/眉毛独立生成件、33 层 PSD |
| `live2d_v5` | **当前交付** | 六个脸部/耳/鼻嘴/颈部生成件；33 层 |
| `live2d_v5_1` | 未验收实验 | 只改两层前发，修补耳根与脸颊边缘；视觉审查未完成 |

v1–v4 保留在根目录，是因为 v5 的回归测试、Manifest 和对照说明仍直接引用它们；不要为了让根目录更短而移动这些基线。

## 目录

| 目录 | 用途 |
|---|---|
| `live2d_v1`–`live2d_v5_1/` | Live2D 版本资产、Manifest、脚本、报告和预览 |
| `docs/` | 当前进度、历史逐层分析、凭据说明 |
| `codex/` | Codex Profile、Reviewer 角色和 Agent 使用说明 |
| `scripts/` | 当前启动脚本与 PSD 打包入口 `live2d_v1_pack.py` |
| `references/` | 上游参考仓库、SDK、迁移校验和私有凭据（不提交密钥） |
| `参考/` | 人设、服设、姿态和原始参考图 |
| `服设/` | 当前服装参考素材 |
| `archive/` | 旧 phase1–4 管线、概念板、场景图；见归档索引 |
| `build/` | 空目录，保留构建输出位置 |
| `tests/` | 空目录，保留项目级测试位置 |

## 运行与验证

当前 v5 的构建/测试命令在 [live2d_v5/README.md](live2d_v5/README.md)。轻量只读检查：

```sh
cd /Users/Link/code/Character
uv run --offline --with pillow --with numpy --with scipy \
  python -m unittest discover -s live2d_v5/scripts -p 'test_*.py' -v
```

浏览器检查会写入 `live2d_v5/reports/`，只在需要更新证据时运行；维护任务不应覆盖已验收报告。

## 生图约定

- 默认使用 Codex 官方内置生图，意向模型 `gpt-image-2.5-sunburst`；内置工具不一定暴露模型选择参数，不能声称实际路由到该模型。
- 只有用户明确说明使用 API 生图时，才允许走 API/BeefAPI。当前暂停 API 调用。
- 后续 v6 仍按“完整独立分件生图、抠图只做隔离修边”的方式，不把旧合成图裁剪后冒充分层。

## 归档与追溯

- 旧 phase1–4、旧表情资产、旧处理脚本、旧基础图层和 phase4 设计说明在 [archive/legacy_character_pipeline/README.md](archive/legacy_character_pipeline/README.md)。
- 服装概念板在 [archive/design_boards/README.md](archive/design_boards/README.md)。
- 场景参考图在 [archive/reference_images/README.md](archive/reference_images/README.md)。
- 移动记录和关键哈希在 [archive/move_manifest.json](archive/move_manifest.json)。当前目录不是 Git 仓库，使用普通移动而非 `git mv`。
