# v5.1 头发耳根/脸颊边缘修补实验（未验收）

2026-10-27。基线是 [v5](../live2d_v5/README.md)，不是独立的新角色版本。本轮只更新 `hair_front_fixed` 和 `hair_fringe_center` 两层；其余 31 层与 v5 字节一致，33 层结构、1024×1536 画布和已验收脸部六件不变。

## 目的

v5 的固定前发在双耳开口和脸颊外侧发梢处仍有硬切口/台阶。v5.1 用官方内置生图重新生成一张完整前发母图，修补：

- 屏幕左右耳开口的连续曲线；
- 耳根与脸颊侧发梢的断裂、平切和方形缺口；
- 中央刘海与固定前发的重叠根部。

这不是完整头发重构，也不解决后发层次、±30° 转头或运动遮挡问题。那些属于 v6。

## 状态

| 项目 | 结果 |
|---|---|
| 自动检查 | **29 项中 28 通过、1 失败**：`screen_right` / `hair_front_fixed` 眼睑重叠 112 > 基线 99（`baseline + 10`）；其余源哈希、两层范围、耳/脸颊区域变化、中央刘海范围检查通过 |
| 视觉审查 | **未完成**：`reports/hair_seam_test.json` 明确 `visualReviewRequired: true` |
| 当前交付 | 仍为 v5；v5.1 不能替代 v5，也不应直接合入正式 Manifest |
| 下一步 | 人工查看 `reports/hair_seam_rois.png` 与 `reports/seam_review_closeup.jpg`，确认后再决定是否采用 |

## 证据

- `hair_fix_manifest.json`：源图、两层注册文件、哈希、范围和构建脚本。
- `generation/hair_fix/generation_log.json`：两次官方内置生图请求与返修提示词；模型不由工具暴露。
- `reports/hair_seam_test.json`：四个 ROI 的像素变化、部分 alpha 统计和“需人工视觉审查”标记。
- `reports/hair_seam_rois.png`：v5 基线与 v5.1 的 4× 局部对照。
- `reports/seam_review_closeup.jpg`：接缝近景。
- `reports/verification.json`、`packed/character_front_v5.psd`：v5.1 装配结果；PSD 与 v5 不同，因两层前发已替换。

## 重建

以下命令只读已保存原图，不发生生图。项目根目录执行：

```sh
uv run --offline --with pillow --with numpy --with scipy python live2d_v5_1/scripts/refine_hair_fix.py
uv run --offline --with pillow --with numpy python live2d_v5_1/scripts/build_delivery.py
uv run --offline --with pillow python live2d_v5_1/scripts/build_face_inspector.py
uv run --offline --with psd-tools --with pillow --with numpy python scripts/live2d_v1_pack.py live2d_v5_1/manifest.json --output-dir live2d_v5_1/packed --stem character_front_v5
uv run --offline --with pillow --with numpy --with scipy python -m unittest discover -s live2d_v5_1/scripts -p 'test_*.py' -v
```

不要运行 `refine_hair.py` 覆盖 v5.1 两层；它是继承的历史脚本，不是本实验的构建入口。v5 的正式重建仍使用 [v5 README](../live2d_v5/README.md) 的命令。
