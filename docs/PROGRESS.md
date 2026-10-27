# 开发进度

更新时间：2026-10-27（香港时间）。工作目录：`/Users/Link/code/Character`。

## 当前结论

- **当前交付：`live2d_v5`**。33 层、1024×1536 PSD，脸部第二组六个分件已验收；其余 27 层沿用 v4。
- **`live2d_v5_1` 未验收**：只修补两层前发的耳根/脸颊边缘；29 项自动检查中 28 项通过，眼睑重叠检查失败，`reports/hair_seam_test.json` 仍要求人工视觉审查。不能替代 v5。
- **v6 尚未开始**：头发分层重构、重新生图、最小 PoC 均属于计划阶段；仓库里没有 v6 实现或验收证据。
- 旧 phase1–4 角色管线已归档到 `archive/legacy_character_pipeline/`，不属于当前 v5 交付链。

## 版本状态

| 版本 | 状态 | 入口 |
|---|---|---|
| `live2d_v1` | 历史基线 | [README](../live2d_v1/README.md) |
| `live2d_v2` | 历史基线 | [README](../live2d_v2/README.md) |
| `live2d_v3` | 历史基线 | [README](../live2d_v3/README.md) |
| `live2d_v4` | 历史基线；v5 测试仍引用 | [README](../live2d_v4/README.md) |
| `live2d_v5` | **当前交付，已验收** | [README](../live2d_v5/README.md) |
| `live2d_v5_1` | 实验；29 项自动检查 28 通过/1 失败，视觉未验收 | [README](../live2d_v5_1/README.md) |

## 已完成并验证

### v5（2026-10-27）

- 完成完整无五官脸底、屏幕左右耳、鼻部软阴影、中性闭口线、头颈连接六个独立分件；官方内置生图 7 次请求、6 次成功。
- v5 保留 33 层结构，只更新六个脸部相关层，其余 27 层与 v4 逐文件字节一致。
- 24 项 Python 检查通过：脸部美术 5、交付与 PSD 9、眼部美术 5、眼球遮挡 5。
- 实际 Chrome 检查：六件检查页三背景/三模式 0 页面错误；装配页联动/独立视线、复位、缩放、发片和图层开关通过。
- 11 个视线姿态及双向独立眼测试通过；PSD 输入哈希与中性回读一致，封包回读零像素差异。
- 证据与入口：[v5 README](../live2d_v5/README.md)、[verification.json](../live2d_v5/reports/verification.json)、[33 层 PSD](../live2d_v5/packed/character_front_v5.psd)。

### v5.1 头发边缘实验（2026-10-27）

- 基线 v5；只替换 `hair_front_fixed` 与 `hair_fringe_center`，其余 31 层字节一致。
- 29 项自动检查：28 项通过；1 项失败——`screen_right` / `hair_front_fixed` 的眼睑重叠为 112，超过基线 99（`baseline + 10`）。源哈希、两层范围、耳根/脸颊区域实际变化、中央刘海范围检查通过。
- **未完成视觉验收**：`hair_seam_test.json` 标记 `visualReviewRequired: true`；需人工查看 `hair_seam_rois.png`、`seam_review_closeup.jpg` 后再决定是否采用。
- 采用前必须先修复或解释 `screen_right` / `hair_front_fixed` 的眼睑重叠回归；在未通过前，不把 v5.1 前发当作 v6 的已验收基线。
- 证据：[v5.1 README](../live2d_v5_1/README.md)、[hair_fix_manifest.json](../live2d_v5_1/hair_fix_manifest.json)、[hair_seam_test.json](../live2d_v5_1/reports/hair_seam_test.json)。

### 历史版本（摘要，详情见各 README）

- v4：十个眼部/眉毛独立生成件，33 层 PSD；19 项检查、11 种视线、PSD 回读通过。
- v3：RGBA 视线裁切修复、官方透明头发分件、浏览器极限视线测试；仍保留 35 层 PSD 和离线预览。
- v2：精修母版、完整移动虹膜/眼白、35 层 PSD、鼠标视线原型；v3 修正了灰度遮罩穿模。
- v1：新全身正面母版与初版拆层，保留作对照。

## 未完成与待验证

### 当前已知问题

- 现有头发主要是三片结构：`hair_back`、`hair_front_fixed`、`hair_fringe_center`。后发层次和隐藏部分不足；固定前发混合了发冠、左右侧发、发饰/挑染等不同运动关系。
- 角色头发移动时，耳朵可能不自然露出或出现遮挡错误；现有结构不适合直接进入较大幅度头部转动开发。
- v5.1 只修了耳根/脸颊边缘，没有重构后发、发冠、左右前侧发，也没有解决运动状态遮挡。

### 待验证

- v5.1 的人工视觉审查与是否采用。
- 头发移动时耳根、后发、脸颊边缘的连续性和露底情况。
- 运动状态下完整头发与双耳遮挡。
- Cubism 绑定和 CMO3 在 Cubism Editor 中的实际编辑兼容性。
- 目标运行时播放、物理实际播放和统一调色。

### 不要误报为已完成

- 不能因为已有 33 层 PSD、预览页或 PSD 回读零差异，就声称已完成 Cubism 绑定。
- 不能把 `AngleX ±5°` 的旧 phase3 审阅动作当作 v5 的 ±30° 转头验证。
- 不能把 v5.1 的自动化检查当作最终美术验收。

## v6：头发分层重构与重新生图计划

**状态：计划阶段，尚未实施；v6.1–v6.4 均为待实施。** 本阶段只重构头发，不重做已验收的眼睛、眉毛、脸、耳朵、鼻嘴和身体素材。

### 目标

- 建立能支持较小幅头部转动和发片运动的头发结构。
- 让发束在移动时具有足够隐藏根部，不露空洞、硬切口或错误边缘。
- 保持发型、配色、挑染、发饰和整体比例与原始角色一致。
- 先验证结构，再批量生图；避免结构未定时重做全部头发。

### 候选结构

以下只是候选，不要求机械拆成固定层数：

- 后发与后脑完整隐藏部分；
- 必要的左右后侧发；
- 发冠及相对固定部分；
- 左侧前侧发；
- 右侧前侧发；
- 中央刘海；
- 其他确实需要独立运动的局部发束。

发饰、挑染等如果不需要独立运动，优先保留在对应发片中，避免无意义增加图层。每片发束必须包含被上层遮住的隐藏根部，而不是只生成可见轮廓。

### 生图规则

- 默认使用 Codex 官方内置生图，意向 `gpt-image-2.5-sunburst`；内置工具若不暴露模型参数，不能声称实际指定成功。
- 只有用户明确说明使用 API 生图时，才允许走 API/BeefAPI。本轮维护和 v6 默认都不调用 API。
- 使用统一原始参考图（`参考/原始参考图/`）分析发型、轮廓和遮挡顺序。
- 先确定发束边界、锚点和层级，再生成需要替换的分件。
- 完整独立分件生图；抠图只做隔离和修边，不从旧合成头发裁剪冒充分层。
- 每片保留隐藏部分；逐片检查/验收后再整合 PSD 与 Manifest。
- 不重生成整个角色，不覆盖 v5 已验收的六层脸部和眼部/眉毛素材。

### 实施顺序

#### v6.1 头发结构分析（待实施）

- 基于原始参考图与 v5 现有分层，确认发束拆分、前后层级、耳朵遮挡关系和资产复用范围。
- 产出一份结构方案和锚点/边界表；不先批量生图。
- 验收：结构方案能解释正常状态和侧发小幅移动时的遮挡关系。

#### v6.2 最小 PoC（待实施）

- 先选一侧耳朵及其对应侧发，完成独立生图、局部合成、小幅移动和遮挡测试。
- 检查耳根是否露出、是否存在明显缝隙、能否自然遮住/露出耳朵。
- 验收：单侧 PoC 的图层、锚点、隐藏根部和移动表现通过人工视觉检查后，再扩大范围。

#### v6.3 完整头发重建（待实施）

- PoC 通过后，完成后发、左右后侧发、发冠、左右前侧发、中央刘海等必要分件。
- 保持发饰/挑染归属合理；每个分件单独验收，不整批盲替换。
- 验收：每层在白色/深色/棋盘背景下无脏边、硬矩形和错误残片；隐藏区足够。

#### v6.4 集成与验收（待实施）

- 整合 PSD、Manifest、预览和相关脚本；更新 v6 版本目录与说明。
- 重点检查：
  - 正常状态的角色还原程度；
  - 三种背景下的透明边缘；
  - 100% 与局部放大细节；
  - 移动时是否露底、断裂、穿帮；
  - 双耳遮挡是否自然；
  - 发束连接是否连续；
  - v5 已验收面部素材是否被破坏。
- 验收：自动化检查 + 人工视觉检查 + v5 回归全部通过后，才能把 v6 标为交付。

### v6 Checklist（全部未开始）

- [ ] v6.1 发束结构、锚点、前后层级和耳朵遮挡关系定稿
- [ ] v6.2 单侧耳朵 + 对应侧发最小 PoC 生图与局部合成
- [ ] v6.2 PoC 人工视觉验收：耳根不露、缝隙可接受、可自然遮/露耳朵
- [ ] v6.3 后发与后脑隐藏部分
- [ ] v6.3 左右后侧发、发冠、左右前侧发、中央刘海
- [ ] 每片隐藏根部与透明边缘检查
- [ ] 双耳与运动状态遮挡回归
- [ ] v6 PSD、Manifest、预览和脚本整合
- [ ] v5 面部六层、眼部十件和身体层回归
- [ ] 文档记录仍未完成的 ±30° 转头与绑定限制

### v6 交付物（计划）

- 新的头发分件原图、清理图、注册 Manifest、PSD、预览页和验证报告。
- 一份明确的层结构/锚点说明。
- 与 v5 的面部六层、眼部十件和身体层的回归对照。
- 若仍不能支持 ±30° 转头，必须在文档中保留该限制，不能把 v7 目标写成 v6 已完成。

## v7 后续方向

在 v6 头发结构稳定后，再研究 ±30° 头部伪 3D 转动、ArtMesh/Deformer 方案、运动状态完整遮挡和运行时绑定。v7 不属于 v6 交付范围。

## 本次维护验证（2026-10-27）

- v5 Python 回归：24/24 通过（`uv run --offline --with pillow --with numpy --with scipy python -m unittest discover -s live2d_v5/scripts -p 'test_*.py' -v`）。
- v5 预览页真实 Chrome 检查：通过（加载、联动/独立视线、复位、缩放、发片、图层开关、无运行时错误）；报告写入 `/tmp`，未覆盖项目报告。
- v5.1 Python 回归：29 项中 28 通过、1 失败（`screen_right` / `hair_front_fixed` 眼睑重叠 112 > 基线 99）；因此 v5.1 继续标记为未验收。
- v5.1 预览页真实 Chrome 检查：通过；只说明页面可加载和交互，不代表边缘美术通过。
- `live2d_v5` 与 `live2d_v5_1` 的全部文件哈希与移动前快照逐项比对：除两个 README 和随后清理的 macOS `.DS_Store` 元数据外无变化；v5 PSD、Manifest、verification 关键哈希不变。
- 归档管线抽查：`archive/legacy_character_pipeline/phase3/verification` 6 项测试通过，说明移动后 phase1/2/3 相对路径与 `references` 链接仍可用。
- Codex 配置未改：`./scripts/codex-live2d` 可加载 `live2d` Profile 与 `live2d-reviewer`；当前官方线路下 `beefapi` 显式校验按预期拒绝。
- 文档本地链接检查：20 个主要 Markdown 文件，0 个缺失链接。
- 未运行：会写入 `live2d_v5/reports/` 的 face inspector/gaze 浏览器测试，避免覆盖既有验收报告。

## 历史记录

| 日期 | 里程碑 | 记录 |
|---|---|---|
| 2026-10-26 | phase1：旧角色 Canvas/校准与三态眼 | [归档说明](../archive/legacy_character_pipeline/README.md) |
| 2026-10-26 | phase2：19 层 PSD、真实 MOC3/CMO3、官方 Core 验证 | [phase2 README](../archive/legacy_character_pipeline/phase2/README.md) |
| 2026-10-26 | phase3：眨眼互补交接、20 层 PSD、发片接缝底层 | [phase3 README](../archive/legacy_character_pipeline/phase3/README.md) |
| 2026-10-26 | phase4：PixiJS + 官方 Core 的 WebGL 播放器 | [phase4 README](../archive/legacy_character_pipeline/phase4/README.md) |
| 2026-10-27 | v1–v4：新母版、视线修复、眼部第一组 | [v4 README](../live2d_v4/README.md) |
| 2026-10-27 | v5：脸部第二组，当前交付 | [v5 README](../live2d_v5/README.md) |
| 2026-10-27 | v5.1：耳根/脸颊边缘修补实验，未验收 | [v5.1 README](../live2d_v5_1/README.md) |

旧 phase1–4 的详细验证边界保留在归档 README 和报告中；本文件不重复整段旧日志，也不改写当时的结论。

## 文档与归档

- 项目入口：[README](../README.md)
- Codex 配置：[codex/README.md](../codex/README.md)
- Agent 规范：[AGENTS.md](../AGENTS.md)
- 归档索引：[archive/README.md](../archive/README.md)
- 移动记录：[archive/move_manifest.json](../archive/move_manifest.json)
- 原始角色参考：[参考/原始参考图/README.md](../参考/原始参考图/README.md)
- 历史逐层分析：[docs/layer-audit-v3/图层分析与逐层生图方案.md](layer-audit-v3/图层分析与逐层生图方案.md)
