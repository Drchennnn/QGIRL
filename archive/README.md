# 归档索引

本目录保存 2026-10-27 项目维护时从根目录移出的历史内容。移动前的关键文件哈希和清单见 [move_manifest.json](move_manifest.json)。

## 分类

| 目录 | 原位置 | 内容与用途 | 当前状态 |
|---|---|---|---|
| `legacy_character_pipeline/` | `phase1`–`phase4`、`outputs`、`work`、`src`、`DESIGN.md` | 旧角色 Canvas 原型、PSD/Cubism 导出、眨眼交接、WebGL 播放器及旧表情/处理资产 | 历史归档；不属于当前 v5 交付链 |
| `design_boards/` | `outputs/design_boards/` | 服装、发型、包鞋等 AI 概念板与提示词/API 日志 | 历史概念资料；当前服设以 `服设/` 为准 |
| `reference_images/` | 根目录的两张雨夜街景、一张雨窗咖啡馆场景图 | 场景/氛围参考，未被当前脚本引用 | 历史参考；保留备查 |

## 仍然有效、未归档的内容

- `live2d_v1`–`live2d_v5_1`：保留在仓库根目录的历史自行拆分版本，便于追溯；均不是当前 See-through 主线素材。
- `docs/`、`codex/`、`scripts/`、`参考/`、`服设/`。
- `scripts/live2d_v1_pack.py`：从旧 `work/` 移出的当前 PSD 打包入口，v1–v5 构建命令仍使用它。

## 使用规则

- 旧管线脚本以 `archive/legacy_character_pipeline/` 作为工作目录运行；其中 `references` 是指向根目录 `references/` 的相对符号链接。
- 归档内容不代表当前模型或当前美术状态。当前交付、已知边界和 v6 计划以根目录 `README.md`、`docs/PROGRESS.md` 为准。
- 归档目录内不再新增计划文档；新增历史材料按上述分类放入对应目录，并在本索引登记。
