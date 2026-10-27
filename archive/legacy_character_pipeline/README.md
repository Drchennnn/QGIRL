# 旧角色管线（phase1–phase4）

2026-10-27 从项目根目录整体归档。这里是旧角色的 Canvas/校准、PSD 与 Cubism 导出、眨眼交接和 WebGL 播放器，不是当前 `live2d_v5` 的交付链。

## 内容

| 路径 | 原用途 |
|---|---|
| `phase1/` | 旧角色校准、三态眼、41 帧眼部采样、离线 Canvas 对比页 |
| `phase2/` | 19 层 PSD、真实 MOC3/CMO3 导出、官方 Core 验证 |
| `phase3/` | 眨眼互补交接、20 层 PSD、发片接缝底层、小幅动态审图 |
| `phase4/` | PixiJS + 官方 Core 的本地 WebGL 播放器 |
| `outputs/` | 旧表情资产、校准参数、调参器、旧对照图 |
| `work/` | 旧图像处理脚本、BeefAPI 生图入口、旧测试 |
| `src/` | 旧管线的固定基础图层 |
| `DESIGN.md` | phase4 播放器的设计说明（历史） |
| `references` | 指向根目录 `../../references/` 的符号链接，供旧脚本读取 L2Dviewer/Auto_Vtb 与凭据 |

注意：当前 v5 使用的 PSD 打包入口已移到根目录 `scripts/live2d_v1_pack.py`，不在本归档的 `work/` 中。

## 追溯

- `phase2/README.md`、`phase3/README.md`、`phase4/README.md` 保留原始说明和验证边界。
- `phase1/第一阶段_动态对比_离线.html` 和 `phase1/reports/` 保留旧原型证据。
- 这些记录只证明旧角色管线当时的状态，不代表当前 `live2d_v5` 已完成 Cubism 绑定、±30° 转头或动态头发遮挡。

## 迁移记录

- 旧工作区的 `outputs/`、`work/` 业务文件在迁移时已核对 SHA256；逐文件记录保留在根目录 `references/migration_verification.json`。
- 原角色 `IMG_3022.png` 与旧 `src/character_base.png` 字节一致；两者现在分别保存在 `参考/原始参考图/` 与 `archive/legacy_character_pipeline/src/`。
- 旧 `.omx` 会话状态、Swift/Python 编译缓存和当前 v5 的生成/验收报告不属于本归档。

## 运行

旧管线不是当前构建入口。如确需复现历史结果，先进入本目录，再按各 phase README 的命令执行；`references` 符号链接使旧的 `references/...` 相对路径继续可用。运行可能依赖旧工具链和已下载的 JDK/Gradle 缓存。
