from pathlib import Path
import base64,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1]
body=json.loads((R/'body_manifest.json').read_text());head=json.loads((R/'head_manifest.json').read_text());layers=body['layers']+head['layers']
(R/'manifest.json').write_text(json.dumps({'canvas':[1024,1536],'layers':layers,'coordinateConvention':'screen_left/right = viewer side','stage':'unrigged artwork prototype'},indent=2))
images={l['name']:Image.open(R/l['file']).convert('RGBA') for l in layers}
def render(offsets=None):
 result=Image.new('RGBA',(1024,1536))
 for l in layers:result.alpha_composite(images[l['name']],(offsets or {}).get(l['name'],(0,0)))
 return result
neutral=render();neutral.save(R/'reports/reassembled.png');a=np.array(neutral);s=np.array(Image.open(R/'assets/front_master_clean.png'))
changed=int((np.any(a!=s,axis=2)&((a[:,:,3]>0)|(s[:,:,3]>0))).sum());assert changed==0
region=np.zeros(a.shape[:2],bool);region[100:260,430:590]=True;interior=ndi.binary_erosion(a[:,:,3]>250,iterations=4)&region
poses=[('neutral',{}),('fringe -3px',{'hair_fringe_center':(-3,0)}),('fringe +3px',{'hair_fringe_center':(3,0)}),('iris -2px',{'iris_screen_left':(-2,0),'iris_screen_right':(-2,0)}),('iris +2px',{'iris_screen_left':(2,0),'iris_screen_right':(2,0)})]
sheet=Image.new('RGB',(1500,350),'#b8bec4');d=ImageDraw.Draw(sheet);checks=[]
for i,(name,offsets) in enumerate(poses):
 im=render(offsets);arr=np.array(im);checks.append({'pose':name,'newTransparentHeadInteriorPixels':int((interior&(arr[:,:,3]<250)).sum())});crop=im.crop((365,15,655,315));sheet.paste(crop,(i*300,15),crop);d.text((i*300+5,326),name,fill='black')
sheet.save(R/'reports/motion_samples.jpg')
preview=Image.new('RGB',(900,1050),'#e2e4e6');full=neutral.copy();full.thumbnail((650,970));preview.paste(full,(20,35),full)
face=neutral.crop((365,15,655,315));preview.paste(face,(580,50),face);bare=images['face'].crop((400,75,620,282));preview.paste(bare,(610,450),bare)
d=ImageDraw.Draw(preview);d.text((590,410),'Separated face backing',fill='black');d.text((585,760),'37 RGBA layers / 1024 x 1536',fill='black');d.text((585,790),'Viewer-left lightning clip',fill='black');preview.save(R/'reports/delivery_preview.jpg')
sheet=Image.new('RGB',(1200,960),'#b9b9b9');d=ImageDraw.Draw(sheet)
for i,l in enumerate(head['layers']):
 im=images[l['name']].crop((370,20,650,310));im.thumbnail((194,204));x=(i%6)*200;y=(i//6)*240;sheet.paste(im,(x,y),im);d.text((x+2,y+210),l['name'],fill='black')
sheet.save(R/'reports/head_layers.jpg')
clip=np.array(images['clip_screen_left']);cy,cx=np.nonzero(clip[:,:,3]);assert cx.mean()<512
report={'canvas':[1024,1536],'layers':len(layers),'neutralChangedPixels':changed,'allFullCanvasRGBA':all(im.mode=='RGBA' and im.size==(1024,1536) for im in images.values()),'clipMeanScreenX':float(cx.mean()),'headMotionChecks':checks,'limitations':['Small translations only; no Cubism meshes, deformers, parameters, physics or runtime export.','Concealed art uses local flat-color and nearest-source extension.','Zero transparent holes does not prove production quality; inspect edges before rigging.','White mannequin follows latest confirmed scope; outfit remains separate.']}
(R/'reports/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
data=[{'name':l['name'],'src':'data:image/png;base64,'+base64.b64encode((R/l['file']).read_bytes()).decode()} for l in layers]
html='''<!doctype html><meta charset="utf-8"><title>角色拆层检查 v1</title><style>body{margin:0;background:#1c2128;color:#eee;font:14px system-ui;display:flex}aside{width:310px;height:100vh;overflow:auto;padding:15px;box-sizing:border-box}main{flex:1;height:100vh;display:grid;place-items:center;background:#abb1b6}canvas{height:96vh;max-width:100%;object-fit:contain}label{display:block;margin:8px 0}input[type=range]{width:190px}button,select{padding:8px;margin:3px}small{color:#bbb}</style><aside><h2>角色拆层检查 v1</h2><p>屏幕左侧发饰 · 37 层 · 未绑定</p><small>勾选检查图层，小幅位移检查补绘。此工具不等于 Live2D 绑定。</small><p><button id="reset">全部复位</button><button id="face">检查脸底</button></p><select id="selected"></select><label>X <input id="x" type="range" min="-12" max="12" value="0"><output id="xv">0</output></label><label>Y <input id="y" type="range" min="-12" max="12" value="0"><output id="yv">0</output></label><div id="rows"></div></aside><main><canvas id="canvas" width="1024" height="1536"></canvas></main><script>const data=DATA;const canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d'),sel=document.getElementById('selected');const rows=document.getElementById('rows');const layers=data.map(d=>({...d,on:true,x:0,y:0,img:new Image()}));function draw(){ctx.clearRect(0,0,1024,1536);for(const l of layers)if(l.on&&l.img.complete)ctx.drawImage(l.img,l.x,l.y)}layers.forEach((l,i)=>{l.img.onload=draw;l.img.src=l.src;sel.add(new Option(l.name,i));const row=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=true;box.onchange=()=>{l.on=box.checked;draw()};l.box=box;row.append(box,document.createTextNode(l.name));rows.append(row)});function sync(){for(const axis of ['x','y']){document.getElementById(axis).value=layers[sel.value][axis];document.getElementById(axis+'v').value=layers[sel.value][axis]}}sel.onchange=sync;for(const axis of ['x','y'])document.getElementById(axis).oninput=e=>{layers[sel.value][axis]=+e.target.value;document.getElementById(axis+'v').value=e.target.value;draw()};document.getElementById('reset').onclick=()=>{for(const l of layers){l.on=true;l.box.checked=true;l.x=l.y=0}sync();draw()};document.getElementById('face').onclick=()=>{for(const l of layers){l.on=l.name==='face';l.box.checked=l.on}draw()};</script>'''.replace('DATA',json.dumps(data))
(R/'角色拆层检查.html').write_text(html)
