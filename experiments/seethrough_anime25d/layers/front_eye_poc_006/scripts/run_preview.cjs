'use strict';
/**
 * Local-only persistent preview server for the unmodified upstream app.
 * Usage: node scripts/run_preview.cjs [adapter.psd] [neutral.rig.json] [port]
 * Ctrl+C closes it. No OBS relay, cloud call, device input, or automatic camera.
 * RUNTIME_APP optionally overrides only /lib/app.js with the explicit006 overlay.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const root = path.resolve(__dirname, '..');
const upstream = path.resolve(root, '../../upstream/Anime2.5DRig');
const psd = path.resolve(process.argv[2] || process.env.ADAPTER_PSD || path.join(root, 'exports/anime25d_adapter.psd'));
const settings = path.resolve(process.argv[3] || process.env.RIG_SETTINGS || path.join(root, 'reports/anime25d/neutral.rig.json'));
const runtimeApp = process.env.RUNTIME_APP ? path.resolve(process.env.RUNTIME_APP) : null;
if (runtimeApp && !fs.existsSync(runtimeApp)) throw new Error('RUNTIME_APP missing: ' + runtimeApp);
const port = Number(process.argv[4] || process.env.PREVIEW_PORT || 0);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be within0..65535.');
if (!fs.existsSync(psd)) throw new Error('Adapter PSD missing: ' + psd);
if (!fs.existsSync(settings)) throw new Error('Matching settings JSON missing: ' + settings + '\nRun test_anime25d.cjs first, or pass the settings path explicitly.');
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.psd': 'application/octet-stream' };
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const settingsData = JSON.parse(fs.readFileSync(settings, 'utf8'));
const landing = `<!doctype html><html lang="zh"><meta charset="utf-8"><title>006 Anime2.5DRig 本地检查</title><style>body{font:16px/1.8 system-ui;background:#202332;color:#edf0fa;max-width:1000px;margin:45px auto;padding:20px}a{color:#9accff}code{overflow-wrap:anywhere}li{margin:15px 0}</style><h1>006 · 实际 Anime2.5DRig 本地检查</h1><p>此服务只绑定127.0.0.1。模型解析、网格和WebGL绘制使用现有上游组件，没有替代画布或云端推理。${runtimeApp ? "<strong>当前启用006限定眨眼app.js覆盖：单一睫毛纹理网格，无开闭透明交叉；必须使用同版适配PSD。</strong>" : "当前使用原始上游app.js。"}</p><ol><li><a href="/" target="_blank">打开真正的 Anime2.5DRig 页面</a>。</li><li>点击「PSDを開く」，选择下面的适配PSD。也可先<a download="anime25d_adapter.psd" href="/__poc006/adapter.psd">下载同版适配PSD</a>，再拖入页面。<br><code>${escapeHTML(psd)}</code></li><li>点击「設定JSONを読み込む」，导入同版设置。设置包含实际画序、关闭的自动/物理/设备输入与eyeEase=${escapeHTML(settingsData.params?.eyeEase)}。<a download="neutral.rig.json" href="/__poc006/settings.rig.json">下载设置JSON</a><br><code>${escapeHTML(settings)}</code></li><li>点击「一時停止」冻结呼吸，再用「目」中的左右开合滑块查看全开、半开、全闭、独立闭眼。请检查眼外角与侧发接合、旧眼框、眼白和虹膜是否越界。不要仅凭模型已载入认定画序/设置已生效。</li></ol><p>自动眨眼、摄像头、麦克风和转头不在当前检查范围。主机终端按Ctrl+C停止本地服务。</p><p>检查用PNG由测试脚本通过上游原生导出获得；编辑锚点浮标不属于实际模型纹理。</p></html>`;
function sendFile(res, file, attachment) {
  fs.stat(file, (error, stat) => {
    if (error || !stat.isFile()) { res.writeHead(404).end('Not found'); return; }
    const headers = { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' };
    if (attachment) headers['Content-Disposition'] = 'attachment; filename="' + attachment + '"';
    res.writeHead(200, headers); fs.createReadStream(file).pipe(res);
  });
}
const server = http.createServer((req, res) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname); }
  catch (_) { res.writeHead(400).end(); return; }
  if (pathname === '/006-ready') {
    const bootstrap = `<script>(async()=>{try{const psd=await(await fetch('/__poc006/adapter.psd')).blob();const input=document.getElementById('fileInput'),dt=new DataTransfer();dt.items.add(new File([psd],'anime25d_adapter.psd'));input.files=dt.files;input.dispatchEvent(new Event('change'));const deadline=Date.now()+120000;while(!window.Anime25D?.state().layers){if(Date.now()>deadline)throw Error('Model loading timeout');await new Promise(r=>setTimeout(r,100));}const config=await(await fetch('/__poc006/settings.rig.json')).blob(),settings=document.getElementById('settingsInput'),st=new DataTransfer();st.items.add(new File([config],'neutral.rig.json'));settings.files=st.files;settings.dispatchEvent(new Event('change'));await new Promise(r=>setTimeout(r,500));document.getElementById('tgBlink').click();}catch(e){console.error('006 autoload:',e);}})();</script>`;
    const html=fs.readFileSync(path.join(upstream,'index.html'),'utf8').replace('</body>',bootstrap+'</body>');
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}).end(html);return;
  }
  if (pathname === '/__poc006/' || pathname === '/__poc006') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }).end(landing); return; }
  if (pathname === '/__poc006/adapter.psd') { sendFile(res, psd, 'anime25d_adapter.psd'); return; }
  if (pathname === '/__poc006/settings.rig.json') { sendFile(res, settings, 'neutral.rig.json'); return; }
  if (pathname === '/relay-info') { res.writeHead(200, { 'Content-Type': 'application/json' }).end('{}'); return; }
  const file = runtimeApp && pathname === '/lib/app.js' ? runtimeApp : path.resolve(upstream, '.' + (pathname === '/' ? '/index.html' : pathname));
  if (file !== runtimeApp && !file.startsWith(upstream + path.sep)) { res.writeHead(403).end(); return; }
  sendFile(res, file);
});
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
server.listen(port, '127.0.0.1', () => {
  const actualPort = server.address().port;
  console.log('Instructions: http://127.0.0.1:' + actualPort + '/__poc006/');
  console.log('Actual upstream: http://127.0.0.1:' + actualPort + '/');
  console.log('Runtime app: ' + (runtimeApp || 'original upstream app.js'));
  console.log('PSD: ' + psd + '\nSettings: ' + settings + '\nCtrl+C to stop.');
});
function close() { server.close(() => process.exit(0)); }
process.on('SIGINT', close); process.on('SIGTERM', close);
