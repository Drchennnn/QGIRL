'use strict';
/**
 * Runs the unmodified upstream Anime2.5DRig page against the adapter PSD.
 * Usage: node .../scripts/test_anime25d.cjs [adapter.psd] [report-directory]
 * Only a temporary 127.0.0.1 static server is started. No relay, device access,
 * model generation, cloud GPU, or writes to the upstream checkout occur.
 * Optional LAYER_ORDER_JSON: file containing {constraints:[{label,before:{names:[],roles:[]},after:{names:[],roles:[]}}]}.
 * Constraints operate on actual back-to-front render order, not parallax depth.
 * EYE_EASE defaults to0; use EYE_EASE=0.3 for the upstream-default comparison.
 * Optional RUNTIME_APP serves only /lib/app.js from the bounded006 overlay; all other upstream files stay unchanged.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
function playwright() {
  for (const modulePath of [process.env.PLAYWRIGHT_MODULE, 'playwright'].filter(Boolean)) {
    try { return require(modulePath); } catch (error) { if (error.code !== 'MODULE_NOT_FOUND') throw error; }
  }
  throw new Error('Playwright is unavailable; set PLAYWRIGHT_MODULE to the existing installation.');
}
const roundRoot = path.resolve(__dirname, '..');
const experimentRoot = path.resolve(roundRoot, '../..');
const upstream = path.join(experimentRoot, 'upstream/Anime2.5DRig');
const psdPath = path.resolve(process.argv[2] || process.env.ADAPTER_PSD || path.join(roundRoot, 'exports/anime25d_adapter.psd'));
const reportRoot = path.resolve(process.argv[3] || process.env.REPORT_DIR || path.join(roundRoot, 'reports/anime25d'));
const runtimeApp = process.env.RUNTIME_APP ? path.resolve(process.env.RUNTIME_APP) : null;
if (runtimeApp) assert(fs.existsSync(runtimeApp), 'RUNTIME_APP file missing: ' + runtimeApp);
const eyeEase = Number(process.env.EYE_EASE ?? 0);
assert(Number.isFinite(eyeEase) && eyeEase >= 0 && eyeEase <= 1, 'EYE_EASE must be within0..1');
const allowSyntheticEyeClose = process.env.ALLOW_SYNTHETIC_EYE_CLOSE === '1';
const smallMotion = process.env.SMALL_MOTION === '1';
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.psd': 'application/octet-stream', '.json': 'application/json' };
function startServer() {
  const server = http.createServer((req, res) => {
    let pathname;
    try { pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname); }
    catch (_) { res.writeHead(400).end(); return; }
    // Deliberately no OBS relay: keep the actual editor local and isolated.
    if (pathname === '/relay-info') { res.writeHead(200, { 'Content-Type': 'application/json' }).end('{}'); return; }
    const candidate = runtimeApp && pathname === '/lib/app.js' ? runtimeApp : path.resolve(upstream, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (candidate !== runtimeApp && !candidate.startsWith(upstream + path.sep)) { res.writeHead(403).end(); return; }
    fs.stat(candidate, (error, stat) => {
      if (error || !stat.isFile()) { res.writeHead(404).end(); return; }
      res.writeHead(200, { 'Content-Type': mime[path.extname(candidate)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      fs.createReadStream(candidate).pipe(res);
    });
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve({ server, url: `http://127.0.0.1:${server.address().port}` }));
  });
}
const poses = [
  { name: 'neutral', left: 1, right: 1 },
  { name: 'both075', left: .75, right: .75 },
  { name: 'both050', left: .5, right: .5 },
  { name: 'both040', left: .4, right: .4 },
  { name: 'both035', left: .35, right: .35 },
  { name: 'both030', left: .3, right: .3 },
  { name: 'both025', left: .25, right: .25 },
  { name: 'both020', left: .2, right: .2 },
  { name: 'both015', left: .15, right: .15 },
  { name: 'both010', left: .1, right: .1 },
  { name: 'both005', left: .05, right: .05 },
  { name: 'closed_both', left: 0, right: 0 },
  { name: 'closed_screen_left', left: 0, right: 1 },
  { name: 'closed_screen_right', left: 1, right: 0 },
  { name: 'neutral_restored', left: 1, right: 1 },
];
function sha256(data) { return crypto.createHash('sha256').update(data).digest('hex'); }
async function snapshot(page) {
  return page.evaluate(() => ({
    state: window.Anime25D.state(),
    blinkRuntime: window.Anime25D006Blink?.state() || null,
    workerRig: window.__rig006_worker || null,
    diagnostics: [...document.querySelectorAll('#diagnostics li')].map(n => ({ level: n.className, text: n.textContent })),
    layerCards: [...document.querySelectorAll('#layers .layer-card')].map(n => ({
      index: Number(n.dataset.index),
      name: n.querySelector('.layer-name')?.textContent,
      normalizedTitle: n.querySelector('.layer-name')?.title,
      role: n.querySelector('.layer-role')?.textContent,
      unknown: n.querySelector('.layer-role')?.classList.contains('unknown'),
      visible: n.querySelector('input[type=checkbox]')?.checked,
      opacity: Number(n.querySelector('input[id$="-opacity"]')?.value),
      depth: Number(n.querySelector('input[id$="-depth"]')?.value),
    })),
    canvas: { width: document.getElementById('cv').width, height: document.getElementById('cv').height },
    status: document.getElementById('appStatus').textContent,
  }));
}
async function nativeDownload(page, button, destination) {
  const wait = page.waitForEvent('download', { timeout: 30000 });
  await page.locator(button).evaluate(node => node.click());
  const download = await wait;
  await download.saveAs(destination);
  const failed = await download.failure();
  if (failed) throw new Error(failed);
  return { suggestedFilename: download.suggestedFilename(), bytes: fs.statSync(destination).size, sha256: sha256(fs.readFileSync(destination)) };
}
function fadeOpacity(openValue, ease, singleMesh = false) {
  if (singleMesh) return { eyeOpen: openValue > 0 ? 1 : 0, eyeClose: 0, eyelash: 1, eyewhite: openValue > 0 ? 1 : 0, irides: openValue > 0 ? 1 : 0 };
  const t = Math.max(0, Math.min(1, (openValue - (.10 + ease * .45)) / .15));
  const eyeOpen = t * t * (3 - 2 * t);
  return { eyeOpen, eyeClose: 1 - eyeOpen };
}
async function composeNativeBackground(page, nativePNG, background, destination) {
  const encoded = fs.readFileSync(nativePNG).toString('base64');
  const result = await page.evaluate(async ({ encoded, background }) => {
    const image = await new Promise((resolve, reject) => {
      const image = new Image(); image.onload = () => resolve(image); image.onerror = reject;
      image.src = 'data:image/png;base64,' + encoded;
    });
    const canvas = document.createElement('canvas'); canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = background === 'white' ? '#ffffff' : background === 'dark' ? '#20212b' : '#dddddd';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (background === 'checker') {
      ctx.fillStyle = '#aaaaaa'; const tile = 12;
      for (let y = 0; y < canvas.height; y += tile) for (let x = 0; x < canvas.width; x += tile)
        if (((x / tile + y / tile) & 1) === 0) ctx.fillRect(x, y, tile, tile);
    }
    ctx.drawImage(image, 0, 0);
    return { width: canvas.width, height: canvas.height, data: canvas.toDataURL('image/png').split(',')[1] };
  }, { encoded, background });
  fs.writeFileSync(destination, Buffer.from(result.data, 'base64'));
  return { width: result.width, height: result.height, sha256: sha256(fs.readFileSync(destination)) };
}
async function setRange(page, id, value) {
  await page.locator('#' + id).evaluate((node, v) => {
    node.value = String(v);
    node.dispatchEvent(new Event('input', { bubbles: true }));
    node.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
}
async function nextFrames(page, count = 3) {
  await page.evaluate(n => new Promise(resolve => {
    const step = () => --n <= 0 ? resolve() : requestAnimationFrame(step);
    requestAnimationFrame(step);
  }), count);
}
const defaultOrderConstraints = [
  { label: 'white inner hair behind face', before: { names: ['back hair_3', 'back hair_4'] }, after: { roles: ['face'] } },
  { label: 'front and side hair occlude eye parts', before: { roles: ['eyewhite', 'irides', 'eyelash', 'eye_close', 'eye_close2'] }, after: { roles: ['front hair', 'side hair'] } },
  { label: 'character-right clip in front of hair', before: { roles: ['front hair', 'side hair'] }, after: { names: ['headwear_1'] } },
];
function normalizedSource(name) { return String(name || '').normalize('NFKC').trim().toLowerCase().replace(/\s+/g, ' '); }
async function constrainLayerOrder(page, rig) {
  const before = (await snapshot(page)).layerCards;
  assert.equal(before.length, rig.layers.length, 'Real editor and worker rig layer counts differ.');
  const nodes = before.map((card, i) => ({ ...card, originalIndex: i, roleKey: windowlessBase(rig.layers[i].name), rigName: rig.layers[i].name }));
  const custom = process.env.LAYER_ORDER_JSON ? JSON.parse(fs.readFileSync(path.resolve(process.env.LAYER_ORDER_JSON), 'utf8')) : {};
  const constraints = custom.constraints || defaultOrderConstraints;
  const matches = (node, selector) => (selector.names || []).some(name => normalizedSource(name) === normalizedSource(node.name)) || (selector.roles || []).includes(node.roleKey);
  const edges = new Map(nodes.map(n => [n.originalIndex, new Set()]));
  const degrees = nodes.map(() => 0), applied = [];
  for (const rule of constraints) {
    const back = nodes.filter(n => matches(n, rule.before || {})), front = nodes.filter(n => matches(n, rule.after || {}));
    for (const b of back) for (const f of front) {
      if (b.originalIndex === f.originalIndex || edges.get(b.originalIndex).has(f.originalIndex)) continue;
      edges.get(b.originalIndex).add(f.originalIndex); degrees[f.originalIndex]++;
    }
    applied.push({ label: rule.label, before: back.map(n => ({ name: n.name, role: n.roleKey })), after: front.map(n => ({ name: n.name, role: n.roleKey })) });
  }
  // Stable topological order preserves all unconstrained relative choices.
  const target = [], used = new Set();
  while (target.length < nodes.length) {
    const next = nodes.find(n => !used.has(n.originalIndex) && degrees[n.originalIndex] === 0);
    assert(next, 'Layer-order constraints form a cycle.');
    target.push(next.originalIndex); used.add(next.originalIndex);
    for (const front of edges.get(next.originalIndex)) degrees[front]--;
  }
  const current = nodes.map(n => n.originalIndex), moves = [];
  for (let destination = 0; destination < target.length; destination++) {
    let from = current.indexOf(target[destination]);
    while (from > destination) {
      const actual = await page.locator(`#layers .layer-card[data-index="${from}"] .layer-name`).textContent();
      assert.equal(actual, nodes[current[from]].name, 'Layer DOM order diverged from the applied UI moves.');
      await page.locator(`#layers .layer-card[data-index="${from}"] button.ord`).first().evaluate(button => button.click());
      [current[from - 1], current[from]] = [current[from], current[from - 1]];
      moves.push({ name: actual, from, to: from - 1 }); from--;
    }
  }
  const after = (await snapshot(page)).layerCards;
  assert.deepEqual(after.map(n => n.name), target.map(i => nodes[i].name));
  const positions = new Map(current.map((originalIndex, index) => [originalIndex, index]));
  for (const [back, front] of edges) for (const f of front) assert(positions.get(back) < positions.get(f));
  // Draw order and parallax depth are independent; do not "fix" order by depth edits.
  for (let i = 0; i < current.length; i++) assert.equal(after[i].depth, nodes[current[i]].depth, 'Order adjustment changed depth.');
  return { direction: 'back_to_front', config: process.env.LAYER_ORDER_JSON || 'built-in semantic constraints', applied, moves,
    before, after, eyebrowBefore: before.filter((_, i) => nodes[i].roleKey === 'eyebrow'),
    eyebrowAfter: after.filter((_, i) => nodes[current[i]].roleKey === 'eyebrow'),
    depthUnchanged: true, constraintsSatisfied: true };
}
async function run() {
  assert(fs.existsSync(psdPath), 'Adapter PSD not found: ' + psdPath);
  assert(fs.existsSync(path.join(upstream, 'index.html')), 'Existing upstream checkout is missing.');
  fs.mkdirSync(reportRoot, { recursive: true });
  const report = {
    status: 'RUNNING', input: psdPath, inputSha256: sha256(fs.readFileSync(psdPath)),
    source: runtimeApp ? 'original upstream index.html/Worker/Rigger/WebGL renderer with explicit006 app.js overlay' : 'unmodified upstream index.html, Rigger worker, app.js deformer and WebGL renderer',
    runtimeApp, runtimeAppSHA256: runtimeApp ? sha256(fs.readFileSync(runtimeApp)) : null,
    upstreamCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: upstream, encoding: 'utf8' }).trim(),
    eyeEase, opacityFormula: runtimeApp ? '006: eyelash=1;eyewhite/irides=(open>0?1:0);eye_close=0;no complementary alpha blend' : 't=clamp((eyeOpen-(0.10+eyeEase*0.45))/0.15,0,1); openAlpha=t*t*(3-2*t); closedAlpha=1-openAlpha',
    cloudCalls: 0, cameraOrMicrophonePermissions: [], externalRequestsBlocked: [], pageErrors: [],
    consoleErrors: [], captures: [],
    limits: [
      'This checks real upstream rendering; it is not Cubism CMO3/MOC3 export or production binding.',
      'Saved phase images do not establish subjective continuous-playback quality.',
      'Native PNGs use the actual upstream export. Primary clean backgrounds are browser compositions of those captured PNGs; PSD assets are not edited.',
      'The separate *_ui_* screenshots preserve the editor view, including anchor handles that can visually cover the eyes.',
    ],
  };
  let server, browser;
  try {
    const launched = await startServer(); server = launched.server;
    browser = await playwright().chromium.launch({ headless: true,
      executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      args: ['--enable-unsafe-swiftshader'],
    });
    const context = await browser.newContext({ viewport: { width: 1550, height: 1250 }, acceptDownloads: true, permissions: [] });
    await context.route('**/*', route => {
      const requestURL = new URL(route.request().url());
      if (requestURL.protocol === 'data:' || requestURL.protocol === 'blob:' || requestURL.origin === launched.url) return route.continue();
      report.externalRequestsBlocked.push(requestURL.origin + requestURL.pathname);
      return route.abort();
    });
    // Observe the real worker's response without changing its message, rig or app code.
    await context.addInitScript(() => {
      const OriginalWorker = window.Worker;
      window.Worker = class DiagnosticWorker extends OriginalWorker {
        constructor(...args) {
          super(...args);
          this.addEventListener('message', event => {
            const rig = event.data && event.data.rig;
            if (!rig) return;
            window.__rig006_worker = {
              canvas: rig.canvas, anchors: rig.anchors, warnings: rig.warnings, synth: rig.synth,
              layers: rig.layers.map(l => ({ name: l.name, source: l.source, side: l.side, group: l.group,
                unknown: !!l.unknown, synthetic: !!l.synthetic, x: l.x, y: l.y, w: l.w, h: l.h,
                z: l.z, depth: l.depth, fade: l.fade, phys: l.phys })),
            };
          });
        }
      };
    });
    const page = await context.newPage();
    page.on('pageerror', e => report.pageErrors.push(e.message));
    page.on('console', message => { if (message.type() === 'error') report.consoleErrors.push(message.text()); });
    await page.goto(launched.url + '/', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !!window.Anime25D, null, { timeout: 20000 });
    await page.locator('#fileInput').setInputFiles(psdPath);
    await page.waitForFunction(() => window.Anime25D.state().layers > 0 || document.getElementById('appStatus').classList.contains('error'), null, { timeout: 120000 });
    assert((await page.evaluate(() => window.Anime25D.state().layers)) > 0,
      await page.locator('#appStatus').textContent());
    report.afterLoad = await snapshot(page);
    if (runtimeApp) assert.equal(report.afterLoad.blinkRuntime?.active, true, '006 overlay guard is inactive; use1024px anime25d_adapter*.psd.');
    assert(report.afterLoad.workerRig, 'Actual worker rig was not observed.');
    // Disable all automatic/device input using existing upstream controls.
    await page.evaluate(() => {
      for (const id of ['tgIdle', 'tgBlink', 'tgRand', 'tgTalk', 'tgPhys', 'tgMouse', 'tgMic', 'tgCam']) {
        const node = document.getElementById(id);
        if (node && node.getAttribute('aria-pressed') === 'true') node.click();
      }
      document.getElementById('btnReset').click();
    });
    for (const id of ['pAngleX', 'pAngleY', 'pAngleZ', 'pEyeX', 'pEyeY', 'pBody', 'pBrow', 'pBrowAngL', 'pBrowAngR', 'pBrowAngSym', 'pBangL', 'pBangC', 'pBangR', 'pMouthOpen', 'pMouthForm', 'pArmY', 'pArmPos', 'pBust']) await setRange(page, id, 0);
    await setRange(page, 'pEyeEase', eyeEase);
    // The upstream still-pose anchor editor removes unconditional breathing too.
    // This is an existing render mode; no deformer/renderer patch or substitute canvas.
    await page.locator('#btnAnchorMode').evaluate(node => node.click());
    report.stillMode = 'Upstream anchor-edit restPose: zero head/body angle, breath and iris bounce; no anchor drag.';
    await nextFrames(page);
    // Keep eye-only PoC from adding a synthetic mouth over the painted mouth.
    report.hiddenMouthLayers = await page.evaluate(() => {
      const hidden = [];
      for (const card of document.querySelectorAll('#layers .layer-card')) {
        const role = card.querySelector('.layer-role')?.textContent || '';
        if (!/口/.test(role)) continue;
        const box = card.querySelector('input[type=checkbox]');
        if (box.checked) { box.click(); hidden.push(card.querySelector('.layer-name')?.textContent); }
      }
      return hidden;
    });
    const sourceRig = report.afterLoad.workerRig;
    report.layerOrder = await constrainLayerOrder(page, sourceRig);
    report.eyeRoles = ['eyewhite', 'irides', 'eyelash', 'eye_close'].map(role => ({ role,
      realSides: [...new Set(sourceRig.layers.filter(l => !l.synthetic && windowlessBase(l.name) === role).map(l => l.side).filter(Boolean))],
      synthetic: sourceRig.layers.filter(l => l.synthetic && windowlessBase(l.name) === role).length,
    }));
    report.syntheticEyeCloseAllowed = allowSyntheticEyeClose;
    for (const role of report.eyeRoles) {
      const sides = role.realSides.sort();
      if (role.role === 'eye_close' && allowSyntheticEyeClose && sides.length === 0) {
        assert.equal(role.synthetic, 2, 'Expected one automatically generated close-eye part per side.');
      } else {
        assert.deepEqual(sides, ['L', 'R'], 'Need real bilateral role ' + role.role);
      }
    }
    report.unknownLayers = sourceRig.layers.filter(l => l.unknown).map(l => l.source || l.name);
    report.beforePoses = await snapshot(page);
    assert(Object.values(report.beforePoses.state.auto).every(v => !v), 'Some automatic input remained enabled.');
    assert.equal(report.beforePoses.state.anchorMode, true);
    report.settingsFile = await nativeDownload(page, '#btnExportSettings', path.join(reportRoot, 'neutral.rig.json'));
    const frozenSettings = JSON.parse(fs.readFileSync(path.join(reportRoot, 'neutral.rig.json'), 'utf8'));
    assert.equal(frozenSettings.params.eyeEase, eyeEase, 'Exported settings lost eyeEase.');
    report.exportedSettingsEyeEase = frozenSettings.params.eyeEase;
    let neutralHash;
    for (const pose of poses) {
      await setRange(page, 'pEyeL', pose.left);
      await setRange(page, 'pEyeR', pose.right);
      await nextFrames(page);
      const state = await snapshot(page);
      assert.equal(state.state.params.eyeOpenL, pose.left);
      assert.equal(state.state.params.eyeOpenR, pose.right);
      const output = path.join(reportRoot, pose.name + '.png');
      const native = await nativeDownload(page, '#btnPng', output);
      if (pose.name === 'neutral') neutralHash = native.sha256;
      if (pose.name === 'neutral_restored') assert.equal(native.sha256, neutralHash, 'Upstream neutral PNG did not restore exactly.');
      const actualOpacity = { left: fadeOpacity(pose.left, state.state.params.eyeEase, !!state.blinkRuntime?.active), right: fadeOpacity(pose.right, state.state.params.eyeEase, !!state.blinkRuntime?.active) };
      const entry = { ...pose, ...native, state: state.state, nativePNG: path.basename(output), actualOpacity,
        actualLayerOpacity: sourceRig.layers.filter(l => l.fade === 'eyeOpen' || l.fade === 'eyeClose' || l.fade === 'eyeClose2').map(l => {
          const saved = frozenSettings.layers.find(s => s.id === String(l.z) + ':' + l.name);
          assert(saved, 'Exported settings missing actual runtime layer ' + l.name);
          const side = l.side === 'L' ? 'left' : 'right';
          const factor = state.blinkRuntime?.active && ['eyelash', 'eyewhite', 'irides'].includes(windowlessBase(l.name)) ? actualOpacity[side][windowlessBase(l.name)] : l.fade === 'eyeOpen' ? actualOpacity[side].eyeOpen : l.fade === 'eyeClose' ? actualOpacity[side].eyeClose : 0;
          return { name: l.name, side: l.side, fade: l.fade, visible: saved?.visible, layerOpacity: saved?.opacity, factor, finalAlpha: saved?.visible ? factor * saved.opacity : 0, maskStillActiveWhenHidden: windowlessBase(l.name) === 'eyewhite' };
        }), backgrounds: [], uiBackgrounds: [] };
      for (const [background, css] of [['white', '#fff'], ['dark', '#20212b'], ['checker', 'repeating-conic-gradient(#aaa 0% 25%,#ddd 0% 50%) 0/24px 24px']]) {
        await page.locator('#cv').evaluate((canvas, style) => { canvas.style.background = style; }, css);
        // Taking a screenshot samples the actual upstream WebGL canvas.
        const filename = pose.name + '_' + background + '.png';
        const composed = await composeNativeBackground(page, output, background, path.join(reportRoot, filename));
        entry.backgrounds.push({ file: filename, ...composed, source: 'native PNG browser composition; no editor UI' });
        const uiFilename = pose.name + '_ui_' + background + '.png';
        await page.locator('#cv').screenshot({ path: path.join(reportRoot, uiFilename) });
        entry.uiBackgrounds.push(uiFilename);
      }
      report.captures.push(entry);
    }
    report.afterPoses = await snapshot(page);
    report.exactNeutralRestore = true;
    if (smallMotion) {
      const motion = { pAngleX: 0.12, pAngleY: -0.08, pAngleZ: 0.06, pBrow: 0.2,
        pBrowAngL: 0.1, pBrowAngR: -0.1, pBangL: 0.1, pBangC: -0.08, pBangR: 0.1 };
      for (const [id, value] of Object.entries(motion)) await setRange(page, id, value);
      await nextFrames(page);
      const state = await snapshot(page);
      const output = path.join(reportRoot, 'small_motion.png');
      const native = await nativeDownload(page, '#btnPng', output);
      const composed = await composeNativeBackground(page, output, 'checker', path.join(reportRoot, 'small_motion_checker.png'));
      report.smallMotion = { params: motion, state, ...native, nativePNG: path.basename(output),
        checkerPNG: { file: 'small_motion_checker.png', ...composed } };
    }
    report.status = 'TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED';
    assert.deepEqual(report.pageErrors, []);
    console.log(`PASS actual Anime2.5DRig ${report.afterPoses.state.modelName}: ${report.afterPoses.state.layers} rig layers; ${poses.length} poses; ${poses.length * 3} clean background frames + matching UI screenshots; exact neutral restore.`);
  } catch (error) {
    report.status = 'FAIL'; report.error = error.stack || String(error);
    throw error;
  } finally {
    fs.writeFileSync(path.join(reportRoot, 'runtime_validation.json'), JSON.stringify(report, null, 2) + '\n');
    if (browser) await browser.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
}
function windowlessBase(name) {
  // The real Rigger normalized name is already canonical; strip its side/part suffix.
  return String(name).replace(/_(l|r)$/, '').replace(/_\d+$/, '');
}
run().catch(error => { console.error(error.message); process.exitCode = 1; });
