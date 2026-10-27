# 角色精修 v3：真实透明度裁切与干净头发分件

> 状态：历史版本，保留追溯。当前交付为 v5；旧 phase1–4 已归档到 `archive/legacy_character_pipeline/`。

2026-10-27。工作目录 `/Users/Link/code/Character`。原母版、v1、v2 和旧 phase1–4 保留。

## 穿模原因与修复

旧浏览器将 L 模式灰度 PNG 直接用于 Canvas `destination-in`。此操作读取 alpha，而灰度 PNG 的黑色背景仍是 alpha=255，所以完整虹膜并未被裁掉。CPU 使用灰度值做 ImageChops.multiply，因而旧 CPU 裁切检查不能证明浏览器正确。

v3 分别保存两种遮罩：`aperture_{side}.png` 为 CPU 灰度几何，`aperture_alpha_{side}.png` 为浏览器真正 RGBA 透明遮罩，二者 alpha/灰度逐像素一致。新浏览器回归在旧版明确复现 alpha=255 的错误，在新版验证背景 alpha=0、实际视线移动及眼眶以外的画面稳定。

图层从底至顶：脸底 → 眼白 → 完整虹膜 → 下眼睑 → 上眼睑/睫毛 → 眉毛 → 固定前发 → 独立刘海。虹膜不放整个人物最底层。原矩形 eye_socket 已退出分层，固定眼白和眼睑不再包含旧虹膜。眼眶改用超采样曲线；保留原开眼高度、小幅 ±4px/±2px 范围及左右独立控制。

## 头发分件

本轮通过 Codex 官方内置 image_gen 生成一张真正透明的头发隔离图，移除了脸、眼、眉、耳、颈和肤色碎片；保持短深蓝发、白色内挑染及屏幕左侧黄绿发饰。输入、完整提示词和原始输出见 `generation/`。无第三方服务或 API key 调用。工具未提供模型选择或型号回报，不能保证使用了 gpt-image-2.5-sunburst。

新分件配准至原头部坐标，并恢复原耳部开口。前发与独立刘海分开，发根 y≤132 固定，至 y=176 达到最大 ±3px 位移；静止前发下不再保留一份会露出的旧刘海。脸底清除隐藏的头发/眼部碎片，颈部接缝用原母版皮肤像素补齐。

生成图的轮廓、笔触及挑染形状有小幅变化，这是 v3 新美术候选，不声称与原图零差异。发饰与白色挑染当前随固定前发保存；不具备独立摆动的隐藏补绘。

## 交付与验证

- `视线与发片精修预览.html`：完全离线，鼠标视线、独立双眼、刘海摆动、图层显隐与复位。
- `packed/character_front_v3.psd`：33 层、1024×1536，RGB 8-bit，静态中性裁切虹膜。完整移动虹膜另存 `assets/eyes/iris_full_{side}.png`。
- `reports/preview_browser.png`、`preview_hair_plus3.png`、`preview_hair_minus3.png`：真实浏览器截图。
- `reports/gaze_browser_test.json`：真实浏览器透明度契约及 11 个极限/分数视线位置；显示颜色比较允许 1.1/255 级舍入误差，避免 Chrome 透明度读回的量化差被误判为运动。
- `scripts/test_eye_occlusion.py`：6 项几何与固定眼睑遮挡检查，使用完整运行时虹膜。
- `scripts/test_assets.py`：8 项交付检查，含 RGBA/灰度遮罩一致、头发无肤色碎片、无固定旧刘海、颈部无新增透明洞、层序、静态/运行时/PSD 一致及输入哈希。

本次验证：8 项交付测试、6 项几何测试、11 个浏览器视线位置及交互测试全部通过；PSD 分层回读零像素差异，静态分层与运行时中性合成零像素差异。浏览器前后对比见 `reports/browser_before_after.jpg`，九方向实拍见 `reports/gaze_browser_nine.png`。

这些验证覆盖当前小幅鼠标原型。未实现摄像头追踪、眨眼、转头、物理、Cubism 绑定或新母版 CMO3/MOC3 导出。PSD 回读是分层包装验证，不等于 Cubism Editor/VTube Studio 兼容性。

## 重建

在项目根目录依次执行，均不会再发出生图请求：

```sh
uv run --offline --with pillow --with numpy --with scipy python live2d_v3/scripts/refine_hair.py
uv run --offline --with pillow --with numpy python live2d_v3/scripts/refine_eyes.py
uv run --offline --with pillow --with numpy python live2d_v3/scripts/build_delivery.py
uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v3/manifest.json --output-dir live2d_v3/packed --stem character_front_v3
uv run --offline --with pillow --with numpy python live2d_v3/scripts/test_assets.py
uv run --offline --with pillow --with numpy python live2d_v3/scripts/test_eye_occlusion.py
node live2d_v3/scripts/test_preview.cjs
node live2d_v3/scripts/test_gaze_browser.cjs
```

浏览器测试复用本机 Chrome 与捆绑 Playwright，未新增项目依赖。
