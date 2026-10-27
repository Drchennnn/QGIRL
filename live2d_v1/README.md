# 正面母版与拆层 v1

> 状态：历史版本，保留追溯。当前交付为 v5；旧 phase1–4 已归档到 `archive/legacy_character_pipeline/`。

2026-10-27，接续聊天「设计日系酷感常服角色板」。最新确认范围为彩色头部 + 纯白人台素体，发饰位于屏幕左侧（角色自身右侧）。原服装设计与旧 phase1–4 资产未改动。

## 交付

- `assets/front_master_clean.png`：1024×1536 透明母版。保留主体 RGB，仅清理 API 背景 alpha 残留并归一化不透明主体。原始图在 `generation/front_master.png`。
- `packed/character_front_v1.psd`：37 层 RGB 8-bit PSD，包含 23 个头部分件和 14 个身体分件。
- `assets/head/`、`assets/body/`：同一 1024×1536 坐标的 RGBA PNG。图层顺序见 `manifest.json`，从底至顶。
- `角色拆层检查.html`：离线单文件图层开关、单图层位移与脸底检查。
- `reports/delivery_preview.jpg`、`reports/head_layers.jpg`、`reports/motion_samples.jpg`：整体、头部拆层、小幅位移证据。

## 补绘方法与验证范围

本轮未再调用生图 API。脸底和后发采用局部纯色补绘，眼白补齐虹膜下遮挡；头发、耳部和身体关节采用源像素延伸。补绘处均由中性姿态前景完全遮盖，所有原有可见主体颜色保留。它是可复现的拆层原型，不是逐片精修的美术终稿。

中性 PNG 重组与清理母版相同，PSD 逐层解码重组也完全相同；验证 JSON 位于 reports 和 packed。刘海横移 ±3px、虹膜横移 ±2px 的指定头部内部区域未新增透明空洞。此项只验证透明覆盖，不等于完整运动质量：刘海位移仍可见少量抗锯齿残边，复杂转头、关节旋转、眼睑闭合尚需精修与绑定阶段验证。

未创建 Cubism 网格、变形器、参数、物理、CMO3 或 MOC3；未声称可直接用于 VTube Studio。上衣、裤子、鞋包尚未加入此白模拆层。

## 重建

在项目根目录依次运行：

```sh
uv run --offline --with pillow --with numpy --with scipy python live2d_v1/scripts/clean_master.py
uv run --offline --with pillow --with numpy --with scipy python live2d_v1/scripts/build_body.py
uv run --offline --with pillow --with numpy --with scipy python live2d_v1/scripts/build_head.py
uv run --offline --with pillow --with numpy --with scipy python live2d_v1/scripts/verify_and_preview.py
uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v1/manifest.json --output-dir live2d_v1/packed --stem character_front_v1
```
