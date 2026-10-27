const {chromium}=require('/Users/Link/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve('live2d_v4');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try {
  const page=await browser.newPage({viewport:{width:1150,height:850}});
  await page.goto('file://'+path.join(root,'视线与发片精修预览.html'));
  await page.waitForFunction(()=>window.__previewReady);
  const contract=await page.evaluate(()=>layers.filter(l=>l.name.startsWith('iris_')).map(l=>{
   const c=document.createElement('canvas');c.width=1024;c.height=1536;const q=c.getContext('2d');q.drawImage(l.mask,0,0);
   return {name:l.name,backgroundAlpha:q.getImageData(0,0,1,1).data[3]};
  }));
  for(const mask of contract)assert.equal(mask.backgroundAlpha,0,mask.name+' mask must have transparent background; black grayscale is opaque to destination-in');
  await page.evaluate(()=>{
   window.__gazeBaseline=new Uint8ClampedArray(ctx.getImageData(0,0,canvas.width,canvas.height).data);
   const makeAllowed=irisLayers=>{
    const src=document.createElement('canvas');src.width=1024;src.height=1536;const s=src.getContext('2d');
    for(const l of irisLayers)s.drawImage(l.mask,0,0);
    const out=document.createElement('canvas');out.width=600;out.height=650;const o=out.getContext('2d');o.drawImage(src,365,15,290,315,0,0,600,650);
    const pixels=o.getImageData(0,0,600,650).data,allowed=new Uint8Array(600*650);
    for(let y=0;y<650;y++)for(let x=0;x<600;x++)if(pixels[(y*600+x)*4+3]>0)
     for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++)if(y+dy>=0&&y+dy<650&&x+dx>=0&&x+dx<600)allowed[(y+dy)*600+x+dx]=1;
    return allowed;
   };
   const irisLayers=layers.filter(l=>l.name.startsWith('iris_'));
   window.__gazeAllowedBySide=Object.fromEntries(irisLayers.map(l=>[l.name.slice('iris_'.length),makeAllowed([l])]));
   window.__gazeAllowed=makeAllowed(irisLayers);
  });
  const poses=[[-4,-2],[0,-2],[4,-2],[-4,0],[0,0],[4,0],[-4,2],[0,2],[4,2],[-1.52,.74],[2.24,-1.26]],checks=[];
  fs.mkdirSync(path.join(root,'reports/gaze_browser'),{recursive:true});
  for(let i=0;i<poses.length;i++){
   const [x,y]=poses[i];
   await page.locator('#gx').fill(String(x/4));await page.locator('#gx').dispatchEvent('input');
   await page.locator('#gy').fill(String(y/2));await page.locator('#gy').dispatchEvent('input');
   const result=await page.evaluate(()=>{
    const current=ctx.getImageData(0,0,600,650).data;let outsideChanges=0,insideChanges=0,quantizationOnly=0;const examples=[];
    for(let p=0;p<600*650;p++){
     const j=p*4;if(current[j]!==window.__gazeBaseline[j]||current[j+1]!==window.__gazeBaseline[j+1]||current[j+2]!==window.__gazeBaseline[j+2]||current[j+3]!==window.__gazeBaseline[j+3]){
      if(window.__gazeAllowed[p])insideChanges++;else {
       // Chrome may change premultiplied-alpha rounding after readback. Compare
       // visible colour over the actual stage, with one 8-bit level tolerance.
       const bg=[185,192,200],a=current[j+3]/255,b=window.__gazeBaseline[j+3]/255;
       let difference=0;for(let c=0;c<3;c++)difference=Math.max(difference,Math.abs(current[j+c]*a+bg[c]*(1-a)-window.__gazeBaseline[j+c]*b-bg[c]*(1-b)));
       if(difference>1.1){outsideChanges++;if(examples.length<8)examples.push({x:p%600,y:Math.floor(p/600),difference});}else quantizationOnly++;
      }
     }
    }
    return {outsideChanges,insideChanges,quantizationOnly,eyes:getPreviewState().eyes,examples};
   });
   assert.equal(result.outsideChanges,0,'Gaze '+x+','+y+' changed pixels outside eye openings: '+JSON.stringify(result.examples));
   if(x||y)assert(result.insideChanges>0,'Gaze controls must actually move the visible iris');
   checks.push({x,y,...result});
   if(i<9){const data=await page.locator('canvas').evaluate(c=>c.toDataURL('image/png'));fs.writeFileSync(path.join(root,'reports/gaze_browser',i+'.png'),Buffer.from(data.split(',')[1],'base64'));}
  }
  await page.locator('#reset').click();
  const independent=[];
  for(const [side,x,y] of [['screen_left',.75,-.5],['screen_right',-.65,.6]]){
   await page.locator('#reset').click();
   await page.locator('#linked').uncheck();
   await page.locator('#eye').selectOption(side);
   await page.locator('#gx').fill(String(x));await page.locator('#gx').dispatchEvent('input');
   await page.locator('#gy').fill(String(y));await page.locator('#gy').dispatchEvent('input');
   const result=await page.evaluate(side=>{
    const current=ctx.getImageData(0,0,600,650).data,own=window.__gazeAllowedBySide[side];
    const other=window.__gazeAllowedBySide[side==='screen_left'?'screen_right':'screen_left'];
    let ownChanges=0,otherChanges=0,outsideChanges=0,quantizationOnly=0;
    for(let p=0;p<600*650;p++){
     const j=p*4;if(current[j]===window.__gazeBaseline[j]&&current[j+1]===window.__gazeBaseline[j+1]&&current[j+2]===window.__gazeBaseline[j+2]&&current[j+3]===window.__gazeBaseline[j+3])continue;
     if(own[p]){ownChanges++;continue;}
     const bg=[185,192,200],a=current[j+3]/255,b=window.__gazeBaseline[j+3]/255;
     let difference=0;for(let c=0;c<3;c++)difference=Math.max(difference,Math.abs(current[j+c]*a+bg[c]*(1-a)-window.__gazeBaseline[j+c]*b-bg[c]*(1-b)));
     if(difference<=1.1){quantizationOnly++;continue;}
     if(other[p])otherChanges++;else outsideChanges++;
    }
    return {side,ownChanges,otherChanges,outsideChanges,quantizationOnly,eyes:getPreviewState().eyes};
   },side);
   assert(result.ownChanges>0,side+' must visibly move its own iris');
   assert.equal(result.otherChanges,0,side+' must not change the other eye');
   assert.equal(result.outsideChanges,0,side+' must not change pixels outside its eye aperture');
   independent.push(result);
  }
  await page.locator('#reset').click();
  const reset=await page.evaluate(()=>{
   const current=ctx.getImageData(0,0,600,650).data,bg=[185,192,200];let visibleChanges=0,quantizationOnly=0;
   for(let p=0;p<600*650;p++){
    const j=p*4;if(current[j]===window.__gazeBaseline[j]&&current[j+1]===window.__gazeBaseline[j+1]&&current[j+2]===window.__gazeBaseline[j+2]&&current[j+3]===window.__gazeBaseline[j+3])continue;
    const a=current[j+3]/255,b=window.__gazeBaseline[j+3]/255;let difference=0;
    for(let c=0;c<3;c++)difference=Math.max(difference,Math.abs(current[j+c]*a+bg[c]*(1-a)-window.__gazeBaseline[j+c]*b-bg[c]*(1-b)));
    if(difference>1.1)visibleChanges++;else quantizationOnly++;
   }
   return {visibleChanges,quantizationOnly,eyes:getPreviewState().eyes};
  });
  assert.equal(reset.visibleChanges,0,'Reset must restore the neutral visible canvas');
  assert.deepEqual(reset.eyes,{screen_left:{x:0,y:0},screen_right:{x:0,y:0}});
  await page.locator('#hair').fill('-3');await page.locator('#hair').dispatchEvent('input');
  await page.screenshot({path:path.join(root,'reports/preview_hair_minus3.png')});
  await page.locator('#reset').click();
  fs.writeFileSync(path.join(root,'reports/gaze_browser_test.json'),JSON.stringify({maskAlphaContract:contract,visibleColourTolerance:1.1,checks,independent,reset,passed:true},null,2));
  console.log('PASS: real browser RGBA clipping, 11 gaze positions, independent eyes, neutral reset, and stable pixels outside eye openings');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
