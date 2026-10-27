# 第四阶段：真实动态播放器

> 已归档（2026-10-27）。以下为旧角色管线当时的记录，路径相对于 `archive/legacy_character_pipeline/`；当前交付与 v6 计划见根目录 `README.md` 和 `docs/PROGRESS.md`。

本地入口：http://127.0.0.1:4176 。页面加载第三阶段真实 MOC3 和纹理，经官方 Cubism Core 及 pixi-live2d-display 内的 Cubism WebGL 渲染器播放。不是 GIF 或 CPU 快照播放器。

## 启动与复现

在本目录执行：

    npm ci --ignore-scripts --no-audit --no-fund
    npm run prepare-assets
    npm test
    npm start

打开上述本地地址；停止服务器按 Ctrl+C。现有 node_modules 可直接 npm start。服务仅监听 127.0.0.1，仅暴露 public/，不会提供项目根目录、PSD、CMO3、报告或凭据。浏览器不连接 CDN 或生图服务。

## 控制

- 左右眼开合、联动、眨眼、慢速闭眼、单眼 Wink、自然眨眼。左右指角色自身。手动开度会中止表情；眨眼从当前开度闭合并回到该开度。
- 表情使用已导出的闭眼微笑、半闭眼、惊讶、嫌弃眼。自然眨眼避开非中性表情，眉毛保持固定。
- 头部 AngleX ±5、AngleY ±3，发片参数 ±0.1；呼吸、轻摆和头发物理可单独开关。它们是绑定参数值，不代表测得的三维转头角度。
- 播放小幅待机：真实 SDK 动作管理器执行第三阶段 6 秒 Review 动作，并显式设置循环。手动输入或复位会中止动作。
- 暂停冻结模型更新；恢复中性清理待机、表情、物理历史和手动开度，关闭呼吸/自然眨眼/轻摆。减少动态偏好也会禁用初次自动眨眼和呼吸。
- 运行播放自检：暂停常规循环并执行实际 WebGL 绘制、Core 更新、动作和物理求值。结果在诊断折叠区显示。

## 物理与兼容适配

runtime.physics3.json 从第三阶段物理配置派生，仅保留前发、后发、侧发三项，输出 Scale 为源值的 0.4；排除眼球、胸部和额外头部/身体物理。最后一层参数夹取确保发片始终在 ±0.1。受控 ±5 输入测试的最大物理发片响应约 0.04993，不能推断任意动作也有相同峰值。

PixiJS 固定 6.5.10，pixi-live2d-display 固定 0.4.0，Core 沿用已有 5.1.0。vendor/pixi-csp-6.5.10 保留同版本官方 CSP 静态 uniform 补丁、MIT 许可和来源；该补丁名称为 unsafe-eval，但用途是替换动态函数生成。页面仍禁止 JavaScript unsafe-eval，仅允许 Core 所需的 WebAssembly 编译。

## 验证证据

- reports/browser_runtime.json：21 项真实 Chrome WebGL 播放自检通过；包括独立眼、开闭图层互补、表情切换、待机循环、暂停、物理范围/开关、复位、数值有限和异步取消。
- reports/browser_neutral.png、browser_wink.png、browser_half_eye.png：真实浏览器画面。browser_narrow.png 为窄屏布局检查。
- reports/node_tests.log：24 项测试通过，覆盖控制状态、眨眼连续性、HTTP 隔离、资产哈希、派生物理、脚本顺序和 CSP 检查。
- reports/asset_provenance.json：复制资源的源路径、字节与 SHA256。
- reports/source_preservation.json：第二阶段 70 个文件、第三阶段已交付 22 个文件哈希保持一致。本轮新增生图调用为 0。
- reports/editor_compatibility.json / .md：本机未发现 Cubism Editor，实际 CMO3 打开/编辑/保存无法验证。

## 保留边界

这是小幅动态审阅候选。浏览器截图可确认模型正常显示及眼形状态，不能替代用户对慢速闭合线条、头发遮挡和最终风格的视觉验收。完整隐藏区、手部抬杯、口腔与统一调色尚未制作。Cubism Editor 和 VTube Studio 兼容性仍未验证；第三阶段原导出诊断保留，原 PSD 独立保留。页面 FPS 仅作实时观察，不作为性能基准。
