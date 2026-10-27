# 脸部第二组 v5

> 状态：当前已验收交付（2026-10-27）。v5.1 只是未验收的头发边缘修补实验，不替代本版本。

2026-10-27。接续 v4，完成完整无五官脸底、左右耳、鼻部软阴影、中性闭口线与头颈连接，共六个独立分件。v4 完整保留；只更新六层，其余27层（含十个眼眉件、三片头发、十四个身体件）与v4字节一致。

## 交付入口

- `脸部第二组_独立分件检查.html`：六件离线检查页，棋盘/白/深底，生成母资产/原生1×/坐标4×。
- `视线与发片精修预览.html`：新脸装配，保留鼠标视线、独立双眼、图层开关、刘海小幅摆动和复位。
- `packed/character_front_v5.psd`：33层、1024×1536、RGB8。
- `reports/delivery_head.jpg`、`face_group_before_after.jpg`：最终头部与v4/v5对照。
- `reports/face_group_components.png`、`face_assembly_three_backgrounds.png`：独立母资产与去头发三背景组合，可查看隐藏区、耳根和下颌。

## 分件与处理

| 图层 | 内容 | 注册有效尺寸 |
|---|---|---|
| face | 完整颅顶、额头、太阳穴、脸颊、连续下颌与下巴；无五官、耳、发或颈 | 189×239 |
| ear_screen_left | 屏幕左耳，含内耳与隐藏耳根 | 24×46 |
| ear_screen_right | 屏幕右耳，含内耳与隐藏耳根 | 26×48 |
| nose | 软鼻影，周围真实透明 | 2×7 |
| mouth | 两段式细浅笑闭口线，周围真实透明 | 28×3 |
| neck_bridge | 头颈连接，保留白色人台/高领衔接，不含下颌线 | 80×59 |

所有新美术RGB来自官方内置image_gen。共7次请求，6次成功；鼻子首个请求失败后重试成功。未使用API key、BeefAPI或第三方生图。工具不暴露模型参数或型号回报，不能确认已指定gpt-image-2.5-sunburst。逐次提示词与状态见 `generation/face/generation_log.json`。

原图与清理后的完整大图保留在 `generation/face/`。清理只移除孤立碎屑，对脸、耳和连接件做母图尺寸3px开运算/2px闭运算与0.7px alpha平滑；不重画RGB，不从旧图抽取肤色或五官。此后等比缩小一次并平移到眼睛/下巴锚点；变换和哈希见 `face_manifest.json`。

耳根放在脸底下面，脸底之后绘制眼睛。头颈完整母件保留；注册导出在y294–303对底端alpha渐隐，与原白色颈部重叠，避免母件闭合底线横压在旧颈上。这是技术衔接，不是新绘制部件。

用户在双耳已生成后补充：后续对称结构优先生成一侧，再镜像配准；明确不对称设计另行保留。这次两个已生成耳件均保存，未再为对称结构重复生图。

## 验证

- 24项Python检查通过：脸部美术5、交付与PSD9、眼部美术5、眼球遮挡5。
- 其余27层逐文件字节一致；六个更新层全部实际变化。双耳位于脸底下方。
- 实际Chrome：六图检查页三背景、三模式，0页面错误；装配页联动/独立视线、复位、缩放、发片及图层开关通过。
- 11个视线姿态及双向独立眼测试，眶外0可见变化；复位恢复。PSD输入哈希与中性回读一致，封包回读零像素差异。
- 视觉核验：新脸底没有原来的下颌缺口，鼻嘴不带肤色方块，装配没有双下颌线或连接处暗横带。独立看连接件底端的白色淡出是预期衔接。

## 范围与后续

这是正面完整分件准备，额头、脸颊、耳根可用于后续变形准备；尚未验证左右约30°转头覆盖，也未生成多视角参考、制作网格关键形态、添加眨眼、摄像头输入或新模型Cubism绑定。视线范围仍是水平±4px、垂直±2px。

头发与身体继续保留上一版的待修问题。下一组是完整后发、固定前发与中心刘海，之后再进入身体及头部多视角参考/网格阶段。最终1024画布中的细五官只有几像素，放大时仍会显示像素，不能声称无限精细。

## 重建

以下命令只读取已保存原图，不发生生图。项目根目录执行：

```sh
uv run --offline --with pillow --with numpy --with scipy python live2d_v5/scripts/refine_face.py
uv run --offline --with pillow --with numpy python live2d_v5/scripts/build_delivery.py
uv run --offline --with pillow python live2d_v5/scripts/build_face_inspector.py
uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v5/manifest.json --output-dir live2d_v5/packed --stem character_front_v5
uv run --offline --with pillow --with numpy --with scipy python -m unittest discover -s live2d_v5/scripts -p 'test_*.py'
node live2d_v5/scripts/test_face_browser.cjs
node live2d_v5/scripts/test_preview.cjs
node live2d_v5/scripts/test_gaze_browser.cjs
```

`refine_hair.py`是继承的历史脚本，不属于重建链；不要运行它覆盖本轮脸底和已验收眉毛。眼部原件与 `refine_eyes.py`为追溯保留，本轮不需重生成或重新配准眼睛。
