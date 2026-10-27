# 第三阶段：眨眼交接与内部发片接缝底层

> 已归档（2026-10-27）。以下为旧角色管线当时的记录，路径相对于 `archive/legacy_character_pipeline/`；当前交付与 v6 计划见根目录 `README.md` 和 `docs/PROGRESS.md`。

2026-10-26（香港时间）。接续已审核第二阶段，本轮不调用生图 API、不统一调色。

## 查看结果

- [离线审图](第三阶段_离线审图.html)：自包含图片/GIF；它不是运行时模型播放器。
- [眨眼采样](reports/blink_phase3.gif)、[各档开合](reports/eye_contact.png)、[左右 Wink](reports/wink_contact.png)。
- [头发小幅采样](reports/hair_small_motion.gif)、[转头与呼吸](reports/small_motion_contact.png)、[底层对照](reports/hair_backing_comparison.png)。
- [20 层 PSD](assets/character_phase3.psd)；[模型入口](exported/character_phase3/character_phase3.model3.json)；同目录含真实 MOC3、CMO3、纹理、动作、表情、物理文件。
- [小幅审阅入口](exported/character_phase3/character_phase3.review.model3.json)：6 秒动作数据，头发参数 ±0.1、AngleX ±5°、呼吸、眨眼；此入口省略 Physics，避免覆盖审阅幅度。动作管理器播放尚未验证。

## 实际改动

1. 眼部互补延迟交接：opening≥0.25 时闭眼层透明度为 0；opening=0 时闭眼层完全显示，眼白/虹膜/睫毛隐藏。0.1～0.25 是交接区；Core 在导出关键帧间插值，不是严格 smoothstep。
2. 新增固定于头部的内部接缝底层，覆盖 12,619 像素，使用原坐标的原 RGB。在相邻发片交界 6px 范围提供底图；不延长外轮廓、不填面部开口、不覆盖耳朵。
3. 原 19 个 PSD 图层名称、矩形、可见性、RGBA 逐项不变。底层使中性合成 12,274 像素略有变化，最大通道差 15/255，接缝外变化 0；不声称整图零差异。
4. AI 头发候选因轮廓、发长、脸部开口变化未采用。此底层是原图像素延续，不是完整 AI 遮挡补绘；大幅转头和发片位移仍需新素材。
5. 已审核第二阶段资产、模型、报告全部通过保存哈希核对，未被覆盖。

## 验证结果

- 官方 Core 5.1.0 加载 MOC3：36 参数、20 Drawable、2,417 顶点、2 个遮罩，79 状态、23 检查通过。
- 左右眼单独/联动、0.249/0.25/0.251 临界值、图层互补与端点、眉毛参数锁定、头发不带动脸/耳/眉/底层通过。
- 头发参数 ±0.1 的发梢位移约 2.93～3.82px；估计根部位移约 0.04～0.15px。根部取顶部 20% 网格估算，并非强验收结论。
- sdk_phase3.json 为最终模型实测；负向回归能检出第二阶段重影机制与损坏 MOC。
- 阶段三资产 6 项、Core 回归 4 项、第一阶段资产/预览与生图路由测试通过。隔离引擎项目 JDK21 强制重跑 Gradle 测试 148 项通过（21 套件，0 失败/错误/跳过），记录见 reports/engine_tests.log 与 reports/delivery_checks.json。

## 复现

在归档根目录 `archive/legacy_character_pipeline/` 执行：

~~~sh
uv run --offline --with psd-tools --with pillow --with numpy python phase3/build_assets.py
phase2/engine/run_export.sh phase3/assets/character_phase3.psd phase3/exported/character_phase3
python3 phase3/package_review.py
node phase3/verification/validate_phase3_core.mjs phase3/exported/character_phase3/character_phase3.moc3 phase3/reports/sdk_phase3.json phase3/reports/sdk_phase3_snapshots.json
uv run --offline --with pillow --with numpy python phase3/render_evidence.py
node --test phase3/verification/validate_phase3_core.test.mjs work/tests/image_models.test.mjs
uv run --offline --with psd-tools --with pillow --with numpy python -m unittest discover -s phase3/verification -p 'test_*.py' -v
~~~

单独运行 Gradle 测试也必须使用 phase2/engine/run_export.sh 内的项目 JAVA_HOME 与 GRADLE_USER_HOME，不能依赖系统 Java。

## 边界与后续

图片来自真实 Core 顶点/UV/遮罩/透明度快照，经本地 CPU 光栅化。GIF 展示离散姿态，不是官方渲染器或物理求解器输出。浏览器、Cubism Editor 实际编辑、VTube Studio、动作管理器、物理播放仍未验证。原 physics3.json 保留，其全幅输出不受本轮 ±0.1 审阅范围自动约束。

仍有 11 条原导出诊断：左眼线/闭眼/嘴的小边界差异，以及 CMO3 原 PSD 编辑链未保留。CMO3 编辑图层来自贴图重建，原 PSD 单独保存。

本轮未制作新手势、袖口拆分、口腔，也未扩大头部转动范围。下一阶段从 Editor/目标运行时兼容性与动态视觉确认继续，再制作点击手部→抬杯→表情→待机。
