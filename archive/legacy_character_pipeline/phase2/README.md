# 第二阶段：真实模型导出 PoC

> 已归档（2026-10-27）。以下为旧角色管线当时的记录，路径相对于 `archive/legacy_character_pipeline/`；当前交付与 v6 计划见根目录 `README.md` 和 `docs/PROGRESS.md`。

2026-10-26。输入沿用第一阶段的校准与绘画素材，不调用生图 API，不统一调色。

## 交付文件

- `assets/character_calibrated.psd`：19 层、RGB8、612×1091；中性合成与第一阶段候选可见像素差异为 0。原闭眼层按既有左右坐标与旋转保存，默认隐藏；眉毛独立。
- `assets/character_minimal.psd`：用于自动绑定的候选。仅在虹膜下方补眼白，让 Cubism 眼白遮罩覆盖完整眼眶。原始半透明虹膜叠加新底图后，中性整图 740 个像素有细微变化；眼部源图最大通道变化 6/255。原版 PSD 和原始 PNG 保留。
- `assets/layer_manifest.json`：图层顺序、裁剪矩形、可见性、坐标约定与 SHA256。
- `exported/character_minimal/`：真实 MOC3、CMO3、model3、纹理、物理及动作等文件。
- `reports/sdk_character.json`：官方 Core 的实际加载与参数计算结果。
- `reports/core_neutral_comparison.png`、`core_eye_contact.png`：使用官方 Core 顶点快照进行本地 CPU 光栅化，供视觉比较。

## 重新生成

```sh
cd /Users/Link/code/Character/archive/legacy_character_pipeline
uv run --with psd-tools --with pillow --with numpy python phase2/build_psd.py
```

PSD 导出时使用透明通道，不把 PNG alpha 转成额外图层蒙版。保存后重新解码各层通道，要求与输入合成差异为 0。`reports/psd_checks.json` 记录检查。

实际引擎使用 `engine/run_export.sh`，具体命令与源代码适配见 `reports/engine_README.md`。采用隔离副本构建，不修改固定的参考仓库。构建需要项目内的 JDK21 和 Gradle 缓存；首次下载依赖需要网络。

```sh
node phase2/verification/validate_core.mjs \
  phase2/exported/character_minimal/character_minimal.moc3 \
  phase2/reports/sdk_character.json phase2/reports/sdk_character_snapshots.json
uv run --offline --with pillow --with numpy python phase2/render_core_evidence.py
```

## 验证边界

官方 Core 的 consistency、Moc/Model 加载、参数计算与有限顶点检查，独立于 Auto_Vtb 的自读回检查。它能证实运行时二进制可用，但不能证明动画自然或 CMO3 可编辑。

离线审图用本地 NumPy 三角形光栅器处理 Core 输出的顶点、UV、透明度和遮罩；不是官方 SDK 渲染器截图，也没有运行浏览器、动作管理器或物理求解器。浏览器路径之前受到访问策略限制，本阶段没有绕过。

自动绑定的开合曲线与第一阶段 41 帧曲线不同；导出候选不替换已校准 Canvas 版本。闭眼线条、网格边缘与细小部件仍需逐项视觉比较。原源图的颜色差异也继续保留。

CMO3 已实际写出并由上游解析器回读；尚未在 Cubism Editor 打开。上游重建的是来自贴图的编辑图层，没有保留原始 PSD 完整编辑链，因此同时保留原版 PSD。

当前只有闭嘴素材；手部仍在衣服整层里。新手势、口腔、隐藏头发、较大转头和完整点击交互不属于本轮导出成功主张。下一轮应先处理当前模型眨眼的视觉差异，再补隐藏区与小幅头发运动，随后拆袖口/手臂/手势。
