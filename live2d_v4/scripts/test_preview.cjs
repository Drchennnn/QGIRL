const {chromium}=require('/Users/Link/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');

const previewPath=path.resolve(process.env.PREVIEW_PATH||'live2d_v4/视线与发片精修预览.html');
const reportDir=path.resolve(process.env.REPORT_DIR||'live2d_v4/reports');
const sha256=value=>crypto.createHash('sha256').update(value).digest('hex');

(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  try{
    const page=await browser.newPage({viewport:{width:1150,height:850}}),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto('file://'+previewPath);
    await page.waitForFunction(()=>window.__previewReady);
    const state=()=>page.evaluate(()=>getPreviewState());
    const canvasHash=async()=>sha256(await page.locator('canvas').evaluate(canvas=>canvas.toDataURL('image/png')));
    const outputValue=id=>page.locator(id).evaluate(output=>output.value);

    const initial=await state(),initialHash=await canvasHash();
    assert(initial.ready);
    assert(initial.layerCount>0);

    await page.locator('#follow').check();
    const box=await page.locator('canvas').boundingBox();
    await page.mouse.move(box.x+box.width*.8,box.y+box.height*.6);
    const follow=await state();
    assert(follow.eyes.screen_left.x>.5&&follow.eyes.screen_left.x===follow.eyes.screen_right.x);

    await page.locator('#follow').uncheck();
    await page.locator('#linked').uncheck();
    await page.locator('#eye').selectOption('screen_left');
    const beforeIndependent=await state();
    await page.locator('#gx').fill('-0.75');
    await page.locator('#gx').dispatchEvent('input');
    await page.locator('#gy').fill('0.35');
    await page.locator('#gy').dispatchEvent('input');
    const independent=await state();
    assert.equal(independent.eyes.screen_left.x,-.75);
    assert.equal(independent.eyes.screen_left.y,.35);
    assert.deepEqual(independent.eyes.screen_right,beforeIndependent.eyes.screen_right);

    await page.locator('#eye').selectOption('screen_right');
    const rightOutputs={x:await outputValue('#gxv'),y:await outputValue('#gyv')};
    assert.equal(rightOutputs.x,beforeIndependent.eyes.screen_right.x.toFixed(2));
    assert.equal(rightOutputs.y,beforeIndependent.eyes.screen_right.y.toFixed(2));
    await page.locator('#gx').fill('0.5');
    await page.locator('#gx').dispatchEvent('input');
    await page.locator('#gy').fill('-0.4');
    await page.locator('#gy').dispatchEvent('input');
    const independentRight=await state();
    assert.deepEqual(independentRight.eyes.screen_left,independent.eyes.screen_left);
    assert.deepEqual(independentRight.eyes.screen_right,{x:.5,y:-.4});
    await page.locator('#eye').selectOption('screen_left');
    const leftOutputs={x:await outputValue('#gxv'),y:await outputValue('#gyv')};
    assert.deepEqual(leftOutputs,{x:'-0.75',y:'0.35'});

    await page.locator('#reset').click();
    const reset=await state(),resetHash=await canvasHash();
    assert.deepEqual(reset.eyes,{screen_left:{x:0,y:0},screen_right:{x:0,y:0}});
    assert.equal(resetHash,initialHash);

    await page.locator('#zoom').click();
    const fullBody=await state(),fullBodyHash=await canvasHash();
    assert.equal(fullBody.head,false);
    assert.notEqual(fullBodyHash,initialHash);
    await page.locator('#zoom').click();
    assert.equal((await state()).head,true);
    assert.equal(await canvasHash(),initialHash);

    await page.locator('#hair').fill('3');
    await page.locator('#hair').dispatchEvent('input');
    const hairHash=await canvasHash();
    assert.notEqual(hairHash,initialHash);
    fs.mkdirSync(reportDir,{recursive:true});
    await page.screenshot({path:path.join(reportDir,'preview_hair_plus3.png')});
    await page.locator('#reset').click();
    assert.equal(await canvasHash(),initialHash);

    await page.locator('details').evaluate(details=>details.open=true);
    const fringeToggle=page.locator('#rows label').filter({hasText:/^hair_fringe_center$/}).locator('input');
    assert.equal(await fringeToggle.count(),1);
    await fringeToggle.uncheck();
    const hiddenFringeHash=await canvasHash();
    assert.notEqual(hiddenFringeHash,initialHash);
    await fringeToggle.check();
    assert.equal(await canvasHash(),initialHash);

    await page.locator('details').evaluate(details=>details.open=false);
    await page.locator('aside').evaluate(aside=>aside.scrollTop=0);
    await page.screenshot({path:path.join(reportDir,'preview_browser.png')});
    assert.deepEqual(errors,[]);
    const report={
      initial,follow,independent,independentRight,leftOutputs,rightOutputs,reset,
      zoom:{head:initialHash,fullBody:fullBodyHash,changed:fullBodyHash!==initialHash},
      hair:{neutral:initialHash,plus3:hairHash,changed:hairHash!==initialHash},
      layerToggle:{visible:initialHash,hidden:hiddenFringeHash,changed:hiddenFringeHash!==initialHash},
      resetRestoresPixels:resetHash===initialHash,errors,passed:true,
    };
    fs.writeFileSync(path.join(reportDir,'browser_test.json'),JSON.stringify(report,null,2));
    console.log('PASS: load, linked mouse gaze, independent left/right eyes, output sync, reset, zoom, hair motion, layer toggle, no runtime errors');
  }finally{
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exit(1)});
