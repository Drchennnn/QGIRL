const {chromium}=require('/Users/Link/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');

const root=path.resolve('live2d_v5_1');
const inspectorPath=path.join(root,'脸部第二组_独立分件检查.html');
const reportDir=path.join(root,'reports');

(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  try{
    const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto('file://'+inspectorPath);
    await page.waitForFunction(()=>window.__faceInspectorReady===true);
    await page.waitForFunction(()=>[...document.images].length===6&&[...document.images].every(image=>image.complete&&image.naturalWidth>0&&image.naturalHeight>0));

    const cards=page.locator('main article');
    assert.equal(await cards.count(),6,'The face inspector must expose exactly six semantic assets');
    const names=await cards.locator('code').allTextContents();
    assert.deepEqual(new Set(names),new Set(['face','neck_bridge','ear_screen_left','ear_screen_right','nose','mouth']));

    const backgrounds=[];
    for(const background of ['checker','white','dark']){
      const button=page.locator(`#background button[data-bg="${background}"]`);
      assert.equal(await button.count(),1);
      await button.click();
      assert.equal(await button.getAttribute('aria-pressed'),'true');
      assert.equal(await page.locator('#background button[aria-pressed="true"]').count(),1);
      backgrounds.push(background);
    }

    const modes=[];
    for(const mode of ['mother','native','zoom']){
      const button=page.locator(`#mode button[data-mode="${mode}"]`);
      assert.equal(await button.count(),1);
      await button.click();
      assert.equal(await button.getAttribute('aria-pressed'),'true');
      assert.equal(await page.locator('#mode button[aria-pressed="true"]').count(),1);
      const loaded=await page.locator('main img').evaluateAll(images=>images.every(image=>image.complete&&image.naturalWidth>0&&image.naturalHeight>0));
      assert(loaded,mode+' must display six loaded assets');
      modes.push(mode);
    }

    fs.mkdirSync(reportDir,{recursive:true});
    await page.screenshot({path:path.join(reportDir,'face_inspector_browser.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    const report={componentCount:6,names,backgrounds,modes,errors,passed:true};
    fs.writeFileSync(path.join(reportDir,'face_inspector_test.json'),JSON.stringify(report,null,2));
    console.log('PASS: six face-group assets, three backgrounds, three display modes, no browser errors');
  }finally{
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exit(1)});
