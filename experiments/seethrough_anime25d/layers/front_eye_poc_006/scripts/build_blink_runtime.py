"""Build the bounded006 app.js overlay without changing the upstream checkout."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[1]
upstream = root.parents[1] / 'upstream' / 'Anime2.5DRig'
source_path = upstream / 'lib' / 'app.js'
source = source_path.read_text()
config = {
    'scope': 'front_eye_poc_006 only;1024px anime25d_adapter PSD',
    'filenamePattern': '^anime25d_adapter(?:[_.-].*)?\\.psd$',
    'policy': 'single textured lash mesh;no eyeOpen/eyeClose opacity crossfade',
    'canvas': [1024, 1024],
    'sourceY': [518, 542],
    'closedThickness': 8,
    'L': {'sourceX': [295, 478], 'targetX': [326, 465],
          'curve': [[[326, 568], [350, 582], [365, 590], [391, 589]],
                    [[391, 589], [423, 590], [447, 584], [465, 575]]]},
    'R': {'sourceX': [593, 778], 'targetX': [600, 750],
          'curve': [[[600, 579], [622, 587], [643, 589], [669, 583]],
                    [[669, 583], [700, 581], [728, 574], [750, 561]]]},
}
insert = '''
// 006-only runtime overlay. Original app.js stays in upstream unchanged.
// A single textured eyelash mesh moves continuously into the hand-drawn closed
// curve. eye_close remains an imported reference and is not drawn. No per-column
// dark min/max silhouette or complementary opacity blend is used.
const BLINK006 = CONFIG;
const BLINK006_FILE = new RegExp(BLINK006.filenamePattern, 'i');
function blink006Active(){
  return CW===BLINK006.canvas[0]&&CH===BLINK006.canvas[1]&&BLINK006_FILE.test(modelName);
}
function blink006CurveY(side,x){
  const spans=BLINK006[side].curve;
  const p=x<spans[0][3][0]?spans[0]:spans[1];
  const at=(t,k)=>(1-t)**3*p[0][k]+3*(1-t)**2*t*p[1][k]+3*(1-t)*t*t*p[2][k]+t**3*p[3][k];
  let lo=0,hi=1;
  for(let i=0;i<20;i++){const t=(lo+hi)/2;if(at(t,0)<x)lo=t;else hi=t;}
  return at((lo+hi)/2,1);
}
function blink006Vertex(side,bn,x,y,open){
  const v=clamp(open,0,1);
  if(v===1)return {x,y}; // neutral texture/geometry is untouched
  const c=BLINK006[side],u=clamp((x-c.sourceX[0])/(c.sourceX[1]-c.sourceX[0]),0,1);
  const tx=c.targetX[0]+u*(c.targetX[1]-c.targetX[0]);
  // Normalize the main upper-lash band only; pixels outside it clamp to the
  // same closed thickness band. White meshes still collapse to the center curve.
  const middle=(BLINK006.sourceY[0]+BLINK006.sourceY[1])/2;
  const thickness=bn==='eyelash'?clamp((y-middle)/(BLINK006.sourceY[1]-BLINK006.sourceY[0]),-.5,.5)*BLINK006.closedThickness:0;
  const ty=blink006CurveY(side,tx)+thickness;
  return {x:v*x+(1-v)*tx,y:v*y+(1-v)*ty};
}
Object.defineProperty(window,'Anime25D006Blink',{value:Object.freeze({
  config:BLINK006,
  state(){return {active:blink006Active(),modelName,policy:BLINK006.policy,config:BLINK006};}
})});
'''.replace('CONFIG', json.dumps(config, separators=(',', ':')))
marker = "const APP_VERSION='2.0.0';"
assert source.count(marker) == 1
patched = source.replace(marker, marker + '\n' + insert)
fade_marker = "function fadeAlpha(L,e,alt){\n  if(!L.fade)return 1;"
fade_replacement = """function fadeAlpha(L,e,alt){
  if(blink006Active()&&L.side){
    const open=L.side==='L'?e.eyeOpenL:e.eyeOpenR;
    if(L.bn==='eye_close'||L.bn==='eye_close2')return 0;
    if(L.bn==='eyelash')return 1;
    if(L.bn==='eyewhite'||L.bn==='irides')return open>0?1:0;
  }
  if(!L.fade)return 1;"""
assert patched.count(fade_marker) == 1
patched = patched.replace(fade_marker, fade_replacement)
local_marker = """    if(L.fade==='eyeOpen'&&EA){
      if(bn==='irides'){"""
local_replacement = """    if(blink006Active()&&EA&&(bn==='eyelash'||bn==='eyewhite')){
      const point=blink006Vertex(eyeSide,bn,x,y,vOpen);x=point.x;y=point.y;
    }else if(L.fade==='eyeOpen'&&EA){
      if(bn==='irides'){"""
assert patched.count(local_marker) == 1
patched = patched.replace(local_marker, local_replacement)
squeeze = """        const tl=smooth((0.32-vOpen)/0.32);   // iris stays round until nearly closed
        y=EA.closeY+(y-EA.closeY)*(1-0.80*tl);"""
assert patched.count(squeeze) == 1
patched = patched.replace(squeeze, """        // 006 irides keep their texture shape and are clipped by the real
        // continuously collapsing eyewhite mask. Generic upstream fallback stays.
        if(!blink006Active()){
          const tl=smooth((0.32-vOpen)/0.32);
          y=EA.closeY+(y-EA.closeY)*(1-0.80*tl);
        }""")
runtime = root / 'runtime'
runtime.mkdir(exist_ok=True)
(runtime / 'app.js').write_text(patched)
(runtime / 'blink_config.json').write_text(json.dumps(config, indent=2) + '\n')
(runtime / 'app.patch.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True), patched.splitlines(True), fromfile='upstream/Anime2.5DRig/lib/app.js', tofile='front_eye_poc_006/runtime/app.js')))
sha = lambda value: hashlib.sha256(value.encode()).hexdigest()
manifest = {
    'scope': config['scope'],
    'upstreamCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip(),
    'originalAppSHA256': sha(source), 'overlayAppSHA256': sha(patched),
    'config': 'blink_config.json', 'diff': 'app.patch.diff',
    'serve': 'RUNTIME_APP=<absolute006/runtime/app.js> node scripts/test_anime25d.cjs or scripts/run_preview.cjs',
    'changes': ['006 filename/canvas guard', 'disable complementary open/closed opacity;closed reference renders0', 'single textured eyelash mesh maps continuously to hand-drawn closed curve', 'eyewhite mesh maps to zero-height closed curve;iris keeps shape and uses real upstream mask'],
    'unchanged': ['upstream files', 'PSD parser/Worker/Rigger', 'WebGL renderer', 'non-eye deformation', 'unmatched filenames/canvas use original upstream policy'],
}
(runtime / 'patch_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
assert source_path.read_text() == source
print('Built006 runtime overlay;upstream app unchanged')
