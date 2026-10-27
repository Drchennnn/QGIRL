# 眼部第一组 v4：十个官方生成独立分件

> 状态：历史基线，保留追溯。当前交付为 v5；v4 仍被 v5 回归测试直接引用，不能移动。

2026-10-27，接续逐层分析。此轮只完成眼部第一组；v3 完整保留。头发、脸底、耳、鼻嘴、身体等非眼组仍沿用 v3，尚未执行分析报告中的后续组。

## 交付入口

- `眼部第一组_独立分件检查.html`：自带全部图片的离线检查页；十个部件可在棋盘/白/深底查看，切换生成母资产、原生大小、坐标图4倍显示。
- `视线与发片精修预览.html`：装配后的角色与鼠标跟随，保留双眼联动/独立、图层开关、刘海滑杆、头部/全身和复位。
- `packed/character_front_v4.psd`：33层、1024×1536、RGB8。静态显示层保存中性裁切虹膜和眼白；完整母资产在 PNG 中另存。
- `generation/eyes/`：十个生成原件、清理后的大图、四个未采用的首版候选、原始正面母版裁剪参考和逐次提示词。
- `eye_manifest.json`：十个原件/注册文件的路径、双份哈希、有效边界、等比缩放与平移记录，以及完整母资产/显示导出区分。

## 实际完成内容

左右各五件：上眼睑/上睫毛、下眼睑/下睫毛、完整眼白、完整虹膜、细眉毛。所有十件的美术像素来自 Codex 官方内置 image_gen；本轮没有从旧眉层、旧下睑、头发或肤色块抽样补图，也没有用程序曲线重画眼睑或虹膜。

共14次官方调用：十件首版，随后分别返修左右虹膜高光位置、左右下睑弧度，共4次。首版下睑过浅、虹膜高光过高，不作为最终装配；候选仍留在 `*_candidate1.png`。实际提示词逐次保存于 `generation/eyes/generation_log.json`。

完整生成件保持透明背景，先去少量孤立碎屑；眼白仅在大图尺寸做2px级alpha边界清理。此后统一等比缩小、平移到现有1024×1536坐标，保留原始大图，未做横纵不等比拉伸。小图可能仍受最终几十像素的有效尺寸限制，不能把放大后像素可见说成已经无限精细。

## 完整母资产与显示导出

- `assets/eyes/iris_full_screen_left/right.png`：完整可移动虹膜，顶端和底部都保留，不是被上睑切断的片。
- `assets/eyes/eyewhite_full_screen_left/right.png`：完整眼白注册底图，含显示开口以外的隐藏覆盖。
- `assets/eyes/iris_screen_left/right.png`、`eyewhite_screen_left/right.png`：当前中性眼眶的静态显示导出，供PSD和中性合成使用。
- 上下眼睑：四个独立PNG，保留自然尖角与有意的两根小下睫毛；不会把设计性断笔误删成碎屑。
- 眉毛：`assets/hair_refined/brow_screen_left/right.png`。只有干净细眉，不再夹带大片头发；位置保持固定，未加入眉毛运动。

灰度/透明度遮罩是技术派生，不是生图分件。开口保留既有眼眶锚点，并按生成上下眼睑的实际边界收口，减少新线条与旧开口间的漏白。CPU用L模式灰度，浏览器用真正RGBA透明度，保持二者逐像素一致。虹膜移动后才裁切，最后绘制固定眼睑；前发仍在五官上方。

## 视觉检查与边界

本次验证：5项生成分件检查、5项眼睑遮挡检查、9项交付检查，共19项通过；浏览器11个视线姿态没有可见眶外变化，左右眼独立输入不改变另一只眼，复位回到原画面。33层PSD回读零像素差异，非眼部23层与v3字节一致。独立分件页10张图、三背景和三种显示尺度均已在Chrome载入与切换检查，页面错误为0。

`reports/eye_group_components.png` 展示十个完整母资产的坐标注册结果，`eye_group_screen_left/right_backgrounds.png` 展示双眼组合在白/深/灰底的对比。`eye_inspector_browser.png` 是实际浏览器分件页截图。大图原件保留更高细节，坐标图以实际使用尺寸验收。

这轮改变了眼部笔触、虹膜色阶和睫毛形状，是新的美术候选，不声称与旧中性图零差异。初步视觉检查显示旧眉毛头发块、旧下睑源图残色已去除；最终审美仍可通过独立分件检查页逐项比较。头发、脸底等分析报告已列出的旧问题仍待后续组处理。

只验证当前小幅鼠标视线范围：水平±4px、垂直±2px。未新增摄像头追踪、眨眼、表情、Cubism绑定、CMO3/MOC3导出；PSD回读成功不等于目标软件兼容。

## 生图路径

仅使用官方内置 image_gen，未使用API key、BeefAPI或其它第三方调用。工具没有模型选择参数或型号回报，因此没有声称已指定 gpt-image-2.5-sunburst。

## 重建与验证

以下构建命令不再发生生图，读取已保存的十个原件。项目根目录执行：

```sh
uv run --offline --with pillow --with numpy --with scipy python live2d_v4/scripts/refine_eyes.py
uv run --offline --with pillow --with numpy python live2d_v4/scripts/build_delivery.py
uv run --offline --with pillow python live2d_v4/scripts/build_eye_inspector.py
uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v4/manifest.json --output-dir live2d_v4/packed --stem character_front_v4
uv run --offline --with pillow --with numpy python live2d_v4/scripts/test_assets.py
uv run --offline --with pillow --with numpy python live2d_v4/scripts/test_eye_artwork.py
uv run --offline --with pillow --with numpy python live2d_v4/scripts/test_eye_occlusion.py
node live2d_v4/scripts/test_preview.cjs
node live2d_v4/scripts/test_gaze_browser.cjs
```

`refine_hair.py` 是为追溯保留的 v3 历史头发脚本，不属于本轮重建链：直接运行它会恢复旧眉毛。此次不修改原头发资产，也不将旧头发脚本当作眼部构建入口。
