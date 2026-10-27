# 角色精修 v2 — 视线准备与交互原型

> 状态：历史版本，保留追溯。当前交付为 v5；旧 phase1–4 已归档到 `archive/legacy_character_pipeline/`。

2026-10-27。保留 v1，所有新版资产位于 live2d_v2。范围仍为彩色头部＋白色素体；服装设计不在本轮拆层范围。

## 交付入口

- 视线与发片精修预览.html：完全离线、自带图层，支持鼠标视线、双眼联动、左右眼独立 X/Y、刘海根部固定摆动、图层开关、全身/头部切换与复位。
- packed/character_front_v2.psd：35 层，1024×1536，RGB 8-bit。
- assets/eyes：完整移动虹膜、眼白、眼眶/睫毛遮挡层及 aperture 遮罩。
- assets/hair_refined：精修脸底、发片、耳、发饰和面部特征。
- reports/gaze_nine.png：九方向视线检查；reports/preview_browser.png 为真实浏览器截图。
- reports/verification.json：18项左右眼×九方向裁切检查；reports/browser_test.json 为浏览器交互验证；packed/character_front_v2_report.json 为 PSD 回读证据。

## 本轮改动

虹膜边缘原先混有眼白和固定睫毛，简单平移会出现白边/残影。本轮局部重绘完整深蓝虹膜、青蓝 U 形纹样和高光；眼白补齐后固定，虹膜移动后再通过固定 aperture 裁切。外观有局部变化，原版本完整保留供对比；不声称新版中性与 v1 零差异。没有使用外部生图服务。

头发修复采用颜色/透明度解混及脸底补全；刘海采用发根固定、下端渐变位移。PSD 是静态分层美术，浏览器的裁切与变形逻辑不自动存在于 PSD 里。PSD 中保存的是中性裁切虹膜，完整移动虹膜另存 PNG，绑定时应使用完整图并建立裁切。

接续修复：脸底新增区限制在额头，避免覆盖耳层上的侧发；PSD 中性虹膜与交互预览统一使用相乘的软遮罩。构建会断言静态分层与运行时中性合成一致，资产测试另检查侧发未被肤色覆盖、PSD 输入哈希和交付合成。

后续若需要生图，使用 Codex 官方内置生图，暂停 API 与第三方生图。优先模型意向为 `gpt-image-2.5-sunburst`；当前工具未开放模型选择，实际模型不可指定。本次接续修复未发出生图请求。

## 眼球追踪在哪一步

1. 本轮：准备虹膜、眼白和遮挡边界，验证眼球移动；鼠标跟随原型已实现。
2. 正式绑定：在 Cubism 建立眼球 X/Y 的网格和关键形，设置眼白裁切；另做左右眨眼和闭合形态。
3. 输入接入：导出模型并把摄像头/人脸捕捉输出映射到模型视线参数；校准方向、中心、幅度、平滑与丢失回正。此步骤未实施，预览不会访问摄像头。

当前浏览器采用屏幕坐标，X 正值向右、Y 正值向下，控制值限制在 -1..1。正式接入时需按目标模型的参数定义校准方向，不能直接照搬屏幕坐标。

本轮默认幅度为水平 ±4px、垂直 ±2px；是这张母版的保守预览范围，不是正式模型的最终参数。

## 验证边界

已验证实际浏览器载入、鼠标联动、左右眼独立、复位、发片滑杆和无 JavaScript 运行错误；九方向裁切检查只证明虹膜不会画到遮罩外。未实现摄像头追踪、眨眼、转头、物理、CMO3/MOC3 导出或 Cubism 导入实测。发片大幅运动及整套动作仍需绑定后的逐帧检查。

本次重建：5 项资产回归测试通过，18 项左右眼×九方向裁切检查通过；35 层 PSD 回读与输入分层零像素差异，静态分层与运行时中性合成零像素差异。浏览器额外验证了左右眼数值同步、缩放/发片/显隐确实改变画面，以及复位逐像素恢复。相对 v1 的中性外观有 2443 个像素变化，主要来自虹膜与分层边缘处理。

这仍是小幅运动原型。原始头部像素较少，放大或将刘海推到极限位置时可见细小锯齿及交接残边；裁切通过不代表已达到逐片美术终稿。`reports/delivery_head.jpg` 与 `reports/preview_browser.png` 为本次重建后的预览。

## 重建

在 /Users/Link/code/Character 下依次运行：

- uv run --offline --with pillow --with numpy --with scipy python live2d_v2/scripts/refine_hair.py
- uv run --offline --with pillow --with numpy --with scipy python live2d_v2/scripts/refine_eyes.py
- uv run --offline --with pillow --with numpy python live2d_v2/scripts/build_delivery.py
- uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v2/manifest.json --output-dir live2d_v2/packed --stem character_front_v2
- node live2d_v2/scripts/test_preview.cjs
- uv run --offline --with pillow --with numpy python live2d_v2/scripts/test_assets.py

浏览器测试使用当前机器已安装 Chrome 和捆绑 Playwright，不新增项目依赖。
